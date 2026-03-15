"""Blueprint Generation Engine — powered by research context.

Takes the master context (compiled from research + user answers)
and generates the complete blueprint kit.

Architecture:
  1 smart-model call → master blueprint (stages × roles matrix)
  N×2 model calls → department sub-blueprints (parallel, split into 2 calls each for depth)
"""
import json
import asyncio
import httpx

from config import OPENROUTER_API_KEY, PLANNER_MODEL, OUTLINE_MODEL, RENDERER_MODEL
from renderer import render_master_blueprint, render_department_blueprint, render_glossary


async def call_llm(system: str, prompt: str, model: str, max_tokens: int = 8000, _retry_count: int = 0) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    async with httpx.AsyncClient(timeout=600) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices")
        if not choices or not isinstance(choices, list):
            raise RuntimeError("LLM returned no choices")
        finish_reason = choices[0].get("finish_reason", "")
        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise RuntimeError("LLM returned empty content")

        # If the response was truncated due to max_tokens, retry with double the limit
        if finish_reason == "length":
            print(f"    WARNING: LLM output truncated at {max_tokens} tokens (finish_reason=length)")
            if _retry_count < 2 and max_tokens < 65000:
                new_limit = min(max_tokens * 2, 65000)
                print(f"    Retrying with max_tokens={new_limit}...")
                return await call_llm(system, prompt, model, max_tokens=new_limit, _retry_count=_retry_count + 1)
            else:
                print(f"    Max retries reached — using truncated output ({len(content)} chars)")

        return content


def extract_json(text: str) -> dict:
    import re

    if not isinstance(text, str):
        text = str(text)
    text = text.strip()

    # Extract from code fences
    if "```json" in text:
        parts = text.split("```json", 1)[1]
        if "```" in parts:
            text = parts.split("```", 1)[0].strip()
        else:
            # No closing fence — take everything after ```json
            text = parts.strip()
    elif "```" in text:
        parts = text.split("```", 1)[1]
        if "```" in parts:
            text = parts.split("```", 1)[0].strip()
        else:
            text = parts.strip()
        # If the extracted text starts with a language tag on its own line, skip it
        if text and not text[0] in '{[':
            first_nl = text.find('\n')
            if first_nl != -1:
                text = text[first_nl + 1:].strip()

    # First, try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # If text doesn't start with { or [, try to find JSON within prose text
    if text and text[0] not in '{[':
        first_brace = text.find('{')
        first_bracket = text.find('[')
        start = -1
        if first_brace != -1 and first_bracket != -1:
            start = min(first_brace, first_bracket)
        elif first_brace != -1:
            start = first_brace
        elif first_bracket != -1:
            start = first_bracket
        if start > 0:
            text = text[start:]
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass

    # Fix common LLM output typos in JSON
    cleaned = text
    # Fix "key":= "value" or "key":- "value" or "key":> "value" typos
    # (LLM sometimes inserts stray characters between colon and value)
    cleaned = re.sub(r'":\s*[=\-~>]+\s*', '": ', cleaned)
    # Remove LLM abbreviation artifacts ("..." used to skip content)
    cleaned = re.sub(r':\s*\.\.\.', ': null', cleaned)
    cleaned = re.sub(r',\s*\.\.\.[\s,]*', '', cleaned)
    cleaned = re.sub(r'\.\.\.\s*$', '', cleaned)
    if cleaned != text:
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            text = cleaned  # Use cleaned version for further repair

    # Repair strategy
    repaired = text

    # Strip trailing garbage characters that aren't valid JSON endings
    while repaired and repaired[-1] not in ']},"0123456789truefalsn':
        repaired = repaired[:-1]

    if not repaired:
        raise json.JSONDecodeError("Empty JSON after stripping", text, 0)

    # Attempt 1: Close unclosed structures
    def try_close_and_parse(s: str) -> dict | None:
        """Try to close unclosed strings, remove trailing commas, and balance brackets."""
        fixed = s
        # Close unclosed strings
        if fixed.count('"') % 2 == 1:
            fixed += '"'
        # Remove trailing commas (including whitespace before them)
        fixed = re.sub(r',\s*$', '', fixed)
        # Remove incomplete key-value pairs at end (trailing "key": with no value)
        fixed = re.sub(r',\s*"[^"]*"\s*:\s*$', '', fixed)
        # Balance brackets/braces
        fixed += ']' * max(0, fixed.count('[') - fixed.count(']'))
        fixed += '}' * max(0, fixed.count('{') - fixed.count('}'))
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            return None

    result = try_close_and_parse(repaired)
    if result is not None:
        return result

    # Attempt 2: Trim back to last complete item boundary, then close
    for trim_char in ['},', '],', '}', ']']:
        idx = repaired.rfind(trim_char)
        if idx > len(repaired) * 0.5:
            trimmed = repaired[:idx + len(trim_char)]
            result = try_close_and_parse(trimmed)
            if result is not None:
                return result

    # Attempt 3: Aggressive — find last valid closing brace/bracket
    last_close = max(repaired.rfind('}'), repaired.rfind(']'))
    if last_close > len(repaired) * 0.3:
        trimmed = repaired[:last_close + 1]
        result = try_close_and_parse(trimmed)
        if result is not None:
            return result

    # Attempt 4: Find the first { and last } and try that substring
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass

    # All attempts failed
    raise json.JSONDecodeError(
        f"Could not parse or repair JSON (length={len(text)})",
        text[:200], 0
    )


# ─── Master Blueprint Generation ─────────────────────────────────────

PLANNER_SYSTEM = """You are a world-class business process architect creating implementation-ready service blueprints.

You have been given REAL RESEARCH about this business's industry — actual compliance standards, actual KPI benchmarks, actual document templates. USE THIS RESEARCH. Do not make up generic content when specific data was provided.

RULES:
1. Use the SPECIFIC industry terminology, standards, and benchmarks from the research
2. Every matrix cell should have 3-6 items (activities, documents, approvals, critical gates, handovers)
3. Documents must have specific field lists based on industry standards
4. KPIs must use the actual benchmark values from the research
5. Compliance items must reference REAL regulations found in the research
6. Return ONLY valid JSON"""


async def generate_master_blueprint(context: str, research: dict) -> dict:
    """Generate master blueprint using research context.

    Uses THREE phases:
      1. Structure call: stages + roles (Grok)
      2. Executive summary: comprehensive business overview (Grok)
      3. Matrix call(s): fill the matrix in batches of roles (Grok)
    """

    r1 = research.get("stage1", {})
    r2 = research.get("stage2", {})

    research_summary = ""
    if r2.get("compliance_requirements"):
        research_summary += "COMPLIANCE: " + json.dumps(r2["compliance_requirements"], separators=(',',':')) + "\n"
    if r2.get("industry_kpis"):
        research_summary += "KPIs: " + json.dumps(r2["industry_kpis"], separators=(',',':')) + "\n"
    if r2.get("workflow_patterns"):
        research_summary += "WORKFLOWS: " + json.dumps(r2["workflow_patterns"], separators=(',',':')) + "\n"
    if r2.get("safety_standards"):
        research_summary += "SAFETY: " + json.dumps(r2["safety_standards"], separators=(',',':')) + "\n"

    # ── CALL 1: Structure (stages + roles) ──
    structure_prompt = f"""{context}

{research_summary}

Define the STRUCTURE for a master service blueprint. Output JSON:
{{
  "company_name": "...",
  "industry_tag": "short label",
  "stages": [{{"id": 1, "name": "Stage Name", "icon": "emoji"}}],
  "roles": [{{"id": "role_key", "name": "Role Name", "icon": "emoji"}}]
}}

CRITICAL RULES:
- stages: Use ALL the process stages from the user's customer journey. Do NOT merge or consolidate. If the user described 10-14 steps, create 10-14 stages.
- roles: Use ALL departments from the user's answers. Include a "client" role. Use snake_case for role IDs.
- Output ONLY JSON. No markdown."""

    # ── CALL 2: Executive Summary (comprehensive overview — the heart of the service blueprint) ──
    summary_prompt = f"""{context}

{research_summary}

INDUSTRY RESEARCH:
{json.dumps(r1, separators=(',',':')) if r1 else 'N/A'}

Generate a COMPREHENSIVE executive summary for this business's master service blueprint. This is the most important document in the entire blueprint kit — it must be thorough, specific, and actionable.

Output JSON:
{{
  "executive_summary": "A 4-5 paragraph executive overview of the business, its market position, operational model, and strategic direction. Reference specific industry standards, market dynamics, and competitive positioning. This should read like a management consulting deliverable.",
  "business_model": {{
    "value_proposition": "What unique value this business delivers",
    "revenue_streams": ["Stream 1 with specifics", "Stream 2"],
    "cost_drivers": ["Major cost driver 1", "Major cost driver 2"],
    "competitive_advantages": ["Advantage 1", "Advantage 2"]
  }},
  "critical_success_factors": [
    {{"factor": "Factor name", "description": "Why it matters and how to measure it", "risk_if_missing": "What happens if this fails"}}
  ],
  "process_overview": [
    {{"stage": "Stage Name", "description": "2-3 sentence description of what happens at this stage, who is involved, what the key deliverables are, and what can go wrong", "duration": "Typical duration", "key_documents": ["Doc 1", "Doc 2"], "critical_handoffs": ["From X to Y"], "risk_points": ["Risk 1"]}}
  ],
  "key_metrics_dashboard": [
    {{"metric": "Metric Name", "target": "Specific target", "current_benchmark": "Industry average", "measurement": "How to measure", "owner": "Who owns this"}}
  ],
  "organizational_overview": {{
    "total_headcount": "Number",
    "department_breakdown": [{{"department": "Name", "headcount": "N", "key_responsibility": "One-line summary"}}],
    "reporting_structure": "Description of org hierarchy",
    "key_dependencies": ["Dept A depends on Dept B for X"]
  }},
  "technology_stack": [
    {{"system": "Name", "purpose": "What it does", "users": "Who uses it", "gaps": "What's missing"}}
  ],
  "strategic_roadmap": [
    {{"timeframe": "0-6 months / 6-12 months / 1-2 years", "initiatives": ["Initiative 1", "Initiative 2"], "expected_impact": "What changes"}}
  ]
}}

REQUIREMENTS:
- executive_summary: 4-5 substantial paragraphs, consulting-grade language
- critical_success_factors: 6-8 factors
- process_overview: One entry per stage from the user's journey (10-14 entries)
- key_metrics_dashboard: 10-15 metrics across all departments
- department_breakdown: Every department with headcount
- strategic_roadmap: 3 timeframes with 3-4 initiatives each
- Be SPECIFIC to this business. No generic content.

Output ONLY JSON. No markdown."""

    # Run structure + summary in parallel (both use OUTLINE_MODEL / Grok)
    print("    Master: generating structure + executive summary (OUTLINE_MODEL)...")
    structure_result, summary_result = await asyncio.gather(
        call_llm(PLANNER_SYSTEM, structure_prompt, OUTLINE_MODEL, max_tokens=4000),
        call_llm(PLANNER_SYSTEM, summary_prompt, OUTLINE_MODEL, max_tokens=32000),
    )

    structure = extract_json(structure_result)

    # Parse executive summary
    try:
        summary_data = extract_json(summary_result)
        structure.update(summary_data)
        print(f"    Master: executive summary OK ({len(summary_result)} chars)")
    except (json.JSONDecodeError, Exception) as e:
        print(f"    Master: executive summary FAILED ({e})")
        structure["executive_summary"] = ""

    stages = structure.get("stages", [])
    roles = structure.get("roles", [])
    print(f"    Master: {len(stages)} stages × {len(roles)} roles = {len(stages)*len(roles)} cells")

    # ── CALL 2+: Matrix in batches of 3-4 roles ──
    stage_list = json.dumps(stages, separators=(',',':'))
    matrix = {}
    batch_size = 4

    for i in range(0, len(roles), batch_size):
        batch_roles = roles[i:i + batch_size]
        role_names = ", ".join(r["name"] for r in batch_roles)
        role_ids = json.dumps(batch_roles, separators=(',',':'))

        matrix_prompt = f"""{context}

STAGES: {stage_list}
ROLES FOR THIS BATCH: {role_ids}

Fill the service blueprint MATRIX for these {len(batch_roles)} roles across all {len(stages)} stages.

Output JSON:
{{
  "matrix": {{
    "roleId-stageId": [
      {{"type": "activity|document|approval|critical|handover", "text": "What (under 12 words)", "detail": "One sentence."}}
    ]
  }}
}}

RULES:
- Use EXACTLY these role IDs for matrix keys: {', '.join(r['id'] for r in batch_roles)}
- Use EXACTLY these stage IDs: {', '.join(str(s['id']) for s in stages)}
- Key format: "roleId-stageId" — e.g., "{batch_roles[0]['id']}-{stages[0]['id']}"
- Generate EVERY combination. That's {len(batch_roles)} × {len(stages)} = {len(batch_roles)*len(stages)} cells.
- Each cell: exactly 2 items.
- Do NOT skip any cell. Do NOT abbreviate with "..."
- Output ONLY JSON. No markdown."""

        print(f"    Matrix batch {i//batch_size+1}: {role_names}")
        batch_result = await call_llm(PLANNER_SYSTEM, matrix_prompt, OUTLINE_MODEL, max_tokens=32000)
        try:
            batch_data = extract_json(batch_result)
            batch_matrix = batch_data.get("matrix", {})

            # Remap keys if LLM used wrong role IDs
            expected_role_ids = {r["id"] for r in batch_roles}
            actual_role_ids = {k.rsplit("-", 1)[0] for k in batch_matrix.keys() if "-" in k}
            if actual_role_ids and not actual_role_ids.intersection(expected_role_ids):
                # LLM used different IDs — try to remap by order
                actual_sorted = sorted(actual_role_ids)
                expected_sorted = [r["id"] for r in batch_roles]
                if len(actual_sorted) == len(expected_sorted):
                    id_map = dict(zip(actual_sorted, expected_sorted))
                    remapped = {}
                    for k, v in batch_matrix.items():
                        parts = k.rsplit("-", 1)
                        if len(parts) == 2 and parts[0] in id_map:
                            remapped[f"{id_map[parts[0]]}-{parts[1]}"] = v
                        else:
                            remapped[k] = v
                    batch_matrix = remapped
                    print(f"      Remapped {len(id_map)} role IDs to match structure")

            matrix.update(batch_matrix)
            print(f"      Got {len(batch_matrix)} cells")
        except (json.JSONDecodeError, Exception) as e:
            print(f"      PARSE FAILED: {e}")

    expected = len(stages) * len(roles)
    actual = len(matrix)
    print(f"    Master: {actual}/{expected} cells filled ({actual*100//expected if expected else 0}%)")

    structure["matrix"] = matrix
    return structure


# ─── Department Blueprint Generation (TWO-CALL for depth) ────────────

DEPT_SYSTEM_PART1 = """You are a world-class business operations architect generating COMPREHENSIVE, IMPLEMENTATION-READY department blueprints.

You have REAL RESEARCH data. USE IT. Every item must be specific, actionable, and grounded in actual industry practice.

QUALITY STANDARD — each item must have:
- Specific names (not "Document A" but "Pre-Delivery Inspection Checklist")
- Detailed descriptions (not "Check machine" but "Inspect all hydraulic connections, test boom extension/retraction cycles, verify platform leveling sensors, check emergency descent system, test all safety interlocks per JCB PDI-AWP-001 standard")
- Real field lists for documents (10-15 fields each)
- Specific numeric targets for KPIs
- Named roles and escalation authorities
- Time durations and SLAs

Output ONLY valid JSON. No markdown. No explanation."""

DEPT_SYSTEM_PART2 = """You are a world-class business operations architect. You are generating the SECOND HALF of a comprehensive department blueprint.

You have REAL RESEARCH data. USE IT. Be as specific, detailed, and actionable as the first part.

QUALITY STANDARD:
- Documents: each must list 10-15 specific fields, who creates it, who reviews it, frequency, approval chain
- KPIs: each must have specific numeric targets, measurement frequency, data source, who is accountable
- Interactions: 4-6 specific flows per connected department (not "sends data" but "sends daily parts consumption report with stock-below-reorder alerts by 5 PM")
- Escalation: 4 levels with specific triggers, response times, authorities, resolution procedures, and 3+ examples each
- Compliance: specific regulation names, clause numbers, audit frequency, documentation requirements

Output ONLY valid JSON. No markdown. No explanation."""


def _build_research_context(dept_name: str, research: dict) -> str:
    """Build filtered research context for a department."""
    r2 = research.get("stage2", {})
    r1 = research.get("stage1", {})

    dept_lower = dept_name.lower()
    dept_words = set(dept_lower.replace("&", " ").replace("/", " ").split())

    def matches_dept(text):
        text_lower = (text or "").lower()
        return dept_lower in text_lower or text_lower in dept_lower or bool(dept_words & set(text_lower.replace("&", " ").replace("/", " ").split()))

    dept_kpis = [k for k in r2.get("industry_kpis", []) if matches_dept(k.get("department", ""))]
    dept_docs = [d for d in r2.get("document_templates", []) if matches_dept(d.get("department", ""))]
    dept_compliance = [c for c in r2.get("compliance_requirements", []) if matches_dept(c.get("applies_to", ""))]

    if not dept_kpis:
        dept_kpis = r2.get("industry_kpis", [])
    if not dept_docs:
        dept_docs = r2.get("document_templates", [])
    if not dept_compliance:
        dept_compliance = r2.get("compliance_requirements", [])

    # Keep research context concise — only what's needed
    industry_brief = ""
    if r1:
        industry_brief = f"INDUSTRY: {r1.get('industry_overview', '')[:300]}"

    return f"""{industry_brief}

COMPLIANCE: {json.dumps(dept_compliance, separators=(',',':'))}
KPIs: {json.dumps(dept_kpis, separators=(',',':'))}
DOCUMENTS: {json.dumps(dept_docs, separators=(',',':'))}
SAFETY: {json.dumps(r2.get('safety_standards', []), separators=(',',':'))}"""


DEPT_SYSTEM_FOCUSED = """You are a world-class business operations architect generating COMPREHENSIVE, IMPLEMENTATION-READY department blueprints.

You have REAL RESEARCH data. USE IT. Every item must be specific, actionable, and grounded in actual industry practice.

QUALITY STANDARD — each item must have:
- Specific names (not "Document A" but "Pre-Delivery Inspection Checklist")
- Detailed descriptions (2-3 sentences minimum)
- Real field lists, numeric targets, named roles, time durations

CRITICAL: You MUST complete the ENTIRE JSON. Do NOT abbreviate with "..." or skip items.
Output ONLY valid JSON. No markdown fences. No explanation."""


async def generate_department(dept_name: str, dept_id: str, context: str, research: dict) -> dict:
    """Generate one department blueprint using FOUR focused LLM calls to prevent truncation."""

    research_ctx = _build_research_context(dept_name, research)

    # ── CALL A: Overview + Team Structure (small, fast) ──
    prompt_a = f"""{context}

{research_ctx}

Generate the OVERVIEW section for the "{dept_name}" department.

JSON:
{{
  "department": "{dept_name}",
  "department_id": "{dept_id}",
  "mission": "One-line mission statement specific to this department",
  "head_role": "Department Head Title",
  "team_structure": [
    {{"role": "Title", "count": "1-2", "reports_to": "...", "key_responsibilities": "3-4 specific bullet points"}}
  ]
}}

REQUIREMENTS:
- team_structure: 4-8 roles with realistic counts and reporting lines
- key_responsibilities: 3-4 specific responsibilities per role, referencing real tools/documents

Output ONLY JSON. No markdown."""

    # ── CALL B: Daily Timeline (focused, detailed) ──
    prompt_b = f"""{context}

{research_ctx}

Generate the DAILY TIMELINE for the "{dept_name}" department. This is a minute-by-minute guide of what happens each day.

JSON:
{{
  "daily_timeline": [
    {{
      "time": "7:00 AM",
      "block_title": "Descriptive Block Title",
      "activities": [
        {{
          "title": "Specific Activity Name",
          "description": "DETAILED: what exactly happens, what systems/tools are used, what the person physically does, what they check, what output they produce. 2-3 sentences. Include specific document names, tool names, SLAs.",
          "tags": ["doc", "system", "critical", "approval", "handover"],
          "icon": "emoji"
        }}
      ]
    }}
  ]
}}

REQUIREMENTS:
- 6-8 time blocks covering full day (7 AM to 6 PM)
- Each block: 3-4 DETAILED activities
- EVERY description: 2-3 sentences with specific tool/document/system names
- Complete the ENTIRE day. Do NOT stop early or abbreviate.

Output ONLY JSON. No markdown."""

    # ── CALL C: Workflows (focused, detailed) ──
    prompt_c = f"""{context}

{research_ctx}

Generate the PROCESS WORKFLOWS for the "{dept_name}" department.

JSON:
{{
  "workflows": [
    {{
      "title": "Specific Workflow Name (e.g., 'Enquiry to Quotation — E2Q')",
      "target_time": "e.g., 48 hours",
      "steps": [
        {{
          "title": "Step Name",
          "description": "DETAILED: what happens, who does it, tools/forms used, decision criteria, output. 2-3 sentences.",
          "role": "Specific role title",
          "color": "blue|green|orange|red|purple|teal",
          "time": "Duration",
          "documents": "Documents created/used",
          "decision_criteria": "Criteria if decision point"
        }}
      ]
    }}
  ]
}}

REQUIREMENTS:
- 4-5 major workflows
- Each workflow: 6-8 detailed steps
- Every step description: 2-3 sentences with specific details
- Complete ALL workflows fully. Do NOT abbreviate.

Output ONLY JSON. No markdown."""

    # ── CALL D: Documents + KPIs + Interactions + Escalation + Compliance ──
    prompt_d = f"""{context}

{research_ctx}

Generate DOCUMENTS, KPIs, INTERACTIONS, ESCALATION MATRIX, and COMPLIANCE for the "{dept_name}" department.

JSON:
{{
  "documents": [
    {{
      "name": "Document Name",
      "description": "Purpose — 2 sentences.",
      "fields": "field1, field2, field3... (10-15 specific fields)",
      "frequency": "Per Job / Daily / Weekly / Monthly",
      "flow": "Created by > Reviewed by > Approved by > Filed in",
      "retention": "Duration",
      "format": "Paper / Digital / Both"
    }}
  ],
  "kpis": [
    {{
      "name": "KPI Name",
      "target": "Numeric target",
      "unit": "%|hours|days|count|currency",
      "description": "What it measures and WHY. Include benchmark.",
      "measurement": "Data source, formula, frequency",
      "accountable": "Responsible role",
      "color": "green|blue|orange|red|purple"
    }}
  ],
  "interactions": [
    {{
      "department": "Other Dept",
      "inbound": ["Specific flow with details and timing"],
      "outbound": ["Specific flow with details and timing"]
    }}
  ],
  "escalation_matrix": [
    {{
      "level": 1,
      "title": "Level Name",
      "trigger": "Specific trigger",
      "description": "What happens at this level",
      "response_time": "SLA",
      "resolution_time": "Target",
      "authority": "Role",
      "actions": ["Action 1", "Action 2", "Action 3"],
      "examples": ["Example 1", "Example 2", "Example 3"]
    }}
  ],
  "compliance_items": [
    {{
      "name": "Regulation Name with clause",
      "description": "Requirements — 2-3 sentences.",
      "frequency": "Audit frequency",
      "responsible": "Role",
      "documentation": "Required records"
    }}
  ]
}}

QUANTITIES:
- documents: 10-15 with 10-15 fields each
- kpis: 8-10 with specific targets
- interactions: 4-6 departments with 2-3 inbound AND 2-3 outbound flows each
- escalation_matrix: 4 levels with 3 examples each
- compliance_items: 5-7 with clause references

Output ONLY JSON. No markdown."""

    # ── CALL E: Documents + KPIs (split from old Part D for depth) ──
    prompt_e = f"""{context}

{research_ctx}

Generate DOCUMENTS and KPIs for the "{dept_name}" department.

JSON:
{{
  "documents": [
    {{
      "name": "Document Name",
      "description": "Purpose — why this document exists and what decisions it enables. 2 sentences.",
      "fields": "field1, field2, field3, field4, field5, field6, field7, field8, field9, field10 — list 10-15 SPECIFIC fields",
      "frequency": "Per Job / Daily / Weekly / Monthly",
      "flow": "Created by Role > Reviewed by Role > Approved by Role > Filed in System",
      "retention": "Duration (e.g., 7 years for tax)",
      "format": "Paper / Digital / Both"
    }}
  ],
  "kpis": [
    {{
      "name": "KPI Name",
      "target": "Specific numeric target (e.g., 95%, <24 hrs, ₹12 Cr)",
      "unit": "%|hours|days|count|currency",
      "description": "What it measures and WHY it matters. Include industry benchmark.",
      "measurement": "Data source, calculation formula, frequency",
      "accountable": "Responsible role",
      "color": "green|blue|orange|red|purple"
    }}
  ]
}}

QUANTITIES:
- documents: 12-15 with 10-15 fields each. Include ALL forms, reports, logs, checklists this dept uses.
- kpis: 8-10 with specific numeric targets. Use research benchmarks where available.

Output ONLY JSON. No markdown."""

    # ── CALL F: Interactions + Escalation + Compliance ──
    prompt_f = f"""{context}

{research_ctx}

Generate DEPARTMENT INTERACTIONS, ESCALATION MATRIX, and COMPLIANCE for the "{dept_name}" department.

JSON:
{{
  "interactions": [
    {{
      "department": "Other Department Name",
      "inbound": [
        "SPECIFIC: 'Receives [what] from [who] by [when] with [details]'"
      ],
      "outbound": [
        "SPECIFIC: 'Sends [what] to [who] within [SLA] attaching [documents]'"
      ]
    }}
  ],
  "escalation_matrix": [
    {{
      "level": 1,
      "title": "Level Name (e.g., 'Frontline Resolution')",
      "trigger": "Specific trigger (e.g., 'Issue not resolved within 2 hours')",
      "description": "What happens — who is notified, what actions taken, what systems used.",
      "response_time": "SLA (e.g., 30 minutes)",
      "resolution_time": "Target resolution time",
      "authority": "Role title",
      "actions": ["Specific action 1", "Specific action 2", "Specific action 3"],
      "examples": ["Real-world example 1", "Real-world example 2", "Real-world example 3"]
    }}
  ],
  "compliance_items": [
    {{
      "name": "Regulation/Standard Name with clause (e.g., 'IS 800:2007 — General Construction in Steel')",
      "description": "What it requires, specific clauses, documentation needed, consequences of non-compliance. 2-3 sentences.",
      "frequency": "Audit/review frequency",
      "responsible": "Role who ensures compliance",
      "documentation": "What records must be maintained"
    }}
  ]
}}

QUANTITIES:
- interactions: 5-7 departments, each with 3-4 specific inbound AND 3-4 specific outbound flows
- escalation_matrix: 4 levels with specific triggers, 3 actions, and 3 examples each
- compliance_items: 5-8 specific regulations/standards with real clause references

Output ONLY JSON. No markdown."""

    # Run all 5 calls in parallel — each is small and focused
    results = await asyncio.gather(
        call_llm(DEPT_SYSTEM_FOCUSED, prompt_a, RENDERER_MODEL, max_tokens=8000),
        call_llm(DEPT_SYSTEM_FOCUSED, prompt_b, RENDERER_MODEL, max_tokens=16000),
        call_llm(DEPT_SYSTEM_FOCUSED, prompt_c, RENDERER_MODEL, max_tokens=16000),
        call_llm(DEPT_SYSTEM_FOCUSED, prompt_e, RENDERER_MODEL, max_tokens=16000),
        call_llm(DEPT_SYSTEM_FOCUSED, prompt_f, RENDERER_MODEL, max_tokens=16000),
    )

    labels = ["A-overview", "B-timeline", "C-workflows", "D-docs/kpis", "E-interactions/esc/compliance"]
    defaults_list = [
        {"department": dept_name, "department_id": dept_id, "mission": "", "team_structure": []},
        {"daily_timeline": []},
        {"workflows": []},
        {"documents": [], "kpis": []},
        {"interactions": [], "escalation_matrix": [], "compliance_items": []},
    ]

    # Parse each part independently
    merged = {}
    parsed_parts = {}
    for label, result, default in zip(labels, results, defaults_list):
        try:
            parsed = extract_json(result)
            merged.update(parsed)
            parsed_parts[label] = parsed
            print(f"      {label}: OK ({len(result)} chars)")
        except (json.JSONDecodeError, Exception) as e:
            print(f"      {label}: PARSE FAILED ({e}) — using empty defaults")
            merged.update(default)
            parsed_parts[label] = default

    # ── Quality validation + retry for thin results ──
    thin_retries = []

    # Check team structure
    if len(merged.get("team_structure", [])) < 3:
        thin_retries.append(("A-overview", prompt_a, 8000, defaults_list[0],
                             "team_structure", 3, "team roles"))

    # Check timeline
    total_acts = sum(len(b.get("activities", [])) for b in merged.get("daily_timeline", []))
    if len(merged.get("daily_timeline", [])) < 4 or total_acts < 10:
        thin_retries.append(("B-timeline", prompt_b, 16000, defaults_list[1],
                             "daily_timeline", 4, "timeline blocks"))

    # Check workflows
    total_wf_steps = sum(len(w.get("steps", [])) for w in merged.get("workflows", []))
    if len(merged.get("workflows", [])) < 3 or total_wf_steps < 12:
        thin_retries.append(("C-workflows", prompt_c, 16000, defaults_list[2],
                             "workflows", 3, "workflows"))

    # Check documents
    if len(merged.get("documents", [])) < 8:
        thin_retries.append(("D-docs/kpis", prompt_e, 16000, defaults_list[3],
                             "documents", 8, "documents"))

    # Check KPIs
    if len(merged.get("kpis", [])) < 6:
        thin_retries.append(("D-docs/kpis(kpi)", prompt_e, 16000, defaults_list[3],
                             "kpis", 6, "KPIs"))

    # Check interactions
    if len(merged.get("interactions", [])) < 3:
        thin_retries.append(("E-interactions", prompt_f, 16000, defaults_list[4],
                             "interactions", 3, "interactions"))

    # Check escalation
    if len(merged.get("escalation_matrix", [])) < 3:
        thin_retries.append(("E-escalation", prompt_f, 16000, defaults_list[4],
                             "escalation_matrix", 3, "escalation levels"))

    # Check compliance
    if len(merged.get("compliance_items", [])) < 3:
        thin_retries.append(("E-compliance", prompt_f, 16000, defaults_list[4],
                             "compliance_items", 3, "compliance items"))

    # Deduplicate retries by prompt (same prompt covers multiple thin sections)
    if thin_retries:
        seen_prompts = set()
        unique_retries = []
        for label, prompt, tokens, default, key, min_count, desc in thin_retries:
            prompt_id = id(prompt)
            if prompt_id not in seen_prompts:
                seen_prompts.add(prompt_id)
                unique_retries.append((label, prompt, tokens, default, key, min_count, desc))
            else:
                # Still log the thin section
                print(f"      THIN: {desc} ({len(merged.get(key, []))}/{min_count}) — covered by pending retry")

        for label, prompt, tokens, default, key, min_count, desc in unique_retries:
            current = len(merged.get(key, []))
            print(f"      THIN: {desc} ({current}/{min_count}) — retrying {label}...")
            try:
                retry_result = await call_llm(DEPT_SYSTEM_FOCUSED, prompt, RENDERER_MODEL, max_tokens=tokens)
                retry_parsed = extract_json(retry_result)
                # Only update if retry produced more content
                for rkey, rval in retry_parsed.items():
                    if isinstance(rval, list) and len(rval) > len(merged.get(rkey, [])):
                        merged[rkey] = rval
                        print(f"      RETRY {label}: {rkey} improved ({len(rval)} items)")
                    elif isinstance(rval, list):
                        print(f"      RETRY {label}: {rkey} no improvement ({len(rval)} vs {len(merged.get(rkey, []))})")
            except Exception as e:
                print(f"      RETRY {label}: FAILED ({e})")

    return merged


# ─── Glossary & Appendix Generation ──────────────────────────────────

GLOSSARY_SYSTEM = """You are a business operations encyclopedia. Generate an exhaustive glossary and appendix that covers EVERYTHING not covered in individual department blueprints.

Think broadly — industry terms, cross-department processes, general business policies, technology landscape, risk factors, market context, vendor relationships, seasonal patterns, career paths, meeting cadences, communication protocols, insurance requirements, facility management, IT infrastructure, data management, customer segmentation, pricing strategies, competitive landscape, and more.

This is the "everything else" document — cast the widest possible net. Be specific to the industry. Output ONLY valid JSON."""


async def generate_glossary(context: str, research: dict, dept_names: list[str]) -> dict:
    """Generate comprehensive glossary and appendix using TWO calls to avoid truncation."""

    r1 = research.get("stage1", {})
    r2 = research.get("stage2", {})

    research_block = f"""RESEARCH DATA:
Industry Overview: {r1.get('industry_overview', '')}
Terminology: {json.dumps(r1.get('industry_terminology', []))}
Common Documents: {json.dumps(r1.get('common_documents', []))}
Pain Points: {json.dumps(r1.get('typical_pain_points', []))}
Key Roles: {json.dumps(r1.get('key_roles', []))}
Compliance: {json.dumps(r2.get('compliance_requirements', []))}
Safety Standards: {json.dumps(r2.get('safety_standards', []))}
KPIs: {json.dumps(r2.get('industry_kpis', []))}
Workflows: {json.dumps(r2.get('workflow_patterns', []))}

DEPARTMENT BLUEPRINTS ALREADY GENERATED FOR: {', '.join(dept_names)}"""

    # ── CALL 1: Glossary + Cross-Dept Processes + Policies + Technology ──
    prompt1 = f"""{context}

{research_block}

Generate PART 1 of a comprehensive GLOSSARY & APPENDIX. This covers everything NOT in the department blueprints.

JSON:
{{
  "glossary": [
    {{"term": "Term/Abbreviation", "full_form": "Full form if abbreviation", "definition": "Clear 1-2 sentence definition specific to this industry", "category": "Technical|Commercial|Legal|Safety|Operations|Finance|HR|IT|Marketing"}}
  ],
  "cross_department_processes": [
    {{"name": "Process Name", "description": "What and why", "departments_involved": ["Dept1", "Dept2"], "trigger": "What starts it", "frequency": "How often", "key_steps": ["Step 1", "Step 2", "Step 3", "Step 4"], "output": "What it produces"}}
  ],
  "general_policies": [
    {{"name": "Policy Name", "scope": "Who it applies to", "description": "What the policy requires — be specific", "enforcement": "How enforced", "consequences": "What happens on violation"}}
  ],
  "technology_landscape": [
    {{"system": "System/Tool Name", "category": "CRM|ERP|Field Service|Communication|Safety|HR|Finance", "purpose": "What it does", "users": "Who uses it", "integration_points": "What it connects to", "status": "Current|Planned|Recommended"}}
  ]
}}

QUANTITIES: glossary 40-60 terms, cross_department_processes 8-12, general_policies 10-15, technology_landscape 10-15.
Output ONLY JSON."""

    # ── CALL 2: Risk + Meetings + Market + People + Benchmarks ──
    prompt2 = f"""{context}

{research_block}

Generate PART 2 of a comprehensive GLOSSARY & APPENDIX. This covers everything NOT in the department blueprints.

JSON:
{{
  "risk_register": [
    {{"risk": "Risk description", "category": "Operational|Financial|Safety|Legal|Market|Reputational", "likelihood": "High|Medium|Low", "impact": "High|Medium|Low", "mitigation": "How to prevent", "contingency": "What to do if it happens", "owner": "Who monitors"}}
  ],
  "meeting_cadences": [
    {{"meeting": "Meeting Name", "frequency": "Daily|Weekly|Monthly|Quarterly", "participants": "Who attends", "agenda": "What's covered", "duration": "How long", "output": "What it produces"}}
  ],
  "seasonal_patterns": [
    {{"period": "When", "pattern": "What happens", "impact": "How it affects operations", "preparation": "What to do in advance"}}
  ],
  "vendor_relationships": [
    {{"vendor_type": "Type", "examples": "Names/categories", "relationship": "How you work together", "key_terms": "Contract terms", "management": "How managed"}}
  ],
  "customer_segmentation": [
    {{"segment": "Name", "description": "Who they are", "needs": "What they need", "buying_pattern": "How they buy", "service_level": "Service level", "revenue_share": "% of revenue"}}
  ],
  "career_paths": [
    {{"track": "Track Name", "levels": ["Entry", "Mid", "Senior", "Leadership"], "typical_progression": "Time per step", "skills_needed": "Key skills"}}
  ],
  "insurance_requirements": [
    {{"type": "Insurance Type", "coverage": "What it covers", "required_by": "Who requires it", "typical_value": "Coverage amount"}}
  ],
  "industry_benchmarks": [
    {{"metric": "Benchmark", "value": "Standard value", "source": "Where from", "context": "What's good vs bad"}}
  ],
  "common_mistakes": [
    {{"mistake": "What goes wrong", "department": "Where", "consequence": "Impact", "prevention": "How to avoid"}}
  ]
}}

QUANTITIES: risk_register 12-15, meeting_cadences 8-10, seasonal_patterns 4-6, vendor_relationships 6-8, customer_segmentation 5-7, career_paths 4-5, insurance 5-6, benchmarks 10-12, common_mistakes 8-10.
Output ONLY JSON."""

    result1, result2 = await asyncio.gather(
        call_llm(GLOSSARY_SYSTEM, prompt1, PLANNER_MODEL, max_tokens=24000),
        call_llm(GLOSSARY_SYSTEM, prompt2, RENDERER_MODEL, max_tokens=24000),
    )

    try:
        part1 = extract_json(result1)
    except (json.JSONDecodeError, Exception) as e:
        print(f"    WARNING: Failed to parse Glossary Part 1 JSON: {e}")
        part1 = {"glossary": [], "cross_department_processes": [], "general_policies": [], "technology_landscape": []}

    try:
        part2 = extract_json(result2)
    except (json.JSONDecodeError, Exception) as e:
        print(f"    WARNING: Failed to parse Glossary Part 2 JSON: {e}")
        part2 = {"risk_register": [], "meeting_cadences": [], "seasonal_patterns": [], "vendor_relationships": [],
                 "customer_segmentation": [], "career_paths": [], "insurance_requirements": [],
                 "industry_benchmarks": [], "common_mistakes": []}

    return {**part1, **part2}


# ─── Main Pipeline ────────────────────────────────────────────────────

async def generate_blueprint_kit(context: str, research: dict, progress_cb=None) -> tuple[list[dict], dict]:
    """Generate complete blueprint kit from research context.
    Returns (files, raw_results) tuple.

    Progress steps (reported to caller via progress_cb):
      1/5  — Master blueprint generation
      2/5  — Master HTML rendering + start departments
      3/5  — Department blueprints (sub-progress in message text)
      4/5  — Glossary & appendix
      5/5  — Saving to account  (reported by _run_generation)
    """
    files = []
    raw_master = None
    raw_departments = []
    raw_glossary = None

    def report(step, total, msg):
        print(f"  [{step}/{total}] {msg}")
        if progress_cb:
            progress_cb(step, total, msg)

    # Steps: 1=master, 2=departments, 3=glossary, 4=saving (reported by caller), 5=done
    report(1, 5, "Generating master blueprint...")
    master = await generate_master_blueprint(context, research)
    raw_master = master

    master_html = render_master_blueprint(master)
    files.append({"name": "service-blueprint.html", "content": master_html})

    roles = master.get("roles", [])
    total_depts = len(roles)
    done_depts = 0

    batch_size = 3  # Smaller batches since each dept is now 2 calls
    for i in range(0, len(roles), batch_size):
        batch = roles[i:i + batch_size]
        report(2, 5, f"Generating departments ({done_depts}/{total_depts})...")
        print(f"    Batch {i // batch_size + 1}: {', '.join(r['name'] for r in batch)}")
        tasks = [
            generate_department(r["name"], r["id"], context, research)
            for r in batch
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for role, result in zip(batch, results):
            if isinstance(result, Exception):
                print(f"    ERROR {role['name']}: {result}")
                # Retry failed department once
                print(f"    RETRYING {role['name']}...")
                try:
                    result = await generate_department(role["name"], role["id"], context, research)
                except Exception as retry_err:
                    print(f"    RETRY FAILED {role['name']}: {retry_err}")
                    done_depts += 1
                    continue
            try:
                html = render_department_blueprint(result, master.get("company_name", ""))
                files.append({"name": f"{role['id']}-blueprint.html", "content": html})
                raw_departments.append(result)
            except Exception as e:
                print(f"    RENDER ERROR {role['name']}: {e}")
                # Retry on render error too (data might have been malformed)
                print(f"    RETRYING {role['name']} after render error...")
                try:
                    result = await generate_department(role["name"], role["id"], context, research)
                    html = render_department_blueprint(result, master.get("company_name", ""))
                    files.append({"name": f"{role['id']}-blueprint.html", "content": html})
                    raw_departments.append(result)
                except Exception as retry_err:
                    print(f"    RETRY FAILED {role['name']}: {retry_err}")
            done_depts += 1
        # Update progress after each batch completes
        report(2, 5, f"Generating departments ({done_depts}/{total_depts})...")

    # ── Glossary & Appendix ──
    report(3, 5, "Generating glossary & appendix...")
    dept_names = [r["name"] for r in roles]
    try:
        glossary_data = await generate_glossary(context, research, dept_names)
        raw_glossary = glossary_data
        glossary_html = render_glossary(glossary_data, master.get("company_name", ""))
        files.append({"name": "glossary-appendix.html", "content": glossary_html})
    except Exception as e:
        print(f"    GLOSSARY ERROR: {e}")

    raw_results = {"master": raw_master, "departments": raw_departments, "glossary": raw_glossary}
    return files, raw_results
