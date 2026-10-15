"""Public landing content and first-party analytics; editing requires existing admin auth."""
import os
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
from sqlalchemy import select, func, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from lib.database import get_db
from models.models import Course, LandingPage, LandingEvent, Review
from services.landing_seed import SLUG
from lib.settings import frontend_url


class SettingsInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    course_id: str = Field(min_length=1, max_length=50)
    seats_filled: int = Field(ge=0, le=100000)
    seats_total: int = Field(ge=1, le=100000)
    instructor_name: str = Field(min_length=1, max_length=100)
    instructor_experience: str = Field(min_length=1, max_length=10)
    instructor_bio: str = Field(min_length=1, max_length=800)
    support_email: str = Field(min_length=3, max_length=255)
    whatsapp_number: str = Field(max_length=20, pattern=r"^\+?[0-9]{8,15}$|^$")
    instagram_url: str = Field(max_length=512)
    linkedin_url: str = Field(max_length=512)
    student_count: str = Field(min_length=1, max_length=20)
    average_rating: str = Field(pattern=r"^(?:[0-4](?:\.[0-9])?|5(?:\.0)?)$")

    @field_validator("instagram_url", "linkedin_url")
    @classmethod
    def safe_url(cls, value):
        if value and not value.startswith("https://"):
            raise ValueError("Use a full https:// URL")
        return value

    @model_validator(mode="after")
    def seats_valid(self):
        if self.seats_filled > self.seats_total:
            raise ValueError("Filled seats cannot exceed total seats")
        if "@" not in self.support_email:
            raise ValueError("Enter a valid support email")
        return self


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=100)
    rating: int = Field(ge=1, le=5)
    review_text: str = Field(min_length=3, max_length=1000)
    role: str = Field(default="", max_length=160)
    display_order: int = Field(default=0, ge=0, le=10000)
    is_sample: bool = True
    outcome: str = Field(default="", max_length=80)

    @model_validator(mode="after")
    def outcome_for_genuine_reviews_only(self):
        if self.is_sample:
            self.outcome = ""
        return self


class EventInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    visitor_id: UUID
    event: Literal["page_view", "webinar_click", "course_click", "calculator_interaction", "signup_started", "browser_open"]
    browser_type: Literal["instagram", "facebook", "browser"]
    referral_code: str | None = Field(default=None, max_length=100)
    section: str = Field(default="", max_length=60)
    value: int | None = Field(default=None, ge=0, le=1000000)


def serialize_review(r):
    return {"id": str(r.id), "name": r.name, "rating": r.rating,
            "review_text": r.text, "role": r.role or "", "display_order": r.display_order,
            "is_sample": r.is_sample, "outcome": (r.outcome or "") if not r.is_sample else ""}


async def record_event(db, *, event_id, visitor_id, event, browser_type, referral_code=None, details=None):
    if not visitor_id:
        return
    await db.execute(insert(LandingEvent).values(event_id=event_id, visitor_id=visitor_id,
        event=event, browser_type=browser_type, referral_code=referral_code, details=details or {})
        .on_conflict_do_nothing(index_elements=["event_id"]))


def create_landing_router(require_admin):
    router = APIRouter(prefix="/api", tags=["data-analytics-landing"])

    @router.get("/landing/data-analytics")
    async def public_content(response: Response, db: AsyncSession = Depends(get_db)):
        page = await db.get(LandingPage, SLUG)
        if not page:
            raise HTTPException(503, "Course information is temporarily unavailable")
        settings = dict(page.settings)
        course = (await db.execute(select(Course).where(Course.course_id == settings["course_id"]))).scalar_one_or_none()
        reviews = (await db.execute(select(Review).where(Review.is_landing == True)
                                   .order_by(Review.display_order, Review.created_at))).scalars().all()
        response.headers["Cache-Control"] = "public, max-age=15"
        return {"settings": settings, "reviews": [serialize_review(r) for r in reviews],
                "webinar_url": os.environ.get("WEBINAR_SIGNUP_URL", "").strip(),
                "checkout_ready": bool(course and course.published and course.price == 1299 and os.environ.get("RAZORPAY_KEY_ID")),
                "payment_mode": "test" if os.environ.get("RAZORPAY_KEY_ID", "").startswith("rzp_test_") else "live",
                "google_ready": bool(frontend_url()) and all(os.environ.get(k, "").strip() for k in ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI", "SESSION_SECRET"])}

    @router.post("/landing/events", status_code=202)
    async def track(body: EventInput, db: AsyncSession = Depends(get_db)):
        count = (await db.execute(select(func.count(LandingEvent.id)).where(
            LandingEvent.visitor_id == str(body.visitor_id),
            LandingEvent.created_at > datetime.now(timezone.utc) - timedelta(hours=1)))).scalar()
        if count >= 150:
            raise HTTPException(429, "Too many analytics events")
        await record_event(db, event_id=str(body.event_id), visitor_id=str(body.visitor_id),
                           event=body.event, browser_type=body.browser_type, referral_code=body.referral_code,
                           details={"section": body.section, "value": body.value})
        await db.commit()
        return {"accepted": True}

    @router.get("/admin/landing/settings", dependencies=[Depends(require_admin)])
    async def get_settings(db: AsyncSession = Depends(get_db)):
        return (await db.get(LandingPage, SLUG)).settings

    @router.put("/admin/landing/settings", dependencies=[Depends(require_admin)])
    async def save_settings(body: SettingsInput, db: AsyncSession = Depends(get_db)):
        course = (await db.execute(select(Course).where(Course.course_id == body.course_id))).scalar_one_or_none()
        if not course:
            raise HTTPException(400, "Choose an existing course")
        if course.price != 1299:
            raise HTTPException(400, "Linked course price must be ₹1,299 to match this landing page")
        page = await db.get(LandingPage, SLUG)
        page.settings = body.model_dump()
        await db.commit()
        return page.settings

    @router.get("/admin/landing/reviews", dependencies=[Depends(require_admin)])
    async def list_reviews(db: AsyncSession = Depends(get_db)):
        rows = (await db.execute(select(Review).where(Review.is_landing == True)
                                .order_by(Review.display_order, Review.created_at))).scalars().all()
        return [serialize_review(r) for r in rows]

    @router.post("/admin/landing/reviews", status_code=201, dependencies=[Depends(require_admin)])
    async def add_review(body: ReviewInput, db: AsyncSession = Depends(get_db)):
        page = await db.get(LandingPage, SLUG)
        course = (await db.execute(select(Course).where(Course.course_id == page.settings["course_id"]))).scalar_one()
        data = body.model_dump()
        data["text"] = data.pop("review_text")
        r = Review(course_id=course.id, is_landing=True, **data)
        db.add(r)
        await db.commit()
        return serialize_review(r)

    @router.put("/admin/landing/reviews/{review_id}", dependencies=[Depends(require_admin)])
    async def edit_review(review_id: UUID, body: ReviewInput, db: AsyncSession = Depends(get_db)):
        r = await db.get(Review, str(review_id))
        if not r or not r.is_landing:
            raise HTTPException(404, "Landing review not found")
        for key, value in body.model_dump().items():
            setattr(r, "text" if key == "review_text" else key, value)
        await db.commit()
        return serialize_review(r)

    @router.delete("/admin/landing/reviews/{review_id}", dependencies=[Depends(require_admin)])
    async def remove_review(review_id: UUID, db: AsyncSession = Depends(get_db)):
        result = await db.execute(delete(Review).where(Review.id == str(review_id), Review.is_landing == True))
        if not result.rowcount:
            raise HTTPException(404, "Landing review not found")
        await db.commit()
        return {"deleted": True}

    @router.get("/admin/landing/analytics", dependencies=[Depends(require_admin)])
    async def analytics(db: AsyncSession = Depends(get_db)):
        since = datetime.now(timezone.utc) - timedelta(days=30)
        rows = (await db.execute(select(LandingEvent.browser_type, LandingEvent.event,
            func.count(LandingEvent.id), func.count(func.distinct(LandingEvent.visitor_id)))
            .where(LandingEvent.created_at >= since).group_by(LandingEvent.browser_type, LandingEvent.event))).all()
        stats = {b: {} for b in ["instagram", "facebook", "browser"]}
        for browser, event, count, visitors in rows:
            stats[browser][event] = {"events": count, "visitors": visitors}
        for values in stats.values():
            starts = values.get("signup_started", {}).get("visitors", 0)
            completed = values.get("signup_completed", {}).get("visitors", 0)
            values["signup_completion_rate"] = round(completed / starts * 100, 1) if starts else 0
        return {"days": 30, "by_browser": stats,
                "note": "Webinar clicks are tracked; Superprofile registrations require a separate provider callback."}

    return router