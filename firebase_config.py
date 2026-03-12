"""Firebase Admin SDK initialization.

On Cloud Run, credentials are auto-discovered via the metadata server.
For local dev, set GOOGLE_APPLICATION_CREDENTIALS env var pointing to a
service account JSON file.
"""
import os
import logging

import firebase_admin
from firebase_admin import credentials, firestore, storage, auth as firebase_auth

from config import FIREBASE_PROJECT_ID, FIRESTORE_DATABASE, STORAGE_BUCKET

logger = logging.getLogger(__name__)

_app = None
_firestore_client = None
_storage_bucket = None


def _initialize():
    """Initialize Firebase Admin SDK (idempotent)."""
    global _app
    if _app is not None:
        return

    cred = None
    sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if sa_path and os.path.isfile(sa_path):
        cred = credentials.Certificate(sa_path)
        logger.info("Firebase: using service account from GOOGLE_APPLICATION_CREDENTIALS")
    else:
        # Cloud Run provides Application Default Credentials automatically
        cred = credentials.ApplicationDefault()
        logger.info("Firebase: using application default credentials")

    _app = firebase_admin.initialize_app(cred, {
        "projectId": FIREBASE_PROJECT_ID,
        "storageBucket": STORAGE_BUCKET,
    })
    logger.info("Firebase Admin SDK initialized (project=%s)", FIREBASE_PROJECT_ID)


def get_firestore_client():
    """Return the Firestore client (initializes SDK on first call)."""
    global _firestore_client
    if _firestore_client is None:
        _initialize()
        _firestore_client = firestore.client(database_id=FIRESTORE_DATABASE)
    return _firestore_client


def get_storage_bucket():
    """Return the Cloud Storage bucket (initializes SDK on first call)."""
    global _storage_bucket
    if _storage_bucket is None:
        _initialize()
        _storage_bucket = storage.bucket(STORAGE_BUCKET)
    return _storage_bucket


def get_auth():
    """Return firebase_admin.auth module (initializes SDK on first call)."""
    _initialize()
    return firebase_auth
