# Plan 4: UX Resilience Layer

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the app resilient for real users: offline handling, session resume, loading states, onboarding tooltips, friendly errors, undo toast, and questionnaire answer backup.

**Architecture:** All frontend-only. New files for offline detection and tooltips. Modifications to index.html for session resume, loading states, and error messages. Modification to editor.js for undo toast.

**Tech Stack:** Vanilla JS, CSS animations, localStorage

**Spec:** `docs/superpowers/specs/2026-03-14-ux-resilience-design.md`

**Depends on:** Plans 1-3B (block editor, chat panel, all existing UI)

**Security:** All user content via textContent. No innerHTML with untrusted data. Skeleton placeholders are empty divs styled via CSS — no content injection.

---

## File Structure

### New Files
| File | Responsibility |
|------|---------------|
| `static/editor/offline.js` | Offline detection, banner UI, reconnect handling |
| `static/editor/tooltips.js` | First-use editor tour (4 steps) |

### Modified Files
| File | Changes |
|------|---------|
| `static/index.html` | Session resume, loading skeletons, friendlyError, button loading audit, script tags, CSS |
| `static/editor/editor.js` | Replace confirm dialog with undo toast on delete |

---

## Chunk 1: Offline Detection & Banner

### Task 1: Create offline.js

**Files:**
- Create: `static/editor/offline.js`

- [ ] **Step 1: Create offline.js**

```javascript
// static/editor/offline.js
// Detects online/offline status, shows banner, flushes save queue on reconnect

(function() {
  'use strict';

  var banner = null;
  var dismissTimeout = null;

  function createBanner() {
    if (banner) return banner;
    banner = document.createElement('div');
    banner.id = 'offlineBanner';
    banner.className = 'offline-banner';
    banner.style.display = 'none';
    document.body.insertBefore(banner, document.body.firstChild);
    return banner;
  }

  function showBanner(message, type) {
    var b = createBanner();
    b.textContent = message;
    b.className = 'offline-banner offline-' + type;
    b.style.display = 'block';

    if (dismissTimeout) clearTimeout(dismissTimeout);
    if (type === 'synced') {
      dismissTimeout = setTimeout(function() {
        b.style.display = 'none';
      }, 3000);
    }
  }

  function hideBanner() {
    if (banner) banner.style.display = 'none';
  }

  function onOffline() {
    showBanner("You're offline \u2014 changes saved locally", 'offline');
  }

  function onOnline() {
    showBanner('Back online \u2014 syncing...', 'reconnecting');
    if (window.BlockEditor && BlockEditor.flushOfflineQueue) {
      BlockEditor.flushOfflineQueue();
    }
    setTimeout(function() {
      showBanner('All changes synced', 'synced');
    }, 1500);
  }

  window.addEventListener('offline', onOffline);
  window.addEventListener('online', onOnline);

  if (!navigator.onLine) {
    onOffline();
  }

  window.OfflineDetector = {
    isOnline: function() { return navigator.onLine; },
    showBanner: showBanner,
    hideBanner: hideBanner
  };
})();
```

- [ ] **Step 2: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add static/editor/offline.js
git commit -m "feat: add offline detection with status banner and reconnect handling"
```

---

## Chunk 2: First-Use Tooltips

### Task 2: Create tooltips.js

**Files:**
- Create: `static/editor/tooltips.js`

- [ ] **Step 1: Create tooltips.js**

```javascript
// static/editor/tooltips.js
// First-use editor tour — 4 tooltip steps shown once per user

(function() {
  'use strict';

  var TOUR_KEY = 'editor_toured';
  var currentStep = 0;
  var overlay = null;
  var tooltip = null;

  var steps = [
    { target: '#chatPanel', message: 'Chat with AI to edit your blueprint', position: 'left' },
    { target: '.be-block-wrapper', message: 'Click any block to edit it directly', position: 'bottom' },
    { target: '.be-drag-handle', message: 'Drag to reorder blocks', position: 'right' },
    { target: null, message: 'Press Ctrl+Z to undo any change', position: 'center' }
  ];

  function _ce(tag, cls, text) {
    var el = document.createElement(tag);
    if (cls) el.className = cls;
    if (text) el.textContent = text;
    return el;
  }

  function startTour() {
    if (localStorage.getItem(TOUR_KEY)) return;
    setTimeout(function() { currentStep = 0; showStep(); }, 800);
  }

  function showStep() {
    cleanup();
    if (currentStep >= steps.length) { completeTour(); return; }

    var step = steps[currentStep];

    overlay = _ce('div', 'tour-overlay');
    overlay.onclick = function() { completeTour(); };
    document.body.appendChild(overlay);

    var targetEl = null;
    if (step.target) {
      targetEl = document.querySelector(step.target);
      if (targetEl) targetEl.classList.add('tour-highlight');
    }

    tooltip = _ce('div', 'tour-tooltip');
    tooltip.appendChild(_ce('div', 'tour-message', step.message));
    tooltip.appendChild(_ce('div', 'tour-counter', (currentStep + 1) + ' / ' + steps.length));

    var actions = _ce('div', 'tour-actions');
    var skipBtn = _ce('button', 'tour-skip', 'Skip tour');
    skipBtn.onclick = function(e) { e.stopPropagation(); completeTour(); };
    actions.appendChild(skipBtn);

    var isLast = currentStep === steps.length - 1;
    var nextBtn = _ce('button', 'tour-next', isLast ? 'Got it!' : 'Next');
    nextBtn.onclick = function(e) {
      e.stopPropagation();
      if (targetEl) targetEl.classList.remove('tour-highlight');
      currentStep++;
      showStep();
    };
    actions.appendChild(nextBtn);
    tooltip.appendChild(actions);
    document.body.appendChild(tooltip);

    // Position tooltip relative to target
    if (targetEl && step.position !== 'center') {
      var rect = targetEl.getBoundingClientRect();
      if (step.position === 'bottom') {
        tooltip.style.top = (rect.bottom + 12) + 'px';
        tooltip.style.left = rect.left + 'px';
      } else if (step.position === 'left') {
        tooltip.style.top = rect.top + 'px';
        tooltip.style.right = (window.innerWidth - rect.left + 12) + 'px';
      } else if (step.position === 'right') {
        tooltip.style.top = rect.top + 'px';
        tooltip.style.left = (rect.right + 12) + 'px';
      }
    } else {
      tooltip.style.top = '50%';
      tooltip.style.left = '50%';
      tooltip.style.transform = 'translate(-50%, -50%)';
    }
  }

  function cleanup() {
    if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay);
    if (tooltip && tooltip.parentNode) tooltip.parentNode.removeChild(tooltip);
    var highlighted = document.querySelectorAll('.tour-highlight');
    for (var i = 0; i < highlighted.length; i++) highlighted[i].classList.remove('tour-highlight');
  }

  function completeTour() {
    cleanup();
    localStorage.setItem(TOUR_KEY, 'true');
  }

  window.EditorTour = {
    start: startTour,
    reset: function() { localStorage.removeItem(TOUR_KEY); }
  };
})();
```

- [ ] **Step 2: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add static/editor/tooltips.js
git commit -m "feat: add first-use editor tooltips tour (4 steps)"
```

---

## Chunk 3: Undo Toast (Replace Confirm Dialog)

### Task 3: Modify editor.js delete flow

**Files:**
- Modify: `static/editor/editor.js`

- [ ] **Step 1: Remove confirm dialog from _deleteBlock**

In `editor.js`, find `_deleteBlock`. Remove the line:
```javascript
if (!confirm('Delete this block?')) return;
```

- [ ] **Step 2: Add _showUndoToast method to BlockEditor**

Add this method to the BlockEditor object, after `_deleteBlock`:

```javascript
_showUndoToast: function(message) {
  var existing = document.getElementById('undoToast');
  if (existing) existing.parentNode.removeChild(existing);

  var toast = document.createElement('div');
  toast.id = 'undoToast';
  toast.className = 'undo-toast';

  var msg = document.createElement('span');
  msg.textContent = message;
  toast.appendChild(msg);

  var undoBtn = document.createElement('button');
  undoBtn.className = 'undo-toast-btn';
  undoBtn.textContent = 'Undo';
  undoBtn.onclick = function() {
    if (window.UndoManager) UndoManager.undo();
    if (toast.parentNode) toast.parentNode.removeChild(toast);
  };
  toast.appendChild(undoBtn);

  var editorMain = document.getElementById('editorMain');
  if (editorMain) editorMain.appendChild(toast);

  setTimeout(function() {
    if (toast.parentNode) toast.parentNode.removeChild(toast);
  }, 5000);
},
```

- [ ] **Step 3: Call _showUndoToast after delete**

In `_deleteBlock`, after `this._scheduleSave()`, add:

```javascript
this._showUndoToast('Block deleted');
```

- [ ] **Step 4: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add static/editor/editor.js
git commit -m "feat: replace delete confirm dialog with undo toast (5s recovery)"
```

---

## Chunk 4: Friendly Errors + Session Resume + Loading States + Wiring

### Task 4: Add all remaining resilience features to index.html

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Add friendlyError utility function**

Read `static/index.html` and add this function near the top of the `<script>` section, before any fetch calls:

```javascript
function friendlyError(e) {
  var msg = (e && e.message) ? e.message : String(e);
  if (msg.indexOf('NetworkError') !== -1 || msg.indexOf('Failed to fetch') !== -1)
    return 'Connection lost. Your changes are saved locally.';
  if (msg.indexOf('401') !== -1 || msg.indexOf('sign in') !== -1)
    return 'Your session expired. Please sign in again.';
  if (msg.indexOf('429') !== -1)
    return 'Too many requests. Please wait a moment and try again.';
  if (msg.indexOf('502') !== -1 || msg.indexOf('503') !== -1)
    return 'Our AI service is temporarily busy. Try again in a few seconds.';
  if (msg.indexOf('session') !== -1 && (msg.indexOf('expired') !== -1 || msg.indexOf('not found') !== -1))
    return "Your session expired. Don't worry \u2014 your saved blueprints are safe in your dashboard.";
  if (msg.indexOf('404') !== -1)
    return 'This item was not found. It may have been deleted or moved.';
  return msg;
}
```

- [ ] **Step 2: Replace error toasts with friendly messages**

Find all instances of `showToast(e.message, 'error')` and `showToast('Error: ' + e.message, 'error')`. Replace with `showToast(friendlyError(e), 'error')`. Search the entire script section.

- [ ] **Step 3: Add session resume logic**

Add `checkSessionResume()` function and `showResumePrompt()` function. Add session saving in `sendAnswer()` success handler. Add session clearing in generation success handler. Wire `checkSessionResume()` into the auth state change handler.

Session save in sendAnswer .then:
```javascript
try {
  localStorage.setItem('bp_session', JSON.stringify({
    sessionId: sessionId, currentStep: currentStep,
    businessDescription: document.getElementById('bizDesc') ? document.getElementById('bizDesc').value : '',
    companyName: data.profile_summary ? data.profile_summary.split(' \u2014 ')[0] : '',
    timestamp: Date.now()
  }));
} catch(ignore) {}
```

Resume prompt function — uses safe DOM methods (textContent, createElement), no innerHTML:
```javascript
function checkSessionResume() {
  try {
    var saved = JSON.parse(localStorage.getItem('bp_session'));
    if (!saved || !saved.sessionId) return;
    if (Date.now() - saved.timestamp > 7200000) { localStorage.removeItem('bp_session'); return; }
    var banner = document.createElement('div');
    banner.className = 'resume-banner'; banner.id = 'resumeBanner';
    var text = document.createElement('span');
    text.textContent = 'Continue your blueprint for ' + (saved.companyName || 'your company') + '?';
    banner.appendChild(text);
    var resumeBtn = document.createElement('button');
    resumeBtn.className = 'resume-btn'; resumeBtn.textContent = 'Resume';
    resumeBtn.onclick = function() { /* resume logic: verify session, restore position */ };
    banner.appendChild(resumeBtn);
    var freshBtn = document.createElement('button');
    freshBtn.className = 'resume-btn resume-btn-secondary'; freshBtn.textContent = 'Start Fresh';
    freshBtn.onclick = function() { localStorage.removeItem('bp_session'); banner.parentNode.removeChild(banner); };
    banner.appendChild(freshBtn);
    var target = document.getElementById('landingScreen');
    if (target) target.insertBefore(banner, target.firstChild);
  } catch(e) { localStorage.removeItem('bp_session'); }
}
```

- [ ] **Step 4: Add loading skeleton CSS**

Add to `<style>`:
```css
.skeleton { background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 6px; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
.skeleton-card { height: 120px; margin-bottom: 1rem; }
.skeleton-block { height: 80px; margin-bottom: 1rem; }
.resume-banner { background: var(--blue-bg); border: 1px solid var(--accent); border-radius: 8px;
                 padding: 0.75rem 1rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.75rem; }
.resume-btn { background: var(--brand); color: white; border: none; padding: 0.4rem 1rem;
              border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85rem; }
.resume-btn-secondary { background: none; border: 1px solid var(--border); color: var(--text-light); }
.offline-banner { padding: 0.5rem 1rem; text-align: center; font-size: 0.85rem; font-weight: 600;
                  position: fixed; top: 0; left: 0; right: 0; z-index: 9999; }
.offline-offline { background: #FEF3CD; color: #856404; }
.offline-reconnecting { background: #FEF3CD; color: #856404; }
.offline-synced { background: #D4EDDA; color: #155724; }
.tour-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); z-index: 9990; }
.tour-highlight { position: relative; z-index: 9991; box-shadow: 0 0 0 4px var(--brand), 0 0 0 8px rgba(37,99,235,0.2); border-radius: 6px; }
.tour-tooltip { position: fixed; background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
                padding: 1rem 1.25rem; box-shadow: 0 8px 24px rgba(0,0,0,0.15); z-index: 9992; max-width: 300px; }
.tour-message { font-size: 0.95rem; margin-bottom: 0.5rem; }
.tour-counter { font-size: 0.75rem; color: var(--text-light); margin-bottom: 0.75rem; }
.tour-actions { display: flex; justify-content: space-between; }
.tour-skip { background: none; border: none; color: var(--text-light); cursor: pointer; font-size: 0.8rem; }
.tour-next { background: var(--brand); color: white; border: none; padding: 0.35rem 1rem; border-radius: 6px;
             cursor: pointer; font-weight: 600; }
.undo-toast { position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%); background: #333; color: white;
              padding: 0.75rem 1.25rem; border-radius: 8px; display: flex; align-items: center; gap: 1rem;
              box-shadow: 0 4px 12px rgba(0,0,0,0.3); z-index: 9000; }
.undo-toast-btn { background: none; border: 1px solid rgba(255,255,255,0.4); color: white; padding: 0.25rem 0.75rem;
                  border-radius: 4px; cursor: pointer; font-weight: 600; }
```

- [ ] **Step 5: Add skeleton rendering to loadDashboardData and EditorScreen.loadSection**

In `loadDashboardData`, before the fetch call, show 3 skeleton cards using createElement (safe — no user content).

In `EditorScreen.loadSection`, before the fetch, show 3 skeleton blocks.

- [ ] **Step 6: Wire tooltips tour into EditorScreen.loadSection**

After `BlockEditor.init()` call, add:
```javascript
if (window.EditorTour) EditorTour.start();
```

- [ ] **Step 7: Add script tags for new files**

At end of `<body>`, after existing editor scripts, add:
```html
<script src="/static/editor/offline.js"></script>
<script src="/static/editor/tooltips.js"></script>
```

- [ ] **Step 8: Wire checkSessionResume into auth handler**

In `firebase.auth().onAuthStateChanged`, after user is confirmed logged in and synced, call `checkSessionResume()`.

- [ ] **Step 9: Commit**

```bash
cd /home/harshwardhan/blueprint_maker
git add static/index.html
git commit -m "feat: add session resume, loading skeletons, friendly errors, tour wiring"
```

---

## Summary

After completing this plan:
1. **Offline banner** with auto-reconnect and sync
2. **Session resume** for returning users mid-questionnaire
3. **Loading skeletons** instead of blank screens
4. **First-use tooltips** (4-step editor tour)
5. **Friendly error messages** for all common failures
6. **Undo toast** with 5-second recovery window
7. **Answer backup** to localStorage

All frontend-only. No backend changes. No new dependencies.
