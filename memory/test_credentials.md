# Mera Mentor - Test Credentials

## Test Users (login via Google OAuth on the UI)
- Admin: admin@meramentor.in  (email listed in ADMIN_EMAILS env var → auto-admin on first sign-in)
- User:  test@meramentor.in

## Admin session token creation (for API-only testing when Google OAuth is not available)
Because the app uses real Google OAuth, an automated test cannot go through Google's consent screen.
For programmatic backend testing, seed a session directly:

```python
# From /app/backend/
import asyncio, secrets
from datetime import datetime, timezone, timedelta
from lib.database import async_session_maker
from models.models import User, UserSession
from sqlalchemy import select

async def make_admin_session():
    async with async_session_maker() as db:
        # Upsert admin user
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
            db.add(u); await db.flush()
        token = secrets.token_urlsafe(48)
        db.add(UserSession(
            user_id=str(u.id),
            session_token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        ))
        await db.commit()
        print(token)

asyncio.run(make_admin_session())
```
Then use the returned token as `Cookie: session_token=<token>` or `Authorization: Bearer <token>`.

## Razorpay Test Keys (active in backend/.env)
- RAZORPAY_KEY_ID: rzp_test_SKU3kjkJnpAHOF
- RAZORPAY_KEY_SECRET: 0EMJUdvDSKKqPAzDmJGh95mQ
- Mode: TEST

## Razorpay Test Card
- Card Number: 4111 1111 1111 1111
- Expiry: any future date
- CVV: any 3 digits
- OTP: 1234

## Supabase PostgreSQL
- DATABASE_URL is set in /app/backend/.env (Supabase pooler URL)

## Cloudflare R2 Object Storage
- Env vars: CLOUDFLARE_R2_ACCOUNT_ID, CLOUDFLARE_R2_ACCESS_KEY_ID, CLOUDFLARE_R2_SECRET_ACCESS_KEY, CLOUDFLARE_R2_BUCKET_NAME
- **NOT configured in local dev** — set on Render only.
- When absent: `is_storage_enabled()` → False, `/api/admin/media/upload` → 503 with a clear message.

## Google OAuth
- Env vars: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, SESSION_SECRET
- **NOT configured in local dev** — set on Render only.
- When absent locally: `/api/auth/google/login` → 500 with "GOOGLE_CLIENT_ID is not set" (fail-fast).

## Seed Data
- 5 courses available in DB
- Coupon: LAUNCH20 (20% off)
