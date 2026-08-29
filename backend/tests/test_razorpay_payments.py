"""
Test suite for Razorpay payment integration in Mera Mentor.
Tests: create-order (real Razorpay), verify payment, webhook, and health check.
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    raise RuntimeError("REACT_APP_BACKEND_URL is not set")

# ===== Fixtures =====

@pytest.fixture(scope="module")
def session():
    """Shared requests session"""
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def auth_token(session):
    """Create a test user session and return the session token"""
    resp = session.post(f"{BASE_URL}/api/auth/session", json={
        "user": {
            "email": f"test_razorpay_{int(time.time())}@meramentor.in",
            "name": "Razorpay Test User",
            "picture": "https://via.placeholder.com/150"
        }
    })
    assert resp.status_code == 200, f"Auth session creation failed: {resp.text}"
    data = resp.json()
    token = data.get("session_token")
    assert token, "No session_token in response"
    print(f"\nCreated test session: {token[:12]}...")
    return token


@pytest.fixture(scope="module")
def authed_session(session, auth_token):
    """Session with auth header"""
    session.headers.update({"Authorization": f"Bearer {auth_token}"})
    return session


@pytest.fixture(scope="module")
def first_course_id(authed_session):
    """Get the first available (non-upsell) course ID"""
    resp = authed_session.get(f"{BASE_URL}/api/courses")
    assert resp.status_code == 200, f"Courses endpoint failed: {resp.text}"
    courses = resp.json()
    non_upsell = [c for c in courses if not c.get("is_upsell")]
    assert len(non_upsell) > 0, "No non-upsell courses available"
    cid = non_upsell[0]["course_id"]
    print(f"\nUsing course_id: {cid}")
    return cid


# ===== Health Check Tests =====

class TestHealthCheck:
    """Verify /api/health endpoint returns expected storage_mode and database status"""

    def test_health_returns_200(self, session):
        resp = session.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200, f"Health check failed: {resp.text}"
        print("\nHEALTH: 200 OK")

    def test_health_database_connected(self, session):
        resp = session.get(f"{BASE_URL}/api/health")
        data = resp.json()
        assert data.get("database") == "connected", \
            f"Expected database='connected', got: {data.get('database')}"
        print(f"\nHEALTH database: {data.get('database')}")

    def test_health_storage_mode_r2(self, session):
        resp = session.get(f"{BASE_URL}/api/health")
        data = resp.json()
        assert data.get("storage_mode") == "r2", \
            f"Expected storage_mode='r2', got: {data.get('storage_mode')}"
        print(f"\nHEALTH storage_mode: {data.get('storage_mode')}")

    def test_health_status_ok(self, session):
        resp = session.get(f"{BASE_URL}/api/health")
        data = resp.json()
        assert data.get("status") == "ok", \
            f"Expected status='ok', got: {data.get('status')}"


# ===== Payment Create-Order Tests =====

class TestCreatePaymentOrder:
    """Verify /api/payments/create-order returns real Razorpay order"""

    def test_create_order_returns_200(self, authed_session, first_course_id):
        resp = authed_session.post(f"{BASE_URL}/api/payments/create-order", json={
            "course_id": first_course_id
        })
        assert resp.status_code == 200, f"create-order failed: {resp.text}"
        print(f"\nCREATE-ORDER: {resp.status_code}")

    def test_create_order_has_real_razorpay_order_id(self, authed_session, first_course_id):
        """Order ID must start with 'order_' — this confirms real Razorpay SDK is used"""
        resp = authed_session.post(f"{BASE_URL}/api/payments/create-order", json={
            "course_id": first_course_id
        })
        data = resp.json()
        order_id = data.get("order_id", "")
        assert order_id.startswith("order_"), \
            f"Expected order_id starting with 'order_', got: {order_id!r}. " \
            f"This likely means Razorpay SDK is not initialized (fallback UUID used)."
        print(f"\norder_id: {order_id}")

    def test_create_order_amount_paise(self, authed_session, first_course_id):
        resp = authed_session.post(f"{BASE_URL}/api/payments/create-order", json={
            "course_id": first_course_id
        })
        data = resp.json()
        amount_paise = data.get("amount_paise")
        assert isinstance(amount_paise, int), f"amount_paise should be int, got: {type(amount_paise)}"
        assert amount_paise > 0, f"amount_paise should be > 0, got: {amount_paise}"
        print(f"\namount_paise: {amount_paise}")

    def test_create_order_key_id_correct(self, authed_session, first_course_id):
        resp = authed_session.post(f"{BASE_URL}/api/payments/create-order", json={
            "course_id": first_course_id
        })
        data = resp.json()
        key_id = data.get("key_id")
        assert key_id == "rzp_test_SKU3kjkJnpAHOF", \
            f"Expected key_id='rzp_test_SKU3kjkJnpAHOF', got: {key_id!r}"
        print(f"\nkey_id: {key_id}")

    def test_create_order_currency_inr(self, authed_session, first_course_id):
        resp = authed_session.post(f"{BASE_URL}/api/payments/create-order", json={
            "course_id": first_course_id
        })
        data = resp.json()
        currency = data.get("currency")
        assert currency == "INR", f"Expected currency='INR', got: {currency!r}"
        print(f"\ncurrency: {currency}")

    def test_create_order_course_info_present(self, authed_session, first_course_id):
        resp = authed_session.post(f"{BASE_URL}/api/payments/create-order", json={
            "course_id": first_course_id
        })
        data = resp.json()
        course_info = data.get("course")
        assert course_info is not None, "Expected 'course' key in response"
        assert "title" in course_info, "Expected 'title' in course info"
        print(f"\ncourse title: {course_info.get('title')}")

    def test_create_order_requires_auth(self, session):
        """Without auth should return 401"""
        # Use a clean session without auth header
        clean = requests.Session()
        resp = clean.post(f"{BASE_URL}/api/payments/create-order", json={"course_id": "any"})
        assert resp.status_code == 401, f"Expected 401, got: {resp.status_code}"
        print(f"\nUnauthenticated create-order: {resp.status_code}")

    def test_create_order_nonexistent_course_404(self, authed_session):
        resp = authed_session.post(f"{BASE_URL}/api/payments/create-order", json={
            "course_id": "nonexistent-course-id-99999"
        })
        assert resp.status_code == 404, f"Expected 404 for unknown course, got: {resp.status_code}"
        print(f"\nNonexistent course: {resp.status_code}")

    def test_create_order_with_coupon(self, authed_session):
        """Test create-order with a valid coupon code (LAUNCH20)"""
        # First get a non-upsell course
        courses_resp = authed_session.get(f"{BASE_URL}/api/courses")
        if courses_resp.status_code != 200:
            pytest.skip("Cannot fetch courses for coupon test")
        courses = [c for c in courses_resp.json() if not c.get("is_upsell")]
        if not courses:
            pytest.skip("No courses available for coupon test")
        # Use a different course to avoid "already purchased" conflict
        course_id = courses[-1]["course_id"] if len(courses) > 1 else courses[0]["course_id"]
        resp = authed_session.post(f"{BASE_URL}/api/payments/create-order", json={
            "course_id": course_id,
            "coupon_code": "LAUNCH20"
        })
        # Either 200 (coupon applied) or 400 (already purchased) is acceptable
        assert resp.status_code in [200, 400], f"Unexpected status: {resp.status_code} — {resp.text}"
        if resp.status_code == 200:
            data = resp.json()
            print(f"\nCoupon applied: amount={data.get('amount')}, paise={data.get('amount_paise')}")


# ===== Payment Verify Tests =====

class TestVerifyPayment:
    """Verify /api/payments/verify completes a purchase (demo mode — no signature)"""

    @pytest.fixture(scope="class")
    def order_data(self, authed_session):
        """Create a fresh order for verification tests"""
        # Get available courses
        courses_resp = authed_session.get(f"{BASE_URL}/api/courses")
        assert courses_resp.status_code == 200
        courses = [c for c in courses_resp.json() if not c.get("is_upsell")]
        assert courses, "No courses available"
        # Try each course until we find one not already purchased
        order = None
        for course in courses:
            resp = authed_session.post(f"{BASE_URL}/api/payments/create-order", json={
                "course_id": course["course_id"]
            })
            if resp.status_code == 200:
                order = resp.json()
                break
            elif resp.status_code == 400 and "Already purchased" in resp.text:
                continue
        if order is None:
            pytest.skip("All courses already purchased for this test user")
        print(f"\nCreated order: {order.get('order_id')}")
        return order

    def test_verify_returns_200(self, authed_session, order_data):
        order_id = order_data.get("order_id")
        resp = authed_session.post(f"{BASE_URL}/api/payments/verify", json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": f"pay_test_{int(time.time())}",
            "razorpay_signature": ""
        })
        assert resp.status_code == 200, f"verify failed: {resp.text}"
        print(f"\nVERIFY: {resp.status_code}")

    def test_verify_response_has_purchase_id(self, authed_session, order_data):
        order_id = order_data.get("order_id")
        resp = authed_session.post(f"{BASE_URL}/api/payments/verify", json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": f"pay_test_{int(time.time())}",
            "razorpay_signature": ""
        })
        # Could be 200 (success) or "Already completed" response
        assert resp.status_code == 200
        data = resp.json()
        assert "purchase_id" in data or "message" in data, \
            f"Expected purchase_id or message in response: {data}"
        print(f"\nVERIFY response: {data}")

    def test_verify_unknown_order_returns_404(self, authed_session):
        resp = authed_session.post(f"{BASE_URL}/api/payments/verify", json={
            "razorpay_order_id": "order_nonexistent99999",
            "razorpay_payment_id": "pay_test_123",
            "razorpay_signature": ""
        })
        assert resp.status_code == 404, f"Expected 404 for unknown order, got: {resp.status_code}"
        print(f"\nUnknown order verify: {resp.status_code}")

    def test_verify_requires_auth(self):
        clean = requests.Session()
        resp = clean.post(f"{BASE_URL}/api/payments/verify", json={
            "razorpay_order_id": "order_any",
            "razorpay_payment_id": "pay_test",
            "razorpay_signature": ""
        })
        assert resp.status_code == 401, f"Expected 401, got: {resp.status_code}"
        print(f"\nUnauthenticated verify: {resp.status_code}")


# ===== Webhook Tests =====

class TestWebhook:
    """Verify /api/payments/webhook accepts POST requests and returns 200"""

    def test_webhook_post_returns_200(self, session):
        """Webhook should accept POST and return 200 (no signature — no webhook secret set)"""
        payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_webhook_123",
                        "order_id": "order_test_webhook_456",
                        "amount": 100000,
                        "currency": "INR"
                    }
                }
            }
        }
        resp = session.post(f"{BASE_URL}/api/payments/webhook", json=payload)
        assert resp.status_code == 200, f"Webhook failed: {resp.status_code} — {resp.text}"
        print(f"\nWEBHOOK: {resp.status_code}")

    def test_webhook_returns_status_ok(self, session):
        payload = {"event": "test.event", "payload": {}}
        resp = session.post(f"{BASE_URL}/api/payments/webhook", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok", f"Expected status='ok', got: {data}"
        print(f"\nWEBHOOK response: {data}")

    def test_webhook_payment_failed_event(self, session):
        """payment.failed event should be handled gracefully"""
        payload = {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_fail_test_123",
                        "order_id": "order_fail_test_456"
                    }
                }
            }
        }
        resp = session.post(f"{BASE_URL}/api/payments/webhook", json=payload)
        assert resp.status_code == 200, f"Webhook failed event rejected: {resp.text}"
        print(f"\nWEBHOOK payment.failed: {resp.status_code}")

    def test_webhook_invalid_json_returns_400(self, session):
        """Invalid JSON payload should return 400"""
        resp = requests.post(
            f"{BASE_URL}/api/payments/webhook",
            data="NOT_JSON",
            headers={"Content-Type": "application/json"}
        )
        assert resp.status_code in [400, 422], \
            f"Expected 400/422 for invalid JSON, got: {resp.status_code}"
        print(f"\nWEBHOOK invalid JSON: {resp.status_code}")
