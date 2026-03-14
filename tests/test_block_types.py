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
