"""
Phase 2 Backend API Tests - Mera Mentor
Tests for: Progress tracking, Certificates, Quizzes, Reviews, Leaderboard, 
           Analytics, Coupons, Notifications, Streaks
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test tokens - created in MongoDB
USER_SESSION = "test_session_1771438055560"
ADMIN_SESSION = "admin_session_1771438072367"


@pytest.fixture
def user_client():
    """Authenticated user session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {USER_SESSION}"
    })
    return session


@pytest.fixture
def admin_client():
    """Authenticated admin session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ADMIN_SESSION}"
    })
    return session


class TestHealthAndAuth:
    """Basic connectivity tests"""
    
    def test_courses_endpoint_public(self):
        """Test public courses endpoint"""
        response = requests.get(f"{BASE_URL}/api/courses")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # Seeded courses exist
        print(f"✅ Courses endpoint: {len(data)} courses found")

    def test_auth_me_with_valid_session(self, user_client):
        """Test auth/me returns user data"""
        response = user_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        print(f"✅ Auth/me: User {data['name']} authenticated")


class TestProgressTracking:
    """Progress tracking - marking lessons complete"""
    
    def test_mark_lesson_complete(self, user_client):
        """Test /api/progress/complete endpoint"""
        payload = {
            "course_id": "course_web_dev",
            "lesson_id": "les_002"  # Second lesson (first is already done in setup)
        }
        response = user_client.post(f"{BASE_URL}/api/progress/complete", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Handle both fresh completion and already completed scenarios
        if "Already completed" in data.get("message", ""):
            print(f"✅ Progress complete: Lesson already completed (idempotent)")
        else:
            assert "completed" in data
            assert "total" in data
            print(f"✅ Progress complete: {data['completed']}/{data['total']} lessons done")

    def test_mark_same_lesson_twice(self, user_client):
        """Test marking already completed lesson returns 'Already completed'"""
        payload = {
            "course_id": "course_web_dev",
            "lesson_id": "les_001"  # Already completed in setup
        }
        response = user_client.post(f"{BASE_URL}/api/progress/complete", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "Already completed" in data.get("message", "")
        print("✅ Duplicate progress: Returns 'Already completed'")

    def test_continue_learning_endpoint(self, user_client):
        """Test /api/progress/continue endpoint"""
        response = user_client.get(f"{BASE_URL}/api/progress/continue")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # User has a purchase so should have in-progress courses
        if len(data) > 0:
            course = data[0]
            assert "course_id" in course
            assert "progress_pct" in course
            assert "next_lesson" in course
            print(f"✅ Continue learning: {len(data)} courses in progress")
        else:
            print("✅ Continue learning: No in-progress courses (may be all completed)")

    def test_get_course_progress(self, user_client):
        """Test /api/progress/{course_id} endpoint"""
        response = user_client.get(f"{BASE_URL}/api/progress/course_web_dev")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Course progress: {len(data)} lessons completed in course_web_dev")


class TestCertificates:
    """Certificate generation and verification"""
    
    def test_get_user_certificates(self, user_client):
        """Test /api/certificates endpoint"""
        response = user_client.get(f"{BASE_URL}/api/certificates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Certificates: {len(data)} certificates for user")

    def test_verify_nonexistent_certificate(self):
        """Test verifying invalid certificate returns 404"""
        response = requests.get(f"{BASE_URL}/api/verify/CERT-INVALID123")
        assert response.status_code == 404
        print("✅ Certificate verify: Returns 404 for invalid cert")


class TestQuizzes:
    """Quiz system tests"""
    
    def test_admin_create_quiz(self, admin_client):
        """Test admin creating a quiz"""
        payload = {
            "course_id": "course_web_dev",
            "lesson_id": "les_001",
            "title": "TEST_HTML Basics Quiz",
            "pass_percentage": 60,
            "questions": [
                {
                    "question_id": "q1",
                    "question": "What does HTML stand for?",
                    "options": ["Hyper Text Markup Language", "Home Tool Markup Language", "Hyperlinks and Text Markup Language"],
                    "correct_answer": "Hyper Text Markup Language"
                },
                {
                    "question_id": "q2",
                    "question": "Which tag is used for the largest heading?",
                    "options": ["<h1>", "<h6>", "<heading>"],
                    "correct_answer": "<h1>"
                }
            ]
        }
        response = admin_client.post(f"{BASE_URL}/api/admin/quizzes", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "quiz_id" in data
        assert data["title"] == "TEST_HTML Basics Quiz"
        print(f"✅ Create quiz: {data['quiz_id']} created")
        return data["quiz_id"]

    def test_get_course_quizzes(self, user_client):
        """Test getting quizzes for a course"""
        response = user_client.get(f"{BASE_URL}/api/quizzes/course_web_dev")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Course quizzes: {len(data)} quizzes found")

    def test_submit_quiz_pass(self, user_client, admin_client):
        """Test submitting quiz with correct answers"""
        # First create a quiz
        quiz_payload = {
            "course_id": "course_web_dev",
            "lesson_id": "les_002",
            "title": "TEST_CSS Quiz",
            "pass_percentage": 50,
            "questions": [
                {
                    "question_id": "css_q1",
                    "question": "What does CSS stand for?",
                    "options": ["Cascading Style Sheets", "Colorful Style Sheets", "Creative Style Sheets"],
                    "correct_answer": "Cascading Style Sheets"
                }
            ]
        }
        create_resp = admin_client.post(f"{BASE_URL}/api/admin/quizzes", json=quiz_payload)
        assert create_resp.status_code == 200
        quiz_id = create_resp.json()["quiz_id"]
        
        # Submit with correct answer
        submit_payload = {
            "answers": {
                "css_q1": "Cascading Style Sheets"
            }
        }
        response = user_client.post(f"{BASE_URL}/api/quizzes/{quiz_id}/submit", json=submit_payload)
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "passed" in data
        assert data["score"] == 100
        assert data["passed"] == True
        print(f"✅ Quiz submit: Passed with {data['score']}%")

    def test_submit_quiz_fail(self, user_client, admin_client):
        """Test submitting quiz with wrong answers"""
        # Create quiz
        quiz_payload = {
            "course_id": "course_web_dev",
            "title": "TEST_Hard Quiz",
            "pass_percentage": 80,
            "questions": [
                {"question_id": "hq1", "question": "Q1?", "options": ["A", "B"], "correct_answer": "A"},
                {"question_id": "hq2", "question": "Q2?", "options": ["A", "B"], "correct_answer": "A"}
            ]
        }
        create_resp = admin_client.post(f"{BASE_URL}/api/admin/quizzes", json=quiz_payload)
        quiz_id = create_resp.json()["quiz_id"]
        
        # Submit with wrong answers
        submit_payload = {"answers": {"hq1": "B", "hq2": "B"}}
        response = user_client.post(f"{BASE_URL}/api/quizzes/{quiz_id}/submit", json=submit_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["passed"] == False
        print(f"✅ Quiz fail: Score {data['score']}%, passed={data['passed']}")


class TestReviews:
    """Reviews system tests"""
    
    def test_get_course_reviews(self):
        """Test getting reviews for a course (public)"""
        response = requests.get(f"{BASE_URL}/api/reviews/course_web_dev")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Course reviews: {len(data)} reviews found")

    def test_submit_review_requires_purchase(self, user_client):
        """Test that review requires purchase"""
        payload = {
            "course_id": "course_data_science",  # Not purchased
            "rating": 5,
            "comment": "Great course!"
        }
        response = user_client.post(f"{BASE_URL}/api/reviews", json=payload)
        assert response.status_code == 403  # Purchase required
        print("✅ Review: Requires purchase (403 for unpurchased course)")

    def test_submit_review_success(self, user_client):
        """Test submitting a review for purchased course"""
        payload = {
            "course_id": "course_web_dev",  # Purchased in setup
            "rating": 4,
            "comment": "TEST_Good learning experience!"
        }
        response = user_client.post(f"{BASE_URL}/api/reviews", json=payload)
        # Either 200 (success) or 400 (already reviewed)
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert "review_id" in data
            print(f"✅ Review submit: {data['review_id']} created")
        else:
            print("✅ Review submit: Already reviewed (400)")


class TestLeaderboard:
    """Leaderboard tests"""
    
    def test_leaderboard_all_time(self, user_client):
        """Test /api/leaderboard with period=all"""
        response = user_client.get(f"{BASE_URL}/api/leaderboard?period=all")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify structure if data exists
        if len(data) > 0:
            entry = data[0]
            assert "rank" in entry
            assert "user_id" in entry
            assert "total_earned" in entry
            assert "badge" in entry
        print(f"✅ Leaderboard all: {len(data)} entries")

    def test_leaderboard_weekly(self, user_client):
        """Test /api/leaderboard with period=weekly"""
        response = user_client.get(f"{BASE_URL}/api/leaderboard?period=weekly")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Leaderboard weekly: {len(data)} entries")

    def test_leaderboard_monthly(self, user_client):
        """Test /api/leaderboard with period=monthly"""
        response = user_client.get(f"{BASE_URL}/api/leaderboard?period=monthly")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Leaderboard monthly: {len(data)} entries")

    def test_my_rank(self, user_client):
        """Test /api/leaderboard/my-rank endpoint"""
        response = user_client.get(f"{BASE_URL}/api/leaderboard/my-rank")
        assert response.status_code == 200
        data = response.json()
        assert "rank" in data
        assert "total_earned" in data
        assert "total_referrals" in data
        assert "badge" in data
        assert "xp" in data
        assert "streak" in data
        print(f"✅ My rank: #{data['rank']}, XP={data['xp']}, Streak={data['streak']}")


class TestAnalytics:
    """Analytics endpoints tests"""
    
    def test_earnings_chart(self, user_client):
        """Test /api/analytics/earnings - 30-day chart data"""
        response = user_client.get(f"{BASE_URL}/api/analytics/earnings")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 30  # 30 days of data
        if len(data) > 0:
            assert "date" in data[0]
            assert "amount" in data[0]
        print(f"✅ Earnings chart: {len(data)} days of data")

    def test_commission_by_level(self, user_client):
        """Test /api/analytics/commission-by-level"""
        response = user_client.get(f"{BASE_URL}/api/analytics/commission-by-level")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # May be empty if no commissions yet
        if len(data) > 0:
            assert "level" in data[0]
            assert "total" in data[0]
            assert "count" in data[0]
        print(f"✅ Commission by level: {len(data)} levels with data")


class TestCoupons:
    """Coupon system tests"""
    
    def test_admin_create_coupon(self, admin_client):
        """Test admin creating a coupon"""
        payload = {
            "code": "TEST50OFF",
            "discount_type": "percent",
            "discount_value": 50,
            "max_uses": 10,
            "applicable_courses": []
        }
        response = admin_client.post(f"{BASE_URL}/api/admin/coupons", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "coupon_id" in data
        assert data["code"] == "TEST50OFF"
        print(f"✅ Create coupon: {data['code']} created")

    def test_admin_list_coupons(self, admin_client):
        """Test admin listing coupons"""
        response = admin_client.get(f"{BASE_URL}/api/admin/coupons")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ List coupons: {len(data)} coupons found")

    def test_validate_valid_coupon(self, user_client):
        """Test validating a valid coupon"""
        payload = {
            "code": "TEST50OFF",
            "course_id": "course_web_dev"
        }
        response = user_client.post(f"{BASE_URL}/api/coupons/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["discount_value"] == 50
        print(f"✅ Validate coupon: {data['code']} is valid, {data['discount_value']}% off")

    def test_validate_invalid_coupon(self, user_client):
        """Test validating invalid coupon returns 404"""
        payload = {"code": "INVALID_CODE", "course_id": "course_web_dev"}
        response = user_client.post(f"{BASE_URL}/api/coupons/validate", json=payload)
        assert response.status_code == 404
        print("✅ Invalid coupon: Returns 404")


class TestNotifications:
    """Notifications system tests"""
    
    def test_get_notifications(self, user_client):
        """Test /api/notifications endpoint"""
        response = user_client.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Notifications: {len(data)} notifications")

    def test_unread_count(self, user_client):
        """Test /api/notifications/unread-count"""
        response = user_client.get(f"{BASE_URL}/api/notifications/unread-count")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        print(f"✅ Unread count: {data['count']} unread")

    def test_mark_notifications_read(self, user_client):
        """Test /api/notifications/mark-read"""
        response = user_client.post(f"{BASE_URL}/api/notifications/mark-read")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print("✅ Mark read: All notifications marked as read")


class TestStreaksAndXP:
    """Streaks and XP gamification tests"""
    
    def test_get_streak(self, user_client):
        """Test /api/streaks endpoint"""
        response = user_client.get(f"{BASE_URL}/api/streaks")
        assert response.status_code == 200
        data = response.json()
        assert "streak" in data
        assert "xp" in data
        print(f"✅ Streaks: {data['streak']} day streak, {data['xp']} XP")


class TestReferralStats:
    """Referral statistics tests"""
    
    def test_referral_stats(self, user_client):
        """Test /api/referrals/stats"""
        response = user_client.get(f"{BASE_URL}/api/referrals/stats")
        assert response.status_code == 200
        data = response.json()
        assert "earned_today" in data
        assert "earned_week" in data
        assert "earned_lifetime" in data
        assert "total_referred" in data
        print(f"✅ Referral stats: Lifetime {data['earned_lifetime']}, {data['total_referred']} referrals")

    def test_referral_counts(self, user_client):
        """Test /api/referrals/counts"""
        response = user_client.get(f"{BASE_URL}/api/referrals/counts")
        assert response.status_code == 200
        data = response.json()
        assert "pending" in data
        assert "active" in data
        assert "churned" in data
        assert "total" in data
        print(f"✅ Referral counts: {data['total']} total (P:{data['pending']}/A:{data['active']}/C:{data['churned']})")


class TestWallet:
    """Wallet and payout tests"""
    
    def test_get_wallet(self, user_client):
        """Test /api/wallet endpoint"""
        response = user_client.get(f"{BASE_URL}/api/wallet")
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "total_earned" in data
        assert "total_withdrawn" in data
        print(f"✅ Wallet: Balance={data['balance']}, Earned={data['total_earned']}")

    def test_wallet_transactions(self, user_client):
        """Test /api/wallet/transactions"""
        response = user_client.get(f"{BASE_URL}/api/wallet/transactions")
        assert response.status_code == 200
        data = response.json()
        assert "commissions" in data
        assert "payouts" in data
        print(f"✅ Transactions: {len(data['commissions'])} commissions, {len(data['payouts'])} payouts")


class TestAdminEndpoints:
    """Admin-only endpoints tests"""
    
    def test_admin_stats(self, admin_client):
        """Test /api/admin/stats"""
        response = admin_client.get(f"{BASE_URL}/api/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_purchases" in data
        assert "total_revenue" in data
        assert "total_commissions" in data
        print(f"✅ Admin stats: {data['total_users']} users, Revenue={data['total_revenue']}")

    def test_admin_create_course(self, admin_client):
        """Test admin course creation"""
        payload = {
            "title": "TEST_New Course",
            "description": "Test course description",
            "price": 299,
            "original_price": 599,
            "category": "Development",
            "published": False,
            "lessons": [
                {"title": "Intro", "description": "Introduction", "video_url": "", "duration": "10 min"}
            ]
        }
        response = admin_client.post(f"{BASE_URL}/api/admin/courses", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "course_id" in data
        assert data["title"] == "TEST_New Course"
        print(f"✅ Create course: {data['course_id']} created")
        return data["course_id"]

    def test_admin_update_course(self, admin_client):
        """Test admin course update"""
        # First create a course
        create_payload = {
            "title": "TEST_Update Course",
            "description": "Test",
            "price": 199,
            "category": "General"
        }
        create_resp = admin_client.post(f"{BASE_URL}/api/admin/courses", json=create_payload)
        course_id = create_resp.json()["course_id"]
        
        # Update it
        update_payload = {"title": "TEST_Updated Course", "price": 249}
        response = admin_client.put(f"{BASE_URL}/api/admin/courses/{course_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "TEST_Updated Course"
        assert data["price"] == 249
        print(f"✅ Update course: {course_id} updated")

    def test_admin_endpoints_require_admin(self, user_client):
        """Test that admin endpoints return 403 for non-admins"""
        response = user_client.get(f"{BASE_URL}/api/admin/stats")
        assert response.status_code == 403
        print("✅ Admin protection: Non-admin gets 403")


class TestCommissionLevels:
    """Commission levels endpoint"""
    
    def test_get_commission_levels(self):
        """Test /api/commission-levels (public)"""
        response = requests.get(f"{BASE_URL}/api/commission-levels")
        assert response.status_code == 200
        data = response.json()
        assert "levels" in data
        assert len(data["levels"]) == 7  # 7 levels
        assert "min_withdrawal" in data
        # Verify commission rates
        expected_rates = [40, 20, 10, 5, 3, 1.5, 0.5]
        actual_rates = [l["percentage"] for l in data["levels"]]
        assert actual_rates == expected_rates
        print(f"✅ Commission levels: {len(data['levels'])} levels, min withdrawal={data['min_withdrawal']}")


class TestReferralLanding:
    """Public referral landing page"""
    
    def test_referral_landing_valid_code(self):
        """Test referral landing with valid code"""
        # Get a valid referral code first
        response = requests.get(f"{BASE_URL}/api/referral/MMMLSCHBIG")
        assert response.status_code == 200
        data = response.json()
        assert "referrer" in data
        assert "courses" in data
        assert "total_students" in data
        print(f"✅ Referral landing: {data['total_students']} total students on platform")

    def test_referral_landing_invalid_code(self):
        """Test referral landing with invalid code"""
        response = requests.get(f"{BASE_URL}/api/referral/INVALID123")
        assert response.status_code == 404
        print("✅ Invalid referral code: Returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
