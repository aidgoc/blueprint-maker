# Blueprint Editor — Design Spec

**Date:** 2026-03-14
**Status:** Approved
**Priority Order:** Chat editing → Questionnaire flow → Bug fixes → Visual editing → Auto-save/undo

## Problem

Blueprint Maker currently generates read-only HTML files. Users cannot:
- Edit generated blueprints (must regenerate entirely)
- Go back during the questionnaire flow
- Review/edit research findings or roles before generation
- Download working ZIP files (bug)
- Rename blueprints (bug)

## Solution: Block-Based Editable Blueprints

Transform blueprints from static HTML files into structured, editable documents composed of typed blocks. Enable editing via both natural language chat and direct visual manipulation.

---

## 1. Block System & Data Model

### Block Types

| Type | Purpose | Data Shape |
|------|---------|-----------|
| `heading` | Section/subsection titles | `{text: str, level: 1-4}` |
| `rich-text` | Paragraphs, notes, descriptions | `{html: str}` (sanitized) |
| `kpi-grid` | Dashboard metrics | `[{name, value, target, unit, trend}]` |
| `workflow` | Step-by-step processes | `{steps: [{id, title, description, type, assignee}], connections}` |
| `checklist` | Action items, requirements | `[{text, checked, priority}]` |
| `table` | Data tables, matrices, escalation matrices | `{columns: [str], rows: [[str]]}` |
| `timeline` | Phased plans, daily timelines | `[{phase, duration, activities: [str]}]` |
| `card-grid` | Grouped info cards (master matrix) | `[{title, type, items: [str]}]` |
| `glossary` | Term definitions | `[{term, definition, related: [str]}]` |
| `divider` | Visual separator | `{style: "solid"\|"dashed"\|"dotted"}` |
| `org-chart` | Team structure, reporting lines | `{roles: [{id, title, reports_to, responsibilities: [str]}]}` |
| `flow-diagram` | Interactions, inbound/outbound flows | `{nodes: [{id, label, type}], edges: [{from, to, label}]}` |

### Generator Output → Block Type Mapping

The existing generator produces specific structures that map to block types:

| Generator Output Field | Block Type | Notes |
|----------------------|-----------|-------|
| `kpis` | `kpi-grid` | Direct mapping |
| `workflows` | `workflow` | Direct mapping |
| `daily_timeline` | `timeline` | Time-blocked activities → phases with time as duration |
| `team_structure` | `org-chart` | Roles with reporting lines |
| `documents` | `checklist` | Document templates/checklists |
| `interactions` | `flow-diagram` | Inbound/outbound department flows |
| `escalation_matrix` | `table` | Leveled escalation as rows, triggers/actions as columns |
| `compliance_items` | `checklist` | Compliance requirements as checklist items |

Each block instance:
```json
{
  "id": "b_abc123",
  "type": "workflow",
  "data": { ... },
  "style": {
    "color_scheme": "blue",
    "layout": "default",
    "custom_css": null
  },
  "html_cache": "<div class='workflow'>...</div>"
}
```

**`html_cache` strategy:** Stored per block in Firestore for instant display. Regenerated lazily — when the block renderer is updated, a `renderer_version` field on the blueprint document is compared to the current server version. On mismatch, `html_cache` is regenerated on next read and saved back.

### Firestore Schema

**Blueprint document** (`blueprints/{blueprint_id}`):
```
blueprint_id (auto)
├── user_id: string
├── title: string
├── business_description: string
├── format: "blocks" | "legacy"          ← new; missing = "legacy"
├── renderer_version: int                ← new; for html_cache invalidation
├── status: "generating" | "completed"
├── section_order: [section_id, ...]
├── folder_id: string | null
├── file_count: int                      ← kept for legacy; ignored for blocks
├── files: [...]                         ← kept for legacy; empty for blocks
├── is_shared: bool
├── share_token: string | null
├── answers: { ... }
├── research: { stage1_research, stage2_research }
├── created_at: timestamp
└── updated_at: timestamp
```

**Sections subcollection** (`blueprints/{blueprint_id}/sections/{section_id}`):
```
section_id (slugified department name, e.g., "service_department")
├── title: string ("Service Department")
├── icon: string
├── position: number
├── blocks: [
│     { id, type, data, style, html_cache }
│   ]
├── created_at: timestamp
└── updated_at: timestamp
```

**Section ID generation:** `section_id` is derived from the department name via slugification (e.g., "Service Department" → "service_department"). `section_order` on the parent blueprint document is the source of truth for ordering; `position` on each section is a denormalized copy for independent queries.

**Document size guard:** If a section's blocks array approaches 800KB (Firestore limit is 1MB), `html_cache` fields are stripped from that section's blocks and regenerated client-side. This is a safety valve, not an expected condition.

**Chat history subcollection** (`blueprints/{blueprint_id}/chat_history/{msg_id}`):
```
msg_id (auto)
├── role: "user" | "assistant"
├── content: string
├── changes_made: [{section_id, block_id, action, before, after}] | null
├── created_at: timestamp
```

`before`/`after` snapshots stored in chat history enable undo-via-chat even after page refresh.

**Chat history retention:** Capped at 200 messages per blueprint. When exceeded, oldest messages are archived (deleted from subcollection; `changes_made` data is lost for archived messages).

### Legacy Blueprint Handling

- Blueprints with `format: "legacy"` (or missing `format` field) continue working as-is
- View/download from Cloud Storage HTML files via existing endpoints
- No migration attempted — legacy blueprints remain read-only
- New blueprints created after this change use `format: "blocks"`
- Existing `create_blueprint()` in `db.py` updated to set `format: "blocks"` by default

---

## 2. Chat-Based Editing (Priority 1)

### Architecture

A chat panel sits alongside the blueprint view. User types natural language, LLM edits the relevant blocks.

### Flow

```
User message
  → Send to LLM with:
      - Section list (titles + IDs only, for routing)
      - Currently viewed section's block data (no html_cache)
      - Chat history (last 10 messages for context)
      - Available block types and their data schemas
      - User's instruction
  → LLM returns structured changes:
      {
        "sections": [
          {
            "section_id": "service",
            "changes": [
              {"block_id": "b3", "action": "update", "data": { ...updated... }},
              {"block_id": "b_new", "action": "add", "after": "b3", "type": "checklist", "data": { ... }},
              {"block_id": "b5", "action": "delete"}
            ]
          }
        ],
        "response": "Added a quality inspection step after step 3."
      }
  → Apply changes to each affected section document
  → Re-render html_cache for affected blocks only (server-side)
  → Save sections to Firestore
  → Push to undo stack (grouped as single entry)
  → Display LLM response in chat panel
```

### Section Routing

When the user's message doesn't name a section explicitly:
1. If user is currently viewing a section → target that section
2. If ambiguous → LLM decides based on section titles and instruction context
3. For cross-section instructions ("add X to every department") → LLM returns multiple entries in `sections` array

### LLM Prompt Strategy

The system prompt instructs the LLM to:
- Return valid JSON matching the change schema above
- Only reference existing block IDs for `update`/`delete` actions
- Generate new UUIDs for `add` actions
- Include the full updated `data` for `update` actions (not a diff)
- The prompt includes the block type schemas so the LLM knows valid data shapes

Error handling for malformed LLM responses:
1. JSON parse failure → retry once with repair (same strategy as `_extract_json()` in generator.py)
2. Invalid block_id reference → skip that change, include warning in response
3. Invalid block type → skip that change, include warning in response

### Model Selection

- **Quick edits** (single block, text changes): Gemini 2.5 Flash or equivalent cheap model via OpenRouter
- **Structural edits** (adding sections, reorganizing): Gemini 2.5 Pro or equivalent
- Model routing is configurable in `config.py` — can swap in DeepSeek, Qwen, etc. via OpenRouter

### API Endpoint

```
POST /api/blueprints/{blueprint_id}/chat
Auth: Required (Firebase token). User must own the blueprint.
Body: { "message": "add a quality check step after dispatch" }
Response: {
  "response": "Added quality check step...",
  "sections": [
    {
      "section_id": "service",
      "changes": [...]
    }
  ]
}
```

---

## 3. Questionnaire Flow — Back/Edit & Research Review (Priority 2)

### New Flow (all 8 questions across 3 stages)

```
Stage 1: Q1 → Q2 → Q3
  → Stage 1 Research runs
  → Research Review Screen (editable: industry context, market insights)
Stage 2: Q4 → Q5 → Q6
  → Stage 2 Research runs
  → Roles/Departments Review Screen (add/remove/rename/reorder roles, edit descriptions)
Stage 3: Q7 → Q8
  → Final Review Screen (all answers + all research + all roles, everything editable)
  → "Generate Blueprint" button
```

### Back Button

- Every question screen gets a back button
- Previous answer is pre-filled
- Answers stored in session, updated on back-and-forth navigation
- Back from Research Review → returns to last question of that stage
- Back from Final Review → returns to Q8

### Research Review Screen

After each research stage completes, show findings in editable format:
- **Stage 1 review:** Industry context, market insights shown as editable text areas
- **Stage 2 review:** Identified roles/departments as an editable list:
  - Add new role (text input + add button)
  - Remove role (X button with confirmation)
  - Rename role (inline edit)
  - Reorder roles (drag or up/down arrows)
  - Edit role description (expandable text area)
- Stage durations and descriptions: editable inline

### Final Review Screen

Before generation, show complete summary:
- All Q&A pairs (click any to jump back and edit)
- All roles/departments (still editable)
- Research highlights (collapsible, editable)
- Estimated generation time
- "Generate Blueprint" button (prominent)

### Re-Research Triggers

Only certain answer changes trigger re-research:

| Changed Field | Re-runs |
|--------------|---------|
| Company name, industry, business type | Stage 1 research |
| Business description, service details | Stage 2 research |
| Team size, location, etc. | Nothing — cosmetic only |

When re-research is needed, show a confirmation: "This change affects the research. Re-run research? (Your previous edits to research will be replaced)"

### Session State

```python
session = {
    ...existing fields...,
    "current_question": int,         # for back/forward navigation
    "research_edits": {              # user's manual edits to research
        "stage1": { ... },
        "stage2": { ... }
    },
    "role_edits": {                  # user's edits to proposed roles
        "added": [],
        "removed": [],
        "renamed": {},
        "reordered": []
    },
    "review_completed": bool         # gate for generation
}
```

These new fields are persisted to Firestore via `session_store.py` (they are small — no exclusion needed). If server restarts mid-questionnaire, user's edits are preserved.

---

## 4. Bug Fixes (Priority 3)

### Bug 1: Download Clears Files from Interface

**Root cause:** Download likely navigates away or triggers session state loss.
**Fix:** Download via background `fetch()` → create Blob URL → trigger download via hidden `<a>` tag. No navigation, no session impact.

### Bug 2: Downloaded Files Are Empty

**Root cause:** ZIP endpoint reads from `session["generated_files"]` which may be empty after server restart or session expiry.
**Fix (new blueprints):** Use `GET /api/blueprints/{id}/export/zip` — renders HTML from Firestore block data on-demand. No dependency on in-memory session.
**Fix (legacy blueprints):** Existing `GET /api/download/{sid}` fetches HTML from Cloud Storage if `session["generated_files"]` is empty.

Note: Two separate download endpoints. The frontend checks `blueprint.format` and calls the appropriate one.

### Bug 3: Rename Doesn't Work

**Root cause:** Inline title edit not wired to API or fails silently.
**Fix:** Connect inline edit to `PUT /api/user/blueprints/{id}` with `{title: newTitle}`. Show save confirmation or error toast.

---

## 5. Visual Inline Editing (Priority 4)

### Editor Modes

Each block has two modes:
- **View mode:** Rendered HTML from `html_cache` (default)
- **Edit mode:** Type-specific editor UI (activated on click)

### Block Interactions

| Action | Behavior |
|--------|----------|
| Hover | Subtle border + floating toolbar (edit, move, duplicate, delete) |
| Click | Enter edit mode for that block type |
| Drag handle | Reorder blocks within section (SortableJS) |
| "+" between blocks | Open block type palette to insert new block |
| Style icon | Open floating style panel (colors, layout variant, fonts) |

### Per-Type Editors

| Block Type | Edit UI |
|-----------|---------|
| `heading` | contenteditable text field |
| `rich-text` | Simple textarea with markdown-like formatting (no contenteditable — too fragile in vanilla JS) |
| `kpi-grid` | Inline form per metric (name, value, target inputs) |
| `workflow` | Step list: edit text per step, drag to reorder, add/remove steps, dropdown for step type |
| `checklist` | Check/uncheck, edit text, add/remove items, drag to reorder |
| `table` | Cell-by-cell editing, add/remove rows and columns |
| `timeline` | Edit phase name/duration, drag to reorder, add/remove phases |
| `card-grid` | Edit card content, change card type via dropdown, change color |
| `glossary` | Edit term/definition pairs, add/remove entries |
| `org-chart` | Edit role names/responsibilities, change reporting lines via dropdown |
| `flow-diagram` | Edit node labels, add/remove connections (simple list UI, not canvas-based) |

### Style Panel

Floating popover when clicking style icon:
- Color scheme picker (predefined palettes matching blueprint design)
- Layout variant (e.g., workflow: vertical vs horizontal)
- Font size override
- Custom background color

### Implementation

- Vanilla JS block editor engine (~2500-3000 lines across all files)
- SortableJS for drag-drop (~8KB, CDN)
- Each block type: `BlockType.render(data, style)` → HTML, `BlockType.editor(data, onChange)` → editor UI
- Block manager class handles: toolbar, drag-drop, insert palette, edit mode toggling
- All edits → update block data → re-render html_cache (via server endpoint) → debounced save → undo stack

### File Structure

```
static/
├── index.html              # existing SPA (add editor container)
├── editor/
│   ├── editor.js           # block editor engine, manager class — MUST load first
│   ├── blocks/             # per-type render + editor functions — register with editor.js
│   │   ├── heading.js
│   │   ├── rich-text.js
│   │   ├── workflow.js
│   │   ├── kpi-grid.js
│   │   ├── checklist.js
│   │   ├── table.js
│   │   ├── timeline.js
│   │   ├── card-grid.js
│   │   ├── glossary.js
│   │   ├── org-chart.js
│   │   ├── flow-diagram.js
│   │   └── divider.js
│   ├── chat-panel.js       # chat editing UI
│   ├── style-panel.js      # block style popover
│   └── undo.js             # undo/redo manager
```

**Loading order:** `editor.js` loads first and exposes a global `BlockEditor` object with a `registerBlockType(name, {render, editor})` method. Each block JS file calls `BlockEditor.registerBlockType(...)` on load. Chat panel, style panel, and undo manager load last and attach to the `BlockEditor` instance.

---

## 6. Auto-Save & Undo/Redo (Priority 5)

### Auto-Save

- **Trigger:** Any block edit (chat or visual)
- **Debounce:** 1.5 seconds of inactivity after last edit
- **Scope:** Save only the affected section document
- **UI indicator:** Top bar shows "Saving..." → "Saved"
- **Failure handling:**
  - Show "Save failed — retrying..."
  - Retry with exponential backoff (1s, 2s, 4s — max 3 attempts)
  - If all retries fail: "Offline — changes saved locally" + queue in localStorage
  - Flush localStorage queue when connection restores

### Undo/Redo

- **Storage:** Client-side array of patches
  ```js
  { id, sectionId, blockId, action, before, after, timestamp }
  ```
- **Keybindings:** Ctrl+Z (undo), Ctrl+Y / Ctrl+Shift+Z (redo)
- **Grouping:** Chat edits that modify multiple blocks → single undo entry
- **Max stack:** 50 entries (oldest dropped when exceeded)
- **Lifetime:** Cleared on page refresh (all changes already auto-saved)
- **Post-refresh undo:** Available via chat history — `before`/`after` snapshots in chat messages allow reverting chat edits even after refresh

### Offline Queue (localStorage)

```js
localStorage["blueprint_save_queue"] = JSON.stringify([
  { sectionId, blocks, timestamp },
  ...
])
```

On page load, check queue and flush any pending saves.

---

## 7. Generation Pipeline Changes

### Current Pipeline
```
LLM → JSON → renderer.py → HTML files → Cloud Storage
```

### New Pipeline
```
LLM → JSON → block_converter.py → blocks with html_cache → Firestore sections
```

The async generation flow remains the same:
1. `POST /api/generate` starts background task, returns `session_id`
2. `GET /api/generate/status/{session_id}` polls for progress
3. When complete, status response includes `blueprint_id`
4. Frontend transitions from polling screen → blueprint editor view using `blueprint_id`

### New Module: `block_converter.py`

Converts generator output JSON into block format:

```python
def convert_department_to_blocks(department_json: dict) -> list[dict]:
    """Convert LLM-generated department JSON into a list of blocks."""
    blocks = []
    blocks.append({"type": "heading", "data": {"text": dept["name"], "level": 1}})

    if dept.get("kpis"):
        blocks.append({"type": "kpi-grid", "data": dept["kpis"]})

    for workflow in dept.get("workflows", []):
        blocks.append({"type": "workflow", "data": workflow})

    if dept.get("daily_timeline"):
        blocks.append({"type": "timeline", "data": dept["daily_timeline"]})

    if dept.get("team_structure"):
        blocks.append({"type": "org-chart", "data": dept["team_structure"]})

    if dept.get("interactions"):
        blocks.append({"type": "flow-diagram", "data": dept["interactions"]})

    if dept.get("escalation_matrix"):
        blocks.append({"type": "table", "data": _escalation_to_table(dept["escalation_matrix"])})

    if dept.get("documents"):
        blocks.append({"type": "checklist", "data": dept["documents"]})

    if dept.get("compliance_items"):
        blocks.append({"type": "checklist", "data": dept["compliance_items"]})

    return blocks
```

### Block Renderer: `block_renderer.py`

Renders individual blocks to HTML (used for `html_cache` and ZIP export):

```python
CURRENT_RENDERER_VERSION = 1  # increment when renderers change

def render_block(block: dict) -> str:
    """Render a single block to HTML fragment."""
    renderer = BLOCK_RENDERERS[block["type"]]
    return renderer(block["data"], block.get("style", {}))

def render_section_to_html(section: dict) -> str:
    """Render a full section to standalone HTML file (for ZIP download)."""
    html_parts = [HTML_HEADER.format(title=section["title"])]
    for block in section["blocks"]:
        html_parts.append(render_block(block))
    html_parts.append(HTML_FOOTER)
    return "\n".join(html_parts)
```

### Partial failure during generation

If section creation partially fails (e.g., 5 of 8 sections written):
- Blueprint status stays `"generating"`
- Error logged with list of failed sections
- Frontend shows "Generation partially complete — X sections ready, Y failed"
- User can retry failed sections individually

---

## 8. API Changes Summary

### New Endpoints

All new endpoints require Firebase authentication. User must own the blueprint (verified via `user_id` match).

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `POST /api/blueprints/{id}/chat` | Owner | Chat-based editing |
| `GET /api/blueprints/{id}/sections` | Owner or shared | List sections (titles, IDs, positions) |
| `GET /api/blueprints/{id}/sections/{sid}` | Owner or shared | Get full section with blocks |
| `PUT /api/blueprints/{id}/sections/{sid}` | Owner | Update section (save blocks) |
| `PUT /api/blueprints/{id}/section-order` | Owner | Reorder sections |
| `GET /api/blueprints/{id}/export/zip` | Owner or shared | Generate ZIP from block data |

Block-level endpoints (add, delete, style) are **not** separate endpoints. All block mutations go through `PUT /api/blueprints/{id}/sections/{sid}` which accepts the full updated blocks array. This is simpler and matches how Firestore stores blocks (as an array within the section document).

### Modified Endpoints

| Endpoint | Change |
|----------|--------|
| `POST /api/answer` | Support `back: true` parameter to go to previous question |
| `POST /api/generate` | Output blocks to Firestore sections instead of HTML to session |
| `GET /api/generate/status/{sid}` | Return `blueprint_id` when complete so frontend can transition to editor |
| `GET /api/download/{sid}` | Legacy only — fetches from Cloud Storage. New blueprints use `/export/zip` |

### Removed Dependencies

- `session["generated_files"]` no longer needed for new blueprints
- Cloud Storage HTML files no longer primary storage (kept only for legacy)

---

## 9. Frontend Structure Changes

### Current: Single `index.html` (~2100 lines)

### New: `index.html` + modular editor scripts

```html
<!-- At end of index.html body -->
<script src="/static/editor/editor.js"></script>
<!-- Block types register with BlockEditor on load -->
<script src="/static/editor/blocks/heading.js"></script>
<script src="/static/editor/blocks/rich-text.js"></script>
<script src="/static/editor/blocks/workflow.js"></script>
<script src="/static/editor/blocks/kpi-grid.js"></script>
<script src="/static/editor/blocks/checklist.js"></script>
<script src="/static/editor/blocks/table.js"></script>
<script src="/static/editor/blocks/timeline.js"></script>
<script src="/static/editor/blocks/card-grid.js"></script>
<script src="/static/editor/blocks/glossary.js"></script>
<script src="/static/editor/blocks/org-chart.js"></script>
<script src="/static/editor/blocks/flow-diagram.js"></script>
<script src="/static/editor/blocks/divider.js"></script>
<!-- Attach to BlockEditor after blocks are registered -->
<script src="/static/editor/chat-panel.js"></script>
<script src="/static/editor/style-panel.js"></script>
<script src="/static/editor/undo.js"></script>
```

The existing `index.html` stays as-is. New editor functionality loads via additional scripts. No build step, no bundler.

### New Screens in SPA

1. **Research Review Screen** — after Stage 1 and Stage 2 research
2. **Roles Review Screen** — editable role/department list
3. **Final Review Screen** — summary of all answers + research before generation
4. **Blueprint Editor Screen** — replaces current read-only detail view for `format: "blocks"` blueprints

---

## 10. External Dependencies

| Dependency | Purpose | Size |
|-----------|---------|------|
| SortableJS | Drag-drop for block reordering | ~8KB (CDN) |

No other new dependencies. No npm, no build tools.

---

## Non-Goals (Explicitly Out of Scope)

- Multi-user collaboration
- Version history / named versions
- Migrating legacy blueprints to block format
- Breaking `index.html` into component files (unless it becomes unmanageable)
- Adding npm/node tooling
- Changing hosting (stays on Cloud Run + Firebase)
