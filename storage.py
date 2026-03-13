"""Cloud Storage layer for blueprint file management."""
import logging
from datetime import timedelta
from typing import Optional

from firebase_config import get_storage_bucket

logger = logging.getLogger(__name__)


def _blueprint_prefix(user_id: str, blueprint_id: str) -> str:
    """Build the storage path prefix for a blueprint."""
    return f"blueprints/{user_id}/{blueprint_id}/"


def upload_blueprint_files(user_id: str, blueprint_id: str, files: list[dict]) -> list[dict]:
    """Upload HTML files to Cloud Storage.

    Args:
        user_id: Firebase UID
        blueprint_id: Firestore blueprint doc ID
        files: list of {"name": str, "content": str}

    Returns:
        list of {"name": str, "storage_path": str, "size_bytes": int}
    """
    bucket = get_storage_bucket()
    prefix = _blueprint_prefix(user_id, blueprint_id)
    uploaded = []

    for f in files:
        name = f["name"]
        content = f["content"]
        storage_path = f"{prefix}{name}"
        try:
            blob = bucket.blob(storage_path)
            content_bytes = content.encode("utf-8") if isinstance(content, str) else content
            blob.upload_from_string(content_bytes, content_type="text/html")

            uploaded.append({
                "name": name,
                "storage_path": storage_path,
                "size_bytes": len(content_bytes),
            })
            logger.info("Uploaded %s (%d bytes)", storage_path, len(content_bytes))
        except Exception as e:
            logger.error("Failed to upload file %s: %s", name, e)

    return uploaded


def get_file_url(storage_path: str, expiry_minutes: int = 60) -> str:
    """Generate a signed URL for a file in Cloud Storage."""
    bucket = get_storage_bucket()
    blob = bucket.blob(storage_path)
    url = blob.generate_signed_url(
        expiration=timedelta(minutes=expiry_minutes),
        method="GET",
    )
    return url


def download_file(storage_path: str) -> Optional[bytes]:
    """Download file content from Cloud Storage."""
    try:
        bucket = get_storage_bucket()
        blob = bucket.blob(storage_path)
        if not blob.exists():
            return None
        return blob.download_as_bytes()
    except Exception as e:
        logger.error("Failed to download file %s: %s", storage_path, e)
        return None


def delete_blueprint_files(user_id: str, blueprint_id: str) -> int:
    """Delete all files for a blueprint. Returns count of deleted files."""
    bucket = get_storage_bucket()
    prefix = _blueprint_prefix(user_id, blueprint_id)
    try:
        blobs = list(bucket.list_blobs(prefix=prefix))
    except Exception as e:
        logger.error("Failed to list blobs for deletion (prefix %s): %s", prefix, e)
        return 0
    count = 0
    for blob in blobs:
        try:
            blob.delete()
            count += 1
            logger.info("Deleted %s", blob.name)
        except Exception as e:
            logger.error("Failed to delete blob %s: %s", blob.name, e)
    return count


def get_storage_usage(user_id: str) -> int:
    """Calculate total bytes used by a user in Cloud Storage."""
    try:
        bucket = get_storage_bucket()
        prefix = f"blueprints/{user_id}/"
        total = 0
        for blob in bucket.list_blobs(prefix=prefix):
            total += blob.size or 0
        return total
    except Exception as e:
        logger.error("Failed to calculate storage usage for user %s: %s", user_id, e)
        return 0
