# SQLAlchemy Models for Mera Mentor
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, 
    ForeignKey, Enum, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from lib.database import Base
import enum

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

# Enums
class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    INSTRUCTOR = "instructor"

class PurchaseStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class CommissionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    REVERSED = "reversed"

class PayoutStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    avatar = Column(String(512))
    phone = Column(String(20))
    google_id = Column(String(255), unique=True, index=True)
    role = Column(String(20), default=UserRole.USER.value)
    
    # Referral system
    referral_code = Column(String(20), unique=True, nullable=False, index=True)
    referred_by_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    referral_chain = Column(JSON, default=list)  # Array of user IDs in chain
    
    # Gamification
    streak = Column(Integer, default=0)
    xp = Column(Integer, default=0)
    last_active = Column(DateTime(timezone=True))
    
    # Status
    status = Column(String(20), default="active")  # active, pending, churned
    email_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    referred_by = relationship("User", remote_side=[id], backref="referrals")
    purchases = relationship("Purchase", back_populates="user")
    commissions_earned = relationship("Commission", foreign_keys="Commission.earned_by_id", back_populates="earned_by")
    payouts = relationship("Payout", back_populates="user")
    progress = relationship("CourseProgress", back_populates="user")
    certificates = relationship("Certificate", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    course_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    original_price = Column(Float)
    image = Column(String(512))
    category = Column(String(100))
    tier = Column(String(20), default="standard")
    
    is_upsell = Column(Boolean, default=False)
    upsell_for = Column(String(50))
    published = Column(Boolean, default=True)
    
    created_by = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="course", cascade="all, delete-orphan")
    purchases = relationship("Purchase", back_populates="course")
    reviews = relationship("Review", back_populates="course")
    quizzes = relationship("Quiz", back_populates="course")

class Lesson(Base):
    __tablename__ = "lessons"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    lesson_id = Column(String(50), unique=True, nullable=False, index=True)
    course_id = Column(UUID(as_uuid=False), ForeignKey("courses.id"), nullable=False)
    
    title = Column(String(255), nullable=False)
    description = Column(Text)
    video_type = Column(String(20), default="youtube")  # youtube, upload
    video_url = Column(String(512))
    video_key = Column(String(255))  # R2/S3 key for uploaded videos
    thumbnail_url = Column(String(512))
    duration = Column(String(20))
    duration_seconds = Column(Integer)
    
    order = Column(Integer, default=0)
    is_free_preview = Column(Boolean, default=False)
    status = Column(String(20), default="ready")  # draft, processing, ready
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    # Relationships
    course = relationship("Course", back_populates="lessons")
    progress = relationship("CourseProgress", back_populates="lesson")

class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    resource_id = Column(String(50), unique=True, nullable=False)
    course_id = Column(UUID(as_uuid=False), ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(UUID(as_uuid=False), ForeignKey("lessons.id"), nullable=True)
    
    name = Column(String(255), nullable=False)
    type = Column(String(20), default="pdf")  # pdf, doc, link
    url = Column(String(512))
    file_key = Column(String(255))  # R2/S3 key
    file_size = Column(Integer)
    is_free_preview = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    course = relationship("Course", back_populates="resources")

class Purchase(Base):
    __tablename__ = "purchases"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    purchase_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    course_id = Column(UUID(as_uuid=False), ForeignKey("courses.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    original_amount = Column(Float)
    discount_amount = Column(Float, default=0)
    coupon_code = Column(String(50))
    
    razorpay_order_id = Column(String(100), unique=True, index=True)
    razorpay_payment_id = Column(String(100), unique=True, index=True)
    razorpay_signature = Column(String(255))
    landing_visitor_id = Column(String(80))
    landing_browser_type = Column(String(20))
    
    status = Column(String(20), default=PurchaseStatus.PENDING.value)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="purchases")
    course = relationship("Course", back_populates="purchases")
    commissions = relationship("Commission", back_populates="purchase")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', name='unique_user_course_purchase'),
    )

class Commission(Base):
    __tablename__ = "commissions"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    commission_id = Column(String(50), unique=True, nullable=False, index=True)
    
    earned_by_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    from_user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    purchase_id = Column(UUID(as_uuid=False), ForeignKey("purchases.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    level = Column(Integer, nullable=False)  # 1-5
    rate = Column(Float, nullable=False)  # percentage rate used
    
    status = Column(String(20), default=CommissionStatus.PENDING.value, index=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    approved_at = Column(DateTime(timezone=True))
    paid_at = Column(DateTime(timezone=True))
    
    # Relationships
    earned_by = relationship("User", foreign_keys=[earned_by_id], back_populates="commissions_earned")
    from_user = relationship("User", foreign_keys=[from_user_id])
    purchase = relationship("Purchase", back_populates="commissions")

class Payout(Base):
    __tablename__ = "payouts"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    payout_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    
    gross_amount = Column(Float, nullable=False)
    tds_amount = Column(Float, default=0)
    tds_rate = Column(Float, default=0)
    net_amount = Column(Float, nullable=False)
    
    # Bank details
    bank_account = Column(String(50))
    bank_ifsc = Column(String(20))
    upi_id = Column(String(100))
    payment_method = Column(String(20))  # bank, upi
    
    status = Column(String(20), default=PayoutStatus.PENDING.value)
    utr_number = Column(String(100))
    
    estimated_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utc_now)
    approved_at = Column(DateTime(timezone=True))
    paid_at = Column(DateTime(timezone=True))
    
    user = relationship("User", back_populates="payouts")

class CourseProgress(Base):
    __tablename__ = "course_progress"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    course_id = Column(UUID(as_uuid=False), ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(UUID(as_uuid=False), ForeignKey("lessons.id"), nullable=False)
    
    completed = Column(Boolean, default=False)
    last_position = Column(Integer, default=0)  # seconds watched
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    user = relationship("User", back_populates="progress")
    lesson = relationship("Lesson", back_populates="progress")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', 'lesson_id', name='unique_user_course_lesson_progress'),
    )

class Certificate(Base):
    __tablename__ = "certificates"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    certificate_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    course_id = Column(UUID(as_uuid=False), ForeignKey("courses.id"), nullable=False)
    
    file_key = Column(String(255))
    file_url = Column(String(512))
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    user = relationship("User", back_populates="certificates")

class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    quiz_id = Column(String(50), unique=True, nullable=False, index=True)
    course_id = Column(UUID(as_uuid=False), ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(UUID(as_uuid=False), ForeignKey("lessons.id"), nullable=True)
    
    title = Column(String(255), nullable=False)
    questions = Column(JSON, default=list)
    passing_score = Column(Integer, default=70)
    is_timed = Column(Boolean, default=False)
    time_limit = Column(Integer, nullable=True)  # minutes
    published = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    course = relationship("Course", back_populates="quizzes")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    quiz_id = Column(UUID(as_uuid=False), ForeignKey("quizzes.id"), nullable=False)
    
    score = Column(Integer, nullable=False)
    passed = Column(Boolean, default=False)
    answers = Column(JSON, default=list)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    course_id = Column(UUID(as_uuid=False), ForeignKey("courses.id"), nullable=False)
    
    rating = Column(Integer, nullable=False)
    text = Column(Text)
    verified = Column(Boolean, default=False)
    name = Column(String(100))
    role = Column(String(160))
    display_order = Column(Integer, default=0)
    is_landing = Column(Boolean, default=False)
    is_sample = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    user = relationship("User", back_populates="reviews")
    course = relationship("Course", back_populates="reviews")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', name='unique_user_course_review'),
    )

class Coupon(Base):
    __tablename__ = "coupons"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    code = Column(String(50), unique=True, nullable=False, index=True)
    
    discount_type = Column(String(20), default="percentage")  # percentage, fixed
    discount_value = Column(Float, nullable=False)
    max_uses = Column(Integer)
    used_count = Column(Integer, default=0)
    
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))
    active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    notification_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    message = Column(Text)
    type = Column(String(20), default="info")  # info, commission, referral, certificate, quiz, payout
    read = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    user = relationship("User", back_populates="notifications")

class MediaAccessLog(Base):
    __tablename__ = "media_access_logs"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    
    media_type = Column(String(20))  # video, pdf, image
    media_id = Column(String(50))
    file_key = Column(String(255))
    action = Column(String(20))  # view, download, upload
    
    ip_address = Column(String(50))
    user_agent = Column(String(512))
    
    created_at = Column(DateTime(timezone=True), default=utc_now)

class EmailLog(Base):
    __tablename__ = "email_logs"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    
    email_type = Column(String(50), nullable=False)  # welcome, purchase, commission, payout, nudge
    to_email = Column(String(255), nullable=False)
    subject = Column(String(255))
    
    resend_id = Column(String(100))
    status = Column(String(20), default="sent")  # sent, failed, bounced
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)

class Media(Base):
    __tablename__ = "media"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    media_id = Column(String(50), unique=True, nullable=False, index=True)
    
    file_key = Column(String(255), nullable=False)
    file_name = Column(String(255))
    file_type = Column(String(20))  # video, pdf, image
    content_type = Column(String(100))
    file_size = Column(Integer)
    
    course_id = Column(UUID(as_uuid=False), ForeignKey("courses.id"), nullable=True)
    lesson_id = Column(UUID(as_uuid=False), ForeignKey("lessons.id"), nullable=True)
    
    storage_mode = Column(String(20), default="mock")  # mock, r2, s3
    status = Column(String(20), default="ready")  # processing, ready
    is_free_preview = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    
    uploaded_by = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=utc_now)


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    category_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    # Retained to preserve historical data; new inline categories are flat.
    parent_id = Column(UUID(as_uuid=False), ForeignKey("categories.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    


class LandingPage(Base):
    __tablename__ = "landing_pages"
    slug = Column(String(80), primary_key=True)
    settings = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class LandingEvent(Base):
    __tablename__ = "landing_events"
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    event_id = Column(String(100), unique=True, nullable=False)
    visitor_id = Column(String(80), nullable=False, index=True)
    event = Column(String(40), nullable=False, index=True)
    browser_type = Column(String(20), nullable=False)
    referral_code = Column(String(100))
    details = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)
