# Plan 1: Block Foundation + Generation Pipeline

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current "generate HTML files → store in Cloud Storage" pipeline with a block-based data model where blueprints are stored as structured JSON sections in Firestore, with HTML rendered on demand.

**Architecture:** Generator produces JSON → `block_converter.py` transforms into typed blocks → `block_renderer.py` renders each block to HTML fragments (cached as `html_cache`) → sections stored in Firestore subcollections. Existing legacy blueprints remain untouched. New `export/zip` endpoint renders blocks to full HTML on demand.

**Tech Stack:** Python FastAPI, Firestore (subcollections), existing OpenRouter LLM pipeline

**Spec:** `docs/superpowers/specs/2026-03-14-blueprint-editor-design.md`

---

## File Structure

### New Files
| File | Responsibility |
|------|---------------|
| `block_types.py` | Block type definitions, schemas, validation, ID generation, slugify |
| `block_converter.py` | Convert generator JSON output → list of typed blocks |
| `block_renderer.py` | Render individual blocks → HTML fragments; render full section → standalone HTML |
| `tests/__init__.py` | Make tests a package |
| `tests/test_block_types.py` | Tests for block schemas and validation |
| `tests/test_block_converter.py` | Tests for generator-output-to-blocks conversion |
| `tests/test_block_renderer.py` | Tests for block-to-HTML rendering |
| `tests/test_block_pipeline.py` | Integration tests for full pipeline |

### Modified Files
| File | Changes |
|------|---------|
| `db.py` | Add section CRUD functions (subcollection), update `create_blueprint` to set `format: "blocks"` |
| `server.py` | Add section endpoints, modify `_persist_blueprint_to_firebase` to save blocks, add `/export/zip` endpoint |
| `generator.py` | Modify `generate_blueprint_kit` to return `(files, raw_results)` tuple |
| `config.py` | Add `CURRENT_RENDERER_VERSION = 1` |

### Key Data Shape Reference (from generator.py LLM prompts)

These are the ACTUAL structures the LLM produces. The block converter must match these exactly.

```python
# From generate_department() Part 1 (generator.py:314-352):
"team_structure": [{"role": str, "count": str, "reports_to": str, "key_responsibilities": str}]
"daily_timeline": [{"time": str, "block_title": str, "activities": [{"title": str, "description": str, "tags": [str], "icon": str}]}]
"workflows": [{"title": str, "target_time": str, "steps": [{"title": str, "description": str, "role": str, "color": str, "time": str, "documents": str, "decision_criteria": str}]}]

# From generate_department() Part 2 (generator.py:373-430):
"documents": [{"name": str, "description": str, "fields": str, "frequency": str, "flow": str, "retention": str, "format": str}]
"kpis": [{"name": str, "target": str, "unit": str, "description": str, "measurement": str, "accountable": str, "color": str}]
"interactions": [{"department": str, "inbound": [str], "outbound": [str]}]  # NOTE: list of dept objects, inbound/outbound are string arrays
"escalation_matrix": [{"level": int, "title": str, "trigger": str, "description": str, "response_time": str, "resolution_time": str, "authority": str, "actions": [str], "examples": [str]}]
"compliance_items": [{"name": str, "description": str, "frequency": str, "responsible": str, "documentation": str}]

# From generate_glossary() (generator.py:502-556):
"glossary": [{"term": str, "full_form": str, "definition": str, "category": str}]  # NOTE: key is "glossary", not "terms"
# Plus: cross_department_processes, general_policies, technology_landscape, risk_register, meeting_cadences, etc.
```

---

## Chunk 1: Block Type Definitions & Validation

### Task 1: Create tests directory and define block type schemas

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_block_types.py`
- Create: `block_types.py`

- [ ] **Step 1: Create tests directory**

```bash
mkdir -p /home/harshwardhan/blueprint_maker/tests
touch /home/harshwardhan/blueprint_maker/tests/__init__.py
```

- [ ] **Step 2: Write test for block type registry**

```python
# tests/test_block_types.py
import pytest
from block_types import BLOCK_TYPES, validate_block, create_block, generate_block_id, slugify

def test_all_block_types_registered():
    expected = {
        "heading", "rich-text", "kpi-grid", "workflow", "checklist",
        "table", "timeline", "card-grid", "glossary", "divider",
        "org-chart", "flow-diagram"
    }
    assert set(BLOCK_TYPES.keys()) == expected

def test_generate_block_id_format():
    bid = generate_block_id()
    assert bid.startswith("b_")
    assert len(bid) == 14  # "b_" + 12 hex chars

def test_create_heading_block():
    block = create_block("heading", {"text": "Service Department", "level": 1})
    assert block["type"] == "heading"
    assert block["data"]["text"] == "Service Department"
    assert block["data"]["level"] == 1
    assert block["id"].startswith("b_")
    assert block["style"] == {"color_scheme": "default", "layout": "default", "custom_css": None}
    assert block["html_cache"] == ""

def test_create_block_invalid_type():
    with pytest.raises(ValueError, match="Unknown block type"):
        create_block("invalid_type", {})

def test_validate_heading_valid():
    block = create_block("heading", {"text": "Hello", "level": 2})
    assert validate_block(block) is True

def test_validate_heading_invalid_level():
    block = create_block("heading", {"text": "Hello", "level": 5})
    assert validate_block(block) is False

def test_validate_workflow_valid():
    data = {
        "steps": [{"id": "s1", "title": "Step 1", "description": "Do thing", "type": "activity", "assignee": "Tech"}],
        "connections": []
    }
    block = create_block("workflow", data)
    assert validate_block(block) is True

def test_validate_kpi_grid_valid():
    data = [{"name": "Revenue", "value": "100K", "target": "120K", "unit": "$", "trend": "up"}]
    block = create_block("kpi-grid", data)
    assert validate_block(block) is True

def test_create_block_with_custom_style():
    block = create_block("heading", {"text": "Test", "level": 1}, style={"color_scheme": "blue"})
    assert block["style"]["color_scheme"] == "blue"
    assert block["style"]["layout"] == "default"

def test_slugify():
    assert slugify("Service Department") == "service_department"
    assert slugify("Sales & Marketing") == "sales_marketing"
    assert slugify("  Field  Tech  ") == "field_tech"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /home/harshwardhan/blueprint_maker && python -m pytest tests/test_block_types.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'block_types'`

- [ ] **Step 4: Implement block_types.py**

```python
# block_types.py
"""Block type definitions, schemas, validation, and ID generation."""

import secrets
import re


def generate_block_id() -> str:
    """Generate a unique block ID like 'b_a1b2c3d4e5f6'."""
    return f"b_{secrets.token_hex(6)}"


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug for section IDs."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s-]+', '_', text)
    return text.strip('_')


def _validate_heading(data):
    return isinstance(data, dict) and isinstance(data.get("text"), str) and data.get("level") in (1, 2, 3, 4)

def _validate_rich_text(data):
    return isinstance(data, dict) and isinstance(data.get("html"), str)

def _validate_kpi_grid(data):
    return isinstance(data, list) and all(isinstance(i, dict) and "name" in i for i in data)

def _validate_workflow(data):
    return isinstance(data, dict) and isinstance(data.get("steps"), list) and all(isinstance(s, dict) and "title" in s for s in data["steps"])

def _validate_checklist(data):
    return isinstance(data, list) and all(isinstance(i, dict) and "text" in i for i in data)

def _validate_table(data):
    return isinstance(data, dict) and isinstance(data.get("columns"), list) and isinstance(data.get("rows"), list)

def _validate_timeline(data):
    return isinstance(data, list) and all(isinstance(i, dict) and "phase" in i for i in data)

def _validate_card_grid(data):
    return isinstance(data, list) and all(isinstance(i, dict) and "title" in i for i in data)

def _validate_glossary(data):
    return isinstance(data, list) and all(isinstance(i, dict) and "term" in i for i in data)

def _validate_divider(data):
    return isinstance(data, dict) and data.get("style") in ("solid", "dashed", "dotted")

def _validate_org_chart(data):
    return isinstance(data, dict) and isinstance(data.get("roles"), list) and all(isinstance(r, dict) and "title" in r for r in data["roles"])

def _validate_flow_diagram(data):
    return isinstance(data, dict) and isinstance(data.get("nodes"), list) and isinstance(data.get("edges"), list)


BLOCK_TYPES = {
    "heading": {"validate": _validate_heading},
    "rich-text": {"validate": _validate_rich_text},
    "kpi-grid": {"validate": _validate_kpi_grid},
    "workflow": {"validate": _validate_workflow},
    "checklist": {"validate": _validate_checklist},
    "table": {"validate": _validate_table},
    "timeline": {"validate": _validate_timeline},
    "card-grid": {"validate": _validate_card_grid},
    "glossary": {"validate": _validate_glossary},
    "divider": {"validate": _validate_divider},
    "org-chart": {"validate": _validate_org_chart},
    "flow-diagram": {"validate": _validate_flow_diagram},
}

DEFAULT_STYLE = {"color_scheme": "default", "layout": "default", "custom_css": None}


def create_block(block_type: str, data: dict | list, style: dict | None = None) -> dict:
    """Create a new block with generated ID and default style."""
    if block_type not in BLOCK_TYPES:
        raise ValueError(f"Unknown block type: {block_type}")
    merged_style = {**DEFAULT_STYLE, **(style or {})}
    return {"id": generate_block_id(), "type": block_type, "data": data, "style": merged_style, "html_cache": ""}


def validate_block(block: dict) -> bool:
    """Validate a block's data against its type schema."""
    block_type = block.get("type")
    if block_type not in BLOCK_TYPES:
        return False
    return BLOCK_TYPES[block_type]["validate"](block.get("data"))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/harshwardhan/blueprint_maker && python -m pytest tests/test_block_types.py -v`
Expected: All 10 tests PASS

- [ ] **Step 6: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add block_types.py tests/__init__.py tests/test_block_types.py
git commit -m "feat: add block type definitions, schemas, and validation"
```

---

## Chunk 2: Block Converter (Generator Output → Blocks)

### Task 2: Convert generator JSON to blocks

**Files:**
- Create: `block_converter.py`
- Create: `tests/test_block_converter.py`

- [ ] **Step 1: Write tests for block converter**

Tests use the ACTUAL data shapes from the generator LLM prompts (see Key Data Shape Reference above).

```python
# tests/test_block_converter.py
import pytest
from block_converter import convert_department_to_blocks, convert_master_to_blocks, convert_glossary_to_blocks

def test_convert_department_heading():
    dept = {"department": "Service", "department_id": "service"}
    blocks = convert_department_to_blocks(dept)
    assert blocks[0]["type"] == "heading"
    assert blocks[0]["data"]["text"] == "Service"

def test_convert_department_kpis():
    """KPIs from generator: {name, target, unit, description, measurement, accountable, color}"""
    dept = {
        "department": "Service", "department_id": "service",
        "kpis": [{"name": "First-Time Fix Rate", "target": "92%", "unit": "%",
                  "description": "Percentage fixed on first visit", "measurement": "Monthly",
                  "accountable": "Service Manager", "color": "green"}]
    }
    blocks = convert_department_to_blocks(dept)
    kpi_blocks = [b for b in blocks if b["type"] == "kpi-grid"]
    assert len(kpi_blocks) == 1
    assert kpi_blocks[0]["data"][0]["name"] == "First-Time Fix Rate"
    assert kpi_blocks[0]["data"][0]["target"] == "92%"

def test_convert_department_workflows():
    """Workflows from generator: {title, target_time, steps: [{title, description, role, color, time, documents, decision_criteria}]}"""
    dept = {
        "department": "Service", "department_id": "service",
        "workflows": [
            {"title": "Service Call Intake", "target_time": "30 min",
             "steps": [{"title": "Receive call", "description": "Log customer details",
                        "role": "CSR", "color": "blue", "time": "5 min",
                        "documents": "Call log", "decision_criteria": ""}]}
        ]
    }
    blocks = convert_department_to_blocks(dept)
    wf_blocks = [b for b in blocks if b["type"] == "workflow"]
    assert len(wf_blocks) == 1
    assert wf_blocks[0]["data"]["steps"][0]["title"] == "Receive call"
    assert wf_blocks[0]["data"]["steps"][0]["assignee"] == "CSR"

def test_convert_department_daily_timeline():
    """daily_timeline from generator: {time, block_title, activities: [{title, description, tags, icon}]}"""
    dept = {
        "department": "Service", "department_id": "service",
        "daily_timeline": [
            {"time": "7:00 AM", "block_title": "Morning Prep",
             "activities": [
                 {"title": "Morning briefing", "description": "Review day's schedule", "tags": ["critical"], "icon": "📋"},
                 {"title": "Check equipment", "description": "Verify van inventory", "tags": ["doc"], "icon": "🔧"}
             ]}
        ]
    }
    blocks = convert_department_to_blocks(dept)
    timeline_blocks = [b for b in blocks if b["type"] == "timeline"]
    assert len(timeline_blocks) == 1
    item = timeline_blocks[0]["data"][0]
    assert item["phase"] == "7:00 AM — Morning Prep"
    assert len(item["activities"]) == 2
    assert "Morning briefing" in item["activities"][0]

def test_convert_department_team_structure():
    """team_structure from generator: {role, count, reports_to, key_responsibilities}"""
    dept = {
        "department": "Service", "department_id": "service",
        "team_structure": [
            {"role": "Service Manager", "count": "1", "reports_to": "GM",
             "key_responsibilities": "Oversee operations, manage team, handle escalations"}
        ]
    }
    blocks = convert_department_to_blocks(dept)
    org_blocks = [b for b in blocks if b["type"] == "org-chart"]
    assert len(org_blocks) == 1
    assert org_blocks[0]["data"]["roles"][0]["title"] == "Service Manager"
    assert org_blocks[0]["data"]["roles"][0]["reports_to"] == "GM"

def test_convert_department_interactions():
    """interactions from generator: [{department, inbound: [str], outbound: [str]}] — list of dept objects with STRING arrays"""
    dept = {
        "department": "Service", "department_id": "service",
        "interactions": [
            {"department": "Sales", "inbound": ["Receives new customer handoff with contract details"],
             "outbound": ["Sends service completion report for billing"]},
            {"department": "Accounting", "inbound": ["Receives budget approvals"],
             "outbound": ["Sends invoice requests within 24 hours"]}
        ]
    }
    blocks = convert_department_to_blocks(dept)
    flow_blocks = [b for b in blocks if b["type"] == "flow-diagram"]
    assert len(flow_blocks) == 1
    nodes = flow_blocks[0]["data"]["nodes"]
    edges = flow_blocks[0]["data"]["edges"]
    # Should have self + Sales + Accounting = 3 nodes
    assert len(nodes) == 3
    # Should have 2 inbound + 2 outbound = 4 edges
    assert len(edges) == 4

def test_convert_department_escalation_matrix():
    """escalation_matrix from generator: {level, title, trigger, description, response_time, resolution_time, authority, actions, examples}"""
    dept = {
        "department": "Service", "department_id": "service",
        "escalation_matrix": [
            {"level": 1, "title": "Frontline Resolution", "trigger": "Customer complaint",
             "description": "Supervisor handles directly", "response_time": "30 min",
             "resolution_time": "2 hours", "authority": "Team Lead",
             "actions": ["Acknowledge complaint", "Document issue", "Propose resolution"],
             "examples": ["Late arrival", "Incomplete work"]}
        ]
    }
    blocks = convert_department_to_blocks(dept)
    table_blocks = [b for b in blocks if b["type"] == "table"]
    assert len(table_blocks) == 1
    assert "Level" in table_blocks[0]["data"]["columns"]
    assert "Response Time" in table_blocks[0]["data"]["columns"]
    assert table_blocks[0]["data"]["rows"][0][0] == "1"

def test_convert_department_documents():
    """documents from generator: {name, description, fields, frequency, flow, retention, format}"""
    dept = {
        "department": "Service", "department_id": "service",
        "documents": [
            {"name": "Work Order Form", "description": "Track service jobs from dispatch to completion",
             "fields": "customer_name, address, issue, technician, date", "frequency": "Per Job",
             "flow": "CSR > Dispatcher > Tech > Manager", "retention": "5 years", "format": "Digital"}
        ]
    }
    blocks = convert_department_to_blocks(dept)
    checklist_blocks = [b for b in blocks if b["type"] == "checklist"]
    assert len(checklist_blocks) >= 1
    assert "Work Order Form" in checklist_blocks[0]["data"][0]["text"]

def test_convert_department_compliance_items():
    """compliance_items from generator: {name, description, frequency, responsible, documentation}"""
    dept = {
        "department": "Service", "department_id": "service",
        "compliance_items": [
            {"name": "OSHA Safety Training", "description": "Annual certification required for all field technicians",
             "frequency": "Annual", "responsible": "Safety Officer", "documentation": "Training records"}
        ]
    }
    blocks = convert_department_to_blocks(dept)
    checklist_blocks = [b for b in blocks if b["type"] == "checklist"]
    compliance_items = [b for b in checklist_blocks if any("OSHA" in item["text"] for item in b["data"])]
    assert len(compliance_items) >= 1

def test_convert_department_empty():
    dept = {"department": "Empty", "department_id": "empty"}
    blocks = convert_department_to_blocks(dept)
    assert len(blocks) == 1  # just heading
    assert blocks[0]["type"] == "heading"

def test_convert_master_blueprint():
    master = {
        "company_name": "Acme Corp", "industry_tag": "HVAC",
        "stages": [{"id": "s1", "name": "Intake", "duration": "1 day"}],
        "roles": [{"id": "r1", "name": "Technician", "responsibilities": ["Fix things"]}],
        "matrix": {"r1-s1": [{"type": "activity", "text": "Receive job", "detail": "Check dispatch"}]}
    }
    blocks = convert_master_to_blocks(master)
    assert blocks[0]["type"] == "heading"
    card_blocks = [b for b in blocks if b["type"] == "card-grid"]
    assert len(card_blocks) > 0

def test_convert_glossary():
    """glossary from generator uses key "glossary" (not "terms"): [{term, full_form, definition, category}]"""
    glossary = {
        "glossary": [
            {"term": "SLA", "full_form": "Service Level Agreement", "definition": "Contract defining service expectations", "category": "Commercial"},
            {"term": "KPI", "full_form": "Key Performance Indicator", "definition": "Measurable performance metric", "category": "Operations"}
        ]
    }
    blocks = convert_glossary_to_blocks(glossary)
    glossary_blocks = [b for b in blocks if b["type"] == "glossary"]
    assert len(glossary_blocks) == 1
    assert len(glossary_blocks[0]["data"]) == 2
    assert glossary_blocks[0]["data"][0]["term"] == "SLA"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/harshwardhan/blueprint_maker && python -m pytest tests/test_block_converter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'block_converter'`

- [ ] **Step 3: Implement block_converter.py**

```python
# block_converter.py
"""Convert generator JSON output into typed blocks.

IMPORTANT: Data shapes must match the ACTUAL LLM prompt templates in generator.py.
See the Key Data Shape Reference in the plan for exact field names.
"""

from block_types import create_block, generate_block_id


def convert_department_to_blocks(dept: dict) -> list[dict]:
    """Convert a department JSON from generator into a list of blocks."""
    blocks = []
    dept_name = dept.get("department", "Department")

    # Heading
    blocks.append(create_block("heading", {"text": dept_name, "level": 1}))

    # Mission as rich text
    if dept.get("mission"):
        blocks.append(create_block("rich-text", {"html": f"<p><strong>Mission:</strong> {dept['mission']}</p>"}))

    # KPIs — generator shape: {name, target, unit, description, measurement, accountable, color}
    if dept.get("kpis"):
        normalized = []
        for kpi in dept["kpis"]:
            normalized.append({
                "name": kpi.get("name", ""),
                "value": str(kpi.get("value", kpi.get("target", ""))),  # generator uses "target" not "value"
                "target": str(kpi.get("target", "")),
                "unit": kpi.get("unit", ""),
                "trend": kpi.get("trend", "stable"),
            })
        blocks.append(create_block("kpi-grid", normalized))

    # Team structure — generator shape: {role, count, reports_to, key_responsibilities (string)}
    if dept.get("team_structure"):
        roles = []
        for member in dept["team_structure"]:
            # key_responsibilities is a string of bullet points, split it
            resp_str = member.get("key_responsibilities", "")
            if isinstance(resp_str, str):
                responsibilities = [r.strip() for r in resp_str.split(",") if r.strip()]
            else:
                responsibilities = resp_str if isinstance(resp_str, list) else []
            roles.append({
                "id": generate_block_id(),
                "title": member.get("role", member.get("title", "")),
                "reports_to": member.get("reports_to", None),
                "responsibilities": responsibilities,
            })
        blocks.append(create_block("org-chart", {"roles": roles}))

    # Daily timeline — generator shape: {time, block_title, activities: [{title, description, tags, icon}]}
    if dept.get("daily_timeline"):
        timeline_data = []
        for item in dept["daily_timeline"]:
            time_str = item.get("time", "")
            block_title = item.get("block_title", "")
            phase_label = f"{time_str} — {block_title}" if block_title else time_str

            # Activities is a list of {title, description} objects
            activity_strings = []
            for act in item.get("activities", []):
                if isinstance(act, dict):
                    activity_strings.append(f"{act.get('title', '')}: {act.get('description', '')}")
                elif isinstance(act, str):
                    activity_strings.append(act)

            timeline_data.append({
                "phase": phase_label,
                "duration": "",
                "activities": activity_strings,
            })
        blocks.append(create_block("timeline", timeline_data))

    # Workflows — generator shape: {title, target_time, steps: [{title, description, role, color, time, documents, decision_criteria}]}
    for workflow in dept.get("workflows", []):
        wf_name = workflow.get("title", workflow.get("name", "Workflow"))
        blocks.append(create_block("heading", {"text": wf_name, "level": 2}))
        steps = []
        for step in workflow.get("steps", []):
            steps.append({
                "id": step.get("id", generate_block_id()),
                "title": step.get("title", step.get("name", "")),
                "description": step.get("description", ""),
                "type": step.get("color", step.get("type", "activity")),  # generator uses "color" as type indicator
                "assignee": step.get("role", step.get("assignee", "")),
            })
        blocks.append(create_block("workflow", {"steps": steps, "connections": []}))

    # Documents — generator shape: {name, description, fields, frequency, flow, retention, format}
    if dept.get("documents"):
        blocks.append(create_block("heading", {"text": "Documents & Templates", "level": 2}))
        items = []
        for doc in dept["documents"]:
            items.append({
                "text": f"{doc.get('name', '')}: {doc.get('description', '')}",
                "checked": False,
                "priority": "normal",
            })
        blocks.append(create_block("checklist", items))

    # Interactions — generator shape: [{department, inbound: [str], outbound: [str]}]
    # NOTE: This is a LIST of department objects. inbound/outbound contain plain strings, not dicts.
    if dept.get("interactions"):
        nodes = [{"id": "self", "label": dept_name, "type": "center"}]
        edges = []
        node_ids = {"self"}

        for interaction in dept["interactions"]:
            other_dept = interaction.get("department", "Unknown")
            node_id = other_dept.lower().replace(" ", "_")
            if node_id not in node_ids:
                nodes.append({"id": node_id, "label": other_dept, "type": "external"})
                node_ids.add(node_id)

            # inbound is a list of strings like "Receives daily stock reorder alerts..."
            for flow_desc in interaction.get("inbound", []):
                label = flow_desc[:80] + "..." if len(flow_desc) > 80 else flow_desc
                edges.append({"from": node_id, "to": "self", "label": label})

            # outbound is a list of strings
            for flow_desc in interaction.get("outbound", []):
                label = flow_desc[:80] + "..." if len(flow_desc) > 80 else flow_desc
                edges.append({"from": "self", "to": node_id, "label": label})

        blocks.append(create_block("flow-diagram", {"nodes": nodes, "edges": edges}))

    # Escalation matrix — generator shape: {level, title, trigger, description, response_time, resolution_time, authority, actions, examples}
    if dept.get("escalation_matrix"):
        blocks.append(create_block("heading", {"text": "Escalation Matrix", "level": 2}))
        columns = ["Level", "Title", "Trigger", "Response Time", "Authority", "Actions"]
        rows = []
        for esc in dept["escalation_matrix"]:
            actions = esc.get("actions", [])
            actions_str = "; ".join(actions) if isinstance(actions, list) else str(actions)
            rows.append([
                str(esc.get("level", "")),
                esc.get("title", ""),
                esc.get("trigger", ""),
                esc.get("response_time", ""),
                esc.get("authority", ""),
                actions_str,
            ])
        blocks.append(create_block("table", {"columns": columns, "rows": rows}))

    # Compliance items — generator shape: {name, description, frequency, responsible, documentation}
    if dept.get("compliance_items"):
        blocks.append(create_block("heading", {"text": "Compliance Requirements", "level": 2}))
        items = []
        for item in dept["compliance_items"]:
            if isinstance(item, dict):
                text = f"{item.get('name', '')}: {item.get('description', '')}"
            else:
                text = str(item)
            items.append({"text": text, "checked": False, "priority": "high"})
        blocks.append(create_block("checklist", items))

    return blocks


def convert_master_to_blocks(master: dict) -> list[dict]:
    """Convert master blueprint JSON into blocks for the master section."""
    blocks = []
    company = master.get("company_name", "Company")
    blocks.append(create_block("heading", {"text": f"{company} — Service Blueprint", "level": 1}))

    # Stages as timeline
    if master.get("stages"):
        timeline = [{"phase": s.get("name", ""), "duration": s.get("duration", ""), "activities": []} for s in master["stages"]]
        blocks.append(create_block("timeline", timeline))

    # Matrix as card-grid, grouped by role
    matrix = master.get("matrix", {})
    for role in master.get("roles", []):
        role_id = role.get("id", "")
        cards = []
        for stage in master.get("stages", []):
            stage_id = stage.get("id", "")
            items_data = matrix.get(f"{role_id}-{stage_id}", [])
            items = [item.get("text", "") for item in items_data] if items_data else []
            card_type = items_data[0].get("type", "activity") if items_data else "activity"
            cards.append({"title": stage.get("name", ""), "type": card_type, "items": items})
        blocks.append(create_block("heading", {"text": role.get("name", ""), "level": 2}))
        blocks.append(create_block("card-grid", cards))

    return blocks


def convert_glossary_to_blocks(glossary: dict) -> list[dict]:
    """Convert glossary JSON into blocks.
    NOTE: Generator uses key "glossary" not "terms".
    Shape: [{term, full_form, definition, category}]
    """
    blocks = []
    blocks.append(create_block("heading", {"text": "Glossary", "level": 1}))

    # Generator uses "glossary" key, not "terms"
    terms = glossary.get("glossary", glossary.get("terms", []))
    glossary_data = []
    for term in terms:
        glossary_data.append({
            "term": term.get("term", ""),
            "definition": term.get("definition", ""),
            "related": term.get("related", []),
        })
    if glossary_data:
        blocks.append(create_block("glossary", glossary_data))

    # Additional glossary sections as rich text
    for key in ["cross_department_processes", "general_policies", "technology_landscape",
                "risk_register", "meeting_cadences"]:
        items = glossary.get(key, [])
        if items and isinstance(items, list):
            heading = key.replace("_", " ").title()
            blocks.append(create_block("heading", {"text": heading, "level": 2}))
            html_parts = []
            for item in items:
                if isinstance(item, dict):
                    name = item.get("name", item.get("term", item.get("meeting", item.get("risk", ""))))
                    desc = item.get("description", item.get("definition", item.get("agenda", "")))
                    html_parts.append(f"<p><strong>{name}</strong>: {desc}</p>")
            if html_parts:
                blocks.append(create_block("rich-text", {"html": "\n".join(html_parts)}))

    return blocks
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/harshwardhan/blueprint_maker && python -m pytest tests/test_block_converter.py -v`
Expected: All 12 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add block_converter.py tests/test_block_converter.py
git commit -m "feat: add block converter to transform generator output to blocks"
```

---

## Chunk 3: Block Renderer (Blocks → HTML)

### Task 3: Render blocks to HTML fragments

**Files:**
- Create: `block_renderer.py`
- Create: `tests/test_block_renderer.py`

- [ ] **Step 1: Write tests for block renderer**

```python
# tests/test_block_renderer.py
import pytest
from block_renderer import render_block, render_section_to_html, CURRENT_RENDERER_VERSION

def test_renderer_version_exists():
    assert isinstance(CURRENT_RENDERER_VERSION, int)
    assert CURRENT_RENDERER_VERSION >= 1

def test_render_heading():
    block = {"type": "heading", "data": {"text": "Service Department", "level": 1}, "style": {}}
    html = render_block(block)
    assert "<h1" in html
    assert "Service Department" in html

def test_render_heading_level_2():
    block = {"type": "heading", "data": {"text": "Workflows", "level": 2}, "style": {}}
    html = render_block(block)
    assert "<h2" in html

def test_render_rich_text():
    block = {"type": "rich-text", "data": {"html": "<p>Some description</p>"}, "style": {}}
    html = render_block(block)
    assert "<p>Some description</p>" in html

def test_render_kpi_grid():
    block = {"type": "kpi-grid", "data": [{"name": "Revenue", "value": "100K", "target": "120K", "unit": "$", "trend": "up"}], "style": {}}
    html = render_block(block)
    assert "Revenue" in html
    assert "100K" in html

def test_render_workflow():
    block = {"type": "workflow", "data": {"steps": [{"id": "s1", "title": "Receive call", "description": "Answer phone", "type": "activity", "assignee": "Rep"}], "connections": []}, "style": {}}
    html = render_block(block)
    assert "Receive call" in html

def test_render_checklist():
    block = {"type": "checklist", "data": [{"text": "Complete form", "checked": False, "priority": "normal"}], "style": {}}
    html = render_block(block)
    assert "Complete form" in html

def test_render_table():
    block = {"type": "table", "data": {"columns": ["Name", "Value"], "rows": [["Revenue", "100K"]]}, "style": {}}
    html = render_block(block)
    assert "<table" in html
    assert "Revenue" in html

def test_render_timeline():
    block = {"type": "timeline", "data": [{"phase": "8:00 AM", "duration": "30 min", "activities": ["Morning briefing"]}], "style": {}}
    html = render_block(block)
    assert "8:00 AM" in html

def test_render_card_grid():
    block = {"type": "card-grid", "data": [{"title": "Intake", "type": "activity", "items": ["Receive job"]}], "style": {}}
    html = render_block(block)
    assert "Intake" in html

def test_render_glossary():
    block = {"type": "glossary", "data": [{"term": "SLA", "definition": "Service Level Agreement", "related": []}], "style": {}}
    html = render_block(block)
    assert "SLA" in html

def test_render_divider():
    block = {"type": "divider", "data": {"style": "solid"}, "style": {}}
    html = render_block(block)
    assert "<hr" in html

def test_render_org_chart():
    block = {"type": "org-chart", "data": {"roles": [{"id": "r1", "title": "Manager", "reports_to": None, "responsibilities": ["Lead team"]}]}, "style": {}}
    html = render_block(block)
    assert "Manager" in html

def test_render_flow_diagram():
    block = {"type": "flow-diagram", "data": {"nodes": [{"id": "a", "label": "Sales", "type": "external"}], "edges": [{"from": "a", "to": "b", "label": "Lead handoff"}]}, "style": {}}
    html = render_block(block)
    assert "Sales" in html

def test_render_unknown_type():
    block = {"type": "unknown", "data": {}, "style": {}}
    html = render_block(block)
    assert html != ""  # graceful fallback

def test_render_section_to_html():
    section = {"title": "Service", "blocks": [{"type": "heading", "data": {"text": "Test", "level": 1}, "style": {}}]}
    html = render_section_to_html(section)
    assert "<!DOCTYPE html>" in html
    assert "<style>" in html
    assert "</html>" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/harshwardhan/blueprint_maker && python -m pytest tests/test_block_renderer.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement block_renderer.py**

```python
# block_renderer.py
"""Render blocks to HTML fragments and full sections to standalone HTML pages."""

import html as html_lib

CURRENT_RENDERER_VERSION = 1

# CSS matching existing blueprint design from renderer.py
BLOCK_CSS = """
:root {
  --bg: #F8FAFC; --surface: #FFFFFF; --text: #1E293B; --text-light: #64748B;
  --brand: #2563EB; --brand-dark: #1E40AF; --accent: #3B82F6;
  --green: #10B981; --green-bg: #ECFDF5; --amber: #F59E0B; --amber-bg: #FFFBEB;
  --red: #EF4444; --red-bg: #FEF2F2; --purple: #8B5CF6; --purple-bg: #F5F3FF;
  --teal: #14B8A6; --teal-bg: #F0FDFA; --blue-bg: #EFF6FF;
  --border: #E2E8F0; --radius: 8px; --shadow: 0 1px 3px rgba(0,0,0,0.1);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: var(--bg); color: var(--text); line-height: 1.6; padding: 2rem; }
.block { margin-bottom: 1.5rem; }
h1,h2,h3,h4 { color: var(--brand-dark); margin-bottom: 0.75rem; }
h1 { font-size: 1.75rem; border-bottom: 3px solid var(--brand); padding-bottom: 0.5rem; }
h2 { font-size: 1.35rem; border-bottom: 2px solid var(--border); padding-bottom: 0.4rem; }
h3 { font-size: 1.15rem; } h4 { font-size: 1rem; }
.rich-text p { margin-bottom: 0.5rem; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }
.kpi-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
            padding: 1rem; box-shadow: var(--shadow); }
.kpi-card .name { font-size: 0.85rem; color: var(--text-light); text-transform: uppercase; }
.kpi-card .value { font-size: 1.5rem; font-weight: 700; color: var(--brand); }
.kpi-card .target { font-size: 0.8rem; color: var(--text-light); }
.kpi-card .trend-up { color: var(--green); } .kpi-card .trend-down { color: var(--red); }
.workflow-steps { display: flex; flex-direction: column; gap: 0.75rem; }
.wf-step { display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.75rem;
           background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); }
.step-num { width: 28px; height: 28px; border-radius: 50%; background: var(--brand); color: white;
            display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 600; flex-shrink: 0; }
.step-type-blue .step-num { background: var(--accent); }
.step-type-green .step-num { background: var(--green); }
.step-type-orange .step-num { background: var(--amber); }
.step-type-red .step-num { background: var(--red); }
.step-type-purple .step-num { background: var(--purple); }
.step-body .title { font-weight: 600; } .step-body .desc { font-size: 0.9rem; color: var(--text-light); }
.step-body .assignee { font-size: 0.8rem; color: var(--accent); margin-top: 0.25rem; }
.checklist { list-style: none; }
.checklist li { padding: 0.5rem 0; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 0.5rem; }
.checklist .chk { width: 16px; height: 16px; border: 2px solid var(--border); border-radius: 3px; flex-shrink: 0; }
.checklist .chk.checked { background: var(--green); border-color: var(--green); }
.checklist .priority-high { border-left: 3px solid var(--red); padding-left: 0.5rem; }
table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: var(--radius);
        overflow: hidden; box-shadow: var(--shadow); }
th { background: var(--brand); color: white; padding: 0.75rem; text-align: left; font-weight: 600; }
td { padding: 0.75rem; border-bottom: 1px solid var(--border); }
tr:hover { background: var(--blue-bg); }
.timeline { display: flex; flex-direction: column; position: relative; padding-left: 2rem; }
.timeline::before { content: ''; position: absolute; left: 0.75rem; top: 0; bottom: 0; width: 2px; background: var(--brand); }
.tl-item { position: relative; padding: 0.75rem 0; }
.tl-item::before { content: ''; position: absolute; left: -1.65rem; top: 1rem;
                   width: 12px; height: 12px; border-radius: 50%; background: var(--brand); border: 2px solid white; }
.tl-item .phase { font-weight: 600; color: var(--brand); }
.tl-item .duration { font-size: 0.85rem; color: var(--text-light); }
.tl-item .activities { font-size: 0.9rem; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 0.75rem; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
        padding: 0.75rem; box-shadow: var(--shadow); }
.card.type-activity { border-left: 3px solid var(--accent); }
.card.type-document { border-left: 3px solid var(--green); }
.card.type-approval { border-left: 3px solid var(--amber); }
.card.type-critical { border-left: 3px solid var(--red); }
.card.type-handover { border-left: 3px solid var(--purple); }
.card .card-title { font-weight: 600; font-size: 0.9rem; margin-bottom: 0.4rem; }
.card .card-item { font-size: 0.85rem; color: var(--text-light); }
.glossary-list { display: grid; gap: 0.75rem; }
.gl-entry { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem; }
.gl-entry .term { font-weight: 700; color: var(--brand); }
.gl-entry .definition { margin-top: 0.25rem; }
.gl-entry .related { font-size: 0.8rem; color: var(--text-light); margin-top: 0.25rem; }
.org-chart { display: flex; flex-direction: column; gap: 0.75rem; }
.org-role { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
            padding: 1rem; box-shadow: var(--shadow); }
.org-role .role-title { font-weight: 700; color: var(--brand); font-size: 1.1rem; }
.org-role .reports-to { font-size: 0.85rem; color: var(--text-light); }
.org-role .responsibilities { margin-top: 0.5rem; padding-left: 1.25rem; }
.org-role .responsibilities li { font-size: 0.9rem; margin-bottom: 0.25rem; }
.flow-diagram { display: flex; flex-wrap: wrap; gap: 1rem; align-items: center; justify-content: center; }
.flow-node { background: var(--surface); border: 2px solid var(--brand); border-radius: var(--radius);
             padding: 0.75rem 1.25rem; font-weight: 600; text-align: center; min-width: 100px; }
.flow-node.type-center { background: var(--brand); color: white; }
.flow-edges { width: 100%; }
.flow-edge { display: flex; align-items: center; gap: 0.5rem; padding: 0.35rem 0;
             font-size: 0.9rem; color: var(--text-light); }
.flow-edge .arrow { color: var(--brand); font-weight: bold; }
hr.divider { border: none; margin: 1.5rem 0; }
hr.divider-solid { border-top: 2px solid var(--border); }
hr.divider-dashed { border-top: 2px dashed var(--border); }
hr.divider-dotted { border-top: 2px dotted var(--border); }
"""


def _esc(text):
    return html_lib.escape(str(text)) if text else ""


def _render_heading(data, style):
    level = min(max(data.get("level", 1), 1), 4)
    return f'<div class="block block-heading"><h{level}>{_esc(data.get("text", ""))}</h{level}></div>'

def _render_rich_text(data, style):
    return f'<div class="block block-rich-text rich-text">{data.get("html", "")}</div>'

def _render_kpi_grid(data, style):
    cards = []
    for kpi in data:
        trend = kpi.get("trend", "")
        trend_cls = "trend-up" if trend == "up" else ("trend-down" if trend == "down" else "")
        unit = _esc(kpi.get("unit", ""))
        cards.append(f'''<div class="kpi-card">
<div class="name">{_esc(kpi.get("name",""))}</div>
<div class="value {trend_cls}">{unit}{_esc(kpi.get("value",""))}</div>
<div class="target">Target: {unit}{_esc(kpi.get("target",""))}</div></div>''')
    return f'<div class="block block-kpi-grid kpi-grid">{"".join(cards)}</div>'

def _render_workflow(data, style):
    steps = []
    for i, step in enumerate(data.get("steps", []), 1):
        stype = _esc(step.get("type", "activity"))
        steps.append(f'''<div class="wf-step step-type-{stype}">
<div class="step-num">{i}</div>
<div class="step-body"><div class="title">{_esc(step.get("title",""))}</div>
<div class="desc">{_esc(step.get("description",""))}</div>
<div class="assignee">{_esc(step.get("assignee",""))}</div></div></div>''')
    return f'<div class="block block-workflow workflow-steps">{"".join(steps)}</div>'

def _render_checklist(data, style):
    items = []
    for item in data:
        chk = "checked" if item.get("checked") else ""
        pri = item.get("priority", "normal")
        pri_cls = f"priority-{pri}" if pri != "normal" else ""
        items.append(f'<li class="{pri_cls}"><span class="chk {chk}"></span><span>{_esc(item.get("text",""))}</span></li>')
    return f'<div class="block block-checklist"><ul class="checklist">{"".join(items)}</ul></div>'

def _render_table(data, style):
    headers = "".join(f"<th>{_esc(c)}</th>" for c in data.get("columns", []))
    rows = "".join("<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in row) + "</tr>" for row in data.get("rows", []))
    return f'<div class="block block-table"><table><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table></div>'

def _render_timeline(data, style):
    items = []
    for item in data:
        acts = ", ".join(_esc(a) for a in item.get("activities", []))
        items.append(f'''<div class="tl-item"><div class="phase">{_esc(item.get("phase",""))}</div>
<div class="duration">{_esc(item.get("duration",""))}</div>
<div class="activities">{acts}</div></div>''')
    return f'<div class="block block-timeline timeline">{"".join(items)}</div>'

def _render_card_grid(data, style):
    cards = []
    for card in data:
        ctype = _esc(card.get("type", "activity"))
        items_html = "".join(f'<div class="card-item">{_esc(i)}</div>' for i in card.get("items", []))
        cards.append(f'<div class="card type-{ctype}"><div class="card-title">{_esc(card.get("title",""))}</div>{items_html}</div>')
    return f'<div class="block block-card-grid card-grid">{"".join(cards)}</div>'

def _render_glossary(data, style):
    entries = []
    for e in data:
        related = ", ".join(_esc(r) for r in e.get("related", []))
        rel_html = f'<div class="related">Related: {related}</div>' if related else ""
        entries.append(f'''<div class="gl-entry"><div class="term">{_esc(e.get("term",""))}</div>
<div class="definition">{_esc(e.get("definition",""))}</div>{rel_html}</div>''')
    return f'<div class="block block-glossary glossary-list">{"".join(entries)}</div>'

def _render_divider(data, style):
    s = _esc(data.get("style", "solid"))
    return f'<hr class="block divider divider-{s}">'

def _render_org_chart(data, style):
    roles = []
    for role in data.get("roles", []):
        reports = f'<div class="reports-to">Reports to: {_esc(role.get("reports_to",""))}</div>' if role.get("reports_to") else ""
        resp = "".join(f"<li>{_esc(r)}</li>" for r in role.get("responsibilities", []))
        resp_html = f'<ul class="responsibilities">{resp}</ul>' if resp else ""
        roles.append(f'<div class="org-role"><div class="role-title">{_esc(role.get("title",""))}</div>{reports}{resp_html}</div>')
    return f'<div class="block block-org-chart org-chart">{"".join(roles)}</div>'

def _render_flow_diagram(data, style):
    nodes_html = []
    for n in data.get("nodes", []):
        t = f"type-{n.get('type','external')}"
        nodes_html.append(f'<div class="flow-node {t}">{_esc(n.get("label",""))}</div>')
    node_map = {n["id"]: n.get("label", n["id"]) for n in data.get("nodes", [])}
    edges_html = []
    for e in data.get("edges", []):
        src = _esc(node_map.get(e.get("from",""), e.get("from","")))
        dst = _esc(node_map.get(e.get("to",""), e.get("to","")))
        edges_html.append(f'<div class="flow-edge">{src} <span class="arrow">&rarr;</span> {dst}: {_esc(e.get("label",""))}</div>')
    return f'<div class="block block-flow-diagram flow-diagram">{"".join(nodes_html)}<div class="flow-edges">{"".join(edges_html)}</div></div>'


BLOCK_RENDERERS = {
    "heading": _render_heading, "rich-text": _render_rich_text, "kpi-grid": _render_kpi_grid,
    "workflow": _render_workflow, "checklist": _render_checklist, "table": _render_table,
    "timeline": _render_timeline, "card-grid": _render_card_grid, "glossary": _render_glossary,
    "divider": _render_divider, "org-chart": _render_org_chart, "flow-diagram": _render_flow_diagram,
}


def render_block(block: dict) -> str:
    """Render a single block to an HTML fragment."""
    renderer = BLOCK_RENDERERS.get(block.get("type", ""))
    if not renderer:
        return f'<div class="block block-unknown">Unknown block type: {_esc(block.get("type",""))}</div>'
    return renderer(block.get("data", {}), block.get("style", {}))


def render_section_to_html(section: dict) -> str:
    """Render a full section to a standalone HTML file."""
    title = _esc(section.get("title", "Blueprint Section"))
    blocks_html = "\n".join(render_block(b) for b in section.get("blocks", []))
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{BLOCK_CSS}</style>
</head>
<body>
{blocks_html}
</body>
</html>'''
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/harshwardhan/blueprint_maker && python -m pytest tests/test_block_renderer.py -v`
Expected: All 16 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add block_renderer.py tests/test_block_renderer.py
git commit -m "feat: add block renderer for HTML fragment generation"
```

---

## Chunk 4: Firestore Section CRUD

### Task 4: Add section CRUD to db.py

**Files:**
- Modify: `db.py`
- Modify: `config.py`

- [ ] **Step 1: Add CURRENT_RENDERER_VERSION to config.py**

Add at end of `config.py`:

```python
# Block renderer version — increment when block renderers change
CURRENT_RENDERER_VERSION = 1
```

- [ ] **Step 2: Update create_blueprint in db.py**

Add three new fields to the blueprint document in `create_blueprint()`. Find the dict passed to `ref.set(...)` and add:

```python
"format": "blocks",
"renderer_version": 1,
"section_order": [],
```

- [ ] **Step 3: Add section CRUD functions to db.py**

Add at end of `db.py`. Note: follows existing pattern — each function calls `get_firestore_client()` locally, uses `_now()` for timestamps, wraps in try/except.

```python
# ─── Sections (subcollection under blueprints) ─────────────────────────


def create_section(blueprint_id: str, section_id: str, title: str, icon: str,
                   position: int, blocks: list[dict]) -> str:
    """Create a section in a blueprint's sections subcollection."""
    try:
        db = get_firestore_client()
        doc_ref = db.collection("blueprints").document(blueprint_id).collection("sections").document(section_id)
        doc_ref.set({
            "title": title,
            "icon": icon,
            "position": position,
            "blocks": blocks,
            "created_at": _now(),
            "updated_at": _now(),
        })
        return section_id
    except GoogleAPICallError as e:
        logger.error("Failed to create section %s in blueprint %s: %s", section_id, blueprint_id, e)
        raise


def get_section(blueprint_id: str, section_id: str) -> dict | None:
    """Get a single section by ID."""
    try:
        db = get_firestore_client()
        doc = db.collection("blueprints").document(blueprint_id).collection("sections").document(section_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    except GoogleAPICallError as e:
        logger.error("Failed to get section %s: %s", section_id, e)
        return None


def list_sections(blueprint_id: str) -> list[dict]:
    """List all sections for a blueprint, ordered by position."""
    try:
        db = get_firestore_client()
        docs = db.collection("blueprints").document(blueprint_id).collection("sections").order_by("position").stream()
        sections = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            sections.append(data)
        return sections
    except GoogleAPICallError as e:
        logger.error("Failed to list sections for blueprint %s: %s", blueprint_id, e)
        return []


def update_section(blueprint_id: str, section_id: str, data: dict) -> None:
    """Update a section's fields."""
    try:
        db = get_firestore_client()
        data["updated_at"] = _now()
        db.collection("blueprints").document(blueprint_id).collection("sections").document(section_id).update(data)
    except GoogleAPICallError as e:
        logger.error("Failed to update section %s: %s", section_id, e)
        raise


def delete_all_sections(blueprint_id: str) -> None:
    """Delete all sections for a blueprint."""
    try:
        db = get_firestore_client()
        docs = db.collection("blueprints").document(blueprint_id).collection("sections").stream()
        for doc in docs:
            doc.reference.delete()
    except GoogleAPICallError as e:
        logger.error("Failed to delete sections for blueprint %s: %s", blueprint_id, e)


def update_section_order(blueprint_id: str, section_order: list[str]) -> None:
    """Update the section_order array on the blueprint document."""
    try:
        db = get_firestore_client()
        db.collection("blueprints").document(blueprint_id).update({
            "section_order": section_order,
            "updated_at": _now(),
        })
    except GoogleAPICallError as e:
        logger.error("Failed to update section order for blueprint %s: %s", blueprint_id, e)
        raise
```

- [ ] **Step 4: Update delete_blueprint in db.py**

At the beginning of the existing `delete_blueprint` function, before deleting the blueprint doc itself, add:

```python
# Delete sections subcollection first
delete_all_sections(blueprint_id)
```

- [ ] **Step 5: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add db.py config.py
git commit -m "feat: add section CRUD to db.py, update blueprint schema for blocks"
```

---

## Chunk 5: Wire Generation Pipeline to Blocks

### Task 5: Modify generator.py and server.py to output blocks

**Files:**
- Modify: `generator.py` (change return value of `generate_blueprint_kit`)
- Modify: `server.py` (update `_persist_blueprint_to_firebase`, add block-saving logic)

- [ ] **Step 1: Modify generate_blueprint_kit to return raw results**

In `generator.py`, modify `generate_blueprint_kit` (line 585) to capture and return raw JSON alongside HTML files. The function currently returns `files` (a list). Change it to always return a tuple `(files, raw_results)`.

At the top of the function, add variables to collect raw results:

```python
raw_master = None
raw_departments = []
raw_glossary = None
```

After `master = await generate_master_blueprint(context, research)` (line 595), add:

```python
raw_master = master
```

Inside the department generation loop, after the result is successfully rendered (line 620), add:

```python
raw_departments.append(result)
```

After glossary generation (line 628-629), add:

```python
raw_glossary = glossary_data
```

Change the return statement (line 634) from:

```python
return files
```

To:

```python
raw_results = {"master": raw_master, "departments": raw_departments, "glossary": raw_glossary}
return files, raw_results
```

- [ ] **Step 2: Update _run_generation in server.py**

In `server.py`, find `_run_generation` where it calls `generate_blueprint_kit`. Currently (around line 547):

```python
files = await generate_blueprint_kit(context, research, progress_cb=progress_cb)
```

Change to:

```python
files, raw_results = await generate_blueprint_kit(context, research, progress_cb=progress_cb)
```

Then store `raw_results` in the session:

```python
session["raw_results"] = raw_results
```

- [ ] **Step 3: Add block-saving to _persist_blueprint_to_firebase**

`_persist_blueprint_to_firebase` is a **synchronous** function (line 257). We cannot use `await` inside it. Add the block-saving logic as synchronous code.

Add imports at the top of the function (inside the try block, alongside existing lazy imports):

```python
from block_converter import convert_department_to_blocks, convert_master_to_blocks, convert_glossary_to_blocks
from block_renderer import render_block, CURRENT_RENDERER_VERSION
from block_types import slugify
from db import create_section, update_section_order
```

After the existing `update_blueprint(bp_id, {...})` call (line 277-283), add the block-saving logic:

```python
# Save blocks to Firestore sections
try:
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
    # Legacy HTML files are already uploaded — blueprint still works
```

- [ ] **Step 4: Update generate/status to return blueprint_id**

In the `/api/generate/status/{session_id}` handler, find the response dict for status `"generated"` and ensure it includes:

```python
"blueprint_id": session.get("blueprint_id"),
```

- [ ] **Step 5: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add generator.py server.py
git commit -m "feat: wire generation pipeline to output blocks to Firestore"
```

---

## Chunk 6: Section API Endpoints + Export ZIP

### Task 6: Add section read endpoints and export/zip

**Files:**
- Modify: `server.py`

All new endpoints follow existing patterns: lazy imports from `db` and `auth`, call `enforce_rate_limit(request)`.

- [ ] **Step 1: Add section list endpoint**

```python
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
```

- [ ] **Step 2: Add section detail endpoint**

```python
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
```

- [ ] **Step 3: Add section update endpoint**

```python
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
```

- [ ] **Step 4: Add section order endpoint**

```python
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
```

- [ ] **Step 5: Add export/zip endpoint**

```python
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
```

- [ ] **Step 6: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add server.py
git commit -m "feat: add section CRUD endpoints and ZIP export from blocks"
```

---

## Chunk 7: Integration Test

### Task 7: End-to-end test of the block pipeline

**Files:**
- Create: `tests/test_block_pipeline.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_block_pipeline.py
"""Integration test: generator JSON → blocks → HTML → section HTML page.
Uses ACTUAL data shapes from generator.py LLM prompts."""
import pytest
from block_converter import convert_department_to_blocks, convert_master_to_blocks, convert_glossary_to_blocks
from block_renderer import render_block, render_section_to_html
from block_types import validate_block, slugify

# Realistic generator output matching actual LLM prompt shapes
SAMPLE_DEPARTMENT = {
    "department": "Service",
    "department_id": "service",
    "mission": "Deliver exceptional field service.",
    "head_role": "Service Manager",
    "team_structure": [
        {"role": "Service Manager", "count": "1", "reports_to": "General Manager",
         "key_responsibilities": "Oversee operations, manage team, handle escalations, review KPIs"},
        {"role": "Dispatcher", "count": "2", "reports_to": "Service Manager",
         "key_responsibilities": "Route technicians, schedule jobs, monitor GPS"},
    ],
    "daily_timeline": [
        {"time": "7:00 AM", "block_title": "Morning Dispatch",
         "activities": [
             {"title": "Morning briefing", "description": "Review day's schedule with team", "tags": ["critical"], "icon": "📋"},
             {"title": "Check equipment", "description": "Verify van inventory and tools", "tags": ["doc"], "icon": "🔧"}
         ]},
    ],
    "workflows": [
        {"title": "Service Call Intake", "target_time": "30 min",
         "steps": [
             {"title": "Receive call", "description": "Log customer details in CRM", "role": "CSR",
              "color": "blue", "time": "5 min", "documents": "Call log", "decision_criteria": ""},
             {"title": "Create work order", "description": "Enter job in field service system", "role": "CSR",
              "color": "green", "time": "10 min", "documents": "Work order form", "decision_criteria": ""},
         ]}
    ],
    "documents": [
        {"name": "Work Order Form", "description": "Track service jobs from dispatch to completion",
         "fields": "customer_name, address, issue_type, technician, date, status",
         "frequency": "Per Job", "flow": "CSR > Dispatcher > Tech", "retention": "5 years", "format": "Digital"},
    ],
    "kpis": [
        {"name": "First-Time Fix Rate", "target": "92%", "unit": "%",
         "description": "Percentage fixed on first visit", "measurement": "Monthly review",
         "accountable": "Service Manager", "color": "green"},
    ],
    "interactions": [
        {"department": "Sales", "inbound": ["Receives new customer handoff with contract details"],
         "outbound": ["Sends service completion report for billing"]},
        {"department": "Accounting", "inbound": ["Receives budget approvals for parts orders"],
         "outbound": ["Sends invoice requests within 24 hours of job completion"]},
    ],
    "escalation_matrix": [
        {"level": 1, "title": "Frontline Resolution", "trigger": "Customer complaint",
         "description": "Team lead handles directly", "response_time": "30 minutes",
         "resolution_time": "2 hours", "authority": "Team Lead",
         "actions": ["Acknowledge complaint", "Document issue", "Propose resolution"],
         "examples": ["Late arrival", "Incomplete work"]},
    ],
    "compliance_items": [
        {"name": "OSHA Safety Training", "description": "Annual safety certification required",
         "frequency": "Annual", "responsible": "Safety Officer", "documentation": "Training records"},
    ],
}


def test_full_department_pipeline():
    blocks = convert_department_to_blocks(SAMPLE_DEPARTMENT)
    assert len(blocks) > 5
    for block in blocks:
        assert validate_block(block), f"Invalid block: {block['type']}"
        html = render_block(block)
        assert len(html) > 0
    section = {"title": "Service Department", "blocks": blocks}
    full_html = render_section_to_html(section)
    assert "<!DOCTYPE html>" in full_html
    assert "Service Manager" in full_html
    assert "First-Time Fix Rate" in full_html

def test_full_master_pipeline():
    master = {
        "company_name": "Acme HVAC", "industry_tag": "HVAC",
        "stages": [{"id": "s1", "name": "Lead", "duration": "1 day"}],
        "roles": [{"id": "r1", "name": "Sales Rep", "responsibilities": ["Generate leads"]}],
        "matrix": {"r1-s1": [{"type": "activity", "text": "Qualify lead", "detail": "Check budget"}]}
    }
    blocks = convert_master_to_blocks(master)
    assert len(blocks) > 0
    for block in blocks:
        assert validate_block(block)

def test_full_glossary_pipeline():
    glossary = {
        "glossary": [  # NOTE: key is "glossary" not "terms"
            {"term": "SLA", "full_form": "Service Level Agreement", "definition": "Contract terms", "category": "Commercial"},
        ]
    }
    blocks = convert_glossary_to_blocks(glossary)
    assert len(blocks) >= 2
    for block in blocks:
        assert validate_block(block)

def test_blocks_have_unique_ids():
    blocks = convert_department_to_blocks(SAMPLE_DEPARTMENT)
    ids = [b["id"] for b in blocks]
    assert len(ids) == len(set(ids))

def test_html_cache_populated():
    blocks = convert_department_to_blocks(SAMPLE_DEPARTMENT)
    for block in blocks:
        block["html_cache"] = render_block(block)
        assert block["html_cache"] != ""
        assert "<" in block["html_cache"]

def test_interactions_produce_correct_edges():
    """Verify interactions (list of dept objects with string arrays) convert correctly."""
    blocks = convert_department_to_blocks(SAMPLE_DEPARTMENT)
    flow_blocks = [b for b in blocks if b["type"] == "flow-diagram"]
    assert len(flow_blocks) == 1
    nodes = flow_blocks[0]["data"]["nodes"]
    edges = flow_blocks[0]["data"]["edges"]
    node_labels = {n["label"] for n in nodes}
    assert "Service" in node_labels
    assert "Sales" in node_labels
    assert "Accounting" in node_labels
    assert len(edges) == 4  # 2 inbound + 2 outbound
```

- [ ] **Step 2: Run all tests**

Run: `cd /home/harshwardhan/blueprint_maker && python -m pytest tests/ -v`
Expected: All tests across all test files PASS

- [ ] **Step 3: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add tests/test_block_pipeline.py
git commit -m "test: add integration tests for block pipeline"
```

---

## Summary

After completing this plan:
1. 12 block types with validation and ID generation
2. Block converter handles ALL generator output shapes correctly (interactions as list, escalation with proper fields, etc.)
3. Block renderer produces styled HTML fragments matching existing blueprint design
4. Section CRUD in Firestore with proper error handling
5. Generation pipeline outputs blocks to Firestore alongside legacy HTML
6. Section API endpoints with auth, rate limiting, and validation
7. ZIP export renders blocks to HTML on demand
8. Full backward compatibility with legacy blueprints

**Next plans:**
- Plan 2: Chat Editing + Questionnaire Flow
- Plan 3: Bug Fixes + Visual Editor + Auto-save
