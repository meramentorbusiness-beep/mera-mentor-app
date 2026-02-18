from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import httpx
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
import hashlib
import hmac
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Razorpay config (mock mode if keys not set)
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
RAZORPAY_ENABLED = bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)

razorpay_client = None
if RAZORPAY_ENABLED:
    import razorpay
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Commission percentages per level
COMMISSION_LEVELS = {
    1: 0.40, 2: 0.20, 3: 0.10, 4: 0.05, 5: 0.03, 6: 0.015, 7: 0.005,
}
MIN_WITHDRAWAL = 100

# Admin emails
ADMIN_EMAILS = os.environ.get("ADMIN_EMAILS", "").split(",")

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

def generate_referral_code():
    return "MM" + uuid.uuid4().hex[:8].upper()

def now_iso():
    return datetime.now(timezone.utc).isoformat()

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
    email = data["email"]
    name = data["name"]
    picture = data.get("picture", "")
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
        is_admin = email.strip() in [e.strip() for e in ADMIN_EMAILS if e.strip()]
        await db.users.insert_one({
            "user_id": user_id, "email": email, "name": name, "picture": picture,
            "phone": "", "referral_code": ref_code, "referred_by": referred_by_user,
            "referral_chain": referral_chain, "status": "pending",
            "is_admin": is_admin, "created_at": now_iso(),
        })
    await db.user_sessions.insert_one({
        "user_id": user_id, "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": now_iso(),
    })
    response.set_cookie(
        key="session_token", value=session_token,
        httponly=True, secure=True, samesite="none", path="/", max_age=7*24*3600
    )
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if user and "created_at" in user and not isinstance(user["created_at"], str):
        user["created_at"] = user["created_at"].isoformat()
    return user

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    if "created_at" in user and not isinstance(user["created_at"], str):
        user["created_at"] = user["created_at"].isoformat()
    return user

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    response.delete_cookie("session_token", path="/", samesite="none", secure=True)
    return {"message": "Logged out"}

@api_router.put("/auth/profile")
async def update_profile(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    updates = {}
    if "phone" in body:
        updates["phone"] = body["phone"]
    if "name" in body:
        updates["name"] = body["name"]
    if updates:
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": updates})
    return await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})

# ---- Admin Course Management ----

@api_router.post("/admin/courses")
async def create_course(request: Request, admin: dict = Depends(require_admin)):
    body = await request.json()
    course_id = f"course_{uuid.uuid4().hex[:10]}"
    course = {
        "course_id": course_id,
        "title": body["title"],
        "description": body.get("description", ""),
        "price": body["price"],
        "original_price": body.get("original_price", body["price"]),
        "image": body.get("image", "https://images.unsplash.com/photo-1562813733-b31f71025d54?w=600"),
        "category": body.get("category", "General"),
        "tier": body.get("tier", "standard"),
        "is_upsell": body.get("is_upsell", False),
        "upsell_for": body.get("upsell_for"),
        "lessons": body.get("lessons", []),
        "resources": body.get("resources", []),
        "created_by": admin["user_id"],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "published": body.get("published", True),
    }
    # Validate lessons structure
    for i, lesson in enumerate(course["lessons"]):
        lesson["lesson_id"] = f"les_{uuid.uuid4().hex[:8]}"
        lesson["order"] = i + 1
    await db.courses.insert_one(course)
    created = await db.courses.find_one({"course_id": course_id}, {"_id": 0})
    return created

@api_router.put("/admin/courses/{course_id}")
async def update_course(course_id: str, request: Request, admin: dict = Depends(require_admin)):
    body = await request.json()
    existing = await db.courses.find_one({"course_id": course_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Course not found")
    updates = {}
    for field in ["title", "description", "price", "original_price", "image", "category", "tier",
                   "is_upsell", "upsell_for", "lessons", "resources", "published"]:
        if field in body:
            updates[field] = body[field]
    if "lessons" in updates:
        for i, lesson in enumerate(updates["lessons"]):
            if not lesson.get("lesson_id"):
                lesson["lesson_id"] = f"les_{uuid.uuid4().hex[:8]}"
            lesson["order"] = i + 1
    updates["updated_at"] = now_iso()
    await db.courses.update_one({"course_id": course_id}, {"$set": updates})
    return await db.courses.find_one({"course_id": course_id}, {"_id": 0})

@api_router.delete("/admin/courses/{course_id}")
async def delete_course(course_id: str, admin: dict = Depends(require_admin)):
    result = await db.courses.delete_one({"course_id": course_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted"}

@api_router.get("/admin/users")
async def list_all_users(admin: dict = Depends(require_admin)):
    users = await db.users.find({}, {"_id": 0}).to_list(500)
    return users

@api_router.get("/admin/stats")
async def admin_stats(admin: dict = Depends(require_admin)):
    total_users = await db.users.count_documents({})
    total_purchases = await db.purchases.count_documents({})
    revenue_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    revenue_result = await db.purchases.aggregate(revenue_pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    commission_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    commission_result = await db.commissions.aggregate(commission_pipeline).to_list(1)
    total_commissions = commission_result[0]["total"] if commission_result else 0
    return {
        "total_users": total_users, "total_purchases": total_purchases,
        "total_revenue": total_revenue, "total_commissions": total_commissions,
    }

# ---- Course Routes ----

@api_router.get("/courses")
async def list_courses():
    courses = await db.courses.find({"published": {"$ne": False}}, {"_id": 0}).to_list(100)
    # Strip lesson video URLs for listing (protection)
    for course in courses:
        if "lessons" in course:
            course["lesson_count"] = len(course["lessons"])
            for lesson in course["lessons"]:
                lesson.pop("video_url", None)
    return courses

@api_router.get("/courses/{course_id}")
async def get_course(course_id: str):
    course = await db.courses.find_one({"course_id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    # Strip video URLs from public view
    if "lessons" in course:
        course["lesson_count"] = len(course["lessons"])
        for lesson in course["lessons"]:
            lesson.pop("video_url", None)
    return course

@api_router.get("/courses/{course_id}/lessons")
async def get_course_lessons(course_id: str, user: dict = Depends(get_current_user)):
    """Protected: only return video URLs to users who purchased the course"""
    course = await db.courses.find_one({"course_id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    # Check if user purchased this course or is admin
    if not user.get("is_admin", False):
        purchase = await db.purchases.find_one(
            {"user_id": user["user_id"], "course_id": course_id}, {"_id": 0}
        )
        if not purchase:
            raise HTTPException(status_code=403, detail="Purchase required to access lessons")
    return {"lessons": course.get("lessons", []), "resources": course.get("resources", [])}

@api_router.get("/courses/{course_id}/upsell")
async def get_upsell(course_id: str):
    upsell = await db.courses.find_one({"upsell_for": course_id, "is_upsell": True}, {"_id": 0})
    return upsell

# ---- Payment / Purchase Routes ----

@api_router.post("/payments/create-order")
async def create_payment_order(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    course_id = body.get("course_id")
    course = await db.courses.find_one({"course_id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    amount_paise = int(course["price"] * 100)
    order_id = f"order_{uuid.uuid4().hex[:12]}"
    if RAZORPAY_ENABLED:
        rz_order = razorpay_client.order.create({
            "amount": amount_paise, "currency": "INR", "payment_capture": 1,
            "notes": {"course_id": course_id, "user_id": user["user_id"]}
        })
        order_id = rz_order["id"]
    await db.orders.insert_one({
        "order_id": order_id, "user_id": user["user_id"], "course_id": course_id,
        "amount": course["price"], "amount_paise": amount_paise,
        "status": "created", "razorpay_enabled": RAZORPAY_ENABLED,
        "created_at": now_iso(),
    })
    return {
        "order_id": order_id, "amount": amount_paise, "currency": "INR",
        "course_title": course["title"], "razorpay_enabled": RAZORPAY_ENABLED,
        "razorpay_key_id": RAZORPAY_KEY_ID if RAZORPAY_ENABLED else None,
    }

@api_router.post("/payments/verify")
async def verify_payment(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    order_id = body.get("order_id")
    course_id = body.get("course_id")
    is_upsell = body.get("is_upsell", False)
    order = await db.orders.find_one({"order_id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if RAZORPAY_ENABLED:
        try:
            razorpay_client.utility.verify_payment_signature({
                "razorpay_order_id": body.get("razorpay_order_id", order_id),
                "razorpay_payment_id": body.get("razorpay_payment_id", ""),
                "razorpay_signature": body.get("razorpay_signature", ""),
            })
        except Exception:
            raise HTTPException(status_code=400, detail="Payment verification failed")
    # Mark order as paid
    await db.orders.update_one({"order_id": order_id}, {"$set": {"status": "paid", "paid_at": now_iso()}})
    # Create purchase
    course = await db.courses.find_one({"course_id": course_id}, {"_id": 0})
    amount = course["price"] if course else order["amount"]
    purchase_id = f"pur_{uuid.uuid4().hex[:12]}"
    await db.purchases.insert_one({
        "purchase_id": purchase_id, "user_id": user["user_id"], "course_id": course_id,
        "course_title": course["title"] if course else "", "amount": amount,
        "is_upsell": is_upsell, "order_id": order_id, "created_at": now_iso(),
    })
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"status": "active"}})
    # Process commissions
    referral_chain = user.get("referral_chain", [])
    for level_idx, ancestor_id in enumerate(referral_chain):
        level = level_idx + 1
        if level > 7:
            break
        rate = COMMISSION_LEVELS.get(level, 0)
        commission_amount = round(amount * rate, 2)
        if commission_amount <= 0:
            continue
        commission_id = f"com_{uuid.uuid4().hex[:12]}"
        await db.commissions.insert_one({
            "commission_id": commission_id, "from_user_id": user["user_id"],
            "from_user_name": user["name"], "to_user_id": ancestor_id,
            "purchase_id": purchase_id, "course_id": course_id,
            "course_title": course["title"] if course else "",
            "amount": commission_amount, "level": level, "status": "approved",
            "created_at": now_iso(),
        })
        await db.wallets.update_one(
            {"user_id": ancestor_id},
            {"$inc": {"balance": commission_amount, "total_earned": commission_amount},
             "$setOnInsert": {"total_withdrawn": 0}},
            upsert=True
        )
    return {"purchase_id": purchase_id, "amount": amount, "course_title": course["title"] if course else ""}

@api_router.get("/purchases")
async def get_purchases(user: dict = Depends(get_current_user)):
    purchases = await db.purchases.find({"user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return purchases

# ---- Referral Routes ----

@api_router.get("/referrals/stats")
async def get_referral_stats(user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_start = (now - timedelta(days=7)).isoformat()
    pipeline_today = [
        {"$match": {"to_user_id": user["user_id"], "created_at": {"$gte": today_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    pipeline_week = [
        {"$match": {"to_user_id": user["user_id"], "created_at": {"$gte": week_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    pipeline_lifetime = [
        {"$match": {"to_user_id": user["user_id"]}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    today_result = await db.commissions.aggregate(pipeline_today).to_list(1)
    week_result = await db.commissions.aggregate(pipeline_week).to_list(1)
    lifetime_result = await db.commissions.aggregate(pipeline_lifetime).to_list(1)
    total_referred = await db.users.count_documents({"referred_by": user["user_id"]})
    return {
        "earned_today": today_result[0]["total"] if today_result else 0,
        "earned_week": week_result[0]["total"] if week_result else 0,
        "earned_lifetime": lifetime_result[0]["total"] if lifetime_result else 0,
        "total_referred": total_referred,
    }

@api_router.get("/referrals/users")
async def get_referred_users(status: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {"referred_by": user["user_id"]}
    if status and status != "all":
        query["status"] = status
    referred = await db.users.find(query, {"_id": 0}).to_list(200)
    result = []
    for ref in referred:
        commissions = await db.commissions.find(
            {"to_user_id": user["user_id"], "from_user_id": ref["user_id"]}, {"_id": 0}
        ).to_list(100)
        purchases = await db.purchases.find({"user_id": ref["user_id"]}, {"_id": 0}).to_list(100)
        total_commission = sum(c["amount"] for c in commissions)
        result.append({
            "user_id": ref["user_id"], "name": ref.get("name", ""), "email": ref.get("email", ""),
            "phone": ref.get("phone", ""), "status": ref.get("status", "pending"),
            "created_at": ref.get("created_at", ""), "purchases": purchases,
            "commissions": commissions, "total_commission": total_commission,
        })
    return result

@api_router.get("/referrals/counts")
async def get_referral_counts(user: dict = Depends(get_current_user)):
    pending = await db.users.count_documents({"referred_by": user["user_id"], "status": {"$in": ["pending", None]}})
    active = await db.users.count_documents({"referred_by": user["user_id"], "status": "active"})
    churned = await db.users.count_documents({"referred_by": user["user_id"], "status": "churned"})
    return {"pending": pending, "active": active, "churned": churned, "total": pending + active + churned}

# ---- Wallet Routes ----

@api_router.get("/wallet")
async def get_wallet(user: dict = Depends(get_current_user)):
    wallet = await db.wallets.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not wallet:
        wallet = {"user_id": user["user_id"], "balance": 0, "total_earned": 0, "total_withdrawn": 0}
    return wallet

@api_router.post("/wallet/payout")
async def request_payout(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    amount = body.get("amount", 0)
    wallet = await db.wallets.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not wallet or wallet.get("balance", 0) < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    if amount < MIN_WITHDRAWAL:
        raise HTTPException(status_code=400, detail=f"Minimum withdrawal is ₹{MIN_WITHDRAWAL}")
    payout_id = f"pay_{uuid.uuid4().hex[:12]}"
    await db.payouts.insert_one({
        "payout_id": payout_id, "user_id": user["user_id"], "amount": amount,
        "status": "pending", "created_at": now_iso(), "processed_at": None,
    })
    await db.wallets.update_one(
        {"user_id": user["user_id"]},
        {"$inc": {"balance": -amount, "total_withdrawn": amount}}
    )
    return {"payout_id": payout_id, "amount": amount, "status": "pending"}

@api_router.get("/wallet/transactions")
async def get_transactions(user: dict = Depends(get_current_user)):
    commissions = await db.commissions.find({"to_user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    payouts = await db.payouts.find({"user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"commissions": commissions, "payouts": payouts}

# ---- Commission Levels ----

@api_router.get("/commission-levels")
async def get_commission_levels():
    return {
        "levels": [{"level": k, "percentage": v * 100, "example_earning": round(500 * v, 2)} for k, v in COMMISSION_LEVELS.items()],
        "min_withdrawal": MIN_WITHDRAWAL,
        "base_course_price": 500,
    }

# ---- Seed Data ----

@app.on_event("startup")
async def seed_data():
    count = await db.courses.count_documents({})
    if count == 0:
        courses = [
            {
                "course_id": "course_web_dev", "title": "Web Development Bootcamp",
                "description": "Learn HTML, CSS, JavaScript, React and Node.js from scratch. Build real-world projects and deploy them.",
                "price": 499, "original_price": 999,
                "image": "https://images.unsplash.com/photo-1562813733-b31f71025d54?w=600",
                "category": "Development", "tier": "standard", "is_upsell": False, "upsell_for": None,
                "published": True, "created_at": now_iso(), "updated_at": now_iso(),
                "lessons": [
                    {"lesson_id": "les_001", "title": "Introduction to Web Development", "description": "Overview of modern web development", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "15 min", "order": 1},
                    {"lesson_id": "les_002", "title": "HTML Fundamentals", "description": "Learn HTML tags, structure and semantics", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "25 min", "order": 2},
                    {"lesson_id": "les_003", "title": "CSS Styling & Layouts", "description": "Master CSS flexbox, grid and responsive design", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "30 min", "order": 3},
                ],
                "resources": [
                    {"name": "HTML Cheat Sheet", "type": "pdf", "url": "#"},
                    {"name": "CSS Reference Guide", "type": "pdf", "url": "#"},
                ],
            },
            {
                "course_id": "course_data_science", "title": "Data Science Masterclass",
                "description": "Master Python, Pandas, Machine Learning and AI. Work on 10+ real datasets and build predictive models.",
                "price": 599, "original_price": 1199,
                "image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600",
                "category": "Data Science", "tier": "standard", "is_upsell": False, "upsell_for": None,
                "published": True, "created_at": now_iso(), "updated_at": now_iso(),
                "lessons": [
                    {"lesson_id": "les_004", "title": "Python for Data Science", "description": "Python basics for data analysis", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "20 min", "order": 1},
                    {"lesson_id": "les_005", "title": "Pandas & NumPy", "description": "Data manipulation with Pandas", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "35 min", "order": 2},
                ],
                "resources": [{"name": "Python Data Science Handbook", "type": "pdf", "url": "#"}],
            },
            {
                "course_id": "course_mobile_dev", "title": "Mobile App Development",
                "description": "Build iOS and Android apps with React Native. Includes publishing to App Store and Google Play.",
                "price": 449, "original_price": 899,
                "image": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=600",
                "category": "Development", "tier": "standard", "is_upsell": False, "upsell_for": None,
                "published": True, "created_at": now_iso(), "updated_at": now_iso(),
                "lessons": [
                    {"lesson_id": "les_006", "title": "React Native Setup", "description": "Setting up your development environment", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "18 min", "order": 1},
                ],
                "resources": [],
            },
            {
                "course_id": "course_digital_marketing", "title": "Digital Marketing Pro",
                "description": "SEO, Google Ads, Facebook Ads, Content Marketing and Analytics. Get certified and grow any business online.",
                "price": 399, "original_price": 799,
                "image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600",
                "category": "Marketing", "tier": "standard", "is_upsell": False, "upsell_for": None,
                "published": True, "created_at": now_iso(), "updated_at": now_iso(),
                "lessons": [
                    {"lesson_id": "les_007", "title": "SEO Fundamentals", "description": "Search engine optimization basics", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "22 min", "order": 1},
                ],
                "resources": [],
            },
            {
                "course_id": "course_ui_ux", "title": "UI/UX Design Fundamentals",
                "description": "Learn Figma, design systems, user research and prototyping. Create beautiful and usable digital products.",
                "price": 349, "original_price": 699,
                "image": "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=600",
                "category": "Design", "tier": "standard", "is_upsell": False, "upsell_for": None,
                "published": True, "created_at": now_iso(), "updated_at": now_iso(),
                "lessons": [
                    {"lesson_id": "les_008", "title": "Design Thinking", "description": "Introduction to design thinking methodology", "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "duration": "20 min", "order": 1},
                ],
                "resources": [],
            },
            {
                "course_id": "course_full_stack_bundle", "title": "Full Stack Developer Bundle",
                "description": "Complete bundle: Web Dev + Data Science + Mobile Dev. Save 60% and become a full-stack powerhouse.",
                "price": 999, "original_price": 2497,
                "image": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=600",
                "category": "Bundle", "tier": "premium", "is_upsell": True, "upsell_for": "course_web_dev",
                "published": True, "created_at": now_iso(), "updated_at": now_iso(),
                "lessons": [], "resources": [],
            },
            {
                "course_id": "course_ai_bundle", "title": "AI & Data Complete Bundle",
                "description": "Data Science + AI/ML + Deep Learning + NLP. The ultimate data career package at an unbeatable price.",
                "price": 899, "original_price": 2097,
                "image": "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=600",
                "category": "Bundle", "tier": "premium", "is_upsell": True, "upsell_for": "course_data_science",
                "published": True, "created_at": now_iso(), "updated_at": now_iso(),
                "lessons": [], "resources": [],
            },
        ]
        await db.courses.insert_many(courses)
        logging.info("Seeded courses data")
    # Indexes
    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("email", unique=True)
    await db.users.create_index("referral_code", unique=True)
    await db.users.create_index("referred_by")
    await db.commissions.create_index("to_user_id")
    await db.commissions.create_index("from_user_id")
    await db.purchases.create_index("user_id")
    await db.orders.create_index("order_id")

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
