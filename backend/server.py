# Mera Mentor - FastAPI Backend with PostgreSQL/Supabase
from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete, and_, or_, desc
from sqlalchemy.orm import selectinload
import os, logging, httpx, uuid, hashlib, hmac, random, asyncio, json, shutil, mimetypes
import razorpay
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import database and models
from lib.database import get_db, init_db, close_db, async_session_maker
from models.models import (
    User, UserSession, Course, Lesson, Resource, Purchase, Commission,
    Payout, CourseProgress, Certificate, Quiz, QuizAttempt, Review,
    Coupon, Notification, MediaAccessLog, EmailLog, Media,
    PurchaseStatus, CommissionStatus, PayoutStatus
)

app = FastAPI(title="Mera Mentor API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")

# Commission levels from environment (5 levels: 40%, 12%, 6%, 3%, 1% = 62% total)
COMMISSION_LEVELS = {
    1: float(os.environ.get("COMMISSION_L1", "40")) / 100,
    2: float(os.environ.get("COMMISSION_L2", "12")) / 100,
    3: float(os.environ.get("COMMISSION_L3", "6")) / 100,
    4: float(os.environ.get("COMMISSION_L4", "3")) / 100,
    5: float(os.environ.get("COMMISSION_L5", "1")) / 100,
}
MIN_WITHDRAWAL = 100
ADMIN_EMAILS = [e.strip() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://meramentor.in")

# Razorpay
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
razorpay_client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# TDS Configuration
TDS_RATE = 0.10
TDS_THRESHOLD = 5000

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def generate_referral_code():
    return "MMM" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))

# ========== Authentication ==========

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[dict]:
    """Get current user from session token"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Find session
    stmt = select(UserSession).where(
        UserSession.session_token == session_token,
        UserSession.expires_at > datetime.now(timezone.utc)
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Get user
    stmt = select(User).where(User.id == session.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {
        "user_id": str(user.id),
        "email": user.email,
        "name": user.name,
        "picture": user.avatar,
        "referral_code": user.referral_code,
        "is_admin": user.email in ADMIN_EMAILS or user.role == "admin",
        "streak": user.streak,
        "xp": user.xp,
    }

async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ========== Helper Functions ==========

async def add_notification(db: AsyncSession, user_id: str, title: str, message: str, ntype: str = "info"):
    """Add notification for a user"""
    notif = Notification(
        notification_id=f"notif_{uuid.uuid4().hex[:10]}",
        user_id=user_id,
        title=title,
        message=message,
        type=ntype,
    )
    db.add(notif)
    await db.commit()

async def add_xp(db: AsyncSession, user_id: str, amount: int, reason: str):
    """Add XP to user"""
    stmt = update(User).where(User.id == user_id).values(xp=User.xp + amount)
    await db.execute(stmt)
    await db.commit()

async def process_commissions(db: AsyncSession, purchase_id: str, buyer_id: str, amount: float, course_title: str):
    """Process commissions for a purchase through the referral chain"""
    # Get buyer with referral chain
    stmt = select(User).where(User.id == buyer_id)
    result = await db.execute(stmt)
    buyer = result.scalar_one_or_none()
    
    if not buyer or not buyer.referral_chain:
        return []
    
    commissions = []
    chain = buyer.referral_chain[:5]  # Max 5 levels
    
    for level, referrer_id in enumerate(chain, start=1):
        rate = COMMISSION_LEVELS.get(level, 0)
        if rate == 0:
            break
        
        commission_amount = round(amount * rate, 2)
        
        # Create commission
        commission = Commission(
            commission_id=f"com_{uuid.uuid4().hex[:12]}",
            earned_by_id=referrer_id,
            from_user_id=buyer_id,
            purchase_id=purchase_id,
            amount=commission_amount,
            level=level,
            rate=rate * 100,
            status=CommissionStatus.PENDING.value,
        )
        db.add(commission)
        commissions.append(commission)
        
        # Notify the earner
        await add_notification(
            db, referrer_id, "Commission Earned!",
            f"₹{commission_amount} from {buyer.name} (L{level}) for {course_title}",
            "commission"
        )
    
    await db.commit()
    return commissions

# ========== Auth Routes ==========
# Google OAuth login/callback are in routes/google_auth.py.
# `/api/auth/me` and `/api/auth/logout` live here.

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if session_token:
        stmt = delete(UserSession).where(UserSession.session_token == session_token)
        await db.execute(stmt)
        await db.commit()
    response.delete_cookie("session_token")
    return {"message": "Logged out"}

# ========== Courses Routes ==========

@api_router.get("/purchases")
async def get_my_purchases(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Return the current user's purchases (course_id is the public string ID)."""
    stmt = (
        select(Purchase, Course.course_id)
        .join(Course, Course.id == Purchase.course_id)
        .where(
            Purchase.user_id == user["user_id"],
            Purchase.status == PurchaseStatus.COMPLETED.value,
        )
        .order_by(Purchase.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "purchase_id": p.purchase_id,
            "course_id": course_id_str,
            "amount": p.amount,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p, course_id_str in rows
    ]

@api_router.get("/courses")
async def get_courses(db: AsyncSession = Depends(get_db)):
    """Get all published courses"""
    stmt = select(Course).where(Course.published == True).order_by(Course.created_at.desc())
    result = await db.execute(stmt)
    courses = result.scalars().all()
    
    course_list = []
    for c in courses:
        # Get lesson count
        stmt = select(func.count(Lesson.id)).where(Lesson.course_id == c.id)
        result = await db.execute(stmt)
        lesson_count = result.scalar() or 0
        
        # Get average rating
        stmt = select(func.avg(Review.rating)).where(Review.course_id == c.id)
        result = await db.execute(stmt)
        avg_rating = result.scalar() or 0
        
        course_list.append({
            "course_id": c.course_id,
            "title": c.title,
            "description": c.description,
            "price": c.price,
            "original_price": c.original_price,
            "image": c.image,
            "category": c.category,
            "tier": c.tier,
            "is_upsell": c.is_upsell,
            "lesson_count": lesson_count,
            "rating": round(avg_rating, 1) if avg_rating else 0,
            "published": c.published,
        })
    
    return course_list

@api_router.get("/courses/{course_id}")
async def get_course(course_id: str, db: AsyncSession = Depends(get_db)):
    """Get course details with lessons"""
    stmt = select(Course).where(Course.course_id == course_id)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get lessons
    stmt = select(Lesson).where(Lesson.course_id == course.id).order_by(Lesson.order)
    result = await db.execute(stmt)
    lessons = result.scalars().all()
    
    # Get resources
    stmt = select(Resource).where(Resource.course_id == course.id)
    result = await db.execute(stmt)
    resources = result.scalars().all()
    
    return {
        "course_id": course.course_id,
        "title": course.title,
        "description": course.description,
        "price": course.price,
        "original_price": course.original_price,
        "image": course.image,
        "category": course.category,
        "tier": course.tier,
        "lessons": [
            {
                "lesson_id": l.lesson_id,
                "title": l.title,
                "description": l.description,
                "video_type": l.video_type,
                "video_url": l.video_url if l.is_free_preview else None,
                "duration": l.duration,
                "order": l.order,
                "is_free_preview": l.is_free_preview,
            }
            for l in lessons
        ],
        "resources": [
            {
                "resource_id": r.resource_id,
                "name": r.name,
                "type": r.type,
                "url": r.url if r.is_free_preview else None,
                "is_free_preview": r.is_free_preview,
            }
            for r in resources
        ],
    }

@api_router.get("/courses/{course_id}/lessons")
async def get_course_lessons(course_id: str, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get full lesson details (requires purchase)"""
    # Get course
    stmt = select(Course).where(Course.course_id == course_id)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if purchased (or admin)
    has_access = user.get("is_admin", False)
    if not has_access:
        stmt = select(Purchase).where(
            Purchase.user_id == user["user_id"],
            Purchase.course_id == course.id,
            Purchase.status == PurchaseStatus.COMPLETED.value
        )
        result = await db.execute(stmt)
        purchase = result.scalar_one_or_none()
        has_access = purchase is not None
    
    # Get lessons
    stmt = select(Lesson).where(Lesson.course_id == course.id).order_by(Lesson.order)
    result = await db.execute(stmt)
    lessons = result.scalars().all()
    
    # Get user progress
    progress_map = {}
    if has_access:
        stmt = select(CourseProgress).where(
            CourseProgress.user_id == user["user_id"],
            CourseProgress.course_id == course.id
        )
        result = await db.execute(stmt)
        progress_records = result.scalars().all()
        progress_map = {str(p.lesson_id): p.completed for p in progress_records}
    
    return {
        "has_access": has_access,
        "lessons": [
            {
                "lesson_id": l.lesson_id,
                "title": l.title,
                "description": l.description,
                "video_type": l.video_type,
                "video_url": l.video_url if (has_access or l.is_free_preview) else None,
                "duration": l.duration,
                "order": l.order,
                "is_free_preview": l.is_free_preview,
                "completed": progress_map.get(str(l.id), False),
            }
            for l in lessons
        ],
    }

# ========== Progress Routes ==========

@api_router.post("/progress/complete")
async def complete_lesson(request: Request, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Mark a lesson as completed"""
    body = await request.json()
    course_id = body.get("course_id")
    lesson_id = body.get("lesson_id")
    
    # Get course and lesson
    stmt = select(Course).where(Course.course_id == course_id)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    stmt = select(Lesson).where(Lesson.lesson_id == lesson_id, Lesson.course_id == course.id)
    result = await db.execute(stmt)
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Check existing progress
    stmt = select(CourseProgress).where(
        CourseProgress.user_id == user["user_id"],
        CourseProgress.course_id == course.id,
        CourseProgress.lesson_id == lesson.id
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        if existing.completed:
            return {"message": "Already completed", "completed": True}
        existing.completed = True
        await db.commit()
    else:
        progress = CourseProgress(
            user_id=user["user_id"],
            course_id=course.id,
            lesson_id=lesson.id,
            completed=True,
        )
        db.add(progress)
        await db.commit()
    
    # Get total progress
    stmt = select(func.count(Lesson.id)).where(Lesson.course_id == course.id)
    result = await db.execute(stmt)
    total_lessons = result.scalar() or 0
    
    stmt = select(func.count(CourseProgress.id)).where(
        CourseProgress.user_id == user["user_id"],
        CourseProgress.course_id == course.id,
        CourseProgress.completed == True
    )
    result = await db.execute(stmt)
    completed_lessons = result.scalar() or 0
    
    # Award XP
    await add_xp(db, user["user_id"], 10, f"Completed lesson: {lesson.title}")
    
    return {
        "message": "Lesson completed!",
        "completed": completed_lessons,
        "total": total_lessons,
        "xp_earned": 10,
    }

@api_router.get("/progress/continue")
async def get_continue_learning(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get courses in progress for continue learning section"""
    # Get purchases
    stmt = select(Purchase).where(
        Purchase.user_id == user["user_id"],
        Purchase.status == PurchaseStatus.COMPLETED.value
    )
    result = await db.execute(stmt)
    purchases = result.scalars().all()
    
    continue_list = []
    for purchase in purchases:
        # Get course
        stmt = select(Course).where(Course.id == purchase.course_id)
        result = await db.execute(stmt)
        course = result.scalar_one_or_none()
        if not course:
            continue
        
        # Get progress
        stmt = select(func.count(Lesson.id)).where(Lesson.course_id == course.id)
        result = await db.execute(stmt)
        total = result.scalar() or 0
        
        stmt = select(func.count(CourseProgress.id)).where(
            CourseProgress.user_id == user["user_id"],
            CourseProgress.course_id == course.id,
            CourseProgress.completed == True
        )
        result = await db.execute(stmt)
        completed = result.scalar() or 0
        
        if completed < total:
            continue_list.append({
                "course_id": course.course_id,
                "title": course.title,
                "image": course.image,
                "completed": completed,
                "total": total,
                "progress": round(completed / total * 100) if total > 0 else 0,
            })
    
    return continue_list

# ========== Referral Routes ==========

@api_router.get("/referrals/stats")
async def get_referral_stats(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get referral statistics"""
    user_id = user["user_id"]
    
    # Total referrals
    stmt = select(func.count(User.id)).where(User.referred_by_id == user_id)
    result = await db.execute(stmt)
    total_referrals = result.scalar() or 0
    
    # Total earned
    stmt = select(func.sum(Commission.amount)).where(Commission.earned_by_id == user_id)
    result = await db.execute(stmt)
    total_earned = result.scalar() or 0
    
    # This month earned
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    stmt = select(func.sum(Commission.amount)).where(
        Commission.earned_by_id == user_id,
        Commission.created_at >= month_start
    )
    result = await db.execute(stmt)
    this_month = result.scalar() or 0
    
    return {
        "total_referrals": total_referrals,
        "total_earned": total_earned,
        "this_month": this_month,
        "referral_code": user["referral_code"],
        "referral_link": f"{FRONTEND_URL}/login?ref={user['referral_code']}",
    }

@api_router.get("/referrals/users")
async def get_referred_users(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get list of referred users"""
    stmt = select(User).where(User.referred_by_id == user["user_id"]).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    referred_users = []
    for u in users:
        # Get total earned from this user
        stmt = select(func.sum(Commission.amount)).where(
            Commission.earned_by_id == user["user_id"],
            Commission.from_user_id == str(u.id)
        )
        result = await db.execute(stmt)
        earned = result.scalar() or 0
        
        # Check if they made a purchase
        stmt = select(func.count(Purchase.id)).where(
            Purchase.user_id == str(u.id),
            Purchase.status == PurchaseStatus.COMPLETED.value
        )
        result = await db.execute(stmt)
        has_purchase = (result.scalar() or 0) > 0
        
        referred_users.append({
            "user_id": str(u.id),
            "name": u.name,
            "email": u.email,
            "picture": u.avatar,
            "status": "active" if has_purchase else u.status or "pending",
            "earned_from": earned,
            "joined": u.created_at.isoformat() if u.created_at else None,
        })
    
    return referred_users

@api_router.get("/referrals/tree")
async def get_referral_tree(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get referral tree for visualization"""
    async def build_node(uid: str, depth: int = 0):
        if depth >= 5:
            return None
        
        stmt = select(User).where(User.id == uid)
        result = await db.execute(stmt)
        u = result.scalar_one_or_none()
        if not u:
            return None
        
        # Get direct referrals
        stmt = select(User).where(User.referred_by_id == uid)
        result = await db.execute(stmt)
        referrals = result.scalars().all()
        
        # Get earnings from subtree
        stmt = select(func.sum(Commission.amount)).where(Commission.from_user_id == uid)
        result = await db.execute(stmt)
        earned = result.scalar() or 0
        
        children = []
        for ref in referrals[:10]:  # Limit children
            child = await build_node(str(ref.id), depth + 1)
            if child:
                children.append(child)
        
        return {
            "name": u.name,
            "attributes": {
                "level": depth,
                "status": u.status or "active",
                "earned": earned,
                "joined": u.created_at.strftime("%Y-%m-%d") if u.created_at else "",
            },
            "user_id": str(u.id),
            "children": children if children else None,
        }
    
    tree = await build_node(user["user_id"])
    return tree or {"name": user["name"], "attributes": {"level": 0}, "children": None}

@api_router.get("/referrals/tree-stats")
async def get_referral_tree_stats(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get referral tree statistics by level"""
    from sqlalchemy import text
    
    # This is a simplified version - counts direct referrals at each level
    counts = []
    for level in range(1, 6):
        # Count users at this level in referral chain
        if level == 1:
            stmt = select(func.count(User.id)).where(User.referred_by_id == user["user_id"])
            result = await db.execute(stmt)
            count = result.scalar() or 0
        else:
            # For deeper levels, use JSON array position check
            # referral_chain is stored as JSON array, so we use json_array_elements to find position
            try:
                # PostgreSQL: Check if user_id appears at position (level-1) in the chain (0-indexed)
                query = text("""
                    SELECT COUNT(*) FROM users 
                    WHERE referral_chain IS NOT NULL 
                    AND jsonb_array_length(referral_chain::jsonb) >= :level
                    AND referral_chain::jsonb->>(:level_idx)::int = :user_id
                """)
                result = await db.execute(query, {"level": level, "level_idx": level - 1, "user_id": user["user_id"]})
                count = result.scalar() or 0
            except Exception:
                count = 0
        counts.append({"level": level, "count": count})
    
    total = sum(c["count"] for c in counts)
    
    # Earnings by level
    stmt = select(Commission.level, func.sum(Commission.amount)).where(
        Commission.earned_by_id == user["user_id"]
    ).group_by(Commission.level)
    result = await db.execute(stmt)
    earnings = {row[0]: {"amount": row[1], "transactions": 0} for row in result.fetchall()}
    
    return {
        "total_network": total,
        "by_level": counts,
        "earnings_by_level": earnings,
    }

# ========== Wallet Routes ==========

@api_router.get("/wallet")
async def get_wallet(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get wallet balance"""
    user_id = user["user_id"]
    
    # Total earned (approved + paid)
    stmt = select(func.sum(Commission.amount)).where(
        Commission.earned_by_id == user_id,
        Commission.status.in_([CommissionStatus.APPROVED.value, CommissionStatus.PAID.value])
    )
    result = await db.execute(stmt)
    total_earned = result.scalar() or 0
    
    # Pending
    stmt = select(func.sum(Commission.amount)).where(
        Commission.earned_by_id == user_id,
        Commission.status == CommissionStatus.PENDING.value
    )
    result = await db.execute(stmt)
    pending = result.scalar() or 0
    
    # Withdrawable (approved only)
    stmt = select(func.sum(Commission.amount)).where(
        Commission.earned_by_id == user_id,
        Commission.status == CommissionStatus.APPROVED.value
    )
    result = await db.execute(stmt)
    withdrawable = result.scalar() or 0
    
    # Total withdrawn
    stmt = select(func.sum(Payout.net_amount)).where(
        Payout.user_id == user_id,
        Payout.status == PayoutStatus.PAID.value
    )
    result = await db.execute(stmt)
    withdrawn = result.scalar() or 0
    
    return {
        "balance": withdrawable,
        "total_earned": total_earned + pending,
        "total_withdrawn": withdrawn or 0,
        "pending": pending,
        "withdrawable": withdrawable,
    }

@api_router.get("/wallet/transactions")
async def get_transactions(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get commission and payout history"""
    user_id = user["user_id"]
    
    # Get commissions
    stmt = select(Commission).where(
        Commission.earned_by_id == user_id
    ).order_by(Commission.created_at.desc()).limit(50)
    result = await db.execute(stmt)
    commissions = result.scalars().all()
    
    commission_list = []
    for c in commissions:
        # Get from user name
        stmt = select(User.name).where(User.id == c.from_user_id)
        result = await db.execute(stmt)
        from_name = result.scalar() or "Unknown"
        
        commission_list.append({
            "commission_id": c.commission_id,
            "amount": c.amount,
            "level": c.level,
            "status": c.status,
            "from_user_name": from_name,
            "course_title": "Course Purchase",  # Simplified
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    
    # Get payouts
    stmt = select(Payout).where(
        Payout.user_id == user_id
    ).order_by(Payout.created_at.desc()).limit(20)
    result = await db.execute(stmt)
    payouts = result.scalars().all()
    
    payout_list = [
        {
            "payout_id": p.payout_id,
            "amount": p.net_amount,
            "gross_amount": p.gross_amount,
            "tds_amount": p.tds_amount,
            "net_amount": p.net_amount,
            "status": p.status,
            "estimated_date": p.estimated_date.isoformat() if p.estimated_date else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in payouts
    ]
    
    return {"commissions": commission_list, "payouts": payout_list}

@api_router.post("/wallet/payout/preview")
async def preview_payout(request: Request, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Preview payout with TDS calculation"""
    body = await request.json()
    amount = body.get("amount", 0)
    
    # Get withdrawable balance
    stmt = select(func.sum(Commission.amount)).where(
        Commission.earned_by_id == user["user_id"],
        Commission.status == CommissionStatus.APPROVED.value
    )
    result = await db.execute(stmt)
    balance = result.scalar() or 0
    
    if balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    if amount < MIN_WITHDRAWAL:
        raise HTTPException(status_code=400, detail=f"Minimum withdrawal is ₹{MIN_WITHDRAWAL}")
    
    # Calculate TDS
    if amount >= TDS_THRESHOLD:
        tds = round(amount * TDS_RATE, 2)
    else:
        tds = 0
    
    net = round(amount - tds, 2)
    
    # Estimated date (next 3 business days)
    est_date = datetime.now(timezone.utc) + timedelta(days=3)
    while est_date.weekday() >= 5:
        est_date += timedelta(days=1)
    
    return {
        "gross": amount,
        "tds": tds,
        "net": net,
        "tds_rate": TDS_RATE * 100 if tds > 0 else 0,
        "estimated_date": est_date.strftime("%d %b %Y"),
        "processing_days": "2-3 business days",
    }

@api_router.post("/wallet/payout")
async def request_payout(request: Request, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Request a payout"""
    body = await request.json()
    amount = body.get("amount", 0)
    bank_details = body.get("bank_details", {})
    
    # Validate
    stmt = select(func.sum(Commission.amount)).where(
        Commission.earned_by_id == user["user_id"],
        Commission.status == CommissionStatus.APPROVED.value
    )
    result = await db.execute(stmt)
    balance = result.scalar() or 0
    
    if balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    if amount < MIN_WITHDRAWAL:
        raise HTTPException(status_code=400, detail=f"Minimum withdrawal is ₹{MIN_WITHDRAWAL}")
    
    # Calculate TDS
    tds = round(amount * TDS_RATE, 2) if amount >= TDS_THRESHOLD else 0
    net = round(amount - tds, 2)
    
    # Estimated date
    est_date = datetime.now(timezone.utc) + timedelta(days=3)
    while est_date.weekday() >= 5:
        est_date += timedelta(days=1)
    
    # Create payout request
    payout = Payout(
        payout_id=f"pay_{uuid.uuid4().hex[:12]}",
        user_id=user["user_id"],
        gross_amount=amount,
        tds_amount=tds,
        tds_rate=TDS_RATE * 100 if tds > 0 else 0,
        net_amount=net,
        bank_account=bank_details.get("account"),
        bank_ifsc=bank_details.get("ifsc"),
        upi_id=bank_details.get("upi"),
        payment_method="upi" if bank_details.get("upi") else "bank",
        estimated_date=est_date,
    )
    db.add(payout)
    
    # Mark commissions as paid (up to the amount)
    stmt = select(Commission).where(
        Commission.earned_by_id == user["user_id"],
        Commission.status == CommissionStatus.APPROVED.value
    ).order_by(Commission.created_at)
    result = await db.execute(stmt)
    commissions = result.scalars().all()
    
    remaining = amount
    for c in commissions:
        if remaining <= 0:
            break
        c.status = CommissionStatus.PAID.value
        c.paid_at = datetime.now(timezone.utc)
        remaining -= c.amount
    
    await db.commit()
    
    await add_notification(
        db, user["user_id"], "Payout Requested",
        f"₹{net} payout requested. Expected by {est_date.strftime('%d %b %Y')}",
        "payout"
    )
    
    return {
        "payout_id": payout.payout_id,
        "gross": amount,
        "tds": tds,
        "net": net,
        "status": "pending",
        "estimated_date": est_date.strftime("%d %b %Y"),
    }

@api_router.get("/wallet/payouts/{payout_id}/receipt")
async def get_payout_receipt(payout_id: str, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get payout receipt for PDF generation"""
    stmt = select(Payout).where(
        Payout.payout_id == payout_id,
        Payout.user_id == user["user_id"]
    )
    result = await db.execute(stmt)
    payout = result.scalar_one_or_none()
    
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    
    return {
        "receipt_id": f"REC-{payout_id.upper()}",
        "payout_id": payout_id,
        "user_name": user["name"],
        "user_email": user["email"],
        "gross_amount": payout.gross_amount,
        "tds_amount": payout.tds_amount,
        "tds_rate": payout.tds_rate,
        "net_amount": payout.net_amount,
        "status": payout.status,
        "requested_date": payout.created_at.strftime("%Y-%m-%d") if payout.created_at else "",
        "estimated_date": payout.estimated_date.strftime("%Y-%m-%d") if payout.estimated_date else "",
        "processed_date": payout.paid_at.strftime("%Y-%m-%d") if payout.paid_at else "",
        "platform": "Mera Mentor",
        "pan_note": "TDS deducted as per Income Tax Act. Please keep this for your tax records.",
    }

# ========== Notifications Routes ==========

@api_router.get("/notifications")
async def get_notifications(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get user notifications"""
    stmt = select(Notification).where(
        Notification.user_id == user["user_id"]
    ).order_by(Notification.created_at.desc()).limit(50)
    result = await db.execute(stmt)
    notifs = result.scalars().all()
    
    return [
        {
            "notification_id": n.notification_id,
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "read": n.read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifs
    ]

@api_router.get("/notifications/unread-count")
async def get_unread_count(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get unread notification count"""
    stmt = select(func.count(Notification.id)).where(
        Notification.user_id == user["user_id"],
        Notification.read == False
    )
    result = await db.execute(stmt)
    count = result.scalar() or 0
    return {"count": count}

@api_router.post("/notifications/mark-read")
async def mark_notifications_read(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Mark all notifications as read"""
    stmt = update(Notification).where(
        Notification.user_id == user["user_id"],
        Notification.read == False
    ).values(read=True)
    await db.execute(stmt)
    await db.commit()
    return {"message": "All marked as read"}

# ========== Leaderboard Routes ==========

@api_router.get("/leaderboard")
async def get_leaderboard(period: str = "all", db: AsyncSession = Depends(get_db)):
    """Get referral leaderboard"""
    # Build date filter
    if period == "weekly":
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    elif period == "monthly":
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    else:
        cutoff = None
    
    # Get top earners
    if cutoff:
        stmt = select(
            Commission.earned_by_id,
            func.sum(Commission.amount).label("total")
        ).where(
            Commission.created_at >= cutoff
        ).group_by(Commission.earned_by_id).order_by(desc("total")).limit(20)
    else:
        stmt = select(
            Commission.earned_by_id,
            func.sum(Commission.amount).label("total")
        ).group_by(Commission.earned_by_id).order_by(desc("total")).limit(20)
    
    result = await db.execute(stmt)
    rankings = result.fetchall()
    
    leaderboard = []
    for rank, (user_id, total) in enumerate(rankings, start=1):
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            # Determine badge
            if rank == 1:
                badge = "diamond"
            elif rank <= 3:
                badge = "gold"
            elif rank <= 10:
                badge = "silver"
            else:
                badge = "bronze"
            
            leaderboard.append({
                "rank": rank,
                "user_id": str(user.id),
                "name": user.name,
                "picture": user.avatar,
                "total_earned": total,
                "badge": badge,
            })
    
    return leaderboard

@api_router.get("/leaderboard/my-rank")
async def get_my_rank(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get current user's rank"""
    # Get user's total
    stmt = select(func.sum(Commission.amount)).where(Commission.earned_by_id == user["user_id"])
    result = await db.execute(stmt)
    my_total = result.scalar() or 0
    
    # Count users with more earnings
    stmt = select(func.count(Commission.earned_by_id.distinct())).where(
        select(func.sum(Commission.amount)).where(
            Commission.earned_by_id == Commission.earned_by_id
        ).correlate(Commission).scalar_subquery() > my_total
    )
    # Simplified: just get approximate rank
    stmt = select(
        Commission.earned_by_id,
        func.sum(Commission.amount).label("total")
    ).group_by(Commission.earned_by_id).order_by(desc("total"))
    result = await db.execute(stmt)
    rankings = result.fetchall()
    
    rank = 1
    for uid, total in rankings:
        if str(uid) == user["user_id"]:
            break
        rank += 1
    
    return {"rank": rank, "total_earned": my_total}

# ========== Analytics Routes ==========

@api_router.get("/analytics/earnings")
async def get_earnings_analytics(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get 30-day earnings data for chart"""
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    stmt = select(
        func.date_trunc('day', Commission.created_at).label("date"),
        func.sum(Commission.amount).label("amount")
    ).where(
        Commission.earned_by_id == user["user_id"],
        Commission.created_at >= thirty_days_ago
    ).group_by("date").order_by("date")
    
    result = await db.execute(stmt)
    data = result.fetchall()
    
    return [
        {"date": row[0].strftime("%Y-%m-%d") if row[0] else "", "amount": row[1] or 0}
        for row in data
    ]

@api_router.get("/analytics/commission-by-level")
async def get_commission_by_level(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get commission breakdown by level for pie chart"""
    stmt = select(
        Commission.level,
        func.sum(Commission.amount).label("amount"),
        func.count(Commission.id).label("count")
    ).where(
        Commission.earned_by_id == user["user_id"]
    ).group_by(Commission.level).order_by(Commission.level)
    
    result = await db.execute(stmt)
    data = result.fetchall()
    
    return [
        {"level": row[0], "amount": row[1] or 0, "count": row[2] or 0}
        for row in data
    ]

# ========== Commission Levels Route ==========

@api_router.get("/commission-levels")
async def get_commission_levels():
    """Get commission level configuration"""
    example_price = 799
    levels = [
        {
            "level": level,
            "percentage": rate * 100,
            "example_earning": round(example_price * rate, 2)
        }
        for level, rate in COMMISSION_LEVELS.items()
    ]
    return {
        "levels": levels,
        "min_withdrawal": MIN_WITHDRAWAL,
        "total_rate": sum(COMMISSION_LEVELS.values()) * 100,
    }

# ========== Referral Landing Route ==========

@api_router.get("/referral/{ref_code}")
async def get_referral_landing(ref_code: str, db: AsyncSession = Depends(get_db)):
    """Get referral landing page data"""
    stmt = select(User).where(User.referral_code == ref_code)
    result = await db.execute(stmt)
    referrer = result.scalar_one_or_none()
    
    if not referrer:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    
    # Get top courses
    stmt = select(Course).where(Course.published == True).limit(3)
    result = await db.execute(stmt)
    courses = result.scalars().all()
    
    return {
        "referrer": {
            "name": referrer.name,
            "picture": referrer.avatar,
        },
        "featured_courses": [
            {
                "course_id": c.course_id,
                "title": c.title,
                "price": c.price,
                "image": c.image,
            }
            for c in courses
        ],
    }

# ========== Streaks Route ==========

@api_router.get("/streaks")
async def get_streaks(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get user streak and XP info"""
    stmt = select(User).where(User.id == user["user_id"])
    result = await db.execute(stmt)
    u = result.scalar_one_or_none()
    
    if not u:
        return {"streak": 0, "xp": 0}
    
    return {
        "streak": u.streak,
        "xp": u.xp,
        "level": u.xp // 100 + 1,
        "xp_to_next": 100 - (u.xp % 100),
    }

# ========== Payments Routes ==========

@api_router.post("/payments/create-order")
async def create_payment_order(request: Request, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Create Razorpay payment order"""
    body = await request.json()
    course_id = body.get("course_id")
    coupon_code = body.get("coupon_code")

    # Get course
    stmt = select(Course).where(Course.course_id == course_id)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check if already purchased
    stmt = select(Purchase).where(
        Purchase.user_id == user["user_id"],
        Purchase.course_id == course.id,
        Purchase.status == PurchaseStatus.COMPLETED.value
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Already purchased")

    # Calculate amount with coupon
    amount = course.price
    discount = 0

    if coupon_code:
        stmt = select(Coupon).where(Coupon.code == coupon_code, Coupon.active == True)
        result = await db.execute(stmt)
        coupon = result.scalar_one_or_none()
        if coupon:
            if coupon.discount_type == "percentage":
                discount = round(amount * coupon.discount_value / 100, 2)
            else:
                discount = coupon.discount_value
            amount = max(0, amount - discount)

    # Re-use existing PENDING order for this user+course (handles double-click / retries)
    stmt = select(Purchase).where(
        Purchase.user_id == user["user_id"],
        Purchase.course_id == course.id,
        Purchase.status == PurchaseStatus.PENDING.value,
    )
    result = await db.execute(stmt)
    pending = result.scalar_one_or_none()

    if pending and pending.razorpay_order_id:
        return {
            "order_id": pending.razorpay_order_id,
            "amount": pending.amount,
            "amount_paise": int(pending.amount * 100),
            "currency": "INR",
            "key_id": RAZORPAY_KEY_ID,
            "course": {"title": course.title, "image": course.image},
        }

    # Create Razorpay order (amount in paise)
    amount_paise = int(amount * 100)
    receipt = f"pur_{uuid.uuid4().hex[:16]}"  # max 40 chars

    if razorpay_client:
        try:
            rz_order = razorpay_client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "receipt": receipt,
                "payment_capture": 1,
            })
            order_id = rz_order["id"]
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Razorpay error: {str(e)}")
    else:
        # Demo mode — no real keys configured
        order_id = f"order_{uuid.uuid4().hex[:16]}"

    # Save pending purchase
    purchase = Purchase(
        purchase_id=receipt,
        user_id=user["user_id"],
        course_id=course.id,
        amount=amount,
        original_amount=course.price,
        discount_amount=discount,
        coupon_code=coupon_code,
        razorpay_order_id=order_id,
        status=PurchaseStatus.PENDING.value,
    )
    db.add(purchase)
    await db.commit()

    return {
        "order_id": order_id,
        "amount": amount,
        "amount_paise": amount_paise,
        "currency": "INR",
        "key_id": RAZORPAY_KEY_ID,
        "course": {
            "title": course.title,
            "image": course.image,
        },
    }

@api_router.post("/payments/verify")
async def verify_payment(request: Request, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Verify Razorpay payment signature and complete purchase"""
    body = await request.json()
    order_id   = body.get("razorpay_order_id")
    payment_id = body.get("razorpay_payment_id", "")
    signature  = body.get("razorpay_signature", "")

    # Find purchase
    stmt = select(Purchase).where(Purchase.razorpay_order_id == order_id)
    result = await db.execute(stmt)
    purchase = result.scalar_one_or_none()

    if not purchase:
        raise HTTPException(status_code=404, detail="Order not found")

    if purchase.status == PurchaseStatus.COMPLETED.value:
        return {"message": "Already completed", "purchase_id": purchase.purchase_id}

    # Signature verification (only when real keys are configured)
    if razorpay_client and signature:
        try:
            razorpay_client.utility.verify_payment_signature({
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            })
        except razorpay.errors.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid payment signature")

    # Mark completed
    purchase.status = PurchaseStatus.COMPLETED.value
    purchase.razorpay_payment_id = payment_id
    purchase.completed_at = datetime.now(timezone.utc)

    # Get course
    stmt = select(Course).where(Course.id == purchase.course_id)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()

    # Process commissions
    if course:
        await process_commissions(db, str(purchase.id), user["user_id"], purchase.amount, course.title)

    # Award XP
    await add_xp(db, user["user_id"], 50, "Purchased course")

    await db.commit()

    await add_notification(
        db, user["user_id"], "Purchase Complete!",
        f"You now have access to {course.title if course else 'the course'}",
        "purchase"
    )

    return {
        "message": "Payment successful!",
        "purchase_id": purchase.purchase_id,
        "course_id": course.course_id if course else None,
    }

@api_router.post("/payments/webhook")
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Razorpay webhook handler with signature verification"""
    payload = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if RAZORPAY_WEBHOOK_SECRET and signature:
        try:
            razorpay_client.utility.verify_webhook_signature(
                payload.decode(), signature, RAZORPAY_WEBHOOK_SECRET
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        event = json.loads(payload)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")

    event_type = event.get("event", "")

    if event_type == "payment.captured":
        payment = event.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment.get("order_id")
        payment_id = payment.get("id")

        if order_id:
            stmt = select(Purchase).where(Purchase.razorpay_order_id == order_id)
            result = await db.execute(stmt)
            purchase = result.scalar_one_or_none()

            if purchase and purchase.status != PurchaseStatus.COMPLETED.value:
                purchase.status = PurchaseStatus.COMPLETED.value
                purchase.razorpay_payment_id = payment_id
                purchase.completed_at = datetime.now(timezone.utc)

                stmt = select(Course).where(Course.id == purchase.course_id)
                result = await db.execute(stmt)
                course = result.scalar_one_or_none()

                if course:
                    await process_commissions(db, str(purchase.id), purchase.user_id, purchase.amount, course.title)

                await db.commit()

    elif event_type == "payment.failed":
        payment = event.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment.get("order_id")
        if order_id:
            stmt = select(Purchase).where(Purchase.razorpay_order_id == order_id)
            result = await db.execute(stmt)
            purchase = result.scalar_one_or_none()
            if purchase and purchase.status == PurchaseStatus.PENDING.value:
                purchase.status = PurchaseStatus.FAILED.value
                await db.commit()

    return {"status": "ok"}

# ========== Admin Routes ==========

@api_router.get("/admin/stats")
async def get_admin_stats(admin: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Get admin dashboard stats"""
    # Total users
    stmt = select(func.count(User.id))
    result = await db.execute(stmt)
    total_users = result.scalar() or 0
    
    # Total purchases
    stmt = select(func.count(Purchase.id)).where(Purchase.status == PurchaseStatus.COMPLETED.value)
    result = await db.execute(stmt)
    total_purchases = result.scalar() or 0
    
    # Total revenue
    stmt = select(func.sum(Purchase.amount)).where(Purchase.status == PurchaseStatus.COMPLETED.value)
    result = await db.execute(stmt)
    total_revenue = result.scalar() or 0
    
    # Total commissions
    stmt = select(func.sum(Commission.amount))
    result = await db.execute(stmt)
    total_commissions = result.scalar() or 0
    
    return {
        "total_users": total_users,
        "total_purchases": total_purchases,
        "total_revenue": total_revenue,
        "total_commissions": total_commissions,
    }

@api_router.post("/admin/courses")
async def create_course(request: Request, admin: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Create a new course"""
    body = await request.json()
    
    course = Course(
        course_id=f"course_{uuid.uuid4().hex[:8]}",
        title=body.get("title", "New Course"),
        description=body.get("description", ""),
        price=body.get("price", 499),
        original_price=body.get("original_price"),
        image=body.get("image", ""),
        category=body.get("category", "General"),
        tier=body.get("tier", "standard"),
        is_upsell=body.get("is_upsell", False),
        upsell_for=body.get("upsell_for"),
        published=body.get("published", True),
        created_by=admin["user_id"],
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    
    # Add lessons
    for i, lesson_data in enumerate(body.get("lessons", [])):
        lesson = Lesson(
            lesson_id=f"les_{uuid.uuid4().hex[:8]}",
            course_id=course.id,
            title=lesson_data.get("title", f"Lesson {i+1}"),
            description=lesson_data.get("description", ""),
            video_type=lesson_data.get("video_type", "youtube"),
            video_url=lesson_data.get("video_url", ""),
            duration=lesson_data.get("duration", ""),
            order=i,
            is_free_preview=lesson_data.get("is_free_preview", False),
        )
        db.add(lesson)
    
    # Add resources
    for res_data in body.get("resources", []):
        resource = Resource(
            resource_id=f"res_{uuid.uuid4().hex[:8]}",
            course_id=course.id,
            name=res_data.get("name", "Resource"),
            type=res_data.get("type", "pdf"),
            url=res_data.get("url", ""),
            is_free_preview=res_data.get("is_free_preview", False),
        )
        db.add(resource)
    
    await db.commit()
    
    return {"message": "Course created", "course_id": course.course_id}

@api_router.put("/admin/courses/{course_id}")
async def update_course(course_id: str, request: Request, admin: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Update a course"""
    body = await request.json()
    
    stmt = select(Course).where(Course.course_id == course_id)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Update fields
    for field in ["title", "description", "price", "original_price", "image", "category", "tier", "is_upsell", "upsell_for", "published"]:
        if field in body:
            setattr(course, field, body[field])
    
    # Update lessons
    if "lessons" in body:
        # Delete old lessons
        stmt = delete(Lesson).where(Lesson.course_id == course.id)
        await db.execute(stmt)
        
        # Add new lessons
        for i, lesson_data in enumerate(body["lessons"]):
            lesson = Lesson(
                lesson_id=lesson_data.get("lesson_id") or f"les_{uuid.uuid4().hex[:8]}",
                course_id=course.id,
                title=lesson_data.get("title", f"Lesson {i+1}"),
                description=lesson_data.get("description", ""),
                video_type=lesson_data.get("video_type", "youtube"),
                video_url=lesson_data.get("video_url", ""),
                duration=lesson_data.get("duration", ""),
                order=i,
                is_free_preview=lesson_data.get("is_free_preview", False),
            )
            db.add(lesson)
    
    await db.commit()
    
    return {"message": "Course updated"}

@api_router.delete("/admin/courses/{course_id}")
async def delete_course(course_id: str, admin: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Delete a course"""
    stmt = select(Course).where(Course.course_id == course_id)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    await db.delete(course)
    await db.commit()
    
    return {"message": "Course deleted"}

@api_router.get("/admin/commission-settings")
async def get_commission_settings(admin: dict = Depends(require_admin)):
    """Get commission settings"""
    return {
        "levels": [{"level": k, "percentage": v * 100} for k, v in COMMISSION_LEVELS.items()],
        "total_payout_percent": sum(v * 100 for v in COMMISSION_LEVELS.values()),
        "platform_keep_percent": 100 - sum(v * 100 for v in COMMISSION_LEVELS.values()),
        "min_withdrawal": MIN_WITHDRAWAL,
    }

# ========== Media Upload Routes ==========

ALLOWED_VIDEO_TYPES = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"]
ALLOWED_PDF_TYPES = ["application/pdf"]
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]

from services.storage_service import upload_file as storage_upload, download_file as storage_download, init_storage, is_storage_enabled

@api_router.post("/admin/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    upload_type: str = Form(...),
    course_id: Optional[str] = Form(None),
    lesson_id: Optional[str] = Form(None),
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Upload media file to cloud object storage"""
    if not is_storage_enabled():
        raise HTTPException(
            status_code=503,
            detail="Cloudflare R2 is not configured. Set CLOUDFLARE_R2_ACCOUNT_ID, "
                   "CLOUDFLARE_R2_ACCESS_KEY_ID, CLOUDFLARE_R2_SECRET_ACCESS_KEY, "
                   "and CLOUDFLARE_R2_BUCKET_NAME in the environment.",
        )

    content_type = file.content_type or ""

    # Validate type
    if upload_type == "video" and content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=400, detail="Invalid video type")
    elif upload_type == "pdf" and content_type not in ALLOWED_PDF_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    elif upload_type == "image" and content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid image type")

    file_content = await file.read()
    file_size = len(file_content)

    # Upload to cloud object storage
    try:
        storage_path = await storage_upload(file_content, upload_type, file.filename, content_type)
    except Exception as e:
        # Log the real error; return a clean message to the client.
        logging.exception("R2 upload failed")
        raise HTTPException(status_code=502, detail=f"Storage upload failed: {type(e).__name__}")

    # Store reference in database
    media = Media(
        media_id=f"media_{uuid.uuid4().hex[:12]}",
        file_key=storage_path,
        file_name=file.filename,
        file_type=upload_type,
        content_type=content_type,
        file_size=file_size,
        storage_mode="r2",
        uploaded_by=admin["user_id"],
    )
    db.add(media)
    await db.commit()

    return {
        "media_id": media.media_id,
        "file_key": storage_path,
        "file_name": file.filename,
        "file_type": upload_type,
        "file_size": file_size,
        "url": f"/api/media/files/{storage_path}",
        "status": "ready",
    }

@api_router.get("/admin/media")
async def list_media(
    upload_type: Optional[str] = None,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List uploaded media"""
    stmt = select(Media)
    if upload_type:
        stmt = stmt.where(Media.file_type == upload_type)
    stmt = stmt.order_by(Media.created_at.desc()).limit(100)

    result = await db.execute(stmt)
    media_list = result.scalars().all()

    return [
        {
            "media_id": m.media_id,
            "file_key": m.file_key,
            "file_name": m.file_name,
            "file_type": m.file_type,
            "file_size": m.file_size,
            "status": m.status,
            "download_count": m.download_count,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in media_list
    ]

@api_router.delete("/admin/media/{media_id}")
async def delete_media(media_id: str, admin: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Soft-delete media record (object storage has no delete API)"""
    stmt = select(Media).where(Media.media_id == media_id)
    result = await db.execute(stmt)
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    await db.delete(media)
    await db.commit()

    return {"message": "Media deleted"}

@api_router.get("/media/files/{file_key:path}")
async def serve_media_file(file_key: str):
    """Proxy media file from cloud object storage"""
    try:
        data, ct = await storage_download(file_key)
        return Response(content=data, media_type=ct)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")

# ========== Health Check ==========

@api_router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "ok",
        "timestamp": now_iso(),
        "database": db_status,
        "storage_mode": "r2",
        "version": "2.0.0",
        "commission_levels": len(COMMISSION_LEVELS),
        "total_commission_rate": sum(COMMISSION_LEVELS.values()) * 100,
    }

# ========== Include Router ==========

app.include_router(api_router)
# Google OAuth 2.0 (real Google Cloud credentials, no third-party broker)
from routes.google_auth import router as google_auth_router
app.include_router(google_auth_router)

# ========== Serve React Frontend (production) ==========

STATIC_BUILD_DIR = ROOT_DIR / "static"

if STATIC_BUILD_DIR.exists():
    # Serve React's hashed JS/CSS/media assets
    react_assets = STATIC_BUILD_DIR / "static"
    if react_assets.exists():
        app.mount("/static", StaticFiles(directory=str(react_assets)), name="react-assets")

    @app.get("/{full_path:path}")
    async def serve_react_spa(full_path: str):
        """Catch-all: serve React index.html for all non-API routes (SPA routing)."""
        index_file = STATIC_BUILD_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse({"message": "Frontend not built"}, status_code=404)

# ========== Startup/Shutdown Events ==========

@app.on_event("startup")
async def startup():
    """Initialize database and storage on startup"""
    await init_db()
    try:
        init_storage()
        from services.storage_service import is_storage_enabled
        if is_storage_enabled():
            print("✅ Cloudflare R2 object storage initialized")
        else:
            print("ℹ️  Object storage not configured (uploads disabled)")
    except Exception as e:
        print(f"⚠️  Storage init warning: {e}")
    print("✅ Mera Mentor API started with PostgreSQL")

@app.on_event("shutdown")
async def shutdown():
    """Close database on shutdown"""
    await close_db()
