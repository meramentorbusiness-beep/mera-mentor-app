"""Seed an admin session and print the token. Run once before backend tests."""
import asyncio, secrets, sys, os
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.database import async_session_maker
from models.models import User, UserSession
from sqlalchemy import select


async def make_admin_session():
    async with async_session_maker() as db:
        r = await db.execute(select(User).where(User.email == "admin@meramentor.in"))
        u = r.scalar_one_or_none()
        if not u:
            u = User(
                email="admin@meramentor.in",
                name="Admin Test",
                role="admin",
                referral_code="MMMTEST0001",
                google_id="test-admin-google-id",
            )
            db.add(u)
            await db.flush()
        token = secrets.token_urlsafe(48)
        db.add(UserSession(
            user_id=str(u.id),
            session_token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        ))
        await db.commit()
        print(token)


if __name__ == "__main__":
    asyncio.run(make_admin_session())
