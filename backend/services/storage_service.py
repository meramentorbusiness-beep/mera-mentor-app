# Cloudflare R2 object storage client for Mera Mentor.
# Uses the S3-compatible R2 API via boto3. Files are stored privately;
# access is gated by the FastAPI layer.
import asyncio
import os
import uuid
from functools import lru_cache
from typing import Tuple

import boto3
from botocore.client import Config

# File type config
MAX_VIDEO_SIZE = 500 * 1024 * 1024   # 500MB
MAX_PDF_SIZE   = 50  * 1024 * 1024   # 50MB
MAX_IMAGE_SIZE = 5   * 1024 * 1024   # 5MB

ALLOWED_VIDEO_TYPES = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"]
ALLOWED_PDF_TYPES   = ["application/pdf"]
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]

_R2_ENV_VARS = (
    "CLOUDFLARE_R2_ACCOUNT_ID",
    "CLOUDFLARE_R2_ACCESS_KEY_ID",
    "CLOUDFLARE_R2_SECRET_ACCESS_KEY",
    "CLOUDFLARE_R2_BUCKET_NAME",
)


def is_storage_enabled() -> bool:
    """True only when all R2 settings are present."""
    return all(os.environ.get(name) for name in _R2_ENV_VARS)


@lru_cache(maxsize=1)
def _client():
    if not is_storage_enabled():
        raise RuntimeError(
            "Cloudflare R2 is not configured. Set CLOUDFLARE_R2_ACCOUNT_ID, "
            "CLOUDFLARE_R2_ACCESS_KEY_ID, CLOUDFLARE_R2_SECRET_ACCESS_KEY, "
            "and CLOUDFLARE_R2_BUCKET_NAME."
        )
    account_id = os.environ["CLOUDFLARE_R2_ACCOUNT_ID"]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["CLOUDFLARE_R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["CLOUDFLARE_R2_SECRET_ACCESS_KEY"],
        region_name="auto",  # R2 does not use standard AWS regions
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            retries={"mode": "standard", "max_attempts": 3},
        ),
    )


def _bucket() -> str:
    return os.environ["CLOUDFLARE_R2_BUCKET_NAME"]


def init_storage() -> None:
    """Validate R2 connectivity on startup. No-op if R2 is not configured."""
    if not is_storage_enabled():
        return
    # head_bucket verifies credentials and bucket existence without listing objects.
    _client().head_bucket(Bucket=_bucket())


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
    """Generate a unique, collision-safe storage key.

    Keys are stored at the bucket root under a per-type prefix — do NOT
    include the bucket name, boto3 passes that separately via Bucket=.
    Example outputs (upload_type -> key):
      video  -> videos/<uuid>.mp4
      pdf    -> pdfs/<uuid>.pdf
      image  -> images/<uuid>.jpg
    """
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()[:20]
    uid = uuid.uuid4().hex
    return f"{upload_type}s/{uid}{ext}"


async def upload_file(file_content: bytes, upload_type: str, filename: str, content_type: str) -> str:
    """Upload a file to R2 and return its storage key."""
    if not is_storage_enabled():
        raise RuntimeError("Object storage is not configured")
    key = generate_storage_path(upload_type, filename)

    def _put() -> None:
        _client().put_object(
            Bucket=_bucket(),
            Key=key,
            Body=file_content,
            ContentType=content_type or "application/octet-stream",
        )

    await asyncio.to_thread(_put)
    return key


async def download_file(storage_path: str) -> Tuple[bytes, str]:
    """Download a file from R2 by its key. Returns (bytes, content_type)."""
    if not is_storage_enabled():
        raise RuntimeError("Object storage is not configured")
    if not storage_path or storage_path.startswith(("/", "http://", "https://")):
        raise ValueError("Invalid storage key")

    def _get() -> Tuple[bytes, str]:
        try:
            resp = _client().get_object(Bucket=_bucket(), Key=storage_path)
        except _client().exceptions.NoSuchKey:
            raise FileNotFoundError(f"Object not found: {storage_path}")
        try:
            data = resp["Body"].read()
            ct = resp.get("ContentType") or "application/octet-stream"
            return data, ct
        finally:
            resp["Body"].close()

    return await asyncio.to_thread(_get)


async def presigned_get_url(storage_path: str, expires_seconds: int = 1800) -> str:
    """Generate a temporary GET URL for a stored object (default 30 min)."""
    if not is_storage_enabled():
        raise RuntimeError("Object storage is not configured")
    if not (1 <= expires_seconds <= 604800):
        raise ValueError("Expiry must be 1 second through 7 days")
    return await asyncio.to_thread(
        lambda: _client().generate_presigned_url(
            "get_object",
            Params={"Bucket": _bucket(), "Key": storage_path},
            ExpiresIn=expires_seconds,
        )
    )
