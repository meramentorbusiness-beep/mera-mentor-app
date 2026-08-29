# Mera Mentor - Multi-Level Referral & Commission Dashboard

## Original Problem Statement
Build a Multi-Level Referral & Commission Dashboard for an online course platform called "Mera Mentor" with tagline "Seekho. Sikhao. Kamao." (Learn. Teach. Earn.)

## Current Architecture (Post-Migration)
- **Frontend**: React + Tailwind CSS + Shadcn UI + Recharts + react-d3-tree
- **Backend**: FastAPI (Python) with SQLAlchemy async
- **Database**: PostgreSQL (Supabase) ✅ MIGRATED FROM MONGODB
- **Auth**: Emergent Google OAuth + session cookies
- **Payments**: Razorpay (MOCK mode)
- **Storage**: Local mock (ready for Cloudflare R2)
- **Email**: Resend (ready when API key provided)

## Commission Structure (5 Levels)
| Level | Rate | Example (₹799 course) |
|-------|------|----------------------|
| L1 (Direct) | 40% | ₹319.60 |
| L2 | 12% | ₹95.88 |
| L3 | 6% | ₹47.94 |
| L4 | 3% | ₹23.97 |
| L5 | 1% | ₹7.99 |
| **Total** | **62%** | **₹495.38** |
| **Platform Keeps** | **38%** | **₹303.62** |


## Deployment Fixes (Aug 29, 2026)
- Removed non-existent `emergentintegrations==0.1.0` from `backend/requirements.txt` (Render pip install was failing; package was never imported anywhere in `/app/backend/`).
- Bumped Docker frontend build stage from `node:18-slim` → `node:20-slim` in `/app/Dockerfile` to satisfy `react-router-dom@7.x` engine requirement of `node >=20.0.0`.
- Verified locally: `pip install -r requirements.txt` exit 0, `yarn install` exit 0 on Node 20.

## Emergent Removal + Real Google OAuth + Cloudflare R2 (Aug 29, 2026)
- **Removed all Emergent references** from application code, comments, env-var names, storage `mode` labels, and `render.yaml`. Only remaining `emergent` strings are `REACT_APP_BACKEND_URL` in `frontend/.env` (system-protected preview URL, overridden on Render).
- **Replaced Emergent-brokered Google auth** with a real Google OAuth 2.0 Authorization Code + OIDC flow. New file `backend/routes/google_auth.py` exposes `GET /api/auth/google/login` and `GET /api/auth/google/callback`. Signed CSRF state carries the referral code through the Google round-trip. ID token verified via `google-auth` (audience + issuer + email_verified). Session cookie unchanged (`session_token`, httpOnly, Secure, SameSite=None, 30-day).
- **Removed the broken `POST /api/auth/session`** endpoint (the frontend was sending `{session_id}` while the backend expected `{user: {...}}` — flow was end-to-end broken).
- **Replaced Emergent Object Storage with Cloudflare R2** via boto3 S3-compatible client (`backend/services/storage_service.py`). Same public API (`upload_file`, `download_file`, `is_storage_enabled`), so upstream media routes did not change. `is_storage_enabled()` returns `False` and uploads short-circuit when R2 env vars are absent (currently the case in local dev). Added `presigned_get_url()` for future direct video streaming.
- **Frontend**: `Login.js` and `ReferralLanding.js` now redirect to `${REACT_APP_BACKEND_URL}/api/auth/google/login?ref=<code>`. Removed the hash-based `AuthCallback` component from `App.js` (no longer needed; OAuth flow now uses a cookie-set redirect).
- **Deps**: Added `itsdangerous==2.2.0` for signed OAuth state. `google-auth`, `boto3`, `httpx` already present.
- Verified locally: backend starts clean, health returns `storage_mode: r2`, `/api/auth/google/login` returns clean 500 with "GOOGLE_CLIENT_ID is not set" until user sets env vars on Render, old `/api/auth/session` returns 404, frontend compiles without errors.

### Env vars user must set on Render for Google OAuth to work:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI` = `https://<render-app>.onrender.com/api/auth/google/callback`
- `SESSION_SECRET` (random string, generate via `python -c "import secrets; print(secrets.token_urlsafe(64))"`)
- `FRONTEND_URL` = `https://<render-app>.onrender.com` (already wired in render.yaml)

### Env vars user must set on Render for R2 uploads:
- `CLOUDFLARE_R2_ACCOUNT_ID`
- `CLOUDFLARE_R2_ACCESS_KEY_ID`
- `CLOUDFLARE_R2_SECRET_ACCESS_KEY`
- `CLOUDFLARE_R2_BUCKET_NAME`

### Google Cloud Console → Credentials → OAuth 2.0 Client (Web app):
Authorized redirect URI (exact, no trailing slash): `https://<render-app>.onrender.com/api/auth/google/callback`



## Migration Completed (Feb 27, 2026)

### What Changed
1. **Database**: MongoDB → PostgreSQL (Supabase)
2. **ORM**: Motor (MongoDB) → SQLAlchemy async
3. **Connection**: Supabase Pooler with SSL
4. **All queries**: Rewritten to use SQL via SQLAlchemy

### Database URL
```
postgresql+asyncpg://postgres.bxfcsmkxyoqrydpydvul:****@aws-1-ap-south-1.pooler.supabase.com:5432/postgres
```

### Tables Created in Supabase
- users, user_sessions
- courses, lessons, resources
- purchases, commissions, payouts
- course_progress, certificates
- quizzes, quiz_attempts, reviews
- coupons, notifications
- media, media_access_logs, email_logs

## Testing Results (Feb 27, 2026)
- **Backend**: 33/33 tests passed (100%)
- **Frontend**: All pages verified working
- **Test File**: `/app/backend/tests/test_postgresql_migration.py`

## Files Structure
```
/app
├── backend/
│   ├── server.py           # FastAPI with SQLAlchemy (REWRITTEN)
│   ├── lib/
│   │   └── database.py     # Supabase PostgreSQL connection
│   ├── models/
│   │   └── models.py       # SQLAlchemy models
│   ├── services/
│   │   ├── storage_service.py   # R2 ready
│   │   ├── email_service.py     # Resend ready
│   │   └── commission_service.py
│   ├── tests/
│   │   └── test_postgresql_migration.py
│   ├── Dockerfile
│   ├── .env
│   └── .env.example
├── frontend/
│   ├── src/pages/
│   ├── vercel.json
│   └── .env.example
└── docker-compose.yml
```

## Environment Variables (.env)
```bash
# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql+asyncpg://...

# Commission (5 levels)
COMMISSION_L1=40
COMMISSION_L2=12
COMMISSION_L3=6
COMMISSION_L4=3
COMMISSION_L5=1

# Other
STORAGE_MODE=mock
FRONTEND_URL=https://meramentor.in
ADMIN_EMAILS=admin@meramentor.in
```

## API Endpoints (All Using PostgreSQL)

### Public
- `GET /api/health` - Health check (shows DB status)
- `GET /api/courses` - List courses
- `GET /api/courses/:id` - Course detail
- `GET /api/commission-levels` - 5 levels config

### Protected (Requires Auth)
- `POST /api/auth/session` - Google OAuth login
- `GET /api/auth/me` - Current user
- `GET /api/referrals/stats` - Referral statistics
- `GET /api/referrals/tree` - Referral tree visualization
- `GET /api/wallet` - Wallet balance
- `POST /api/wallet/payout` - Request payout
- `POST /api/payments/create-order` - Create order
- `POST /api/payments/verify` - Verify payment

### Admin
- `GET /api/admin/stats` - Platform stats
- `POST/PUT/DELETE /api/admin/courses` - Course CRUD
- `POST /api/admin/media/upload` - Media upload

## Integrated Systems
- **Razorpay**: ✅ LIVE (rzp_test_SKU3kjkJnpAHOF) — real order creation + signature verification + webhook
- **Emergent Object Storage**: ✅ LIVE — replacing local disk storage for media uploads
- **Resend**: ⏳ Ready (needs RESEND_API_KEY)
- **Cloudflare R2**: Replaced by Emergent Object Storage

## Seed Data in PostgreSQL
- 2 users (admin@meramentor.in, test@meramentor.in)
- 5 courses with lessons
- 1 coupon (LAUNCH20 - 20% off)

## Deployment (Render - Single Web Service)

### Root Dockerfile (multi-stage)
- Stage 1: Node 18 → builds React with `REACT_APP_BACKEND_URL=""`
- Stage 2: Python 3.11 → FastAPI serves API + React static files

### Files
- `/Dockerfile` — root-level, used by Render
- `/render.yaml` — Render config (dockerfilePath: ./Dockerfile)
- `/.dockerignore` — excludes node_modules, build artifacts
- `/docker-compose.yml` — local full-stack testing

### Render Setup
1. Connect GitHub repo in Render dashboard
2. Create Web Service → Docker
3. Set environment variables (see render.yaml for list)
4. Deploy

## Next Steps to Launch
1. ~~Add Razorpay keys for real payments~~ ✅ DONE
2. Add Resend API key for emails
3. Deploy to production
4. Add RAZORPAY_WEBHOOK_SECRET after pointing webhook URL in Razorpay dashboard
5. Switch to live keys (`rzp_live_...`) when ready
