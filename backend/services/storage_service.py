# Emergent Object Storage Service for Mera Mentor
import os
import uuid
import requests
from typing import Optional

# Configuration
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
_STORAGE_BASE = (os.environ.get("INTEGRATION_PROXY_URL") or "").strip() or "https://integrations.emergentagent.com"
STORAGE_URL = _STORAGE_BASE.rstrip("/") + "/objstore/api/v1/storage"
APP_NAME = "mera-mentor"

# File type config
MAX_VIDEO_SIZE = 500 * 1024 * 1024   # 500MB
MAX_PDF_SIZE   = 50  * 1024 * 1024   # 50MB
MAX_IMAGE_SIZE = 5   * 1024 * 1024   # 5MB

ALLOWED_VIDEO_TYPES = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"]
ALLOWED_PDF_TYPES   = ["application/pdf"]
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]

_storage_key: Optional[str] = None


def init_storage(force: bool = False) -> str:
    """Initialise storage once at startup; reuse the key every request."""
    global _storage_key
    if _storage_key and not force:
        return _storage_key
    resp = requests.post(
        f"{STORAGE_URL}/init",
        json={"emergent_key": EMERGENT_KEY},
        timeout=30,
    )
    resp.raise_for_status()
    _storage_key = resp.json()["storage_key"]
    return _storage_key


def put_object(path: str, data: bytes, content_type: str) -> dict:
    """Upload bytes to object storage. Returns {"path": ..., "size": ..., "etag": ...}"""
    key = init_storage()
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data,
        timeout=120,
    )
    if resp.status_code == 404:
        # Storage key went stale — reinit and retry once
        key = init_storage(force=True)
        resp = requests.put(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key, "Content-Type": content_type},
            data=data,
            timeout=120,
        )
    resp.raise_for_status()
    return resp.json()


def get_object(path: str) -> tuple:
    """Download bytes from object storage. Returns (bytes, content_type)."""
    key = init_storage()
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key},
        timeout=60,
    )
    if resp.status_code == 404 and "storage_key" not in resp.text.lower():
        raise FileNotFoundError(f"Object not found: {path}")
    if resp.status_code == 404:
        key = init_storage(force=True)
        resp = requests.get(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key},
            timeout=60,
        )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


def validate_file_type(content_type: str, upload_type: str) -> tuple:
    if upload_type == "video":
        if content_type not in ALLOWED_VIDEO_TYPES:
            return False, "Invalid video type. Allowed: MP4, MOV, AVI, WebM"
        return True, ""
    elif upload_type == "pdf":
        if content_type not in ALLOWED_PDF_TYPES:
            return False, "Only PDF files allowed"
        return True, ""
    elif upload_type == "image":
        if content_type not in ALLOWED_IMAGE_TYPES:
            return False, "Invalid image type. Allowed: JPEG, PNG, WebP, GIF"
        return True, ""
    return False, "Invalid upload type"


def validate_file_size(file_size: int, upload_type: str) -> tuple:
    limits = {"video": MAX_VIDEO_SIZE, "pdf": MAX_PDF_SIZE, "image": MAX_IMAGE_SIZE}
    max_size = limits.get(upload_type, MAX_IMAGE_SIZE)
    if file_size > max_size:
        size_mb = max_size // (1024 * 1024)
        return False, f"File too large. Max: {size_mb}MB"
    return True, ""


def generate_storage_path(upload_type: str, filename: str) -> str:
    """Generate a unique, collision-safe storage path."""
    ext_map = {
        "video/mp4": ".mp4", "video/quicktime": ".mov",
        "video/x-msvideo": ".avi", "video/webm": ".webm",
        "application/pdf": ".pdf", "image/jpeg": ".jpg",
        "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif",
    }
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()
    uid = uuid.uuid4().hex
    return f"{APP_NAME}/{upload_type}s/{uid}{ext}"


async def upload_file(file_content: bytes, upload_type: str, filename: str, content_type: str) -> str:
    """Upload a file and return its storage path."""
    path = generate_storage_path(upload_type, filename)
    result = put_object(path, file_content, content_type)
    return result["path"]


async def download_file(storage_path: str) -> tuple:
    """Download a file by its storage path. Returns (bytes, content_type)."""
    return get_object(storage_path)


def is_storage_enabled() -> bool:
    return bool(EMERGENT_KEY)
