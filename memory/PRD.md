# Mera Mentor - Multi-Level Referral & Commission Dashboard

## Original Problem Statement
Build a Multi-Level Referral & Commission Dashboard for an online course platform called "Mera Mentor" with tagline "Seekho. Sikhao. Kamao." (Learn. Teach. Earn.)

## User Personas
- **Learners/Users**: Sign up, browse/purchase courses, share referral links, earn commissions
- **Admin**: Manage courses (upload video lessons via YouTube, PDF resources), view platform stats

## Core Architecture
- **Frontend**: React + Tailwind CSS + Shadcn UI + Recharts + react-d3-tree
- **Backend**: FastAPI (Python) + MongoDB (current) / PostgreSQL (ready)
- **Auth**: Emergent Google OAuth + session cookies
- **Payments**: Razorpay (MOCK mode until keys provided)
- **Storage**: Mock local storage (ready for Cloudflare R2)
- **Email**: Resend (ready when API key provided)
- **Real-time**: Server-Sent Events (SSE) for notifications

## Commission Structure (5 Levels)
| Level | Rate | Example (₹799 course) |
|-------|------|----------------------|
| L1 (Direct) | 40% | ₹319.60 |
| L2 | 12% | ₹95.88 |
| L3 | 6% | ₹47.94 |
| L4 | 3% | ₹23.97 |
| L5 | 1% | ₹7.99 |
| **Total** | **62%** | **₹495.38** |
| **Platform** | **38%** | **₹303.62** |

### Earning Potential Calculator
```
Sirf 5 logo ko refer karo, woh bhi 5-5 karein:
L1 (5 people)    × ₹320 = ₹1,600
L2 (25 people)   × ₹96  = ₹2,400
L3 (125 people)  × ₹48  = ₹6,000
L4 (625 people)  × ₹24  = ₹15,000
L5 (3125 people) × ₹8   = ₹25,000
─────────────────────────────────
Total potential: ₹50,000+ 🔥
```

## What's Been Implemented

### Phase 1 - MVP ✅
- Google OAuth login with referral code capture
- Dashboard with earnings stats, referral link, QR code
- Referred Users list with tabs
- Commission Wallet with payout requests
- Course Marketplace with purchase flow
- Admin Panel - course CRUD

### Phase 2 - Advanced Features ✅
- Course Progress Tracking
- Certificate Generation
- Quiz System
- Reviews & Ratings
- Leaderboard
- Commission Analytics Charts
- Coupon System
- Notifications (SSE real-time)
- Gamification (streaks, XP)

### Phase 3 - Batch 3 ✅
- Referral Tree Visualization (react-d3-tree)
- Payout Improvements (TDS, estimated dates, receipts)

### Phase 4 - Production Ready ✅
1. **Commission Updated**: 7 levels → 5 levels (saves 18% per sale)
2. **Media Upload System**: Drag-drop, progress bar, library
3. **Cloudflare R2 Ready**: Storage service with presigned URLs
4. **Resend Email Ready**: Welcome, purchase, commission, payout emails
5. **Health Check Endpoint**: `/api/health`
6. **Docker Configuration**: Dockerfile + docker-compose.yml
7. **Environment Variables**: All configs from .env
8. **PostgreSQL Models**: SQLAlchemy models ready for migration

## File Structure
```
/app
├── backend/
│   ├── server.py                 # FastAPI main app
│   ├── models/
│   │   └── models.py             # SQLAlchemy models (ready)
│   ├── services/
│   │   ├── storage_service.py    # R2/S3 storage
│   │   ├── email_service.py      # Resend emails
│   │   └── commission_service.py # Commission logic
│   ├── lib/
│   │   └── database.py           # PostgreSQL connection
│   ├── tests/                    # pytest tests
│   ├── uploads/                  # Local file storage
│   ├── Dockerfile
│   ├── .env
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   └── components/
│   ├── vercel.json
│   ├── .env
│   └── .env.example
└── docker-compose.yml
```

## Environment Variables

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://...  # When ready for PostgreSQL
MONGO_URL=mongodb://...        # Current MongoDB

# Storage
STORAGE_MODE=mock              # mock | r2
CLOUDFLARE_R2_*               # R2 credentials

# Email
RESEND_API_KEY=               # Resend API key
RESEND_FROM_EMAIL=            # From address

# Payments
RAZORPAY_KEY_ID=              # Razorpay key
RAZORPAY_KEY_SECRET=          # Razorpay secret

# Commission (percentages)
COMMISSION_L1=40
COMMISSION_L2=12
COMMISSION_L3=6
COMMISSION_L4=3
COMMISSION_L5=1
```

### Frontend (.env)
```bash
REACT_APP_BACKEND_URL=https://api.meramentor.in
REACT_APP_RAZORPAY_KEY_ID=
REACT_APP_GOOGLE_CLIENT_ID=
```

## Testing Results
- **Backend Tests**: 92/92 passed (100%)
- **Test Coverage**: Auth, Courses, Referrals, Commissions, Wallet, Admin

## Deployment

### Backend (Hostinger/VPS)
```bash
docker-compose up -d
```

### Frontend (Vercel)
```bash
vercel --prod
```

## MOCKED Systems (Needs Keys)
- **Razorpay**: Payment gateway
- **Resend**: Email notifications
- **Cloudflare R2**: Cloud storage
- **PostgreSQL**: Database (using MongoDB currently)

## Next Steps to Launch

1. **Get API Keys**:
   - Razorpay: https://dashboard.razorpay.com
   - Resend: https://resend.com
   - Cloudflare R2: https://dash.cloudflare.com
   - Supabase: https://supabase.com (for PostgreSQL)

2. **Configure .env** with real values

3. **Deploy**:
   - Backend to Hostinger/VPS
   - Frontend to Vercel

4. **Test in Production**:
   - OAuth flow
   - Payment flow
   - Email delivery
   - File uploads

5. **Launch meramentor.in** 🚀
