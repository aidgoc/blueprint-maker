"""Service Blueprint Maker — FastAPI Server
Staged architecture: 3 question stages with research between each.

Security hardening applied:
- Rate limiting (in-memory, per-IP)
- Input size validation
- Session cleanup (TTL-based)
- Error message sanitization
- CORS restriction
- Session ID entropy increase
- Firebase Authentication (optional for anonymous, required for user endpoints)
"""
import asyncio
import json
import logging
import os
import secrets
import time
import uuid
import zipfile
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel, field_validator

from config import PORT
from questionnaire import (
    get_question_for_step, get_stage_for_step, get_total_questions,
    compile_stage_answers, generate_stage2_questions, STAGES,
)
from research import research_industry, research_compliance_and_kpis, compile_master_context
from generator import generate_blueprint_kit
from session_store import save_session, get_session, update_session, cleanup_expired, delete_session

logger = logging.getLogger(__name__)

app = FastAPI(title="Service Blueprint Maker", docs_url=None, redoc_url=None)

# --- CORS: restrict to same-origin in production ---
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

sessions: dict = {}
BASE_DIR = Path(__file__).parent

# --- Security constants ---
MAX_INPUT_LENGTH = 5000          # Max chars per answer/description
MAX_SESSIONS = 200               # Max concurrent sessions
SESSION_TTL_SECONDS = 7200       # 2 hours
MAX_REQUESTS_PER_MINUTE = 30     # Per IP
MAX_GENERATE_PER_HOUR = 5        # Per IP (expensive LLM calls)
SESSION_ID_LENGTH = 24           # Longer session IDs (96 bits)


# --- Lazy Firebase imports (don't break if firebase-admin not installed) ---

_firebase_available = None


def is_firebase_available() -> bool:
    """Check if Firebase SDK is available and initialized."""
    global _firebase_available
    if _firebase_available is not None:
        return _firebase_available
    try:
        from firebase_config import get_firestore_client
        get_firestore_client()
        _firebase_available = True
    except Exception as e:
        logger.warning("Firebase not available: %s", e)
        _firebase_available = False
    return _firebase_available


# ─── Rate Limiting (in-memory) ───────────────────────────────────────

class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""

    def __init__(self):
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.generate_requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup_window(self, timestamps: list[float], window_seconds: int) -> list[float]:
        now = time.time()
        return [t for t in timestamps if now - t < window_seconds]

    def check_rate_limit(self, ip: str) -> bool:
        """Returns True if request is allowed, False if rate limited."""
        self.requests[ip] = self._cleanup_window(self.requests[ip], 60)
        if len(self.requests[ip]) >= MAX_REQUESTS_PER_MINUTE:
            return False
        self.requests[ip].append(time.time())
        return True

    def check_generate_limit(self, ip: str) -> bool:
        """Returns True if generate request is allowed."""
        self.generate_requests[ip] = self._cleanup_window(self.generate_requests[ip], 3600)
        if len(self.generate_requests[ip]) >= MAX_GENERATE_PER_HOUR:
            return False
        self.generate_requests[ip].append(time.time())
        return True

    def cleanup(self):
        """Remove stale entries."""
        now = time.time()
        for ip in list(self.requests.keys()):
            self.requests[ip] = [t for t in self.requests[ip] if now - t < 60]
            if not self.requests[ip]:
                del self.requests[ip]
        for ip in list(self.generate_requests.keys()):
            self.generate_requests[ip] = [t for t in self.generate_requests[ip] if now - t < 3600]
            if not self.generate_requests[ip]:
                del self.generate_requests[ip]


rate_limiter = RateLimiter()


def get_client_ip(request: Request) -> str:
    """Get client IP, respecting X-Forwarded-For for Cloud Run."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(request: Request):
    ip = get_client_ip(request)
    if not rate_limiter.check_rate_limit(ip):
        raise HTTPException(429, "Too many requests. Please slow down.")


# ─── Session Cleanup ─────────────────────────────────────────────────

def cleanup_expired_sessions():
    """Remove expired sessions from memory and Firestore."""
    cleanup_expired(sessions)


# ─── Input Validation ────────────────────────────────────────────────

class StartRequest(BaseModel):
    business_description: str

    @field_validator("business_description")
    @classmethod
    def validate_description(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Business description cannot be empty")
        if len(v) > MAX_INPUT_LENGTH:
            raise ValueError(f"Description too long (max {MAX_INPUT_LENGTH} characters)")
        return v


class AnswerRequest(BaseModel):
    session_id: str
    answer: str

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Answer cannot be empty")
        if len(v) > MAX_INPUT_LENGTH:
            raise ValueError(f"Answer too long (max {MAX_INPUT_LENGTH} characters)")
        return v

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v):
        if not v or len(v) > 48:
            raise ValueError("Invalid session ID")
        if not all(c in "0123456789abcdef" for c in v):
            raise ValueError("Invalid session ID format")
        return v


class GenerateRequest(BaseModel):
    session_id: str

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v):
        if not v or len(v) > 48:
            raise ValueError("Invalid session ID")
        if not all(c in "0123456789abcdef" for c in v):
            raise ValueError("Invalid session ID format")
        return v


class CreateFolderRequest(BaseModel):
    name: str
    color: str = "#6366f1"

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Folder name cannot be empty")
        if len(v) > 100:
            raise ValueError("Folder name too long (max 100 characters)")
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v):
        v = v.strip()
        if not v.startswith("#") or len(v) not in (4, 7):
            raise ValueError("Invalid color format (use hex, e.g. #6366f1)")
        return v


class UpdateFolderRequest(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


class UpdateBlueprintRequest(BaseModel):
    title: Optional[str] = None
    folder_id: Optional[str] = None
    is_shared: Optional[bool] = None


# ─── Error Sanitization ──────────────────────────────────────────────

def safe_error_message(e: Exception) -> str:
    """Sanitize error messages to avoid leaking internal details."""
    msg = str(e)
    # Strip file paths
    if "/" in msg or "\\" in msg:
        msg = "An internal error occurred"
    # Strip API keys or tokens that might appear in errors
    if any(keyword in msg.lower() for keyword in ["api_key", "token", "secret", "password", "authorization"]):
        msg = "An internal error occurred"
    # Truncate overly long messages
    if len(msg) > 200:
        msg = msg[:200] + "..."
    return msg


# ─── Firebase helper for post-generation persistence ─────────────────

def _persist_blueprint_to_firebase(user_id: str, session: dict) -> bool:
    """Save a generated blueprint to Firestore + Cloud Storage.

    Called synchronously after generation completes for authenticated users.
    Returns True on success, False on failure.
    """
    try:
        from db import create_blueprint, update_blueprint, update_user, get_user
        from storage import upload_blueprint_files

        title = session["answers"].get("company_name", "Untitled Blueprint")
        description = session.get("business_description", "")
        files = session.get("generated_files", [])

        bp_id = create_blueprint(user_id, title, description)

        uploaded = upload_blueprint_files(user_id, bp_id, files)

        total_bytes = sum(f["size_bytes"] for f in uploaded)

        update_blueprint(bp_id, {
            "status": "completed",
            "file_count": len(uploaded),
            "files": uploaded,
            "answers": session.get("answers", {}),
            "research": session.get("research", {}),
        })

        user = get_user(user_id)
        if user:
            update_user(user_id, {
                "blueprint_count": (user.get("blueprint_count", 0) or 0) + 1,
                "storage_used_bytes": (user.get("storage_used_bytes", 0) or 0) + total_bytes,
            })

        session["blueprint_id"] = bp_id
        logger.info("Persisted blueprint %s for user %s", bp_id, user_id)

        # Save blocks to Firestore sections
        try:
            from block_converter import convert_department_to_blocks, convert_master_to_blocks, convert_glossary_to_blocks
            from block_renderer import render_block, CURRENT_RENDERER_VERSION
            from block_types import slugify
            from db import create_section, update_section_order

            raw = session.get("raw_results", {})
            if raw:
                section_order = []
                position = 0

                # Master section
                if raw.get("master"):
                    master_blocks = convert_master_to_blocks(raw["master"])
                    for block in master_blocks:
                        block["html_cache"] = render_block(block)
                    create_section(bp_id, "master_blueprint", "Master Blueprint", "", position, master_blocks)
                    section_order.append("master_blueprint")
                    position += 1

                # Department sections
                for dept in raw.get("departments", []):
                    dept_blocks = convert_department_to_blocks(dept)
                    for block in dept_blocks:
                        block["html_cache"] = render_block(block)
                    dept_name = dept.get("department", "Department")
                    sid = slugify(dept_name)
                    create_section(bp_id, sid, dept_name, "", position, dept_blocks)
                    section_order.append(sid)
                    position += 1

                # Glossary section
                if raw.get("glossary"):
                    glossary_blocks = convert_glossary_to_blocks(raw["glossary"])
                    for block in glossary_blocks:
                        block["html_cache"] = render_block(block)
                    create_section(bp_id, "glossary", "Glossary & Appendix", "", position, glossary_blocks)
                    section_order.append("glossary")

                update_section_order(bp_id, section_order)
                update_blueprint(bp_id, {"format": "blocks", "renderer_version": CURRENT_RENDERER_VERSION})
                logger.info("Saved %d block sections for blueprint %s", len(section_order), bp_id)

        except Exception as e:
            logger.error("Failed to save blocks for %s (falling back to legacy): %s", bp_id, e)
            # Legacy HTML files are already uploaded -- blueprint still works

        return True

    except Exception as e:
        logger.error("Failed to persist blueprint for user %s: %s", user_id, e)
        return False


# ─── Routes ──────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = BASE_DIR / "static" / "index.html"
    if not index_path.exists():
        raise HTTPException(500, "Page not found")
    return index_path.read_text()


@app.post("/api/start")
async def start_session(req: StartRequest, request: Request):
    enforce_rate_limit(request)

    # Require auth — user must be signed in
    user = None
    if is_firebase_available():
        from auth import get_current_user as _get_current_user
        try:
            user = await _get_current_user(request)
        except HTTPException:
            raise HTTPException(401, "Authentication required. Please sign in.")

    # Cleanup expired sessions before checking limits
    cleanup_expired_sessions()

    if len(sessions) >= MAX_SESSIONS:
        raise HTTPException(503, "Service is busy. Please try again later.")

    sid = secrets.token_hex(SESSION_ID_LENGTH // 2)  # Cryptographically random
    sess_data = {
        "business_description": req.business_description,
        "answers": {},
        "current_step": 0,
        "current_stage": 1,
        "status": "intake",
        "research": {},
        "stage2_questions": [],
        "master_context": "",
        "generated_files": [],
        "created_at": time.time(),
        "user_id": user.uid if user else None,
    }
    save_session(sid, sess_data, sessions)
    q = get_question_for_step(0, sessions[sid])
    stage_info = STAGES[1]
    return {
        "session_id": sid,
        "question": q,
        "step": 0,
        "total_steps": get_total_questions(),
        "stage": 1,
        "stage_name": stage_info["name"],
        "stage_description": stage_info["description"],
    }


@app.post("/api/answer")
async def answer_question(req: AnswerRequest, request: Request):
    enforce_rate_limit(request)

    sess = get_session(req.session_id, sessions)
    if not sess:
        raise HTTPException(404, "Session not found. It may have expired or the server was restarted. Please start a new blueprint.")

    # Prevent concurrent modification while researching/generating
    if sess["status"] in ("researching", "generating", "compiling"):
        raise HTTPException(409, "Session is busy. Please wait.")

    step = sess["current_step"]
    q = get_question_for_step(step, sess)
    if not q or "key" not in q:
        raise HTTPException(400, "Invalid question step")
    sess["answers"][q["key"]] = req.answer
    sess["current_step"] += 1
    next_step = sess["current_step"]
    total = get_total_questions()

    current_stage = get_stage_for_step(step)
    next_stage = get_stage_for_step(next_step) if next_step < total else None

    # -- Stage transition: trigger research --
    if next_stage and next_stage != current_stage:
        if current_stage == 1 and next_stage == 2:
            # Stage 1 complete -> Run industry research
            sess["status"] = "researching"
            stage1 = compile_stage_answers(sess, 1)

            try:
                research = await research_industry(
                    industry=stage1.get("industry_description", ""),
                    services=stage1.get("industry_description", ""),
                    company=stage1.get("company_name", ""),
                )
                sess["research"]["stage1"] = research

                # Generate Stage 2 questions based on research
                stage2_qs = generate_stage2_questions(research)
                sess["stage2_questions"] = stage2_qs

                sess["status"] = "intake"
                sess["current_stage"] = 2

                update_session(req.session_id, sess)
                q = get_question_for_step(next_step, sess)
                stage_info = STAGES[2]
                return {
                    "done": False,
                    "question": q,
                    "step": next_step,
                    "total_steps": total,
                    "stage": 2,
                    "stage_name": stage_info["name"],
                    "stage_description": stage_info["description"],
                    "research_complete": True,
                    "research_summary": {
                        "industry_overview": research.get("industry_overview", ""),
                        "departments_found": research.get("typical_departments", []),
                        "stages_found": research.get("typical_process_stages", []),
                        "terminology": research.get("industry_terminology", [])[:5],
                    },
                }
            except Exception as e:
                # Research failed -- continue with default questions (sanitize error)
                sess["status"] = "intake"
                sess["current_stage"] = 2
                sess["stage2_questions"] = [
                    {"key": "departments_confirm", "question": "What departments does your business have?", "placeholder": "e.g., Sales, Operations, Finance..."},
                    {"key": "customer_journey", "question": "Walk through your process from first customer contact to job completion.", "placeholder": ""},
                    {"key": "key_challenges", "question": "What are your biggest operational challenges?", "placeholder": ""},
                ]
                update_session(req.session_id, sess)
                q = get_question_for_step(next_step, sess)
                return {
                    "done": False,
                    "question": q,
                    "step": next_step,
                    "total_steps": total,
                    "stage": 2,
                    "stage_name": "Your Operations",
                    "stage_description": "Research encountered an issue, but let's continue.",
                    "research_complete": False,
                }

        elif current_stage == 2 and next_stage == 3:
            # Stage 2 complete -> Run compliance/KPI research
            sess["status"] = "researching"
            stage1 = compile_stage_answers(sess, 1)
            stage2 = compile_stage_answers(sess, 2)

            # Parse departments from user's response
            dept_text = stage2.get("departments_confirm", "")
            departments = [d.strip() for d in dept_text.replace(",", "\n").split("\n") if d.strip() and len(d.strip()) > 1]
            if not departments:
                departments = sess.get("research", {}).get("stage1", {}).get("typical_departments", ["Operations", "Sales", "Finance"])

            try:
                research = await research_compliance_and_kpis(
                    industry=stage1.get("industry_description", ""),
                    services=stage1.get("industry_description", ""),
                    departments=departments,
                    region="US",
                )
                sess["research"]["stage2"] = research
            except Exception:
                sess["research"]["stage2"] = {"error": "Research unavailable"}

            sess["status"] = "intake"
            sess["current_stage"] = 3
            update_session(req.session_id, sess)
            q = get_question_for_step(next_step, sess)
            stage_info = STAGES[3]
            return {
                "done": False,
                "question": q,
                "step": next_step,
                "total_steps": total,
                "stage": 3,
                "stage_name": stage_info["name"],
                "stage_description": stage_info["description"],
                "research_complete": True,
            }

    # -- All questions done --
    if next_step >= total:
        sess["status"] = "compiling"

        # Compile master context from all research + answers
        stage1 = compile_stage_answers(sess, 1)
        stage2 = compile_stage_answers(sess, 2)
        stage3 = compile_stage_answers(sess, 3)
        r1 = sess.get("research", {}).get("stage1", {})
        r2 = sess.get("research", {}).get("stage2", {})

        try:
            master_context = await compile_master_context(stage1, r1, stage2, r2, stage3)
            sess["master_context"] = master_context
            sess["status"] = "ready"
        except Exception:
            sess["status"] = "ready"
            # Build a minimal context so generation can still proceed
            sess["master_context"] = f"Company: {stage1.get('company_name', 'Unknown')}\nIndustry: {stage1.get('industry_description', 'Unknown')}"

        update_session(req.session_id, sess)

        # Build profile for display
        departments = r1.get("typical_departments", [])
        stages = r1.get("typical_process_stages", [])
        company = stage1.get("company_name", "Company")
        industry = stage1.get("industry_description", "")

        return {
            "done": True,
            "profile_summary": f"{company} — {industry[:80]}",
            "departments": departments,
            "stages": stages,
            "research_findings": {
                "compliance_items": len(r2.get("compliance_requirements", [])),
                "kpis_found": len(r2.get("industry_kpis", [])),
                "documents_found": len(r2.get("document_templates", [])),
                "safety_standards": len(r2.get("safety_standards", [])),
            },
        }

    # -- Normal next question (within same stage) --
    update_session(req.session_id, sess)
    q = get_question_for_step(next_step, sess)
    stage = get_stage_for_step(next_step)
    stage_info = STAGES[stage]
    return {
        "done": False,
        "question": q,
        "step": next_step,
        "total_steps": total,
        "stage": stage,
        "stage_name": stage_info["name"],
        "stage_description": stage_info["description"],
    }


async def _run_generation(session_id: str, sess: dict):
    """Run blueprint generation in background, updating progress in session."""
    try:
        def progress_callback(step: int, total: int, message: str):
            sess["generate_progress"] = {"step": step, "total_steps": total, "message": message}

        files, raw_results = await generate_blueprint_kit(sess["master_context"], sess.get("research", {}), progress_cb=progress_callback)
        sess["generated_files"] = files
        sess["raw_results"] = raw_results
        sess["status"] = "generated"
        sess["generate_progress"] = {"step": 4, "total_steps": 4, "message": "Done!"}
        update_session(session_id, sess)

        # Persist to Firebase
        user_id = sess.get("user_id")
        if user_id and is_firebase_available():
            persist_ok = _persist_blueprint_to_firebase(user_id, sess)
            if not persist_ok:
                sess["persist_warning"] = True
    except Exception as e:
        logger.error("Generation failed for session %s: %s", session_id, e)
        sess["status"] = "ready"  # Allow retry
        sess["generate_error"] = safe_error_message(e)
        sess["generate_progress"] = None
        update_session(session_id, sess)


@app.post("/api/generate")
async def generate_blueprint(req: GenerateRequest, request: Request):
    enforce_rate_limit(request)

    ip = get_client_ip(request)
    if not rate_limiter.check_generate_limit(ip):
        raise HTTPException(429, "Generation rate limit reached. Please try again later.")

    sess = get_session(req.session_id, sessions)
    if not sess:
        raise HTTPException(404, "Session not found. It may have expired or the server was restarted. Please start a new blueprint.")
    if sess["status"] == "generating":
        raise HTTPException(409, "Generation already in progress. Please wait.")
    if sess["status"] not in ("ready", "generated"):
        raise HTTPException(400, "Complete the questionnaire first.")

    sess["status"] = "generating"
    sess["generate_progress"] = {"step": 0, "total_steps": 4, "message": "Starting generation..."}

    # Launch generation in background
    asyncio.create_task(_run_generation(req.session_id, sess))

    return {"status": "started", "session_id": req.session_id}


def _recover_files_from_storage(sess: dict) -> list[dict]:
    """Recover generated files from Cloud Storage when not in memory.

    After a server restart, generated_files is empty (excluded from Firestore
    persistence). But if the blueprint was persisted to Cloud Storage, we can
    download the files back.
    """
    if sess.get("generated_files"):
        return sess["generated_files"]

    blueprint_id = sess.get("blueprint_id")
    user_id = sess.get("user_id")
    if not blueprint_id or not user_id:
        return []

    try:
        from storage import download_file
        from db import get_blueprint

        bp = get_blueprint(blueprint_id)
        if not bp or not bp.get("files"):
            return []

        recovered = []
        for f in bp["files"]:
            content = download_file(f["storage_path"])
            if content is not None:
                recovered.append({
                    "name": f["name"],
                    "content": content.decode("utf-8"),
                })
        if recovered:
            sess["generated_files"] = recovered
            logger.info("Recovered %d files from Cloud Storage for blueprint %s", len(recovered), blueprint_id)
        return recovered
    except Exception as e:
        logger.error("Failed to recover files from storage: %s", e)
        return []


@app.get("/api/download/{session_id}")
async def download_kit(session_id: str, request: Request):
    enforce_rate_limit(request)

    # Validate session_id format
    if not session_id or len(session_id) > 48 or not all(c in "0123456789abcdef" for c in session_id):
        raise HTTPException(400, "Invalid session ID")

    sess = get_session(session_id, sessions)
    if not sess or sess["status"] != "generated":
        raise HTTPException(404, "No generated files")

    files = _recover_files_from_storage(sess)
    if not files:
        raise HTTPException(404, "Generated files are no longer available. Check your dashboard for saved blueprints.")

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.writestr(f["name"], f["content"])
    buf.seek(0)

    company = sess["answers"].get("company_name", "blueprint") or "blueprint"
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in company).strip().replace(" ", "-")
    if not safe_name:
        safe_name = "blueprint"

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}-service-blueprint.zip"'},
    )


@app.get("/api/preview/{session_id}/{filename:path}")
async def preview_file(session_id: str, filename: str, request: Request):
    enforce_rate_limit(request)

    # Validate session_id format
    if not session_id or len(session_id) > 48 or not all(c in "0123456789abcdef" for c in session_id):
        raise HTTPException(400, "Invalid session ID")

    sess = get_session(session_id, sessions)
    if not sess or sess["status"] != "generated":
        raise HTTPException(404, "No generated files")

    # Sanitize filename -- only allow basename (no path traversal)
    safe_filename = os.path.basename(filename)
    if not safe_filename or safe_filename != filename:
        raise HTTPException(400, "Invalid filename")

    files = _recover_files_from_storage(sess)
    for f in files:
        if f["name"] == safe_filename:
            return HTMLResponse(f["content"])
    raise HTTPException(404, "File not found")


@app.get("/api/status/{session_id}")
async def session_status(session_id: str, request: Request):
    enforce_rate_limit(request)

    # Validate session_id format
    if not session_id or len(session_id) > 48 or not all(c in "0123456789abcdef" for c in session_id):
        raise HTTPException(400, "Invalid session ID")

    sess = get_session(session_id, sessions)
    if not sess:
        raise HTTPException(404, "Session not found. It may have expired or the server was restarted. Please start a new blueprint.")
    return {"status": sess["status"]}


@app.get("/api/generate/status/{session_id}")
async def generate_status(session_id: str, request: Request):
    enforce_rate_limit(request)

    if not session_id or len(session_id) > 48 or not all(c in "0123456789abcdef" for c in session_id):
        raise HTTPException(400, "Invalid session ID")

    sess = get_session(session_id, sessions)
    if not sess:
        raise HTTPException(404, "Session not found")

    progress = sess.get("generate_progress")

    if sess["status"] == "generated":
        files = _recover_files_from_storage(sess)
        response = {
            "status": "done",
            "file_count": len(files),
            "files": [f["name"] for f in files],
            "blueprint_id": sess.get("blueprint_id"),
        }
        if sess.get("persist_warning"):
            response["persist_warning"] = True
        return response
    elif sess["status"] == "generating":
        return {
            "status": "generating",
            "step": progress["step"] if progress else 0,
            "total_steps": progress["total_steps"] if progress else 4,
            "message": progress["message"] if progress else "Working...",
        }
    elif sess.get("generate_error"):
        error = sess.pop("generate_error")
        return {"status": "error", "detail": error}
    else:
        return {"status": sess["status"]}


# ─── Auth & User Endpoints ───────────────────────────────────────────

@app.post("/api/auth/sync")
async def auth_sync(request: Request):
    """Called after Firebase client-side login. Verifies token, upserts user."""
    enforce_rate_limit(request)

    if not is_firebase_available():
        raise HTTPException(503, "Authentication service unavailable")

    from auth import verify_firebase_token
    from db import create_or_update_user

    user = verify_firebase_token(request)
    profile = create_or_update_user(user.uid, user.email, user.name, user.picture)
    return {"status": "ok", "user": profile}


@app.get("/api/user/profile")
async def get_user_profile(request: Request):
    """Get current user's profile and stats."""
    enforce_rate_limit(request)

    if not is_firebase_available():
        raise HTTPException(503, "Authentication service unavailable")

    from auth import get_current_user as _get_current_user
    from db import get_user

    user = await _get_current_user(request)
    profile = get_user(user.uid)
    if not profile:
        raise HTTPException(404, "User profile not found. Please log in again.")
    return profile


@app.get("/api/user/blueprints")
async def list_user_blueprints_endpoint(request: Request, folder_id: Optional[str] = None):
    """List blueprints for the authenticated user."""
    enforce_rate_limit(request)

    if not is_firebase_available():
        raise HTTPException(503, "Authentication service unavailable")

    from auth import get_current_user as _get_current_user
    from db import list_user_blueprints

    user = await _get_current_user(request)
    try:
        blueprints = list_user_blueprints(user.uid, folder_id=folder_id)
        return {"blueprints": blueprints}
    except Exception as e:
        logger.error("Failed to list blueprints: %s", e)
        raise HTTPException(500, "Failed to load blueprints")


@app.get("/api/user/blueprints/{blueprint_id}/files")
async def list_blueprint_files(blueprint_id: str, request: Request):
    """List files in a blueprint."""
    enforce_rate_limit(request)

    if not is_firebase_available():
        raise HTTPException(503, "Authentication service unavailable")

    from auth import get_current_user as _get_current_user
    from db import get_blueprint

    user = await _get_current_user(request)
    bp = get_blueprint(blueprint_id)
    if not bp or bp.get("user_id") != user.uid:
        raise HTTPException(404, "Blueprint not found")

    return {"files": bp.get("files", [])}


@app.get("/api/user/blueprints/{blueprint_id}/preview/{filename:path}")
async def preview_blueprint_file(blueprint_id: str, filename: str, request: Request):
    """Preview a file from a saved blueprint via Cloud Storage."""
    enforce_rate_limit(request)

    if not is_firebase_available():
        raise HTTPException(503, "Authentication service unavailable")

    from auth import get_current_user as _get_current_user
    from db import get_blueprint
    from storage import download_file

    user = await _get_current_user(request)
    bp = get_blueprint(blueprint_id)
    if not bp or bp.get("user_id") != user.uid:
        raise HTTPException(404, "Blueprint not found")

    # Sanitize filename
    safe_filename = os.path.basename(filename)
    if not safe_filename or safe_filename != filename:
        raise HTTPException(400, "Invalid filename")

    # Find the file in blueprint's file list
    target_file = None
    for f in bp.get("files", []):
        if f.get("name") == safe_filename:
            target_file = f
            break

    if not target_file:
        raise HTTPException(404, "File not found")

    try:
        content = download_file(target_file["storage_path"])
        if content is None:
            raise HTTPException(404, "File not found in storage")
        return HTMLResponse(content.decode("utf-8"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to preview file: %s", e)
        raise HTTPException(500, "Failed to load file preview")


@app.put("/api/user/blueprints/{blueprint_id}")
async def update_blueprint_endpoint(blueprint_id: str, req: UpdateBlueprintRequest, request: Request):
    """Update blueprint metadata (rename, move to folder, toggle sharing)."""
    enforce_rate_limit(request)

    if not is_firebase_available():
        raise HTTPException(503, "Authentication service unavailable")

    from auth import get_current_user as _get_current_user
    from db import get_blueprint, update_blueprint, generate_share_token

    user = await _get_current_user(request)
    bp = get_blueprint(blueprint_id)
    if not bp or bp.get("user_id") != user.uid:
        raise HTTPException(404, "Blueprint not found")

    update_data = {}
    if req.title is not None:
        update_data["title"] = req.title.strip()[:200]
    if req.folder_id is not None:
        update_data["folder_id"] = req.folder_id if req.folder_id else None
    if req.is_shared is not None:
        update_data["is_shared"] = req.is_shared
        if req.is_shared and not bp.get("share_token"):
            update_data["share_token"] = generate_share_token()
        elif not req.is_shared:
            update_data["share_token"] = None

    if not update_data:
        raise HTTPException(400, "No fields to update")

    try:
        update_blueprint(blueprint_id, update_data)
        updated = get_blueprint(blueprint_id)
        return updated
    except Exception as e:
        logger.error("Failed to update blueprint: %s", e)
        raise HTTPException(500, "Failed to update blueprint")


@app.delete("/api/user/blueprints/{blueprint_id}")
async def delete_blueprint_endpoint(blueprint_id: str, request: Request):
    """Delete a blueprint and its storage files."""
    enforce_rate_limit(request)

    if not is_firebase_available():
        raise HTTPException(503, "Authentication service unavailable")

    from auth import get_current_user as _get_current_user
    from db import get_blueprint, delete_blueprint, get_user, update_user
    from storage import delete_blueprint_files

    user = await _get_current_user(request)
    bp = get_blueprint(blueprint_id)
    if not bp or bp.get("user_id") != user.uid:
        raise HTTPException(404, "Blueprint not found")

    try:
        # Calculate storage to reclaim
        total_bytes = sum(f.get("size_bytes", 0) for f in bp.get("files", []))

        # Delete storage files
        delete_blueprint_files(user.uid, blueprint_id)

        # Delete Firestore document
        delete_blueprint(blueprint_id)

        # Update user stats
        profile = get_user(user.uid)
        if profile:
            new_count = max(0, (profile.get("blueprint_count", 0) or 0) - 1)
            new_bytes = max(0, (profile.get("storage_used_bytes", 0) or 0) - total_bytes)
            update_user(user.uid, {
                "blueprint_count": new_count,
                "storage_used_bytes": new_bytes,
            })

        return {"status": "deleted"}
    except Exception as e:
        logger.error("Failed to delete blueprint: %s", e)
        raise HTTPException(500, "Failed to delete blueprint")


@app.get("/api/shared/{share_token}")
async def view_shared_blueprint(share_token: str, request: Request):
    """Public endpoint to view a shared blueprint (no auth required)."""
    enforce_rate_limit(request)

    if not is_firebase_available():
        raise HTTPException(503, "Service unavailable")

    from db import get_shared_blueprint

    if not share_token or len(share_token) > 64:
        raise HTTPException(400, "Invalid share token")

    bp = get_shared_blueprint(share_token)
    if not bp:
        raise HTTPException(404, "Shared blueprint not found")

    # Return safe subset (no internal IDs, no storage paths)
    return {
        "title": bp.get("title", ""),
        "business_description": bp.get("business_description", ""),
        "status": bp.get("status", ""),
        "file_count": bp.get("file_count", 0),
        "files": [{"name": f.get("name", "")} for f in bp.get("files", [])],
        "created_at": bp.get("created_at"),
    }


# ─── Folder Endpoints ───────────────────────────────────────────────

@app.get("/api/user/folders")
async def list_folders_endpoint(request: Request):
    """List folders for the authenticated user."""
    enforce_rate_limit(request)

    if not is_firebase_available():
        raise HTTPException(503, "Authentication service unavailable")

    from auth import get_current_user as _get_current_user
    from db import list_folders

    user = await _get_current_user(request)
    try:
        folders = list_folders(user.uid)
        return {"folders": folders}
    except Exception as e:
        logger.error("Failed to list folders: %s", e)
        raise HTTPException(500, "Failed to load folders")


@app.post("/api/user/folders")
async def create_folder_endpoint(req: CreateFolderRequest, request: Request):
    """Create a new folder."""
    enforce_rate_limit(request)

    if not is_firebase_available():
        raise HTTPException(503, "Authentication service unavailable")

    from auth import get_current_user as _get_current_user
    from db import create_folder

    user = await _get_current_user(request)
    try:
        folder_id = create_folder(user.uid, req.name, req.color)
        return {"id": folder_id, "name": req.name, "color": req.color}
    except Exception as e:
        logger.error("Failed to create folder: %s", e)
        raise HTTPException(500, "Failed to create folder")


@app.put("/api/user/folders/{folder_id}")
async def update_folder_endpoint(folder_id: str, req: UpdateFolderRequest, request: Request):
    """Update a folder's name or color."""
    enforce_rate_limit(request)

    if not is_firebase_available():
        raise HTTPException(503, "Authentication service unavailable")

    from auth import get_current_user as _get_current_user
    from db import get_folder, update_folder

    user = await _get_current_user(request)
    folder = get_folder(folder_id)
    if not folder or folder.get("user_id") != user.uid:
        raise HTTPException(404, "Folder not found")

    update_data = {}
    if req.name is not None:
        update_data["name"] = req.name.strip()[:100]
    if req.color is not None:
        update_data["color"] = req.color.strip()

    if not update_data:
        raise HTTPException(400, "No fields to update")

    try:
        update_folder(folder_id, update_data)
        return {"status": "updated"}
    except Exception as e:
        logger.error("Failed to update folder: %s", e)
        raise HTTPException(500, "Failed to update folder")


@app.delete("/api/user/folders/{folder_id}")
async def delete_folder_endpoint(folder_id: str, request: Request):
    """Delete a folder (moves its blueprints to root)."""
    enforce_rate_limit(request)

    if not is_firebase_available():
        raise HTTPException(503, "Authentication service unavailable")

    from auth import get_current_user as _get_current_user
    from db import get_folder, delete_folder

    user = await _get_current_user(request)
    folder = get_folder(folder_id)
    if not folder or folder.get("user_id") != user.uid:
        raise HTTPException(404, "Folder not found")

    try:
        delete_folder(folder_id)
        return {"status": "deleted"}
    except Exception as e:
        logger.error("Failed to delete folder: %s", e)
        raise HTTPException(500, "Failed to delete folder")


# ─── Section API Endpoints ──────────────────────────────────────────


@app.get("/api/blueprints/{blueprint_id}/sections")
async def list_blueprint_sections(blueprint_id: str, request: Request):
    """List sections for a blueprint (titles, IDs, positions only)."""
    enforce_rate_limit(request)
    from auth import get_current_user
    from db import get_blueprint, list_sections

    user = await get_current_user(request)
    bp = get_blueprint(blueprint_id)
    if not bp or (bp.get("user_id") != user.uid and not bp.get("is_shared")):
        raise HTTPException(404, "Blueprint not found")
    if bp.get("format") != "blocks":
        raise HTTPException(400, "Legacy blueprint — sections not available")

    sections = list_sections(blueprint_id)
    return [{"id": s["id"], "title": s["title"], "icon": s.get("icon", ""),
             "position": s.get("position", 0), "block_count": len(s.get("blocks", []))} for s in sections]


@app.get("/api/blueprints/{blueprint_id}/sections/{section_id}")
async def get_blueprint_section(blueprint_id: str, section_id: str, request: Request):
    """Get a full section with all blocks."""
    enforce_rate_limit(request)
    from auth import get_current_user
    from db import get_blueprint, get_section, update_section, update_blueprint
    from block_renderer import render_block, CURRENT_RENDERER_VERSION

    user = await get_current_user(request)
    bp = get_blueprint(blueprint_id)
    if not bp or (bp.get("user_id") != user.uid and not bp.get("is_shared")):
        raise HTTPException(404, "Blueprint not found")

    section = get_section(blueprint_id, section_id)
    if not section:
        raise HTTPException(404, "Section not found")

    # Regenerate html_cache if renderer version is newer
    bp_version = bp.get("renderer_version", 0)
    if bp_version < CURRENT_RENDERER_VERSION:
        for block in section.get("blocks", []):
            block["html_cache"] = render_block(block)
        update_section(blueprint_id, section_id, {"blocks": section["blocks"]})
        update_blueprint(blueprint_id, {"renderer_version": CURRENT_RENDERER_VERSION})

    return section


@app.put("/api/blueprints/{blueprint_id}/sections/{section_id}")
async def update_blueprint_section(blueprint_id: str, section_id: str, request: Request):
    """Update a section's blocks."""
    enforce_rate_limit(request)
    from auth import get_current_user
    from db import get_blueprint, update_section
    from block_renderer import render_block
    from block_types import validate_block

    user = await get_current_user(request)
    bp = get_blueprint(blueprint_id)
    if not bp or bp.get("user_id") != user.uid:
        raise HTTPException(404, "Blueprint not found")

    body = await request.json()
    blocks = body.get("blocks")
    if blocks is None:
        raise HTTPException(400, "blocks field required")

    # Validate and re-render
    for block in blocks:
        if not validate_block(block):
            raise HTTPException(400, f"Invalid block: {block.get('id', 'unknown')}")
        block["html_cache"] = render_block(block)

    update_section(blueprint_id, section_id, {"blocks": blocks})
    return {"status": "ok"}


@app.post("/api/blueprints/{blueprint_id}/chat")
async def chat_edit_blueprint(blueprint_id: str, request: Request):
    """Chat-based editing: user sends message, LLM modifies blocks."""
    enforce_rate_limit(request)
    from auth import get_current_user
    from db import get_blueprint, list_sections, get_section, update_section, update_blueprint
    from block_renderer import render_block
    from chat_editor import build_edit_prompt, call_edit_llm, parse_edit_response, apply_changes_to_blocks

    user = await get_current_user(request)
    bp = get_blueprint(blueprint_id)
    if not bp or bp.get("user_id") != user.uid:
        raise HTTPException(404, "Blueprint not found")
    if bp.get("format") != "blocks":
        raise HTTPException(400, "Chat editing not available for legacy blueprints")

    body = await request.json()
    message = body.get("message", "").strip()
    current_section_id = body.get("section_id")  # which section user is viewing
    if not message:
        raise HTTPException(400, "message is required")

    # Get all sections for context
    all_sections = list_sections(blueprint_id)
    section_summaries = [{"id": s["id"], "title": s["title"]} for s in all_sections]

    # Get current section blocks
    current_blocks = []
    if current_section_id:
        section = get_section(blueprint_id, current_section_id)
        if section:
            current_blocks = section.get("blocks", [])

    # Load chat history from Firestore
    chat_history = _get_chat_history(blueprint_id)

    # Build prompt and call LLM
    prompt = build_edit_prompt(section_summaries, current_blocks, current_section_id or "", chat_history, message)

    try:
        raw_response = await call_edit_llm(prompt)
    except Exception as e:
        logger.error("Chat LLM call failed for blueprint %s: %s", blueprint_id, e)
        raise HTTPException(502, "AI editing service temporarily unavailable. Please try again.")

    parsed = parse_edit_response(raw_response)
    if not parsed:
        # LLM returned something unparseable — return the raw text as a conversational response
        _save_chat_messages(blueprint_id, message, raw_response, [])
        return {"response": raw_response, "sections": []}

    # Apply changes to each affected section
    result_sections = []
    all_undo_entries = []

    for section_change in parsed.get("sections", []):
        sid = section_change.get("section_id")
        changes = section_change.get("changes", [])
        if not sid or not changes:
            continue

        section_doc = get_section(blueprint_id, sid)
        if not section_doc:
            continue

        blocks = section_doc.get("blocks", [])
        updated_blocks, undo_entries = apply_changes_to_blocks(blocks, changes)

        # Re-render html_cache for changed blocks
        changed_ids = {c["block_id"] for c in changes}
        for block in updated_blocks:
            if block["id"] in changed_ids or not block.get("html_cache"):
                block["html_cache"] = render_block(block)

        # Save to Firestore
        update_section(blueprint_id, sid, {"blocks": updated_blocks})

        result_sections.append({"section_id": sid, "changes": changes})
        all_undo_entries.extend([{**u, "section_id": sid} for u in undo_entries])

    # Save chat history
    _save_chat_messages(blueprint_id, message, parsed.get("response", ""), all_undo_entries)

    return {
        "response": parsed.get("response", "Changes applied."),
        "sections": result_sections,
    }


def _get_chat_history(blueprint_id: str, limit: int = 10) -> list[dict]:
    """Get recent chat messages for a blueprint."""
    try:
        from firebase_config import get_firestore_client
        db = get_firestore_client()
        docs = (db.collection("blueprints").document(blueprint_id)
                .collection("chat_history")
                .order_by("created_at", direction="DESCENDING")
                .limit(limit * 2)  # Get both user and assistant messages
                .stream())
        messages = []
        for doc in docs:
            data = doc.to_dict()
            messages.append({"role": data.get("role"), "content": data.get("content")})
        messages.reverse()  # Chronological order
        return messages[-limit * 2:]  # Last N exchanges
    except Exception:
        return []


def _save_chat_messages(blueprint_id: str, user_message: str, assistant_response: str,
                        undo_entries: list[dict]) -> None:
    """Save user and assistant messages to chat history."""
    try:
        from firebase_config import get_firestore_client
        from datetime import datetime, timezone
        db = get_firestore_client()
        col = db.collection("blueprints").document(blueprint_id).collection("chat_history")

        now = datetime.now(timezone.utc)
        col.add({"role": "user", "content": user_message, "changes_made": None, "created_at": now})
        col.add({
            "role": "assistant",
            "content": assistant_response,
            "changes_made": [{"section_id": u.get("section_id"), "block_id": u.get("block_id"),
                              "action": u.get("action"), "before": u.get("before"), "after": u.get("after")}
                             for u in undo_entries] if undo_entries else None,
            "created_at": now,
        })

        # Trim to 200 messages max
        all_docs = list(col.order_by("created_at").stream())
        if len(all_docs) > 200:
            for doc in all_docs[:len(all_docs) - 200]:
                doc.reference.delete()

    except Exception as e:
        logger.warning("Failed to save chat history for %s: %s", blueprint_id, e)


@app.put("/api/blueprints/{blueprint_id}/section-order")
async def update_blueprint_section_order(blueprint_id: str, request: Request):
    """Reorder sections."""
    enforce_rate_limit(request)
    from auth import get_current_user
    from db import get_blueprint, update_section_order, update_section

    user = await get_current_user(request)
    bp = get_blueprint(blueprint_id)
    if not bp or bp.get("user_id") != user.uid:
        raise HTTPException(404, "Blueprint not found")

    body = await request.json()
    section_order = body.get("section_order")
    if not isinstance(section_order, list):
        raise HTTPException(400, "section_order must be a list")

    update_section_order(blueprint_id, section_order)
    for i, sid in enumerate(section_order):
        update_section(blueprint_id, sid, {"position": i})
    return {"status": "ok"}


@app.get("/api/blueprints/{blueprint_id}/export/zip")
async def export_blueprint_zip(blueprint_id: str, request: Request):
    """Generate a ZIP file from block data on demand."""
    enforce_rate_limit(request)
    from auth import get_current_user
    from db import get_blueprint, list_sections
    from block_renderer import render_section_to_html

    user = await get_current_user(request)
    bp = get_blueprint(blueprint_id)
    if not bp or (bp.get("user_id") != user.uid and not bp.get("is_shared")):
        raise HTTPException(404, "Blueprint not found")
    if bp.get("format") != "blocks":
        raise HTTPException(400, "Use /api/download/{session_id} for legacy blueprints")

    sections = list_sections(blueprint_id)
    if not sections:
        raise HTTPException(404, "No sections found")

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for section in sections:
            html = render_section_to_html(section)
            # Sanitize filename
            safe_name = "".join(c for c in section["id"] if c.isalnum() or c in ("_", "-"))
            zf.writestr(f"{safe_name}.html", html)

    zip_buffer.seek(0)
    safe_title = "".join(c for c in bp.get("title", "blueprint") if c.isalnum() or c in ("_", "-", " ")).replace(" ", "_")
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}_blueprint.zip"'}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=True)
