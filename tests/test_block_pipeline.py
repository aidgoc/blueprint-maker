# tests/test_block_pipeline.py
"""Integration test: generator JSON -> blocks -> HTML -> section HTML page.
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
             {"title": "Morning briefing", "description": "Review day's schedule with team", "tags": ["critical"], "icon": "\U0001f4cb"},
             {"title": "Check equipment", "description": "Verify van inventory and tools", "tags": ["doc"], "icon": "\U0001f527"}
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
