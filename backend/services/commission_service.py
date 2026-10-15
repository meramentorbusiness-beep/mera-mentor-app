# Commission Service for Mera Mentor
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from models.models import User, Purchase, Commission, CommissionStatus
from services.email_service import send_commission_earned

# Commission rates from environment (default: 40%, 12%, 6%, 3%, 1%)
COMMISSION_RATES = {
    1: float(os.environ.get("COMMISSION_L1", "").strip() or "40") / 100,
    2: float(os.environ.get("COMMISSION_L2", "").strip() or "12") / 100,
    3: float(os.environ.get("COMMISSION_L3", "").strip() or "6") / 100,
    4: float(os.environ.get("COMMISSION_L4", "").strip() or "3") / 100,
    5: float(os.environ.get("COMMISSION_L5", "").strip() or "1") / 100,
}

def get_commission_levels() -> List[Dict]:
    """Get commission levels configuration"""
    example_price = 799
    return [
        {
            "level": level,
            "percentage": rate * 100,
            "example_earning": round(example_price * rate, 2)
        }
        for level, rate in COMMISSION_RATES.items()
    ]

def get_total_commission_rate() -> float:
    """Get total commission rate (sum of all levels)"""
    return sum(COMMISSION_RATES.values())

def calculate_commission(amount: float, level: int) -> float:
    """Calculate commission for a specific level"""
    rate = COMMISSION_RATES.get(level, 0)
    return round(amount * rate, 2)

async def process_commissions(
    db: AsyncSession,
    purchase_id: str,
    buyer_id: str,
    amount: float
) -> List[Commission]:
    """
    Process commissions for a purchase.
    Walks up the referral chain and creates commission records.
    """
    # Get buyer with referral chain
    stmt = select(User).where(User.id == buyer_id)
    result = await db.execute(stmt)
    buyer = result.scalar_one_or_none()
    
    if not buyer or not buyer.referral_chain:
        return []
    
    # Check for duplicate commissions
    stmt = select(Commission).where(Commission.purchase_id == purchase_id)
    result = await db.execute(stmt)
    existing = result.scalars().all()
    if existing:
        return []  # Already processed
    
    commissions = []
    referral_chain = buyer.referral_chain[:5]  # Max 5 levels
    
    for level, referrer_id in enumerate(referral_chain, start=1):
        # Get referrer
        stmt = select(User).where(User.id == referrer_id)
        result = await db.execute(stmt)
        referrer = result.scalar_one_or_none()
        
        if not referrer:
            continue
        
        rate = COMMISSION_RATES.get(level, 0)
        if rate == 0:
            break
        
        commission_amount = calculate_commission(amount, level)
        
        # Create commission record
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
        
        # Get total earnings for email
        stmt = select(func.sum(Commission.amount)).where(
            Commission.earned_by_id == referrer_id,
            Commission.status.in_([CommissionStatus.PENDING.value, CommissionStatus.APPROVED.value])
        )
        result = await db.execute(stmt)
        total_earned = result.scalar() or 0
        total_earned += commission_amount
        
        # Send email notification (non-blocking)
        try:
            await send_commission_earned(
                user_email=referrer.email,
                user_name=referrer.name,
                amount=commission_amount,
                from_user_name=buyer.name,
                level=level,
                total_earned=total_earned
            )
        except Exception as e:
            print(f"Error sending commission email: {e}")
    
    await db.commit()
    return commissions

async def reverse_commissions(db: AsyncSession, purchase_id: str) -> int:
    """
    Reverse commissions for a refunded purchase.
    - Pending commissions are deleted
    - Approved/Paid commissions are marked as reversed
    """
    stmt = select(Commission).where(Commission.purchase_id == purchase_id)
    result = await db.execute(stmt)
    commissions = result.scalars().all()
    
    reversed_count = 0
    for commission in commissions:
        if commission.status == CommissionStatus.PENDING.value:
            await db.delete(commission)
        else:
            commission.status = CommissionStatus.REVERSED.value
        reversed_count += 1
    
    await db.commit()
    return reversed_count

async def auto_approve_commissions(db: AsyncSession) -> int:
    """
    Auto-approve commissions older than 7 days.
    Called by cron job daily.
    """
    from datetime import timedelta
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    
    stmt = select(Commission).where(
        Commission.status == CommissionStatus.PENDING.value,
        Commission.created_at <= cutoff
    )
    result = await db.execute(stmt)
    commissions = result.scalars().all()
    
    approved_count = 0
    for commission in commissions:
        commission.status = CommissionStatus.APPROVED.value
        commission.approved_at = datetime.now(timezone.utc)
        approved_count += 1
    
    await db.commit()
    return approved_count

async def get_wallet_balance(db: AsyncSession, user_id: str) -> Dict:
    """Get wallet balance breakdown for a user"""
    # Total earned (approved + paid)
    stmt = select(func.sum(Commission.amount)).where(
        Commission.earned_by_id == user_id,
        Commission.status.in_([CommissionStatus.APPROVED.value, CommissionStatus.PAID.value])
    )
    result = await db.execute(stmt)
    total_earned = result.scalar() or 0
    
    # Withdrawable (approved only)
    stmt = select(func.sum(Commission.amount)).where(
        Commission.earned_by_id == user_id,
        Commission.status == CommissionStatus.APPROVED.value
    )
    result = await db.execute(stmt)
    withdrawable = result.scalar() or 0
    
    # Pending (not yet approved)
    stmt = select(func.sum(Commission.amount)).where(
        Commission.earned_by_id == user_id,
        Commission.status == CommissionStatus.PENDING.value
    )
    result = await db.execute(stmt)
    pending = result.scalar() or 0
    
    # Paid out
    stmt = select(func.sum(Commission.amount)).where(
        Commission.earned_by_id == user_id,
        Commission.status == CommissionStatus.PAID.value
    )
    result = await db.execute(stmt)
    paid_out = result.scalar() or 0
    
    return {
        "balance": withdrawable,
        "total_earned": total_earned + pending,
        "withdrawable": withdrawable,
        "pending": pending,
        "paid_out": paid_out,
        "total_withdrawn": paid_out,
    }

async def get_commission_history(db: AsyncSession, user_id: str, limit: int = 50) -> List[Dict]:
    """Get commission transaction history for a user"""
    stmt = select(Commission).where(
        Commission.earned_by_id == user_id
    ).order_by(Commission.created_at.desc()).limit(limit)
    
    result = await db.execute(stmt)
    commissions = result.scalars().all()
    
    history = []
    for c in commissions:
        # Get from_user details
        stmt = select(User).where(User.id == c.from_user_id)
        result = await db.execute(stmt)
        from_user = result.scalar_one_or_none()
        
        history.append({
            "commission_id": c.commission_id,
            "amount": c.amount,
            "level": c.level,
            "rate": c.rate,
            "status": c.status,
            "from_user_name": from_user.name if from_user else "Unknown",
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "approved_at": c.approved_at.isoformat() if c.approved_at else None,
        })
    
    return history
