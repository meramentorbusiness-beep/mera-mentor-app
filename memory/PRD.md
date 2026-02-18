# Mera Mentor - Multi-Level Referral & Commission Dashboard

## Original Problem Statement
Build a Multi-Level Referral & Commission Dashboard for an online course platform called "Mera Mentor" with tagline "Seekho. Sikhao. Kamao." (Learn. Teach. Earn.)

## User Personas
- **Learners/Users**: Sign up, browse/purchase courses, share referral links, earn commissions
- **Admin**: Manage courses (upload video lessons via YouTube, PDF resources), view platform stats

## Core Requirements
- 5-level referral commission chain: L1=40%, L2=12%, L3=6%, L4=3%, L5=1% (Total 62%, Platform keeps 38%)
- Currency: INR (₹)
- Auth: Google OAuth (Emergent Auth)
- Payment: Razorpay (MOCK mode until keys provided)
- Video protection: youtube-nocookie.com, access only for purchasers

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn UI + Recharts + react-d3-tree
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Auth**: Emergent Google OAuth + session cookies
- **Real-time**: Server-Sent Events (SSE) for notifications
- **Storage**: Mock local storage (ready for R2/S3 integration)

## What's Been Implemented

### Phase 1 - MVP (Feb 18, 2026) ✅
1. Google OAuth login with referral code capture from URL
2. Dashboard with earnings stats, referral link (copy/share), QR code, commission pyramid
3. Referred Users list with Pending/Active/Churned tabs
4. Commission Wallet with payout requests, transaction history
5. Course Marketplace with purchase flow (mock Razorpay)
6. Course Detail page with protected video player
7. Upsell flow after course purchase
8. Admin Panel - course CRUD, lesson management
9. Multi-level commission processing
10. Seed data: 7 courses with lessons

### Phase 2 - Batches 1 & 2 (Feb 18, 2026) ✅
1. Course Progress Tracking - Mark lessons complete
2. Certificate Generation - Auto-generated upon completion
3. Quiz System - Admin creates quizzes, users submit answers
4. Reviews & Ratings - Course reviews with verified badge
5. Leaderboard - Period filters, badges
6. Commission Analytics Charts - 30-day earnings
7. Coupon System - Admin creates coupons
8. Notifications - Real-time bell with unread count
9. Gamification - Streak tracking, XP system
10. Referral Landing Page - Public page for referral traffic

### Phase 3 - Batch 3 (Feb 18, 2026) ✅
1. Referral Tree Visualization - Interactive D3 tree
2. Real-time SSE Notifications - Instant toast notifications
3. Payout Improvements - TDS (10% > ₹5,000), estimated dates, PDF receipts

### Phase 4 - Media Upload & Commission Update (Feb 18, 2026) ✅
1. **Commission Structure Updated**: 7 levels → 5 levels
   - L1: 40%, L2: 12%, L3: 6%, L4: 3%, L5: 1%
   - Total payout: 62% (was 80%)
   - Platform keeps: 38% (was 20%)
   - **Savings**: +₹180 per ₹1,000 sale

2. **Media Upload System (Mock Storage)**:
   - Admin can upload videos (MP4, MOV, AVI, WebM - max 2GB)
   - Admin can upload PDFs (max 50MB)
   - Admin can upload images (JPEG, PNG, WebP - max 10MB)
   - Drag-and-drop upload with progress bar
   - Media Library with filter by type
   - Secure file serving with auth checks
   - Ready for R2/S3 integration when keys provided

3. **Enhanced Admin Panel**:
   - New tabs: Courses | Media Library | Settings
   - Commission structure visualization
   - Storage configuration display
   - Per-lesson video source toggle (YouTube or Upload)
   - Free preview toggle for lessons and resources

## Testing Results (Feb 18, 2026)
- **Backend**: 92/92 tests passed (100%)
- **Test Files**: 
  - `/app/backend/tests/test_phase2_features.py`
  - `/app/backend/tests/test_phase3_comprehensive.py`
  - `/app/backend/tests/test_commission_chain.py`

## API Endpoints Summary

### Media Upload (NEW)
- `POST /api/admin/media/upload` - Upload video/PDF/image
- `GET /api/admin/media` - List all uploaded media
- `DELETE /api/admin/media/{media_id}` - Delete media
- `PATCH /api/admin/media/{media_id}` - Update media metadata
- `GET /api/media/video/{lesson_id}` - Serve lesson video (auth required)
- `GET /api/media/pdf/{resource_id}` - Serve PDF (auth required)
- `GET /api/media/serve/{file_key}` - Serve file with signed URL
- `GET /api/admin/commission-settings` - Get commission config

### Authentication
- `POST /api/auth/session` - Google OAuth callback
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

### Courses
- `GET /api/courses` - List all courses (public)
- `GET /api/courses/:id` - Course detail
- `GET /api/courses/:id/lessons` - Lessons (requires purchase)

### Referrals & Network
- `GET /api/referrals/stats` - Referral stats
- `GET /api/referrals/tree` - Referral tree visualization
- `GET /api/referrals/tree-stats` - Tree stats by level

### Wallet & Payouts
- `GET /api/wallet` - Wallet balance
- `POST /api/wallet/payout/preview` - Preview with TDS
- `POST /api/wallet/payout` - Request payout
- `GET /api/wallet/payouts/:id/receipt` - Payout receipt

## MOCKED Systems
- **Razorpay**: Payment gateway is mocked
- **Email Notifications**: Stored in DB but not sent
- **Cloud Storage**: Using local mock storage (ready for R2/S3)

## Environment Variables for Cloud Storage (When Ready)
```bash
# Cloudflare R2
STORAGE_MODE=r2
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret
R2_BUCKET_NAME=mera-mentor-media

# OR AWS S3
STORAGE_MODE=s3
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=ap-south-1
AWS_BUCKET_NAME=mera-mentor-media
```

## Prioritized Backlog

### P0 - Critical (Next Steps)
- Razorpay real key integration
- Cloud storage integration (R2/S3 when keys provided)

### P1 - Important
- WhatsApp/SMS referral nudges (Twilio)
- Email notification system (Resend)
- Instructor/Affiliate roles

### P2 - Nice to Have
- Video transcoding integration (Bunny.net/Cloudflare Stream)
- PWA support
- SEO & meta tags
- Rate limiting and fraud detection

## Key Technical Details
- TDS Rate: 10% for payouts > ₹5,000
- Min Withdrawal: ₹100
- Commission Total: 62% (38% platform fee)
- Max upload sizes: Video 2GB, PDF 50MB, Image 10MB
- SSE heartbeat: every 30 seconds
