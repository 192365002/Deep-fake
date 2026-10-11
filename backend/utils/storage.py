"""
Supabase Storage Utilities for Social Shield
Handles user-isolated private file storage, signed URL generation, validation, and cleanup.
"""
import os
import uuid
import logging
from typing import Optional, Dict, Any
from utils.database import get_supabase_client, is_mock_db

logger = logging.getLogger(__name__)

STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "scan-media")
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4", "audio/x-m4a"}
ALL_ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES | ALLOWED_AUDIO_TYPES


def validate_file(file_bytes: bytes, content_type: str, category: str = "image"):
    """Enforce strict file type and size constraints"""
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File size ({len(file_bytes)} bytes) exceeds 20MB limit")

    if category == "image" and content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(f"Unsupported image type: {content_type}. Allowed: {ALLOWED_IMAGE_TYPES}")
    elif category == "video" and content_type not in ALLOWED_VIDEO_TYPES:
        raise ValueError(f"Unsupported video type: {content_type}. Allowed: {ALLOWED_VIDEO_TYPES}")
    elif category == "audio" and content_type not in ALLOWED_AUDIO_TYPES:
        raise ValueError(f"Unsupported audio type: {content_type}. Allowed: {ALLOWED_AUDIO_TYPES}")
    elif content_type not in ALL_ALLOWED_TYPES:
        raise ValueError(f"Unsupported media type: {content_type}")


async def upload_scan_media(
    user_id: str,
    file_bytes: bytes,
    original_filename: str,
    content_type: str,
    category: str = "image"
) -> Dict[str, Any]:
    """
    Uploads a file to Supabase Storage in user-scoped path: {user_id}/{unique_filename}.
    Generates a temporary signed URL for authorized client viewing.
    """
    validate_file(file_bytes, content_type, category)

    # Sanitize and unique-ify filename
    ext = os.path.splitext(original_filename)[1].lower()
    if not ext:
        ext = ".jpg" if "jpeg" in content_type else (".png" if "png" in content_type else ".bin")
    
    unique_name = f"{uuid.uuid4().hex}{ext}"
    storage_path = f"{user_id}/{unique_name}"

    client = get_supabase_client()
    if client is not None and not is_mock_db():
        try:
            # Upload to private bucket
            res = client.storage.from_(STORAGE_BUCKET).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": "false"}
            )
            
            # Generate 1-hour signed URL
            signed_url_res = client.storage.from_(STORAGE_BUCKET).create_signed_url(
                path=storage_path,
                expires_in=3600
            )
            signed_url = signed_url_res.get("signedURL") or signed_url_res.get("signedUrl")

            return {
                "storage_path": storage_path,
                "storage_url": signed_url,
                "bucket": STORAGE_BUCKET,
                "file_size": len(file_bytes),
                "content_type": content_type
            }
        except Exception as e:
            logger.error(f"Failed to upload to Supabase Storage: {e}. Falling back to local/memory ref.")
            
    # Dev / Mock fallback
    return {
        "storage_path": f"local://{storage_path}",
        "storage_url": f"/static/uploads/{unique_name}",
        "bucket": STORAGE_BUCKET,
        "file_size": len(file_bytes),
        "content_type": content_type
    }


async def delete_scan_media(storage_path: Optional[str]) -> bool:
    """Removes stored media from Supabase Storage when scan record is deleted"""
    if not storage_path or storage_path.startswith("local://"):
        return True

    client = get_supabase_client()
    if client is not None and not is_mock_db():
        try:
            client.storage.from_(STORAGE_BUCKET).remove([storage_path])
            logger.info(f"Deleted storage object: {storage_path}")
            return True
        except Exception as e:
            logger.warning(f"Error removing storage object {storage_path}: {e}")
            return False
    return True


async def get_authorized_url(storage_path: str, expires_in: int = 3600) -> Optional[str]:
    """Generates a fresh temporary signed URL for authorized access"""
    if not storage_path:
        return None
    if storage_path.startswith("local://"):
        return storage_path.replace("local://", "/static/uploads/")

    client = get_supabase_client()
    if client is not None and not is_mock_db():
        try:
            res = client.storage.from_(STORAGE_BUCKET).create_signed_url(storage_path, expires_in)
            return res.get("signedURL") or res.get("signedUrl")
        except Exception as e:
            logger.error(f"Failed to create signed URL for {storage_path}: {e}")
            return None
    return None
