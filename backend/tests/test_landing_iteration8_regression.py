"""Landing page/public-admin/payment/auth regression checks for Data Analytics flow."""
import os
import uuid
from pathlib import Path

import pytest
import requests


def _load_key_from_env_file(path: str, key: str) -> str | None:
    p = Path(path)
    if not p.exists():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line or line.strip().startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == key:
            return v.strip()
    return None


def _base_url() -> str:
    value = os.environ.get("REACT_APP_BACKEND_URL")
    if not value:
        value = _load_key_from_env_file("/app/frontend/.env", "REACT_APP_BACKEND_URL")
    assert value, "REACT_APP_BACKEND_URL missing"
    return value.rstrip("/")


BASE_URL = _base_url()
ADMIN_SESSION = os.environ.get("ADMIN_SESSION") or _load_key_from_env_file("/app/.local/test.env", "ADMIN_SESSION")
USER_SESSION = os.environ.get("USER_SESSION") or _load_key_from_env_file("/app/.local/test.env", "USER_SESSION")


@pytest.fixture
def api_client():
    """Shared API client for unauthenticated requests."""
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture
def admin_client():
    """Admin-authenticated client for landing and admin APIs."""
    if not ADMIN_SESSION:
        pytest.skip("ADMIN_SESSION missing in /app/.local/test.env")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {ADMIN_SESSION}"})
    return s


@pytest.fixture
def user_client():
    """Non-admin authenticated client for authorization checks."""
    if not USER_SESSION:
        pytest.skip("USER_SESSION missing in /app/.local/test.env")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {USER_SESSION}"})
    return s


# Public landing content + webinar linkage + sample reviews
def test_public_landing_payload_and_seed_reviews(api_client):
    response = api_client.get(f"{BASE_URL}/api/landing/data-analytics", timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert data["webinar_url"] == "https://superprofile.bio/e/CFnAGrLC"
    assert data["settings"]["course_id"] == "course_data_analytics"
    assert isinstance(data["reviews"], list)
    assert len(data["reviews"]) == 20
    assert all(r["is_sample"] for r in data["reviews"])


# Public/admin course listing behavior for draft landing course
def test_public_courses_exclude_draft_landing_course(api_client):
    response = api_client.get(f"{BASE_URL}/api/courses", timeout=30)
    assert response.status_code == 200
    courses = response.json()
    assert all(c["course_id"] != "course_data_analytics" for c in courses)


def test_admin_courses_include_draft_landing_course(admin_client):
    response = admin_client.get(f"{BASE_URL}/api/admin/courses", timeout=30)
    assert response.status_code == 200
    courses = response.json()
    landing = [c for c in courses if c["course_id"] == "course_data_analytics"]
    assert len(landing) == 1
    assert landing[0]["published"] is False


# Landing analytics constraints: allowlist + dedupe
def test_landing_events_reject_spoofed_server_events(api_client):
    payload = {
        "event_id": str(uuid.uuid4()),
        "visitor_id": str(uuid.uuid4()),
        "event": "signup_completed",
        "browser_type": "browser",
        "section": "test",
    }
    r1 = api_client.post(f"{BASE_URL}/api/landing/events", json=payload, timeout=30)
    assert r1.status_code == 422

    payload["event"] = "purchase_completed"
    payload["event_id"] = str(uuid.uuid4())
    r2 = api_client.post(f"{BASE_URL}/api/landing/events", json=payload, timeout=30)
    assert r2.status_code == 422


def test_landing_events_deduplicate_event_id(admin_client, api_client):
    before = admin_client.get(f"{BASE_URL}/api/admin/landing/analytics", timeout=30)
    assert before.status_code == 200
    before_count = before.json()["by_browser"]["facebook"].get("browser_open", {}).get("events", 0)

    event_id = str(uuid.uuid4())
    payload = {
        "event_id": event_id,
        "visitor_id": str(uuid.uuid4()),
        "event": "browser_open",
        "browser_type": "facebook",
        "section": "dedupe-test",
    }
    first = api_client.post(f"{BASE_URL}/api/landing/events", json=payload, timeout=30)
    second = api_client.post(f"{BASE_URL}/api/landing/events", json=payload, timeout=30)
    assert first.status_code == 202
    assert second.status_code == 202

    after = admin_client.get(f"{BASE_URL}/api/admin/landing/analytics", timeout=30)
    assert after.status_code == 200
    after_count = after.json()["by_browser"]["facebook"].get("browser_open", {}).get("events", 0)
    assert after_count - before_count == 1


# Google OAuth initiation + callback state validation
def test_google_login_redirect_has_state_nonce_and_cookie(api_client):
    params = {
        "visitor_id": str(uuid.uuid4()),
        "browser_type": "browser",
        "intent": "signup",
        "ref": "MMTESTADMIN",
    }
    response = api_client.get(f"{BASE_URL}/api/auth/google/login", params=params, allow_redirects=False, timeout=30)
    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert location.startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert "state=" in location
    assert "nonce=" in location
    assert "google_oauth_state=" in (response.headers.get("set-cookie", "") or "")


def test_google_callback_missing_state_is_rejected(api_client):
    response = api_client.get(
        f"{BASE_URL}/api/auth/google/callback",
        params={"code": "dummy"},
        allow_redirects=False,
        timeout=30,
    )
    assert response.status_code == 400
    assert "state" in response.text.lower()


def test_google_callback_state_mismatch_is_rejected(api_client):
    api_client.cookies.set("google_oauth_state", "expected-state", domain="pdf-upload-fix-9.preview.emergentagent.com", path="/api/auth/google")
    response = api_client.get(
        f"{BASE_URL}/api/auth/google/callback",
        params={"code": "dummy", "state": "wrong-state"},
        allow_redirects=False,
        timeout=30,
    )
    assert response.status_code == 400
    assert "invalid oauth state" in response.text.lower()


# Admin authz and settings/review CRUD
def test_landing_admin_requires_auth(api_client, user_client):
    unauth = api_client.get(f"{BASE_URL}/api/admin/landing/settings", timeout=30)
    assert unauth.status_code == 401
    non_admin = user_client.get(f"{BASE_URL}/api/admin/landing/settings", timeout=30)
    assert non_admin.status_code == 403


def test_landing_settings_validate_and_persist(admin_client):
    get_response = admin_client.get(f"{BASE_URL}/api/admin/landing/settings", timeout=30)
    assert get_response.status_code == 200
    settings = get_response.json()

    invalid = dict(settings)
    invalid["seats_total"] = 5
    invalid["seats_filled"] = 6
    bad = admin_client.put(f"{BASE_URL}/api/admin/landing/settings", json=invalid, timeout=30)
    assert bad.status_code == 422

    original = dict(settings)
    updated = dict(settings)
    updated["seats_filled"] = min((settings.get("seats_filled", 0) + 1), settings.get("seats_total", 50))
    saved = admin_client.put(f"{BASE_URL}/api/admin/landing/settings", json=updated, timeout=30)
    assert saved.status_code == 200
    assert saved.json()["seats_filled"] == updated["seats_filled"]

    reload_response = admin_client.get(f"{BASE_URL}/api/admin/landing/settings", timeout=30)
    assert reload_response.status_code == 200
    assert reload_response.json()["seats_filled"] == updated["seats_filled"]

    restore = admin_client.put(f"{BASE_URL}/api/admin/landing/settings", json=original, timeout=30)
    assert restore.status_code == 200


def test_landing_reviews_crud_with_rating_bounds_and_public_propagation(admin_client, api_client):
    invalid = {
        "name": "TEST bad rating",
        "rating": 6,
        "review_text": "invalid",
        "role": "",
        "display_order": 9999,
        "is_sample": True,
    }
    invalid_resp = admin_client.post(f"{BASE_URL}/api/admin/landing/reviews", json=invalid, timeout=30)
    assert invalid_resp.status_code == 422

    name = f"TEST Landing {uuid.uuid4().hex[:6]}"
    create_payload = {
        "name": name,
        "rating": 5,
        "review_text": "TEST review text for CRUD",
        "role": "QA",
        "display_order": 9998,
        "is_sample": True,
    }
    created = admin_client.post(f"{BASE_URL}/api/admin/landing/reviews", json=create_payload, timeout=30)
    assert created.status_code == 201
    created_data = created.json()
    assert created_data["name"] == name
    review_id = created_data["id"]

    updated = dict(create_payload)
    updated["rating"] = 4
    updated["review_text"] = "TEST updated review text"
    updated["is_sample"] = False
    edit = admin_client.put(f"{BASE_URL}/api/admin/landing/reviews/{review_id}", json=updated, timeout=30)
    assert edit.status_code == 200
    assert edit.json()["rating"] == 4
    assert edit.json()["is_sample"] is False

    admin_list = admin_client.get(f"{BASE_URL}/api/admin/landing/reviews", timeout=30)
    assert admin_list.status_code == 200
    assert any(r["id"] == review_id and r["review_text"] == "TEST updated review text" for r in admin_list.json())

    public = api_client.get(f"{BASE_URL}/api/landing/data-analytics", timeout=30)
    assert public.status_code == 200
    assert any(r["id"] == review_id and r["is_sample"] is False for r in public.json()["reviews"])

    deleted = admin_client.delete(f"{BASE_URL}/api/admin/landing/reviews/{review_id}", timeout=30)
    assert deleted.status_code == 200
    verify_deleted = admin_client.get(f"{BASE_URL}/api/admin/landing/reviews", timeout=30)
    assert verify_deleted.status_code == 200
    assert all(r["id"] != review_id for r in verify_deleted.json())


# Payment safety checks for draft landing course + webhook fail-fast
def test_payments_reject_draft_landing_course(user_client):
    payload = {
        "course_id": "course_data_analytics",
        "referral_code": "MMTESTADMIN",
        "visitor_id": str(uuid.uuid4()),
        "browser_type": "browser",
    }
    response = user_client.post(f"{BASE_URL}/api/payments/create-order", json=payload, timeout=30)
    assert response.status_code == 404
    assert "not open for enrollment" in response.text.lower()


def test_verify_payment_rejects_missing_signature_fields(user_client):
    response = user_client.post(
        f"{BASE_URL}/api/payments/verify",
        json={"razorpay_order_id": "", "razorpay_payment_id": "", "razorpay_signature": ""},
        timeout=30,
    )
    assert response.status_code == 400
    assert "verification" in response.text.lower()


def test_webhook_requires_secret_and_rejects_unconfigured(api_client):
    response = api_client.post(f"{BASE_URL}/api/payments/webhook", json={}, timeout=30)
    assert response.status_code == 503
    assert "not configured" in response.text.lower()


def test_temp_published_course_order_retry_and_cross_user_protection(admin_client, user_client):
    """Temporary payment fixture: create ₹1299 published course, test retry + ownership, then cleanup."""
    temp_course_id = None
    create_payload = {
        "title": f"TEST Temp Payment {uuid.uuid4().hex[:6]}",
        "description": "Temporary API fixture",
        "price": 1299,
        "category": "Testing",
        "published": True,
        "lessons": [{"title": "Fixture Lesson", "video_type": "youtube", "video_url": "https://youtu.be/test"}],
    }

    create = admin_client.post(f"{BASE_URL}/api/admin/courses", json=create_payload, timeout=30)
    assert create.status_code == 200
    temp_course_id = create.json()["course_id"]

    try:
        body = {
            "course_id": temp_course_id,
            "referral_code": "MMTESTADMIN",
            "visitor_id": str(uuid.uuid4()),
            "browser_type": "browser",
        }
        first = user_client.post(f"{BASE_URL}/api/payments/create-order", json=body, timeout=45)
        if first.status_code == 502:
            pytest.skip("Razorpay test key/provider blocked order creation in preview")
        assert first.status_code == 200
        first_data = first.json()
        assert isinstance(first_data["order_id"], str)
        assert first_data["amount"] == 1299

        # Retry should not create duplicate/uniqueness error; same pending order can be reused
        second = user_client.post(f"{BASE_URL}/api/payments/create-order", json=body, timeout=45)
        assert second.status_code == 200
        second_data = second.json()
        assert second_data["order_id"] == first_data["order_id"]

        # Other user (admin token) must not be able to verify this user's order
        cross = admin_client.post(
            f"{BASE_URL}/api/payments/verify",
            json={
                "razorpay_order_id": first_data["order_id"],
                "razorpay_payment_id": "pay_fake_cross_user",
                "razorpay_signature": "sig_fake_cross_user",
            },
            timeout=30,
        )
        assert cross.status_code == 404
        assert "order not found" in cross.text.lower()
    finally:
        if temp_course_id:
            admin_client.delete(f"{BASE_URL}/api/admin/courses/{temp_course_id}", timeout=30)
