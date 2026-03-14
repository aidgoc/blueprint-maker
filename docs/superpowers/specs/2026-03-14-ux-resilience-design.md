# UX Resilience Layer — Design Spec

**Date:** 2026-03-14
**Status:** Approved
**Priority:** All items are P1 — these are baseline requirements for real users

## Problem

The app works for developers who understand what's happening, but real users will:
- Close the tab mid-questionnaire and lose progress
- Have their internet drop during editing or generation
- Not know how to use the editor (no onboarding)
- See cryptic error messages and not know what to do
- Accidentally delete blocks with no easy recovery
- Stare at blank screens wondering if something is loading

## Solution: Frontend-Only Resilience Layer

Seven features, all frontend-only (no backend changes needed). Each is a small, independent JS file.

---

## 1. Offline Detection & Recovery

**File:** `static/editor/offline.js`

Listen to `navigator.onLine` and `online`/`offline` events. Show/hide a top banner.

**Banner states:**
- Offline: yellow banner — "You're offline — changes saved locally"
- Reconnecting: yellow banner — "Back online — syncing..."
- Synced: green flash — "All changes synced" (auto-dismiss after 3s)

**Generation resilience:** If offline during generation polling, pause polling. On reconnect, resume polling from where it left off.

**Integration:** The offline queue from `editor.js` (`BlockEditor.flushOfflineQueue()`) is called on reconnect.

---

## 2. Session Resume (Questionnaire)

**Implementation:** In `static/index.html` (inline, small)

**Save:** After each answer submission, write to localStorage:
```json
{
  "bp_session": {
    "sessionId": "abc123",
    "currentStep": 3,
    "businessDescription": "HVAC company...",
    "companyName": "Acme Corp",
    "timestamp": 1710400000000
  }
}
```

**Resume:** On page load (in the auth state change handler), if `bp_session` exists and is < 2 hours old:
- Show banner: "Continue your blueprint for Acme Corp?" with [Resume] [Start Fresh] buttons
- Resume: navigate to questionnaire, call `/api/answer` with `back: false` to verify session, restore position
- Start Fresh: clear localStorage, show landing

**Clear:** Remove `bp_session` on generation complete or explicit "Start Fresh."

---

## 3. Loading States

**Implementation:** CSS in `static/index.html` + small JS additions

**Button loading:** Every API-triggering button already has some loading logic. Audit and ensure consistency:
- Set `disabled = true` + add `.loading` class (shows spinner via CSS)
- Re-enable on success or error (never leave disabled)

**Skeleton screens:**
- Dashboard: 3 pulsing grey card placeholders while `/api/user/blueprints` loads
- Editor sidebar: 4 pulsing bars while sections load
- Editor main: 3 pulsing block placeholders while section content loads

**CSS-only skeletons:**
```css
.skeleton { background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 6px; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
```

---

## 4. First-Use Tooltips

**File:** `static/editor/tooltips.js`

**Trigger:** First time user opens the editor screen (tracked via `localStorage.getItem('editor_toured')`)

**Sequence (4 steps):**
1. Highlight chat panel → "Chat with AI to edit your blueprint"
2. Highlight first block → "Click any block to edit it directly"
3. Highlight drag handle → "Drag to reorder blocks"
4. General tooltip → "Press Ctrl+Z to undo any change"

**UI:** Small tooltip div with arrow, message text, step counter "1/4", and [Next] / [Got it] buttons. Semi-transparent overlay behind to focus attention.

**Behavior:**
- Each step highlights the target element (add a temporary CSS class)
- "Next" advances to next step
- "Got it" on last step closes tour, sets `localStorage.setItem('editor_toured', 'true')`
- User can click "Skip tour" at any point

---

## 5. Human Error Messages

**Implementation:** Utility function in `static/index.html` (inline)

```javascript
function friendlyError(error) {
  var msg = error.message || String(error);
  if (msg.includes('NetworkError') || msg.includes('Failed to fetch'))
    return 'Connection lost. Your changes are saved locally.';
  if (msg.includes('401') || msg.includes('sign in'))
    return 'Your session expired. Please sign in again.';
  if (msg.includes('429'))
    return 'Too many requests. Please wait a moment and try again.';
  if (msg.includes('502') || msg.includes('503'))
    return 'Our AI service is temporarily busy. Try again in a few seconds.';
  if (msg.includes('session') && msg.includes('expired'))
    return "Your session expired. Don't worry — your saved blueprints are safe in your dashboard.";
  if (msg.includes('404'))
    return 'This item was not found. It may have been deleted or moved.';
  return msg; // fallback to original
}
```

Replace all `showToast(e.message, 'error')` calls with `showToast(friendlyError(e), 'error')`.

---

## 6. Undo Toast (Delete Recovery)

**Implementation:** Modify `BlockEditor._deleteBlock` in `editor.js`

**Current:** `confirm('Delete this block?')` → delete immediately
**New:** Delete immediately (no confirm dialog) → show toast "Block deleted. [Undo]" for 5 seconds

**Toast UI:**
- Dark background toast at bottom of editor
- Text: "Block deleted"
- [Undo] button that calls `UndoManager.undo()`
- Auto-dismiss after 5 seconds
- If another delete happens within 5s, replace the toast

---

## 7. Auto-Save Questionnaire Answers

**Implementation:** In `static/index.html` (part of session resume feature)

On every `sendAnswer()` success, save the current answer to the `bp_session` localStorage object. This means if the server loses the session (restart, cold start), and the user returns, we can offer to pre-fill their answers in a new session.

**Flow on session loss:**
1. User returns, clicks "Resume"
2. Server returns 404 (session expired)
3. Frontend shows: "Your previous session expired, but we saved your answers. Starting fresh with your previous answers pre-filled."
4. Call `/api/start` with saved `businessDescription`
5. Auto-submit saved answers one by one via `/api/answer`

---

## Non-Goals

- No service worker / PWA (overkill for this stage)
- No localStorage encryption (no sensitive data stored — just answers and step position)
- No A/B testing of tooltip content
- No analytics on error rates (future consideration)

## File Summary

| File | Type | Purpose |
|------|------|---------|
| `static/editor/offline.js` | New | Offline detection, banner, reconnect handling |
| `static/editor/tooltips.js` | New | First-use editor tour (4 steps) |
| `static/editor/editor.js` | Modify | Remove confirm dialog from delete, add undo toast |
| `static/index.html` | Modify | Session resume, loading skeletons, friendlyError, button states |
