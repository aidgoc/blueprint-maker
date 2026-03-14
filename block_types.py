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
