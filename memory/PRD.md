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
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Auth**: Emergent Google OAuth + session cookies

## What's Been Implemented (Feb 18, 2026)
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

## Testing Results
- Backend: 100% (14/14 endpoints)
- Frontend: 95% (minor overlay on nav, functional)

## P0 - Critical (Next)
- Razorpay real key integration (user needs to get keys from Razorpay)
- Admin email configuration in .env (ADMIN_EMAILS)
- File upload for course resources (PDFs)

## P1 - Important
- Course progress tracking (mark lessons complete)
- Email notifications for referral sign-ups
- Dashboard analytics charts (earnings over time)
- Mobile app-like PWA support

## P2 - Nice to Have
- Leaderboard for top referrers
- Coupon/discount code system
- Certificate generation on course completion
- Dark mode toggle
