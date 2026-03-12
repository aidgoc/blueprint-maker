# HEFT ERP — Service Blueprint Reference Data Model

> Extracted from the 14-file Service Blueprint suite at `/home/harshwardhan/Downloads/Service Blueprint/`.
> This document is the authoritative reference for building the blueprint generator.

---

## 1. Master Blueprint Grid Structure (`service-blueprint.html`)

The master blueprint is a **13-role x 12-stage matrix** rendered as a scrollable CSS grid. Each cell contains zero or more **typed cards** (activity, document, approval, critical, handover). The grid supports **6 Business Unit views** that overlay BU-specific cards on top of the common base data.

### Grid Layout
- CSS Grid: `170px` role-label column + `repeat(12, minmax(260px, 1fr))` stage columns
- Minimum grid width: `3600px` (horizontally scrollable)
- Corner cell: "Role / Stage →"

---

## 2. The 12 Stages

| # | Stage ID | Stage Name | Icon |
|---|----------|-----------|------|
| 1 | 1 | Enquiry & Lead Capture | 📥 |
| 2 | 2 | Site Assessment & Technical Survey | 📐 |
| 3 | 3 | Estimation & Quotation | 💰 |
| 4 | 4 | Negotiation & Contract | 🤝 |
| 5 | 5 | Equipment Planning & Allocation | 🏗️ |
| 6 | 6 | Mobilization & Transport | 🚛 |
| 7 | 7 | Site Setup & Commissioning | ⚙️ |
| 8 | 8 | Operations & Execution | 🔧 |
| 9 | 9 | Billing & Invoicing | 🧾 |
| 10 | 10 | Demobilization | 📦 |
| 11 | 11 | Final Settlement & Closure | ✅ |
| 12 | 12 | Feedback & Review | ⭐ |

### Stage Header Visual
- Background: `var(--navy)` (#1B3A5C), white text
- Contains: circled stage number (22px circle, semi-transparent white bg), icon, name
- Font: 12px, bold

---

## 3. The 13 Roles

| # | Role ID | Role Name | Icon |
|---|---------|-----------|------|
| 1 | client | Client / Customer | 🏢 |
| 2 | sales | Sales & Business Development | 📞 |
| 3 | estimation | Estimation / Commercial | 📊 |
| 4 | technical | Technical & Engineering | 🔩 |
| 5 | operations | Operations | 🎯 |
| 6 | hse | HSE (Health, Safety, Environment) | 🧺 |
| 7 | hr | HR & Manpower | 👥 |
| 8 | logistics | Logistics & Transport | 🚚 |
| 9 | maintenance | Maintenance / Workshop | 🔧 |
| 10 | procurement | Material Procurement / Stores | 📦 |
| 11 | finance | Finance & Accounts | 💳 |
| 12 | management | Senior Management / Directors | 👔 |
| 13 | site | Site Team (Supervisors, Operators, Riggers) | 👷 |

### Role Label Visual
- Background: `var(--navy-dark)` (#0F2740), white text
- Sticky left (`position: sticky; left: 0; z-index: 10`)
- Width: `min-width: 170px; max-width: 170px`
- Contains: icon (16px) + name (11px, bold)
- Clickable: opens corresponding department sub-blueprint

---

## 4. Cell Data Model — The 5 Card Types

Each cell in the grid is keyed as `"{roleId}-{stageId}"` (e.g., `"sales-1"`, `"technical-2"`).

The COMMON object stores arrays of card objects per key. Cards are constructed using shorthand functions:

```javascript
function A(text, detail) { return { type: "activity",  text, detail }; }
function D(text, detail) { return { type: "document",  text, detail }; }
function P(text, detail) { return { type: "approval",  text, detail }; }
function C(text, detail) { return { type: "critical",  text, detail }; }
function H(text, detail) { return { type: "handover",  text, detail }; }
```

### Card Fields
| Field | Type | Description |
|-------|------|-------------|
| `type` | string | One of: `"activity"`, `"document"`, `"approval"`, `"critical"`, `"handover"` |
| `text` | string | Primary card title/description (11px, bold). May include emoji prefix for documents (📄). |
| `detail` | string | Expanded detail text (10.5px, gray). Hidden by default, shown on cell click. |

### Card Visual Styles

| Type | CSS Class | Background | Left Border | Icon |
|------|-----------|-----------|-------------|------|
| Activity | `.card.activity` | `#E8F0FE` (--blue-card) | `#4A90D9` (--blue-border) | 🔹 |
| Document | `.card.document` | `#E6F7ED` (--green-card) | `#34A853` (--green-border) | 📄 |
| Approval | `.card.approval` | `#FFF3E0` (--orange-card) | `#F09300` (--orange-border) | ✅ |
| Critical | `.card.critical` | `#FDECEA` (--red-bg) | `#D93025` (--red-badge) | ⚠️ |
| Handover | `.card.handover` | `#F3E8FD` (--purple-card) | `#8E24AA` (--purple-border) | 🔄 |

### Card HTML Structure
```html
<div class="card activity">
  <span class="card-icon">🔹</span>
  <span class="card-title">Card text here</span>
  <div class="card-detail">Detail text here</div>
</div>
```
- Cards have `border-left: 3px solid` with type-specific color
- `border-radius: 5px`, `padding: 5px 7px`, `margin-bottom: 4px`
- Detail is hidden by default; shown when parent `.bp-cell` gets class `.expanded`

### Empty Cells
- Cells with no cards get class `.empty-cell`
- Background: `var(--gray-light)` (#F5F7FA)
- Not clickable

---

## 5. Business Unit (BU) Overlay System

The master blueprint supports **6 views** via tab switching:

| BU Key | Tab Label | Extra Data Object | BU Tag |
|--------|-----------|-------------------|--------|
| `common` | Common Flow (All Business Units) | _(none — base COMMON only)_ | — |
| `crane` | Crane Rental (Long/Short Term) | `BU_CRANE` | `"CRANE"` |
| `windmill` | Windmill Erection | `BU_WINDMILL` | `"WIND"` |
| `port` | Port Handling | `BU_PORT` | `"PORT"` |
| `heavy` | Heavy Lifting | `BU_HEAVY` | `"HEAVY"` |
| `logistics` | Logistics (ODC Transport) | `BU_LOGISTICS` | `"ODC"` |

### How BU Data Merges with COMMON

```javascript
function getCards(bu, roleId, stageId) {
  var key = roleId + "-" + stageId;
  var base = COMMON[key] || [];           // Always included
  var extras = BU_MAP[bu].extras;         // Array of BU overlay objects
  extras.forEach(function(ex) {
    if (ex[key]) base = base.concat(ex[key]);  // BU-specific cards appended
  });
  return base;
}
```

- BU-specific cards are tagged with a `_buTag` (e.g., "CRANE", "WIND") and display a small purple badge
- Badge visual: `font-size: 8px`, `background: var(--purple-card)`, `color: var(--purple-border)`, `border-radius: 3px`

### BU Data Objects — Key Coverage

Each BU object uses the same `"{roleId}-{stageId}"` key format and the same `A()`, `D()`, `P()`, `C()`, `H()` constructors. They only define keys where that BU has additional/different activities. Example keys per BU:

**BU_CRANE:** `client-1`, `technical-2`, `estimation-3`, `operations-5`, `operations-8`, `finance-9`, `site-8`, `procurement-5`, `procurement-8`

**BU_WINDMILL:** `client-1`, `technical-2`, `operations-5`, `hse-7`, `operations-8`, `technical-8`, `procurement-5`, `procurement-8`

**BU_PORT:** `client-1`, `technical-2`, `operations-5`, `hse-7`, `operations-8`, `logistics-6`, `procurement-5`, `procurement-8`

**BU_HEAVY:** `client-1`, `technical-2`, `operations-5`, `technical-5`, `hse-7`, `operations-8`, `procurement-5`, `procurement-8`

**BU_LOGISTICS:** `client-1`, `technical-2`, `operations-5`, `logistics-6`, `hse-6`, `operations-8`, `client-7`, `procurement-5`, `procurement-8`

---

## 6. COMMON Data — Cell Population Summary (156 entries total)

Below shows which role-stage combinations have data vs. are empty in the COMMON (base) layer:

### Stage 1 (Enquiry & Lead Capture)
- **Has data:** client, sales, estimation, technical, operations, finance, management
- **Empty:** hse, hr, logistics, maintenance, procurement, site

### Stage 2 (Site Assessment & Technical Survey)
- **Has data:** client, sales, estimation, technical, operations, hse, management
- **Empty:** hr, logistics, maintenance, procurement, finance, site

### Stages 3–12
All 13 roles have a COMMON entry for every stage (156 total = 13 roles x 12 stages). Many role-stage combos are empty arrays `[]` for early stages (hse, hr, logistics, maintenance, procurement, site typically activate from stage 5 onward).

**Key patterns:**
- **Client** has data in all 12 stages
- **Sales** has data in stages 1–4, 8–9, 11–12
- **Estimation** has data in stages 1–3, 9, 11–12
- **Technical** has data in stages 1–2, 5, 7–8, 10, 12
- **Operations** has data in all stages except possibly stage 4
- **HSE** activates from stage 5 (site setup safety) through stage 12
- **HR** activates from stage 5 (crew deployment) through stage 12
- **Logistics** activates from stage 6 (mobilization) through stage 12
- **Maintenance** activates from stage 5 through stage 12
- **Procurement** activates from stage 5 through stage 12
- **Finance** has data in stages 1, 3–4, 9, 11–12
- **Management** has data in stages 1, 3–5, 8–9, 11–12
- **Site** activates from stage 7 (site setup) through stage 12

---

## 7. Department Sub-Blueprint Structure

Each of the 13 departments has a standalone HTML file with a **tabbed section layout**. All share the same CSS variable system and visual language as the master blueprint.

### 7a. Department Blueprint Files

| File | Department | # Tabs |
|------|-----------|--------|
| `client-blueprint.html` | Client / Customer Journey | 9 |
| `sales-blueprint.html` | Sales & Business Development | 8 |
| `estimation-blueprint.html` | Estimation / Commercial | 9 |
| `technical-blueprint.html` | Technical & Engineering | 7 |
| `operations-blueprint.html` | Operations | 8 |
| `hse-blueprint.html` | HSE (Health, Safety, Environment) | 9 |
| `hr-blueprint.html` | HR & Manpower | 9 |
| `logistics-blueprint.html` | Logistics & Transport | 9 |
| `maintenance-blueprint.html` | Maintenance / Workshop | 9 |
| `procurement-blueprint.html` | Material Procurement / Stores | 9 |
| `finance-blueprint.html` | Finance & Accounts | 6 |
| `management-blueprint.html` | Senior Management / Directors | 5 |
| `site-team-blueprint.html` | Site Team (Supervisors, Operators, Riggers) | 9 |

### 7b. Sales Blueprint — Tab Structure (8 tabs)

```javascript
var TABS = [
  { id: "dashboard",  label: "Dashboard" },
  { id: "timeline",   label: "Daily Timeline" },
  { id: "funnel",     label: "Sales Funnel" },
  { id: "workflows",  label: "Key Workflows" },
  { id: "documents",  label: "Documents" },
  { id: "clients",    label: "Client Management" },
  { id: "bu",         label: "BU Variations" },
  { id: "kpis",       label: "KPIs & Targets" }
];
```

**Section content types (from builder functions):**

1. **Dashboard** (`buildDashboard`) — Metric cards in a grid (`card-grid` with `metric-card` items). Each card has: h4 label, large `.value` number, `.detail` text. Color variants: blue (default), green, orange, red, purple, teal.

2. **Daily Timeline** (`buildTimeline`) — Vertical timeline with time-blocks. Each block has a circular time marker (e.g., "8A", "9A"), collapsible header with time range, and body containing activity items. Activity items have: colored icon (36px square, rounded), h4 title, description paragraph, tags (doc, approval, critical, system, handover).

3. **Sales Funnel** (`buildFunnel`) — Funnel visualization with decreasing-width bars. Each stage: colored bar (100% to ~30% width), label text, stats beside it.

4. **Key Workflows** (`buildWorkflows`) — Collapsible workflow sections with `.wf-header` and `.wf-body`. Inside: flow-steps displayed as a horizontal flex row with arrow separators (→). Step types: default (blue), approval (orange), critical (red), document (green), handover (purple).

5. **Documents** (`buildDocuments`) — Grid of document cards (`doc-grid` with `doc-card` items). Each card: h4 name, description, `.doc-flow` (who creates → who reviews), `.doc-freq` badge (daily/weekly/per-project).

6. **Client Management** (`buildClients`) — Table layout (`client-table`) with columns for client data. Also includes interaction maps and scorecard grids.

7. **BU Variations** (`buildBU`) — Sub-tabs (`bu-tabs` with `bu-tab` buttons). Each BU panel (`bu-panel`) contains detail cards in a grid (`bu-detail-grid` with `bu-detail-card` items). Each card: h4 heading, bulleted list items.

8. **KPIs & Targets** (`buildKPIs`) — KPI table (`kpi-table`) with columns: Metric, Target, Formula, Frequency, Owner. Also includes scorecard-grid with score-cards.

### 7c. Operations Blueprint — Tab Structure (8 tabs, hardcoded HTML)

Unlike Sales (which uses JS builders), Operations uses **inline HTML sections**:

| Tab Label | Section ID | Content Type |
|-----------|-----------|-------------|
| Dashboard Overview | `sec-overview` | Metric cards (card-grid) |
| Daily Timeline | `sec-timeline` | Time-blocks with activity items |
| Key Workflows | `sec-workflows` | Workflow step visualizations |
| Documents | `sec-documents` | Document card grid |
| Dept. Interactions | `sec-interactions` | Interaction map (dept-card grid) |
| Escalation Matrix | `sec-escalation` | Escalation levels (esc-matrix) |
| Business Unit Ops | `sec-bu` | BU sub-tabs with detail cards |
| KPIs & Metrics | `sec-kpis` | KPI table + scorecard grid |

**Operations-specific section types not in Sales:**

- **Dept. Interactions** (`interaction-map`): Grid of `dept-card` items. Each card has a department name and flow items with direction badges (`flow-dir.in`, `flow-dir.out`, `flow-dir.both`).

- **Escalation Matrix** (`esc-matrix`): Horizontal flex of `esc-level` items (L1→L2→L3→L4). Each level: colored badge, title, description, time limit, examples. Arrow connectors between levels.

---

## 8. Visual Design System — CSS Variables

```css
:root {
  /* Primary palette */
  --navy: #1B3A5C;
  --navy-light: #2A5580;
  --navy-dark: #0F2740;

  /* Card type colors */
  --blue-card: #E8F0FE;       --blue-border: #4A90D9;
  --green-card: #E6F7ED;      --green-border: #34A853;
  --orange-card: #FFF3E0;     --orange-border: #F09300;
  --red-bg: #FDECEA;          --red-badge: #D93025;
  --purple-card: #F3E8FD;     --purple-border: #8E24AA;

  /* Additional colors (dept blueprints) */
  --teal: #00897B;            --teal-bg: #E0F2F1;
  --amber: #FF8F00;           --amber-bg: #FFF8E1;

  /* Neutrals */
  --gray-light: #F5F7FA;
  --gray-mid: #DDE3EA;
  --gray-text: #5F6B7A;
  --white: #FFFFFF;
  --text-dark: #1A1A2E;

  /* Shadows */
  --shadow: 0 2px 8px rgba(0,0,0,0.08);
  --shadow-lg: 0 4px 16px rgba(0,0,0,0.12);
}
```

### Typography
- Font family: `'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif`
- Base font size: `13px`
- Line height: `1.5` (master), `1.55` (dept blueprints)
- Card title: `11px, font-weight: 600`
- Card detail: `10.5px, color: var(--gray-text)`
- Section title: `18px, font-weight: 700, color: var(--navy)`
- Stage header: `12px, font-weight: 700, white`
- Role label: `11px, font-weight: 600, white`

### Layout Patterns

1. **Master Grid**: Sticky header + sticky tabs + legend bar + controls bar + horizontally scrollable grid
2. **Dept Blueprint**: Sticky header + breadcrumb + sticky nav tabs + legend bar + sections (one visible at a time)
3. **Card Grids**: `display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px`
4. **Document Grids**: `repeat(auto-fill, minmax(250-280px, 1fr)); gap: 14px`
5. **Interaction Maps**: `repeat(auto-fill, minmax(300px, 1fr)); gap: 14px`
6. **Workflow Steps**: `display: flex; align-items: flex-start; gap: 0` (horizontal flow with arrow separators)
7. **Timeline**: Vertical with left border line (3px gradient), circular time markers, collapsible blocks

### Common UI Components

| Component | Class | Description |
|-----------|-------|-------------|
| Metric Card | `.metric-card` | White card, 8px radius, shadow, 4px left border. Color variants: default/green/orange/red/purple/teal |
| Document Card | `.doc-card` | White card, 8px radius, shadow, 4px left green border. Hover: translateY(-2px) |
| Workflow Step | `.wf-step-box` | 120px wide, 8px radius, 2px border, centered text. Color variants: blue/green/orange/red/purple/teal |
| Collapsible Section | `.collapsible-header` + `.collapsible-body` | Navy header with chevron, white body, toggle hidden class |
| Tag/Badge | `.tag` | 9px, 2px 6px padding, 3px radius. Types: `.doc`, `.approval`, `.critical`, `.system`, `.handover` |
| BU Tab | `.bu-tab` | Sub-navigation within BU Variations section. Orange bottom border when active. |
| KPI Table | `.kpi-table` | Full-width table, navy header, alternating row colors, shadow |
| Score Card | `.score-card` | Centered card with large value (28px bold), label, detail |
| Escalation Level | `.esc-level` | Flex item with colored badge, arrow connector to next level |

---

## 9. Master Blueprint — Additional UI Features

### Tab Bar (BU Switching)
- Class: `.tabs-container` / `.tab-btn`
- Background: `var(--navy-light)`
- Active indicator: `border-bottom: 3px solid #FFB74D`
- Sticky at `top: 72px`

### Legend Bar
- Horizontal flex with 5 legend items (one per card type)
- Each: 14px color swatch + label text
- Background: white, bottom border

### Controls Bar
- Expand All / Collapse All buttons
- Class: `.ctrl-btn`

### Cell Interaction
- Click cell → toggle `.expanded` class → shows/hides `.card-detail` on all cards in that cell
- Empty cells have no click interaction

### Department Hub (Tab: "Department Hub")
- Grid of clickable department cards linking to sub-blueprint files
- Summary metrics bar: 14 files, 1.3MB total, 13 departments, 12 stages, 5 BUs, 110+ tabs
- Cards show: icon, name, filename, description, size badge, tabs badge, patched badge

---

## 10. Summary for Blueprint Generator

To generate a new blueprint for a different company/industry:

1. **Define STAGES** array (id, name, icon) — the horizontal process flow
2. **Define ROLES** array (id, name, icon) — the vertical organizational roles
3. **Populate COMMON** object — base cell data for every `role-stage` combination using the 5 card constructors (A, D, P, C, H)
4. **Optionally define BU variants** — overlay objects with BU-specific additions per cell
5. **Generate department sub-blueprints** — each with 5-9 tabs following the standard section types:
   - Dashboard (metric cards)
   - Daily Timeline (time-blocks with activities)
   - Key Workflows (horizontal step flows)
   - Documents (document card grid)
   - Department Interactions (interaction map)
   - Escalation Matrix (level cards with arrows)
   - BU Variations (sub-tabbed detail cards)
   - KPIs & Metrics (table + scorecard)
6. **Apply the CSS variable system** for consistent theming
7. **All files are standalone HTML** — no build step, no external dependencies
