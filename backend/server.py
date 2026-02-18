from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os, logging, httpx, uuid, hashlib, hmac, random
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
RAZORPAY_ENABLED = bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)
razorpay_client = None
if RAZORPAY_ENABLED:
    import razorpay
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

COMMISSION_LEVELS = {1: 0.40, 2: 0.20, 3: 0.10, 4: 0.05, 5: 0.03, 6: 0.015, 7: 0.005}
MIN_WITHDRAWAL = 100
ADMIN_EMAILS = os.environ.get("ADMIN_EMAILS", "").split(",")

# XP rewards
XP_LESSON_COMPLETE = 10
XP_QUIZ_PASS = 25
XP_COURSE_COMPLETE = 100
XP_REFERRAL = 50
XP_REVIEW = 15

# ---- Auth Helpers ----
async def get_current_user(request: Request) -> dict:
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def require_admin(request: Request) -> dict:
    user = await get_current_user(request)
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def optional_user(request: Request):
    try:
        return await get_current_user(request)
    except Exception:
        return None

def generate_referral_code():
    return "MM" + uuid.uuid4().hex[:8].upper()

def now_iso():
    return datetime.now(timezone.utc).isoformat()

async def add_xp(user_id: str, amount: int, reason: str):
    await db.users.update_one({"user_id": user_id}, {"$inc": {"xp": amount}})
    await db.xp_log.insert_one({"user_id": user_id, "amount": amount, "reason": reason, "created_at": now_iso()})

async def add_notification(user_id: str, title: str, message: str, ntype: str = "info"):
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:10]}", "user_id": user_id,
        "title": title, "message": message, "type": ntype,
        "read": False, "created_at": now_iso(),
    })

# ---- Auth Routes ----
@api_router.post("/auth/session")
async def process_session(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id")
    referral_code = body.get("referral_code")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    async with httpx.AsyncClient() as http_client:
        resp = await http_client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        data = resp.json()
    email, name, picture = data["email"], data["name"], data.get("picture", "")
    session_token = data["session_token"]
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        user_id = existing["user_id"]
        updates = {"name": name, "picture": picture}
        if email.strip() in [e.strip() for e in ADMIN_EMAILS if e.strip()]:
            updates["is_admin"] = True
        await db.users.update_one({"email": email}, {"$set": updates})
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        ref_code = generate_referral_code()
        referred_by_user = None
        referral_chain = []
        if referral_code:
            referrer = await db.users.find_one({"referral_code": referral_code}, {"_id": 0})
            if referrer:
                referred_by_user = referrer["user_id"]
                parent_chain = referrer.get("referral_chain", [])
                referral_chain = [referrer["user_id"]] + parent_chain[:6]
                await add_notification(referrer["user_id"], "New Referral!", f"{name} joined using your referral link", "referral")
                await add_xp(referrer["user_id"], XP_REFERRAL, f"Referral: {name} joined")
        is_admin = email.strip() in [e.strip() for e in ADMIN_EMAILS if e.strip()]
        await db.users.insert_one({
            "user_id": user_id, "email": email, "name": name, "picture": picture,
            "phone": "", "referral_code": ref_code, "referred_by": referred_by_user,
            "referral_chain": referral_chain, "status": "pending",
            "is_admin": is_admin, "xp": 0, "streak": 0, "last_streak_date": None,
            "onboarding_complete": False, "created_at": now_iso(),
        })
    await db.user_sessions.insert_one({
        "user_id": user_id, "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": now_iso(),
    })
    response.set_cookie(key="session_token", value=session_token, httponly=True, secure=True, samesite="none", path="/", max_age=7*24*3600)
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    st = request.cookies.get("session_token")
    if st: await db.user_sessions.delete_many({"session_token": st})
    response.delete_cookie("session_token", path="/", samesite="none", secure=True)
    return {"message": "Logged out"}

@api_router.put("/auth/profile")
async def update_profile(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    updates = {}
    for f in ["phone", "name", "bio", "city", "interests", "onboarding_complete"]:
        if f in body: updates[f] = body[f]
    if updates: await db.users.update_one({"user_id": user["user_id"]}, {"$set": updates})
    return await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})

# ---- Course Routes ----
@api_router.get("/courses")
async def list_courses():
    courses = await db.courses.find({"published": {"$ne": False}}, {"_id": 0}).to_list(100)
    for c in courses:
        if "lessons" in c:
            c["lesson_count"] = len(c["lessons"])
            for l in c["lessons"]: l.pop("video_url", None)
        # Get avg rating
        pipeline = [{"$match": {"course_id": c["course_id"]}}, {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}]
        rating_result = await db.reviews.aggregate(pipeline).to_list(1)
        c["avg_rating"] = round(rating_result[0]["avg"], 1) if rating_result else 0
        c["review_count"] = rating_result[0]["count"] if rating_result else 0
    return courses

@api_router.get("/courses/{course_id}")
async def get_course(course_id: str):
    course = await db.courses.find_one({"course_id": course_id}, {"_id": 0})
    if not course: raise HTTPException(status_code=404, detail="Course not found")
    if "lessons" in course:
        course["lesson_count"] = len(course["lessons"])
        for l in course["lessons"]: l.pop("video_url", None)
    pipeline = [{"$match": {"course_id": course_id}}, {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}]
    r = await db.reviews.aggregate(pipeline).to_list(1)
    course["avg_rating"] = round(r[0]["avg"], 1) if r else 0
    course["review_count"] = r[0]["count"] if r else 0
    return course

@api_router.get("/courses/{course_id}/lessons")
async def get_course_lessons(course_id: str, user: dict = Depends(get_current_user)):
    course = await db.courses.find_one({"course_id": course_id}, {"_id": 0})
    if not course: raise HTTPException(status_code=404, detail="Course not found")
    if not user.get("is_admin", False):
        purchase = await db.purchases.find_one({"user_id": user["user_id"], "course_id": course_id}, {"_id": 0})
        if not purchase: raise HTTPException(status_code=403, detail="Purchase required")
    progress = await db.progress.find({"user_id": user["user_id"], "course_id": course_id}, {"_id": 0}).to_list(100)
    completed_ids = {p["lesson_id"] for p in progress}
    lessons = course.get("lessons", [])
    for l in lessons:
        l["completed"] = l.get("lesson_id", "") in completed_ids
    quizzes = await db.quizzes.find({"course_id": course_id}, {"_id": 0}).to_list(100)
    return {"lessons": lessons, "resources": course.get("resources", []), "quizzes": quizzes, "progress_count": len(completed_ids), "total_count": len(lessons)}

@api_router.get("/courses/{course_id}/upsell")
async def get_upsell(course_id: str):
    return await db.courses.find_one({"upsell_for": course_id, "is_upsell": True}, {"_id": 0})

# ---- Progress Tracking ----
@api_router.post("/progress/complete")
async def mark_lesson_complete(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    course_id, lesson_id = body["course_id"], body["lesson_id"]
    existing = await db.progress.find_one({"user_id": user["user_id"], "course_id": course_id, "lesson_id": lesson_id})
    if existing: return {"message": "Already completed"}
    await db.progress.insert_one({"user_id": user["user_id"], "course_id": course_id, "lesson_id": lesson_id, "completed_at": now_iso()})
    await add_xp(user["user_id"], XP_LESSON_COMPLETE, f"Completed lesson")
    # Update streak
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    last_date = user.get("last_streak_date")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    if last_date == today:
        pass
    elif last_date == yesterday:
        await db.users.update_one({"user_id": user["user_id"]}, {"$inc": {"streak": 1}, "$set": {"last_streak_date": today}})
    else:
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"streak": 1, "last_streak_date": today}})
    # Check course completion
    course = await db.courses.find_one({"course_id": course_id}, {"_id": 0})
    total_lessons = len(course.get("lessons", []))
    completed = await db.progress.count_documents({"user_id": user["user_id"], "course_id": course_id})
    if completed >= total_lessons and total_lessons > 0:
        existing_cert = await db.certificates.find_one({"user_id": user["user_id"], "course_id": course_id})
        if not existing_cert:
            cert_id = f"CERT-{uuid.uuid4().hex[:8].upper()}"
            await db.certificates.insert_one({
                "certificate_id": cert_id, "user_id": user["user_id"], "course_id": course_id,
                "course_title": course["title"], "user_name": user["name"],
                "completed_at": now_iso(),
            })
            await add_xp(user["user_id"], XP_COURSE_COMPLETE, f"Completed {course['title']}")
            await add_notification(user["user_id"], "Certificate Earned!", f"Congratulations! You completed {course['title']}", "certificate")
    return {"message": "Lesson completed", "completed": completed, "total": total_lessons}

@api_router.get("/progress/continue")
async def get_continue_learning(user: dict = Depends(get_current_user)):
    purchases = await db.purchases.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(100)
    result = []
    for p in purchases:
        course = await db.courses.find_one({"course_id": p["course_id"]}, {"_id": 0})
        if not course or not course.get("lessons"): continue
        total = len(course["lessons"])
        completed = await db.progress.count_documents({"user_id": user["user_id"], "course_id": p["course_id"]})
        if completed >= total: continue
        progress_list = await db.progress.find({"user_id": user["user_id"], "course_id": p["course_id"]}, {"_id": 0}).to_list(100)
        completed_ids = {pr["lesson_id"] for pr in progress_list}
        next_lesson = None
        for l in course["lessons"]:
            if l.get("lesson_id") not in completed_ids:
                next_lesson = {"title": l["title"], "lesson_id": l["lesson_id"]}; break
        result.append({
            "course_id": p["course_id"], "course_title": course["title"], "image": course.get("image", ""),
            "completed": completed, "total": total, "progress_pct": round((completed / total) * 100),
            "next_lesson": next_lesson,
        })
    return result

@api_router.get("/progress/{course_id}")
async def get_course_progress(course_id: str, user: dict = Depends(get_current_user)):
    progress = await db.progress.find({"user_id": user["user_id"], "course_id": course_id}, {"_id": 0}).to_list(100)
    return progress

# ---- Certificates ----
@api_router.get("/certificates")
async def get_user_certificates(user: dict = Depends(get_current_user)):
    return await db.certificates.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(50)

@api_router.get("/verify/{certificate_id}")
async def verify_certificate(certificate_id: str):
    cert = await db.certificates.find_one({"certificate_id": certificate_id}, {"_id": 0})
    if not cert: raise HTTPException(status_code=404, detail="Certificate not found")
    return cert

# ---- Quizzes ----
@api_router.post("/admin/quizzes")
async def create_quiz(request: Request, admin: dict = Depends(require_admin)):
    body = await request.json()
    quiz_id = f"quiz_{uuid.uuid4().hex[:8]}"
    quiz = {
        "quiz_id": quiz_id, "course_id": body["course_id"], "lesson_id": body.get("lesson_id"),
        "title": body["title"], "pass_percentage": body.get("pass_percentage", 70),
        "questions": body.get("questions", []), "created_at": now_iso(),
    }
    await db.quizzes.insert_one(quiz)
    return await db.quizzes.find_one({"quiz_id": quiz_id}, {"_id": 0})

@api_router.get("/quizzes/{course_id}")
async def get_course_quizzes(course_id: str, user: dict = Depends(get_current_user)):
    quizzes = await db.quizzes.find({"course_id": course_id}, {"_id": 0}).to_list(50)
    for q in quizzes:
        attempt = await db.quiz_attempts.find_one({"user_id": user["user_id"], "quiz_id": q["quiz_id"]}, {"_id": 0, "answers": 0})
        q["last_attempt"] = attempt
    return quizzes

@api_router.post("/quizzes/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    answers = body.get("answers", {})
    quiz = await db.quizzes.find_one({"quiz_id": quiz_id}, {"_id": 0})
    if not quiz: raise HTTPException(status_code=404, detail="Quiz not found")
    correct = 0
    total = len(quiz.get("questions", []))
    for q in quiz["questions"]:
        if answers.get(q["question_id"]) == q.get("correct_answer"):
            correct += 1
    score = round((correct / total) * 100) if total > 0 else 0
    passed = score >= quiz.get("pass_percentage", 70)
    attempt_id = f"att_{uuid.uuid4().hex[:8]}"
    await db.quiz_attempts.insert_one({
        "attempt_id": attempt_id, "user_id": user["user_id"], "quiz_id": quiz_id,
        "course_id": quiz["course_id"], "score": score, "correct": correct, "total": total,
        "passed": passed, "answers": answers, "created_at": now_iso(),
    })
    if passed:
        await add_xp(user["user_id"], XP_QUIZ_PASS, f"Quiz passed: {quiz['title']}")
        await add_notification(user["user_id"], "Quiz Passed!", f"You scored {score}% on {quiz['title']}", "quiz")
    return {"score": score, "correct": correct, "total": total, "passed": passed, "pass_percentage": quiz.get("pass_percentage", 70)}

# ---- Reviews ----
@api_router.post("/reviews")
async def add_review(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    course_id = body["course_id"]
    existing = await db.reviews.find_one({"user_id": user["user_id"], "course_id": course_id})
    if existing: raise HTTPException(status_code=400, detail="You already reviewed this course")
    purchase = await db.purchases.find_one({"user_id": user["user_id"], "course_id": course_id})
    if not purchase: raise HTTPException(status_code=403, detail="Purchase required to review")
    review_id = f"rev_{uuid.uuid4().hex[:8]}"
    await db.reviews.insert_one({
        "review_id": review_id, "user_id": user["user_id"], "user_name": user["name"],
        "user_picture": user.get("picture", ""), "course_id": course_id,
        "rating": body["rating"], "comment": body.get("comment", ""),
        "verified": True, "created_at": now_iso(),
    })
    await add_xp(user["user_id"], XP_REVIEW, "Left a review")
    return {"review_id": review_id}

@api_router.get("/reviews/{course_id}")
async def get_reviews(course_id: str):
    return await db.reviews.find({"course_id": course_id}, {"_id": 0}).sort("created_at", -1).to_list(100)

# ---- Coupons ----
@api_router.post("/admin/coupons")
async def create_coupon(request: Request, admin: dict = Depends(require_admin)):
    body = await request.json()
    coupon = {
        "coupon_id": f"cpn_{uuid.uuid4().hex[:8]}", "code": body["code"].upper(),
        "discount_type": body.get("discount_type", "percent"),
        "discount_value": body["discount_value"],
        "max_uses": body.get("max_uses", 100), "used_count": 0,
        "expiry_date": body.get("expiry_date"), "applicable_courses": body.get("applicable_courses", []),
        "active": True, "created_at": now_iso(),
    }
    await db.coupons.insert_one(coupon)
    return await db.coupons.find_one({"coupon_id": coupon["coupon_id"]}, {"_id": 0})

@api_router.get("/admin/coupons")
async def list_coupons(admin: dict = Depends(require_admin)):
    return await db.coupons.find({}, {"_id": 0}).to_list(100)

@api_router.post("/coupons/validate")
async def validate_coupon(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    code = body.get("code", "").upper()
    course_id = body.get("course_id")
    coupon = await db.coupons.find_one({"code": code, "active": True}, {"_id": 0})
    if not coupon: raise HTTPException(status_code=404, detail="Invalid coupon")
    if coupon.get("expiry_date") and coupon["expiry_date"] < now_iso():
        raise HTTPException(status_code=400, detail="Coupon expired")
    if coupon["used_count"] >= coupon["max_uses"]:
        raise HTTPException(status_code=400, detail="Coupon usage limit reached")
    if coupon.get("applicable_courses") and course_id not in coupon["applicable_courses"]:
        raise HTTPException(status_code=400, detail="Coupon not valid for this course")
    return coupon

# ---- Notifications ----
@api_router.get("/notifications")
async def get_notifications(user: dict = Depends(get_current_user)):
    return await db.notifications.find({"user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(50)

@api_router.get("/notifications/unread-count")
async def get_unread_count(user: dict = Depends(get_current_user)):
    count = await db.notifications.count_documents({"user_id": user["user_id"], "read": False})
    return {"count": count}

@api_router.post("/notifications/mark-read")
async def mark_notifications_read(user: dict = Depends(get_current_user)):
    await db.notifications.update_many({"user_id": user["user_id"], "read": False}, {"$set": {"read": True}})
    return {"message": "All marked as read"}

# ---- Leaderboard ----
@api_router.get("/leaderboard")
async def get_leaderboard(period: str = "all"):
    match_stage = {}
    if period == "monthly":
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0).isoformat()
        match_stage = {"created_at": {"$gte": month_start}}
    elif period == "weekly":
        week_start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        match_stage = {"created_at": {"$gte": week_start}}
    pipeline = [
        {"$match": match_stage} if match_stage else {"$match": {}},
        {"$group": {"_id": "$to_user_id", "total_earned": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total_earned": -1}}, {"$limit": 20},
    ]
    results = await db.commissions.aggregate(pipeline).to_list(20)
    leaderboard = []
    for idx, r in enumerate(results):
        user = await db.users.find_one({"user_id": r["_id"]}, {"_id": 0, "user_id": 1, "name": 1, "picture": 1, "xp": 1})
        if not user: continue
        total_refs = await db.users.count_documents({"referred_by": r["_id"]})
        badge = "none"
        if total_refs >= 100: badge = "diamond"
        elif total_refs >= 50: badge = "gold"
        elif total_refs >= 20: badge = "silver"
        elif total_refs >= 5: badge = "bronze"
        leaderboard.append({
            "rank": idx + 1, "user_id": user["user_id"], "name": user.get("name", ""),
            "picture": user.get("picture", ""), "xp": user.get("xp", 0),
            "total_earned": r["total_earned"], "total_referrals": total_refs, "badge": badge,
        })
    return leaderboard

@api_router.get("/leaderboard/my-rank")
async def get_my_rank(user: dict = Depends(get_current_user)):
    pipeline = [
        {"$group": {"_id": "$to_user_id", "total_earned": {"$sum": "$amount"}}},
        {"$sort": {"total_earned": -1}},
    ]
    all_earners = await db.commissions.aggregate(pipeline).to_list(1000)
    rank = 0
    my_earned = 0
    for idx, e in enumerate(all_earners):
        if e["_id"] == user["user_id"]:
            rank = idx + 1
            my_earned = e["total_earned"]
            break
    total_refs = await db.users.count_documents({"referred_by": user["user_id"]})
    badge = "none"
    if total_refs >= 100: badge = "diamond"
    elif total_refs >= 50: badge = "gold"
    elif total_refs >= 20: badge = "silver"
    elif total_refs >= 5: badge = "bronze"
    return {"rank": rank, "total_earned": my_earned, "total_referrals": total_refs, "badge": badge, "xp": user.get("xp", 0), "streak": user.get("streak", 0)}

# ---- Analytics ----
@api_router.get("/analytics/earnings")
async def get_earnings_chart(user: dict = Depends(get_current_user)):
    days_30 = []
    now = datetime.now(timezone.utc)
    for i in range(29, -1, -1):
        d = now - timedelta(days=i)
        day_start = d.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        day_end = d.replace(hour=23, minute=59, second=59).isoformat()
        pipeline = [
            {"$match": {"to_user_id": user["user_id"], "created_at": {"$gte": day_start, "$lte": day_end}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]
        result = await db.commissions.aggregate(pipeline).to_list(1)
        days_30.append({"date": d.strftime("%d %b"), "amount": result[0]["total"] if result else 0})
    return days_30

@api_router.get("/analytics/commission-by-level")
async def get_commission_by_level(user: dict = Depends(get_current_user)):
    pipeline = [
        {"$match": {"to_user_id": user["user_id"]}},
        {"$group": {"_id": "$level", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    results = await db.commissions.aggregate(pipeline).to_list(10)
    return [{"level": r["_id"], "total": r["total"], "count": r["count"]} for r in results]

# ---- Referral Landing (public) ----
@api_router.get("/referral/{referral_code}")
async def get_referral_info(referral_code: str):
    referrer = await db.users.find_one({"referral_code": referral_code}, {"_id": 0, "user_id": 1, "name": 1, "picture": 1})
    if not referrer: raise HTTPException(status_code=404, detail="Invalid referral code")
    total_users = await db.users.count_documents({})
    courses = await db.courses.find({"published": True, "is_upsell": False}, {"_id": 0, "course_id": 1, "title": 1, "image": 1, "price": 1, "original_price": 1, "category": 1}).to_list(10)
    # Track click
    await db.referral_clicks.insert_one({"referral_code": referral_code, "created_at": now_iso()})
    return {"referrer": referrer, "total_students": total_users, "courses": courses}

# ---- Streaks ----
@api_router.get("/streaks")
async def get_streak(user: dict = Depends(get_current_user)):
    return {"streak": user.get("streak", 0), "xp": user.get("xp", 0), "last_streak_date": user.get("last_streak_date")}

# ---- Wallet / Payouts / Referral Stats (keep existing) ----
@api_router.get("/referrals/stats")
async def get_referral_stats(user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_start = (now - timedelta(days=7)).isoformat()
    pipelines = {
        "today": [{"$match": {"to_user_id": user["user_id"], "created_at": {"$gte": today_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}],
        "week": [{"$match": {"to_user_id": user["user_id"], "created_at": {"$gte": week_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}],
        "lifetime": [{"$match": {"to_user_id": user["user_id"]}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}],
    }
    today_r = await db.commissions.aggregate(pipelines["today"]).to_list(1)
    week_r = await db.commissions.aggregate(pipelines["week"]).to_list(1)
    life_r = await db.commissions.aggregate(pipelines["lifetime"]).to_list(1)
    total_referred = await db.users.count_documents({"referred_by": user["user_id"]})
    return {
        "earned_today": today_r[0]["total"] if today_r else 0,
        "earned_week": week_r[0]["total"] if week_r else 0,
        "earned_lifetime": life_r[0]["total"] if life_r else 0,
        "total_referred": total_referred,
    }

@api_router.get("/referrals/users")
async def get_referred_users(status: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {"referred_by": user["user_id"]}
    if status and status != "all": query["status"] = status
    referred = await db.users.find(query, {"_id": 0}).to_list(200)
    result = []
    for ref in referred:
        commissions = await db.commissions.find({"to_user_id": user["user_id"], "from_user_id": ref["user_id"]}, {"_id": 0}).to_list(100)
        purchases = await db.purchases.find({"user_id": ref["user_id"]}, {"_id": 0}).to_list(100)
        result.append({
            "user_id": ref["user_id"], "name": ref.get("name", ""), "email": ref.get("email", ""),
            "phone": ref.get("phone", ""), "status": ref.get("status", "pending"),
            "created_at": ref.get("created_at", ""), "purchases": purchases,
            "commissions": commissions, "total_commission": sum(c["amount"] for c in commissions),
        })
    return result

@api_router.get("/referrals/counts")
async def get_referral_counts(user: dict = Depends(get_current_user)):
    pending = await db.users.count_documents({"referred_by": user["user_id"], "status": {"$in": ["pending", None]}})
    active = await db.users.count_documents({"referred_by": user["user_id"], "status": "active"})
    churned = await db.users.count_documents({"referred_by": user["user_id"], "status": "churned"})
    return {"pending": pending, "active": active, "churned": churned, "total": pending + active + churned}

# ---- Referral Tree (Batch 3) ----
async def build_referral_tree_node(user_id: str, depth: int = 0, max_depth: int = 7):
    """Recursively build referral tree for visualization"""
    if depth >= max_depth:
        return None
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "user_id": 1, "name": 1, "picture": 1, "email": 1, "status": 1, "created_at": 1})
    if not user:
        return None
    # Get direct referrals
    direct_refs = await db.users.find({"referred_by": user_id}, {"_id": 0, "user_id": 1}).to_list(100)
    # Get total earnings from this user's subtree
    pipeline = [{"$match": {"from_user_id": user_id}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    earnings = await db.commissions.aggregate(pipeline).to_list(1)
    total_earned = earnings[0]["total"] if earnings else 0
    children = []
    for ref in direct_refs:
        child = await build_referral_tree_node(ref["user_id"], depth + 1, max_depth)
        if child:
            children.append(child)
    return {
        "name": user.get("name", "Unknown"),
        "attributes": {
            "level": depth,
            "status": user.get("status", "pending"),
            "earned": total_earned,
            "joined": user.get("created_at", "")[:10] if user.get("created_at") else "",
        },
        "user_id": user_id,
        "picture": user.get("picture", ""),
        "email": user.get("email", ""),
        "children": children if children else None,
    }

@api_router.get("/referrals/tree")
async def get_referral_tree(user: dict = Depends(get_current_user)):
    tree = await build_referral_tree_node(user["user_id"], 0, 7)
    if not tree:
        return {"name": user["name"], "attributes": {"level": 0, "status": "active"}, "children": None}
    return tree

@api_router.get("/referrals/tree-stats")
async def get_referral_tree_stats(user: dict = Depends(get_current_user)):
    """Get summary stats for referral tree"""
    counts_by_level = []
    for level in range(1, 8):
        # Find users at this level in the chain
        count = await db.users.count_documents({f"referral_chain.{level-1}": user["user_id"]})
        if level == 1:
            count = await db.users.count_documents({"referred_by": user["user_id"]})
        counts_by_level.append({"level": level, "count": count})
    total_network = sum(c["count"] for c in counts_by_level)
    pipeline = [{"$match": {"to_user_id": user["user_id"]}}, {"$group": {"_id": "$level", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}]
    earnings_by_level = await db.commissions.aggregate(pipeline).to_list(10)
    earnings_map = {e["_id"]: {"amount": e["total"], "transactions": e["count"]} for e in earnings_by_level}
    return {"total_network": total_network, "by_level": counts_by_level, "earnings_by_level": earnings_map}

@api_router.get("/wallet")
async def get_wallet(user: dict = Depends(get_current_user)):
    wallet = await db.wallets.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return wallet or {"user_id": user["user_id"], "balance": 0, "total_earned": 0, "total_withdrawn": 0}

# TDS (Tax Deducted at Source) rate - 10% for commissions above threshold
TDS_RATE = 0.10
TDS_THRESHOLD = 5000  # No TDS below this amount

def calculate_tds(amount: float) -> dict:
    """Calculate TDS deduction for payout"""
    if amount < TDS_THRESHOLD:
        return {"gross": amount, "tds": 0, "net": amount, "tds_rate": 0}
    tds = round(amount * TDS_RATE, 2)
    return {"gross": amount, "tds": tds, "net": round(amount - tds, 2), "tds_rate": TDS_RATE * 100}

@api_router.post("/wallet/payout/preview")
async def preview_payout(request: Request, user: dict = Depends(get_current_user)):
    """Preview payout with TDS calculation before confirming"""
    body = await request.json()
    amount = body.get("amount", 0)
    wallet = await db.wallets.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not wallet or wallet.get("balance", 0) < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    if amount < MIN_WITHDRAWAL:
        raise HTTPException(status_code=400, detail=f"Minimum withdrawal is ₹{MIN_WITHDRAWAL}")
    calc = calculate_tds(amount)
    # Estimated processing date (next business day + 2 days)
    est_date = datetime.now(timezone.utc) + timedelta(days=3)
    while est_date.weekday() >= 5:  # Skip weekends
        est_date += timedelta(days=1)
    return {
        **calc,
        "estimated_date": est_date.strftime("%d %b %Y"),
        "processing_days": "2-3 business days",
    }

@api_router.post("/wallet/payout")
async def request_payout(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    amount = body.get("amount", 0)
    bank_details = body.get("bank_details", {})
    wallet = await db.wallets.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not wallet or wallet.get("balance", 0) < amount: raise HTTPException(status_code=400, detail="Insufficient balance")
    if amount < MIN_WITHDRAWAL: raise HTTPException(status_code=400, detail=f"Minimum withdrawal is ₹{MIN_WITHDRAWAL}")
    calc = calculate_tds(amount)
    payout_id = f"pay_{uuid.uuid4().hex[:12]}"
    est_date = datetime.now(timezone.utc) + timedelta(days=3)
    while est_date.weekday() >= 5:
        est_date += timedelta(days=1)
    await db.payouts.insert_one({
        "payout_id": payout_id, "user_id": user["user_id"],
        "gross_amount": calc["gross"], "tds_amount": calc["tds"], "net_amount": calc["net"],
        "amount": calc["net"],  # backwards compatibility
        "tds_rate": calc["tds_rate"],
        "bank_details": bank_details,
        "status": "pending", "created_at": now_iso(),
        "estimated_date": est_date.isoformat(),
        "processed_at": None,
    })
    await db.wallets.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": -amount, "total_withdrawn": amount}})
    await add_notification(user["user_id"], "Payout Requested", f"₹{calc['net']} payout requested. Expected by {est_date.strftime('%d %b %Y')}", "payout")
    return {"payout_id": payout_id, "gross": calc["gross"], "tds": calc["tds"], "net": calc["net"], "status": "pending", "estimated_date": est_date.strftime("%d %b %Y")}

@api_router.get("/wallet/payouts/{payout_id}/receipt")
async def get_payout_receipt(payout_id: str, user: dict = Depends(get_current_user)):
    """Generate receipt data for a payout (for PDF generation on frontend)"""
    payout = await db.payouts.find_one({"payout_id": payout_id, "user_id": user["user_id"]}, {"_id": 0})
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    return {
        "receipt_id": f"REC-{payout_id.upper()}",
        "payout_id": payout_id,
        "user_name": user["name"],
        "user_email": user["email"],
        "gross_amount": payout.get("gross_amount", payout.get("amount", 0)),
        "tds_amount": payout.get("tds_amount", 0),
        "tds_rate": payout.get("tds_rate", 0),
        "net_amount": payout.get("net_amount", payout.get("amount", 0)),
        "status": payout["status"],
        "requested_date": payout.get("created_at", "")[:10],
        "estimated_date": payout.get("estimated_date", "")[:10] if payout.get("estimated_date") else "",
        "processed_date": payout.get("processed_at", "")[:10] if payout.get("processed_at") else "",
        "platform": "Mera Mentor",
        "pan_note": "TDS deducted as per Income Tax Act. Please keep this for your tax records.",
    }

@api_router.get("/wallet/transactions")
async def get_transactions(user: dict = Depends(get_current_user)):
    commissions = await db.commissions.find({"to_user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    payouts = await db.payouts.find({"user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"commissions": commissions, "payouts": payouts}

@api_router.get("/commission-levels")
async def get_commission_levels():
    return {"levels": [{"level": k, "percentage": v * 100, "example_earning": round(500 * v, 2)} for k, v in COMMISSION_LEVELS.items()], "min_withdrawal": MIN_WITHDRAWAL, "base_course_price": 500}

# ---- Payment ----
@api_router.post("/payments/create-order")
async def create_payment_order(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    course_id = body.get("course_id")
    coupon_code = body.get("coupon_code")
    course = await db.courses.find_one({"course_id": course_id}, {"_id": 0})
    if not course: raise HTTPException(status_code=404, detail="Course not found")
    amount = course["price"]
    discount = 0
    if coupon_code:
        coupon = await db.coupons.find_one({"code": coupon_code.upper(), "active": True}, {"_id": 0})
        if coupon:
            if coupon["discount_type"] == "percent":
                discount = round(amount * coupon["discount_value"] / 100, 2)
            else:
                discount = coupon["discount_value"]
            amount = max(amount - discount, 0)
            await db.coupons.update_one({"code": coupon_code.upper()}, {"$inc": {"used_count": 1}})
    amount_paise = int(amount * 100)
    order_id = f"order_{uuid.uuid4().hex[:12]}"
    if RAZORPAY_ENABLED:
        rz_order = razorpay_client.order.create({"amount": amount_paise, "currency": "INR", "payment_capture": 1})
        order_id = rz_order["id"]
    await db.orders.insert_one({"order_id": order_id, "user_id": user["user_id"], "course_id": course_id, "amount": amount, "discount": discount, "amount_paise": amount_paise, "status": "created", "razorpay_enabled": RAZORPAY_ENABLED, "created_at": now_iso()})
    return {"order_id": order_id, "amount": amount_paise, "currency": "INR", "course_title": course["title"], "razorpay_enabled": RAZORPAY_ENABLED, "razorpay_key_id": RAZORPAY_KEY_ID if RAZORPAY_ENABLED else None, "discount": discount}

@api_router.post("/payments/verify")
async def verify_payment(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    order_id, course_id = body.get("order_id"), body.get("course_id")
    is_upsell = body.get("is_upsell", False)
    order = await db.orders.find_one({"order_id": order_id}, {"_id": 0})
    if not order: raise HTTPException(status_code=404, detail="Order not found")
    if RAZORPAY_ENABLED:
        try:
            razorpay_client.utility.verify_payment_signature({"razorpay_order_id": body.get("razorpay_order_id", order_id), "razorpay_payment_id": body.get("razorpay_payment_id", ""), "razorpay_signature": body.get("razorpay_signature", "")})
        except Exception:
            raise HTTPException(status_code=400, detail="Payment verification failed")
    await db.orders.update_one({"order_id": order_id}, {"$set": {"status": "paid", "paid_at": now_iso()}})
    course = await db.courses.find_one({"course_id": course_id}, {"_id": 0})
    amount = order["amount"]
    purchase_id = f"pur_{uuid.uuid4().hex[:12]}"
    await db.purchases.insert_one({"purchase_id": purchase_id, "user_id": user["user_id"], "course_id": course_id, "course_title": course["title"] if course else "", "amount": amount, "is_upsell": is_upsell, "order_id": order_id, "created_at": now_iso()})
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"status": "active"}})
    referral_chain = user.get("referral_chain", [])
    for level_idx, ancestor_id in enumerate(referral_chain):
        level = level_idx + 1
        if level > 7: break
        rate = COMMISSION_LEVELS.get(level, 0)
        commission_amount = round(amount * rate, 2)
        if commission_amount <= 0: continue
        commission_id = f"com_{uuid.uuid4().hex[:12]}"
        await db.commissions.insert_one({"commission_id": commission_id, "from_user_id": user["user_id"], "from_user_name": user["name"], "to_user_id": ancestor_id, "purchase_id": purchase_id, "course_id": course_id, "course_title": course["title"] if course else "", "amount": commission_amount, "level": level, "status": "approved", "created_at": now_iso()})
        await db.wallets.update_one({"user_id": ancestor_id}, {"$inc": {"balance": commission_amount, "total_earned": commission_amount}, "$setOnInsert": {"total_withdrawn": 0}}, upsert=True)
        ancestor = await db.users.find_one({"user_id": ancestor_id}, {"_id": 0, "name": 1})
        await add_notification(ancestor_id, f"Commission Earned!", f"₹{commission_amount} from {user['name']}'s purchase of {course['title'] if course else 'a course'} (Level {level})", "commission")
    return {"purchase_id": purchase_id, "amount": amount, "course_title": course["title"] if course else ""}

@api_router.get("/purchases")
async def get_purchases(user: dict = Depends(get_current_user)):
    return await db.purchases.find({"user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)

# ---- Admin ----
@api_router.post("/admin/courses")
async def create_course(request: Request, admin: dict = Depends(require_admin)):
    body = await request.json()
    course_id = f"course_{uuid.uuid4().hex[:10]}"
    course = {"course_id": course_id, "title": body["title"], "description": body.get("description", ""), "price": body["price"], "original_price": body.get("original_price", body["price"]), "image": body.get("image", "https://images.unsplash.com/photo-1562813733-b31f71025d54?w=600"), "category": body.get("category", "General"), "tier": body.get("tier", "standard"), "is_upsell": body.get("is_upsell", False), "upsell_for": body.get("upsell_for"), "lessons": body.get("lessons", []), "resources": body.get("resources", []), "created_by": admin["user_id"], "created_at": now_iso(), "updated_at": now_iso(), "published": body.get("published", True)}
    for i, l in enumerate(course["lessons"]):
        l["lesson_id"] = f"les_{uuid.uuid4().hex[:8]}"; l["order"] = i + 1
    await db.courses.insert_one(course)
    return await db.courses.find_one({"course_id": course_id}, {"_id": 0})

@api_router.put("/admin/courses/{course_id}")
async def update_course(course_id: str, request: Request, admin: dict = Depends(require_admin)):
    body = await request.json()
    existing = await db.courses.find_one({"course_id": course_id}, {"_id": 0})
    if not existing: raise HTTPException(status_code=404, detail="Course not found")
    updates = {}
    for f in ["title", "description", "price", "original_price", "image", "category", "tier", "is_upsell", "upsell_for", "lessons", "resources", "published"]:
        if f in body: updates[f] = body[f]
    if "lessons" in updates:
        for i, l in enumerate(updates["lessons"]):
            if not l.get("lesson_id"): l["lesson_id"] = f"les_{uuid.uuid4().hex[:8]}"
            l["order"] = i + 1
    updates["updated_at"] = now_iso()
    await db.courses.update_one({"course_id": course_id}, {"$set": updates})
    return await db.courses.find_one({"course_id": course_id}, {"_id": 0})

@api_router.delete("/admin/courses/{course_id}")
async def delete_course(course_id: str, admin: dict = Depends(require_admin)):
    r = await db.courses.delete_one({"course_id": course_id})
    if r.deleted_count == 0: raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Deleted"}

@api_router.get("/admin/stats")
async def admin_stats(admin: dict = Depends(require_admin)):
    total_users = await db.users.count_documents({})
    total_purchases = await db.purchases.count_documents({})
    rev = await db.purchases.aggregate([{"$group": {"_id": None, "total": {"$sum": "$amount"}}}]).to_list(1)
    com = await db.commissions.aggregate([{"$group": {"_id": None, "total": {"$sum": "$amount"}}}]).to_list(1)
    return {"total_users": total_users, "total_purchases": total_purchases, "total_revenue": rev[0]["total"] if rev else 0, "total_commissions": com[0]["total"] if com else 0}

# ---- Seed Data ----
@app.on_event("startup")
async def seed_data():
    count = await db.courses.count_documents({})
    if count == 0:
        courses = [
            {"course_id": "course_web_dev", "title": "Web Development Bootcamp", "description": "Learn HTML, CSS, JavaScript, React and Node.js from scratch. Build real-world projects.", "price": 499, "original_price": 999, "image": "https://images.unsplash.com/photo-1562813733-b31f71025d54?w=600", "category": "Development", "tier": "standard", "is_upsell": False, "upsell_for": None, "published": True, "created_at": now_iso(), "updated_at": now_iso(), "lessons": [{"lesson_id": "les_001", "title": "Introduction to Web Dev", "description": "Overview of modern web development", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "15 min", "order": 1}, {"lesson_id": "les_002", "title": "HTML Fundamentals", "description": "Learn HTML tags and semantics", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "25 min", "order": 2}, {"lesson_id": "les_003", "title": "CSS Styling & Layouts", "description": "Master CSS flexbox, grid", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "30 min", "order": 3}], "resources": [{"name": "HTML Cheat Sheet", "type": "pdf", "url": "#"}, {"name": "CSS Reference Guide", "type": "pdf", "url": "#"}]},
            {"course_id": "course_data_science", "title": "Data Science Masterclass", "description": "Master Python, Pandas, ML and AI. Work on 10+ real datasets.", "price": 599, "original_price": 1199, "image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600", "category": "Data Science", "tier": "standard", "is_upsell": False, "upsell_for": None, "published": True, "created_at": now_iso(), "updated_at": now_iso(), "lessons": [{"lesson_id": "les_004", "title": "Python for Data Science", "description": "Python basics", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "20 min", "order": 1}, {"lesson_id": "les_005", "title": "Pandas & NumPy", "description": "Data manipulation", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "35 min", "order": 2}], "resources": [{"name": "Python Handbook", "type": "pdf", "url": "#"}]},
            {"course_id": "course_mobile_dev", "title": "Mobile App Development", "description": "Build iOS and Android apps with React Native.", "price": 449, "original_price": 899, "image": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=600", "category": "Development", "tier": "standard", "is_upsell": False, "upsell_for": None, "published": True, "created_at": now_iso(), "updated_at": now_iso(), "lessons": [{"lesson_id": "les_006", "title": "React Native Setup", "description": "Setting up environment", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "18 min", "order": 1}], "resources": []},
            {"course_id": "course_digital_marketing", "title": "Digital Marketing Pro", "description": "SEO, Google Ads, Facebook Ads, Content Marketing.", "price": 399, "original_price": 799, "image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600", "category": "Marketing", "tier": "standard", "is_upsell": False, "upsell_for": None, "published": True, "created_at": now_iso(), "updated_at": now_iso(), "lessons": [{"lesson_id": "les_007", "title": "SEO Fundamentals", "description": "SEO basics", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "22 min", "order": 1}], "resources": []},
            {"course_id": "course_ui_ux", "title": "UI/UX Design Fundamentals", "description": "Learn Figma, design systems, user research.", "price": 349, "original_price": 699, "image": "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=600", "category": "Design", "tier": "standard", "is_upsell": False, "upsell_for": None, "published": True, "created_at": now_iso(), "updated_at": now_iso(), "lessons": [{"lesson_id": "les_008", "title": "Design Thinking", "description": "Design thinking methodology", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "20 min", "order": 1}], "resources": []},
            {"course_id": "course_full_stack_bundle", "title": "Full Stack Developer Bundle", "description": "Web Dev + Data Science + Mobile Dev. Save 60%.", "price": 999, "original_price": 2497, "image": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=600", "category": "Bundle", "tier": "premium", "is_upsell": True, "upsell_for": "course_web_dev", "published": True, "created_at": now_iso(), "updated_at": now_iso(), "lessons": [], "resources": []},
            {"course_id": "course_ai_bundle", "title": "AI & Data Complete Bundle", "description": "Data Science + AI/ML + Deep Learning + NLP.", "price": 899, "original_price": 2097, "image": "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=600", "category": "Bundle", "tier": "premium", "is_upsell": True, "upsell_for": "course_data_science", "published": True, "created_at": now_iso(), "updated_at": now_iso(), "lessons": [], "resources": []},
        ]
        await db.courses.insert_many(courses)
        logging.info("Seeded courses data")
    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("email", unique=True)
    await db.users.create_index("referral_code", unique=True)
    await db.users.create_index("referred_by")
    await db.commissions.create_index("to_user_id")
    await db.commissions.create_index("from_user_id")
    await db.purchases.create_index("user_id")
    await db.orders.create_index("order_id")
    await db.progress.create_index([("user_id", 1), ("course_id", 1), ("lesson_id", 1)], unique=True)
    await db.notifications.create_index("user_id")
    await db.certificates.create_index("certificate_id", unique=True)

app.include_router(api_router)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','), allow_methods=["*"], allow_headers=["*"])
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
