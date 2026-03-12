"""HTML Template Renderer — generates beautiful blueprint HTML files."""
import json


CSS_VARS = """
:root {
  --navy: #1B3A5C;
  --navy-light: #2A5580;
  --navy-dark: #0F2740;
  --blue-card: #E8F0FE;
  --blue-border: #4A90D9;
  --green-card: #E6F7ED;
  --green-border: #34A853;
  --orange-card: #FFF3E0;
  --orange-border: #F09300;
  --red-badge: #D93025;
  --red-bg: #FDECEA;
  --purple-card: #F3E8FD;
  --purple-border: #8E24AA;
  --gray-light: #F5F7FA;
  --gray-mid: #DDE3EA;
  --gray-text: #5F6B7A;
  --white: #FFFFFF;
  --text-dark: #1A1A2E;
  --shadow: 0 2px 8px rgba(0,0,0,0.08);
  --shadow-lg: 0 4px 16px rgba(0,0,0,0.12);
  --teal: #00897B;
  --teal-bg: #E0F2F1;
}
"""

BASE_CSS = CSS_VARS + """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
  background: var(--gray-light); color: var(--text-dark); line-height: 1.55; font-size: 13px;
}
.main-header {
  background: linear-gradient(135deg, var(--navy-dark), var(--navy));
  color: #fff; padding: 20px 32px; position: sticky; top: 0; z-index: 200;
  box-shadow: var(--shadow-lg);
}
.main-header h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }
.main-header .subtitle { font-size: 12px; opacity: 0.8; margin-top: 4px; }
.nav-tabs {
  background: var(--navy-light); padding: 0 32px; display: flex; gap: 0;
  position: sticky; top: 68px; z-index: 199; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow-x: auto;
}
.nav-tab {
  padding: 12px 20px; border: none; background: transparent; color: rgba(255,255,255,0.7);
  font-size: 12px; font-weight: 600; cursor: pointer; border-bottom: 3px solid transparent;
  white-space: nowrap; transition: all 0.2s;
}
.nav-tab:hover { color: #fff; background: rgba(255,255,255,0.08); }
.nav-tab.active { color: #fff; border-bottom-color: #FFB74D; background: rgba(255,255,255,0.1); }
.legend-bar {
  display: flex; flex-wrap: wrap; gap: 16px; padding: 10px 32px;
  background: #fff; border-bottom: 1px solid var(--gray-mid); align-items: center;
}
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--gray-text); }
.legend-swatch { width: 13px; height: 13px; border-radius: 3px; border: 1px solid rgba(0,0,0,0.15); }
.legend-swatch.activity { background: var(--blue-card); border-color: var(--blue-border); }
.legend-swatch.document { background: var(--green-card); border-color: var(--green-border); }
.legend-swatch.approval { background: var(--orange-card); border-color: var(--orange-border); }
.legend-swatch.critical { background: var(--red-bg); border-color: var(--red-badge); }
.legend-swatch.handover { background: var(--purple-card); border-color: var(--purple-border); }
.section { display: none; padding: 20px 32px; max-width: 1440px; margin: 0 auto; }
.section.active { display: block; }
.section-title {
  font-size: 18px; font-weight: 700; color: var(--navy); margin-bottom: 6px;
  padding-bottom: 8px; border-bottom: 2px solid var(--navy);
}
.section-desc { font-size: 13px; color: var(--gray-text); margin-bottom: 20px; line-height: 1.6; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin-bottom: 24px; }
.metric-card {
  background: #fff; border-radius: 8px; padding: 16px; box-shadow: var(--shadow);
  border-left: 4px solid var(--blue-border);
}
.metric-card.green { border-left-color: var(--green-border); }
.metric-card.orange { border-left-color: var(--orange-border); }
.metric-card.red { border-left-color: var(--red-badge); }
.metric-card.purple { border-left-color: var(--purple-border); }
.metric-card.teal { border-left-color: var(--teal); }
.metric-card h4 { font-size: 11px; text-transform: uppercase; color: var(--gray-text); letter-spacing: 0.5px; margin-bottom: 6px; }
.metric-card .value { font-size: 26px; font-weight: 700; color: var(--navy); }
.metric-card .detail { font-size: 11px; color: var(--gray-text); margin-top: 4px; }

/* Timeline */
.timeline { position: relative; margin: 20px 0; }
.timeline::before {
  content: ''; position: absolute; left: 24px; top: 0; bottom: 0; width: 3px;
  background: linear-gradient(to bottom, var(--navy), var(--blue-border), var(--teal), var(--orange-border)); border-radius: 2px;
}
.time-block { margin-bottom: 24px; position: relative; padding-left: 60px; }
.time-marker {
  position: absolute; left: 10px; top: 0; width: 32px; height: 32px; border-radius: 50%;
  background: var(--navy); color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700; z-index: 2; box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}
.time-block-header {
  background: var(--navy); color: #fff; padding: 10px 16px; border-radius: 8px 8px 0 0;
  display: flex; justify-content: space-between; align-items: center; cursor: pointer;
}
.time-block-header h3 { font-size: 14px; font-weight: 600; }
.time-block-header .time-range { font-size: 12px; opacity: 0.8; }
.time-block-body {
  background: #fff; border: 1px solid var(--gray-mid); border-top: none;
  border-radius: 0 0 8px 8px; padding: 16px; box-shadow: var(--shadow);
}
.time-block-body.collapsed { display: none; }
.activity-item { display: flex; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--gray-light); align-items: flex-start; }
.activity-item:last-child { border-bottom: none; }
.act-icon {
  width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center;
  justify-content: center; font-size: 16px; flex-shrink: 0;
}
.act-icon.blue { background: var(--blue-card); }
.act-icon.green { background: var(--green-card); }
.act-icon.orange { background: var(--orange-card); }
.act-icon.red { background: var(--red-bg); }
.act-icon.purple { background: var(--purple-card); }
.act-icon.teal { background: var(--teal-bg); }
.act-content h4 { font-size: 13px; font-weight: 600; }
.act-content p { font-size: 12px; color: var(--gray-text); margin-top: 2px; line-height: 1.5; }
.tag { font-size: 9px; padding: 2px 6px; border-radius: 3px; font-weight: 600; display: inline-block; margin-top: 4px; margin-right: 4px; }
.tag.doc { background: var(--green-card); color: var(--green-border); }
.tag.approval { background: var(--orange-card); color: var(--orange-border); }
.tag.critical { background: var(--red-bg); color: var(--red-badge); }
.tag.system { background: var(--blue-card); color: var(--blue-border); }
.tag.handover { background: var(--purple-card); color: var(--purple-border); }

/* Workflows */
.workflow-container { background: #fff; border-radius: 8px; padding: 20px; box-shadow: var(--shadow); margin-bottom: 20px; overflow-x: auto; }
.workflow-title { font-size: 15px; font-weight: 700; color: var(--navy); margin-bottom: 14px; }
.workflow-steps { display: flex; align-items: flex-start; gap: 0; min-width: max-content; padding: 10px 0; }
.wf-step { display: flex; flex-direction: column; align-items: center; min-width: 140px; max-width: 160px; text-align: center; }
.wf-step-box {
  width: 120px; padding: 10px 8px; border-radius: 8px; font-size: 11px; font-weight: 600;
  line-height: 1.4; border: 2px solid; min-height: 56px; display: flex; align-items: center; justify-content: center;
}
.wf-step-box.blue { background: var(--blue-card); border-color: var(--blue-border); color: var(--navy); }
.wf-step-box.green { background: var(--green-card); border-color: var(--green-border); color: #1B5E20; }
.wf-step-box.orange { background: var(--orange-card); border-color: var(--orange-border); color: #E65100; }
.wf-step-box.red { background: var(--red-bg); border-color: var(--red-badge); color: var(--red-badge); }
.wf-step-box.purple { background: var(--purple-card); border-color: var(--purple-border); color: var(--purple-border); }
.wf-step-box.teal { background: var(--teal-bg); border-color: var(--teal); color: #004D40; }
.wf-step .wf-role { font-size: 9px; color: var(--gray-text); margin-top: 4px; }
.wf-step .wf-time { font-size: 9px; color: var(--orange-border); margin-top: 2px; font-weight: 600; }
.wf-arrow { display: flex; align-items: center; justify-content: center; min-width: 36px; padding-top: 14px; color: var(--navy); font-size: 18px; font-weight: 700; }

/* Document cards */
.doc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; margin-bottom: 20px; }
.doc-card {
  background: #fff; border-radius: 8px; padding: 14px; box-shadow: var(--shadow);
  border-left: 4px solid var(--green-border);
}
.doc-card h4 { font-size: 13px; font-weight: 600; color: var(--navy); margin-bottom: 4px; }
.doc-card .doc-desc { font-size: 11px; color: var(--gray-text); line-height: 1.5; }
.doc-card .doc-flow { font-size: 10px; color: var(--blue-border); margin-top: 6px; font-weight: 500; }
.doc-card .doc-freq { font-size: 9px; background: var(--blue-card); color: var(--blue-border); padding: 2px 6px; border-radius: 3px; display: inline-block; margin-top: 4px; font-weight: 600; }

/* KPI cards */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 14px; margin-bottom: 20px; }
.kpi-card {
  background: #fff; border-radius: 8px; padding: 16px; box-shadow: var(--shadow); text-align: center;
  border-top: 4px solid var(--blue-border);
}
.kpi-card.green { border-top-color: var(--green-border); }
.kpi-card.orange { border-top-color: var(--orange-border); }
.kpi-card.red { border-top-color: var(--red-badge); }
.kpi-card.purple { border-top-color: var(--purple-border); }
.kpi-card .kpi-name { font-size: 11px; text-transform: uppercase; color: var(--gray-text); letter-spacing: 0.5px; }
.kpi-card .kpi-value { font-size: 28px; font-weight: 700; color: var(--navy); margin: 8px 0; }
.kpi-card .kpi-target { font-size: 11px; color: var(--green-border); font-weight: 600; }
.kpi-card .kpi-desc { font-size: 11px; color: var(--gray-text); margin-top: 6px; }

/* Interaction map */
.interaction-map { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; margin-bottom: 20px; }
.dept-card {
  background: #fff; border-radius: 8px; padding: 16px; box-shadow: var(--shadow);
  border-top: 3px solid var(--blue-border);
}
.dept-card h4 { font-size: 14px; font-weight: 700; color: var(--navy); margin-bottom: 8px; }
.flow-item { font-size: 12px; padding: 4px 0; border-bottom: 1px dashed var(--gray-mid); display: flex; gap: 6px; align-items: flex-start; }
.flow-item:last-child { border-bottom: none; }
.flow-dir { font-size: 10px; font-weight: 700; padding: 1px 5px; border-radius: 3px; flex-shrink: 0; margin-top: 1px; }
.flow-dir.in { background: var(--green-card); color: var(--green-border); }
.flow-dir.out { background: var(--blue-card); color: var(--blue-border); }

/* Escalation */
.esc-matrix { display: flex; gap: 0; margin-bottom: 20px; flex-wrap: wrap; }
.esc-level { flex: 1; min-width: 220px; background: #fff; border: 1px solid var(--gray-mid); padding: 16px; }
.esc-level:first-child { border-radius: 8px 0 0 8px; }
.esc-level:last-child { border-radius: 0 8px 8px 0; }
.esc-level .level-badge { display: inline-block; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; color: #fff; margin-bottom: 8px; }
.esc-level h4 { font-size: 13px; font-weight: 700; color: var(--navy); margin-bottom: 4px; }
.esc-level .esc-desc { font-size: 11px; color: var(--gray-text); line-height: 1.5; }
.esc-level .esc-time { font-size: 10px; font-weight: 600; color: var(--orange-border); margin-top: 6px; }

/* Compliance */
.compliance-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; margin-bottom: 20px; }
.compliance-card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: var(--shadow); border-top: 4px solid var(--navy); }
.compliance-card h4 { font-size: 14px; font-weight: 700; color: var(--navy); margin-bottom: 4px; }
.compliance-card p { font-size: 12px; color: var(--gray-text); line-height: 1.5; }
.compliance-card .freq { font-size: 10px; color: var(--orange-border); font-weight: 600; margin-top: 6px; }

/* Data table */
.data-table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 12px; }
.data-table th { background: var(--navy); color: #fff; padding: 10px 12px; text-align: left; font-size: 11px; }
.data-table td { padding: 10px 12px; border-bottom: 1px solid var(--gray-mid); }
.data-table tr:hover td { background: var(--blue-card); }

/* Blueprint grid (master) */
.blueprint-wrapper { overflow-x: auto; padding: 16px; }
.blueprint-grid { display: grid; gap: 1px; background: var(--gray-mid); border: 1px solid var(--gray-mid); border-radius: 8px; overflow: hidden; }
.stage-header {
  background: var(--navy); color: white; padding: 12px 8px; text-align: center;
  font-weight: 700; font-size: 12px; display: flex; flex-direction: column; align-items: center; gap: 4px;
}
.stage-header .stage-num {
  background: rgba(255,255,255,0.2); border-radius: 50%; width: 22px; height: 22px;
  display: flex; align-items: center; justify-content: center; font-size: 11px;
}
.role-label {
  background: var(--navy-dark); color: white; padding: 10px 10px; font-weight: 600; font-size: 11px;
  display: flex; align-items: center; gap: 6px; position: sticky; left: 0; z-index: 10; min-width: 170px; max-width: 170px;
}
.corner-cell {
  background: var(--navy-dark); color: white; padding: 10px; font-weight: 700; font-size: 12px;
  display: flex; align-items: center; justify-content: center; position: sticky; left: 0; z-index: 11;
  min-width: 170px; max-width: 170px;
}
.bp-cell {
  background: white; padding: 6px; min-height: 80px; position: relative; cursor: pointer; transition: background 0.15s;
}
.bp-cell:hover { background: #F8FAFC; }
.card {
  padding: 4px 6px; border-radius: 4px; font-size: 10px; line-height: 1.35; margin-bottom: 3px;
  border-left: 3px solid; cursor: pointer;
}
.card.activity { background: var(--blue-card); border-color: var(--blue-border); }
.card.document { background: var(--green-card); border-color: var(--green-border); }
.card.approval { background: var(--orange-card); border-color: var(--orange-border); }
.card.critical { background: var(--red-bg); border-color: var(--red-badge); }
.card.handover { background: var(--purple-card); border-color: var(--purple-border); }
.card-detail { display: none; font-size: 9px; color: var(--gray-text); margin-top: 2px; line-height: 1.4; }
.bp-cell.expanded .card-detail { display: block; }
.ctrl-btn {
  padding: 6px 14px; border: 1px solid var(--gray-mid); border-radius: 6px; background: white;
  font-size: 12px; cursor: pointer; font-weight: 500; transition: all 0.2s;
}
.ctrl-btn:hover { background: var(--gray-light); border-color: var(--blue-border); }
.controls-bar { display: flex; gap: 12px; padding: 10px 32px; background: #fff; border-bottom: 1px solid var(--gray-mid); }

/* Print */
@media print {
  .main-header, .nav-tabs { position: static; }
  .section { display: block !important; page-break-inside: avoid; }
  .time-block-body.collapsed { display: block !important; }
  body { font-size: 11px; }
}
@media (max-width: 768px) {
  .main-header, .section { padding-left: 12px; padding-right: 12px; }
  .nav-tabs { padding: 0 8px; }
  .nav-tab { padding: 9px 12px; font-size: 10.5px; }
  .card-grid, .doc-grid, .kpi-grid, .interaction-map, .compliance-grid { grid-template-columns: 1fr; }
  .workflow-steps { flex-direction: column; align-items: center; }
  .wf-arrow { transform: rotate(90deg); }
}
"""


def _esc(text) -> str:
    """HTML-escape text. Handles lists, dicts, and non-string types."""
    if text is None:
        return ""
    if isinstance(text, list):
        text = ", ".join(str(item) for item in text)
    elif isinstance(text, dict):
        text = json.dumps(text)
    elif not isinstance(text, str):
        text = str(text)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ─── Master Blueprint Renderer ────────────────────────────────────────


def render_master_blueprint(data: dict) -> str:
    """Render the master service blueprint (stages × roles grid)."""
    stages = data.get("stages", [])
    roles = data.get("roles", [])
    matrix = data.get("matrix", {})
    company = _esc(data.get("company_name", "Company"))
    industry = _esc(data.get("industry_tag", ""))
    num_stages = len(stages)
    num_roles = len(roles)

    # Build grid HTML
    grid_cols = num_stages + 1  # +1 for role label column
    min_width = grid_cols * 220

    # Header row
    header_cells = f'<div class="corner-cell">Roles \\ Stages</div>'
    for s in stages:
        sid = s.get("id", "")
        sname = _esc(s.get("name", ""))
        sicon = s.get("icon", "")
        header_cells += f'''<div class="stage-header">
            <div class="stage-num">{sid}</div>
            <div>{sicon}</div>
            <div>{sname}</div>
        </div>'''

    # Data rows
    data_rows = ""
    for r in roles:
        rid = r.get("id", "")
        rname = _esc(r.get("name", ""))
        ricon = r.get("icon", "")
        has_file = rid != "client"
        link_start = f'<a href="{rid}-blueprint.html" target="_blank" style="color:inherit;text-decoration:none;">' if has_file else ""
        link_end = "</a>" if has_file else ""
        data_rows += f'<div class="role-label">{link_start}{ricon} {rname}{link_end}</div>'

        for s in stages:
            sid = s.get("id", "")
            key = f"{rid}-{sid}"
            items = matrix.get(key, [])
            cards = ""
            for item in items:
                itype = item.get("type", "activity")
                itext = _esc(item.get("text", ""))
                idetail = _esc(item.get("detail", ""))
                cards += f'<div class="card {itype}"><span>{itext}</span><div class="card-detail">{idetail}</div></div>'
            data_rows += f'<div class="bp-cell" onclick="this.classList.toggle(\'expanded\')">{cards}</div>'

    grid_html = f'''<div class="blueprint-wrapper">
        <div class="blueprint-grid" style="grid-template-columns: 170px repeat({num_stages}, minmax(180px, 1fr)); min-width: {min_width}px;">
            {header_cells}
            {data_rows}
        </div>
    </div>'''

    # Hub section
    hub_cards = ""
    for r in roles:
        rid = r.get("id", "")
        rname = _esc(r.get("name", ""))
        ricon = r.get("icon", "")
        hub_cards += f'''<a href="{rid}-blueprint.html" target="_blank" class="hub-card">
            <div style="font-size:28px;margin-bottom:6px;">{ricon}</div>
            <div style="font-size:14px;font-weight:700;color:var(--navy);margin-bottom:4px;">{rname}</div>
            <div style="font-size:10px;color:var(--gray-text);font-family:monospace;margin-bottom:6px;">{rid}-blueprint.html</div>
            <div style="font-size:11px;color:var(--gray-text);">Detailed department blueprint with daily timeline, workflows, documents, KPIs</div>
        </a>'''

    hub_html = f'''<div id="hubSection" class="section" style="display:none;">
        <div class="section-title">Department Blueprints</div>
        <div class="section-desc">Each department has a detailed sub-blueprint. Click to open.</div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;">
            {hub_cards}
        </div>
    </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company} — Master Service Blueprint</title>
<style>{BASE_CSS}
.hub-card {{
  background: #fff; border-radius: 10px; padding: 18px; box-shadow: var(--shadow);
  border-left: 5px solid var(--blue-border); cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s; text-decoration: none; color: inherit; display: block;
}}
.hub-card:hover {{ transform: translateY(-3px); box-shadow: var(--shadow-lg); }}
</style>
</head>
<body>

<header class="main-header">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
    <div>
      <h1>{company} — Master Service Blueprint</h1>
      <div class="subtitle">{industry} | {num_roles} Roles | {num_stages} Stages | Complete Process Map</div>
    </div>
    <div style="display:flex;gap:8px;">
      <button class="ctrl-btn" onclick="toggleView()" style="background:rgba(255,255,255,0.15);color:#fff;border-color:rgba(255,255,255,0.3);font-weight:700;" id="viewToggle">Department Hub</button>
    </div>
  </div>
</header>

<div class="legend-bar">
  <strong style="font-size:12px;margin-right:8px;">Legend:</strong>
  <div class="legend-item"><div class="legend-swatch activity"></div> Activity</div>
  <div class="legend-item"><div class="legend-swatch document"></div> Document</div>
  <div class="legend-item"><div class="legend-swatch approval"></div> Approval Gate</div>
  <div class="legend-item"><div class="legend-swatch critical"></div> Critical Gate</div>
  <div class="legend-item"><div class="legend-swatch handover"></div> Handover Point</div>
  <div class="legend-item" style="margin-left:auto;opacity:0.6;">Click any cell to expand details</div>
</div>

<div class="controls-bar">
  <button class="ctrl-btn" onclick="expandAll()">Expand All Cells</button>
  <button class="ctrl-btn" onclick="collapseAll()">Collapse All Cells</button>
  <button class="ctrl-btn" onclick="window.print()">Print / Save PDF</button>
</div>

<div id="gridView">{grid_html}</div>
{hub_html}

<script>
function expandAll() {{ document.querySelectorAll('.bp-cell').forEach(c => c.classList.add('expanded')); }}
function collapseAll() {{ document.querySelectorAll('.bp-cell').forEach(c => c.classList.remove('expanded')); }}
var showHub = false;
function toggleView() {{
  showHub = !showHub;
  document.getElementById('gridView').style.display = showHub ? 'none' : 'block';
  document.getElementById('hubSection').style.display = showHub ? 'block' : 'none';
  document.getElementById('viewToggle').textContent = showHub ? 'Blueprint Grid' : 'Department Hub';
}}
</script>
</body>
</html>'''


# ─── Department Blueprint Renderer ────────────────────────────────────


def render_department_blueprint(data: dict, company_name: str) -> str:
    """Render a detailed department sub-blueprint."""
    dept = _esc(data.get("department", "Department"))
    dept_id = data.get("department_id", "dept")
    mission = _esc(data.get("mission", ""))
    company = _esc(company_name)

    tabs = []
    sections = []

    # ── Tab 1: Overview ──
    tabs.append("Overview")
    team_html = ""
    for t in data.get("team_structure", []):
        role = _esc(t.get("role", ""))
        count = _esc(str(t.get("count", "")))
        reports = _esc(t.get("reports_to", ""))
        responsibilities = _esc(t.get("key_responsibilities", ""))
        resp_html = ""
        if responsibilities:
            resp_html = f'<div style="font-size:11px;color:var(--gray-text);margin-top:6px;padding-top:6px;border-top:1px solid var(--gray-mid);line-height:1.5;">{responsibilities}</div>'
        team_html += f'''<div class="metric-card">
            <h4>{role}</h4>
            <div class="value">{count}</div>
            <div class="detail">Reports to: {reports}</div>
            {resp_html}
        </div>'''

    head_role = _esc(data.get("head_role", ""))
    head_html = f'<div style="font-size:13px;color:var(--navy);margin-bottom:16px;font-weight:600;">Department Head: {head_role}</div>' if head_role else ""

    sections.append(f'''<div class="section active" id="sec-0">
        <div class="section-title">{dept} — Overview</div>
        <div class="section-desc">{mission}</div>
        {head_html}
        <h3 style="font-size:15px;font-weight:600;color:var(--navy);margin-bottom:12px;">Team Structure</h3>
        <div class="card-grid">{team_html}</div>
    </div>''')

    # ── Tab 2: Daily Timeline ──
    tabs.append("Daily Timeline")
    timeline_html = '<div class="timeline">'
    colors = ["blue", "green", "teal", "orange", "purple", "red"]
    for i, block in enumerate(data.get("daily_timeline", [])):
        time = _esc(block.get("time", ""))
        title = _esc(block.get("block_title", ""))
        color = colors[i % len(colors)]
        acts_html = ""
        for act in block.get("activities", []):
            aicon = act.get("icon", "")
            atitle = _esc(act.get("title", ""))
            adesc = _esc(act.get("description", ""))
            tags_html = ""
            for tag in act.get("tags", []):
                tag_str = tag if isinstance(tag, str) else str(tag)
                tag_class = tag_str.lower().split()[0] if tag_str else "system"
                if tag_class not in ("doc", "system", "critical", "approval", "handover"):
                    tag_class = "system"
                tags_html += f'<span class="tag {tag_class}">{_esc(tag_str).upper()}</span>'
            acts_html += f'''<div class="activity-item">
                <div class="act-icon {color}">{aicon}</div>
                <div class="act-content">
                    <h4>{atitle}</h4>
                    <p>{adesc}</p>
                    <div>{tags_html}</div>
                </div>
            </div>'''

        timeline_html += f'''<div class="time-block">
            <div class="time-marker">{time.split(":")[0] if ":" in time else time[:3]}</div>
            <div class="time-block-header" onclick="this.nextElementSibling.classList.toggle('collapsed')">
                <h3>{title}</h3>
                <span class="time-range">{time}</span>
            </div>
            <div class="time-block-body">{acts_html}</div>
        </div>'''
    timeline_html += '</div>'

    sections.append(f'''<div class="section" id="sec-1">
        <div class="section-title">Daily Activity Timeline</div>
        <div class="section-desc">Typical workday schedule for the {dept} team.</div>
        {timeline_html}
    </div>''')

    # ── Tab 3: Workflows ──
    tabs.append("Workflows")
    wf_html = ""
    for wf in data.get("workflows", []):
        wf_title = _esc(wf.get("title", ""))
        wf_target = _esc(wf.get("target_time", ""))
        target_badge = f'<span style="font-size:11px;background:var(--orange-card);color:var(--orange-border);padding:3px 10px;border-radius:4px;font-weight:600;">Target: {wf_target}</span>' if wf_target else ""

        # Visual flow (horizontal steps)
        flow_html = ""
        for j, step in enumerate(wf.get("steps", [])):
            stitle = _esc(step.get("title", ""))
            srole = _esc(step.get("role", ""))
            scolor = step.get("color", "blue")
            stime = _esc(step.get("time", ""))
            if j > 0:
                flow_html += '<div class="wf-arrow">&rarr;</div>'
            flow_html += f'''<div class="wf-step">
                <div class="wf-step-box {scolor}">{stitle}</div>
                <div class="wf-role">{srole}</div>
                <div class="wf-time">{stime}</div>
            </div>'''

        # Detailed breakdown table below the flow
        detail_rows = ""
        for j, step in enumerate(wf.get("steps", [])):
            stitle = _esc(step.get("title", ""))
            sdesc = _esc(step.get("description", ""))
            srole = _esc(step.get("role", ""))
            stime = _esc(step.get("time", ""))
            sdocs = _esc(step.get("documents", ""))
            scriteria = _esc(step.get("decision_criteria", ""))
            scolor = step.get("color", "blue")
            extras = ""
            if sdocs:
                extras += f'<div style="margin-top:4px;"><span class="tag doc">DOC</span> {sdocs}</div>'
            if scriteria:
                extras += f'<div style="margin-top:4px;"><span class="tag approval">DECISION</span> {scriteria}</div>'
            detail_rows += f'''<tr>
                <td style="font-weight:600;white-space:nowrap;vertical-align:top;">{j+1}. {stitle}</td>
                <td style="line-height:1.5;">{sdesc}{extras}</td>
                <td style="white-space:nowrap;vertical-align:top;">{srole}</td>
                <td style="white-space:nowrap;vertical-align:top;color:var(--orange-border);font-weight:600;">{stime}</td>
            </tr>'''

        wf_html += f'''<div class="workflow-container">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:8px;">
                <div class="workflow-title" style="margin-bottom:0;">{wf_title}</div>
                {target_badge}
            </div>
            <div class="workflow-steps">{flow_html}</div>
            <div style="margin-top:16px;">
                <table class="data-table">
                    <thead><tr><th>Step</th><th>Details</th><th>Owner</th><th>Duration</th></tr></thead>
                    <tbody>{detail_rows}</tbody>
                </table>
            </div>
        </div>'''

    sections.append(f'''<div class="section" id="sec-2">
        <div class="section-title">Process Workflows</div>
        <div class="section-desc">Key workflows and process flows for {dept}.</div>
        {wf_html}
    </div>''')

    # ── Tab 4: Documents ──
    tabs.append("Documents")
    docs_html = '<div class="doc-grid">'
    for doc in data.get("documents", []):
        dname = _esc(doc.get("name", ""))
        ddesc = _esc(doc.get("description", ""))
        dfields = _esc(doc.get("fields", ""))
        dfreq = _esc(doc.get("frequency", ""))
        dflow = _esc(doc.get("flow", ""))
        dretention = _esc(doc.get("retention", ""))
        dformat = _esc(doc.get("format", ""))

        # Parse fields into individual items for better display
        field_items = [f.strip() for f in dfields.split(",") if f.strip()]
        if len(field_items) > 3:
            fields_display = '<div style="font-size:10px;margin-top:6px;padding:8px;background:var(--gray-light);border-radius:4px;">'
            fields_display += '<strong style="color:var(--navy);display:block;margin-bottom:4px;">Fields:</strong>'
            fields_display += '<div style="display:flex;flex-wrap:wrap;gap:3px;">'
            for fi in field_items:
                fields_display += f'<span style="background:#fff;border:1px solid var(--gray-mid);padding:1px 5px;border-radius:3px;font-size:9px;">{_esc(fi)}</span>'
            fields_display += '</div></div>'
        else:
            fields_display = f'<div style="font-size:10px;margin-top:6px;padding:6px;background:var(--gray-light);border-radius:4px;"><strong style="color:var(--navy);">Fields:</strong> {dfields}</div>'

        meta_badges = f'<span class="doc-freq">{dfreq}</span>'
        if dformat:
            meta_badges += f' <span style="font-size:9px;background:var(--purple-card);color:var(--purple-border);padding:2px 6px;border-radius:3px;display:inline-block;margin-top:4px;font-weight:600;">{dformat}</span>'
        if dretention:
            meta_badges += f' <span style="font-size:9px;background:var(--orange-card);color:var(--orange-border);padding:2px 6px;border-radius:3px;display:inline-block;margin-top:4px;font-weight:600;">Retain: {dretention}</span>'

        docs_html += f'''<div class="doc-card">
            <h4>{dname}</h4>
            <div class="doc-desc">{ddesc}</div>
            {fields_display}
            <div class="doc-flow">{dflow}</div>
            <div style="margin-top:6px;">{meta_badges}</div>
        </div>'''
    docs_html += '</div>'

    sections.append(f'''<div class="section" id="sec-3">
        <div class="section-title">Documents & Forms</div>
        <div class="section-desc">All documents created, used, and maintained by {dept}. Total: {len(data.get("documents", []))} documents.</div>
        {docs_html}
    </div>''')

    # ── Tab 5: KPIs ──
    tabs.append("KPIs")
    kpi_html = '<div class="kpi-grid">'
    kpi_colors = ["green", "blue", "orange", "purple", "red", "teal"]
    for i, kpi in enumerate(data.get("kpis", [])):
        kname = _esc(kpi.get("name", ""))
        ktarget = _esc(str(kpi.get("target", "")))
        kunit = _esc(kpi.get("unit", ""))
        kdesc = _esc(kpi.get("description", ""))
        kmeasure = _esc(kpi.get("measurement", ""))
        kaccount = _esc(kpi.get("accountable", ""))
        kcolor = kpi.get("color", kpi_colors[i % len(kpi_colors)])
        extras = ""
        if kmeasure:
            extras += f'<div style="font-size:10px;color:var(--gray-text);margin-top:6px;padding-top:6px;border-top:1px dashed var(--gray-mid);"><strong>How:</strong> {kmeasure}</div>'
        if kaccount:
            extras += f'<div style="font-size:10px;color:var(--navy);margin-top:4px;font-weight:600;">Owner: {kaccount}</div>'
        kpi_html += f'''<div class="kpi-card {kcolor}">
            <div class="kpi-name">{kname}</div>
            <div class="kpi-value">{ktarget}</div>
            <div class="kpi-target">Target: {ktarget} {kunit}</div>
            <div class="kpi-desc">{kdesc}</div>
            {extras}
        </div>'''
    kpi_html += '</div>'

    sections.append(f'''<div class="section" id="sec-4">
        <div class="section-title">Key Performance Indicators</div>
        <div class="section-desc">Performance metrics for {dept}. Total: {len(data.get("kpis", []))} KPIs tracked.</div>
        {kpi_html}
    </div>''')

    # ── Tab 6: Interactions ──
    tabs.append("Interactions")
    int_html = '<div class="interaction-map">'
    for inter in data.get("interactions", []):
        idept = _esc(inter.get("department", ""))
        items_html = ""
        for inb in inter.get("inbound", []):
            items_html += f'<div class="flow-item"><span class="flow-dir in">IN</span> <span>{_esc(inb)}</span></div>'
        for outb in inter.get("outbound", []):
            items_html += f'<div class="flow-item"><span class="flow-dir out">OUT</span> <span>{_esc(outb)}</span></div>'
        int_html += f'''<div class="dept-card">
            <h4>{idept}</h4>
            {items_html}
        </div>'''
    int_html += '</div>'

    sections.append(f'''<div class="section" id="sec-5">
        <div class="section-title">Department Interactions</div>
        <div class="section-desc">How {dept} connects with other departments.</div>
        {int_html}
    </div>''')

    # ── Tab 7: Escalation ──
    tabs.append("Escalation")
    esc_html = ""
    esc_colors = ["#34A853", "#F09300", "#D93025", "#8E24AA"]
    for i, esc in enumerate(data.get("escalation_matrix", [])):
        elevel = esc.get("level", i + 1)
        etitle = _esc(esc.get("title", f"Level {elevel}"))
        edesc = _esc(esc.get("description", ""))
        etrigger = _esc(esc.get("trigger", ""))
        etime = _esc(esc.get("response_time", ""))
        eresolution = _esc(esc.get("resolution_time", ""))
        eauth = _esc(esc.get("authority", ""))
        ecolor = esc_colors[min(i, len(esc_colors) - 1)]

        trigger_html = f'<div style="font-size:11px;margin-top:6px;padding:6px;background:var(--red-bg);border-radius:4px;"><strong style="color:var(--red-badge);">Trigger:</strong> {etrigger}</div>' if etrigger else ""

        actions_html = ""
        for act in esc.get("actions", []):
            actions_html += f'<div style="font-size:10px;color:var(--text-dark);margin-top:2px;padding-left:10px;">&#8226; {_esc(act)}</div>'
        if actions_html:
            actions_html = f'<div style="margin-top:6px;"><strong style="font-size:10px;color:var(--navy);">Actions:</strong>{actions_html}</div>'

        examples_html = ""
        for ex in esc.get("examples", []):
            examples_html += f'<div style="font-size:10px;color:var(--gray-text);margin-top:2px;padding-left:10px;">&#8226; {_esc(ex)}</div>'
        if examples_html:
            examples_html = f'<div style="margin-top:6px;"><strong style="font-size:10px;color:var(--navy);">Examples:</strong>{examples_html}</div>'

        time_display = f'<span style="color:var(--orange-border);font-weight:600;">Response: {etime}</span>'
        if eresolution:
            time_display += f' <span style="color:var(--gray-text);">|</span> <span style="color:var(--green-border);font-weight:600;">Resolution: {eresolution}</span>'

        esc_html += f'''<div style="background:#fff;border-radius:8px;padding:16px;box-shadow:var(--shadow);margin-bottom:12px;border-left:5px solid {ecolor};">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div>
                    <span class="level-badge" style="background:{ecolor};display:inline-block;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:700;color:#fff;">Level {elevel}</span>
                    <span style="font-size:14px;font-weight:700;color:var(--navy);margin-left:8px;">{etitle}</span>
                </div>
                <div style="font-size:11px;">{time_display}</div>
            </div>
            <div style="font-size:12px;color:var(--gray-text);margin-top:8px;line-height:1.5;">{edesc}</div>
            {trigger_html}
            <div style="font-size:11px;color:var(--navy);margin-top:6px;font-weight:600;">Authority: {eauth}</div>
            {actions_html}
            {examples_html}
        </div>'''

    sections.append(f'''<div class="section" id="sec-6">
        <div class="section-title">Escalation Matrix</div>
        <div class="section-desc">When and how to escalate issues in {dept}. {len(data.get("escalation_matrix", []))} escalation levels defined.</div>
        {esc_html}
    </div>''')

    # ── Tab 8: Compliance ──
    tabs.append("Compliance")
    comp_html = '<div class="compliance-grid">'
    for ci in data.get("compliance_items", []):
        cname = _esc(ci.get("name", ""))
        cdesc = _esc(ci.get("description", ""))
        cfreq = _esc(ci.get("frequency", ""))
        cresp = _esc(ci.get("responsible", ""))
        cdocs = _esc(ci.get("documentation", ""))
        extras = ""
        if cresp:
            extras += f'<div style="font-size:10px;color:var(--navy);margin-top:6px;font-weight:600;">Responsible: {cresp}</div>'
        if cdocs:
            extras += f'<div style="font-size:10px;color:var(--gray-text);margin-top:4px;padding:4px 6px;background:var(--gray-light);border-radius:3px;"><strong>Records:</strong> {cdocs}</div>'
        comp_html += f'''<div class="compliance-card">
            <h4>{cname}</h4>
            <p>{cdesc}</p>
            <div class="freq">Frequency: {cfreq}</div>
            {extras}
        </div>'''
    comp_html += '</div>'

    sections.append(f'''<div class="section" id="sec-7">
        <div class="section-title">Compliance & Regulations</div>
        <div class="section-desc">Regulatory requirements and standards for {dept}. Total: {len(data.get("compliance_items", []))} compliance items.</div>
        {comp_html}
    </div>''')

    # ── Build tab navigation ──
    tab_nav = ""
    for i, tab in enumerate(tabs):
        active = " active" if i == 0 else ""
        tab_nav += f'<button class="nav-tab{active}" onclick="switchTab({i})">{tab}</button>'

    sections_html = "\n".join(sections)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{dept} — Blueprint | {company}</title>
<style>{BASE_CSS}</style>
</head>
<body>

<header class="main-header">
  <div style="font-size:12px;opacity:0.7;margin-bottom:4px;">
    <a href="service-blueprint.html" style="color:#FFB74D;text-decoration:none;">Master Blueprint</a> &rsaquo; {dept}
  </div>
  <h1>{dept}</h1>
  <div class="subtitle">{company} | Department Blueprint</div>
</header>

<nav class="nav-tabs">{tab_nav}</nav>

{sections_html}

<script>
function switchTab(idx) {{
  document.querySelectorAll('.nav-tab').forEach((t, i) => t.classList.toggle('active', i === idx));
  document.querySelectorAll('.section').forEach((s, i) => s.classList.toggle('active', i === idx));
}}
</script>
</body>
</html>'''


# ─── Glossary & Appendix Renderer ─────────────────────────────────────


def render_glossary(data: dict, company_name: str) -> str:
    """Render the glossary & appendix catch-all reference document."""
    company = _esc(company_name)

    tabs = []
    sections = []

    # ── Tab 1: Glossary ──
    tabs.append("Glossary")
    # Group terms by category
    terms = data.get("glossary", [])
    categories = {}
    for t in terms:
        cat = t.get("category", "General")
        if isinstance(cat, list):
            cat = cat[0] if cat else "General"
        categories.setdefault(cat, []).append(t)

    glossary_html = ""
    cat_colors = {"Technical": "blue", "Commercial": "green", "Legal": "orange", "Safety": "red",
                  "Operations": "teal", "Finance": "purple", "HR": "purple", "IT": "blue",
                  "Marketing": "green", "General": "blue"}
    for cat, cat_terms in sorted(categories.items()):
        color = cat_colors.get(cat, "blue")
        glossary_html += f'<h3 style="font-size:14px;font-weight:700;color:var(--navy);margin:20px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--{color}-border);">{_esc(cat)} ({len(cat_terms)} terms)</h3>'
        glossary_html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:10px;margin-bottom:16px;">'
        for t in sorted(cat_terms, key=lambda x: x.get("term", "")):
            term = _esc(t.get("term", ""))
            full_form = _esc(t.get("full_form", ""))
            definition = _esc(t.get("definition", ""))
            abbr_html = f'<div style="font-size:10px;color:var(--{color}-border);font-weight:600;">{full_form}</div>' if full_form and full_form != term else ""
            glossary_html += f'''<div style="background:#fff;border-radius:6px;padding:10px 12px;box-shadow:var(--shadow);border-left:3px solid var(--{color}-border);">
                <div style="font-size:13px;font-weight:700;color:var(--navy);">{term}</div>
                {abbr_html}
                <div style="font-size:11px;color:var(--gray-text);margin-top:4px;line-height:1.5;">{definition}</div>
            </div>'''
        glossary_html += '</div>'

    sections.append(f'''<div class="section active" id="sec-0">
        <div class="section-title">Industry Glossary</div>
        <div class="section-desc">Complete terminology reference — {len(terms)} terms across {len(categories)} categories.</div>
        {glossary_html}
    </div>''')

    # ── Tab 2: Cross-Department Processes ──
    tabs.append("Cross-Dept Processes")
    xdept_html = ""
    for proc in data.get("cross_department_processes", []):
        pname = _esc(proc.get("name", ""))
        pdesc = _esc(proc.get("description", ""))
        ptrigger = _esc(proc.get("trigger", ""))
        pfreq = _esc(proc.get("frequency", ""))
        poutput = _esc(proc.get("output", ""))
        depts = proc.get("departments_involved", [])
        if isinstance(depts, str):
            depts = [depts]
        dept_badges = " ".join(f'<span style="font-size:9px;background:var(--blue-card);color:var(--blue-border);padding:2px 6px;border-radius:3px;font-weight:600;">{_esc(d)}</span>' for d in depts)
        steps = proc.get("key_steps", [])
        if isinstance(steps, str):
            steps = [steps]
        steps_html = ""
        for j, step in enumerate(steps):
            steps_html += f'<div style="font-size:11px;padding:3px 0;color:var(--text-dark);">{j+1}. {_esc(step)}</div>'

        xdept_html += f'''<div class="workflow-container">
            <div class="workflow-title">{pname}</div>
            <div style="font-size:12px;color:var(--gray-text);margin-bottom:8px;">{pdesc}</div>
            <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:8px;">
                <div style="font-size:10px;"><strong>Trigger:</strong> {ptrigger}</div>
                <div style="font-size:10px;"><strong>Frequency:</strong> {pfreq}</div>
                <div style="font-size:10px;"><strong>Output:</strong> {poutput}</div>
            </div>
            <div style="margin-bottom:8px;">{dept_badges}</div>
            {steps_html}
        </div>'''

    sections.append(f'''<div class="section" id="sec-1">
        <div class="section-title">Cross-Department Processes</div>
        <div class="section-desc">Processes that span multiple departments — {len(data.get("cross_department_processes", []))} processes mapped.</div>
        {xdept_html}
    </div>''')

    # ── Tab 3: Policies ──
    tabs.append("Policies")
    pol_html = '<div class="doc-grid">'
    for pol in data.get("general_policies", []):
        pname = _esc(pol.get("name", ""))
        pscope = _esc(pol.get("scope", ""))
        pdesc = _esc(pol.get("description", ""))
        penforce = _esc(pol.get("enforcement", ""))
        pconseq = _esc(pol.get("consequences", ""))
        pol_html += f'''<div class="doc-card" style="border-left-color:var(--navy);">
            <h4>{pname}</h4>
            <div style="font-size:9px;background:var(--blue-card);color:var(--blue-border);padding:2px 6px;border-radius:3px;display:inline-block;font-weight:600;margin-bottom:4px;">Scope: {pscope}</div>
            <div class="doc-desc">{pdesc}</div>
            <div style="font-size:10px;color:var(--navy);margin-top:6px;"><strong>Enforcement:</strong> {penforce}</div>
            <div style="font-size:10px;color:var(--red-badge);margin-top:4px;"><strong>Violation:</strong> {pconseq}</div>
        </div>'''
    pol_html += '</div>'

    sections.append(f'''<div class="section" id="sec-2">
        <div class="section-title">General Policies</div>
        <div class="section-desc">Company-wide policies and rules — {len(data.get("general_policies", []))} policies.</div>
        {pol_html}
    </div>''')

    # ── Tab 4: Technology Landscape ──
    tabs.append("Technology")
    tech_html = ""
    tech_items = data.get("technology_landscape", [])
    # Group by category
    tech_cats = {}
    for t in tech_items:
        cat = t.get("category", "Other")
        if isinstance(cat, list):
            cat = cat[0] if cat else "Other"
        tech_cats.setdefault(cat, []).append(t)

    for cat, items in sorted(tech_cats.items()):
        tech_html += f'<h3 style="font-size:14px;font-weight:700;color:var(--navy);margin:16px 0 10px;">{_esc(cat)}</h3>'
        tech_html += '<table class="data-table"><thead><tr><th>System</th><th>Purpose</th><th>Users</th><th>Integrations</th><th>Status</th></tr></thead><tbody>'
        for t in items:
            status = _esc(t.get("status", ""))
            status_color = {"Current": "var(--green-border)", "Planned": "var(--orange-border)", "Recommended": "var(--blue-border)"}.get(status, "var(--gray-text)")
            tech_html += f'''<tr>
                <td style="font-weight:600;">{_esc(t.get("system", ""))}</td>
                <td>{_esc(t.get("purpose", ""))}</td>
                <td>{_esc(t.get("users", ""))}</td>
                <td style="font-size:11px;">{_esc(t.get("integration_points", ""))}</td>
                <td><span style="color:{status_color};font-weight:600;font-size:11px;">{status}</span></td>
            </tr>'''
        tech_html += '</tbody></table>'

    sections.append(f'''<div class="section" id="sec-3">
        <div class="section-title">Technology Landscape</div>
        <div class="section-desc">Systems, tools, and technology — current and recommended. {len(tech_items)} systems mapped.</div>
        {tech_html}
    </div>''')

    # ── Tab 5: Risk Register ──
    tabs.append("Risk Register")
    risk_html = '<table class="data-table"><thead><tr><th>Risk</th><th>Category</th><th style="text-align:center;">Likelihood</th><th style="text-align:center;">Impact</th><th>Mitigation</th><th>Contingency</th><th>Owner</th></tr></thead><tbody>'
    risk_colors = {"High": "var(--red-badge)", "Medium": "var(--orange-border)", "Low": "var(--green-border)"}
    for r in data.get("risk_register", []):
        likelihood = _esc(r.get("likelihood", ""))
        impact = _esc(r.get("impact", ""))
        lcolor = risk_colors.get(likelihood, "var(--gray-text)")
        icolor = risk_colors.get(impact, "var(--gray-text)")
        risk_html += f'''<tr>
            <td style="font-weight:600;">{_esc(r.get("risk", ""))}</td>
            <td><span style="font-size:10px;background:var(--blue-card);color:var(--blue-border);padding:2px 5px;border-radius:3px;">{_esc(r.get("category", ""))}</span></td>
            <td style="text-align:center;"><span style="color:{lcolor};font-weight:700;">{likelihood}</span></td>
            <td style="text-align:center;"><span style="color:{icolor};font-weight:700;">{impact}</span></td>
            <td style="font-size:11px;">{_esc(r.get("mitigation", ""))}</td>
            <td style="font-size:11px;">{_esc(r.get("contingency", ""))}</td>
            <td style="font-size:11px;white-space:nowrap;">{_esc(r.get("owner", ""))}</td>
        </tr>'''
    risk_html += '</tbody></table>'

    sections.append(f'''<div class="section" id="sec-4">
        <div class="section-title">Risk Register</div>
        <div class="section-desc">Business risks across all categories — {len(data.get("risk_register", []))} risks identified.</div>
        {risk_html}
    </div>''')

    # ── Tab 6: Meetings & Cadences ──
    tabs.append("Meetings")
    meet_html = '<div class="doc-grid">'
    freq_colors = {"Daily": "red", "Weekly": "orange", "Monthly": "blue", "Quarterly": "purple", "Annual": "teal"}
    for m in data.get("meeting_cadences", []):
        mfreq = _esc(m.get("frequency", ""))
        fcolor_key = mfreq.split("/")[0].strip() if "/" in mfreq else mfreq
        fcolor = freq_colors.get(fcolor_key, "blue")
        meet_html += f'''<div class="doc-card" style="border-left-color:var(--{fcolor}-border);">
            <h4>{_esc(m.get("meeting", ""))}</h4>
            <span style="font-size:9px;background:var(--{fcolor}-card);color:var(--{fcolor}-border);padding:2px 6px;border-radius:3px;font-weight:600;">{mfreq}</span>
            <span style="font-size:9px;background:var(--gray-light);color:var(--gray-text);padding:2px 6px;border-radius:3px;margin-left:4px;">{_esc(m.get("duration", ""))}</span>
            <div style="font-size:11px;margin-top:6px;"><strong>Participants:</strong> {_esc(m.get("participants", ""))}</div>
            <div style="font-size:11px;margin-top:4px;color:var(--gray-text);"><strong>Agenda:</strong> {_esc(m.get("agenda", ""))}</div>
            <div style="font-size:10px;margin-top:4px;color:var(--green-border);"><strong>Output:</strong> {_esc(m.get("output", ""))}</div>
        </div>'''
    meet_html += '</div>'

    sections.append(f'''<div class="section" id="sec-5">
        <div class="section-title">Meeting Cadences</div>
        <div class="section-desc">Recurring meetings and review cycles — {len(data.get("meeting_cadences", []))} meetings.</div>
        {meet_html}
    </div>''')

    # ── Tab 7: Market & Customers ──
    tabs.append("Market & Customers")
    market_html = ""

    # Customer segments
    segs = data.get("customer_segmentation", [])
    if segs:
        market_html += '<h3 style="font-size:15px;font-weight:700;color:var(--navy);margin-bottom:12px;">Customer Segments</h3>'
        market_html += '<div class="card-grid">'
        seg_colors = ["blue", "green", "orange", "purple", "teal", "red"]
        for i, seg in enumerate(segs):
            color = seg_colors[i % len(seg_colors)]
            market_html += f'''<div class="metric-card {color}">
                <h4>{_esc(seg.get("segment", ""))}</h4>
                <div style="font-size:12px;color:var(--text-dark);margin-top:4px;">{_esc(seg.get("description", ""))}</div>
                <div style="font-size:11px;color:var(--gray-text);margin-top:6px;"><strong>Needs:</strong> {_esc(seg.get("needs", ""))}</div>
                <div style="font-size:11px;color:var(--gray-text);margin-top:3px;"><strong>Buying Pattern:</strong> {_esc(seg.get("buying_pattern", ""))}</div>
                <div style="font-size:11px;color:var(--gray-text);margin-top:3px;"><strong>Service Level:</strong> {_esc(seg.get("service_level", ""))}</div>
                <div style="font-size:12px;font-weight:700;color:var(--navy);margin-top:6px;">{_esc(seg.get("revenue_share", ""))}</div>
            </div>'''
        market_html += '</div>'

    # Seasonal patterns
    seasons = data.get("seasonal_patterns", [])
    if seasons:
        market_html += '<h3 style="font-size:15px;font-weight:700;color:var(--navy);margin:24px 0 12px;">Seasonal Patterns</h3>'
        market_html += '<table class="data-table"><thead><tr><th>Period</th><th>Pattern</th><th>Impact</th><th>Preparation</th></tr></thead><tbody>'
        for s in seasons:
            market_html += f'''<tr>
                <td style="font-weight:600;white-space:nowrap;">{_esc(s.get("period", ""))}</td>
                <td>{_esc(s.get("pattern", ""))}</td>
                <td>{_esc(s.get("impact", ""))}</td>
                <td>{_esc(s.get("preparation", ""))}</td>
            </tr>'''
        market_html += '</tbody></table>'

    # Vendor relationships
    vendors = data.get("vendor_relationships", [])
    if vendors:
        market_html += '<h3 style="font-size:15px;font-weight:700;color:var(--navy);margin:24px 0 12px;">Vendor & Partner Relationships</h3>'
        market_html += '<div class="doc-grid">'
        for v in vendors:
            market_html += f'''<div class="doc-card" style="border-left-color:var(--teal);">
                <h4>{_esc(v.get("vendor_type", ""))}</h4>
                <div class="doc-desc">{_esc(v.get("examples", ""))}</div>
                <div style="font-size:11px;margin-top:4px;"><strong>Relationship:</strong> {_esc(v.get("relationship", ""))}</div>
                <div style="font-size:11px;margin-top:3px;color:var(--gray-text);"><strong>Terms:</strong> {_esc(v.get("key_terms", ""))}</div>
                <div style="font-size:10px;margin-top:3px;color:var(--blue-border);"><strong>Management:</strong> {_esc(v.get("management", ""))}</div>
            </div>'''
        market_html += '</div>'

    sections.append(f'''<div class="section" id="sec-6">
        <div class="section-title">Market, Customers & Vendors</div>
        <div class="section-desc">Customer segments, seasonal patterns, and vendor relationships.</div>
        {market_html}
    </div>''')

    # ── Tab 8: Career Paths & Insurance ──
    tabs.append("People & Compliance")
    people_html = ""

    # Career paths
    careers = data.get("career_paths", [])
    if careers:
        people_html += '<h3 style="font-size:15px;font-weight:700;color:var(--navy);margin-bottom:12px;">Career Paths</h3>'
        for cp in careers:
            track = _esc(cp.get("track", ""))
            levels = cp.get("levels", [])
            if isinstance(levels, str):
                levels = [levels]
            progression = _esc(cp.get("typical_progression", ""))
            skills = _esc(cp.get("skills_needed", ""))
            path_steps = ""
            for j, level in enumerate(levels):
                if j > 0:
                    path_steps += '<span style="color:var(--navy);font-weight:700;margin:0 6px;">&rarr;</span>'
                path_steps += f'<span style="background:var(--blue-card);border:1px solid var(--blue-border);padding:4px 10px;border-radius:4px;font-size:11px;font-weight:600;color:var(--navy);">{_esc(level)}</span>'
            people_html += f'''<div style="background:#fff;border-radius:8px;padding:14px;box-shadow:var(--shadow);margin-bottom:12px;border-left:4px solid var(--purple-border);">
                <div style="font-size:14px;font-weight:700;color:var(--navy);margin-bottom:8px;">{track}</div>
                <div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;margin-bottom:8px;">{path_steps}</div>
                <div style="font-size:11px;color:var(--gray-text);"><strong>Progression:</strong> {progression}</div>
                <div style="font-size:11px;color:var(--gray-text);margin-top:3px;"><strong>Skills:</strong> {skills}</div>
            </div>'''

    # Insurance
    insurance = data.get("insurance_requirements", [])
    if insurance:
        people_html += '<h3 style="font-size:15px;font-weight:700;color:var(--navy);margin:24px 0 12px;">Insurance Requirements</h3>'
        people_html += '<table class="data-table"><thead><tr><th>Type</th><th>Coverage</th><th>Required By</th><th>Typical Value</th></tr></thead><tbody>'
        for ins in insurance:
            people_html += f'''<tr>
                <td style="font-weight:600;">{_esc(ins.get("type", ""))}</td>
                <td>{_esc(ins.get("coverage", ""))}</td>
                <td>{_esc(ins.get("required_by", ""))}</td>
                <td style="font-weight:600;color:var(--navy);">{_esc(ins.get("typical_value", ""))}</td>
            </tr>'''
        people_html += '</tbody></table>'

    sections.append(f'''<div class="section" id="sec-7">
        <div class="section-title">People & Compliance</div>
        <div class="section-desc">Career paths, insurance requirements, and people-related policies.</div>
        {people_html}
    </div>''')

    # ── Tab 9: Benchmarks & Common Mistakes ──
    tabs.append("Benchmarks & Pitfalls")
    bench_html = ""

    benchmarks = data.get("industry_benchmarks", [])
    if benchmarks:
        bench_html += '<h3 style="font-size:15px;font-weight:700;color:var(--navy);margin-bottom:12px;">Industry Benchmarks</h3>'
        bench_html += '<div class="kpi-grid">'
        bcolors = ["green", "blue", "orange", "purple", "teal", "red"]
        for i, b in enumerate(benchmarks):
            color = bcolors[i % len(bcolors)]
            bench_html += f'''<div class="kpi-card {color}">
                <div class="kpi-name">{_esc(b.get("metric", ""))}</div>
                <div class="kpi-value">{_esc(b.get("value", ""))}</div>
                <div style="font-size:10px;color:var(--gray-text);margin-top:4px;">{_esc(b.get("context", ""))}</div>
                <div style="font-size:9px;color:var(--blue-border);margin-top:4px;">Source: {_esc(b.get("source", ""))}</div>
            </div>'''
        bench_html += '</div>'

    mistakes = data.get("common_mistakes", [])
    if mistakes:
        bench_html += '<h3 style="font-size:15px;font-weight:700;color:var(--navy);margin:24px 0 12px;">Common Mistakes to Avoid</h3>'
        for m in mistakes:
            bench_html += f'''<div style="background:#fff;border-radius:8px;padding:12px 14px;box-shadow:var(--shadow);margin-bottom:8px;border-left:4px solid var(--red-badge);">
                <div style="font-size:13px;font-weight:600;color:var(--red-badge);">{_esc(m.get("mistake", ""))}</div>
                <div style="font-size:11px;color:var(--gray-text);margin-top:4px;">
                    <span style="background:var(--blue-card);padding:1px 5px;border-radius:3px;font-size:9px;font-weight:600;color:var(--blue-border);">{_esc(m.get("department", ""))}</span>
                    <strong style="margin-left:6px;">Impact:</strong> {_esc(m.get("consequence", ""))}
                </div>
                <div style="font-size:11px;color:var(--green-border);margin-top:4px;"><strong>Prevention:</strong> {_esc(m.get("prevention", ""))}</div>
            </div>'''

    sections.append(f'''<div class="section" id="sec-8">
        <div class="section-title">Industry Benchmarks & Common Pitfalls</div>
        <div class="section-desc">How you compare to industry standards, and mistakes to avoid.</div>
        {bench_html}
    </div>''')

    # ── Build tab navigation ──
    tab_nav = ""
    for i, tab in enumerate(tabs):
        active = " active" if i == 0 else ""
        tab_nav += f'<button class="nav-tab{active}" onclick="switchGlossaryTab({i})">{tab}</button>'

    sections_html = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Glossary & Appendix | {company}</title>
<style>{BASE_CSS}</style>
</head>
<body>

<header class="main-header">
  <div style="font-size:12px;opacity:0.7;margin-bottom:4px;">
    <a href="service-blueprint.html" style="color:#FFB74D;text-decoration:none;">Master Blueprint</a> &rsaquo; Glossary & Appendix
  </div>
  <h1>Glossary & Appendix</h1>
  <div class="subtitle">{company} | Everything Else — The Complete Reference</div>
</header>

<nav class="nav-tabs">{tab_nav}</nav>

{sections_html}

<script>
function switchGlossaryTab(idx) {{
  document.querySelectorAll('.nav-tab').forEach((t, i) => t.classList.toggle('active', i === idx));
  document.querySelectorAll('.section').forEach((s, i) => s.classList.toggle('active', i === idx));
}}
</script>
</body>
</html>"""
