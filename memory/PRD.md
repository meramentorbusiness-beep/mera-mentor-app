# Mera Mentor - Multi-Level Referral & Commission Dashboard

## Original Problem Statement
Build a Multi-Level Referral & Commission Dashboard for an online course platform called "Mera Mentor" with tagline "Seekho. Sikhao. Kamao." (Learn. Teach. Earn.)

## Current Architecture (Post-Migration)
- **Frontend**: React + Tailwind CSS + Shadcn UI + Recharts + react-d3-tree
- **Backend**: FastAPI (Python) with SQLAlchemy async
- **Database**: PostgreSQL (Supabase) ✅ MIGRATED FROM MONGODB
- **Auth**: Direct Google OAuth 2.0 authorization-code/OIDC + session cookies (no OTP)
- **Payments**: Real Razorpay SDK in TEST mode; signature, ownership and captured-payment checks required. No simulated success fallback.
- **Storage**: Cloudflare R2 integration; credentials absent in current preview, uploads unavailable (not mocked).
- **Email**: Resend (ready when API key provided)
- **Public landing**: `/courses/data-analytics`, isolated React entry with dashboard/router/charts loaded only outside the public route. Standalone CSS, self-hosted Plus Jakarta Sans, WebP images.
- **Current preview database**: isolated PostgreSQL 15 at the DATABASE_URL in backend `.env`; production Supabase data/credentials were not present in this fork. Data and opt-in local startup configuration persist in `/app/.local/postgresql`. Production Supabase architecture remains unchanged.

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

## Deploy-blocker + R2 upload hardening (Sep 2, 2026)
- **Render build failure** — `lucide-react` was `^0.507.0`; without a shipped `yarn.lock`, Render's fresh install resolved to a newer version where the `Eye` icon export path had shifted, causing CRA build to fail. Pinned to exact `0.507.0` in `frontend/package.json`. Verified with `CI=true DISABLE_ESLINT_PLUGIN=true yarn build` (Render's exact flags) → Compiled successfully.
- **`/api/admin/media/upload` 500** — the 500 the user saw was actually the previously-deployed OLD Emergent-storage code still running (since the build blocker prevented the new R2 code from deploying). Hardened the endpoint (server.py:1533) to short-circuit with **HTTP 503 + clear env-var list** when R2 isn't configured, and wraps the boto3 call in try/except returning **HTTP 502** with a clean error message on upload failure (real error logged server-side via `logging.exception`).
- **`GET /api/purchases`** — added (was missing, causing `Courses.js .some()` crash). Returns current user's completed purchases with public `course_id` string.
- Testing agent iteration 7 report: 10/10 backend tests passed, R2 client wiring verified via boto3 stubs, frontend production build verified.


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
- **Razorpay**: Real TEST order creation verified; no live payment completion tested. Webhook refuses requests until its secret is configured.
- **Google OAuth**: User-provided credentials configured server-side. User added the exact preview callback on 2026-09-21; Google sign-in form now opens without redirect mismatch. Actual user consent/callback is a manual verification step.
- **Resend**: Ready (needs RESEND_API_KEY).
- **Cloudflare R2**: Current storage integration; unavailable in this preview without R2 credentials.
- **Superprofile webinar**: Direct outbound signup link `https://superprofile.bio/e/CFnAGrLC`; ref/UTM parameters carried through. Only outbound clicks are measured, not external registration completion.

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

## Data Analytics Landing Page — 2026-09-21

### User requirements and explicit choices
- New standalone, public single-scroll `/courses/data-analytics`, course fee ₹1,299, orange/dark Mera Mentor branding, Hinglish copy, Instagram-first mobile experience, no videos.
- Eleven sections: outcome hero and dual CTAs; pain points; five exact skill areas; salary ROI; five-level referral calculator; curriculum accordions; 20 initial reviews; instructor credibility; pricing/seats/checklist/no-refund disclosure; eight exact FAQs; final CTAs and signup. Footer support, configurable WhatsApp/social links, terms/privacy.
- Initially requested phone OTP for in-app browsers; user explicitly overrode with **“don't go for otp verfication”**. No phone authentication/OTP added. Instagram/Facebook users get a sticky banner and external-browser instructions; regular browsers use existing direct Google OAuth.
- User supplied `https://superprofile.bio/e/CFnAGrLC` and requested all webinar buttons link directly to it. No competing webinar registration form was created.
- User supplied Google client credentials; secret is only in backend `.env`, never frontend source. User confirmed adding `${REACT_APP_BACKEND_URL}/api/auth/google/callback` to Google Cloud.
- Speed target <1.5s; mobile-first at 375px; 48px controls, 16px functional text; static WebP hero <150KB; lazy instructor image, CSS-only animations, no carousel/animation library, inline critical CSS, single limited-weight Google Font self-hosted.

### Implemented and verified
- Bold illustrated hero with generated course-workspace bitmap (17,322 bytes), real instructor image from webinar page (14,344-byte WebP), Plus Jakarta Sans variable font (27,348 bytes). No course video or iframe is created.
- All webinar CTAs open Superprofile with attribution; course exploration scrolls to pricing. Sticky bottom webinar/buy bar appears on scroll.
- User-agent detection handles Instagram/FBAN/FBAV. Browser dialog has iOS menu/copy guidance and Android Chrome intent. It does not claim JavaScript can force Safari to open.
- URL referral is persisted with storage-failure handling and passed through webinar URLs, signed OAuth state, browser handoff and order initiation. Regular-browser ref query is cleaned only after successful persistence. In-app query is deliberately retained so the native Open in Browser menu preserves attribution across isolated storage.
- Existing OAuth signed-state flow extended with visitor/browser/intent and nonce verification. New verified accounts inherit referred_by_id/referral_chain. Returning accounts are not re-attributed. Purchase intent resumes checkout; normal signup redirects to dashboard.
- Salary calculator uses explicit ₹45,000/month scenario, handles positive/zero/negative differences honestly. Annual salary-to-fee comparison is labelled illustrative, not investment ROI or a placement promise.
- Referral calculator: rounded estimates ₹440/132/66/33/11. Direct 5 referrals = ₹2,200; direct 3 = ₹1,320. Full 5-level scenario with five purchases per person = ₹68,750; per-level breakdown shown. This intentionally corrects the mathematically inconsistent requested ₹13,700 example rather than fabricating a total. Actual linked-course commissions use the ₹1,101 pre-tax base and exact percentages.
- Six suggested roadmap modules over 24 weeks (not fabricated lesson durations), eight FAQs, no-refund note, full inclusion checklist.
- `Review` model extended with name, optional role, display_order, is_landing, is_sample. Existing student/course reviews preserved; marketing samples are excluded from actual course rating aggregation. Twenty generated testimonials are visibly SAMPLE-labelled.
- Admin → Courses → Landing page: add/edit/delete/rate/order/sample-label reviews; link course; edit filled/total seats; instructor details; student count/rating; support email; WhatsApp and social URLs. Unknown WhatsApp/Instagram URLs are hidden until configured.
- First-party LandingEvent analytics: views, webinar/course clicks, calculators, signup starts; server-confirmed new signup/purchase events; deduplication, validation and browser comparison. No client-forged conversion events accepted. Admin dashboard shows last 30 days.
- Razorpay SDK loaded only on purchase. Existing payment code hardened: no fake orders, required signatures, buyer ownership, captured provider amount/currency/order validation, draft rejection, retry reuse and fail-closed webhook. Purchase events use stored visitor origin.
- New authenticated admin courses endpoint includes drafts; old published-only admin listing fixed.

### Architecture / files
- `/app/frontend/src/index.js`: standalone landing vs asynchronous existing dashboard app.
- `/app/frontend/src/landing/`: DataAnalyticsLandingPage.js, Sections.js, Calculators.js, Dialogs.js, client.js, content.js, landing.css.
- `/app/frontend/src/components/admin/LandingManager.js`: admin controls, review editor and analytics.
- `/app/frontend/public/landing/`: compressed generated hero, actual instructor portrait, self-hosted font.
- `/app/backend/routes/landing.py`: public content/events and protected settings/review/analytics APIs.
- `/app/backend/services/landing_seed.py`: repeatable migrations, one-time labelled samples and safe draft course.
- `/app/backend/models/models.py`: Review additions, LandingPage, LandingEvent, purchase attribution columns.
- `/app/backend/routes/google_auth.py`: existing direct Google OAuth with signed attribution and verified conversion event.
- `/app/backend/services/preview_database.py`: opt-in, loopback-only preview PostgreSQL recovery before init_db. Config/data persist under `/app`; remote Supabase never starts a local process and still requires SSL.

### Testing and verification
- Testing report `/app/test_reports/iteration_8.json`; tests `/app/backend/tests/test_landing_iteration8_regression.py`.
- 15/15 backend regression tests passed initially and again after follow-ups; final JUnit `/app/test_reports/pytest/pytest_iteration8_final.xml`.
- Frontend tested at 320,375,390,428,768,1024,1440 widths: no horizontal overflow, working calculators, accordions, mobile reviews, sticky CTAs, legal dialogs and admin review CRUD.
- Production build passes: initial landing JS 97.78KB gzip and CSS 8.08KB gzip. Dashboard chunks deferred. One preview navigation DOMContentLoaded measurement ~528ms; this is **not** a guaranteed <1.5s mobile-data LCP/load measurement. Real-device slow-network testing remains.
- Follow-up Playwright: regular referral capture/URL cleanup/reload preservation; Instagram ref/native handoff preserved, browser modal closes, no OTP; zero video and zero iframe on clean application loads.
- Initial intermittent hidden iframe was reproduced in a Cloudflare hosting challenge, not application media. Do not strip external security challenges. No app iframe or video component exists.
- Google redirect_uri_mismatch was resolved by user allowlisting callback; real Google sign-in form confirmed. No real Google account credentials/consent were used by automated tests, so full callback/session creation remains user verification.
- Real Razorpay TEST order creation/retry/ownership rejection passed; no real captured transaction was performed.
- Preview DB stopped after inactivity because ephemeral system config reset. Added guarded persistent startup helper; cold startup restored database and /api/health=200; regression suite passed afterward.

### Current limitations (not mocked)
- Production Supabase credentials/data are not in preview. `course_data_analytics` is a deliberate **DRAFT**, not a purchasable empty placeholder. Admin must link/publish an actual ₹1,299 course with real content to open checkout.
- Reviews are SAMPLE content, not verified endorsements. Replace with authentic reviews and verify supplied 500+/4.8 metrics. Instructor source webinar says 2.5+ years; landing uses user's explicitly supplied 4+ years, so confirm before promotion.
- Google real-user callback and completed payment still require manual verification; provider initiation is verified.
- Superprofile registration completions cannot be tracked without a supported provider callback; only click/ref links implemented.
- WhatsApp and Instagram contact/profile details were not provided; editable but not invented.
- Resend, R2 preview credentials and Razorpay webhook secret remain unconfigured. No runtime APIs are mocked.

### Prioritized next actions
- **P0 / user verification**: complete real Google sign-in; restore the intended existing Supabase connection or provide real content in preview; link/publish actual ₹1,299 course and verify a complete test purchase.
- **P1**: replace sample reviews, confirm mentor experience/social-proof metrics, add WhatsApp/Instagram links; configure payment webhook and missing email/storage credentials; test on real Instagram iOS/Android with mobile network throttling.
- **P1 / previous scope**: comprehensive quiz/category/PDF resource regression remains pending from the previous session; this landing iteration did not claim to complete it.
- **P2**: split large existing server.py/AdminCourses.js further; provider-confirmed webinar signup attribution; measure/A-B test webinar CTA conversion using existing analytics.
