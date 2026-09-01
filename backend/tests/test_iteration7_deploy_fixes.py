"""Iteration 7 backend tests: verify deployment-blocker fixes.

Covers:
- /api/health returns 200 with expected shape
- /api/purchases requires auth (401) and returns list with admin session
- /api/admin/media/upload requires auth (401) and returns 503 with clear message when R2 unconfigured
- /api/courses returns 200 (no regression)
- /api/auth/me returns 401 without auth
- /api/auth/google/login fails-fast when GOOGLE_CLIENT_ID missing
- R2 client wiring correctness (unit-level check on storage_service)
"""
import os
import sys
import subprocess
import pytest
import requests
from pathlib import Path

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    # Read from frontend .env (this is the source of truth per env config)
    env_file = Path("/app/frontend/.env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"
BASE_URL = BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def admin_token():
    """Create a fresh admin session and return the token."""
    result = subprocess.run(
        [sys.executable, "/app/backend/tests/create_admin_session.py"],
        capture_output=True, text=True, cwd="/app/backend", timeout=30,
    )
    assert result.returncode == 0, f"seed failed: {result.stderr}"
    # Last non-empty line is the token
    lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
    token = lines[-1]
    assert len(token) > 30, f"invalid token: {token!r}"
    return token


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ---------------- Health & basic ----------------
class TestHealth:
    def test_health_ok(self):
        r = requests.get(f"{BASE_URL}/api/health", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"
        assert data["storage_mode"] == "r2"


# ---------------- Courses (regression) ----------------
class TestCourses:
    def test_courses_public(self):
        r = requests.get(f"{BASE_URL}/api/courses", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------------- Auth ----------------
class TestAuth:
    def test_me_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert r.status_code == 401

    def test_google_login_failfast(self):
        # No GOOGLE_CLIENT_ID configured locally -> should error clearly
        r = requests.get(
            f"{BASE_URL}/api/auth/google/login",
            timeout=15,
            allow_redirects=False,
        )
        # Fail-fast: not a redirect; should be an error status
        assert r.status_code >= 400, f"expected error, got {r.status_code}"
        body = r.text.lower()
        assert "google_client_id" in body or "google" in body

    def test_me_with_admin_session(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == "admin@meramentor.in"
        assert data["is_admin"] is True


# ---------------- Purchases (previously missing) ----------------
class TestPurchases:
    def test_purchases_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/purchases", timeout=15)
        assert r.status_code == 401

    def test_purchases_admin_returns_list(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/purchases", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)


# ---------------- Media upload guardrails ----------------
class TestMediaUpload:
    def test_upload_requires_auth(self):
        # Without auth -> 401 (before file even parsed)
        r = requests.post(
            f"{BASE_URL}/api/admin/media/upload",
            files={"file": ("t.png", b"x", "image/png")},
            data={"upload_type": "image"},
            timeout=15,
        )
        assert r.status_code == 401

    def test_upload_returns_503_when_r2_missing(self, admin_headers):
        r = requests.post(
            f"{BASE_URL}/api/admin/media/upload",
            headers=admin_headers,
            files={"file": ("t.png", b"x" * 10, "image/png")},
            data={"upload_type": "image"},
            timeout=20,
        )
        assert r.status_code == 503, f"expected 503, got {r.status_code}: {r.text}"
        detail = r.json().get("detail", "")
        assert "Cloudflare R2" in detail
        assert "CLOUDFLARE_R2_ACCOUNT_ID" in detail
        assert "CLOUDFLARE_R2_ACCESS_KEY_ID" in detail
        assert "CLOUDFLARE_R2_SECRET_ACCESS_KEY" in detail
        assert "CLOUDFLARE_R2_BUCKET_NAME" in detail


# ---------------- R2 client wiring (unit-level) ----------------
class TestR2ClientWiring:
    def test_client_endpoint_and_signature(self, monkeypatch):
        sys.path.insert(0, "/app/backend")
        # Set fake env vars
        monkeypatch.setenv("CLOUDFLARE_R2_ACCOUNT_ID", "fakeacct1234")
        monkeypatch.setenv("CLOUDFLARE_R2_ACCESS_KEY_ID", "fake-ak")
        monkeypatch.setenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY", "fake-sk")
        monkeypatch.setenv("CLOUDFLARE_R2_BUCKET_NAME", "fake-bucket")

        import importlib
        from services import storage_service
        importlib.reload(storage_service)
        # bust cache
        storage_service._client.cache_clear()

        assert storage_service.is_storage_enabled() is True
        client = storage_service._client()
        assert client.meta.endpoint_url == "https://fakeacct1234.r2.cloudflarestorage.com"
        assert client.meta.region_name == "auto"
        assert client.meta.config.signature_version == "s3v4"
        assert client.meta.config.s3["addressing_style"] == "path"
