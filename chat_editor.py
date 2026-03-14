# chat_editor.py
"""LLM-powered chat editing for block-based blueprints.

Handles: prompt construction, LLM call, response parsing, change application.
"""

import json
import logging
import re
import copy

import httpx

from config import OPENROUTER_API_KEY, EDITOR_MODEL
from block_types import BLOCK_TYPES, create_block

logger = logging.getLogger(__name__)

# Block type schemas for the LLM prompt
BLOCK_SCHEMAS = {
    "heading": '{"text": "string", "level": 1-4}',
    "rich-text": '{"html": "string"}',
    "kpi-grid": '[{"name": "string", "value": "string", "target": "string", "unit": "string", "trend": "up|down|stable"}]',
    "workflow": '{"steps": [{"id": "string", "title": "string", "description": "string", "type": "activity|document|approval|critical|handover", "assignee": "string"}], "connections": []}',
    "checklist": '[{"text": "string", "checked": false, "priority": "normal|high|low"}]',
    "table": '{"columns": ["string"], "rows": [["string"]]}',
    "timeline": '[{"phase": "string", "duration": "string", "activities": ["string"]}]',
    "card-grid": '[{"title": "string", "type": "activity|document|approval|critical|handover", "items": ["string"]}]',
    "glossary": '[{"term": "string", "definition": "string", "related": ["string"]}]',
    "divider": '{"style": "solid|dashed|dotted"}',
    "org-chart": '{"roles": [{"id": "string", "title": "string", "reports_to": "string|null", "responsibilities": ["string"]}]}',
    "flow-diagram": '{"nodes": [{"id": "string", "label": "string", "type": "center|external"}], "edges": [{"from": "string", "to": "string", "label": "string"}]}',
}

SYSTEM_PROMPT = """You are a blueprint editor AI. You modify business blueprint sections based on user instructions.

You receive:
1. A list of all sections (titles + IDs) for context
2. The current section's blocks (structured data, no HTML)
3. Recent chat history
4. The user's editing instruction

You return a JSON object with your changes:

{
  "sections": [
    {
      "section_id": "the_section_id",
      "changes": [
        {"block_id": "existing_block_id", "action": "update", "data": { ...full updated data... }},
        {"block_id": "new_unique_id", "action": "add", "after": "block_id_to_insert_after", "type": "block_type", "data": { ...data... }},
        {"block_id": "block_to_remove", "action": "delete"}
      ]
    }
  ],
  "response": "Brief description of what you changed."
}

Rules:
- For "update": include the FULL updated data object, not a partial diff
- For "add": generate a unique block_id starting with "b_", specify the "type" and full "data"
- For "delete": only include block_id and action
- Only modify blocks that need changing — leave others untouched
- If the instruction affects multiple sections, include multiple entries in "sections"
- If the instruction is unclear, ask for clarification in "response" with empty "sections": []

Available block types and their data schemas:
"""


def build_edit_prompt(all_sections: list[dict], current_blocks: list[dict],
                      current_section_id: str, chat_history: list[dict],
                      instruction: str) -> str:
    """Build the LLM prompt for chat editing."""

    # Section overview (titles only)
    section_list = "\n".join(f"- {s['id']}: {s['title']}" for s in all_sections)

    # Current section blocks (strip html_cache to save tokens)
    clean_blocks = []
    for block in current_blocks:
        clean = {k: v for k, v in block.items() if k != "html_cache"}
        clean_blocks.append(clean)
    blocks_json = json.dumps(clean_blocks, indent=2)

    # Recent chat history (last 10)
    history_text = ""
    if chat_history:
        recent = chat_history[-10:]
        lines = []
        for msg in recent:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        history_text = "\n".join(lines)

    history_section = ""
    if history_text:
        history_section = "Recent chat history:\n" + history_text + "\n\n"

    prompt = f"""All sections in this blueprint:
{section_list}

Currently viewing section: {current_section_id}

Current section blocks:
{blocks_json}

{history_section}User instruction: {instruction}

Return ONLY valid JSON matching the schema above."""

    return prompt


def _build_system_prompt() -> str:
    """Build system prompt with block type schemas."""
    schemas = "\n".join(f"- {name}: {schema}" for name, schema in BLOCK_SCHEMAS.items())
    return SYSTEM_PROMPT + schemas


async def call_edit_llm(prompt: str, model: str = None) -> str:
    """Call LLM via OpenRouter for editing."""
    model = model or EDITOR_MODEL
    system = _build_system_prompt()

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 8000,
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def parse_edit_response(raw: str) -> dict | None:
    """Parse LLM response into structured changes. Returns None if unparseable."""
    # Strip markdown code block wrappers
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        result = json.loads(text)
        if "sections" in result and "response" in result:
            return result
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            result = json.loads(match.group())
            if "sections" in result and "response" in result:
                return result
        except json.JSONDecodeError:
            pass

    logger.warning("Failed to parse edit response: %s", raw[:200])
    return None


def apply_changes_to_blocks(blocks: list[dict], changes: list[dict]) -> tuple[list[dict], list[dict]]:
    """Apply a list of changes to blocks. Returns (updated_blocks, undo_entries).

    Changes are: update, add, delete.
    Invalid block_ids are silently skipped.
    """
    blocks = copy.deepcopy(blocks)
    undo_entries = []
    block_map = {b["id"]: i for i, b in enumerate(blocks)}

    for change in changes:
        block_id = change.get("block_id")
        action = change.get("action")

        if action == "update":
            idx = block_map.get(block_id)
            if idx is None:
                continue
            before = copy.deepcopy(blocks[idx]["data"])
            blocks[idx]["data"] = change["data"]
            undo_entries.append({
                "block_id": block_id,
                "action": "update",
                "before": before,
                "after": copy.deepcopy(change["data"]),
            })

        elif action == "add":
            after_id = change.get("after")
            new_block = {
                "id": block_id,
                "type": change.get("type", "rich-text"),
                "data": change.get("data", {}),
                "style": {"color_scheme": "default", "layout": "default", "custom_css": None},
                "html_cache": "",
            }
            if after_id and after_id in block_map:
                insert_idx = block_map[after_id] + 1
            else:
                insert_idx = 0

            blocks.insert(insert_idx, new_block)
            # Rebuild index
            block_map = {b["id"]: i for i, b in enumerate(blocks)}
            undo_entries.append({
                "block_id": block_id,
                "action": "add",
                "before": None,
                "after": copy.deepcopy(new_block["data"]),
            })

        elif action == "delete":
            idx = block_map.get(block_id)
            if idx is None:
                continue
            before = copy.deepcopy(blocks[idx]["data"])
            blocks.pop(idx)
            block_map = {b["id"]: i for i, b in enumerate(blocks)}
            undo_entries.append({
                "block_id": block_id,
                "action": "delete",
                "before": before,
                "after": None,
            })

    return blocks, undo_entries
