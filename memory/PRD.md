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
- `FRONTEND_URL` no longer used (removed 2026-10-23); optional `CORS_ORIGINS`, `GOOGLE_REDIRECT_URI`

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
# FRONTEND_URL removed — app is same-domain; redirects are relative
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

## Category Workflow Simplification — 2026-09-28 (current behavior)

### User requirement
Remove the separate folder/category management section. Inside the existing Create/Edit Course form, provide exactly one Category field: choose an existing database category from dropdown suggestions or type a new name; create it automatically only on successful course save. No new category page, route, admin section or separate creation flow. Preserve existing categories and course attachments. User reiterated this should make organizing courses with videos/resources into categories easy.

### Changes made
- `frontend/src/pages/AdminCourses.js`: removed the Settings **Course Categories** card, `CategoryManager`, `CategoryRow`, parent/root tree controls, category add/rename/delete handlers, associated local state and category-management icons/imports. Removed hardcoded fallback category choices.
- Replaced the select-only course category control with one labelled shadcn Input backed by native HTML datalist suggestions (no dependency added). It accepts an existing category or any new name, limits names to 100 characters, and refreshes database choices on opening the editor and after saving.
- `backend/server.py`: removed POST `/api/admin/categories`, PUT/DELETE `/api/admin/categories/{category_id}` and obsolete default-category startup seeding. Only read-only GET `/api/categories` remains, intentionally used by the course field. No new HTTP route or page was added.
- Course POST/PUT now resolve categories in the same database transaction as course save. Course creation uses flush rather than an early commit, so a failed save does not leave an orphan category/course. No category is created while typing or cancelling.
- `backend/services/course_categories.py`: small shared helper normalizes spaces, validates names, matches existing spelling case-insensitively, includes legacy Course.category values in suggestions, and uses a PostgreSQL transaction lock to prevent duplicate concurrent creation.
- `backend/models/models.py`: retained the actively used Category model/table and existing `parent_id` data; removed the obsolete hierarchy ORM relationship. No existing category or parent assignment was deleted/migrated. All newly created inline categories are flat.
- Category groups the course; its videos and PDF/resource URLs remain attached to that course. This does not create a new physical object-storage-folder workflow or move uploaded files.

### Verification / cleanup
- `/app/test_reports/iteration_9.json`: no backend/frontend bugs; 11/11 backend tests in `/app/backend/tests/test_inline_category_course_flow_iteration9.py` passed.
- Covered create/select/edit, category persistence/suggestions refresh, cancellation, whitespace/case dedupe, simultaneous saves, invalid input/no orphan behavior, category-only updates preserving video/PDF URLs, 401/403 admin protection, and removed write routes returning404.
- Desktop and 375px mobile checks passed; exactly one Category input, no standalone manager, no dialog horizontal overflow. Production build passes; only pre-existing hook-dependency warnings remain as optional tech debt.
- Source search confirmed no runtime references to CategoryManager/CategoryRow, category-management write URLs or old add/parent/rename/delete controls. Read-only suggestions + active Category model are deliberately retained, not dangling code.
- Main agent cleaned only the exact iteration9 test fixture course/category IDs after tests; existing categories/data preserved.
- Test sessions were renewed for48hours on2026-09-28; details remain in memory/test_credentials.md, no auth logic changed.
- Preview DB startup was blocked by supervisor's minimal PATH. Existing system PostgreSQL runtime/data were intact. Configured absolute PREVIEW_POSTGRES_BIN/PREVIEW_RUNUSER paths and updated the opt-in helper; health200, actual course persistence and tests verified. Remote Supabase behavior unchanged.

### Remaining / next actions
- **P0 for this request**: none; user can verify Admin → Courses → New Course → Category → Save Course.
- **Unchanged blocker**: actual R2 uploads cannot be verified/used in this preview without storage credentials. Attachment URL preservation was tested with explicit fixtures, not simulated upload success. No runtime category API is mocked.
- **Earlier backlog**: actual landing-course content, real Google user consent/full payment verification, provider credentials and full quiz regression remain as listed above; old standalone category-management tasks are superseded by this inline flow.
- **Optional future usability improvement**: a category filter on the existing course list only if requested; no additional management page.

## Landing Copy, Trust & Dashboard Connection — 2026-10-03 to 2026-10-12

### Latest user request / choices
- Main heading: keep both no-coding-background and two-month timeline. Remove “Hum Fluff Cut Kar Rahe Hain” entirely, no replacement heading in that slot.
- Add original trust-building inspired by bootcamp structure: honest job disclaimer with concrete learning/support commitments, optional outcome labels for real testimonials, market statistics ONLY with credible sources, repeat CTAs after important sections.
- Connect landing to existing dashboard via Google authentication. Show before/after copy and distinguish completed work from missing real data.
- Explicit choices: **leave module timings unspecified** (do not convert to an eight-week module plan); **keep clearly labelled sample reviews**.
- User previously stopped publishing. No publish/redeploy performed for this work; all verification is in preview. User returned after credit recharge on2026-10-12; continue same task, not new scope.

### Before → after
- Old H1: “6 Mahine Mein Data Analyst Ban Jao.” Old subline: “Bina Coding Background Ke.”
- New H1: **“No Coding Background? Become a Data Analyst in 2 Months.”** New subline: “Excel se AI tak. Step by step, apni pace pe.”
- “Hum Fluff Cut Kar Rahe Hain.” → deleted, with no replacement headline. Existing adjacent skills description now says “Excel se AI tak — yeh hai aapka data analytics skill stack”, avoiding the earlier job-guarantee phrasing.
- Removed all module duration fields and the24-week roadmap total. Six modules and lifetime revision remain; no invented replacement durations. Updated HTML description/title and runtime landing title.

### Implemented
- `LearningPromise.js`: original section after skills, “Skills par focus. Job ki guarantee nahi.” States hiring depends on practice/portfolio/interviews/market and two months is a learning goal, NOT a placement deadline. Commitments limited to existing offering: practical learning, webinar doubt support, lifetime access.
- CTAs retained in hero, curriculum, pricing, final block and sticky bar; added webinar/pricing links immediately after trust section, with existing referral/event tracking.
- Public hero now uses course facts (six modules, beginner friendly, lifetime access) instead of unverified500+/4.8 totals. Review summary no longer presents generated reviews as measured student satisfaction.
- Twenty SAMPLE testimonials remain publicly labelled per user choice. `Review.outcome` optional80-character field, repeatable migration, admin editor and API serialization/validation. Genuine reviews can have manually supplied concrete outcomes; samples have outcomes cleared server-side and never receive outcome badges. No genuine outcomes invented.
- `ReviewCard.js` handles safe optional outcome display. `LandingReviewEditor.js` extracts existing editor, adds outcome guidance and disables outcome field whileSample is selected. Unsupported aggregate-stat inputs removed from admin form; old metadata retained for backward-compatible settings saves only.
- `AccountButton.js`: Google sign-in at header and signup section for guests; Instagram/Facebook still receive external-browser guidance (noOTP). Existing authenticated users receive direct header/final Dashboard links.
- Landing checks existing secure server session at `/api/auth/me`, rather than trusting localStorage. Existing direct Google OAuth callback already saves session cookie and redirects signup to `/dashboard`; this flow preserved. Purchase intent still resumes checkout. No provider replacement or auth credentials exposed.
- Follow-up fixes from testing: replaced linked-course native select causing invalidDOM nesting with existing shadcn Select; removed requests to nonexistent notification-stream endpoint while preserving supported unread-count polling; deferred RazorpaySDK on admin/dashboard as well as landing using shared `/src/lib/razorpay.js`. Marketplace loads SDK on purchase and no longer has an obsolete fake-success demo branch.

### Not added / real content needed
- No market salary/openings/demand-growth strip added. Need dated, source-linked numbers for the intended job market. Competitor statistics were NOT copied or presented as Mera Mentor results.
- No real testimonial outcomes currently exist in preview: all20 initial reviews are samples. Admin capability is ready; owner must provide authentic testimonials and learner-reported outcomes before showing real tags.
- Existing salary ROI calculator remains explicitly an illustrative scenario, not a sourced average, forecast or guaranteed income. It was not relabelled as market research.
- Structure reference only: https://codebasics.io/bootcamps/data-analytics-bootcamp-with-practical-job-assistance (clear expectation-setting, outcomes, repeat CTAs). No competitor text, counts, refund policy, community or placement services copied.

### Verification
- Agent report `/app/test_reports/iteration_10.json`: newreview outcome/backend regressions19passed; copy, removedtimings, sample labeling, repeatedCTAs, Instagram behavior and responsive320/375/390/428/768/1024/1440 verified. Main smoke image `/app/.local/trust-page-smoke.jpg`.
- Main follow-up after fixes: linked-course selector and genuine/sample outcome editor pass, no invalid-select/hydration warnings, no404stream requests; checkout SDK absent until needed. One expected401from initial unauthenticated session probe is not a login failure.
- Browser test confirmed authenticated landing → existing protecteddashboard and guest Google entry → real Google sign-in form without redirect mismatch. Actual human Google consent/token callback has NOT been automated; owner should complete one real sign-in.
- Final production BUILD (not publish) passes2026-10-12: mainJS99.01KB gzip, mainCSS8.53KB gzip. Dashboard chunks remain deferred.
- Final pytest rerun: **19/19 passed**, `/app/test_reports/pytest/pytest_iteration10_final.xml`. No runtime APIs mocked. Temporary real-labelled outcome test reviews were deleted; finalpayment-fixture course/pendingpurchase from this run cleaned without touching actual content.
- Credit-pause/resume restored runtime files after app startup, leaving failed Uvicorn child offline. Added bounded120s wait for configured preview executables in opt-in helper; no credentials/ports/defaultDBs changed. Backend recovered with preserved data andhealth200. Prior investigation's supervisor-env hypothesis was not supported by the trace: .env is loaded and failure was the explicit executable-availability check, notKeyError. No supervisor secrets were copied into system config.
- During the nine-day pause,48-hour test sessions correctly expired. Only existing isolated test fixtures were renewed2026-10-12; real-user Google session/auth logic unchanged.

### Remaining priorities
- **P0 current request**: no known code blocker; user review of before/after and one actual Google sign-in remain.
- **P1 content**: authentic testimonials/outcomes and dated market statistics; mentor-experience/source verification from earlier notes remains.
- **Unchanged earlier blockers**: actual landing course remains draft until real content/linking; paymentsTESTmode, webhook secret absent, R2/email credentials absent. Production requires externalPostgreSQL configuration per earlier deploymentRCA; do NOT retry publishing without userrequest.
- **Optional trust improvement**: add a consenting learner’s real project snapshot alongside their reported outcome, when authentic evidence is available.

---

## 2026-06 (fork) — Public landing entry point + single CTA

### Problem
Opening the Render root URL went straight to `/login`; the Data Analytics landing page was not
reachable as the public entry point.

### Routing audit (before changes)
- `/` was wrapped in `ProtectedRoute` (`frontend/src/App.js:41`), whose effect pushed logged-out
  users to `/login` (`App.js:31`). This was the ONLY redirect-to-/login in the whole app — no
  backend redirect, no second guard.
- `/courses/data-analytics` is not a React Router route: `frontend/src/index.js:7-11` branches on
  `window.location.pathname` and renders the landing bundle directly (keeps dashboard/charts out of
  the public bundle).
- SPA fallback already present: `backend/server.py:2069-2075` serves `index.html` for all non-API
  paths; `Dockerfile` stage 2 copies the React build into `/app/static`. No change needed.
- OAuth callback already redirects to `/dashboard` (`backend/routes/google_auth.py:277,285`).
- Landing copy on main was already current: new headline, "Find Courses", no "Hum Fluff Cut Kar
  Rahe Hain" line. The live Render site was simply an older build.

### Implemented
- `frontend/src/App.js`: added public `RootEntry` route for `/` — logged-in users `Navigate` to
  `/dashboard`, logged-out users `window.location.replace('/courses/data-analytics')`. The protected
  `Layout` branch keeps all its children (`dashboard`, `referrals`, `wallet`, `courses`, `upsell`,
  `admin/courses`); only the old `index` redirect was removed.
- `frontend/src/landing/DataAnalyticsLandingPage.js`: "Find Courses" now routes logged-out students
  to `/login` (carrying `?ref=` when a referral code exists) instead of starting Google OAuth
  inline. Logged-in students still go to `/dashboard`. In-app (Instagram/Facebook) browsers still
  get the "open in browser" dialog. Google OAuth config, login route and redirect URI untouched.

### Route table
| Route | Access |
|---|---|
| `/` | public → landing (logged out) / `/dashboard` (logged in) |
| `/courses/data-analytics` | public (direct load + refresh) |
| `/login` | public; redirects to `/dashboard` if already signed in |
| `/ref/:code` | public |
| `/dashboard`, `/referrals`, `/wallet`, `/courses`, `/courses/:id`, `/upsell/:id`, `/admin/courses` | protected → `/login` |

### Verification (preview, screenshot tool)
- `/` logged out → landing renders with "Find Courses" hero CTA. PASS
- "Find Courses" logged out → `/login` ("Welcome back" / "Continue with Google"). PASS
- `/dashboard` logged out → `/login`. PASS
- `/courses/data-analytics` direct load → headline + hero render. PASS
- Logged in: landing navbar shows account name + logout (no Sign in button); `/` → `/dashboard`;
  `/login` → `/dashboard`. PASS
- "Free Webinar Join Karo" unchanged; ₹1,299 still shown in pricing card, final CTA and sticky bar.

### Notes / remaining
- Workspace has NO git remote configured (`git remote -v` empty, `git fetch` denied), so the agent
  cannot pull or push. User must use the "Save to GitHub" button, then redeploy on Render.
- Real Google consent flow still only verifiable by the owner on the live domain.
