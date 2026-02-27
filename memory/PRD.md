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

## MOCKED Systems (Add Keys to Enable)
- **Razorpay**: Payment gateway
- **Resend**: Email notifications
- **Cloudflare R2**: Cloud storage

## Seed Data in PostgreSQL
- 2 users (admin@meramentor.in, test@meramentor.in)
- 5 courses with lessons
- 1 coupon (LAUNCH20 - 20% off)

## Deployment Ready

### Backend (Hostinger/VPS)
```bash
docker-compose up -d
```

### Frontend (Vercel)
```bash
vercel --prod
```

## Next Steps to Launch
1. Add Razorpay keys for real payments
2. Add Resend API key for emails
3. Add Cloudflare R2 for cloud storage
4. Deploy to production
5. Launch meramentor.in 🚀
