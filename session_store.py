"""Session persistence layer — write-through cache with Firestore backup.

Sessions live in-memory for speed. On key state changes, they're written to
Firestore so users can resume after Cloud Run restarts or cold starts.

generated_files are excluded from Firestore (too large, already persisted
to Cloud Storage via _persist_blueprint_to_firebase).
"""
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Keys that are too large or transient to persist to Firestore
_EXCLUDE_FROM_FIRESTORE = {"generated_files", "generate_progress", "generate_error"}


def _firestore_collection():
    """Get the Firestore sessions collection (lazy import)."""
    from firebase_config import get_firestore_client
    from config import FIRESTORE_DATABASE
    db = get_firestore_client()
    return db.collection("sessions")


def _to_firestore_data(sess: dict) -> dict:
    """Strip keys that shouldn't go to Firestore."""
    return {k: v for k, v in sess.items() if k not in _EXCLUDE_FROM_FIRESTORE}


def save_session(sid: str, sess: dict, sessions: dict) -> None:
    """Save session to memory and Firestore."""
    sessions[sid] = sess
    try:
        _firestore_collection().document(sid).set(_to_firestore_data(sess))
    except Exception as e:
        logger.error("Failed to persist session %s to Firestore: %s", sid, e)


def update_session(sid: str, sess: dict) -> None:
    """Write current session state to Firestore (call after key mutations)."""
    try:
        _firestore_collection().document(sid).set(_to_firestore_data(sess))
    except Exception as e:
        logger.error("Failed to update session %s in Firestore: %s", sid, e)


def get_session(sid: str, sessions: dict) -> Optional[dict]:
    """Get session from memory, falling back to Firestore."""
    sess = sessions.get(sid)
    if sess is not None:
        return sess

    # Try Firestore recovery
    try:
        doc = _firestore_collection().document(sid).get()
        if doc.exists:
            sess = doc.to_dict()
            # Check TTL
            created_at = sess.get("created_at", 0)
            if time.time() - created_at > 7200:  # SESSION_TTL_SECONDS
                # Expired — clean up Firestore too
                try:
                    _firestore_collection().document(sid).delete()
                except Exception:
                    pass
                return None
            # Restore to memory cache
            sessions[sid] = sess
            logger.info("Recovered session %s from Firestore (status=%s)", sid, sess.get("status"))
            return sess
    except Exception as e:
        logger.error("Failed to recover session %s from Firestore: %s", sid, e)

    return None


def delete_session(sid: str, sessions: dict) -> None:
    """Remove session from memory and Firestore."""
    sessions.pop(sid, None)
    try:
        _firestore_collection().document(sid).delete()
    except Exception as e:
        logger.error("Failed to delete session %s from Firestore: %s", sid, e)


def cleanup_expired(sessions: dict) -> None:
    """Remove expired sessions from memory and Firestore."""
    now = time.time()
    expired = [
        sid for sid, sess in sessions.items()
        if now - sess.get("created_at", 0) > 7200
    ]
    for sid in expired:
        delete_session(sid, sessions)
