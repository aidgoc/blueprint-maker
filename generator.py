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

from config import OPENROUTER_API_KEY, PLANNER_MODEL, RENDERER_MODEL
from renderer import render_master_blueprint, render_department_blueprint, render_glossary


async def call_llm(system: str, prompt: str, model: str, max_tokens: int = 8000) -> str:
    async with httpx.AsyncClient(timeout=300) as client:
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
        return data["choices"][0]["message"]["content"]


def extract_json(text: str) -> dict:
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        repaired = text
        # Strip trailing garbage
        while repaired and repaired[-1] not in ']},"0123456789truefalsn':
            repaired = repaired[:-1]
        # Try multiple repair strategies
        for attempt in range(5):
            try:
                # Close unclosed strings
                if repaired.count('"') % 2 == 1:
                    repaired += '"'
                # Remove trailing commas
                while repaired and repaired.rstrip()[-1:] == ',':
                    repaired = repaired.rstrip()[:-1]
                # Remove incomplete key-value pairs (trailing "key":  with no value)
                import re
                repaired = re.sub(r',\s*"[^"]*"\s*:\s*$', '', repaired)
                # Close brackets/braces
                repaired += ']' * max(0, repaired.count('[') - repaired.count(']'))
                repaired += '}' * max(0, repaired.count('{') - repaired.count('}'))
                return json.loads(repaired)
            except json.JSONDecodeError:
                # Try trimming back to last complete item
                # Find last complete object/array boundary
                for trim_char in ['},', '],', '}', ']']:
                    idx = repaired.rfind(trim_char)
                    if idx > len(repaired) * 0.5:  # Don't trim more than half
                        repaired = repaired[:idx + len(trim_char)]
                        break
                else:
                    break
        # Final aggressive attempt — trim to last valid closing brace/bracket
        last_close = max(repaired.rfind('}'), repaired.rfind(']'))
        if last_close > len(repaired) * 0.3:
            repaired = repaired[:last_close + 1]
            repaired += ']' * max(0, repaired.count('[') - repaired.count(']'))
            repaired += '}' * max(0, repaired.count('{') - repaired.count('}'))
        return json.loads(repaired)


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
    """Generate master blueprint using research context."""

    r1 = research.get("stage1", {})
    r2 = research.get("stage2", {})

    compliance_text = ""
    if r2.get("compliance_requirements"):
        compliance_text = "REAL COMPLIANCE STANDARDS FOUND:\n" + json.dumps(r2["compliance_requirements"], indent=1)

    kpi_text = ""
    if r2.get("industry_kpis"):
        kpi_text = "REAL INDUSTRY KPI BENCHMARKS:\n" + json.dumps(r2["industry_kpis"], indent=1)

    doc_text = ""
    if r2.get("document_templates"):
        doc_text = "REAL DOCUMENT TEMPLATES FOUND:\n" + json.dumps(r2["document_templates"], indent=1)

    workflow_text = ""
    if r2.get("workflow_patterns"):
        workflow_text = "REAL WORKFLOW PATTERNS:\n" + json.dumps(r2["workflow_patterns"], indent=1)

    prompt = f"""{context}

### RESEARCH-BACKED DATA (use these — they are from real industry sources):
{compliance_text}
{kpi_text}
{doc_text}
{workflow_text}

---

Using ALL the above context and research, generate a master service blueprint JSON:
{{
  "company_name": "...",
  "industry_tag": "short label",
  "stages": [{{"id": 1, "name": "Stage Name", "icon": "emoji"}}],
  "roles": [{{"id": "role_key", "name": "Role Name", "icon": "emoji"}}],
  "matrix": {{
    "role_key-1": [
      {{"type": "activity|document|approval|critical|handover", "text": "What", "detail": "Details"}}
    ]
  }}
}}

IMPORTANT:
- Use the ACTUAL stages and departments from the user's answers (refined as needed)
- Matrix keys: "roleId-stageId". Generate for EVERY role × stage.
- Each cell: 3-6 items. Use real document names, real standards, real terminology.
- Include a "client" role for the customer's perspective.
- Output ONLY the JSON."""

    result = await call_llm(PLANNER_SYSTEM, prompt, PLANNER_MODEL, max_tokens=16000)
    return extract_json(result)


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


async def generate_department(dept_name: str, dept_id: str, context: str, research: dict) -> dict:
    """Generate one department blueprint using TWO LLM calls for maximum depth."""

    r2 = research.get("stage2", {})
    r1 = research.get("stage1", {})

    # Filter research to this department (broader matching)
    dept_lower = dept_name.lower()
    dept_words = set(dept_lower.replace("&", " ").replace("/", " ").split())

    def matches_dept(text):
        text_lower = (text or "").lower()
        return dept_lower in text_lower or text_lower in dept_lower or bool(dept_words & set(text_lower.replace("&", " ").replace("/", " ").split()))

    dept_kpis = [k for k in r2.get("industry_kpis", []) if matches_dept(k.get("department", ""))]
    dept_docs = [d for d in r2.get("document_templates", []) if matches_dept(d.get("department", ""))]
    dept_compliance = [c for c in r2.get("compliance_requirements", []) if matches_dept(c.get("applies_to", ""))]

    # If no department-specific items, include all
    if not dept_kpis:
        dept_kpis = r2.get("industry_kpis", [])
    if not dept_docs:
        dept_docs = r2.get("document_templates", [])
    if not dept_compliance:
        dept_compliance = r2.get("compliance_requirements", [])

    # Include Stage 1 research for industry context
    industry_context = ""
    if r1:
        industry_context = f"""INDUSTRY CONTEXT:
Overview: {r1.get('industry_overview', '')}
Common Documents: {json.dumps(r1.get('common_documents', []))}
Key Roles: {json.dumps(r1.get('key_roles', []))}
Pain Points: {json.dumps(r1.get('typical_pain_points', []))}
Terminology: {json.dumps(r1.get('industry_terminology', [])[:8])}"""

    research_context = f"""{industry_context}

COMPLIANCE & REGULATORY DATA:
{json.dumps(dept_compliance, indent=1)}

KPI BENCHMARKS:
{json.dumps(dept_kpis, indent=1)}

DOCUMENT TEMPLATES:
{json.dumps(dept_docs, indent=1)}

ESCALATION PATTERNS:
{json.dumps(r2.get('escalation_patterns', []), indent=1)}

WORKFLOW PATTERNS:
{json.dumps(r2.get('workflow_patterns', []), indent=1)}

SAFETY STANDARDS:
{json.dumps(r2.get('safety_standards', []), indent=1)}"""

    # ── CALL 1: Overview + Timeline + Workflows ──
    prompt_part1 = f"""{context}

{research_context}

Generate PART 1 of a comprehensive blueprint for the "{dept_name}" department.

This is for a REAL business — make every item specific, actionable, and grounded in industry practice.

PART 1 JSON (overview + timeline + workflows):
{{
  "department": "{dept_name}",
  "department_id": "{dept_id}",
  "mission": "Comprehensive one-line mission statement",
  "head_role": "Title",
  "team_structure": [
    {{"role": "Title", "count": "1-2", "reports_to": "...", "key_responsibilities": "3-4 bullet points of what this person does"}}
  ],
  "daily_timeline": [
    {{
      "time": "7:00 AM",
      "block_title": "Descriptive Block Title",
      "activities": [
        {{
          "title": "Specific Activity Name",
          "description": "DETAILED description — what exactly happens, what systems are used, what the person physically does, what they check, what they produce. Minimum 2-3 sentences. Include specific tools, forms, systems, and SLAs.",
          "tags": ["doc", "system", "critical", "approval", "handover"],
          "icon": "emoji"
        }}
      ]
    }}
  ],
  "workflows": [
    {{
      "title": "Specific Workflow Name (e.g., 'Enquiry to Quotation — E2Q')",
      "target_time": "e.g., 48 hours",
      "steps": [
        {{
          "title": "Step Name",
          "description": "DETAILED description — what happens, who does it, what tools/forms are used, decision criteria, output produced. 2-3 sentences minimum.",
          "role": "Specific role title",
          "color": "blue|green|orange|red|purple|teal",
          "time": "Duration (e.g., 30 min, 2 hours, 1 day)",
          "documents": "Any documents created/used at this step",
          "decision_criteria": "If this is a decision point, what are the criteria?"
        }}
      ]
    }}
  ]
}}

QUANTITY REQUIREMENTS:
- team_structure: List EVERY role in the department (4-8 roles), with realistic counts and reporting lines
- daily_timeline: 7-8 time blocks covering full day (7 AM to 6 PM), each block with 4-6 DETAILED activities
- workflows: 4-6 major workflows, each with 7-10 detailed steps

EVERY activity description must be 2-3 sentences minimum. Include specific tool names, document names, SLA times, and decision criteria.

Output ONLY the JSON."""

    # ── CALL 2: Documents + KPIs + Interactions + Escalation + Compliance ──
    prompt_part2 = f"""{context}

{research_context}

Generate PART 2 of a comprehensive blueprint for the "{dept_name}" department.

This is for a REAL business — make every item specific, actionable, and grounded in REAL industry standards.

PART 2 JSON (documents + KPIs + interactions + escalation + compliance):
{{
  "documents": [
    {{
      "name": "Specific Document Name",
      "description": "Detailed purpose — why this document exists, what business process it supports, what decisions it enables. 2 sentences.",
      "fields": "field1, field2, field3, field4, field5, field6, field7, field8, field9, field10 — list 10-15 SPECIFIC fields",
      "frequency": "When created (Per Job / Daily / Weekly / Monthly / Per Event)",
      "flow": "Created by Role > Reviewed by Role > Approved by Role > Filed in System",
      "retention": "How long to keep (e.g., 7 years for tax, 5 years for safety)",
      "format": "Paper / Digital / Both"
    }}
  ],
  "kpis": [
    {{
      "name": "Specific KPI Name",
      "target": "Specific numeric target (e.g., 95%, <24 hrs, ₹12 Cr)",
      "unit": "%|hours|days|count|currency",
      "description": "What this KPI measures and WHY it matters. Include industry benchmark if available.",
      "measurement": "How to measure — data source, calculation formula, frequency",
      "accountable": "Who is responsible for hitting this target",
      "color": "green|blue|orange|red|purple"
    }}
  ],
  "interactions": [
    {{
      "department": "Other Department Name",
      "inbound": [
        "SPECIFIC flow: 'Receives daily stock reorder alerts from Parts Warehouse by 9 AM with item codes, current stock levels, and reorder quantities'"
      ],
      "outbound": [
        "SPECIFIC flow: 'Sends approved purchase orders to Finance for payment processing within 24 hours of vendor confirmation, attaching quotation comparison sheet'"
      ]
    }}
  ],
  "escalation_matrix": [
    {{
      "level": 1,
      "title": "Specific Level Name (e.g., 'Frontline Resolution')",
      "trigger": "Specific trigger criteria (e.g., 'Service request not acknowledged within 2 hours')",
      "description": "Detailed description of what happens at this level — who is notified, what actions are taken, what systems are used, what documentation is created.",
      "response_time": "Specific SLA (e.g., 30 minutes)",
      "resolution_time": "Target resolution time",
      "authority": "Specific role title",
      "actions": ["Specific action 1", "Specific action 2", "Specific action 3"],
      "examples": ["Detailed real-world example 1", "Detailed real-world example 2", "Detailed real-world example 3"]
    }}
  ],
  "compliance_items": [
    {{
      "name": "Specific Regulation/Standard Name (e.g., 'IS 4573:2019 — Powered Industrial Trucks')",
      "description": "What this regulation requires, specific clauses that apply to this department, what documentation must be maintained, consequences of non-compliance. 2-3 sentences.",
      "frequency": "Audit/review frequency",
      "responsible": "Who ensures compliance",
      "documentation": "What records must be maintained"
    }}
  ]
}}

QUANTITY REQUIREMENTS:
- documents: 12-18 documents with 10-15 fields each
- kpis: 8-12 KPIs with specific numeric targets (use research benchmarks)
- interactions: 5-7 departments, each with 3-5 specific inbound AND 3-5 specific outbound flows
- escalation_matrix: 4 levels with detailed triggers, actions, and 3+ examples each
- compliance_items: 5-8 specific regulations/standards with clause references

USE the research data for real regulation names, real KPI benchmarks, and real document standards. Do not use generic placeholders.

Output ONLY the JSON."""

    # Run both calls in parallel
    result1, result2 = await asyncio.gather(
        call_llm(DEPT_SYSTEM_PART1, prompt_part1, RENDERER_MODEL, max_tokens=16000),
        call_llm(DEPT_SYSTEM_PART2, prompt_part2, RENDERER_MODEL, max_tokens=16000),
    )

    part1 = extract_json(result1)
    part2 = extract_json(result2)

    # Merge
    merged = {**part1, **part2}
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
        call_llm(GLOSSARY_SYSTEM, prompt1, PLANNER_MODEL, max_tokens=16000),
        call_llm(GLOSSARY_SYSTEM, prompt2, RENDERER_MODEL, max_tokens=16000),
    )

    part1 = extract_json(result1)
    part2 = extract_json(result2)

    return {**part1, **part2}


# ─── Main Pipeline ────────────────────────────────────────────────────

async def generate_blueprint_kit(context: str, research: dict) -> list[dict]:
    """Generate complete blueprint kit from research context."""
    files = []

    print("  [1/4] Generating master blueprint (smart model)...")
    master = await generate_master_blueprint(context, research)

    print("  [2/4] Rendering master HTML...")
    master_html = render_master_blueprint(master)
    files.append({"name": "service-blueprint.html", "content": master_html})

    roles = master.get("roles", [])
    print(f"  [3/4] Generating {len(roles)} department blueprints (2 calls each for depth)...")

    batch_size = 3  # Smaller batches since each dept is now 2 calls
    for i in range(0, len(roles), batch_size):
        batch = roles[i:i + batch_size]
        print(f"    Batch {i // batch_size + 1}: {', '.join(r['name'] for r in batch)}")
        tasks = [
            generate_department(r["name"], r["id"], context, research)
            for r in batch
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for role, result in zip(batch, results):
            if isinstance(result, Exception):
                print(f"    ERROR {role['name']}: {result}")
                continue
            try:
                html = render_department_blueprint(result, master.get("company_name", ""))
                files.append({"name": f"{role['id']}-blueprint.html", "content": html})
            except Exception as e:
                print(f"    RENDER ERROR {role['name']}: {e}")

    # ── Glossary & Appendix ──
    print("  [4/4] Generating glossary & appendix (smart model)...")
    dept_names = [r["name"] for r in roles]
    try:
        glossary_data = await generate_glossary(context, research, dept_names)
        glossary_html = render_glossary(glossary_data, master.get("company_name", ""))
        files.append({"name": "glossary-appendix.html", "content": glossary_html})
    except Exception as e:
        print(f"    GLOSSARY ERROR: {e}")

    return files
