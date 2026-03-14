# Plan 5: Visual Redesign — App CSS + Blueprint Output + Legacy Renderer

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the visual identity from "functional developer tool" to "premium SaaS product" (app UI) and "corporate consulting deliverable" (blueprint output). Three coordinated CSS rewrites across the app frontend, block renderer, and legacy renderer — no JavaScript changes.

**Architecture:** App UI uses Inter + JetBrains Mono with a clean Notion/Linear-inspired palette. Blueprint output uses Crimson Pro + Source Sans 3 with a navy/gold consulting palette. All changes are CSS-only — class names referenced by JS are preserved, only visual properties change.

**Tech Stack:** Vanilla CSS (no preprocessors), Google Fonts CDN

**Spec:** `docs/superpowers/specs/2026-03-14-visual-redesign-design.md`

---

## File Structure

### Modified Files
| File | Changes |
|------|---------|
| `static/index.html` | Add Google Fonts `<link>` in `<head>`, replace entire `<style>` block with new design system CSS |
| `block_renderer.py` | Replace `BLOCK_CSS` constant with consulting-grade styles, add Google Fonts link in `render_section_to_html()`, update HTML structure in each renderer function |
| `renderer.py` | Replace `CSS_VARS` + `BASE_CSS` with navy/gold consulting palette |

### No New Files

### JS Class Names That MUST Be Preserved
These classes are toggled/added/removed by JavaScript and must keep their names:
- `.hidden` — display toggling throughout
- `.selected` — modal color picker
- `.active` — sidebar items, stage steps, dashboard folder cards, view toggle buttons
- `.done` — stage steps, gen steps
- Screen IDs: `#landingScreen`, `#authScreen`, `#appScreen`, `#dashboardScreen`, `#detailScreen`, `#editorScreen`
- All element IDs referenced by `getElementById()` (see CLAUDE.md)
- All `className =` assignments in JS (bp-card, bp-badge, dash-grid, file-list, modal, etc.)

---

## Chunk 1: App CSS Rewrite (static/index.html)

### Task 1: Add Google Fonts link and replace entire `<style>` block

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Add Google Fonts link tag in `<head>` before `<style>`**

Add this line after the `<title>` tag (line 6) and before `<style>` (line 7):

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

- [ ] **Step 2: Replace the entire `<style>` block (lines 7-885) with the new design system CSS**

Replace everything between `<style>` and `</style>` (inclusive) with:

```html
<style>
/* ══════════════════════════════════════════════════════════════
   Blueprint Maker — Design System v2
   Inter + JetBrains Mono | 8px grid | 12px card radius
   ══════════════════════════════════════════════════════════════ */

:root {
  /* Backgrounds */
  --bg: #FFFFFF;
  --bg-subtle: #F9FAFB;
  --bg-hover: #F3F4F6;

  /* Text */
  --text: #111827;
  --text-secondary: #6B7280;
  --text-tertiary: #9CA3AF;
  --text-muted: #9CA3AF; /* alias for tertiary — JS uses this name */
  --text-light: #9CA3AF; /* alias — editor/chat CSS uses this name */

  /* Brand */
  --brand: #2563EB;
  --brand-light: #DBEAFE;
  --brand-dark: #1D4ED8;
  --brand-hover: #1D4ED8; /* alias — JS-generated className uses this */

  /* Accent */
  --accent: #F59E0B;
  --accent-light: #FEF3C7;

  /* Surface */
  --surface: #FFFFFF;

  /* Borders */
  --border: #E5E7EB;
  --border-light: #F3F4F6;

  /* Status */
  --green: #059669;
  --green-light: #ECFDF5;
  --amber: #D97706;
  --amber-light: #FFFBEB;
  --red: #DC2626;
  --red-light: #FEF2F2;
  --purple: #8B5CF6;
  --purple-light: #F5F3FF;
  --teal: #14B8A6;
  --teal-light: #F0FDFA;

  /* Aliases for existing CSS that references these names */
  --blue-bg: #EFF6FF;
  --red-bg: #FEF2F2;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow: 0 1px 3px rgba(0,0,0,0.08);
  --shadow-lg: 0 4px 12px rgba(0,0,0,0.1);
}

* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg); color: var(--text); min-height: 100vh;
  font-size: 16px; line-height: 1.6;
  -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
}

/* ── Transitions (global) ── */
button, a, input, textarea, select {
  transition: all 150ms ease-out;
}
button:active:not(:disabled) {
  transform: scale(0.98);
}

/* ── Header ── */
.header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 24px 32px; position: relative; z-index: 10;
}
.wordmark {
  font-size: 20px; font-weight: 700; color: var(--text); letter-spacing: -0.5px;
}
.stage-counter {
  font-size: 14px; color: var(--text-tertiary); font-weight: 500;
}

/* ── Stage Progress ── */
.stage-progress {
  display: flex; align-items: center; justify-content: center;
  gap: 0; padding: 0 32px 32px; position: relative;
}
.stage-step {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  position: relative; z-index: 2;
}
.stage-dot {
  width: 12px; height: 12px; border-radius: 50%;
  border: 2px solid var(--border); background: var(--surface);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.stage-step.active .stage-dot {
  background: var(--brand); border-color: var(--brand);
  box-shadow: 0 0 0 4px rgba(37,99,235,0.15);
}
.stage-step.done .stage-dot { background: var(--green); border-color: var(--green); }
.stage-label {
  font-size: 14px; font-weight: 500; color: var(--text-tertiary);
  letter-spacing: 0.2px; transition: color 0.3s;
}
.stage-step.active .stage-label { color: var(--brand); font-weight: 600; }
.stage-step.done .stage-label { color: var(--green); font-weight: 600; }
.stage-line {
  width: 80px; height: 2px; background: var(--border); flex-shrink: 0;
  margin-bottom: 22px; transition: background 0.4s;
}
.stage-line.done { background: var(--green); }

/* ── Landing ── */
.landing-screen {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: calc(100vh - 80px); padding: 0 24px 64px; text-align: center;
}
.landing-screen h2 {
  font-size: 40px; font-weight: 600; color: var(--text);
  letter-spacing: -1px; line-height: 1.15; margin-bottom: 16px;
}
.landing-screen .tagline {
  font-size: 18px; color: var(--text-secondary); max-width: 480px;
  line-height: 1.6; margin-bottom: 48px; font-weight: 400;
}
.start-form { max-width: 560px; width: 100%; }
.start-form textarea {
  width: 100%; padding: 20px 24px; border: 1px solid var(--border); border-radius: 12px;
  font-size: 16px; font-family: inherit; resize: vertical; min-height: 160px; outline: none;
  transition: border-color 200ms, box-shadow 200ms; color: var(--text); background: var(--surface);
  line-height: 1.6;
}
.start-form textarea:focus {
  border-color: var(--brand); box-shadow: 0 0 0 3px var(--brand-light);
}
.start-form textarea::placeholder { color: var(--text-tertiary); }
.start-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 32px; background: var(--accent); color: #1F2937; border: none; border-radius: 8px;
  font-size: 15px; font-weight: 600; cursor: pointer; transition: all 150ms ease-out; font-family: inherit;
  margin-top: 16px; height: 48px;
}
.start-btn:hover { background: #E8910A; transform: translateY(-1px); box-shadow: var(--shadow-lg); }
.start-btn:active { transform: scale(0.98); }

.features {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px; max-width: 680px; width: 100%; margin-top: 56px;
}
.feature-card {
  background: var(--surface); border-radius: 12px; padding: 24px;
  box-shadow: var(--shadow-sm); text-align: left; transition: box-shadow 150ms ease-out;
}
.feature-card:hover { box-shadow: var(--shadow); }
.feature-dot { width: 8px; height: 8px; border-radius: 50%; margin-bottom: 16px; }
.feature-card:nth-child(1) .feature-dot { background: var(--brand); }
.feature-card:nth-child(2) .feature-dot { background: var(--green); }
.feature-card:nth-child(3) .feature-dot { background: var(--accent); }
.feature-card:nth-child(4) .feature-dot { background: var(--purple); }
.feature-card h4 { font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 8px; }
.feature-card p { font-size: 14px; color: var(--text-secondary); line-height: 1.6; }

/* ── Question Screen ── */
.question-screen {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: calc(100vh - 160px); padding: 0 24px;
}
.question-container {
  max-width: 640px; width: 100%;
  animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.question-number {
  font-size: 14px; font-weight: 500; color: var(--text-secondary); margin-bottom: 12px;
  letter-spacing: 0.3px;
}
.question-text {
  font-size: 24px; font-weight: 600; color: var(--text); line-height: 1.35;
  letter-spacing: -0.3px; margin-bottom: 32px; max-width: 580px;
}
.answer-area textarea {
  width: 100%; padding: 16px 20px; border: 1px solid var(--border); border-radius: 12px;
  font-size: 16px; font-family: inherit; resize: none; outline: none;
  transition: border-color 200ms, box-shadow 200ms; color: var(--text); background: var(--surface);
  min-height: 100px; line-height: 1.6; overflow: hidden;
}
.answer-area textarea:focus {
  border-color: var(--brand); box-shadow: 0 0 0 3px var(--brand-light);
}
.answer-area textarea::placeholder { color: var(--text-tertiary); }
.answer-actions {
  display: flex; justify-content: flex-end; align-items: center; gap: 16px; margin-top: 16px;
}
.key-hint { font-size: 14px; color: var(--text-tertiary); }
.continue-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 12px 24px; background: var(--brand); color: #fff; border: none; border-radius: 8px;
  font-size: 14px; font-weight: 600; cursor: pointer; transition: all 150ms ease-out; font-family: inherit;
}
.continue-btn:hover { background: var(--brand-dark); }
.continue-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.continue-btn .spinner {
  width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff; border-radius: 50%; animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Research Interstitial ── */
.research-screen {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: calc(100vh - 160px); padding: 0 24px; text-align: center;
}
.research-pulse {
  width: 48px; height: 48px; border-radius: 50%; background: var(--brand);
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; margin-bottom: 24px;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.1); }
}
.research-screen h3 {
  font-size: 20px; font-weight: 600; color: var(--text); margin-bottom: 8px;
}
.research-screen .research-sub {
  font-size: 14px; color: var(--text-secondary); max-width: 400px; line-height: 1.6;
}

/* ── Findings Card ── */
.findings-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 24px 28px; max-width: 560px; width: 100%; margin-top: 32px; text-align: left;
  animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-sm);
}
.findings-card h4 {
  font-size: 14px; font-weight: 600; color: var(--green); margin-bottom: 12px;
  display: flex; align-items: center; gap: 8px;
}
.findings-card .finding-row {
  font-size: 14px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 8px;
}
.findings-tags {
  display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px;
}
.f-tag {
  font-size: 14px; padding: 6px 14px; border-radius: 100px;
  background: var(--bg-subtle); color: var(--brand); font-weight: 500;
}
.stage-flow { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 16px; }
.stage-item {
  padding: 6px 12px; background: var(--green-light); border: 1px solid rgba(5,150,105,0.2);
  border-radius: 8px; font-size: 14px; font-weight: 500; color: #065F46;
}
.arrow-sep { color: var(--text-tertiary); font-weight: 400; font-size: 14px; }
.findings-continue {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 12px 24px; background: var(--brand); color: #fff; border: none; border-radius: 8px;
  font-size: 14px; font-weight: 600; cursor: pointer; transition: all 150ms ease-out; font-family: inherit;
  margin-top: 24px; width: 100%;  justify-content: center;
}
.findings-continue:hover { background: var(--brand-dark); }

/* ── Profile Summary ── */
.profile-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 32px; max-width: 640px; width: 100%;
  animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-sm);
}
.profile-card h4 { font-size: 16px; font-weight: 700; color: var(--green); margin-bottom: 8px; }
.profile-card .summary-text {
  font-size: 14px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 16px;
}
.profile-card .research-stats {
  font-size: 14px; color: var(--text-secondary); line-height: 1.6;
  padding: 16px; background: var(--bg-subtle); border-radius: 8px; margin-bottom: 16px;
}
.dept-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.dept-tag {
  font-size: 14px; padding: 6px 14px; border-radius: 100px;
  background: var(--brand-light); color: var(--brand); font-weight: 500;
}
.section-label {
  font-size: 14px; color: var(--text-tertiary); font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; margin-top: 16px;
}
.generate-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 32px; background: var(--brand); color: #fff; border: none; border-radius: 8px;
  font-size: 15px; font-weight: 600; cursor: pointer; transition: all 150ms ease-out; font-family: inherit;
  margin-top: 24px;
}
.generate-btn:hover { background: var(--brand-dark); transform: translateY(-1px); box-shadow: var(--shadow-lg); }
.generate-btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; box-shadow: none; }

/* ── Generation Screen ── */
.gen-screen {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: calc(100vh - 160px); padding: 0 24px; text-align: center;
}
.gen-pulse {
  width: 40px; height: 40px; border-radius: 50%; background: var(--brand);
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; margin-bottom: 24px;
}
.gen-screen h3 { font-size: 20px; font-weight: 600; color: var(--text); margin-bottom: 8px; }
.gen-screen .gen-sub { font-size: 14px; color: var(--text-secondary); margin-bottom: 24px; }
.gen-steps { text-align: left; max-width: 320px; width: 100%; }
.gen-step {
  font-size: 14px; color: var(--text-tertiary); padding: 8px 0;
  display: flex; align-items: center; gap: 8px;
}
.gen-step.done { color: var(--green); }
.gen-step.active { color: var(--text); font-weight: 500; }

/* ── Results ── */
.result-screen {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: calc(100vh - 160px); padding: 0 24px;
}
.result-card {
  background: var(--surface); border-radius: 12px;
  padding: 32px; max-width: 600px; width: 100%;
  animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-sm);
}
.result-card h3 {
  font-size: 20px; font-weight: 700; color: var(--text); margin-bottom: 24px;
}
.file-list { list-style: none; padding: 0; }
.file-list li {
  padding: 16px; border-radius: 12px; margin-bottom: 8px;
  display: flex; justify-content: space-between; align-items: center; font-size: 14px;
  transition: background 150ms ease-out; background: var(--bg-subtle);
}
.file-list li:hover { background: var(--brand-light); }
.file-list li .fname { font-weight: 600; color: var(--text); display: flex; align-items: center; gap: 8px; }
.file-list li .fname::before {
  content: ''; display: inline-block; width: 8px; height: 8px; border-radius: 2px; background: var(--brand);
}
.file-list li a {
  color: var(--brand); text-decoration: none; font-weight: 600; font-size: 14px;
}
.file-list li a:hover { text-decoration: underline; }
.download-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 32px; background: var(--green); color: #fff; border: none;
  border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer;
  margin-top: 24px; text-decoration: none; transition: all 150ms ease-out; font-family: inherit;
}
.download-btn:hover { background: #047857; transform: translateY(-1px); box-shadow: var(--shadow-lg); }
.restart-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 12px 24px; background: transparent; color: var(--text-secondary); border: 1px solid var(--border);
  border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer;
  margin-top: 12px; text-decoration: none; transition: all 150ms ease-out; font-family: inherit;
}
.restart-btn:hover { border-color: var(--text-secondary); color: var(--text); }

.hidden { display: none !important; }

/* ── Toast Notifications ── */
.toast-container {
  position: fixed; bottom: 24px; right: 24px; z-index: 9999;
  display: flex; flex-direction: column-reverse; gap: 8px;
}
.toast {
  padding: 16px 20px; border-radius: 12px; font-size: 14px; font-weight: 500;
  color: #fff; box-shadow: var(--shadow-lg); animation: toastIn 0.3s ease, toastOut 0.3s ease 2.7s forwards;
  max-width: 360px; font-family: inherit;
}
.toast.success { background: var(--green); }
.toast.error { background: #1F2937; }
.toast.info { background: #1F2937; }
@keyframes toastIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes toastOut { from { opacity: 1; } to { opacity: 0; transform: translateY(12px); } }

/* ── Auth Screen ── */
.auth-screen {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: calc(100vh - 80px); padding: 0 24px 64px;
}
.auth-card {
  background: var(--surface); border-radius: 16px;
  padding: 40px 36px; max-width: 420px; width: 100%; box-shadow: var(--shadow);
  animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.auth-wordmark {
  font-size: 28px; font-weight: 700; color: var(--text); text-align: center;
  letter-spacing: -0.8px; margin-bottom: 8px;
}
.auth-tagline {
  font-size: 14px; color: var(--text-secondary); text-align: center; margin-bottom: 32px;
}
.google-btn {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; padding: 12px 20px; background: var(--surface); color: var(--text);
  border: 1px solid var(--border); border-radius: 8px; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: all 150ms ease-out; font-family: inherit;
}
.google-btn:hover { background: var(--bg-subtle); border-color: #D1D5DB; box-shadow: var(--shadow-sm); }
.google-btn svg { width: 18px; height: 18px; }
.auth-divider {
  display: flex; align-items: center; gap: 16px; margin: 24px 0;
}
.auth-divider span { font-size: 14px; color: var(--text-tertiary); font-weight: 500; white-space: nowrap; }
.auth-divider::before, .auth-divider::after {
  content: ''; flex: 1; height: 1px; background: var(--border);
}
.auth-form { display: flex; flex-direction: column; gap: 12px; }
.auth-input {
  width: 100%; padding: 12px 14px; border: 1px solid var(--border); border-radius: 6px;
  font-size: 14px; font-family: inherit; outline: none; color: var(--text);
  background: var(--surface); transition: border-color 200ms, box-shadow 200ms;
}
.auth-input:focus { border-color: var(--brand); box-shadow: 0 0 0 3px var(--brand-light); }
.auth-input::placeholder { color: var(--text-tertiary); }
.auth-submit {
  width: 100%; padding: 12px 20px; background: var(--brand); color: #fff; border: none;
  border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer;
  transition: all 150ms ease-out; font-family: inherit; margin-top: 4px;
}
.auth-submit:hover { background: var(--brand-dark); }
.auth-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.auth-error {
  color: var(--red); font-size: 14px; text-align: center; min-height: 20px; margin-top: 4px;
}
.auth-toggle {
  text-align: center; margin-top: 24px; font-size: 14px; color: var(--text-secondary);
}
.auth-toggle a {
  color: var(--brand); cursor: pointer; font-weight: 600; text-decoration: none;
}
.auth-toggle a:hover { text-decoration: underline; }
.auth-forgot {
  text-align: right; margin-top: -4px;
}
.auth-forgot a {
  font-size: 14px; color: var(--brand); cursor: pointer; text-decoration: none; font-weight: 500;
}
.auth-forgot a:hover { text-decoration: underline; }
.auth-skip {
  text-align: center; margin-top: 16px;
}
.auth-skip a {
  font-size: 14px; color: var(--text-tertiary); cursor: pointer; text-decoration: none;
}
.auth-skip a:hover { color: var(--text-secondary); text-decoration: underline; }

/* ── Dashboard ── */
.dash-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 32px; border-bottom: 1px solid var(--border); background: var(--surface);
  position: sticky; top: 0; z-index: 100;
}
.dash-header .wordmark { font-size: 20px; font-weight: 700; color: var(--text); letter-spacing: -0.5px; }
.dash-user-area { display: flex; align-items: center; gap: 12px; position: relative; }
.dash-avatar {
  width: 36px; height: 36px; border-radius: 50%; background: var(--brand);
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 600; cursor: pointer; overflow: hidden;
  border: 2px solid var(--border); transition: border-color 150ms;
}
.dash-avatar:hover { border-color: var(--brand); }
.dash-avatar img { width: 100%; height: 100%; object-fit: cover; }
.dash-user-name {
  font-size: 14px; font-weight: 500; color: var(--text); cursor: pointer;
}
.dash-dropdown {
  position: absolute; top: 48px; right: 0; background: var(--surface);
  border: 1px solid var(--border); border-radius: 12px; box-shadow: var(--shadow-lg);
  min-width: 180px; padding: 8px 0; z-index: 200;
  animation: slideUp 0.15s ease;
}
.dash-dropdown-item {
  padding: 10px 16px; font-size: 14px; color: var(--text); cursor: pointer;
  transition: background 100ms; display: block; width: 100%; text-align: left;
  border: none; background: none; font-family: inherit;
}
.dash-dropdown-item:hover { background: var(--bg-hover); }
.dash-dropdown-item.danger { color: var(--red); }

.dash-content { max-width: 1200px; margin: 0 auto; padding: 32px; }

.dash-welcome {
  font-size: 28px; font-weight: 600; color: var(--text); letter-spacing: -0.5px;
  margin-bottom: 24px;
}

.dash-stats {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 32px;
}
.dash-stat-card {
  background: var(--surface); border-radius: 12px;
  padding: 24px; box-shadow: var(--shadow-sm);
}
.dash-stat-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 28px; font-weight: 500; color: var(--text); letter-spacing: -0.5px;
}
.dash-stat-label { font-size: 14px; color: var(--text-tertiary); font-weight: 500; margin-top: 4px; }

.dash-action-bar {
  display: flex; align-items: center; gap: 12px; margin-bottom: 24px; flex-wrap: wrap;
}
.dash-new-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 24px; background: var(--brand); color: #fff; border: none;
  border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer;
  transition: all 150ms ease-out; font-family: inherit;
}
.dash-new-btn:hover { background: var(--brand-dark); transform: translateY(-1px); box-shadow: var(--shadow); }
.dash-search {
  flex: 1; min-width: 200px; padding: 10px 16px; border: 1px solid var(--border);
  border-radius: 8px; font-size: 14px; outline: none; font-family: inherit;
  color: var(--text); background: var(--surface); transition: border-color 200ms;
}
.dash-search:focus { border-color: var(--brand); box-shadow: 0 0 0 3px var(--brand-light); }
.dash-view-toggle {
  display: flex; border: 1px solid var(--border); border-radius: 8px; overflow: hidden;
}
.dash-view-btn {
  padding: 8px 12px; background: var(--surface); border: none; cursor: pointer;
  color: var(--text-tertiary); transition: all 150ms ease-out; display: flex; align-items: center;
}
.dash-view-btn.active { background: var(--brand-light); color: var(--brand); }
.dash-view-btn:hover { color: var(--text); }
.dash-view-btn + .dash-view-btn { border-left: 1px solid var(--border); }

/* Folders */
.dash-folders {
  display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; align-items: center;
}
.dash-folder-card {
  display: flex; align-items: center; gap: 10px; padding: 10px 16px;
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  cursor: pointer; transition: all 150ms ease-out; font-size: 14px; font-weight: 500;
  color: var(--text);
}
.dash-folder-card:hover { box-shadow: var(--shadow); }
.dash-folder-card.active { background: var(--brand-light); border-color: var(--brand); }
.dash-folder-count {
  font-size: 14px; color: var(--text-tertiary); background: var(--bg-subtle);
  padding: 2px 8px; border-radius: 100px; font-weight: 600;
  font-family: 'JetBrains Mono', monospace; font-size: 12px;
}
.dash-folder-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.dash-add-folder {
  display: flex; align-items: center; gap: 8px; padding: 10px 16px;
  background: none; border: 1px dashed var(--border); border-radius: 12px;
  cursor: pointer; font-size: 14px; color: var(--text-tertiary); font-family: inherit;
  transition: all 150ms ease-out;
}
.dash-add-folder:hover { border-color: var(--brand); color: var(--brand); }

/* Blueprint grid */
.dash-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.bp-card {
  background: var(--surface); border-radius: 12px;
  padding: 24px; transition: all 150ms ease-out; cursor: pointer; position: relative;
  box-shadow: var(--shadow-sm);
}
.bp-card:hover { box-shadow: var(--shadow); }
.bp-card-title {
  font-size: 16px; font-weight: 600; color: var(--text); margin-bottom: 8px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.bp-card-date { font-size: 14px; color: var(--text-tertiary); margin-bottom: 12px; }
.bp-card-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.bp-badge {
  font-size: 14px; padding: 4px 12px; border-radius: 100px; font-weight: 500;
}
.bp-badge.completed { background: var(--green-light); color: #065F46; }
.bp-badge.generating { background: var(--amber-light); color: #92400E; }
.bp-badge.failed { background: var(--red-light); color: #991B1B; }
.bp-badge.folder-tag { background: var(--brand-light); color: var(--brand); }
.bp-card-actions {
  position: absolute; top: 12px; right: 12px;
  opacity: 0; transition: opacity 150ms;
}
.bp-card:hover .bp-card-actions { opacity: 1; }
.bp-menu-btn {
  width: 32px; height: 32px; border-radius: 8px; border: none; background: none;
  cursor: pointer; color: var(--text-tertiary); font-size: 16px; display: flex;
  align-items: center; justify-content: center; transition: all 150ms;
}
.bp-menu-btn:hover { background: var(--bg-hover); color: var(--text); }
.bp-menu {
  position: absolute; top: 36px; right: 0; background: var(--surface);
  border: 1px solid var(--border); border-radius: 12px; box-shadow: var(--shadow-lg);
  min-width: 180px; padding: 8px 0; z-index: 50;
}
.bp-menu-item {
  padding: 10px 16px; font-size: 14px; color: var(--text); cursor: pointer;
  transition: background 100ms; display: block; width: 100%; text-align: left;
  border: none; background: none; font-family: inherit;
}
.bp-menu-item:hover { background: var(--bg-hover); }
.bp-menu-item.danger { color: var(--red); }
.bp-menu-item.danger:hover { background: var(--red-light); }
.bp-share-icon { color: var(--brand); font-size: 14px; }

/* List view */
.dash-list { width: 100%; }
.dash-list-table {
  width: 100%; border-collapse: collapse; font-size: 14px;
}
.dash-list-table th {
  text-align: left; padding: 12px 16px; font-size: 14px; font-weight: 600;
  color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
}
.dash-list-table td {
  padding: 16px; border-bottom: 1px solid var(--border); color: var(--text);
}
.dash-list-table tr:hover td { background: var(--bg-hover); }
.dash-list-table .td-name { font-weight: 600; cursor: pointer; }
.dash-list-table .td-name:hover { color: var(--brand); }

/* Empty state */
.dash-empty {
  text-align: center; padding: 80px 24px;
}
.dash-empty-icon {
  width: 64px; height: 64px; margin: 0 auto 24px; background: var(--brand-light);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 28px;
}
.dash-empty h3 { font-size: 20px; font-weight: 600; color: var(--text); margin-bottom: 8px; }
.dash-empty p { font-size: 14px; color: var(--text-secondary); margin-bottom: 24px; }

/* Modal */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4); backdrop-filter: blur(4px); z-index: 500; display: flex;
  align-items: center; justify-content: center; padding: 24px;
  animation: fadeIn 0.15s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.modal {
  background: var(--surface); border-radius: 16px; padding: 28px;
  max-width: 420px; width: 100%; box-shadow: var(--shadow-lg);
  animation: slideUp 0.2s ease;
}
.modal h3 { font-size: 16px; font-weight: 600; color: var(--text); margin-bottom: 16px; }
.modal-input {
  width: 100%; padding: 12px 14px; border: 1px solid var(--border); border-radius: 6px;
  font-size: 14px; outline: none; font-family: inherit; margin-bottom: 12px;
  color: var(--text);
}
.modal-input:focus { border-color: var(--brand); box-shadow: 0 0 0 3px var(--brand-light); }
.modal-colors { display: flex; gap: 8px; margin-bottom: 16px; }
.modal-color {
  width: 28px; height: 28px; border-radius: 50%; border: 2px solid transparent;
  cursor: pointer; transition: all 150ms;
}
.modal-color:hover, .modal-color.selected { border-color: var(--text); transform: scale(1.15); }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; }
.modal-cancel {
  padding: 8px 18px; background: none; border: 1px solid var(--border);
  border-radius: 8px; font-size: 14px; cursor: pointer; font-family: inherit; color: var(--text);
}
.modal-cancel:hover { background: var(--bg-hover); }
.modal-confirm {
  padding: 8px 18px; background: var(--brand); color: #fff; border: none;
  border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; font-family: inherit;
}
.modal-confirm:hover { background: var(--brand-dark); }
.modal-confirm.danger { background: var(--red); }
.modal-confirm.danger:hover { background: #B91C1C; }

/* Share panel */
.share-panel {
  margin-top: 16px; padding: 16px; background: var(--bg-subtle); border-radius: 8px;
}
.share-url-row { display: flex; gap: 8px; margin-top: 8px; }
.share-url-input {
  flex: 1; padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px;
  font-size: 14px; font-family: 'JetBrains Mono', monospace; color: var(--text-secondary); outline: none;
}
.share-copy-btn {
  padding: 8px 14px; background: var(--brand); color: #fff; border: none;
  border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer;
  font-family: inherit; transition: background 150ms;
}
.share-copy-btn:hover { background: var(--brand-dark); }

/* Detail back link */
.dash-back {
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 14px; color: var(--text-tertiary); cursor: pointer; text-decoration: none;
  margin-bottom: 24px; font-weight: 500; transition: color 150ms;
}
.dash-back:hover { color: var(--brand); }

/* Blueprint detail */
.bp-detail-card {
  background: var(--surface); border-radius: 12px;
  padding: 32px; max-width: 680px; box-shadow: var(--shadow-sm);
}
.bp-detail-title {
  font-size: 20px; font-weight: 700; color: var(--text); margin-bottom: 4px;
}
.bp-detail-date { font-size: 14px; color: var(--text-tertiary); margin-bottom: 24px; }
.bp-detail-actions { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 24px; }

/* Loading overlay for dashboard */
.dash-loading {
  display: flex; align-items: center; justify-content: center; padding: 64px;
}
.dash-loading .spinner {
  width: 32px; height: 32px; border: 3px solid var(--border);
  border-top-color: var(--brand); border-radius: 50%; animation: spin 0.6s linear infinite;
}

@media (max-width: 768px) {
  .dash-stats { grid-template-columns: 1fr; }
  .dash-grid { grid-template-columns: 1fr; }
  .dash-header { padding: 12px 16px; }
  .dash-content { padding: 24px 16px; }
  .dash-user-name { display: none; }
  .dash-action-bar { flex-direction: column; align-items: stretch; }
  .dash-search { min-width: unset; }
}

@media (max-width: 640px) {
  .landing-screen h2 { font-size: 28px; }
  .question-text { font-size: 20px; }
  .features { grid-template-columns: 1fr; }
  .header { padding: 24px 16px; }
  .stage-line { width: 40px; }
  .auth-card { padding: 28px 20px; }
}

/* ── Chat Panel ── */
.chat-header { padding: 16px; border-bottom: 1px solid var(--border); }
.chat-header h4 { margin: 0; font-size: 16px; font-weight: 600; }
.chat-hint { font-size: 14px; color: var(--text-tertiary); }
.chat-messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.chat-msg { padding: 12px 16px; border-radius: 12px; max-width: 85%; word-wrap: break-word; font-size: 14px; line-height: 1.6; }
.chat-msg-user { background: var(--brand); color: white; align-self: flex-end; border-bottom-right-radius: 4px; }
.chat-msg-assistant { background: var(--surface); border: 1px solid var(--border); align-self: flex-start; border-bottom-left-radius: 4px; }
.chat-msg-loading { align-self: flex-start; background: var(--surface); border: 1px solid var(--border); padding: 16px; }
.chat-typing { display: flex; gap: 4px; }
.chat-typing span { width: 8px; height: 8px; border-radius: 50%; background: var(--text-tertiary); animation: chatBounce 1.4s infinite; }
.chat-typing span:nth-child(2) { animation-delay: 0.2s; }
.chat-typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes chatBounce { 0%,80%,100% { transform: scale(0); } 40% { transform: scale(1); } }
.chat-input-area { padding: 16px; border-top: 1px solid var(--border); display: flex; gap: 8px; }
.chat-input { flex: 1; border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; font-size: 14px; resize: none; font-family: inherit; }
.chat-input:focus { outline: none; border-color: var(--brand); }
.chat-send-btn { background: var(--brand); color: white; border: none; border-radius: 8px; padding: 8px 16px; cursor: pointer; font-weight: 600; font-size: 14px; }
.chat-send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Editor Screen ── */
#editorScreen { display: none; height: calc(100vh - 60px); }
.editor-layout { display: flex; height: 100%; }
.editor-sidebar {
  width: 220px; border-right: 1px solid var(--border); overflow-y: auto; background: var(--surface);
}
.editor-sidebar .section-item {
  padding: 12px 16px; cursor: pointer; border-bottom: 1px solid var(--border-light);
  font-size: 14px; transition: all 150ms;
}
.editor-sidebar .section-item:hover { background: var(--bg-hover); }
.editor-sidebar .section-item.active {
  border-left: 2px solid var(--brand); background: transparent; color: var(--text); font-weight: 600;
}
.editor-main { flex: 1; overflow-y: auto; padding: 32px; }
.editor-chat { width: 350px; border-left: 1px solid var(--border); display: flex; flex-direction: column; background: var(--bg-subtle); }
.editor-block { margin-bottom: 16px; }

/* Back Button */
.back-btn { background: none; border: 1px solid var(--border); color: var(--text-tertiary); padding: 6px 12px;
            border-radius: 8px; cursor: pointer; font-size: 14px; margin-bottom: 12px; }
.back-btn:hover { background: var(--surface); color: var(--text); }
.back-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* Editable Findings */
.editable-findings { max-width: 600px; }
.findings-hint { font-size: 14px; color: var(--text-tertiary); margin-bottom: 16px; }
.findings-edit { width: 100%; border: 1px solid var(--border); border-radius: 6px; padding: 8px; font-family: inherit;
                 font-size: 14px; resize: vertical; margin-bottom: 12px; }
.findings-edit:focus { outline: none; border-color: var(--brand); }
.editable-tag-list { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
.editable-tag { cursor: text; position: relative; padding-right: 24px; }
.tag-remove { cursor: pointer; position: absolute; right: 4px; top: 50%; transform: translateY(-50%);
              color: rgba(0,0,0,0.4); font-weight: bold; }
.tag-remove:hover { color: var(--red); }
.add-tag-btn { background: none; border: 1px dashed var(--border); color: var(--text-tertiary); padding: 6px 12px;
               border-radius: 6px; cursor: pointer; font-size: 14px; margin-bottom: 16px; }
.add-tag-btn:hover { border-color: var(--brand); color: var(--brand); }

/* Review Card */
.review-card { max-width: 650px; margin: 0 auto; }
.review-hint { font-size: 14px; color: var(--text-tertiary); margin-bottom: 16px; }

/* Block Editor */
.be-block-wrapper { position: relative; margin-bottom: 8px; border: 1px solid transparent; border-radius: 8px; transition: border-color 150ms; }
.be-block-wrapper:hover { border-color: var(--border); }
.be-block-wrapper:hover .be-toolbar { opacity: 1; }
.be-toolbar { position: absolute; top: -36px; right: 0; display: flex; gap: 2px; opacity: 0; transition: opacity 150ms; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 4px; z-index: 10; box-shadow: var(--shadow); }
.be-tb-btn { background: none; border: none; padding: 4px 8px; cursor: pointer; font-size: 14px; border-radius: 6px; color: var(--text-tertiary); }
.be-tb-btn:hover { background: var(--bg-hover); color: var(--brand); }
.be-tb-del:hover { background: var(--red-light); color: var(--red); }
.be-drag-handle { cursor: grab; padding: 4px 8px; font-size: 14px; color: var(--text-tertiary); }
.be-block-content { padding: 8px; }
.be-ghost { opacity: 0.4; }
.be-insert-btn { text-align: center; height: 20px; position: relative; }
.be-insert-plus { width: 24px; height: 24px; border-radius: 50%; border: 1px dashed var(--border); background: var(--surface); color: var(--text-tertiary); cursor: pointer; font-size: 16px; line-height: 1; opacity: 0; transition: opacity 150ms; }
.be-insert-btn:hover .be-insert-plus { opacity: 1; }
.be-insert-plus:hover { border-color: var(--brand); color: var(--brand); background: var(--brand-light); }
.be-palette { position: absolute; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; box-shadow: var(--shadow-lg); padding: 8px; display: flex; flex-wrap: wrap; gap: 4px; z-index: 20; max-width: 300px; }
.be-palette-item { background: none; border: 1px solid var(--border); padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 14px; }
.be-palette-item:hover { background: var(--bg-hover); border-color: var(--brand); }
.be-done-btn { margin-top: 12px; background: var(--brand); color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px; }
.be-input { width: 100%; border: 1px solid var(--border); border-radius: 6px; padding: 8px; font-size: 14px; margin-bottom: 4px; font-family: inherit; }
.be-input:focus { outline: none; border-color: var(--brand); }
.be-input-sm { width: auto; min-width: 100px; }
.be-textarea { width: 100%; border: 1px solid var(--border); border-radius: 6px; padding: 8px; font-size: 14px; font-family: inherit; resize: vertical; }
.be-textarea-sm { width: 100%; border: 1px solid var(--border); border-radius: 6px; padding: 6px 8px; font-size: 14px; font-family: inherit; resize: vertical; }
.be-select { border: 1px solid var(--border); border-radius: 6px; padding: 6px 8px; font-size: 14px; }
.be-select-sm { border: 1px solid var(--border); border-radius: 6px; padding: 4px 6px; font-size: 14px; }
.be-btn-add { background: none; border: 1px dashed var(--border); color: var(--text-tertiary); padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 14px; margin-top: 4px; }
.be-btn-add:hover { border-color: var(--brand); color: var(--brand); }
.be-btn-sm { background: none; border: none; cursor: pointer; padding: 4px 8px; font-size: 14px; color: var(--text-tertiary); }
.be-btn-del:hover { color: var(--red); }
.be-hint { font-size: 14px; color: var(--text-tertiary); margin-top: 4px; }
.be-section-label { font-weight: 600; margin: 8px 0 4px; font-size: 14px; }
.be-no-editor { color: var(--text-tertiary); font-style: italic; padding: 16px; font-size: 14px; }
.be-save-indicator { padding: 4px 12px; font-size: 14px; color: var(--text-tertiary); text-align: right; }
.be-save-saving { color: var(--amber); }
.be-save-saved { color: var(--green); }
.be-save-error { color: var(--red); }

/* Block type specific render styles */
.be-wf-step { display: flex; gap: 8px; padding: 8px; background: var(--surface); border: 1px solid var(--border); border-radius: 6px; margin-bottom: 4px; }
.be-wf-num { width: 24px; height: 24px; border-radius: 50%; background: var(--brand); color: white; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; }
.be-wf-title { font-weight: 600; } .be-wf-desc { font-size: 14px; color: var(--text-tertiary); } .be-wf-assignee { font-size: 14px; color: var(--accent); }
.be-wf-edit-row { display: flex; gap: 8px; align-items: flex-start; margin-bottom: 8px; padding: 8px; background: var(--bg-subtle); border-radius: 6px; }
.be-wf-fields { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.be-cl-row { display: flex; gap: 8px; align-items: center; margin-bottom: 4px; }
.be-cl-input { flex: 1; }
.be-kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }
.be-kpi-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px; }
.be-kpi-name { font-size: 14px; color: var(--text-tertiary); text-transform: uppercase; }
.be-kpi-value { font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 500; color: var(--brand); }
.be-kpi-target { font-size: 14px; color: var(--text-tertiary); }
.be-kpi-row { display: flex; gap: 4px; align-items: center; margin-bottom: 4px; }
.be-table { width: 100%; border-collapse: collapse; }
.be-table th { background: var(--brand); color: white; padding: 8px; text-align: left; font-size: 14px; }
.be-table td { padding: 8px; border-bottom: 1px solid var(--border); font-size: 14px; }
.be-table-row { display: flex; gap: 4px; margin-bottom: 4px; }
.be-timeline .be-tl-item { padding: 8px 0; border-left: 2px solid var(--brand); padding-left: 16px; margin-bottom: 4px; }
.be-tl-phase { font-weight: 600; color: var(--brand); }
.be-tl-dur { font-size: 14px; color: var(--text-tertiary); }
.be-tl-act { font-size: 14px; }
.be-tl-edit-row { display: flex; gap: 4px; margin-bottom: 4px; flex-wrap: wrap; }
.be-card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; }
.be-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 8px; border-left: 3px solid var(--accent); }
.be-card-activity { border-left-color: var(--accent); }
.be-card-title { font-weight: 600; font-size: 14px; }
.be-card-item { font-size: 14px; color: var(--text-tertiary); }
.be-card-edit { margin-bottom: 12px; padding: 8px; background: var(--bg-subtle); border-radius: 6px; }
.be-glossary .be-gl-entry { padding: 6px 0; border-bottom: 1px solid var(--border); }
.be-gl-term { font-weight: 600; color: var(--brand); }
.be-gl-def { color: var(--text); }
.be-gl-row { display: flex; gap: 4px; margin-bottom: 4px; }
.be-org .be-org-role { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px; margin-bottom: 8px; }
.be-org-title { font-weight: 700; color: var(--brand); }
.be-org-reports { font-size: 14px; color: var(--text-tertiary); }
.be-org-resp { font-size: 14px; padding-left: 8px; }
.be-org-edit { margin-bottom: 12px; padding: 8px; background: var(--bg-subtle); border-radius: 6px; }
.be-flow-nodes { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
.be-flow-node { background: var(--surface); border: 2px solid var(--brand); border-radius: 8px; padding: 6px 12px; font-weight: 600; font-size: 14px; }
.be-flow-center { background: var(--brand); color: white; }
.be-flow-edge { font-size: 14px; color: var(--text-tertiary); padding: 2px 0; }
.be-flow-row { display: flex; gap: 4px; margin-bottom: 4px; }
.be-checklist { list-style: none; padding: 0; }
.be-checklist li { padding: 6px 0; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); font-size: 14px; }
.be-cl-check { width: 16px; height: 16px; border: 2px solid var(--border); border-radius: 4px; flex-shrink: 0; }
.be-cl-check.checked { background: var(--green); border-color: var(--green); }
.be-cl-high { border-left: 3px solid var(--red); padding-left: 8px; }
.be-divider { border: none; }
.be-divider-solid { border-top: 2px solid var(--border); margin: 16px 0; }
.be-divider-dashed { border-top: 2px dashed var(--border); margin: 16px 0; }
.be-divider-dotted { border-top: 2px dotted var(--border); margin: 16px 0; }
.be-rendered-heading { margin-bottom: 0; }

/* Style panel */
.be-style-panel { position: fixed; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; box-shadow: var(--shadow-lg); padding: 16px; z-index: 100; min-width: 200px; }
.be-style-title { font-weight: 600; margin-bottom: 8px; font-size: 14px; }
.be-style-label { display: block; font-size: 14px; color: var(--text-tertiary); margin: 8px 0 4px; }
.be-style-colors { display: flex; gap: 8px; }
.be-swatch { width: 24px; height: 24px; border-radius: 50%; border: 2px solid var(--border); cursor: pointer; }
.be-swatch.active { border-color: var(--brand); box-shadow: 0 0 0 2px var(--brand); }
.be-swatch-default { background: var(--surface); }
.be-swatch-blue { background: #3B82F6; }
.be-swatch-green { background: #059669; }
.be-swatch-orange { background: #D97706; }
.be-swatch-red { background: #DC2626; }
.be-swatch-purple { background: #8B5CF6; }
.be-swatch-teal { background: #14B8A6; }

/* Skeletons */
.skeleton { background: linear-gradient(90deg, var(--bg-subtle) 25%, var(--bg-hover) 50%, var(--bg-subtle) 75%);
            background-size: 200% 100%; animation: shimmer 1.5s ease-in-out infinite; border-radius: 8px; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
.skeleton-card { height: 120px; margin-bottom: 16px; }
.skeleton-block { height: 80px; margin-bottom: 16px; }

/* Resume banner */
.resume-banner { background: var(--brand-light); border: 1px solid var(--brand); border-radius: 12px;
                 padding: 12px 16px; margin-bottom: 16px; display: flex; align-items: center; gap: 12px; }
.resume-btn { background: var(--brand); color: white; border: none; padding: 6px 16px;
              border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px; }
.resume-btn-secondary { background: none; border: 1px solid var(--border); color: var(--text-tertiary); }

/* Offline banner */
.offline-banner { padding: 8px 16px; text-align: center; font-size: 14px; font-weight: 600;
                  position: fixed; top: 0; left: 0; right: 0; z-index: 9999; }
.offline-offline { background: #FEF3CD; color: #856404; }
.offline-reconnecting { background: #FEF3CD; color: #856404; }
.offline-synced { background: #D4EDDA; color: #155724; }

/* Tour */
.tour-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); z-index: 9990; }
.tour-highlight { position: relative; z-index: 9991; box-shadow: 0 0 0 4px var(--brand), 0 0 0 8px rgba(37,99,235,0.2); border-radius: 8px; }
.tour-tooltip { position: fixed; background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
                padding: 16px 20px; box-shadow: var(--shadow-lg); z-index: 9992; max-width: 300px; }
.tour-message { font-size: 14px; margin-bottom: 8px; line-height: 1.6; }
.tour-counter { font-size: 14px; color: var(--text-tertiary); margin-bottom: 12px; }
.tour-actions { display: flex; justify-content: space-between; }
.tour-skip { background: none; border: none; color: var(--text-tertiary); cursor: pointer; font-size: 14px; }
.tour-next { background: var(--brand); color: white; border: none; padding: 6px 16px; border-radius: 8px;
             cursor: pointer; font-weight: 600; font-size: 14px; }

/* Undo toast */
.undo-toast { position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%); background: #1F2937; color: white;
              padding: 12px 20px; border-radius: 12px; display: flex; align-items: center; gap: 16px;
              box-shadow: var(--shadow-lg); z-index: 9000; font-size: 14px; }
.undo-toast-btn { background: none; border: 1px solid rgba(255,255,255,0.3); color: white; padding: 4px 12px;
                  border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 14px; }
</style>
```

**Commit after Chunk 1:**
```
git add static/index.html
git commit -m "visual: rewrite app CSS with Inter/JetBrains Mono design system

New design tokens: 8px grid, 12px card radius, updated color palette,
150ms transitions, shadow-based card separation, 14px minimum font size.
All JS class names and IDs preserved — CSS-only changes.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Chunk 2: Blueprint Output CSS (block_renderer.py)

### Task 2: Replace BLOCK_CSS and update renderer functions for consulting-grade output

**Files:**
- Modify: `block_renderer.py`

- [ ] **Step 1: Replace `BLOCK_CSS` constant with consulting-grade navy/gold styles**

Replace the entire `BLOCK_CSS = """..."""` block (lines 9-98 in current file) with:

```python
BLOCK_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=Source+Sans+3:wght@400;500;600&display=swap');

:root {
  --bp-navy: #1B2B4B;
  --bp-navy-light: #2D4A7A;
  --bp-gold: #C8A960;
  --bp-gold-light: #F5EDD6;
  --bp-bg: #FAFAF8;
  --bp-surface: #FFFFFF;
  --bp-text: #2D3748;
  --bp-text-light: #718096;
  --bp-border: #E2E8F0;
  --bp-green: #38A169;
  --bp-red: #E53E3E;
  --bp-blue: #3182CE;
  --bp-radius: 8px;
  --bp-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Source Sans 3', 'Source Sans Pro', -apple-system, sans-serif;
  background: var(--bp-bg); color: var(--bp-text); line-height: 1.7;
  padding: 2.5rem 3rem; max-width: 900px; margin: 0 auto; font-size: 15px;
}
.block { margin-bottom: 2rem; }

/* Headings — Crimson Pro with gold underline */
h1, h2, h3, h4 { font-family: 'Crimson Pro', Georgia, serif; color: var(--bp-navy); margin-bottom: 0.75rem; line-height: 1.3; }
h1 { font-size: 28px; font-weight: 600; padding-bottom: 0.75rem; border-bottom: none; position: relative; }
h1::after { content: ''; display: block; width: 60px; height: 2px; background: var(--bp-gold); margin-top: 0.75rem; }
h2 { font-size: 22px; font-weight: 600; padding-bottom: 0.5rem; border-bottom: none; position: relative; }
h2::after { content: ''; display: block; width: 40px; height: 2px; background: var(--bp-gold); margin-top: 0.5rem; }
h3 { font-size: 18px; font-weight: 600; }
h4 { font-size: 16px; font-weight: 600; }

/* Rich text */
.rich-text p { margin-bottom: 0.75rem; }

/* KPI Grid — large number cards */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1.25rem; }
.kpi-card {
  background: var(--bp-surface); border: 1px solid var(--bp-border); border-radius: var(--bp-radius);
  padding: 1.25rem; box-shadow: var(--bp-shadow); text-align: center;
}
.kpi-card .name { font-size: 0.85rem; color: var(--bp-text-light); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 500; }
.kpi-card .value { font-family: 'Source Sans 3', sans-serif; font-size: 2rem; font-weight: 600; color: var(--bp-navy); margin: 0.5rem 0; }
.kpi-card .target { font-size: 0.85rem; color: var(--bp-text-light); }
.kpi-card .trend-up { color: var(--bp-green); }
.kpi-card .trend-down { color: var(--bp-red); }
.kpi-card .trend-arrow { font-size: 0.9rem; margin-right: 2px; }
.kpi-card .previous { font-size: 0.8rem; color: var(--bp-text-light); margin-left: 4px; }

/* Workflow — vertical timeline with numbered circles */
.workflow-steps { display: flex; flex-direction: column; gap: 0; padding-left: 0; }
.wf-step {
  display: flex; align-items: flex-start; gap: 1.25rem; padding: 1rem 0;
  position: relative;
}
.wf-step:not(:last-child)::after {
  content: ''; position: absolute; left: 17px; top: 44px; bottom: -4px;
  width: 2px; background: var(--bp-gold);
}
.step-num {
  width: 36px; height: 36px; border-radius: 50%; background: var(--bp-navy); color: white;
  display: flex; align-items: center; justify-content: center; font-size: 0.9rem;
  font-weight: 600; flex-shrink: 0; position: relative; z-index: 1;
}
.step-body .title { font-weight: 600; color: var(--bp-navy); font-size: 1rem; }
.step-body .desc { font-size: 0.9rem; color: var(--bp-text); margin-top: 0.25rem; }
.step-body .assignee { font-size: 0.85rem; color: var(--bp-navy-light); margin-top: 0.25rem; font-weight: 500; }

/* Step color variants — applied to step-num background */
.step-type-blue .step-num { background: var(--bp-blue); }
.step-type-green .step-num { background: var(--bp-green); }
.step-type-orange .step-num { background: #DD6B20; }
.step-type-red .step-num { background: var(--bp-red); }
.step-type-purple .step-num { background: #805AD5; }

/* Checklist */
.checklist { list-style: none; }
.checklist li { padding: 0.75rem 0; border-bottom: 1px solid var(--bp-border); display: flex; align-items: center; gap: 0.75rem; }
.checklist .chk { width: 18px; height: 18px; border: 2px solid var(--bp-border); border-radius: 4px; flex-shrink: 0; }
.checklist .chk.checked { background: var(--bp-green); border-color: var(--bp-green); }
.checklist .priority-high { border-left: 3px solid var(--bp-red); padding-left: 0.75rem; }

/* Tables — navy header, alternating rows, gold left border */
table { width: 100%; border-collapse: collapse; background: var(--bp-surface); border-radius: var(--bp-radius);
        overflow: hidden; box-shadow: var(--bp-shadow); border-left: 3px solid var(--bp-gold); }
th { background: var(--bp-navy); color: white; padding: 0.75rem 1rem; text-align: left; font-weight: 600; font-size: 0.9rem; }
td { padding: 0.75rem 1rem; border-bottom: 1px solid var(--bp-border); font-size: 0.9rem; }
tr:nth-child(even) { background: var(--bp-bg); }
tr:nth-child(odd) { background: var(--bp-surface); }

/* Timeline */
.timeline { display: flex; flex-direction: column; position: relative; padding-left: 2.5rem; }
.timeline::before { content: ''; position: absolute; left: 1rem; top: 0; bottom: 0; width: 2px; background: var(--bp-gold); }
.tl-item { position: relative; padding: 1rem 0; }
.tl-item::before { content: ''; position: absolute; left: -1.85rem; top: 1.25rem;
                   width: 14px; height: 14px; border-radius: 50%; background: var(--bp-navy); border: 2px solid var(--bp-surface); }
.tl-item .phase { font-family: 'Crimson Pro', serif; font-weight: 600; color: var(--bp-navy); font-size: 1.05rem; }
.tl-item .duration { font-size: 0.85rem; color: var(--bp-text-light); }
.tl-item .activities { font-size: 0.9rem; margin-top: 0.25rem; }

/* Card Grid */
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }
.card { background: var(--bp-surface); border: 1px solid var(--bp-border); border-radius: var(--bp-radius);
        padding: 1rem; box-shadow: var(--bp-shadow); }
.card.type-activity { border-left: 3px solid var(--bp-blue); }
.card.type-document { border-left: 3px solid var(--bp-green); }
.card.type-approval { border-left: 3px solid var(--bp-gold); }
.card.type-critical { border-left: 3px solid var(--bp-red); }
.card.type-handover { border-left: 3px solid #805AD5; }
.card .card-title { font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem; color: var(--bp-navy); }
.card .card-item { font-size: 0.85rem; color: var(--bp-text-light); }

/* Glossary */
.glossary-list { display: grid; gap: 1rem; }
.gl-entry { background: var(--bp-surface); border: 1px solid var(--bp-border); border-radius: var(--bp-radius); padding: 1.25rem; }
.gl-entry .term { font-family: 'Crimson Pro', serif; font-weight: 700; color: var(--bp-navy); font-size: 1.05rem; }
.gl-entry .definition { margin-top: 0.35rem; }
.gl-entry .related { font-size: 0.85rem; color: var(--bp-text-light); margin-top: 0.35rem; }

/* Org Chart — card-based with navy header bar */
.org-chart { display: flex; flex-direction: column; gap: 1rem; }
.org-role {
  background: var(--bp-surface); border: 1px solid var(--bp-border); border-radius: var(--bp-radius);
  overflow: hidden; box-shadow: var(--bp-shadow);
}
.org-role .role-header { background: var(--bp-navy); color: white; padding: 0.75rem 1rem; }
.org-role .role-title { font-family: 'Crimson Pro', serif; font-weight: 700; color: white; font-size: 1.1rem; }
.org-role .role-body { padding: 1rem; }
.org-role .reports-to { font-size: 0.85rem; color: var(--bp-text-light); margin-bottom: 0.5rem; }
.org-role .responsibilities { margin-top: 0.5rem; padding-left: 1.25rem; }
.org-role .responsibilities li { font-size: 0.9rem; margin-bottom: 0.35rem; }

/* Flow Diagram */
.flow-diagram { display: flex; flex-wrap: wrap; gap: 1rem; align-items: center; justify-content: center; }
.flow-node { background: var(--bp-surface); border: 2px solid var(--bp-navy); border-radius: var(--bp-radius);
             padding: 0.75rem 1.25rem; font-weight: 600; text-align: center; min-width: 100px; }
.flow-node.type-center { background: var(--bp-navy); color: white; }
.flow-edges { width: 100%; }
.flow-edge { display: flex; align-items: center; gap: 0.5rem; padding: 0.35rem 0;
             font-size: 0.9rem; color: var(--bp-text-light); }
.flow-edge .arrow { color: var(--bp-navy); font-weight: bold; }

/* Dividers */
hr.divider { border: none; margin: 2rem 0; }
hr.divider-solid { border-top: 2px solid var(--bp-border); }
hr.divider-dashed { border-top: 2px dashed var(--bp-border); }
hr.divider-dotted { border-top: 2px dotted var(--bp-border); }

/* Key Insight callouts */
.insight-callout {
  border-left: 4px solid var(--bp-gold); background: var(--bp-gold-light);
  padding: 1.25rem 1.5rem; border-radius: 0 var(--bp-radius) var(--bp-radius) 0;
  margin: 1.5rem 0;
}
.insight-callout .insight-label {
  font-weight: 700; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px;
  color: var(--bp-navy); margin-bottom: 0.5rem;
}

/* Cover page */
.cover-page {
  text-align: center; padding: 6rem 3rem; min-height: 80vh;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.cover-line { width: 120px; height: 3px; background: var(--bp-gold); margin: 2rem auto; }
.cover-title { font-family: 'Crimson Pro', serif; font-size: 36px; font-weight: 700; color: var(--bp-navy); line-height: 1.2; }
.cover-subtitle { font-family: 'Crimson Pro', serif; font-size: 22px; font-weight: 400; color: var(--bp-navy-light); margin-top: 0.75rem; }
.cover-meta { font-size: 0.9rem; color: var(--bp-text-light); margin-top: 2.5rem; line-height: 1.8; }
.cover-footer { font-size: 0.85rem; color: var(--bp-text-light); margin-top: 4rem; }

/* Page footer */
.page-footer {
  border-top: 1px solid var(--bp-navy); padding-top: 0.75rem; margin-top: 3rem;
  display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--bp-text-light);
}

/* Print styles */
@media print {
  body { padding: 1.5rem; }
  .cover-page { page-break-after: always; }
  .block { page-break-inside: avoid; }
}
"""
```

- [ ] **Step 2: Update `_render_org_chart` to use navy header bar HTML structure**

Replace the `_render_org_chart` function with:

```python
def _render_org_chart(data, style):
    roles = []
    for role in data.get("roles", []):
        reports = f'<div class="reports-to">Reports to: {_esc(role.get("reports_to",""))}</div>' if role.get("reports_to") else ""
        resp = "".join(f"<li>{_esc(r)}</li>" for r in role.get("responsibilities", []))
        resp_html = f'<ul class="responsibilities">{resp}</ul>' if resp else ""
        roles.append(f'''<div class="org-role">
<div class="role-header"><div class="role-title">{_esc(role.get("title",""))}</div></div>
<div class="role-body">{reports}{resp_html}</div></div>''')
    return f'<div class="block block-org-chart org-chart">{"".join(roles)}</div>'
```

- [ ] **Step 3: Add `_render_cover_page` function and update the renderers dict**

Add this function after `_render_flow_diagram` and before `BLOCK_RENDERERS`:

```python
def _render_cover_page(data, style):
    company = _esc(data.get("company_name", ""))
    title = _esc(data.get("title", "Service Blueprint"))
    subtitle = _esc(data.get("subtitle", "& Operational Manual"))
    date = _esc(data.get("date", ""))
    dept_count = _esc(data.get("department_count", ""))
    meta_parts = []
    if date:
        meta_parts.append(f"Prepared: {date}")
    if dept_count:
        meta_parts.append(f"Departments: {dept_count}")
    meta_html = "<br>".join(meta_parts)
    return f'''<div class="block cover-page">
<div class="cover-line"></div>
<div class="cover-title">{company}</div>
<div class="cover-subtitle">{title}<br>{subtitle}</div>
<div class="cover-line"></div>
<div class="cover-meta">{meta_html}</div>
<div class="cover-footer">Generated by Blueprint Maker</div>
</div>'''
```

Then update the `BLOCK_RENDERERS` dict to include it:

```python
BLOCK_RENDERERS = {
    "heading": _render_heading, "rich-text": _render_rich_text, "kpi-grid": _render_kpi_grid,
    "workflow": _render_workflow, "checklist": _render_checklist, "table": _render_table,
    "timeline": _render_timeline, "card-grid": _render_card_grid, "glossary": _render_glossary,
    "divider": _render_divider, "org-chart": _render_org_chart, "flow-diagram": _render_flow_diagram,
    "cover-page": _render_cover_page,
}
```

- [ ] **Step 4: Update `render_section_to_html` to include Google Fonts link and page footer**

Replace `render_section_to_html` with:

```python
def render_section_to_html(section: dict, company_name: str = "", page_number: int = 0) -> str:
    """Render a full section to a standalone HTML file."""
    title = _esc(section.get("title", "Blueprint Section"))
    blocks_html = "\n".join(render_block(b) for b in section.get("blocks", []))
    footer_html = ""
    if company_name or page_number:
        left = f"{_esc(company_name)}" if company_name else ""
        right_parts = []
        if title:
            right_parts.append(title)
        if page_number:
            right_parts.append(str(page_number))
        right = " | ".join(right_parts)
        footer_html = f'<div class="page-footer"><span>{left}</span><span>{right}</span></div>'
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=Source+Sans+3:wght@400;500;600&display=swap" rel="stylesheet">
<style>{BLOCK_CSS}</style>
</head>
<body>
{blocks_html}
{footer_html}
</body>
</html>'''
```

**Note:** The `company_name` and `page_number` parameters are optional and default to empty/0, so existing callers of `render_section_to_html(section)` continue to work without changes.

**Commit after Chunk 2:**
```
git add block_renderer.py
git commit -m "visual: consulting-grade blueprint output CSS (navy/gold palette)

Crimson Pro + Source Sans 3 typography, navy header tables, gold-accent
timelines, card-based org chart with header bars, cover page support,
page footer component. All existing block types preserved.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Chunk 3: Legacy Renderer CSS Update (renderer.py)

### Task 3: Update CSS_VARS and BASE_CSS in renderer.py to match consulting palette

**Files:**
- Modify: `renderer.py`

- [ ] **Step 1: Replace `CSS_VARS` constant (lines 5-43) with navy/gold palette**

Replace the entire `CSS_VARS = """..."""` block with:

```python
CSS_VARS = """
:root {
  --bg: #FAFAF8;
  --surface: #FFFFFF;
  --text: #2D3748;
  --text-secondary: #718096;
  --text-muted: #A0AEC0;
  --brand: #1B2B4B;
  --brand-light: #EBF0F7;
  --brand-hover: #2D4A7A;
  --blue-card: #DBEAFE;
  --blue-border: #1B2B4B;
  --green: #38A169;
  --green-card: #C6F6D5;
  --green-border: #38A169;
  --green-light: #F0FFF4;
  --amber: #C8A960;
  --amber-card: #F5EDD6;
  --amber-border: #C8A960;
  --amber-light: #FEFCF3;
  --red: #E53E3E;
  --red-card: #FED7D7;
  --red-border: #E53E3E;
  --red-light: #FFF5F5;
  --purple: #805AD5;
  --purple-card: #E9D8FD;
  --purple-border: #805AD5;
  --purple-light: #FAF5FF;
  --teal: #319795;
  --teal-card: #B2F5EA;
  --teal-light: #E6FFFA;
  --border: #E2E8F0;
  --border-light: #EDF2F7;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow: 0 1px 3px rgba(0,0,0,0.08);
  --shadow-lg: 0 4px 12px rgba(0,0,0,0.1);
  --radius: 8px;
  --gold: #C8A960;
  --gold-light: #F5EDD6;
}
"""
```

- [ ] **Step 2: Update the `BASE_CSS` body and heading styles (lines 45-50)**

Replace:
```python
BASE_CSS = CSS_VARS + """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, Helvetica, sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.6; font-size: 14px;
  -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
}
```

With:
```python
BASE_CSS = CSS_VARS + """
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=Source+Sans+3:wght@400;500;600&display=swap');
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Source Sans 3', 'Source Sans Pro', -apple-system, sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.7; font-size: 15px;
  -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
}
```

- [ ] **Step 3: Update `.main-header h1` to use Crimson Pro**

Replace:
```css
.main-header h1 {
  font-size: 18px; font-weight: 700; color: var(--text); letter-spacing: -0.3px;
}
```

With:
```css
.main-header h1 {
  font-family: 'Crimson Pro', Georgia, serif;
  font-size: 20px; font-weight: 700; color: var(--brand); letter-spacing: -0.3px;
}
```

- [ ] **Step 4: Update `.section-title` to use Crimson Pro with gold underline**

Replace:
```css
.section-title {
  font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 4px;
  letter-spacing: -0.2px;
}
```

With:
```css
.section-title {
  font-family: 'Crimson Pro', Georgia, serif;
  font-size: 20px; font-weight: 700; color: var(--brand); margin-bottom: 4px;
  letter-spacing: -0.2px; padding-bottom: 0.5rem; position: relative;
}
.section-title::after {
  content: ''; display: block; width: 40px; height: 2px; background: var(--gold); margin-top: 0.5rem;
}
```

- [ ] **Step 5: Update table header to navy background**

Replace:
```css
.data-table th { background: var(--bg); color: var(--text); padding: 10px 14px; text-align: left; font-size: 12px; font-weight: 600; border-bottom: 2px solid var(--border); }
```

With:
```css
.data-table th { background: var(--brand); color: white; padding: 10px 14px; text-align: left; font-size: 13px; font-weight: 600; border-bottom: none; }
.data-table { border-left: 3px solid var(--gold); }
.data-table tr:nth-child(even) td { background: var(--bg); }
```

- [ ] **Step 6: Update `.workflow-title` to use Crimson Pro**

Replace:
```css
.workflow-title { font-size: 15px; font-weight: 700; color: var(--text); margin-bottom: 14px; }
```

With:
```css
.workflow-title { font-family: 'Crimson Pro', Georgia, serif; font-size: 16px; font-weight: 700; color: var(--brand); margin-bottom: 14px; }
```

- [ ] **Step 7: Update `.nav-tab.active` to use navy brand color**

Replace:
```css
.nav-tab.active { color: var(--brand); border-bottom-color: var(--brand); }
```

With:
```css
.nav-tab.active { color: var(--brand); border-bottom-color: var(--gold); }
```

**Commit after Chunk 3:**
```
git add renderer.py
git commit -m "visual: update legacy renderer CSS to navy/gold consulting palette

Crimson Pro headings, Source Sans 3 body, navy table headers with gold
left border, gold underline on section titles. Matches block_renderer
consulting aesthetic for visual consistency.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Summary

| Chunk | Scope | Files | Key Changes |
|-------|-------|-------|-------------|
| 1 | App CSS rewrite | `static/index.html` | Inter + JetBrains Mono, new palette, 8px grid, 12px radius, 14px min font, shadow-based cards, 150ms transitions, Google Fonts link |
| 2 | Blueprint output CSS | `block_renderer.py` | Crimson Pro + Source Sans 3, navy/gold palette, vertical timeline workflows, navy-header tables, card org charts, cover page, page footer |
| 3 | Legacy renderer CSS | `renderer.py` | Navy/gold palette, Crimson Pro headings, Source Sans 3 body, navy table headers, gold accents |

### What's preserved (no JS breakage)
- All class names used by `classList.add/remove/toggle/contains`: `.hidden`, `.selected`, `.active`, `.done`
- All element IDs used by `getElementById()`
- All `className =` assignments in JS
- All functional CSS (display toggling, layout structure, z-index layering)
- The `querySelector('.start-btn')` reference

### What changes (visual only)
- Colors (new palette with CSS custom properties)
- Typography (Inter/JetBrains Mono for app, Crimson Pro/Source Sans 3 for output)
- Spacing (8px grid system)
- Border radius (12px cards, 8px buttons, 6px inputs)
- Shadows (shadow-based separation instead of borders)
- Transitions (150ms ease-out globally)
- Font sizes (14px minimum throughout)
