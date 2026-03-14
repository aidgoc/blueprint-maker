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
