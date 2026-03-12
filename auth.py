"""Authentication middleware for Firebase ID tokens."""
import logging
from typing import Optional

from fastapi import Request, HTTPException, Depends

from firebase_config import get_auth

logger = logging.getLogger(__name__)


class UserInfo:
    """Authenticated user info extracted from a Firebase ID token."""

    def __init__(self, uid: str, email: Optional[str], name: Optional[str], picture: Optional[str]):
        self.uid = uid
        self.email = email
        self.name = name
        self.picture = picture

    def dict(self):
        return {
            "uid": self.uid,
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
        }


def _extract_bearer_token(request: Request) -> Optional[str]:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None


def verify_firebase_token(request: Request) -> UserInfo:
    """Verify a Firebase ID token from the Authorization header.

    Returns UserInfo on success, raises HTTPException on failure.
    """
    token = _extract_bearer_token(request)
    if not token:
        raise HTTPException(401, "Missing or invalid Authorization header")

    try:
        auth = get_auth()
        decoded = auth.verify_id_token(token)
    except Exception as e:
        logger.warning("Token verification failed: %s", e)
        raise HTTPException(401, "Invalid or expired authentication token")

    return UserInfo(
        uid=decoded.get("uid", ""),
        email=decoded.get("email"),
        name=decoded.get("name"),
        picture=decoded.get("picture"),
    )


async def get_current_user(request: Request) -> UserInfo:
    """FastAPI dependency — requires valid Firebase auth."""
    return verify_firebase_token(request)


async def get_optional_user(request: Request) -> Optional[UserInfo]:
    """FastAPI dependency — returns UserInfo if authenticated, None otherwise."""
    token = _extract_bearer_token(request)
    if not token:
        return None
    try:
        auth = get_auth()
        decoded = auth.verify_id_token(token)
        return UserInfo(
            uid=decoded.get("uid", ""),
            email=decoded.get("email"),
            name=decoded.get("name"),
            picture=decoded.get("picture"),
        )
    except Exception:
        return None
