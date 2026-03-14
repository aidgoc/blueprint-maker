# Plan 2: Chat Editing + Questionnaire Back/Edit Flow

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add chat-based blueprint editing via LLM and redesign the questionnaire flow to support going back, editing research findings, reviewing roles, and a final review screen before generation.

**Architecture:** Chat editing sends user message + current section blocks to LLM via OpenRouter, receives structured JSON changes, applies them to Firestore. Questionnaire flow adds back navigation, research review screens, and a final review screen. All changes are in `server.py` (new endpoints), `chat_editor.py` (new module), and `static/index.html` (frontend).

**Tech Stack:** Python FastAPI, OpenRouter LLM API, Firestore, vanilla JS frontend

**Spec:** `docs/superpowers/specs/2026-03-14-blueprint-editor-design.md` — Sections 2 and 3

**Depends on:** Plan 1 (block foundation) must be complete — needs `block_types.py`, `block_renderer.py`, `db.py` section CRUD, section API endpoints.

**Security note:** All dynamic user content must be rendered via `textContent` or properly escaped. Never use `innerHTML` with untrusted data. The `html_cache` from blocks is server-rendered and trusted, but user-entered text (chat messages, answers, department names) must always use `textContent`.

---

## File Structure

### New Files
| File | Responsibility |
|------|---------------|
| `chat_editor.py` | LLM-powered chat editing: build prompt, call LLM, parse changes, apply to blocks |
| `static/editor/chat-panel.js` | Chat panel UI: message input, message history, loading states |
| `tests/test_chat_editor.py` | Tests for chat editing logic |

### Modified Files
| File | Changes |
|------|---------|
| `server.py` | Add chat endpoint, modify `/api/answer` for back navigation, add research review flow |
| `config.py` | Add `EDITOR_MODEL` for chat editing |
| `static/index.html` | Back button on questions, research review screen, roles review screen, final review screen, chat panel container, editor screen |
| `session_store.py` | Persist new session fields (current_question, research_edits, role_edits) |

---

## Chunk 1: Chat Editor Backend

### Task 1: Create the chat editing module

**Files:**
- Create: `chat_editor.py`
- Create: `tests/test_chat_editor.py`
- Modify: `config.py`

- [ ] **Step 1: Add EDITOR_MODEL to config.py**

Add at end of `config.py`:

```python
# Model for chat-based blueprint editing (fast, cheap)
EDITOR_MODEL = os.getenv("EDITOR_MODEL", "google/gemini-2.5-flash")
```

- [ ] **Step 2: Write tests for chat editor**

```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /home/harshwardhan/blueprint_maker && python -m pytest tests/test_chat_editor.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement chat_editor.py**

```python
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

    prompt = f"""All sections in this blueprint:
{section_list}

Currently viewing section: {current_section_id}

Current section blocks:
{blocks_json}

{f"Recent chat history:\n{history_text}\n" if history_text else ""}
User instruction: {instruction}

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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/harshwardhan/blueprint_maker && python -m pytest tests/test_chat_editor.py -v`
Expected: All 11 tests PASS

- [ ] **Step 6: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add chat_editor.py tests/test_chat_editor.py config.py
git commit -m "feat: add chat editor module for LLM-powered blueprint editing"
```

---

## Chunk 2: Chat API Endpoint

### Task 2: Add the chat endpoint to server.py

**Files:**
- Modify: `server.py`

- [ ] **Step 1: Add chat endpoint**

Add this endpoint to `server.py` (near the section endpoints added by Plan 1):

```python
@app.post("/api/blueprints/{blueprint_id}/chat")
async def chat_edit_blueprint(blueprint_id: str, request: Request):
    """Chat-based editing: user sends message, LLM modifies blocks."""
    enforce_rate_limit(request)
    from auth import get_current_user
    from db import get_blueprint, list_sections, get_section, update_section, update_blueprint
    from block_renderer import render_block
    from chat_editor import build_edit_prompt, call_edit_llm, parse_edit_response, apply_changes_to_blocks

    user = await get_current_user(request)
    bp = get_blueprint(blueprint_id)
    if not bp or bp.get("user_id") != user.uid:
        raise HTTPException(404, "Blueprint not found")
    if bp.get("format") != "blocks":
        raise HTTPException(400, "Chat editing not available for legacy blueprints")

    body = await request.json()
    message = body.get("message", "").strip()
    current_section_id = body.get("section_id")  # which section user is viewing
    if not message:
        raise HTTPException(400, "message is required")

    # Get all sections for context
    all_sections = list_sections(blueprint_id)
    section_summaries = [{"id": s["id"], "title": s["title"]} for s in all_sections]

    # Get current section blocks
    current_blocks = []
    if current_section_id:
        section = get_section(blueprint_id, current_section_id)
        if section:
            current_blocks = section.get("blocks", [])

    # Load chat history from Firestore
    chat_history = _get_chat_history(blueprint_id)

    # Build prompt and call LLM
    prompt = build_edit_prompt(section_summaries, current_blocks, current_section_id or "", chat_history, message)

    try:
        raw_response = await call_edit_llm(prompt)
    except Exception as e:
        logger.error("Chat LLM call failed for blueprint %s: %s", blueprint_id, e)
        raise HTTPException(502, "AI editing service temporarily unavailable. Please try again.")

    parsed = parse_edit_response(raw_response)
    if not parsed:
        # LLM returned something unparseable — return the raw text as a conversational response
        _save_chat_messages(blueprint_id, message, raw_response, [])
        return {"response": raw_response, "sections": []}

    # Apply changes to each affected section
    result_sections = []
    all_undo_entries = []

    for section_change in parsed.get("sections", []):
        sid = section_change.get("section_id")
        changes = section_change.get("changes", [])
        if not sid or not changes:
            continue

        section_doc = get_section(blueprint_id, sid)
        if not section_doc:
            continue

        blocks = section_doc.get("blocks", [])
        updated_blocks, undo_entries = apply_changes_to_blocks(blocks, changes)

        # Re-render html_cache for changed blocks
        changed_ids = {c["block_id"] for c in changes}
        for block in updated_blocks:
            if block["id"] in changed_ids or not block.get("html_cache"):
                block["html_cache"] = render_block(block)

        # Save to Firestore
        update_section(blueprint_id, sid, {"blocks": updated_blocks})

        result_sections.append({"section_id": sid, "changes": changes})
        all_undo_entries.extend([{**u, "section_id": sid} for u in undo_entries])

    # Save chat history
    _save_chat_messages(blueprint_id, message, parsed.get("response", ""), all_undo_entries)

    return {
        "response": parsed.get("response", "Changes applied."),
        "sections": result_sections,
    }
```

- [ ] **Step 2: Add chat history helpers**

Add these helper functions to `server.py`:

```python
def _get_chat_history(blueprint_id: str, limit: int = 10) -> list[dict]:
    """Get recent chat messages for a blueprint."""
    try:
        from firebase_config import get_firestore_client
        db = get_firestore_client()
        docs = (db.collection("blueprints").document(blueprint_id)
                .collection("chat_history")
                .order_by("created_at", direction="DESCENDING")
                .limit(limit * 2)  # Get both user and assistant messages
                .stream())
        messages = []
        for doc in docs:
            data = doc.to_dict()
            messages.append({"role": data.get("role"), "content": data.get("content")})
        messages.reverse()  # Chronological order
        return messages[-limit * 2:]  # Last N exchanges
    except Exception:
        return []


def _save_chat_messages(blueprint_id: str, user_message: str, assistant_response: str,
                        undo_entries: list[dict]) -> None:
    """Save user and assistant messages to chat history."""
    try:
        from firebase_config import get_firestore_client
        from datetime import datetime, timezone
        db = get_firestore_client()
        col = db.collection("blueprints").document(blueprint_id).collection("chat_history")

        now = datetime.now(timezone.utc)
        col.add({"role": "user", "content": user_message, "changes_made": None, "created_at": now})
        col.add({
            "role": "assistant",
            "content": assistant_response,
            "changes_made": [{"section_id": u.get("section_id"), "block_id": u.get("block_id"),
                              "action": u.get("action"), "before": u.get("before"), "after": u.get("after")}
                             for u in undo_entries] if undo_entries else None,
            "created_at": now,
        })

        # Trim to 200 messages max
        all_docs = list(col.order_by("created_at").stream())
        if len(all_docs) > 200:
            for doc in all_docs[:len(all_docs) - 200]:
                doc.reference.delete()

    except Exception as e:
        logger.warning("Failed to save chat history for %s: %s", blueprint_id, e)
```

- [ ] **Step 3: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add server.py
git commit -m "feat: add chat editing API endpoint with history persistence"
```

---

## Chunk 3: Chat Panel Frontend

### Task 3: Create the chat panel UI

**Files:**
- Create: `static/editor/chat-panel.js`
- Modify: `static/index.html` (add editor screen with chat panel)

- [ ] **Step 1: Create editor directory**

```bash
mkdir -p /home/harshwardhan/blueprint_maker/static/editor
```

- [ ] **Step 2: Create chat-panel.js**

All user-generated content (chat messages, user names) must use `textContent` for safe rendering. Only `html_cache` from server-rendered blocks uses DOM insertion via a sanitized path.

```javascript
// static/editor/chat-panel.js
// Chat panel UI for blueprint editing
// SECURITY: All user content rendered via textContent, never innerHTML

(function() {
  'use strict';

  var chatMessages = [];
  var chatBlueprintId = null;
  var chatSectionId = null;
  var chatLoading = false;

  function createEl(tag, className, text) {
    var el = document.createElement(tag);
    if (className) el.className = className;
    if (text) el.textContent = text;
    return el;
  }

  window.ChatPanel = {
    init: function(blueprintId, sectionId) {
      chatBlueprintId = blueprintId;
      chatSectionId = sectionId;
      chatMessages = [];
      this.render();
    },

    setSectionId: function(sectionId) {
      chatSectionId = sectionId;
    },

    render: function() {
      var panel = document.getElementById('chatPanel');
      if (!panel) return;
      while (panel.firstChild) panel.removeChild(panel.firstChild);

      // Header
      var header = createEl('div', 'chat-header');
      header.appendChild(createEl('h4', null, 'Edit with AI'));
      header.appendChild(createEl('span', 'chat-hint', 'Describe what you want to change'));
      panel.appendChild(header);

      // Messages area
      var msgArea = createEl('div', 'chat-messages');
      msgArea.id = 'chatMessages';
      chatMessages.forEach(function(msg) {
        var el = createEl('div', 'chat-msg chat-msg-' + msg.role, msg.content);
        msgArea.appendChild(el);
      });
      panel.appendChild(msgArea);

      // Input area
      var inputArea = createEl('div', 'chat-input-area');

      var input = document.createElement('textarea');
      input.className = 'chat-input';
      input.id = 'chatInput';
      input.placeholder = 'e.g., "Add a quality check step after dispatch"';
      input.rows = 2;
      input.onkeydown = function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          ChatPanel.send();
        }
      };
      inputArea.appendChild(input);

      var sendBtn = createEl('button', 'chat-send-btn', 'Send');
      sendBtn.id = 'chatSendBtn';
      sendBtn.onclick = function() { ChatPanel.send(); };
      inputArea.appendChild(sendBtn);

      panel.appendChild(inputArea);

      // Scroll to bottom
      setTimeout(function() { msgArea.scrollTop = msgArea.scrollHeight; }, 50);
    },

    send: function() {
      if (chatLoading || !chatBlueprintId) return;
      var input = document.getElementById('chatInput');
      var message = input.value.trim();
      if (!message) return;

      // Add user message
      chatMessages.push({role: 'user', content: message});
      input.value = '';
      this.render();

      // Show loading
      chatLoading = true;
      var sendBtn = document.getElementById('chatSendBtn');
      if (sendBtn) { sendBtn.disabled = true; sendBtn.textContent = 'Thinking...'; }

      var msgArea = document.getElementById('chatMessages');
      var loadingEl = createEl('div', 'chat-msg chat-msg-loading');
      var typing = createEl('div', 'chat-typing');
      typing.appendChild(createEl('span'));
      typing.appendChild(createEl('span'));
      typing.appendChild(createEl('span'));
      loadingEl.appendChild(typing);
      if (msgArea) msgArea.appendChild(loadingEl);

      fetchWithAuth('/api/blueprints/' + chatBlueprintId + '/chat', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({message: message, section_id: chatSectionId})
      })
      .then(function(data) {
        chatLoading = false;
        chatMessages.push({role: 'assistant', content: data.response || 'Changes applied.'});
        ChatPanel.render();

        // If changes were made, reload the current section
        if (data.sections && data.sections.length > 0) {
          if (window.EditorScreen && window.EditorScreen.reloadSection) {
            window.EditorScreen.reloadSection(chatSectionId);
          }
        }
      })
      .catch(function(e) {
        chatLoading = false;
        chatMessages.push({role: 'assistant', content: 'Error: ' + e.message});
        ChatPanel.render();
      });
    }
  };
})();
```

- [ ] **Step 3: Add chat panel CSS and editor screen to index.html**

In `static/index.html`, add CSS for the chat panel in the `<style>` section:

```css
/* Chat Panel */
.chat-header { padding: 1rem; border-bottom: 1px solid var(--border); }
.chat-header h4 { margin: 0; font-size: 1rem; }
.chat-hint { font-size: 0.8rem; color: var(--text-light); }
.chat-messages { flex: 1; overflow-y: auto; padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem; }
.chat-msg { padding: 0.75rem 1rem; border-radius: 12px; max-width: 85%; word-wrap: break-word; font-size: 0.9rem; line-height: 1.5; }
.chat-msg-user { background: var(--brand); color: white; align-self: flex-end; border-bottom-right-radius: 4px; }
.chat-msg-assistant { background: var(--surface); border: 1px solid var(--border); align-self: flex-start; border-bottom-left-radius: 4px; }
.chat-msg-loading { align-self: flex-start; background: var(--surface); border: 1px solid var(--border); padding: 1rem; }
.chat-typing { display: flex; gap: 4px; }
.chat-typing span { width: 8px; height: 8px; border-radius: 50%; background: var(--text-light); animation: chatBounce 1.4s infinite; }
.chat-typing span:nth-child(2) { animation-delay: 0.2s; }
.chat-typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes chatBounce { 0%,80%,100% { transform: scale(0); } 40% { transform: scale(1); } }
.chat-input-area { padding: 1rem; border-top: 1px solid var(--border); display: flex; gap: 0.5rem; }
.chat-input { flex: 1; border: 1px solid var(--border); border-radius: 8px; padding: 0.5rem 0.75rem; font-size: 0.9rem; resize: none; font-family: inherit; }
.chat-input:focus { outline: none; border-color: var(--brand); }
.chat-send-btn { background: var(--brand); color: white; border: none; border-radius: 8px; padding: 0.5rem 1rem; cursor: pointer; font-weight: 600; }
.chat-send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* Editor Screen */
#editorScreen { display: none; height: calc(100vh - 60px); }
.editor-layout { display: flex; height: 100%; }
.editor-sidebar { width: 220px; border-right: 1px solid var(--border); overflow-y: auto; background: var(--surface); }
.editor-sidebar .section-item { padding: 0.75rem 1rem; cursor: pointer; border-bottom: 1px solid var(--border); font-size: 0.9rem; }
.editor-sidebar .section-item:hover { background: var(--blue-bg); }
.editor-sidebar .section-item.active { background: var(--brand); color: white; }
.editor-main { flex: 1; overflow-y: auto; padding: 2rem; }
.editor-chat { width: 350px; border-left: 1px solid var(--border); display: flex; flex-direction: column; background: var(--bg); }
.editor-block { margin-bottom: 1rem; }
```

- [ ] **Step 4: Add editor screen HTML to index.html**

Add this HTML inside the main app container (after the existing screens, find a suitable location near `detailScreen`):

```html
<!-- Editor Screen -->
<div id="editorScreen">
  <div class="editor-layout">
    <div class="editor-sidebar" id="editorSidebar"></div>
    <div class="editor-main" id="editorMain">
      <div id="editorBlocks"></div>
    </div>
    <div class="editor-chat" id="chatPanel"></div>
  </div>
</div>
```

- [ ] **Step 5: Add editor screen JS to index.html**

Add these functions in the `<script>` section. NOTE: Block `html_cache` is server-generated trusted HTML and is inserted via a dedicated rendering path. All user-entered content uses `textContent`.

```javascript
// --- Editor Screen ---
var editorBlueprintId = null;
var editorSections = [];
var editorCurrentSection = null;

window.EditorScreen = {
  show: function(blueprintId) {
    editorBlueprintId = blueprintId;
    hideAllScreens();
    document.getElementById('editorScreen').style.display = 'block';
    this.loadSections();
  },

  loadSections: function() {
    fetchWithAuth('/api/blueprints/' + editorBlueprintId + '/sections', {headers: authHeaders()})
    .then(function(sections) {
      editorSections = sections;
      EditorScreen.renderSidebar();
      if (sections.length > 0) {
        EditorScreen.loadSection(sections[0].id);
      }
    })
    .catch(function(e) { showToast('Failed to load sections: ' + e.message, 'error'); });
  },

  renderSidebar: function() {
    var sidebar = document.getElementById('editorSidebar');
    while (sidebar.firstChild) sidebar.removeChild(sidebar.firstChild);

    // Back to dashboard button
    var backBtn = document.createElement('div');
    backBtn.className = 'section-item';
    backBtn.style.fontWeight = '600';
    backBtn.textContent = '\u2190 Dashboard';
    backBtn.onclick = function() { showDashboard(); };
    sidebar.appendChild(backBtn);

    editorSections.forEach(function(s) {
      var item = document.createElement('div');
      item.className = 'section-item' + (editorCurrentSection === s.id ? ' active' : '');
      item.textContent = s.title;
      item.onclick = function() { EditorScreen.loadSection(s.id); };
      sidebar.appendChild(item);
    });
  },

  loadSection: function(sectionId) {
    editorCurrentSection = sectionId;
    this.renderSidebar();

    fetchWithAuth('/api/blueprints/' + editorBlueprintId + '/sections/' + sectionId, {headers: authHeaders()})
    .then(function(section) {
      EditorScreen.renderBlocks(section);
      ChatPanel.init(editorBlueprintId, sectionId);
    })
    .catch(function(e) { showToast('Failed to load section: ' + e.message, 'error'); });
  },

  reloadSection: function(sectionId) {
    if (sectionId === editorCurrentSection) {
      this.loadSection(sectionId);
    }
  },

  renderBlocks: function(section) {
    var main = document.getElementById('editorBlocks');
    while (main.firstChild) main.removeChild(main.firstChild);

    var blocks = section.blocks || [];
    blocks.forEach(function(block) {
      var el = document.createElement('div');
      el.className = 'editor-block';
      el.setAttribute('data-block-id', block.id);
      // html_cache is server-generated trusted HTML from block_renderer.py
      if (block.html_cache) {
        // Create a shadow container for trusted server-rendered content
        var content = document.createElement('div');
        content.className = 'block-content';
        // This is trusted server-generated HTML, not user input
        var range = document.createRange();
        range.selectNode(content);
        var frag = range.createContextualFragment(block.html_cache);
        content.appendChild(frag);
        el.appendChild(content);
      } else {
        el.textContent = block.type + ': ' + JSON.stringify(block.data).substring(0, 100);
      }
      main.appendChild(el);
    });
  }
};
```

- [ ] **Step 6: Wire editor screen into blueprint opening**

In the existing code where blueprints are opened (in the dashboard card click handler or `showDetailScreen`), add a check: if `bp.format === 'blocks'`, show the editor screen. Find the relevant click handler and add:

```javascript
// When opening a blueprint:
if (bp.format === 'blocks') {
  EditorScreen.show(bp.id);
  return;
}
// else: fall through to existing detail view for legacy blueprints
```

Also add `editorScreen` to the `hideAllScreens` function's list of screens.

- [ ] **Step 7: Wire generation completion to editor**

In the `pollGenerationStatus` function, when status is `"done"` and the response includes `blueprint_id`, navigate to the editor:

```javascript
// In the success handler where showResults(data) is currently called:
if (data.blueprint_id) {
  EditorScreen.show(data.blueprint_id);
} else {
  showResults(data);  // fallback for legacy
}
```

- [ ] **Step 8: Add script tag for chat-panel.js**

At the end of `<body>` in `index.html`, before `</body>`:

```html
<script src="/static/editor/chat-panel.js"></script>
```

- [ ] **Step 9: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add static/editor/chat-panel.js static/index.html
git commit -m "feat: add chat panel UI and editor screen for block-based blueprints"
```

---

## Chunk 4: Questionnaire Back Navigation

### Task 4: Add back button support to the questionnaire flow

**Files:**
- Modify: `server.py` (update `/api/answer` to support `back: true`)
- Modify: `static/index.html` (add back button to question UI)

- [ ] **Step 1: Update AnswerRequest model in server.py**

Find the `AnswerRequest` Pydantic model and add a `back` field:

```python
class AnswerRequest(BaseModel):
    session_id: str
    answer: str = ""  # make optional for back navigation
    back: bool = False  # new: go back to previous question
```

- [ ] **Step 2: Add back navigation logic to /api/answer**

At the beginning of the `answer_question` handler (after getting the session, before `step = sess["current_step"]`), add:

```python
    # Handle back navigation
    if req.back:
        step = sess["current_step"]
        if step <= 0:
            raise HTTPException(400, "Already at the first question")

        sess["current_step"] -= 1
        prev_step = sess["current_step"]
        prev_stage = get_stage_for_step(prev_step)

        # If going back across a stage boundary, restore previous stage
        if prev_stage != sess.get("current_stage"):
            sess["current_stage"] = prev_stage

        update_session(req.session_id, sess)
        q = get_question_for_step(prev_step, sess)
        stage_info = STAGES[prev_stage]

        # Pre-fill with previous answer
        prev_answer = sess["answers"].get(q["key"], "")

        return {
            "done": False,
            "question": q,
            "step": prev_step,
            "total_steps": get_total_questions(),
            "stage": prev_stage,
            "stage_name": stage_info["name"],
            "stage_description": stage_info["description"],
            "previous_answer": prev_answer,
        }
```

- [ ] **Step 3: Add back button to frontend**

In `static/index.html`, modify the `showQuestion` function. After the question text is set, add a back button:

```javascript
// Inside showQuestion, after setting question text, before showOnly('questionArea'):
var existingBack = document.getElementById('questionBackBtn');
if (!existingBack) {
  existingBack = document.createElement('button');
  existingBack.id = 'questionBackBtn';
  existingBack.className = 'back-btn';
  existingBack.textContent = '\u2190 Back';
  existingBack.onclick = function() { goBack(); };
  var container = document.getElementById('questionContainer');
  container.insertBefore(existingBack, container.firstChild);
}
existingBack.style.display = (stepNum <= 1) ? 'none' : 'inline-block';
```

Add the `goBack` function:

```javascript
window.goBack = function() {
  if (!sessionId) return;
  var btn = document.getElementById('questionBackBtn');
  if (btn) btn.disabled = true;

  fetchWithAuth('/api/answer', {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({session_id: sessionId, answer: '', back: true})
  })
  .then(function(data) {
    if (btn) btn.disabled = false;
    if (data.stage) updateStageBar(data.stage);
    showQuestion(data.question, data.step + 1);
    if (data.previous_answer) {
      document.getElementById('userInput').value = data.previous_answer;
      autoResize(document.getElementById('userInput'));
    }
  })
  .catch(function(e) {
    if (btn) btn.disabled = false;
    showToast(e.message, 'error');
  });
};
```

Add CSS:

```css
.back-btn { background: none; border: 1px solid var(--border); color: var(--text-light); padding: 0.4rem 0.75rem;
            border-radius: 6px; cursor: pointer; font-size: 0.85rem; margin-bottom: 0.75rem; }
.back-btn:hover { background: var(--surface); color: var(--text); }
.back-btn:disabled { opacity: 0.5; cursor: not-allowed; }
```

- [ ] **Step 4: Add default session fields in /api/start**

In the session initialization dict in `/api/start`, add:

```python
"current_question": 0,
"research_edits": {},
"role_edits": {"added": [], "removed": [], "renamed": {}, "reordered": []},
"review_completed": False,
```

- [ ] **Step 5: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add server.py static/index.html
git commit -m "feat: add back button navigation to questionnaire flow"
```

---

## Chunk 5: Research Review Screen

### Task 5: Add editable research review after each research stage

**Files:**
- Modify: `static/index.html` (make findings editable)
- Modify: `server.py` (accept research edits)

- [ ] **Step 1: Replace showFindings with editable version**

Replace the `showFindings` function in `static/index.html` with an editable version. All user content uses `textContent` — departments/stages are editable via `contentEditable` spans (which is safe since contentEditable creates text nodes, not HTML).

```javascript
function showFindings(data) {
  var card = document.getElementById('findingsCard');
  card.classList.remove('hidden');
  card.className = 'findings-card editable-findings';
  while (card.firstChild) card.removeChild(card.firstChild);

  card.appendChild(_ce('h4', null, 'Research Findings \u2014 Review & Edit'));
  card.appendChild(_ce('p', 'findings-hint', 'You can edit these findings before continuing. Changes will be used for blueprint generation.'));

  // Industry overview (editable textarea)
  if (data.industry_overview) {
    card.appendChild(_ce('div', 'section-label', 'Industry Overview'));
    var ta = document.createElement('textarea');
    ta.className = 'findings-edit';
    ta.id = 'editIndustryOverview';
    ta.value = data.industry_overview;
    ta.rows = 3;
    card.appendChild(ta);
  }

  // Departments (editable tags with add/remove)
  if (data.departments_found && data.departments_found.length) {
    card.appendChild(_ce('div', 'section-label', 'Departments Identified'));
    var dList = _ce('div', 'editable-tag-list');
    dList.id = 'editDepartments';
    data.departments_found.forEach(function(d) { _addEditableTag(dList, d); });
    card.appendChild(dList);

    var addDeptBtn = _ce('button', 'add-tag-btn', '+ Add Department');
    addDeptBtn.onclick = function() {
      var name = prompt('Department name:');
      if (name && name.trim()) _addEditableTag(dList, name.trim());
    };
    card.appendChild(addDeptBtn);
  }

  // Process stages (editable tags)
  if (data.stages_found && data.stages_found.length) {
    card.appendChild(_ce('div', 'section-label', 'Process Stages'));
    var sList = _ce('div', 'editable-tag-list');
    sList.id = 'editStages';
    data.stages_found.forEach(function(s) { _addEditableTag(sList, s); });
    card.appendChild(sList);

    var addStageBtn = _ce('button', 'add-tag-btn', '+ Add Stage');
    addStageBtn.onclick = function() {
      var name = prompt('Stage name:');
      if (name && name.trim()) _addEditableTag(sList, name.trim());
    };
    card.appendChild(addStageBtn);
  }

  // Continue button (saves edits)
  var contBtn = _ce('button', 'findings-continue', 'Looks Good \u2014 Continue');
  contBtn.onclick = function() {
    var edits = {};
    var overviewEl = document.getElementById('editIndustryOverview');
    if (overviewEl) edits.industry_overview = overviewEl.value;
    var deptList = document.getElementById('editDepartments');
    if (deptList) edits.departments = _collectTags(deptList);
    var stageList = document.getElementById('editStages');
    if (stageList) edits.stages = _collectTags(stageList);

    // Save edits to session via API
    if (Object.keys(edits).length > 0 && sessionId) {
      fetchWithAuth('/api/research-edits', {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({session_id: sessionId, edits: edits})
      }).catch(function() {}); // fire and forget
    }
    if (window._pendingQuestion) {
      showQuestion(window._pendingQuestion, window._pendingStep);
      window._pendingQuestion = null;
    }
  };
  card.appendChild(contBtn);
}

// Helper: create element with class and textContent (safe — no innerHTML)
function _ce(tag, cls, text) {
  var el = document.createElement(tag);
  if (cls) el.className = cls;
  if (text) el.textContent = text;
  return el;
}

function _addEditableTag(container, text) {
  var tag = document.createElement('span');
  tag.className = 'f-tag editable-tag';
  tag.contentEditable = 'true';
  tag.textContent = text;

  var removeBtn = document.createElement('span');
  removeBtn.className = 'tag-remove';
  removeBtn.textContent = '\u00d7';
  removeBtn.onclick = function(e) {
    e.stopPropagation();
    if (tag.parentNode) tag.parentNode.removeChild(tag);
  };
  tag.appendChild(removeBtn);
  container.appendChild(tag);
}

function _collectTags(container) {
  var tags = [];
  var els = container.querySelectorAll('.editable-tag');
  for (var i = 0; i < els.length; i++) {
    var text = els[i].textContent.replace('\u00d7', '').trim();
    if (text) tags.push(text);
  }
  return tags;
}
```

Add CSS for editable findings:

```css
.editable-findings { max-width: 600px; }
.findings-hint { font-size: 0.85rem; color: var(--text-light); margin-bottom: 1rem; }
.findings-edit { width: 100%; border: 1px solid var(--border); border-radius: 6px; padding: 0.5rem; font-family: inherit;
                 font-size: 0.9rem; resize: vertical; margin-bottom: 0.75rem; }
.findings-edit:focus { outline: none; border-color: var(--brand); }
.editable-tag-list { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.5rem; }
.editable-tag { cursor: text; position: relative; padding-right: 1.5rem; }
.tag-remove { cursor: pointer; position: absolute; right: 4px; top: 50%; transform: translateY(-50%);
              color: rgba(0,0,0,0.4); font-weight: bold; }
.tag-remove:hover { color: var(--red); }
.add-tag-btn { background: none; border: 1px dashed var(--border); color: var(--text-light); padding: 0.3rem 0.75rem;
               border-radius: 6px; cursor: pointer; font-size: 0.85rem; margin-bottom: 1rem; }
.add-tag-btn:hover { border-color: var(--brand); color: var(--brand); }
```

- [ ] **Step 2: Add research-edits endpoint to server.py**

```python
@app.post("/api/research-edits")
async def save_research_edits(request: Request):
    """Save user's edits to research findings."""
    enforce_rate_limit(request)
    body = await request.json()
    sid = body.get("session_id")
    edits = body.get("edits", {})

    sess = get_session(sid, sessions)
    if not sess:
        raise HTTPException(404, "Session not found")

    # Store edits in session
    if "research_edits" not in sess:
        sess["research_edits"] = {}

    stage = sess.get("current_stage", 1)
    sess["research_edits"][f"stage{stage}"] = edits

    # Also update the actual research data so it's used in generation
    research_key = f"stage{stage}"
    if research_key in sess.get("research", {}):
        r = sess["research"][research_key]
        if "industry_overview" in edits:
            r["industry_overview"] = edits["industry_overview"]
        if "departments" in edits:
            r["typical_departments"] = edits["departments"]
        if "stages" in edits:
            r["typical_process_stages"] = edits["stages"]

    update_session(sid, sess)
    return {"status": "ok"}
```

- [ ] **Step 3: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add server.py static/index.html
git commit -m "feat: add editable research review screen with department/stage editing"
```

---

## Chunk 6: Final Review Screen + Generation-to-Editor Flow

### Task 6: Enhance the profile/review screen and wire generation to editor

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Enhance showProfile into a full review screen**

Replace the existing `showProfile` function. All content uses safe `textContent` rendering.

```javascript
function showProfile(data) {
  showOnly('profileArea');
  var area = document.getElementById('profileContent');
  while (area.firstChild) area.removeChild(area.firstChild);

  var card = _ce('div', 'profile-card review-card');
  card.appendChild(_ce('h4', null, 'Final Review \u2014 Everything Looks Good?'));
  card.appendChild(_ce('p', 'review-hint', 'Review your answers and research findings. Edit departments below or go back to change any answer.'));
  card.appendChild(_ce('p', 'summary-text', data.profile_summary));

  // Research stats
  if (data.research_findings) {
    var rf = data.research_findings;
    card.appendChild(_ce('div', 'research-stats',
      (rf.compliance_items || 0) + ' compliance standards, ' +
      (rf.kpis_found || 0) + ' KPI benchmarks, ' +
      (rf.documents_found || 0) + ' document templates, ' +
      (rf.safety_standards || 0) + ' safety standards'));
  }

  // Departments (editable)
  if (data.departments && data.departments.length) {
    card.appendChild(_ce('div', 'section-label', 'Departments to Generate'));
    var dList = _ce('div', 'editable-tag-list');
    dList.id = 'reviewDepartments';
    data.departments.forEach(function(d) { _addEditableTag(dList, d); });
    card.appendChild(dList);

    var addBtn = _ce('button', 'add-tag-btn', '+ Add Department');
    addBtn.onclick = function() {
      var name = prompt('Department name:');
      if (name && name.trim()) _addEditableTag(dList, name.trim());
    };
    card.appendChild(addBtn);
  }

  // Process stages
  if (data.stages && data.stages.length) {
    card.appendChild(_ce('div', 'section-label', 'Process Stages'));
    var sFlow = _ce('div', 'stage-flow');
    data.stages.forEach(function(s, i) {
      if (i > 0) sFlow.appendChild(_ce('span', 'arrow-sep', '\u2192'));
      sFlow.appendChild(_ce('span', 'stage-item', s));
    });
    card.appendChild(sFlow);
  }

  // Go back link
  var backLink = _ce('button', 'back-btn', '\u2190 Go back and edit answers');
  backLink.style.marginTop = '1rem';
  backLink.onclick = function() { goBack(); };
  card.appendChild(backLink);

  area.appendChild(card);

  // Generate button
  var btnWrap = _ce('div');
  btnWrap.style.textAlign = 'center';
  btnWrap.style.marginTop = '1.5rem';
  var genBtn = _ce('button', 'generate-btn', 'Generate Blueprint Kit');
  genBtn.id = 'generateBtn';
  genBtn.onclick = function() {
    // Save department edits before generating
    var deptList = document.getElementById('reviewDepartments');
    if (deptList && sessionId) {
      var depts = _collectTags(deptList);
      fetchWithAuth('/api/research-edits', {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({session_id: sessionId, edits: {departments: depts}})
      }).catch(function() {});
    }
    genBtn.disabled = true;
    generateBlueprint();
  };
  btnWrap.appendChild(genBtn);
  area.appendChild(btnWrap);
}
```

- [ ] **Step 2: Wire generation completion to editor screen**

In the `pollGenerationStatus` function, find where `showResults(data)` is called on success (when `data.status === 'done'`). Add before the existing `showResults` call:

```javascript
if (data.blueprint_id) {
  EditorScreen.show(data.blueprint_id);
  return;
}
// fallback to existing showResults for legacy
```

- [ ] **Step 3: Add review CSS**

```css
.review-card { max-width: 650px; margin: 0 auto; }
.review-hint { font-size: 0.85rem; color: var(--text-light); margin-bottom: 1rem; }
```

- [ ] **Step 4: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add static/index.html
git commit -m "feat: add final review screen and post-generation editor navigation"
```

---

## Chunk 7: Persist New Session Fields

### Task 7: Ensure new session fields are persisted

**Files:**
- Modify: `session_store.py` (verify exclusions)
- Modify: `server.py` (add default values)

- [ ] **Step 1: Verify session_store.py exclusions**

Read `session_store.py` and confirm the exclusion set. The new fields (`current_question`, `research_edits`, `role_edits`, `review_completed`) are small and MUST be persisted. Verify they are NOT in the exclusion list. If they are excluded, remove them from the exclusion set.

- [ ] **Step 2: Verify /api/start has default values for new fields**

Confirm that the session init in `/api/start` includes (from Chunk 4 Step 4):

```python
"current_question": 0,
"research_edits": {},
"role_edits": {"added": [], "removed": [], "renamed": {}, "reordered": []},
"review_completed": False,
```

If already added in Chunk 4, this is a verification step only.

- [ ] **Step 3: Commit (if changes needed)**

```bash
cd /home/harshwardhan/blueprint_maker
git add session_store.py server.py
git commit -m "feat: persist questionnaire navigation state across restarts"
```

---

## Summary

After completing this plan:
1. **Chat editing works end-to-end**: user types instruction -> LLM edits blocks -> changes saved -> UI refreshed
2. **Chat history persisted** in Firestore subcollection with undo snapshots (before/after)
3. **Back button** on every question with previous answer pre-filled
4. **Research review screen** — edit industry overview, add/remove/rename departments and stages
5. **Final review screen** — see all data, edit departments, go back to any question
6. **Post-generation navigation** — goes straight to editor screen with chat panel
7. **Editor screen** with section sidebar, block display, and integrated chat panel
8. **XSS-safe** — all user content rendered via textContent, server-generated html_cache used only for trusted block rendering

**Depends on:** Plan 1 (block foundation) being complete
**Next:** Plan 3 (Bug Fixes + Visual Editor + Auto-save)
