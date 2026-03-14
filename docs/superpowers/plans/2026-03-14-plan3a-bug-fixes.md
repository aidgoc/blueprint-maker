# Plan 3A: Bug Fixes

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix three known bugs: download clears files from interface, downloaded files are empty, and rename doesn't work.

**Architecture:** Frontend-only fixes for download (use fetch + Blob URL) and rename (wire to existing PUT endpoint). Backend fix for empty ZIP (fetch from Cloud Storage when session files missing; use /export/zip for block-format blueprints).

**Tech Stack:** Vanilla JS frontend, Python FastAPI backend

**Spec:** `docs/superpowers/specs/2026-03-14-blueprint-editor-design.md` — Section 4

**Depends on:** Plan 1 (block foundation) for `/export/zip` endpoint.

---

## File Structure

### Modified Files
| File | Changes |
|------|---------|
| `static/index.html` | Fix download to use fetch+Blob, fix rename wiring, route download by blueprint format |
| `server.py` | Fix `/api/download/{sid}` to recover from Cloud Storage when files missing |

---

## Chunk 1: Fix Download (Bugs 1 & 2)

### Task 1: Fix download to not clear interface and handle empty files

**Files:**
- Modify: `static/index.html`
- Modify: `server.py`

- [ ] **Step 1: Find the current download handler in index.html**

Read `static/index.html` and search for the download button click handler. It likely uses `window.location` or a direct link to `/api/download/{sid}`, which navigates away and clears state.

- [ ] **Step 2: Replace download with fetch + Blob approach**

Find all download triggers in the frontend (in blueprint detail view, results screen, and dashboard card menus). Replace them with a safe download function that doesn't navigate away:

```javascript
// Add this utility function near the top of the script section:
function downloadFile(url, filename) {
  // Download via fetch + Blob — no navigation, no state loss
  fetchWithAuth(url, {headers: authHeaders()})
  .then(function(response) {
    // fetchWithAuth returns parsed JSON — we need the raw response for binary
    // So we need a separate raw fetch for downloads
    return fetch(url, {headers: {'Authorization': 'Bearer ' + authToken}});
  })
  .then(function(response) {
    if (!response.ok) throw new Error('Download failed');
    return response.blob();
  })
  .then(function(blob) {
    var blobUrl = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename || 'blueprint.zip';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(blobUrl);
  })
  .catch(function(e) {
    showToast('Download failed: ' + e.message, 'error');
  });
}
```

Then replace every download trigger. For example, find where the download ZIP button calls something like:
```javascript
// OLD (navigates away):
window.location.href = '/api/download/' + sessionId;
// or
window.open('/api/download/' + sessionId);
```

Replace with:
```javascript
// NEW (background fetch):
downloadFile('/api/download/' + sessionId, 'blueprint.zip');
```

For block-format blueprints (from dashboard), use the new export endpoint:
```javascript
// In dashboard download handler, check format:
if (bp.format === 'blocks') {
  downloadFile('/api/blueprints/' + bp.id + '/export/zip', bp.title + '_blueprint.zip');
} else {
  // Legacy: try session-based download, fall back to blueprint-based
  downloadFile('/api/download/' + (bp.session_id || sessionId), bp.title + '_blueprint.zip');
}
```

- [ ] **Step 3: Fix server.py download endpoint to recover from Cloud Storage**

In `server.py`, find the `/api/download/{session_id}` handler. It currently reads from `session["generated_files"]` which may be empty. The `_recover_files_from_storage` function exists but may not be called in all paths.

Verify that the download handler calls `_recover_files_from_storage(sess)` before trying to build the ZIP. If files are still empty after recovery, return a helpful error instead of an empty ZIP.

Read the current implementation and ensure this flow:
```python
files = sess.get("generated_files", [])
if not files:
    files = _recover_files_from_storage(sess)
if not files:
    raise HTTPException(404, "Blueprint files not available. They may have expired.")
```

- [ ] **Step 4: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add static/index.html server.py
git commit -m "fix: download via fetch+Blob to prevent UI state loss and empty files"
```

---

## Chunk 2: Fix Rename

### Task 2: Wire inline title edit to the API

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Find the rename functionality in index.html**

Search for `renameBlueprintModal` or similar rename handler. Read the current implementation to understand what's broken.

- [ ] **Step 2: Fix the rename handler**

The rename modal likely calls `PUT /api/user/blueprints/{id}` but may have a bug (wrong field name, missing error handling, not updating UI after success). Fix it:

```javascript
// The rename handler should:
// 1. Show a prompt/modal for the new name
// 2. Call PUT /api/user/blueprints/{id} with {title: newTitle}
// 3. Update the UI on success (update card title, show toast)
// 4. Show error on failure

function renameBlueprintAction(bp) {
  var newTitle = prompt('Rename blueprint:', bp.title);
  if (!newTitle || newTitle.trim() === '' || newTitle.trim() === bp.title) return;

  fetchWithAuth('/api/user/blueprints/' + bp.id, {
    method: 'PUT',
    headers: authHeaders(),
    body: JSON.stringify({title: newTitle.trim()})
  })
  .then(function() {
    bp.title = newTitle.trim();
    showToast('Renamed successfully', 'success');
    loadDashboardData(); // refresh the list
  })
  .catch(function(e) {
    showToast('Rename failed: ' + e.message, 'error');
  });
}
```

Verify the existing `renameBlueprintModal` function works correctly. If it already exists and looks correct, check:
- Is `fetchWithAuth` being used (not plain `fetch`)?
- Is the body `{title: newTitle}` (not `{name: newTitle}` or some other field)?
- Does it refresh the UI after success?
- Does it show errors on failure?

Fix whatever is broken.

- [ ] **Step 3: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add static/index.html
git commit -m "fix: wire blueprint rename to API and refresh UI on success"
```

---

## Summary

After completing this plan:
1. Download button uses fetch + Blob — no navigation, no state loss
2. Block-format blueprints download via `/export/zip` endpoint
3. Legacy blueprints recover files from Cloud Storage when session is empty
4. Empty files get a clear error instead of an empty ZIP
5. Rename works and refreshes the dashboard

**Next:** Plan 3B (Visual Editor + Auto-save)
