# Visual Redesign — Design Spec

**Date:** 2026-03-14
**Status:** Approved

## Goal

Transform the app from "functional developer tool" to "premium SaaS product" with two distinct visual identities:
- **App UI:** Modern SaaS aesthetic (Notion/Figma/Linear style)
- **Blueprint Output:** Corporate consulting deliverable (McKinsey/BCG style)

---

## Part A: App Design System

### Typography

| Use | Font | Weight | Size |
|-----|------|--------|------|
| Page headings | Inter | 600 (semi-bold) | 28-40px |
| Section headings | Inter | 600 | 20-24px |
| Body text | Inter | 400 | 16px (base) |
| Secondary text | Inter | 400 | 14px |
| Stats/numbers | JetBrains Mono | 500 | varies |
| Buttons | Inter | 600 | 14-15px |

Minimum text size: 14px. No text smaller than that anywhere.

Load via Google Fonts:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

### Color Palette

```css
:root {
  /* Backgrounds */
  --bg: #FFFFFF;
  --bg-subtle: #F9FAFB;
  --bg-hover: #F3F4F6;

  /* Text */
  --text: #111827;
  --text-secondary: #6B7280;
  --text-tertiary: #9CA3AF;

  /* Brand */
  --brand: #2563EB;
  --brand-light: #DBEAFE;
  --brand-dark: #1D4ED8;

  /* Accent (CTAs, highlights) */
  --accent: #F59E0B;
  --accent-light: #FEF3C7;

  /* Borders */
  --border: #E5E7EB;
  --border-light: #F3F4F6;

  /* Status */
  --success: #059669;
  --success-bg: #ECFDF5;
  --warning: #D97706;
  --warning-bg: #FFFBEB;
  --error: #DC2626;
  --error-bg: #FEF2F2;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow: 0 1px 3px rgba(0,0,0,0.08);
  --shadow-lg: 0 4px 12px rgba(0,0,0,0.1);
}
```

### Spacing & Layout

- **Grid:** 8px base unit. All spacing is multiples of 8 (8, 16, 24, 32, 48, 64)
- **Card padding:** 24px
- **Section gaps:** 32px
- **Page margins:** 32px on desktop, 16px on mobile
- **Max content width:** 1200px (centered)
- **Border radius:** 12px on cards, 8px on buttons, 6px on inputs

### Components

**Buttons:**
- Primary: `--brand` bg, white text, 8px radius, 14px font, 12px 20px padding
- Secondary: white bg, `--border` border, `--text` color
- Ghost: no bg, no border, `--text-secondary` color
- Press effect: `transform: scale(0.98)` on active
- Transition: 150ms ease-out

**Cards:**
- White bg, 12px radius, `--shadow-sm` shadow
- Hover: `--shadow` shadow (subtle lift)
- No visible border by default (shadow provides separation)
- 24px internal padding

**Inputs:**
- 1px `--border` border, 6px radius
- 12px 14px padding
- Focus: `--brand` border, subtle `--brand-light` ring
- Placeholder: `--text-tertiary`

**Toasts:**
- 12px radius, `--shadow-lg` shadow
- Dark bg (`#1F2937`) for errors/info, `--success-bg` for success
- Slide in from bottom-right

**Modals:**
- Centered, `--shadow-lg`, 16px radius
- Backdrop: `rgba(0,0,0,0.4)` with blur(4px)

### Transitions

- All interactive elements: `transition: all 150ms ease-out`
- Page transitions: fade-in 200ms
- Skeleton shimmer: 1.5s ease-in-out infinite

---

## Part B: Screen-by-Screen Redesign

### Landing Page

```
┌─────────────────────────────────────────────┐
│  Logo                          [Sign In]    │
│                                              │
│                                              │
│     Build your business blueprint            │
│          in minutes, not months              │
│                                              │
│    AI-powered operational blueprints         │
│    for every department in your company      │
│                                              │
│  ┌───────────────────────────────────────┐   │
│  │ Describe your business...             │   │
│  │                                       │   │
│  │                                       │   │
│  └───────────────────────────────────────┘   │
│         [ Start Building →  ]                │
│                                              │
│                                              │
│   ┌──────┐  ┌──────┐  ┌──────┐              │
│   │Sample│  │Sample│  │Sample│              │
│   │  1   │  │  2   │  │  3   │              │
│   └──────┘  └──────┘  └──────┘              │
│   "HVAC"    "Legal"   "Retail"              │
│                                              │
└─────────────────────────────────────────────┘
```

- Centered layout, max-width 680px for content
- Headline: 40px Inter semi-bold
- Subtitle: 18px Inter regular, `--text-secondary`
- Textarea: large (160px height), 16px font, generous padding
- CTA: amber bg, dark text, large (48px height)
- Sample cards below: small blueprint thumbnails with industry labels

### Auth Screen

- Same centered layout as landing
- Clean card with tabs: "Sign In" / "Sign Up"
- Google button: white bg, Google icon, "Continue with Google"
- Divider: "or" with lines
- Email/password fields: clean, stacked
- Minimal — no marketing content on this screen

### Questionnaire Flow

```
┌─────────────────────────────────────────────┐
│  ← Back                    ████████░░ 5/8   │
│                                              │
│                                              │
│        Question 5 of 8                       │
│                                              │
│     What departments does your               │
│     business have?                           │
│                                              │
│  ┌───────────────────────────────────────┐   │
│  │                                       │   │
│  │                                       │   │
│  └───────────────────────────────────────┘   │
│                              [ Continue → ]  │
│                                              │
└─────────────────────────────────────────────┘
```

- Full-screen, vertically centered
- Thin progress bar at very top (not chunky stage dots)
- Question number: small, `--text-secondary`
- Question text: 24px, `--text`
- Back button: ghost button, top-left
- Continue button: primary, bottom-right

### Research Review

- Same centered layout
- Card with editable findings
- Tags: pill-shaped, `--bg-subtle` bg, editable
- "Looks Good — Continue" button: primary, full-width at bottom

### Dashboard

```
┌──────┬──────────────────────────────────────┐
│      │  My Blueprints          [+ New]      │
│ All  │  ─────────────────────────────        │
│      │  ┌──────┐ ┌──────┐ ┌──────┐          │
│Folder│  │ Acme │ │ Beta │ │ Corp │          │
│  1   │  │ HVAC │ │ Legal│ │Retail│          │
│      │  │ 12dep│ │ 8dep │ │ 10dep│          │
│Folder│  │ Mar 5│ │ Mar 3│ │ Feb  │          │
│  2   │  └──────┘ └──────┘ └──────┘          │
│      │                                       │
│      │                                       │
│ ──── │                                       │
│Stats │                                       │
│ 5 bp │                                       │
│2.1MB │                                       │
└──────┴──────────────────────────────────────┘
```

- Sidebar: 240px, collapsible on mobile
- Cards: clean white, hover shadow, no heavy borders
- Card content: title (16px 600), department count + date (14px secondary)
- Three-dot menu: appears on hover only
- Empty state: centered icon + "Create your first blueprint" + CTA

### Editor

```
┌──────┬──────────────────────────┬───────────┐
│      │              Saved ●     │ Edit AI   │
│Master│                          │           │
│      │  ┌────────────────────┐  │ Chat msg  │
│Servce│  │  Service Dept      │  │ Chat msg  │
│      │  │  ══════════════    │  │           │
│Sales │  │                    │  │           │
│      │  │  [KPI] [KPI] [KPI]│  │           │
│Ops   │  │                    │  │           │
│      │  │  Workflow:         │  │           │
│Gloss │  │  1. Step one       │  │ ┌───────┐ │
│      │  │  2. Step two       │  │ │ Type  │ │
│      │  │  3. Step three     │  │ │ here  │ │
│      │  └────────────────────┘  │ └───────┘ │
└──────┴──────────────────────────┴───────────┘
```

- Sidebar: active section = left blue border (2px), not full bg color
- Content: generous spacing between blocks, hover shows floating toolbar pill
- Chat: clean bubbles, brand color for user, white for assistant
- Save indicator: tiny colored dot, not text

---

## Part C: Blueprint Output Design (Consulting Deliverable)

### Fonts

```html
<link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=Source+Sans+3:wght@400;500;600&display=swap" rel="stylesheet">
```

| Use | Font | Weight |
|-----|------|--------|
| Cover title | Crimson Pro | 700 |
| Section headings | Crimson Pro | 600 |
| Body text | Source Sans 3 | 400 |
| Table headers | Source Sans 3 | 600 |
| KPI numbers | Source Sans 3 | 600 |

### Color Palette

```css
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
}
```

### Page Structure

**Cover page:**
```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│     ━━━━━━━━━━━━━━━━━━━━━          │
│                                     │
│     ACME HVAC SOLUTIONS             │
│                                     │
│     Service Blueprint               │
│     & Operational Manual            │
│                                     │
│     ━━━━━━━━━━━━━━━━━━━━━          │
│                                     │
│     Prepared: March 2026            │
│     Departments: 12                 │
│     Pages: 48                       │
│                                     │
│                                     │
│                                     │
│     Generated by Blueprint Maker    │
│                                     │
└─────────────────────────────────────┘
```

- Crimson Pro 700, 36px title
- Gold decorative lines above and below title
- Navy background option or white with navy text

**Section pages:**
- Section title: Crimson Pro 600, 28px, navy
- Gold underline (2px, 60px wide) below section titles
- Body: Source Sans 3, 15px, generous line-height (1.7)

**KPI cards:**
```
┌──────────────┐
│ First-Time   │
│ Fix Rate     │
│              │
│   92%        │ ← large, navy, Source Sans 600
│   ▲ 85%     │ ← trend + previous, green/red
│              │
│ Target: 95%  │ ← small, text-light
└──────────────┘
```

**Workflow steps:**
```
  ①─── Receive Call
  │    Log customer details in CRM.
  │    Assignee: CSR
  │
  ②─── Create Work Order
  │    Enter job in field service system.
  │    Assignee: CSR
  │
  ③─── Dispatch Technician
       Route to nearest available tech.
       Assignee: Dispatcher
```

Vertical timeline with numbered circles (navy bg, white text), connecting lines (gold), step content indented.

**Tables:**
- Header row: navy bg, white text
- Alternating rows: white / `--bp-bg`
- No heavy borders — just subtle bottom borders
- Gold left border on the first column

**Org chart:**
- Card-based with connecting lines
- Navy header bar on each role card
- Responsibilities as bullet points below

**Key Insight callouts:**
```
┌─ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ─┐
│  💡 KEY INSIGHT                     │
│                                     │
│  First-time fix rate directly       │
│  correlates with customer           │
│  retention. Each 1% improvement     │
│  reduces callbacks by 3%.          │
└─ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ─┘
```
Gold left border, `--bp-gold-light` background.

**Page footer:**
```
Acme HVAC — Service Blueprint          Service Department │ 12
```
Company name left, section + page number right. Thin navy line above.

---

## Part D: Implementation Approach

### What changes

| Component | Current | Change |
|-----------|---------|--------|
| `static/index.html` | All CSS inline in `<style>` | Full CSS rewrite — same file, replace entire `<style>` block |
| `block_renderer.py` | BLOCK_CSS constant | Replace with consulting-grade CSS + HTML structure |
| `renderer.py` | BASE_CSS + render functions | Update CSS to match new blueprint palette (legacy support) |
| Google Fonts | None | Add Inter + JetBrains Mono (app) + Crimson Pro + Source Sans 3 (output) |

### What doesn't change

- All JavaScript (functionality stays the same)
- Backend logic, API endpoints, data model
- Block type editors (they inherit from the CSS, no JS changes)
- File structure

### Implementation order

1. **App CSS rewrite** — Replace the entire `<style>` section in index.html with the new design system. This is a single large edit but affects no JS.
2. **Blueprint output CSS** — Rewrite `BLOCK_CSS` in `block_renderer.py` with the consulting-grade styles. Update HTML structure in each renderer function for the new layout.
3. **Legacy renderer** — Update `BASE_CSS` in `renderer.py` to match (for legacy blueprints).

---

## Non-Goals

- No framework migration (stays vanilla JS/CSS)
- No separate CSS files (stays inline in index.html for simplicity)
- No responsive mobile redesign (desktop-first, basic mobile via media queries)
- No dark mode (future consideration)
- No custom illustrations or icons (use Unicode/emoji)
