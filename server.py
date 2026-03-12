"""Service Blueprint Maker — FastAPI Server
Staged architecture: 3 question stages with research between each.

Security hardening applied:
- Rate limiting (in-memory, per-IP)
- Input size validation
- Session cleanup (TTL-based)
- Error message sanitization
- CORS restriction
- Session ID entropy increase
"""
import asyncio
import json
import os
import secrets
import time
import uuid
import zipfile
from collections import defaultdict
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, field_validator

from config import PORT
from questionnaire import (
    get_question_for_step, get_stage_for_step, get_total_questions,
    compile_stage_answers, generate_stage2_questions, STAGES,
)
from research import research_industry, research_compliance_and_kpis, compile_master_context
from generator import generate_blueprint_kit

app = FastAPI(title="Service Blueprint Maker", docs_url=None, redoc_url=None)

# --- CORS: restrict to same-origin in production ---
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
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
    """Remove sessions older than TTL."""
    now = time.time()
    expired = [
        sid for sid, sess in sessions.items()
        if now - sess.get("created_at", 0) > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        del sessions[sid]


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

    # Cleanup expired sessions before checking limits
    cleanup_expired_sessions()

    if len(sessions) >= MAX_SESSIONS:
        raise HTTPException(503, "Service is busy. Please try again later.")

    sid = secrets.token_hex(SESSION_ID_LENGTH // 2)  # Cryptographically random
    sessions[sid] = {
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
    }
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

    sess = sessions.get(req.session_id)
    if not sess:
        raise HTTPException(404, "Session not found")

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


@app.post("/api/generate")
async def generate_blueprint(req: GenerateRequest, request: Request):
    enforce_rate_limit(request)

    ip = get_client_ip(request)
    if not rate_limiter.check_generate_limit(ip):
        raise HTTPException(429, "Generation rate limit reached. Please try again later.")

    sess = sessions.get(req.session_id)
    if not sess:
        raise HTTPException(404, "Session not found")
    if sess["status"] == "generating":
        raise HTTPException(409, "Generation already in progress. Please wait.")
    if sess["status"] not in ("ready", "generated"):
        raise HTTPException(400, "Complete the questionnaire first.")

    sess["status"] = "generating"

    try:
        files = await generate_blueprint_kit(sess["master_context"], sess.get("research", {}))
        sess["generated_files"] = files
        sess["status"] = "generated"
        return {
            "status": "done",
            "file_count": len(files),
            "files": [f["name"] for f in files],
        }
    except Exception as e:
        sess["status"] = "ready"
        raise HTTPException(500, f"Generation failed: {safe_error_message(e)}")


@app.get("/api/download/{session_id}")
async def download_kit(session_id: str, request: Request):
    enforce_rate_limit(request)

    # Validate session_id format
    if not session_id or len(session_id) > 48 or not all(c in "0123456789abcdef" for c in session_id):
        raise HTTPException(400, "Invalid session ID")

    sess = sessions.get(session_id)
    if not sess or sess["status"] != "generated":
        raise HTTPException(404, "No generated files")

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sess["generated_files"]:
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

    sess = sessions.get(session_id)
    if not sess or sess["status"] != "generated":
        raise HTTPException(404, "No generated files")

    # Sanitize filename -- only allow basename (no path traversal)
    import os
    safe_filename = os.path.basename(filename)
    if not safe_filename or safe_filename != filename:
        raise HTTPException(400, "Invalid filename")

    for f in sess["generated_files"]:
        if f["name"] == safe_filename:
            return HTMLResponse(f["content"])
    raise HTTPException(404, "File not found")


@app.get("/api/status/{session_id}")
async def session_status(session_id: str, request: Request):
    enforce_rate_limit(request)

    # Validate session_id format
    if not session_id or len(session_id) > 48 or not all(c in "0123456789abcdef" for c in session_id):
        raise HTTPException(400, "Invalid session ID")

    sess = sessions.get(session_id)
    if not sess:
        raise HTTPException(404, "Session not found")
    return {"status": sess["status"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=True)
