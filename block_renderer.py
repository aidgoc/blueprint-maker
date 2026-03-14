# block_renderer.py
"""Render blocks to HTML fragments and full sections to standalone HTML pages."""

import html as html_lib

CURRENT_RENDERER_VERSION = 1

# CSS matching existing blueprint design from renderer.py
BLOCK_CSS = """
:root {
  --bg: #F8FAFC; --surface: #FFFFFF; --text: #1E293B; --text-light: #64748B;
  --brand: #2563EB; --brand-dark: #1E40AF; --accent: #3B82F6;
  --green: #10B981; --green-bg: #ECFDF5; --amber: #F59E0B; --amber-bg: #FFFBEB;
  --red: #EF4444; --red-bg: #FEF2F2; --purple: #8B5CF6; --purple-bg: #F5F3FF;
  --teal: #14B8A6; --teal-bg: #F0FDFA; --blue-bg: #EFF6FF;
  --border: #E2E8F0; --radius: 8px; --shadow: 0 1px 3px rgba(0,0,0,0.1);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: var(--bg); color: var(--text); line-height: 1.6; padding: 2rem; }
.block { margin-bottom: 1.5rem; }
h1,h2,h3,h4 { color: var(--brand-dark); margin-bottom: 0.75rem; }
h1 { font-size: 1.75rem; border-bottom: 3px solid var(--brand); padding-bottom: 0.5rem; }
h2 { font-size: 1.35rem; border-bottom: 2px solid var(--border); padding-bottom: 0.4rem; }
h3 { font-size: 1.15rem; } h4 { font-size: 1rem; }
.rich-text p { margin-bottom: 0.5rem; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }
.kpi-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
            padding: 1rem; box-shadow: var(--shadow); }
.kpi-card .name { font-size: 0.85rem; color: var(--text-light); text-transform: uppercase; }
.kpi-card .value { font-size: 1.5rem; font-weight: 700; color: var(--brand); }
.kpi-card .target { font-size: 0.8rem; color: var(--text-light); }
.kpi-card .trend-up { color: var(--green); } .kpi-card .trend-down { color: var(--red); }
.workflow-steps { display: flex; flex-direction: column; gap: 0.75rem; }
.wf-step { display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.75rem;
           background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); }
.step-num { width: 28px; height: 28px; border-radius: 50%; background: var(--brand); color: white;
            display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 600; flex-shrink: 0; }
.step-type-blue .step-num { background: var(--accent); }
.step-type-green .step-num { background: var(--green); }
.step-type-orange .step-num { background: var(--amber); }
.step-type-red .step-num { background: var(--red); }
.step-type-purple .step-num { background: var(--purple); }
.step-body .title { font-weight: 600; } .step-body .desc { font-size: 0.9rem; color: var(--text-light); }
.step-body .assignee { font-size: 0.8rem; color: var(--accent); margin-top: 0.25rem; }
.checklist { list-style: none; }
.checklist li { padding: 0.5rem 0; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 0.5rem; }
.checklist .chk { width: 16px; height: 16px; border: 2px solid var(--border); border-radius: 3px; flex-shrink: 0; }
.checklist .chk.checked { background: var(--green); border-color: var(--green); }
.checklist .priority-high { border-left: 3px solid var(--red); padding-left: 0.5rem; }
table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: var(--radius);
        overflow: hidden; box-shadow: var(--shadow); }
th { background: var(--brand); color: white; padding: 0.75rem; text-align: left; font-weight: 600; }
td { padding: 0.75rem; border-bottom: 1px solid var(--border); }
tr:hover { background: var(--blue-bg); }
.timeline { display: flex; flex-direction: column; position: relative; padding-left: 2rem; }
.timeline::before { content: ''; position: absolute; left: 0.75rem; top: 0; bottom: 0; width: 2px; background: var(--brand); }
.tl-item { position: relative; padding: 0.75rem 0; }
.tl-item::before { content: ''; position: absolute; left: -1.65rem; top: 1rem;
                   width: 12px; height: 12px; border-radius: 50%; background: var(--brand); border: 2px solid white; }
.tl-item .phase { font-weight: 600; color: var(--brand); }
.tl-item .duration { font-size: 0.85rem; color: var(--text-light); }
.tl-item .activities { font-size: 0.9rem; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 0.75rem; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
        padding: 0.75rem; box-shadow: var(--shadow); }
.card.type-activity { border-left: 3px solid var(--accent); }
.card.type-document { border-left: 3px solid var(--green); }
.card.type-approval { border-left: 3px solid var(--amber); }
.card.type-critical { border-left: 3px solid var(--red); }
.card.type-handover { border-left: 3px solid var(--purple); }
.card .card-title { font-weight: 600; font-size: 0.9rem; margin-bottom: 0.4rem; }
.card .card-item { font-size: 0.85rem; color: var(--text-light); }
.glossary-list { display: grid; gap: 0.75rem; }
.gl-entry { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem; }
.gl-entry .term { font-weight: 700; color: var(--brand); }
.gl-entry .definition { margin-top: 0.25rem; }
.gl-entry .related { font-size: 0.8rem; color: var(--text-light); margin-top: 0.25rem; }
.org-chart { display: flex; flex-direction: column; gap: 0.75rem; }
.org-role { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
            padding: 1rem; box-shadow: var(--shadow); }
.org-role .role-title { font-weight: 700; color: var(--brand); font-size: 1.1rem; }
.org-role .reports-to { font-size: 0.85rem; color: var(--text-light); }
.org-role .responsibilities { margin-top: 0.5rem; padding-left: 1.25rem; }
.org-role .responsibilities li { font-size: 0.9rem; margin-bottom: 0.25rem; }
.flow-diagram { display: flex; flex-wrap: wrap; gap: 1rem; align-items: center; justify-content: center; }
.flow-node { background: var(--surface); border: 2px solid var(--brand); border-radius: var(--radius);
             padding: 0.75rem 1.25rem; font-weight: 600; text-align: center; min-width: 100px; }
.flow-node.type-center { background: var(--brand); color: white; }
.flow-edges { width: 100%; }
.flow-edge { display: flex; align-items: center; gap: 0.5rem; padding: 0.35rem 0;
             font-size: 0.9rem; color: var(--text-light); }
.flow-edge .arrow { color: var(--brand); font-weight: bold; }
hr.divider { border: none; margin: 1.5rem 0; }
hr.divider-solid { border-top: 2px solid var(--border); }
hr.divider-dashed { border-top: 2px dashed var(--border); }
hr.divider-dotted { border-top: 2px dotted var(--border); }
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
        roles.append(f'<div class="org-role"><div class="role-title">{_esc(role.get("title",""))}</div>{reports}{resp_html}</div>')
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


BLOCK_RENDERERS = {
    "heading": _render_heading, "rich-text": _render_rich_text, "kpi-grid": _render_kpi_grid,
    "workflow": _render_workflow, "checklist": _render_checklist, "table": _render_table,
    "timeline": _render_timeline, "card-grid": _render_card_grid, "glossary": _render_glossary,
    "divider": _render_divider, "org-chart": _render_org_chart, "flow-diagram": _render_flow_diagram,
}


def render_block(block: dict) -> str:
    """Render a single block to an HTML fragment."""
    renderer = BLOCK_RENDERERS.get(block.get("type", ""))
    if not renderer:
        return f'<div class="block block-unknown">Unknown block type: {_esc(block.get("type",""))}</div>'
    return renderer(block.get("data", {}), block.get("style", {}))


def render_section_to_html(section: dict) -> str:
    """Render a full section to a standalone HTML file."""
    title = _esc(section.get("title", "Blueprint Section"))
    blocks_html = "\n".join(render_block(b) for b in section.get("blocks", []))
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{BLOCK_CSS}</style>
</head>
<body>
{blocks_html}
</body>
</html>'''
