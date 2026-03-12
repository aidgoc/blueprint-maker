"""Firestore data layer for users, blueprints, folders, and teams."""
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional

from google.cloud.firestore_v1 import FieldFilter

from firebase_config import get_firestore_client

logger = logging.getLogger(__name__)


def _now():
    return datetime.now(timezone.utc)


# ─── Users ──────────────────────────────────────────────────────────────

def create_or_update_user(uid: str, email: Optional[str], name: Optional[str], photo: Optional[str]) -> dict:
    """Create or update user document on login (upsert)."""
    db = get_firestore_client()
    ref = db.collection("users").document(uid)
    doc = ref.get()

    if doc.exists:
        update_data = {
            "last_login": _now(),
        }
        if email:
            update_data["email"] = email
        if name:
            update_data["display_name"] = name
        if photo:
            update_data["photo_url"] = photo
        ref.update(update_data)
        return ref.get().to_dict()
    else:
        user_data = {
            "uid": uid,
            "email": email or "",
            "display_name": name or "",
            "photo_url": photo or "",
            "plan": "free",
            "created_at": _now(),
            "last_login": _now(),
            "blueprint_count": 0,
            "storage_used_bytes": 0,
        }
        ref.set(user_data)
        return user_data


def get_user(uid: str) -> Optional[dict]:
    """Get user profile by UID."""
    db = get_firestore_client()
    doc = db.collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None


def update_user(uid: str, data: dict) -> None:
    """Partial update of user document."""
    db = get_firestore_client()
    db.collection("users").document(uid).update(data)


# ─── Blueprints ─────────────────────────────────────────────────────────

def create_blueprint(user_id: str, title: str, description: str) -> str:
    """Create a new blueprint document. Returns the auto-generated doc ID."""
    db = get_firestore_client()
    data = {
        "user_id": user_id,
        "title": title,
        "business_description": description,
        "status": "generating",
        "folder_id": None,
        "file_count": 0,
        "files": [],
        "answers": {},
        "research": {},
        "is_shared": False,
        "share_token": None,
        "created_at": _now(),
        "updated_at": _now(),
    }
    _, ref = db.collection("blueprints").add(data)
    return ref.id


def get_blueprint(blueprint_id: str) -> Optional[dict]:
    """Get a single blueprint by ID."""
    db = get_firestore_client()
    doc = db.collection("blueprints").document(blueprint_id).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None


def list_user_blueprints(user_id: str, folder_id: Optional[str] = None) -> list[dict]:
    """List blueprints for a user, optionally filtered by folder."""
    db = get_firestore_client()
    query = db.collection("blueprints").where(filter=FieldFilter("user_id", "==", user_id))

    if folder_id is not None:
        query = query.where(filter=FieldFilter("folder_id", "==", folder_id))

    query = query.order_by("created_at", direction="DESCENDING")
    results = []
    for doc in query.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results


def update_blueprint(blueprint_id: str, data: dict) -> None:
    """Update blueprint fields."""
    db = get_firestore_client()
    data["updated_at"] = _now()
    db.collection("blueprints").document(blueprint_id).update(data)


def delete_blueprint(blueprint_id: str) -> Optional[dict]:
    """Delete blueprint document. Returns the deleted doc data (for cleanup)."""
    db = get_firestore_client()
    ref = db.collection("blueprints").document(blueprint_id)
    doc = ref.get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["id"] = doc.id
    ref.delete()
    return data


def get_shared_blueprint(share_token: str) -> Optional[dict]:
    """Get a blueprint by its share token."""
    db = get_firestore_client()
    query = (
        db.collection("blueprints")
        .where(filter=FieldFilter("is_shared", "==", True))
        .where(filter=FieldFilter("share_token", "==", share_token))
        .limit(1)
    )
    for doc in query.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None


def generate_share_token() -> str:
    """Generate a URL-safe share token."""
    return secrets.token_urlsafe(16)


# ─── Folders ────────────────────────────────────────────────────────────

def create_folder(user_id: str, name: str, color: str = "#6366f1") -> str:
    """Create a folder. Returns the auto-generated doc ID."""
    db = get_firestore_client()
    data = {
        "user_id": user_id,
        "name": name,
        "color": color,
        "blueprint_count": 0,
        "created_at": _now(),
    }
    _, ref = db.collection("folders").add(data)
    return ref.id


def list_folders(user_id: str) -> list[dict]:
    """List all folders for a user."""
    db = get_firestore_client()
    query = (
        db.collection("folders")
        .where(filter=FieldFilter("user_id", "==", user_id))
        .order_by("created_at")
    )
    results = []
    for doc in query.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results


def get_folder(folder_id: str) -> Optional[dict]:
    """Get a single folder."""
    db = get_firestore_client()
    doc = db.collection("folders").document(folder_id).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None


def update_folder(folder_id: str, data: dict) -> None:
    """Update folder fields."""
    db = get_firestore_client()
    db.collection("folders").document(folder_id).update(data)


def delete_folder(folder_id: str) -> bool:
    """Delete a folder after moving its blueprints to root. Returns True if deleted."""
    db = get_firestore_client()
    ref = db.collection("folders").document(folder_id)
    doc = ref.get()
    if not doc.exists:
        return False

    folder_data = doc.to_dict()
    user_id = folder_data.get("user_id")

    # Move all blueprints in this folder to root (folder_id = None)
    blueprints = (
        db.collection("blueprints")
        .where(filter=FieldFilter("user_id", "==", user_id))
        .where(filter=FieldFilter("folder_id", "==", folder_id))
    )
    for bp_doc in blueprints.stream():
        bp_doc.reference.update({"folder_id": None, "updated_at": _now()})

    ref.delete()
    return True


# ─── Teams (stubs for future) ───────────────────────────────────────────

def create_team(name: str, owner_id: str) -> str:
    """Stub: Create a team. Returns doc ID."""
    raise NotImplementedError("Teams feature is not yet available")


def get_team(team_id: str) -> Optional[dict]:
    """Stub: Get team by ID."""
    raise NotImplementedError("Teams feature is not yet available")


def add_team_member(team_id: str, uid: str, role: str = "member") -> None:
    """Stub: Add a member to a team."""
    raise NotImplementedError("Teams feature is not yet available")


def list_user_teams(uid: str) -> list[dict]:
    """Stub: List teams a user belongs to."""
    raise NotImplementedError("Teams feature is not yet available")
