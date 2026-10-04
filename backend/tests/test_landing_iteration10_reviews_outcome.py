"""Regression tests for landing review outcome behavior and admin protections."""
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
    """Shared API client for unauthenticated checks."""
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture
def admin_client():
    """Admin-authenticated API client for landing admin CRUD."""
    if not ADMIN_SESSION:
        pytest.skip("ADMIN_SESSION missing in /app/.local/test.env")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {ADMIN_SESSION}"})
    return s


@pytest.fixture
def user_client():
    """Non-admin authenticated API client for authorization checks."""
    if not USER_SESSION:
        pytest.skip("USER_SESSION missing in /app/.local/test.env")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {USER_SESSION}"})
    return s


# Review outcome lifecycle: sample -> genuine with outcome -> sample (cleared)
def test_review_outcome_lifecycle_and_public_visibility(admin_client, api_client):
    review_id = None
    create_payload = {
        "name": f"TEST Outcome {uuid.uuid4().hex[:6]}",
        "rating": 5,
        "review_text": "TEST temporary fixture review",
        "role": "QA",
        "display_order": 9997,
        "is_sample": True,
        "outcome": "Should be cleared for sample",
    }

    try:
        created = admin_client.post(f"{BASE_URL}/api/admin/landing/reviews", json=create_payload, timeout=30)
        assert created.status_code == 201
        created_data = created.json()
        review_id = created_data["id"]
        assert created_data["is_sample"] is True
        assert created_data["outcome"] == ""

        to_genuine = dict(create_payload)
        to_genuine["is_sample"] = False
        to_genuine["outcome"] = "Landed first analyst role"
        updated = admin_client.put(f"{BASE_URL}/api/admin/landing/reviews/{review_id}", json=to_genuine, timeout=30)
        assert updated.status_code == 200
        updated_data = updated.json()
        assert updated_data["is_sample"] is False
        assert updated_data["outcome"] == "Landed first analyst role"

        public_after_genuine = api_client.get(f"{BASE_URL}/api/landing/data-analytics", timeout=30)
        assert public_after_genuine.status_code == 200
        found_genuine = [r for r in public_after_genuine.json()["reviews"] if r["id"] == review_id]
        assert len(found_genuine) == 1
        assert found_genuine[0]["outcome"] == "Landed first analyst role"

        back_to_sample = dict(to_genuine)
        back_to_sample["is_sample"] = True
        back_to_sample["outcome"] = "Should not survive"
        reverted = admin_client.put(f"{BASE_URL}/api/admin/landing/reviews/{review_id}", json=back_to_sample, timeout=30)
        assert reverted.status_code == 200
        reverted_data = reverted.json()
        assert reverted_data["is_sample"] is True
        assert reverted_data["outcome"] == ""

        public_after_revert = api_client.get(f"{BASE_URL}/api/landing/data-analytics", timeout=30)
        assert public_after_revert.status_code == 200
        found_reverted = [r for r in public_after_revert.json()["reviews"] if r["id"] == review_id]
        assert len(found_reverted) == 1
        assert found_reverted[0]["outcome"] == ""
    finally:
        if review_id:
            admin_client.delete(f"{BASE_URL}/api/admin/landing/reviews/{review_id}", timeout=30)


# Review outcome input validation and auth guards
def test_review_outcome_max_length_enforced(admin_client):
    payload = {
        "name": f"TEST Maxlen {uuid.uuid4().hex[:6]}",
        "rating": 5,
        "review_text": "TEST max length fixture",
        "role": "QA",
        "display_order": 9996,
        "is_sample": False,
        "outcome": "X" * 81,
    }
    response = admin_client.post(f"{BASE_URL}/api/admin/landing/reviews", json=payload, timeout=30)
    assert response.status_code == 422


def test_review_admin_routes_require_auth_and_admin_role(api_client, user_client):
    payload = {
        "name": "TEST Auth",
        "rating": 5,
        "review_text": "Auth check",
        "role": "QA",
        "display_order": 1,
        "is_sample": True,
        "outcome": "",
    }
    unauth = api_client.post(f"{BASE_URL}/api/admin/landing/reviews", json=payload, timeout=30)
    assert unauth.status_code == 401
    non_admin = user_client.post(f"{BASE_URL}/api/admin/landing/reviews", json=payload, timeout=30)
    assert non_admin.status_code == 403


# Backward-compatible settings retention for hidden trust fields
def test_settings_roundtrip_preserves_backcompat_metadata(admin_client):
    get_response = admin_client.get(f"{BASE_URL}/api/admin/landing/settings", timeout=30)
    assert get_response.status_code == 200
    original = get_response.json()
    assert "student_count" in original
    assert "average_rating" in original

    save_response = admin_client.put(f"{BASE_URL}/api/admin/landing/settings", json=original, timeout=30)
    assert save_response.status_code == 200
    saved = save_response.json()
    assert saved["student_count"] == original["student_count"]
    assert saved["average_rating"] == original["average_rating"]
