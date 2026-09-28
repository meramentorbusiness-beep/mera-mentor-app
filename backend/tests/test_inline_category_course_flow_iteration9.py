"""Inline category-in-course flow regression tests (iteration 9)."""
import os
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

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
    """Unauthenticated API client."""
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture
def admin_client():
    """Admin-authenticated API client for course write flow."""
    if not ADMIN_SESSION:
        pytest.skip("ADMIN_SESSION missing in /app/.local/test.env")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {ADMIN_SESSION}"})
    return s


@pytest.fixture
def user_client():
    """Non-admin authenticated API client for authz checks."""
    if not USER_SESSION:
        pytest.skip("USER_SESSION missing in /app/.local/test.env")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {USER_SESSION}"})
    return s


@pytest.fixture
def created_courses(admin_client):
    """Track test-created course_ids and clean them up."""
    ids: list[str] = []
    yield ids
    for cid in ids:
        admin_client.delete(f"{BASE_URL}/api/admin/courses/{cid}", timeout=30)


def _create_course(admin_client: requests.Session, title: str, category: str, lessons=None, resources=None):
    payload = {
        "title": title,
        "description": "TEST inline category flow",
        "price": 499,
        "original_price": 999,
        "image": "https://example.com/test-course.jpg",
        "category": category,
        "published": False,
        "lessons": lessons or [],
        "resources": resources or [],
    }
    return admin_client.post(f"{BASE_URL}/api/admin/courses", json=payload, timeout=45)


# Category suggestion and route simplification checks
def test_get_categories_returns_deduplicated_suggestions(api_client):
    response = api_client.get(f"{BASE_URL}/api/categories", timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    lowered = [item["name"].strip().lower() for item in data if isinstance(item.get("name"), str)]
    assert len(lowered) == len(set(lowered))


def test_removed_admin_category_write_routes_are_not_registered(admin_client):
    payload = {"name": f"TEST_CAT_{uuid.uuid4().hex[:6]}"}
    post_resp = admin_client.post(f"{BASE_URL}/api/admin/categories", json=payload, timeout=30)
    put_resp = admin_client.put(f"{BASE_URL}/api/admin/categories/fake", json=payload, timeout=30)
    delete_resp = admin_client.delete(f"{BASE_URL}/api/admin/categories/fake", timeout=30)
    assert post_resp.status_code == 404
    assert put_resp.status_code == 404
    assert delete_resp.status_code == 404


# Auth constraints for category creation through course save
def test_admin_course_create_requires_auth_for_category_write(api_client):
    payload = {"title": "TEST unauth course", "category": "TEST unauthorized category"}
    response = api_client.post(f"{BASE_URL}/api/admin/courses", json=payload, timeout=30)
    assert response.status_code == 401


def test_admin_course_create_forbidden_for_non_admin(user_client):
    payload = {"title": "TEST non-admin course", "category": "TEST user forbidden category"}
    response = user_client.post(f"{BASE_URL}/api/admin/courses", json=payload, timeout=30)
    assert response.status_code == 403


# Inline create/select category and persistence
def test_create_course_with_new_category_persists_and_appears_in_suggestions(admin_client, api_client, created_courses):
    category = f"TEST_CAT_IT9_{uuid.uuid4().hex[:8]}"
    title = f"TEST_IT9_COURSE_{uuid.uuid4().hex[:8]}"
    response = _create_course(admin_client, title, category)
    assert response.status_code == 200
    created = response.json()
    assert created["category"] == category
    course_id = created["course_id"]
    created_courses.append(course_id)

    detail = api_client.get(f"{BASE_URL}/api/courses/{course_id}", timeout=30)
    assert detail.status_code == 200
    assert detail.json()["category"] == category

    categories = api_client.get(f"{BASE_URL}/api/categories", timeout=30)
    assert categories.status_code == 200
    options = [item["name"] for item in categories.json()]
    assert category in options


def test_case_whitespace_category_normalization_reuses_existing(admin_client, api_client, created_courses):
    base = f"TEST CAT IT9 {uuid.uuid4().hex[:6]}"
    first = _create_course(admin_client, f"TEST_A_{uuid.uuid4().hex[:6]}", f"  {base}  ")
    assert first.status_code == 200
    created_courses.append(first.json()["course_id"])

    second = _create_course(admin_client, f"TEST_B_{uuid.uuid4().hex[:6]}", f"{base.lower()}   ")
    assert second.status_code == 200
    created_courses.append(second.json()["course_id"])

    options = api_client.get(f"{BASE_URL}/api/categories", timeout=30)
    assert options.status_code == 200
    normalized = [item["name"].strip().lower() for item in options.json()]
    assert normalized.count(base.lower()) == 1


# Validation and rollback safety
def test_create_rejects_empty_title(admin_client):
    payload = {"title": "   ", "category": f"TEST_CAT_{uuid.uuid4().hex[:6]}"}
    response = admin_client.post(f"{BASE_URL}/api/admin/courses", json=payload, timeout=30)
    assert response.status_code == 400


def test_create_rejects_invalid_category_inputs_and_does_not_orphan_category(admin_client, api_client):
    marker = f"TEST_CAT_ORPHAN_{uuid.uuid4().hex[:8]}"
    before = api_client.get(f"{BASE_URL}/api/categories", timeout=30)
    assert before.status_code == 200
    before_set = {item["name"].strip().lower() for item in before.json()}

    invalid_payloads = [
        {"title": "TEST bad cat", "category": "   "},
        {"title": "TEST bad cat", "category": "x" * 101},
        {"title": "TEST bad cat", "category": 123},
        {"title": "   ", "category": marker},
    ]

    for payload in invalid_payloads:
        response = admin_client.post(f"{BASE_URL}/api/admin/courses", json=payload, timeout=30)
        assert response.status_code == 400

    after = api_client.get(f"{BASE_URL}/api/categories", timeout=30)
    assert after.status_code == 200
    after_set = {item["name"].strip().lower() for item in after.json()}
    assert marker.lower() not in after_set
    assert before_set.issubset(after_set) or before_set == after_set


# Category-only updates must preserve existing lesson/resource attachments
def test_category_only_update_preserves_lessons_and_resources(admin_client, api_client, created_courses):
    unique = uuid.uuid4().hex[:8]
    lesson_video = f"https://cdn.example.com/videos/{unique}.mp4"
    resource_url = f"https://cdn.example.com/resources/{unique}.pdf"
    lessons = [{"title": "L1", "video_type": "youtube", "video_url": lesson_video, "description": "d", "duration": "10m", "is_free_preview": True}]
    resources = [{"name": "R1", "type": "pdf", "url": resource_url, "is_free_preview": True}]
    created = _create_course(admin_client, f"TEST_ATTACH_{unique}", f"TEST_CAT_ATTACH_{unique}", lessons=lessons, resources=resources)
    assert created.status_code == 200
    cid = created.json()["course_id"]
    created_courses.append(cid)

    before = api_client.get(f"{BASE_URL}/api/courses/{cid}", timeout=30)
    assert before.status_code == 200
    before_data = before.json()
    assert before_data["lessons"][0]["video_url"] == lesson_video
    assert before_data["resources"][0]["url"] == resource_url

    update_payload = {"category": f"TEST_CAT_ATTACH_UPDATED_{unique}"}
    updated = admin_client.put(f"{BASE_URL}/api/admin/courses/{cid}", json=update_payload, timeout=30)
    assert updated.status_code == 200

    after = api_client.get(f"{BASE_URL}/api/courses/{cid}", timeout=30)
    assert after.status_code == 200
    after_data = after.json()
    assert after_data["category"] == f"TEST_CAT_ATTACH_UPDATED_{unique}"
    assert after_data["lessons"][0]["video_url"] == lesson_video
    assert after_data["resources"][0]["url"] == resource_url


def test_category_update_to_existing_works_without_duplicate_name(admin_client, api_client, created_courses):
    existing_name = f"TEST_CAT_EXIST_{uuid.uuid4().hex[:6]}"
    c1 = _create_course(admin_client, f"TEST_EXIST_A_{uuid.uuid4().hex[:6]}", existing_name)
    assert c1.status_code == 200
    created_courses.append(c1.json()["course_id"])

    c2 = _create_course(admin_client, f"TEST_EXIST_B_{uuid.uuid4().hex[:6]}", f"TEST_OTHER_{uuid.uuid4().hex[:6]}")
    assert c2.status_code == 200
    second_id = c2.json()["course_id"]
    created_courses.append(second_id)

    upd = admin_client.put(f"{BASE_URL}/api/admin/courses/{second_id}", json={"category": existing_name.lower()}, timeout=30)
    assert upd.status_code == 200

    detail = api_client.get(f"{BASE_URL}/api/courses/{second_id}", timeout=30)
    assert detail.status_code == 200
    assert detail.json()["category"].strip().lower() == existing_name.lower()

    categories = api_client.get(f"{BASE_URL}/api/categories", timeout=30)
    assert categories.status_code == 200
    lowered = [item["name"].strip().lower() for item in categories.json()]
    assert lowered.count(existing_name.lower()) == 1


# Concurrent saves should create one canonical category option
def test_concurrent_course_creates_with_same_new_category_deduplicate(admin_client, api_client, created_courses):
    cat = f"TEST_CONCURRENT_{uuid.uuid4().hex[:8]}"

    def _worker(idx):
        title = f"TEST_CON_{idx}_{uuid.uuid4().hex[:6]}"
        return _create_course(admin_client, title, cat)

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(_worker, [1, 2]))

    for resp in responses:
        assert resp.status_code == 200
        created_courses.append(resp.json()["course_id"])

    options = api_client.get(f"{BASE_URL}/api/categories", timeout=30)
    assert options.status_code == 200
    lowered = [item["name"].strip().lower() for item in options.json()]
    assert lowered.count(cat.lower()) == 1
