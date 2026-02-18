# Mera Mentor - Multi-Level Referral & Commission Dashboard

## Original Problem Statement
Build a Multi-Level Referral & Commission Dashboard for an online course platform called "Mera Mentor" with tagline "Seekho. Sikhao. Kamao." (Learn. Teach. Earn.)

## User Personas
- **Learners/Users**: Sign up, browse/purchase courses, share referral links, earn commissions
- **Admin**: Manage courses (upload video lessons via YouTube, PDF resources), view platform stats

## Core Requirements
- 7-level referral commission chain: L1=40%, L2=20%, L3=10%, L4=5%, L5=3%, L6=1.5%, L7=0.5%
- Currency: INR (₹)
- Auth: Google OAuth (Emergent Auth)
- Payment: Razorpay (MOCK mode until keys provided)
- Video protection: youtube-nocookie.com, access only for purchasers

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn UI + Recharts + react-d3-tree
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Auth**: Emergent Google OAuth + session cookies
- **Real-time**: Server-Sent Events (SSE) for notifications

## What's Been Implemented

### Phase 1 - MVP (Feb 18, 2026) ✅
1. Google OAuth login with referral code capture from URL
2. Dashboard with earnings stats, referral link (copy/share), QR code, commission pyramid
3. Referred Users list with Pending/Active/Churned tabs, expandable cards
4. Commission Wallet with payout requests, transaction history
5. Course Marketplace with purchase flow (mock Razorpay)
6. Course Detail page with protected video player and lesson sidebar
7. Upsell flow after course purchase
8. Admin Panel - course CRUD, lesson management, resource management, platform stats
9. Multi-level commission processing (7 levels deep)
10. Seed data: 7 courses with lessons and resources

### Phase 2 - Batches 1 & 2 (Feb 18, 2026) ✅
1. **Course Progress Tracking** - Mark lessons complete, video resume
2. **Certificate Generation** - Auto-generated upon course completion
3. **Quiz System** - Admin creates quizzes, users submit answers, scoring with pass/fail
4. **Reviews & Ratings** - Course reviews with verified badge
5. **Leaderboard** - Period filters (weekly/monthly/all), badges (bronze/silver/gold/diamond)
6. **Commission Analytics Charts** - 30-day earnings LineChart, commission-by-level PieChart
7. **Coupon System** - Admin creates coupons, validation with discount calculation
8. **Notifications** - Real-time bell with unread count, popover with notification types
9. **Gamification** - Streak tracking, XP system, badges displayed in UI
10. **Referral Landing Page** - Public page for incoming referral traffic

### Phase 3 - Batch 3 (Feb 18, 2026) ✅
1. **Referral Tree Visualization** - Interactive org-chart using react-d3-tree with zoom/reset controls
2. **Real-time Notifications (SSE)** - Server-Sent Events for instant toast notifications
3. **Payout Improvements**:
   - TDS calculation (10% for payouts > ₹5,000)
   - Estimated processing dates (2-3 business days)
   - PDF receipt generation for payouts

## Testing Results (Feb 18, 2026)
- **Backend**: 92/92 tests passed (100%)
- **Frontend**: All pages verified working
- **Test Files**: 
  - `/app/backend/tests/test_phase2_features.py`
  - `/app/backend/tests/test_phase3_comprehensive.py`
  - `/app/backend/tests/test_commission_chain.py`

## API Endpoints Summary

### Authentication
- `POST /api/auth/session` - Google OAuth callback
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout
- `PUT /api/auth/profile` - Update profile

### Courses
- `GET /api/courses` - List all courses (public)
- `GET /api/courses/:id` - Course detail (public)
- `GET /api/courses/:id/lessons` - Lessons (requires purchase)
- `GET /api/courses/:id/upsell` - Get upsell course

### Progress & Certificates
- `POST /api/progress/complete` - Mark lesson complete
- `GET /api/progress/continue` - Continue learning list
- `GET /api/certificates` - User certificates
- `GET /api/verify/:certificateId` - Verify certificate (public)

### Quizzes & Reviews
- `GET /api/quizzes/:courseId` - Course quizzes
- `POST /api/quizzes/:quizId/submit` - Submit quiz
- `GET /api/reviews/:courseId` - Course reviews
- `POST /api/reviews` - Add review

### Referrals & Network
- `GET /api/referrals/stats` - Referral stats
- `GET /api/referrals/users` - Referred users list
- `GET /api/referrals/counts` - Status counts
- `GET /api/referrals/tree` - Referral tree visualization
- `GET /api/referrals/tree-stats` - Tree stats by level
- `GET /api/referral/:code` - Referral landing page data

### Wallet & Payouts
- `GET /api/wallet` - Wallet balance
- `POST /api/wallet/payout/preview` - Preview with TDS
- `POST /api/wallet/payout` - Request payout
- `GET /api/wallet/transactions` - Transaction history
- `GET /api/wallet/payouts/:id/receipt` - Payout receipt

### Notifications
- `GET /api/notifications` - All notifications
- `GET /api/notifications/unread-count` - Unread count
- `POST /api/notifications/mark-read` - Mark all read
- `GET /api/notifications/stream` - SSE real-time stream

### Leaderboard & Analytics
- `GET /api/leaderboard` - Leaderboard
- `GET /api/leaderboard/my-rank` - User rank
- `GET /api/analytics/earnings` - 30-day earnings
- `GET /api/analytics/commission-by-level` - Commission breakdown

### Admin
- `GET /api/admin/stats` - Platform stats
- `POST/PUT/DELETE /api/admin/courses` - Course CRUD
- `POST /api/admin/quizzes` - Create quiz
- `POST /api/admin/coupons` - Create coupon

### Payments
- `POST /api/payments/create-order` - Create payment order
- `POST /api/payments/verify` - Verify payment

## MOCKED Systems
- **Razorpay**: Payment gateway is mocked - purchases complete immediately
- **Email Notifications**: Notifications stored in DB but not actually sent

## Prioritized Backlog

### P0 - Critical (Next Steps)
- Razorpay real key integration (user needs Razorpay account)
- WhatsApp/SMS referral nudges (Twilio integration)
- Email notification system (Resend integration)

### P1 - Important
- Instructor/Affiliate roles with different permissions
- Advanced admin analytics (cohort analysis, CSV export)
- Public user profiles
- Course bundles and advanced upsells

### P2 - Nice to Have
- PWA support (manifest, service worker)
- SEO & meta tags
- Rate limiting and fraud detection
- OTP for payout requests
- Dark mode toggle

## Database Collections
- `users` - User profiles with referral_chain
- `user_sessions` - Session tokens
- `courses` - Course content
- `purchases` - Purchase records
- `commissions` - Commission records
- `wallets` - User wallets
- `payouts` - Payout requests
- `progress` - Lesson completion
- `certificates` - Generated certificates
- `quizzes` - Quiz questions
- `quiz_attempts` - Quiz submissions
- `reviews` - Course reviews
- `coupons` - Discount codes
- `notifications` - User notifications
- `xp_log` - XP history

## Key Technical Details
- TDS Rate: 10% for payouts > ₹5,000
- Min Withdrawal: ₹100
- Commission Total: 80% (20% platform fee)
- SSE heartbeat: every 30 seconds
- Estimated payout processing: 2-3 business days
