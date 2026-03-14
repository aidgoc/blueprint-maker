# block_renderer.py
"""Render blocks to HTML fragments and full sections to standalone HTML pages."""

import html as html_lib

CURRENT_RENDERER_VERSION = 1

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


def _esc(text):
    return html_lib.escape(str(text)) if text else ""


def _render_heading(data, style):
    level = min(max(data.get("level", 1), 1), 4)
    return f'<div class="block block-heading"><h{level}>{_esc(data.get("text", ""))}</h{level}></div>'

def _render_rich_text(data, style):
    return f'<div class="block block-rich-text rich-text">{data.get("html", "")}</div>'

def _render_kpi_grid(data, style):
    cards = []
    for kpi in data:
        trend = kpi.get("trend", "")
        trend_cls = "trend-up" if trend == "up" else ("trend-down" if trend == "down" else "")
        unit = _esc(kpi.get("unit", ""))
        cards.append(f'''<div class="kpi-card">
<div class="name">{_esc(kpi.get("name",""))}</div>
<div class="value {trend_cls}">{unit}{_esc(kpi.get("value",""))}</div>
<div class="target">Target: {unit}{_esc(kpi.get("target",""))}</div></div>''')
    return f'<div class="block block-kpi-grid kpi-grid">{"".join(cards)}</div>'

def _render_workflow(data, style):
    steps = []
    for i, step in enumerate(data.get("steps", []), 1):
        stype = _esc(step.get("type", "activity"))
        steps.append(f'''<div class="wf-step step-type-{stype}">
<div class="step-num">{i}</div>
<div class="step-body"><div class="title">{_esc(step.get("title",""))}</div>
<div class="desc">{_esc(step.get("description",""))}</div>
<div class="assignee">{_esc(step.get("assignee",""))}</div></div></div>''')
    return f'<div class="block block-workflow workflow-steps">{"".join(steps)}</div>'

def _render_checklist(data, style):
    items = []
    for item in data:
        chk = "checked" if item.get("checked") else ""
        pri = item.get("priority", "normal")
        pri_cls = f"priority-{pri}" if pri != "normal" else ""
        items.append(f'<li class="{pri_cls}"><span class="chk {chk}"></span><span>{_esc(item.get("text",""))}</span></li>')
    return f'<div class="block block-checklist"><ul class="checklist">{"".join(items)}</ul></div>'

def _render_table(data, style):
    headers = "".join(f"<th>{_esc(c)}</th>" for c in data.get("columns", []))
    rows = "".join("<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in row) + "</tr>" for row in data.get("rows", []))
    return f'<div class="block block-table"><table><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table></div>'

def _render_timeline(data, style):
    items = []
    for item in data:
        acts = ", ".join(_esc(a) for a in item.get("activities", []))
        items.append(f'''<div class="tl-item"><div class="phase">{_esc(item.get("phase",""))}</div>
<div class="duration">{_esc(item.get("duration",""))}</div>
<div class="activities">{acts}</div></div>''')
    return f'<div class="block block-timeline timeline">{"".join(items)}</div>'

def _render_card_grid(data, style):
    cards = []
    for card in data:
        ctype = _esc(card.get("type", "activity"))
        items_html = "".join(f'<div class="card-item">{_esc(i)}</div>' for i in card.get("items", []))
        cards.append(f'<div class="card type-{ctype}"><div class="card-title">{_esc(card.get("title",""))}</div>{items_html}</div>')
    return f'<div class="block block-card-grid card-grid">{"".join(cards)}</div>'

def _render_glossary(data, style):
    entries = []
    for e in data:
        related = ", ".join(_esc(r) for r in e.get("related", []))
        rel_html = f'<div class="related">Related: {related}</div>' if related else ""
        entries.append(f'''<div class="gl-entry"><div class="term">{_esc(e.get("term",""))}</div>
<div class="definition">{_esc(e.get("definition",""))}</div>{rel_html}</div>''')
    return f'<div class="block block-glossary glossary-list">{"".join(entries)}</div>'

def _render_divider(data, style):
    s = _esc(data.get("style", "solid"))
    return f'<hr class="block divider divider-{s}">'

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

def _render_flow_diagram(data, style):
    nodes_html = []
    for n in data.get("nodes", []):
        t = f"type-{n.get('type','external')}"
        nodes_html.append(f'<div class="flow-node {t}">{_esc(n.get("label",""))}</div>')
    node_map = {n["id"]: n.get("label", n["id"]) for n in data.get("nodes", [])}
    edges_html = []
    for e in data.get("edges", []):
        src = _esc(node_map.get(e.get("from",""), e.get("from","")))
        dst = _esc(node_map.get(e.get("to",""), e.get("to","")))
        edges_html.append(f'<div class="flow-edge">{src} <span class="arrow">&rarr;</span> {dst}: {_esc(e.get("label",""))}</div>')
    return f'<div class="block block-flow-diagram flow-diagram">{"".join(nodes_html)}<div class="flow-edges">{"".join(edges_html)}</div></div>'


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


BLOCK_RENDERERS = {
    "heading": _render_heading, "rich-text": _render_rich_text, "kpi-grid": _render_kpi_grid,
    "workflow": _render_workflow, "checklist": _render_checklist, "table": _render_table,
    "timeline": _render_timeline, "card-grid": _render_card_grid, "glossary": _render_glossary,
    "divider": _render_divider, "org-chart": _render_org_chart, "flow-diagram": _render_flow_diagram,
    "cover-page": _render_cover_page,
}


def render_block(block: dict) -> str:
    """Render a single block to an HTML fragment."""
    renderer = BLOCK_RENDERERS.get(block.get("type", ""))
    if not renderer:
        return f'<div class="block block-unknown">Unknown block type: {_esc(block.get("type",""))}</div>'
    return renderer(block.get("data", {}), block.get("style", {}))


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
