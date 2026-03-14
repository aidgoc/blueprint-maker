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
                 {"title": "Morning briefing", "description": "Review day's schedule", "tags": ["critical"], "icon": "\U0001f4cb"},
                 {"title": "Check equipment", "description": "Verify van inventory", "tags": ["doc"], "icon": "\U0001f527"}
             ]}
        ]
    }
    blocks = convert_department_to_blocks(dept)
    timeline_blocks = [b for b in blocks if b["type"] == "timeline"]
    assert len(timeline_blocks) == 1
    item = timeline_blocks[0]["data"][0]
    assert item["phase"] == "7:00 AM \u2014 Morning Prep"
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
    """interactions from generator: [{department, inbound: [str], outbound: [str]}] -- list of dept objects with STRING arrays"""
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
