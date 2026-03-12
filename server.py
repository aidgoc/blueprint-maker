"""Service Blueprint Maker — FastAPI Server
Staged architecture: 3 question stages with research between each."""
import asyncio
import json
import uuid
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from config import PORT
from questionnaire import (
    get_question_for_step, get_stage_for_step, get_total_questions,
    compile_stage_answers, generate_stage2_questions, STAGES,
)
from research import research_industry, research_compliance_and_kpis, compile_master_context
from generator import generate_blueprint_kit

app = FastAPI(title="Service Blueprint Maker")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

sessions: dict = {}
BASE_DIR = Path(__file__).parent


class StartRequest(BaseModel):
    business_description: str

class AnswerRequest(BaseModel):
    session_id: str
    answer: str

class GenerateRequest(BaseModel):
    session_id: str


@app.get("/", response_class=HTMLResponse)
async def index():
    return (BASE_DIR / "static" / "index.html").read_text()


@app.post("/api/start")
async def start_session(req: StartRequest):
    sid = uuid.uuid4().hex[:12]
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
async def answer_question(req: AnswerRequest):
    sess = sessions.get(req.session_id)
    if not sess:
        raise HTTPException(404, "Session not found")

    step = sess["current_step"]
    q = get_question_for_step(step, sess)
    sess["answers"][q["key"]] = req.answer
    sess["current_step"] += 1
    next_step = sess["current_step"]
    total = get_total_questions()

    current_stage = get_stage_for_step(step)
    next_stage = get_stage_for_step(next_step) if next_step < total else None

    # ── Stage transition: trigger research ──
    if next_stage and next_stage != current_stage:
        if current_stage == 1 and next_stage == 2:
            # Stage 1 complete → Run industry research
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
                # Research failed — continue with default questions
                sess["status"] = "intake"
                sess["current_stage"] = 2
                from questionnaire import STAGES as S
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
                    "stage_description": f"Research encountered an issue, but let's continue. ({e})",
                    "research_complete": False,
                }

        elif current_stage == 2 and next_stage == 3:
            # Stage 2 complete → Run compliance/KPI research
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
                    region="US",  # default, could ask
                )
                sess["research"]["stage2"] = research
            except Exception as e:
                sess["research"]["stage2"] = {"error": str(e)}

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

    # ── All questions done ──
    if next_step >= total:
        sess["status"] = "compiling"

        # Compile master context from all research + answers
        stage1 = compile_stage_answers(sess, 1)
        stage2 = compile_stage_answers(sess, 2)
        stage3 = compile_stage_answers(sess, 3)
        r1 = sess.get("research", {}).get("stage1", {})
        r2 = sess.get("research", {}).get("stage2", {})

        master_context = await compile_master_context(stage1, r1, stage2, r2, stage3)
        sess["master_context"] = master_context
        sess["status"] = "ready"

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

    # ── Normal next question (within same stage) ──
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
async def generate_blueprint(req: GenerateRequest):
    sess = sessions.get(req.session_id)
    if not sess:
        raise HTTPException(404, "Session not found")
    if sess["status"] not in ("ready", "generated"):
        raise HTTPException(400, "Complete the questionnaire first")

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
        raise HTTPException(500, f"Generation failed: {str(e)}")


@app.get("/api/download/{session_id}")
async def download_kit(session_id: str):
    sess = sessions.get(session_id)
    if not sess or sess["status"] != "generated":
        raise HTTPException(404, "No generated files")

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sess["generated_files"]:
            zf.writestr(f["name"], f["content"])
    buf.seek(0)

    company = sess["answers"].get("company_name", "blueprint")
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in company).strip().replace(" ", "-")

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}-service-blueprint.zip"'},
    )


@app.get("/api/preview/{session_id}/{filename}")
async def preview_file(session_id: str, filename: str):
    sess = sessions.get(session_id)
    if not sess or sess["status"] != "generated":
        raise HTTPException(404, "No generated files")

    for f in sess["generated_files"]:
        if f["name"] == filename:
            return HTMLResponse(f["content"])
    raise HTTPException(404, "File not found")


@app.get("/api/status/{session_id}")
async def session_status(session_id: str):
    sess = sessions.get(session_id)
    if not sess:
        raise HTTPException(404, "Session not found")
    return {"status": sess["status"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=True)
