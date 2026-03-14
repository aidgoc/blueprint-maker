# tests/test_chat_editor.py
import pytest
import json
from chat_editor import build_edit_prompt, parse_edit_response, apply_changes_to_blocks

def test_build_edit_prompt_includes_instruction():
    sections = [{"id": "service", "title": "Service Department"}]
    blocks = [
        {"id": "b_001", "type": "heading", "data": {"text": "Service", "level": 1}},
        {"id": "b_002", "type": "workflow", "data": {"steps": [{"id": "s1", "title": "Step 1", "description": "Do thing", "type": "activity", "assignee": "Tech"}], "connections": []}},
    ]
    chat_history = []
    instruction = "Add a quality check step after Step 1"

    prompt = build_edit_prompt(sections, blocks, "service", chat_history, instruction)
    assert "Add a quality check step" in prompt
    assert "service" in prompt.lower()
    assert "b_001" in prompt
    assert "b_002" in prompt

def test_build_edit_prompt_strips_html_cache():
    """html_cache should NOT be sent to the LLM (wastes tokens)."""
    sections = [{"id": "service", "title": "Service"}]
    blocks = [{"id": "b_001", "type": "heading", "data": {"text": "Test", "level": 1}, "html_cache": "<h1>Test</h1>"}]
    prompt = build_edit_prompt(sections, blocks, "service", [], "edit something")
    assert "html_cache" not in prompt
    assert "<h1>Test</h1>" not in prompt

def test_parse_edit_response_valid():
    raw = json.dumps({
        "sections": [
            {"section_id": "service", "changes": [
                {"block_id": "b_002", "action": "update", "data": {"steps": [{"id": "s1", "title": "Updated Step", "description": "New desc", "type": "activity", "assignee": "Tech"}], "connections": []}}
            ]}
        ],
        "response": "Updated the step."
    })
    result = parse_edit_response(raw)
    assert result["response"] == "Updated the step."
    assert len(result["sections"]) == 1
    assert result["sections"][0]["section_id"] == "service"

def test_parse_edit_response_with_markdown_wrapper():
    raw = '```json\n{"sections": [{"section_id": "s", "changes": []}], "response": "Done."}\n```'
    result = parse_edit_response(raw)
    assert result["response"] == "Done."

def test_parse_edit_response_malformed():
    result = parse_edit_response("This is not JSON at all")
    assert result is None

def test_apply_changes_update():
    blocks = [
        {"id": "b_001", "type": "heading", "data": {"text": "Old Title", "level": 1}},
        {"id": "b_002", "type": "workflow", "data": {"steps": [], "connections": []}},
    ]
    changes = [{"block_id": "b_001", "action": "update", "data": {"text": "New Title", "level": 1}}]
    updated, undo_entries = apply_changes_to_blocks(blocks, changes)
    assert updated[0]["data"]["text"] == "New Title"
    assert undo_entries[0]["before"]["text"] == "Old Title"
    assert undo_entries[0]["after"]["text"] == "New Title"

def test_apply_changes_add():
    blocks = [{"id": "b_001", "type": "heading", "data": {"text": "Title", "level": 1}}]
    changes = [{"block_id": "b_new", "action": "add", "after": "b_001", "type": "checklist",
                "data": [{"text": "New item", "checked": False, "priority": "normal"}]}]
    updated, undo_entries = apply_changes_to_blocks(blocks, changes)
    assert len(updated) == 2
    assert updated[1]["type"] == "checklist"
    assert updated[1]["id"] == "b_new"

def test_apply_changes_delete():
    blocks = [
        {"id": "b_001", "type": "heading", "data": {"text": "Title", "level": 1}},
        {"id": "b_002", "type": "divider", "data": {"style": "solid"}},
    ]
    changes = [{"block_id": "b_002", "action": "delete"}]
    updated, undo_entries = apply_changes_to_blocks(blocks, changes)
    assert len(updated) == 1
    assert undo_entries[0]["action"] == "delete"
    assert undo_entries[0]["before"]["style"] == "solid"

def test_apply_changes_invalid_block_id_skipped():
    blocks = [{"id": "b_001", "type": "heading", "data": {"text": "Title", "level": 1}}]
    changes = [{"block_id": "nonexistent", "action": "update", "data": {"text": "Nope", "level": 1}}]
    updated, undo_entries = apply_changes_to_blocks(blocks, changes)
    assert len(updated) == 1
    assert updated[0]["data"]["text"] == "Title"  # unchanged
    assert len(undo_entries) == 0

def test_apply_changes_add_at_beginning():
    blocks = [{"id": "b_001", "type": "heading", "data": {"text": "Title", "level": 1}}]
    changes = [{"block_id": "b_new", "action": "add", "after": None, "type": "rich-text",
                "data": {"html": "<p>Intro</p>"}}]
    updated, undo_entries = apply_changes_to_blocks(blocks, changes)
    assert len(updated) == 2
    assert updated[0]["type"] == "rich-text"
    assert updated[0]["id"] == "b_new"
