"""
Backend API Tests - PostgreSQL Migration Verification
Tests for Mera Mentor after MongoDB → PostgreSQL (Supabase) migration
Verifies: Health, Auth, Courses, Referrals, Wallet, Payments, Admin
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip('/')
if not BASE_URL:
    BASE_URL = "https://learn-earn-19.preview.emergentagent.com"

# Test session tokens (created dynamically)
TEST_USER_SESSION = None
ADMIN_USER_SESSION = None
TEST_USER_ID = None
ADMIN_USER_ID = None


class TestDatabaseMigrationVerification:
    """Tests to verify MongoDB → PostgreSQL migration"""

    def test_health_check_database_connected(self):
        """Health check should show database: connected (PostgreSQL)"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["database"] == "connected", "Database should be connected"
        assert data["status"] == "ok"
        assert "version" in data
        print(f"✅ Health check passed - Database: {data['database']}, Version: {data['version']}")

    def test_health_check_commission_levels(self):
        """Health check should show 5 commission levels (62% total)"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["commission_levels"] == 5, "Should have 5 commission levels"
        assert round(data["total_commission_rate"]) == 62, "Total commission rate should be 62%"
        print(f"✅ Commission levels: {data['commission_levels']}, Total rate: {data['total_commission_rate']}%")


class TestCommissionLevels:
    """Tests for 5-level commission structure (40%, 12%, 6%, 3%, 1%)"""

    def test_commission_levels_endpoint(self):
        """Commission levels endpoint should return 5 levels with correct percentages"""
        response = requests.get(f"{BASE_URL}/api/commission-levels")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["levels"]) == 5, "Should have 5 levels"
        assert data["levels"][0]["level"] == 1 and data["levels"][0]["percentage"] == 40
        assert data["levels"][1]["level"] == 2 and data["levels"][1]["percentage"] == 12
        assert data["levels"][2]["level"] == 3 and data["levels"][2]["percentage"] == 6
        assert data["levels"][3]["level"] == 4 and data["levels"][3]["percentage"] == 3
        assert data["levels"][4]["level"] == 5 and data["levels"][4]["percentage"] == 1
        
        assert data["min_withdrawal"] == 100
        assert round(data["total_rate"]) == 62
        print(f"✅ Commission levels verified: L1={data['levels'][0]['percentage']}%, L2={data['levels'][1]['percentage']}%, L3={data['levels'][2]['percentage']}%, L4={data['levels'][3]['percentage']}%, L5={data['levels'][4]['percentage']}%")

    def test_commission_example_earnings(self):
        """Example earnings should be calculated correctly for ₹799 course"""
        response = requests.get(f"{BASE_URL}/api/commission-levels")
        assert response.status_code == 200
        data = response.json()
        
        # For ₹799 course
        assert data["levels"][0]["example_earning"] == 319.6  # 40% of 799
        assert data["levels"][1]["example_earning"] == 95.88  # 12% of 799
        assert data["levels"][2]["example_earning"] == 47.94  # 6% of 799
        assert data["levels"][3]["example_earning"] == 23.97  # 3% of 799
        assert data["levels"][4]["example_earning"] == 7.99   # 1% of 799
        print(f"✅ Example earnings verified for ₹799 course")


class TestAuthFlow:
    """Tests for authentication flow"""

    def test_protected_route_without_auth(self):
        """Protected routes should return 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print(f"✅ Protected route returns 401 without auth")

    def test_create_session_creates_user(self):
        """Google OAuth session creation should work and create user"""
        global TEST_USER_SESSION, TEST_USER_ID
        unique_email = f"test_{uuid.uuid4().hex[:8]}@meramentor.in"
        
        response = requests.post(
            f"{BASE_URL}/api/auth/session",
            json={
                "user": {
                    "email": unique_email,
                    "name": "Test User PyTest",
                    "picture": "https://ui-avatars.com/api/?name=Test",
                    "sub": f"google-{uuid.uuid4().hex[:8]}"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "session_token" in data
        assert "user" in data
        assert data["user"]["email"] == unique_email
        assert data["user"]["referral_code"].startswith("MMM")
        
        TEST_USER_SESSION = data["session_token"]
        TEST_USER_ID = data["user"]["user_id"]
        print(f"✅ Session created for {unique_email}")

    def test_create_admin_session(self):
        """Admin user session creation should work"""
        global ADMIN_USER_SESSION, ADMIN_USER_ID
        
        response = requests.post(
            f"{BASE_URL}/api/auth/session",
            json={
                "user": {
                    "email": "admin@meramentor.in",
                    "name": "Admin User",
                    "picture": "https://ui-avatars.com/api/?name=Admin",
                    "sub": f"admin-google-{uuid.uuid4().hex[:8]}"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["user"]["is_admin"] == True
        ADMIN_USER_SESSION = data["session_token"]
        ADMIN_USER_ID = data["user"]["user_id"]
        print(f"✅ Admin session created, is_admin={data['user']['is_admin']}")

    def test_session_cookie_auth(self):
        """Session token should work for authentication"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        assert "referral_code" in data
        print(f"✅ Session authentication works")

    def test_invalid_token_returns_401(self):
        """Invalid token should return 401"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        assert response.status_code == 401
        print(f"✅ Invalid token returns 401")


class TestCourseEndpoints:
    """Tests for course endpoints"""

    def test_course_listing(self):
        """Course listing should return 5 seeded courses"""
        response = requests.get(f"{BASE_URL}/api/courses")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 5, "Should have at least 5 courses"
        
        # Verify course structure
        course = data[0]
        assert "course_id" in course
        assert "title" in course
        assert "price" in course
        assert "lesson_count" in course
        print(f"✅ Course listing returns {len(data)} courses")

    def test_course_detail_with_lessons(self):
        """Course detail should return lessons"""
        # First get a course
        response = requests.get(f"{BASE_URL}/api/courses")
        assert response.status_code == 200
        courses = response.json()
        course_id = courses[0]["course_id"]
        
        # Get course detail
        response = requests.get(f"{BASE_URL}/api/courses/{course_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["course_id"] == course_id
        assert "lessons" in data
        assert len(data["lessons"]) > 0
        
        # Free preview lessons should have video URL
        free_lessons = [l for l in data["lessons"] if l["is_free_preview"]]
        if free_lessons:
            assert free_lessons[0]["video_url"] is not None
        
        # Non-preview lessons should NOT have video URL (for unauthenticated users)
        paid_lessons = [l for l in data["lessons"] if not l["is_free_preview"]]
        if paid_lessons:
            assert paid_lessons[0]["video_url"] is None
        
        print(f"✅ Course detail returns {len(data['lessons'])} lessons")

    def test_course_not_found(self):
        """Invalid course ID should return 404"""
        response = requests.get(f"{BASE_URL}/api/courses/invalid_course_id")
        assert response.status_code == 404
        print(f"✅ Invalid course returns 404")


class TestReferralEndpoints:
    """Tests for referral system endpoints"""

    def test_referral_stats(self):
        """Referral stats endpoint should work"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        response = requests.get(
            f"{BASE_URL}/api/referrals/stats",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "total_referrals" in data
        assert "total_earned" in data
        assert "referral_code" in data
        assert "referral_link" in data
        assert data["referral_code"].startswith("MMM")
        print(f"✅ Referral stats work - Code: {data['referral_code']}")

    def test_referral_tree(self):
        """Referral tree endpoint should work"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        response = requests.get(
            f"{BASE_URL}/api/referrals/tree",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "name" in data
        assert "attributes" in data
        assert data["attributes"]["level"] == 0
        print(f"✅ Referral tree returns tree structure")

    def test_referral_tree_stats(self):
        """Referral tree stats endpoint should work"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        response = requests.get(
            f"{BASE_URL}/api/referrals/tree-stats",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "total_network" in data
        assert "by_level" in data
        print(f"✅ Referral tree stats work")


class TestWalletEndpoints:
    """Tests for wallet and payout endpoints"""

    def test_wallet_balance(self):
        """Wallet endpoint should return balance info"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        response = requests.get(
            f"{BASE_URL}/api/wallet",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "balance" in data
        assert "total_earned" in data
        assert "total_withdrawn" in data
        assert "pending" in data
        assert "withdrawable" in data
        print(f"✅ Wallet balance: ₹{data['balance']}")

    def test_payout_preview_insufficient_balance(self):
        """Payout preview should fail with insufficient balance"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        response = requests.post(
            f"{BASE_URL}/api/wallet/payout/preview",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"},
            json={"amount": 1000}
        )
        # Should return 400 for insufficient balance
        assert response.status_code == 400
        print(f"✅ Payout preview correctly fails with insufficient balance")

    def test_payout_minimum_withdrawal(self):
        """Payout should enforce minimum withdrawal amount"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        response = requests.post(
            f"{BASE_URL}/api/wallet/payout/preview",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"},
            json={"amount": 50}  # Below minimum of 100
        )
        assert response.status_code == 400
        assert "Minimum withdrawal" in response.json().get("detail", "")
        print(f"✅ Minimum withdrawal (₹100) enforced")


class TestPaymentFlow:
    """Tests for payment flow (mocked Razorpay)"""

    def test_create_payment_order(self):
        """Payment order creation should work"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        # Get a course
        response = requests.get(f"{BASE_URL}/api/courses")
        courses = response.json()
        # Find a course that user hasn't purchased
        course_id = courses[-1]["course_id"]  # Use last course
        
        response = requests.post(
            f"{BASE_URL}/api/payments/create-order",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"},
            json={"course_id": course_id}
        )
        
        if response.status_code == 400 and "Already purchased" in response.text:
            pytest.skip("Course already purchased")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "order_id" in data
        assert "amount" in data
        assert "currency" in data
        assert data["currency"] == "INR"
        print(f"✅ Payment order created: {data['order_id']}")

    def test_payment_verification(self):
        """Payment verification should complete purchase"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        # Get a course
        response = requests.get(f"{BASE_URL}/api/courses")
        courses = response.json()
        course_id = courses[-2]["course_id"]  # Use second to last course
        
        # Create order
        response = requests.post(
            f"{BASE_URL}/api/payments/create-order",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"},
            json={"course_id": course_id}
        )
        
        if response.status_code == 400:
            pytest.skip("Course already purchased or order creation failed")
        
        order_id = response.json()["order_id"]
        
        # Verify payment
        response = requests.post(
            f"{BASE_URL}/api/payments/verify",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"},
            json={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": f"test_pay_{uuid.uuid4().hex[:8]}"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Payment successful!"
        assert "purchase_id" in data
        print(f"✅ Payment verified, purchase_id: {data['purchase_id']}")


class TestAdminEndpoints:
    """Tests for admin endpoints"""

    def test_admin_stats_as_admin(self):
        """Admin stats should work for admin users"""
        global ADMIN_USER_SESSION
        if not ADMIN_USER_SESSION:
            pytest.skip("No admin session")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {ADMIN_USER_SESSION}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "total_users" in data
        assert "total_purchases" in data
        assert "total_revenue" in data
        assert "total_commissions" in data
        print(f"✅ Admin stats: {data['total_users']} users, {data['total_purchases']} purchases")

    def test_admin_stats_as_non_admin(self):
        """Admin stats should return 403 for non-admin users"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"}
        )
        assert response.status_code == 403
        print(f"✅ Admin stats correctly returns 403 for non-admin")

    def test_admin_commission_settings(self):
        """Admin should be able to get commission settings"""
        global ADMIN_USER_SESSION
        if not ADMIN_USER_SESSION:
            pytest.skip("No admin session")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/commission-settings",
            headers={"Authorization": f"Bearer {ADMIN_USER_SESSION}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["levels"]) == 5
        assert data["min_withdrawal"] == 100
        print(f"✅ Admin commission settings accessible")


class TestLeaderboard:
    """Tests for leaderboard endpoints"""

    def test_leaderboard_all_time(self):
        """Leaderboard endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/leaderboard")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✅ Leaderboard returns {len(data)} entries")

    def test_leaderboard_weekly(self):
        """Weekly leaderboard should work"""
        response = requests.get(f"{BASE_URL}/api/leaderboard?period=weekly")
        assert response.status_code == 200
        print(f"✅ Weekly leaderboard works")

    def test_my_rank(self):
        """My rank endpoint should work"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        response = requests.get(
            f"{BASE_URL}/api/leaderboard/my-rank",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "rank" in data
        assert "total_earned" in data
        print(f"✅ My rank: #{data['rank']}")


class TestNotifications:
    """Tests for notification endpoints"""

    def test_notifications_list(self):
        """Notifications endpoint should work"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Notifications: {len(data)} items")

    def test_unread_count(self):
        """Unread notification count should work"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        response = requests.get(
            f"{BASE_URL}/api/notifications/unread-count",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        print(f"✅ Unread count: {data['count']}")


class TestAnalytics:
    """Tests for analytics endpoints"""

    def test_earnings_analytics(self):
        """Earnings analytics should work"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        response = requests.get(
            f"{BASE_URL}/api/analytics/earnings",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Earnings analytics: {len(data)} data points")

    def test_commission_by_level(self):
        """Commission by level analytics should work"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        response = requests.get(
            f"{BASE_URL}/api/analytics/commission-by-level",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Commission by level: {len(data)} levels with data")


class TestStreaks:
    """Tests for streaks and XP endpoints"""

    def test_streaks_endpoint(self):
        """Streaks endpoint should work"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        response = requests.get(
            f"{BASE_URL}/api/streaks",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "streak" in data
        assert "xp" in data
        assert "level" in data
        print(f"✅ Streaks: {data['streak']} days, {data['xp']} XP, Level {data['level']}")


class TestReferralLanding:
    """Tests for referral landing page"""

    def test_referral_landing_page(self):
        """Referral landing endpoint should work with valid code"""
        global TEST_USER_SESSION
        if not TEST_USER_SESSION:
            pytest.skip("No test user session")
        
        # Get user's referral code
        response = requests.get(
            f"{BASE_URL}/api/referrals/stats",
            headers={"Authorization": f"Bearer {TEST_USER_SESSION}"}
        )
        ref_code = response.json()["referral_code"]
        
        # Get referral landing page
        response = requests.get(f"{BASE_URL}/api/referral/{ref_code}")
        assert response.status_code == 200
        data = response.json()
        
        assert "referrer" in data
        assert "featured_courses" in data
        print(f"✅ Referral landing page works")

    def test_invalid_referral_code(self):
        """Invalid referral code should return 404"""
        response = requests.get(f"{BASE_URL}/api/referral/INVALID123")
        assert response.status_code == 404
        print(f"✅ Invalid referral code returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
