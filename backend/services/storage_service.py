# Cloudflare R2 Storage Service
import os
import uuid
import aiofiles
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# Configuration from environment
STORAGE_MODE = os.environ.get("STORAGE_MODE", "mock")  # mock, r2, s3

# Cloudflare R2 configuration
R2_ENDPOINT = os.environ.get("CLOUDFLARE_R2_ENDPOINT", "")
R2_ACCESS_KEY = os.environ.get("CLOUDFLARE_R2_ACCESS_KEY_ID", "")
R2_SECRET_KEY = os.environ.get("CLOUDFLARE_R2_SECRET_ACCESS_KEY", "")
R2_BUCKET = os.environ.get("CLOUDFLARE_R2_BUCKET_NAME", "mera-mentor-media")
R2_PUBLIC_URL = os.environ.get("CLOUDFLARE_R2_PUBLIC_URL", "")

# Mock storage directory
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# File size limits
MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

# Allowed file types
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"]
ALLOWED_PDF_TYPES = ["application/pdf"]
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]

# Initialize S3 client (works with R2)
s3_client = None
if STORAGE_MODE == "r2" and R2_ENDPOINT and R2_ACCESS_KEY:
    s3_client = boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )

def get_file_extension(content_type: str) -> str:
    """Get file extension from content type"""
    ext_map = {
        "video/mp4": ".mp4",
        "video/quicktime": ".mov",
        "video/x-msvideo": ".avi",
        "video/webm": ".webm",
        "application/pdf": ".pdf",
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    return ext_map.get(content_type, "")

def validate_file_type(content_type: str, upload_type: str) -> tuple[bool, str]:
    """Validate file type against allowed types"""
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

def validate_file_size(file_size: int, upload_type: str) -> tuple[bool, str]:
    """Validate file size against limits"""
    limits = {"video": MAX_VIDEO_SIZE, "pdf": MAX_PDF_SIZE, "image": MAX_IMAGE_SIZE}
    max_size = limits.get(upload_type, MAX_IMAGE_SIZE)
    if file_size > max_size:
        size_mb = max_size // (1024 * 1024)
        return False, f"File too large. Max: {size_mb}MB"
    return True, ""

def generate_file_key(upload_type: str, course_id: Optional[str] = None, 
                       lesson_id: Optional[str] = None, ext: str = "") -> str:
    """Generate unique file key with folder structure"""
    uid = uuid.uuid4().hex[:12]
    if course_id and lesson_id:
        return f"{upload_type}s/{course_id}/{lesson_id}/{uid}{ext}"
    elif course_id:
        return f"{upload_type}s/{course_id}/{uid}{ext}"
    return f"{upload_type}s/{uid}{ext}"

# ========== Mock Storage Functions ==========

async def save_file_mock(file_content: bytes, file_key: str) -> str:
    """Save file to local storage (mock mode)"""
    file_path = UPLOAD_DIR / file_key
    file_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_content)
    return str(file_path)

async def delete_file_mock(file_key: str) -> bool:
    """Delete file from local storage (mock mode)"""
    file_path = UPLOAD_DIR / file_key
    if file_path.exists():
        file_path.unlink()
        return True
    return False

def get_download_url_mock(file_key: str) -> str:
    """Generate download URL for mock storage"""
    return f"/api/media/files/{file_key}"

# ========== R2/S3 Storage Functions ==========

async def generate_presigned_upload_url(file_key: str, content_type: str, expires_in: int = 900) -> Optional[str]:
    """Generate presigned URL for direct upload to R2 (15 min expiry)"""
    if STORAGE_MODE == "mock" or not s3_client:
        return None
    
    try:
        url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": R2_BUCKET,
                "Key": file_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )
        return url
    except ClientError as e:
        print(f"Error generating upload URL: {e}")
        return None

async def generate_presigned_download_url(file_key: str, expires_in: int = 3600) -> Optional[str]:
    """Generate presigned URL for download from R2 (1 hour expiry)"""
    if STORAGE_MODE == "mock" or not s3_client:
        return get_download_url_mock(file_key)
    
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": R2_BUCKET,
                "Key": file_key,
            },
            ExpiresIn=expires_in,
        )
        return url
    except ClientError as e:
        print(f"Error generating download URL: {e}")
        return None

async def upload_file_to_r2(file_content: bytes, file_key: str, content_type: str) -> bool:
    """Upload file directly to R2"""
    if STORAGE_MODE == "mock" or not s3_client:
        await save_file_mock(file_content, file_key)
        return True
    
    try:
        s3_client.put_object(
            Bucket=R2_BUCKET,
            Key=file_key,
            Body=file_content,
            ContentType=content_type,
        )
        return True
    except ClientError as e:
        print(f"Error uploading to R2: {e}")
        return False

async def delete_file_from_r2(file_key: str) -> bool:
    """Delete file from R2"""
    if STORAGE_MODE == "mock" or not s3_client:
        return await delete_file_mock(file_key)
    
    try:
        s3_client.delete_object(Bucket=R2_BUCKET, Key=file_key)
        return True
    except ClientError as e:
        print(f"Error deleting from R2: {e}")
        return False

def get_public_url(file_key: str) -> str:
    """Get public URL for a file (for thumbnails, etc.)"""
    if STORAGE_MODE == "mock" or not R2_PUBLIC_URL:
        return f"/api/media/files/{file_key}"
    return f"{R2_PUBLIC_URL}/{file_key}"

# ========== Unified Interface ==========

async def upload_file(file_content: bytes, file_key: str, content_type: str) -> str:
    """Upload file to storage (handles mock/R2 automatically)"""
    if STORAGE_MODE == "r2" and s3_client:
        await upload_file_to_r2(file_content, file_key, content_type)
        return get_public_url(file_key)
    else:
        await save_file_mock(file_content, file_key)
        return get_download_url_mock(file_key)

async def delete_file(file_key: str) -> bool:
    """Delete file from storage (handles mock/R2 automatically)"""
    if STORAGE_MODE == "r2" and s3_client:
        return await delete_file_from_r2(file_key)
    return await delete_file_mock(file_key)

async def get_signed_url(file_key: str, expires_in: int = 3600) -> str:
    """Get signed download URL (handles mock/R2 automatically)"""
    if STORAGE_MODE == "r2" and s3_client:
        url = await generate_presigned_download_url(file_key, expires_in)
        return url or get_download_url_mock(file_key)
    return get_download_url_mock(file_key)

def is_r2_enabled() -> bool:
    """Check if R2 storage is enabled"""
    return STORAGE_MODE == "r2" and s3_client is not None
