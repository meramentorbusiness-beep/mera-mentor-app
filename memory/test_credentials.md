# Mera Mentor - Test Credentials

## Current preview configuration — 2026-09-21
- The fork arrived with no backend `.env` and no DATABASE_URL. Preview now uses an **isolated local PostgreSQL database**, not the production Supabase database. Production data has not been copied or modified.
- Backend secrets are in `/app/backend/.env`. Do not copy their values into frontend code or reports.
- User-provided Google client credentials are configured; callback is `${REACT_APP_BACKEND_URL}/api/auth/google/callback`. User confirmed allowlisting on 2026-09-21; Playwright verified the real Google sign-in form, without redirect mismatch. A full consent/callback still needs a real Google user.
- Existing recorded Razorpay test credentials are restored in backend `.env`; no new payment provider was added. Webhook secret is still missing, so unsigned/unconfigured webhooks are rejected.
- Webinar: `https://superprofile.bio/e/CFnAGrLC` (external signup; click/ref parameter tracking only, no external registration callback).
- No OTP authentication, per explicit user request.
- API-only preview users: `admin@meramentor.in` (admin, referral `MMTESTADMIN`) and `test@meramentor.in` (user, referral `MMTESTUSER`). No app passwords: Google OAuth is used for real login.
- Current 48-hour test session tokens are in `/app/.local/test.env`: `ADMIN_SESSION`, `USER_SESSION`. These sessions are test fixtures, not a public login bypass. Set browser `session_token` cookie on the current preview domain for admin UI testing.
- Existing fixture sessions renewed on 2026-09-28 for 48 hours for category-form regression; token values and account roles unchanged. No app login or OAuth behavior modified.
- Same fixture sessions renewed on 2026-10-03 for 48 hours for landing trust-content and Google-dashboard regression; token values/roles unchanged. Production credentials and publishing settings untouched.
- Local PostgreSQL data is under `/app/.local/postgresql` (ignored by git), using database settings from backend `.env`.
- `PREVIEW_POSTGRES_DATA` in backend `.env` opts into the guarded persistent local bootstrap. After inactivity, server startup restores this exact existing data, not an empty system cluster. Do not remove the data directory or initialize a replacement database. Supabase configurations must NOT set this preview-only flag.
- Preview bootstrap also uses `PREVIEW_POSTGRES_BIN` and `PREVIEW_RUNUSER` from backend `.env`, avoiding supervisor's minimal PATH after inactivity. PostgreSQL system runtime remains required. No production database setting changed.
- Landing course `course_data_analytics` is deliberately a **draft** until actual lessons are uploaded/published or an existing published ₹1,299 course is linked. Checkout must not sell empty placeholder content.
- Older entries below describe prior environments; current preview notes above take precedence.

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
