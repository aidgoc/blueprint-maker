"""HTML Template Renderer — generates beautiful blueprint HTML files."""
import json


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

BASE_CSS = CSS_VARS + """
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=Source+Sans+3:wght@400;500;600&display=swap');
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Source Sans 3', 'Source Sans Pro', -apple-system, sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.7; font-size: 15px;
  -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
}
.main-header {
  background: var(--surface); border-bottom: 1px solid var(--border);
  padding: 20px 32px; position: sticky; top: 0; z-index: 200;
  display: flex; justify-content: space-between; align-items: flex-start;
}
.header-left { flex: 1; }
.header-right {
  font-size: 13px; font-weight: 500; color: var(--text-muted); letter-spacing: -0.3px;
  padding-top: 4px;
}
.main-header h1 {
  font-family: 'Crimson Pro', Georgia, serif;
  font-size: 20px; font-weight: 700; color: var(--brand); letter-spacing: -0.3px;
}
.main-header .subtitle {
  font-size: 13px; color: var(--text-secondary); margin-top: 2px;
}
.main-header .breadcrumb {
  font-size: 12px; color: var(--text-muted); margin-bottom: 4px;
}
.main-header .breadcrumb a {
  color: var(--brand); text-decoration: none; font-weight: 500;
}
.main-header .breadcrumb a:hover { text-decoration: underline; }
.nav-tabs {
  background: var(--surface); padding: 0 32px; display: flex; gap: 0;
  position: sticky; top: 64px; z-index: 199; border-bottom: 1px solid var(--border); overflow-x: auto;
}
.nav-tab {
  padding: 14px 20px; border: none; background: transparent; color: var(--text-secondary);
  font-size: 13px; font-weight: 600; cursor: pointer; border-bottom: 2px solid transparent;
  white-space: nowrap; transition: all 0.15s; font-family: inherit;
}
.nav-tab:hover { color: var(--text); }
.nav-tab.active { color: var(--brand); border-bottom-color: var(--gold); }
.legend-bar {
  display: flex; flex-wrap: wrap; gap: 16px; padding: 10px 32px;
  background: var(--surface); border-bottom: 1px solid var(--border); align-items: center;
}
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 12px; color: var(--text-secondary); }
.legend-swatch { width: 10px; height: 10px; border-radius: 50%; }
.legend-swatch.activity { background: var(--brand); }
.legend-swatch.document { background: var(--green); }
.legend-swatch.approval { background: var(--amber); }
.legend-swatch.critical { background: var(--red); }
.legend-swatch.handover { background: var(--purple); }
.section { display: none; padding: 24px 32px; max-width: 1440px; margin: 0 auto; }
.section.active { display: block; }
.section-title {
  font-family: 'Crimson Pro', Georgia, serif;
  font-size: 20px; font-weight: 700; color: var(--brand); margin-bottom: 4px;
  letter-spacing: -0.2px; padding-bottom: 0.5rem; position: relative;
}
.section-title::after {
  content: ''; display: block; width: 40px; height: 2px; background: var(--gold); margin-top: 0.5rem;
}
.section-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 24px; line-height: 1.6; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; margin-bottom: 24px; }
.metric-card {
  background: var(--surface); border-radius: var(--radius); padding: 20px; box-shadow: var(--shadow-sm);
  border: 1px solid var(--border); position: relative; overflow: hidden;
}
.metric-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: var(--brand);
}
.metric-card.green::before { background: var(--green); }
.metric-card.orange::before { background: var(--amber); }
.metric-card.red::before { background: var(--red); }
.metric-card.purple::before { background: var(--purple); }
.metric-card.teal::before { background: var(--teal); }
.metric-card.blue::before { background: var(--brand); }
.metric-card h4 { font-size: 11px; text-transform: uppercase; color: var(--text-secondary); letter-spacing: 0.5px; margin-bottom: 8px; font-weight: 600; }
.metric-card .value { font-size: 28px; font-weight: 700; color: var(--brand); }
.metric-card .detail { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }

/* Timeline */
.timeline { position: relative; margin: 20px 0; }
.timeline::before {
  content: ''; position: absolute; left: 24px; top: 0; bottom: 0; width: 2px;
  background: var(--border); border-radius: 1px;
}
.time-block { margin-bottom: 20px; position: relative; padding-left: 60px; }
.time-marker {
  position: absolute; left: 14px; top: 0; width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700; z-index: 2; border: 2px solid var(--surface);
}
.time-marker.blue { background: var(--brand-light); color: var(--brand); }
.time-marker.green { background: var(--green-light); color: var(--green); }
.time-marker.teal { background: var(--teal-light); color: var(--teal); }
.time-marker.orange { background: var(--amber-light); color: var(--amber); }
.time-marker.purple { background: var(--purple-light); color: var(--purple); }
.time-marker.red { background: var(--red-light); color: var(--red); }
.time-block-header {
  background: var(--surface); border: 1px solid var(--border); color: var(--text);
  padding: 12px 16px; border-radius: var(--radius) var(--radius) 0 0;
  display: flex; justify-content: space-between; align-items: center; cursor: pointer;
  transition: background 0.15s;
}
.time-block-header:hover { background: var(--bg); }
.time-block-header h3 { font-size: 14px; font-weight: 600; }
.time-block-header .time-range { font-size: 12px; color: var(--text-secondary); font-weight: 500; }
.time-block-body {
  background: var(--surface); border: 1px solid var(--border); border-top: none;
  border-radius: 0 0 var(--radius) var(--radius); padding: 16px; box-shadow: var(--shadow-sm);
}
.time-block-body.collapsed { display: none; }
.activity-item { display: flex; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--border-light); align-items: flex-start; }
.activity-item:last-child { border-bottom: none; }
.act-icon {
  width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center;
  justify-content: center; font-size: 15px; flex-shrink: 0;
}
.act-icon.blue { background: var(--blue-card); }
.act-icon.green { background: var(--green-card); }
.act-icon.orange { background: var(--amber-card); }
.act-icon.red { background: var(--red-card); }
.act-icon.purple { background: var(--purple-card); }
.act-icon.teal { background: var(--teal-card); }
.act-content h4 { font-size: 13px; font-weight: 600; color: var(--text); }
.act-content p { font-size: 12px; color: var(--text-secondary); margin-top: 2px; line-height: 1.5; }
.tag { font-size: 10px; padding: 2px 8px; border-radius: 100px; font-weight: 600; display: inline-block; margin-top: 4px; margin-right: 4px; }
.tag.doc { background: var(--green-light); color: var(--green); }
.tag.approval { background: var(--amber-light); color: var(--amber); }
.tag.critical { background: var(--red-light); color: var(--red); }
.tag.system { background: var(--brand-light); color: var(--brand); }
.tag.handover { background: var(--purple-light); color: var(--purple); }

/* Workflows */
.workflow-container { background: var(--surface); border-radius: var(--radius); padding: 22px; box-shadow: var(--shadow-sm); margin-bottom: 18px; overflow-x: auto; border: 1px solid var(--border); }
.workflow-title { font-family: 'Crimson Pro', Georgia, serif; font-size: 16px; font-weight: 700; color: var(--brand); margin-bottom: 14px; }
.workflow-steps { display: flex; align-items: flex-start; gap: 0; min-width: max-content; padding: 10px 0; }
.wf-step { display: flex; flex-direction: column; align-items: center; min-width: 140px; max-width: 160px; text-align: center; }
.wf-step-box {
  width: 120px; padding: 10px 8px; border-radius: 8px; font-size: 11px; font-weight: 600;
  line-height: 1.4; border: 1.5px solid; min-height: 56px; display: flex; align-items: center; justify-content: center;
}
.wf-step-box.blue { background: var(--brand-light); border-color: var(--brand); color: var(--brand); }
.wf-step-box.green { background: var(--green-light); border-color: var(--green); color: #065F46; }
.wf-step-box.orange { background: var(--amber-light); border-color: var(--amber); color: #92400E; }
.wf-step-box.red { background: var(--red-light); border-color: var(--red); color: var(--red); }
.wf-step-box.purple { background: var(--purple-light); border-color: var(--purple); color: var(--purple); }
.wf-step-box.teal { background: var(--teal-light); border-color: var(--teal); color: #134E4A; }
.wf-step .wf-role { font-size: 10px; color: var(--text-secondary); margin-top: 6px; }
.wf-step .wf-time { font-size: 10px; color: var(--amber); margin-top: 2px; font-weight: 600; }
.wf-arrow { display: flex; align-items: center; justify-content: center; min-width: 36px; padding-top: 14px; color: var(--text-muted); font-size: 18px; font-weight: 400; }

/* Document cards */
.doc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; margin-bottom: 20px; }
.doc-card {
  background: var(--surface); border-radius: var(--radius); padding: 18px; box-shadow: var(--shadow-sm);
  border: 1px solid var(--border); position: relative; overflow: hidden;
}
.doc-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--green);
}
.doc-card h4 { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.doc-card .doc-desc { font-size: 12px; color: var(--text-secondary); line-height: 1.5; }
.doc-card .doc-flow { font-size: 11px; color: var(--brand); margin-top: 6px; font-weight: 500; }
.doc-card .doc-freq { font-size: 10px; background: var(--brand-light); color: var(--brand); padding: 3px 10px; border-radius: 100px; display: inline-block; margin-top: 6px; font-weight: 600; }

/* KPI cards */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 14px; margin-bottom: 20px; }
.kpi-card {
  background: var(--surface); border-radius: var(--radius); padding: 20px; box-shadow: var(--shadow-sm); text-align: center;
  border: 1px solid var(--border); position: relative; overflow: hidden;
}
.kpi-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--brand);
}
.kpi-card.green::before { background: var(--green); }
.kpi-card.orange::before { background: var(--amber); }
.kpi-card.red::before { background: var(--red); }
.kpi-card.purple::before { background: var(--purple); }
.kpi-card.blue::before { background: var(--brand); }
.kpi-card.teal::before { background: var(--teal); }
.kpi-card .kpi-name { font-size: 11px; text-transform: uppercase; color: var(--text-secondary); letter-spacing: 0.5px; font-weight: 600; }
.kpi-card .kpi-value { font-size: 28px; font-weight: 700; color: var(--brand); margin: 8px 0; }
.kpi-card .kpi-target { font-size: 12px; color: var(--green); font-weight: 600; }
.kpi-card .kpi-desc { font-size: 12px; color: var(--text-secondary); margin-top: 6px; }

/* Interaction map */
.interaction-map { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; margin-bottom: 20px; }
.dept-card {
  background: var(--surface); border-radius: var(--radius); padding: 18px; box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
}
.dept-card h4 { font-size: 14px; font-weight: 700; color: var(--text); margin-bottom: 10px; }
.flow-item { font-size: 12px; padding: 5px 0; border-bottom: 1px solid var(--border-light); display: flex; gap: 8px; align-items: flex-start; }
.flow-item:last-child { border-bottom: none; }
.flow-dir { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 100px; flex-shrink: 0; margin-top: 1px; }
.flow-dir.in { background: var(--green-light); color: var(--green); }
.flow-dir.out { background: var(--brand-light); color: var(--brand); }

/* Escalation */
.esc-card {
  background: var(--surface); border-radius: var(--radius); padding: 20px;
  box-shadow: var(--shadow-sm); margin-bottom: 14px; border: 1px solid var(--border);
  position: relative; overflow: hidden;
}
.esc-card::before {
  content: ''; position: absolute; top: 0; left: 0; bottom: 0; width: 4px;
}
.esc-card.level-1::before { background: var(--green); }
.esc-card.level-2::before { background: var(--amber); }
.esc-card.level-3::before { background: var(--red); }
.esc-card.level-4::before { background: var(--purple); }

/* Compliance */
.compliance-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; margin-bottom: 20px; }
.compliance-card {
  background: var(--surface); border-radius: var(--radius); padding: 20px; box-shadow: var(--shadow-sm);
  border: 1px solid var(--border); position: relative; overflow: hidden;
}
.compliance-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--text);
}
.compliance-card h4 { font-size: 14px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.compliance-card p { font-size: 12px; color: var(--text-secondary); line-height: 1.5; }
.compliance-card .freq { font-size: 11px; color: var(--amber); font-weight: 600; margin-top: 6px; }

/* Data table */
.data-table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; }
.data-table th { background: var(--brand); color: white; padding: 10px 14px; text-align: left; font-size: 13px; font-weight: 600; border-bottom: none; }
.data-table { border-left: 3px solid var(--gold); }
.data-table tr:nth-child(even) td { background: var(--bg); }
.data-table td { padding: 10px 14px; border-bottom: 1px solid var(--border); color: var(--text); }
.data-table tr:hover td { background: var(--bg); }

/* Blueprint grid (master) */
.blueprint-wrapper { overflow-x: auto; padding: 16px; }
.blueprint-grid { display: grid; gap: 1px; background: var(--border); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.stage-header {
  background: #F0F4F8; color: var(--text); padding: 14px 10px; text-align: center;
  font-weight: 700; font-size: 12px; display: flex; flex-direction: column; align-items: center; gap: 4px;
  border-bottom: 2px solid var(--brand);
}
.stage-header .stage-num {
  background: var(--brand); color: #fff; border-radius: 50%; width: 22px; height: 22px;
  display: flex; align-items: center; justify-content: center; font-size: 11px;
}
.role-label {
  background: #F8FAFC; color: var(--text); padding: 12px 12px; font-weight: 600; font-size: 12px;
  display: flex; align-items: center; gap: 6px; position: sticky; left: 0; z-index: 10; min-width: 170px; max-width: 170px;
  border-right: 2px solid var(--border);
}
.corner-cell {
  background: #F0F4F8; color: var(--text-secondary); padding: 12px; font-weight: 600; font-size: 12px;
  display: flex; align-items: center; justify-content: center; position: sticky; left: 0; z-index: 11;
  min-width: 170px; max-width: 170px; border-right: 2px solid var(--border); border-bottom: 2px solid var(--brand);
}
.bp-cell {
  background: var(--surface); padding: 8px; min-height: 80px; position: relative; cursor: pointer; transition: background 0.15s;
}
.bp-cell:hover { background: var(--bg); }
.card {
  padding: 5px 8px; border-radius: 6px; font-size: 11px; line-height: 1.4; margin-bottom: 4px;
  border-left: 3px solid; cursor: pointer;
}
.card.activity { background: var(--brand-light); border-color: #DBEAFE; }
.card.document { background: var(--green-light); border-color: #D1FAE5; }
.card.approval { background: var(--amber-light); border-color: #FDE68A; }
.card.critical { background: var(--red-light); border-color: #FECACA; }
.card.handover { background: var(--purple-light); border-color: #E9D5FF; }
.card-detail { display: none; font-size: 10px; color: var(--text-secondary); margin-top: 3px; line-height: 1.4; }
.bp-cell.expanded .card-detail { display: block; }
.ctrl-btn {
  padding: 8px 16px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface);
  font-size: 13px; cursor: pointer; font-weight: 500; transition: all 0.15s; color: var(--text);
  font-family: inherit;
}
.ctrl-btn:hover { background: var(--bg); border-color: var(--brand); color: var(--brand); }
.controls-bar { display: flex; gap: 10px; padding: 10px 32px; background: var(--surface); border-bottom: 1px solid var(--border); }

/* Print */
@media print {
  .main-header, .nav-tabs { position: static; }
  .section { display: block !important; page-break-inside: avoid; }
  .time-block-body.collapsed { display: block !important; }
  .nav-tabs, .controls-bar, .legend-bar { display: none; }
  body { font-size: 12px; background: #fff; }
}
@media (max-width: 768px) {
  .main-header, .section { padding-left: 14px; padding-right: 14px; }
  .nav-tabs { padding: 0 10px; }
  .nav-tab { padding: 10px 14px; font-size: 12px; }
  .card-grid, .doc-grid, .kpi-grid, .interaction-map, .compliance-grid { grid-template-columns: 1fr; }
  .workflow-steps { flex-direction: column; align-items: center; }
  .wf-arrow { transform: rotate(90deg); }
}
"""


import re as _re

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
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#x27;")


def _css_class(text) -> str:
    """Sanitize a string for use as a CSS class name. Only allow alphanumeric, hyphens, underscores."""
    if not text or not isinstance(text, str):
        return "activity"
    return _re.sub(r'[^a-zA-Z0-9_-]', '', text)[:30]


def _esc_id(text) -> str:
    """Sanitize a string for use as an HTML id or filename prefix. Only allow alphanumeric, hyphens, underscores."""
    if not text or not isinstance(text, str):
        return "item"
    return _re.sub(r'[^a-zA-Z0-9_-]', '', text)[:50]


# ─── Master Blueprint Renderer ────────────────────────────────────────


def render_master_blueprint(data: dict) -> str:
    """Render the master service blueprint (stages x roles grid)."""
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
    header_cells = f'<div class="corner-cell">Roles / Stages</div>'
    for s in stages:
        sid = _esc(str(s.get("id", "")))
        sname = _esc(s.get("name", ""))
        sicon = _esc(s.get("icon", ""))
        header_cells += f'''<div class="stage-header">
            <div class="stage-num">{sid}</div>
            <div>{sicon}</div>
            <div>{sname}</div>
        </div>'''

    # Data rows
    data_rows = ""
    for r in roles:
        rid = _esc_id(r.get("id", ""))
        rname = _esc(r.get("name", ""))
        ricon = _esc(r.get("icon", ""))
        has_file = rid != "client"
        link_start = f'<a href="{rid}-blueprint.html" target="_blank" style="color:inherit;text-decoration:none;">' if has_file else ""
        link_end = "</a>" if has_file else ""
        data_rows += f'<div class="role-label">{link_start}{ricon} {rname}{link_end}</div>'

        for s in stages:
            sid = _esc(str(s.get("id", "")))
            key = f"{rid}-{sid}"
            items = matrix.get(key, [])
            cards = ""
            for item in items:
                itype = _css_class(item.get("type", "activity"))
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
        rid = _esc_id(r.get("id", ""))
        rname = _esc(r.get("name", ""))
        ricon = _esc(r.get("icon", ""))
        hub_cards += f'''<a href="{rid}-blueprint.html" target="_blank" class="hub-card">
            <div style="font-size:28px;margin-bottom:10px;">{ricon}</div>
            <div style="font-size:14px;font-weight:700;color:var(--text);margin-bottom:4px;">{rname}</div>
            <div style="font-size:11px;color:var(--text-muted);font-family:monospace;margin-bottom:8px;">{rid}-blueprint.html</div>
            <div style="font-size:12px;color:var(--text-secondary);line-height:1.5;">Detailed department blueprint with daily timeline, workflows, documents, KPIs</div>
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
  background: var(--surface); border-radius: var(--radius); padding: 24px; box-shadow: var(--shadow-sm);
  border: 1px solid var(--border); cursor: pointer;
  transition: all 0.2s; text-decoration: none; color: inherit; display: block;
}}
.hub-card:hover {{ border-color: var(--brand); box-shadow: var(--shadow); transform: translateY(-2px); }}
</style>
</head>
<body>

<header class="main-header">
  <div class="header-left">
    <h1>{company}</h1>
    <div class="subtitle">{industry} &middot; {num_roles} Roles &middot; {num_stages} Stages &middot; Complete Process Map</div>
  </div>
  <div class="header-right">
    <span>Blueprint</span>
    <div style="margin-top:8px;">
      <button class="ctrl-btn" onclick="toggleView()" id="viewToggle">Department Hub</button>
    </div>
  </div>
</header>

<div class="legend-bar">
  <span style="font-size:12px;font-weight:600;color:var(--text);margin-right:8px;">Legend</span>
  <div class="legend-item"><div class="legend-swatch activity"></div> Activity</div>
  <div class="legend-item"><div class="legend-swatch document"></div> Document</div>
  <div class="legend-item"><div class="legend-swatch approval"></div> Approval Gate</div>
  <div class="legend-item"><div class="legend-swatch critical"></div> Critical Gate</div>
  <div class="legend-item"><div class="legend-swatch handover"></div> Handover Point</div>
  <div class="legend-item" style="margin-left:auto;color:var(--text-muted);font-size:11px;">Click any cell to expand details</div>
</div>

<div class="controls-bar">
  <button class="ctrl-btn" onclick="expandAll()">Expand All</button>
  <button class="ctrl-btn" onclick="collapseAll()">Collapse All</button>
  <button class="ctrl-btn" onclick="window.print()">Print / PDF</button>
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
            resp_html = f'<div style="font-size:12px;color:var(--text-secondary);margin-top:8px;padding-top:8px;border-top:1px solid var(--border);line-height:1.5;">{responsibilities}</div>'
        team_html += f'''<div class="metric-card">
            <h4>{role}</h4>
            <div class="value">{count}</div>
            <div class="detail">Reports to: {reports}</div>
            {resp_html}
        </div>'''

    head_role = _esc(data.get("head_role", ""))
    head_html = f'<div style="font-size:13px;color:var(--text);margin-bottom:16px;font-weight:600;">Department Head: {head_role}</div>' if head_role else ""

    sections.append(f'''<div class="section active" id="sec-0">
        <div class="section-title">{dept} — Overview</div>
        <div class="section-desc">{mission}</div>
        {head_html}
        <h3 style="font-size:15px;font-weight:600;color:var(--text);margin-bottom:12px;">Team Structure</h3>
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
            aicon = _esc(act.get("icon", ""))
            atitle = _esc(act.get("title", ""))
            adesc = _esc(act.get("description", ""))
            tags_html = ""
            for tag in act.get("tags", []):
                tag_str = tag if isinstance(tag, str) else str(tag)
                tag_class = _css_class(tag_str.lower().split()[0] if tag_str else "system")
                if tag_class not in ("doc", "system", "critical", "approval", "handover"):
                    tag_class = "system"
                tags_html += f'<span class="tag {tag_class}">{_esc(tag_str).upper()}</span>'
            acts_html += f'''<div class="activity-item">
                <div class="act-icon {_css_class(color)}">{aicon}</div>
                <div class="act-content">
                    <h4>{atitle}</h4>
                    <p>{adesc}</p>
                    <div>{tags_html}</div>
                </div>
            </div>'''

        timeline_html += f'''<div class="time-block">
            <div class="time-marker {_css_class(color)}">{time.split(":")[0] if ":" in time else time[:3]}</div>
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
        target_badge = f'<span style="font-size:11px;background:var(--amber-light);color:var(--amber);padding:4px 12px;border-radius:100px;font-weight:600;">Target: {wf_target}</span>' if wf_target else ""

        # Visual flow (horizontal steps)
        flow_html = ""
        for j, step in enumerate(wf.get("steps", [])):
            stitle = _esc(step.get("title", ""))
            srole = _esc(step.get("role", ""))
            scolor = _css_class(step.get("color", "blue"))
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
            scolor = _css_class(step.get("color", "blue"))
            extras = ""
            if sdocs:
                extras += f'<div style="margin-top:4px;"><span class="tag doc">DOC</span> {sdocs}</div>'
            if scriteria:
                extras += f'<div style="margin-top:4px;"><span class="tag approval">DECISION</span> {scriteria}</div>'
            detail_rows += f'''<tr>
                <td style="font-weight:600;white-space:nowrap;vertical-align:top;">{j+1}. {stitle}</td>
                <td style="line-height:1.5;">{sdesc}{extras}</td>
                <td style="white-space:nowrap;vertical-align:top;">{srole}</td>
                <td style="white-space:nowrap;vertical-align:top;color:var(--amber);font-weight:600;">{stime}</td>
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
            fields_display = '<div style="font-size:11px;margin-top:8px;padding:8px 10px;background:var(--bg);border-radius:6px;">'
            fields_display += '<strong style="color:var(--text);display:block;margin-bottom:4px;font-size:10px;text-transform:uppercase;letter-spacing:0.3px;">Fields</strong>'
            fields_display += '<div style="display:flex;flex-wrap:wrap;gap:4px;">'
            for fi in field_items:
                fields_display += f'<span style="background:var(--surface);border:1px solid var(--border);padding:2px 6px;border-radius:4px;font-size:10px;color:var(--text-secondary);">{_esc(fi)}</span>'
            fields_display += '</div></div>'
        else:
            fields_display = f'<div style="font-size:11px;margin-top:8px;padding:6px 10px;background:var(--bg);border-radius:6px;"><strong style="color:var(--text);font-size:10px;">Fields:</strong> {dfields}</div>'

        meta_badges = f'<span class="doc-freq">{dfreq}</span>'
        if dformat:
            meta_badges += f' <span style="font-size:10px;background:var(--purple-light);color:var(--purple);padding:3px 10px;border-radius:100px;display:inline-block;margin-top:6px;font-weight:600;">{dformat}</span>'
        if dretention:
            meta_badges += f' <span style="font-size:10px;background:var(--amber-light);color:var(--amber);padding:3px 10px;border-radius:100px;display:inline-block;margin-top:6px;font-weight:600;">Retain: {dretention}</span>'

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
        kcolor = _css_class(kpi.get("color", kpi_colors[i % len(kpi_colors)]))
        extras = ""
        if kmeasure:
            extras += f'<div style="font-size:11px;color:var(--text-secondary);margin-top:8px;padding-top:8px;border-top:1px solid var(--border);"><strong>How:</strong> {kmeasure}</div>'
        if kaccount:
            extras += f'<div style="font-size:11px;color:var(--text);margin-top:4px;font-weight:600;">Owner: {kaccount}</div>'
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
    esc_colors = ["#10B981", "#F59E0B", "#EF4444", "#8B5CF6"]
    esc_levels = ["level-1", "level-2", "level-3", "level-4"]
    for i, esc in enumerate(data.get("escalation_matrix", [])):
        elevel = esc.get("level", i + 1)
        etitle = _esc(esc.get("title", f"Level {elevel}"))
        edesc = _esc(esc.get("description", ""))
        etrigger = _esc(esc.get("trigger", ""))
        etime = _esc(esc.get("response_time", ""))
        eresolution = _esc(esc.get("resolution_time", ""))
        eauth = _esc(esc.get("authority", ""))
        ecolor = esc_colors[min(i, len(esc_colors) - 1)]
        elevel_class = esc_levels[min(i, len(esc_levels) - 1)]

        trigger_html = f'<div style="font-size:12px;margin-top:10px;padding:10px 12px;background:var(--amber-light);border-radius:8px;border:1px solid var(--amber-card);"><strong style="color:var(--amber);">Trigger:</strong> {etrigger}</div>' if etrigger else ""

        actions_html = ""
        for act in esc.get("actions", []):
            actions_html += f'<div style="font-size:12px;color:var(--text);margin-top:3px;padding-left:14px;">&#8226; {_esc(act)}</div>'
        if actions_html:
            actions_html = f'<div style="margin-top:10px;"><strong style="font-size:12px;color:var(--text);">Actions:</strong>{actions_html}</div>'

        examples_html = ""
        for ex in esc.get("examples", []):
            examples_html += f'<div style="font-size:12px;color:var(--text-secondary);margin-top:3px;padding-left:14px;">&#8226; {_esc(ex)}</div>'
        if examples_html:
            examples_html = f'<div style="margin-top:10px;"><strong style="font-size:12px;color:var(--text);">Examples:</strong>{examples_html}</div>'

        time_display = f'<span style="color:var(--amber);font-weight:600;">Response: {etime}</span>'
        if eresolution:
            time_display += f' <span style="color:var(--text-muted);">&middot;</span> <span style="color:var(--green);font-weight:600;">Resolution: {eresolution}</span>'

        esc_html += f'''<div class="esc-card {elevel_class}">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;padding-left:8px;">
                <div>
                    <span style="background:{ecolor};display:inline-block;padding:3px 12px;border-radius:100px;font-size:11px;font-weight:700;color:#fff;">Level {elevel}</span>
                    <span style="font-size:14px;font-weight:700;color:var(--text);margin-left:10px;">{etitle}</span>
                </div>
                <div style="font-size:12px;">{time_display}</div>
            </div>
            <div style="font-size:13px;color:var(--text-secondary);margin-top:10px;line-height:1.5;padding-left:8px;">{edesc}</div>
            <div style="padding-left:8px;">
                {trigger_html}
                <div style="font-size:12px;color:var(--text);margin-top:10px;font-weight:600;">Authority: {eauth}</div>
                {actions_html}
                {examples_html}
            </div>
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
            extras += f'<div style="font-size:11px;color:var(--text);margin-top:8px;font-weight:600;">Responsible: {cresp}</div>'
        if cdocs:
            extras += f'<div style="font-size:11px;color:var(--text-secondary);margin-top:4px;padding:6px 8px;background:var(--bg);border-radius:6px;"><strong>Records:</strong> {cdocs}</div>'
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
  <div class="header-left">
    <div class="breadcrumb">
      <a href="service-blueprint.html">Master Blueprint</a>
      <span style="margin:0 6px;color:var(--text-muted);">/</span>
      <span>{dept}</span>
    </div>
    <h1>{dept}</h1>
    <div class="subtitle">{company} &middot; Department Blueprint</div>
  </div>
  <div class="header-right">Blueprint</div>
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
    color_map = {"blue": "--brand", "green": "--green", "orange": "--amber", "red": "--red",
                 "purple": "--purple", "teal": "--teal"}
    for cat, cat_terms in sorted(categories.items()):
        color = cat_colors.get(cat, "blue")
        css_var = color_map.get(color, "--brand")
        glossary_html += f'<h3 style="font-size:14px;font-weight:700;color:var(--text);margin:24px 0 10px;padding-bottom:8px;border-bottom:2px solid var({css_var});">{_esc(cat)} ({len(cat_terms)} terms)</h3>'
        glossary_html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:10px;margin-bottom:16px;">'
        for t in sorted(cat_terms, key=lambda x: x.get("term", "")):
            term = _esc(t.get("term", ""))
            full_form = _esc(t.get("full_form", ""))
            definition = _esc(t.get("definition", ""))
            abbr_html = f'<div style="font-size:11px;color:var({css_var});font-weight:600;">{full_form}</div>' if full_form and full_form != term else ""
            glossary_html += f'''<div style="background:var(--surface);border-radius:8px;padding:12px 14px;box-shadow:var(--shadow-sm);border:1px solid var(--border);position:relative;overflow:hidden;">
                <div style="position:absolute;top:0;left:0;bottom:0;width:3px;background:var({css_var});"></div>
                <div style="padding-left:4px;">
                    <div style="font-size:13px;font-weight:700;color:var(--text);">{term}</div>
                    {abbr_html}
                    <div style="font-size:12px;color:var(--text-secondary);margin-top:4px;line-height:1.5;">{definition}</div>
                </div>
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
        dept_badges = " ".join(f'<span style="font-size:10px;background:var(--brand-light);color:var(--brand);padding:3px 10px;border-radius:100px;font-weight:600;">{_esc(d)}</span>' for d in depts)
        steps = proc.get("key_steps", [])
        if isinstance(steps, str):
            steps = [steps]
        steps_html = ""
        for j, step in enumerate(steps):
            steps_html += f'<div style="font-size:12px;padding:3px 0;color:var(--text);">{j+1}. {_esc(step)}</div>'

        xdept_html += f'''<div class="workflow-container">
            <div class="workflow-title">{pname}</div>
            <div style="font-size:13px;color:var(--text-secondary);margin-bottom:10px;">{pdesc}</div>
            <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:10px;">
                <div style="font-size:11px;"><strong>Trigger:</strong> {ptrigger}</div>
                <div style="font-size:11px;"><strong>Frequency:</strong> {pfreq}</div>
                <div style="font-size:11px;"><strong>Output:</strong> {poutput}</div>
            </div>
            <div style="margin-bottom:10px;">{dept_badges}</div>
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
        pol_html += f'''<div class="doc-card" style="overflow:hidden;">
            <div style="position:absolute;top:0;left:0;right:0;height:3px;background:var(--brand);"></div>
            <h4>{pname}</h4>
            <span style="font-size:10px;background:var(--brand-light);color:var(--brand);padding:3px 10px;border-radius:100px;display:inline-block;font-weight:600;margin-bottom:6px;">Scope: {pscope}</span>
            <div class="doc-desc">{pdesc}</div>
            <div style="font-size:11px;color:var(--text);margin-top:8px;"><strong>Enforcement:</strong> {penforce}</div>
            <div style="font-size:11px;color:var(--red);margin-top:4px;"><strong>Violation:</strong> {pconseq}</div>
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
        tech_html += f'<h3 style="font-size:14px;font-weight:700;color:var(--text);margin:20px 0 10px;">{_esc(cat)}</h3>'
        tech_html += '<table class="data-table"><thead><tr><th>System</th><th>Purpose</th><th>Users</th><th>Integrations</th><th>Status</th></tr></thead><tbody>'
        for t in items:
            status = _esc(t.get("status", ""))
            status_color = {"Current": "var(--green)", "Planned": "var(--amber)", "Recommended": "var(--brand)"}.get(status, "var(--text-secondary)")
            tech_html += f'''<tr>
                <td style="font-weight:600;">{_esc(t.get("system", ""))}</td>
                <td>{_esc(t.get("purpose", ""))}</td>
                <td>{_esc(t.get("users", ""))}</td>
                <td style="font-size:12px;">{_esc(t.get("integration_points", ""))}</td>
                <td><span style="color:{status_color};font-weight:600;font-size:12px;">{status}</span></td>
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
    risk_colors = {"High": "var(--red)", "Medium": "var(--amber)", "Low": "var(--green)"}
    for r in data.get("risk_register", []):
        likelihood = _esc(r.get("likelihood", ""))
        impact = _esc(r.get("impact", ""))
        lcolor = risk_colors.get(likelihood, "var(--text-secondary)")
        icolor = risk_colors.get(impact, "var(--text-secondary)")
        risk_html += f'''<tr>
            <td style="font-weight:600;">{_esc(r.get("risk", ""))}</td>
            <td><span style="font-size:10px;background:var(--brand-light);color:var(--brand);padding:3px 10px;border-radius:100px;font-weight:600;">{_esc(r.get("category", ""))}</span></td>
            <td style="text-align:center;"><span style="color:{lcolor};font-weight:700;">{likelihood}</span></td>
            <td style="text-align:center;"><span style="color:{icolor};font-weight:700;">{impact}</span></td>
            <td style="font-size:12px;">{_esc(r.get("mitigation", ""))}</td>
            <td style="font-size:12px;">{_esc(r.get("contingency", ""))}</td>
            <td style="font-size:12px;white-space:nowrap;">{_esc(r.get("owner", ""))}</td>
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
    freq_css = {"red": "--red", "orange": "--amber", "blue": "--brand", "purple": "--purple", "teal": "--teal"}
    for m in data.get("meeting_cadences", []):
        mfreq = _esc(m.get("frequency", ""))
        fcolor_key = mfreq.split("/")[0].strip() if "/" in mfreq else mfreq
        fcolor = freq_colors.get(fcolor_key, "blue")
        fcss = freq_css.get(fcolor, "--brand")
        # Use card background colors
        card_bg_map = {"red": "--red-light", "orange": "--amber-light", "blue": "--brand-light", "purple": "--purple-light", "teal": "--teal-light"}
        fbg = card_bg_map.get(fcolor, "--brand-light")
        meet_html += f'''<div class="doc-card" style="overflow:hidden;">
            <div style="position:absolute;top:0;left:0;right:0;height:3px;background:var({fcss});"></div>
            <h4>{_esc(m.get("meeting", ""))}</h4>
            <span style="font-size:10px;background:var({fbg});color:var({fcss});padding:3px 10px;border-radius:100px;font-weight:600;">{mfreq}</span>
            <span style="font-size:10px;background:var(--bg);color:var(--text-secondary);padding:3px 10px;border-radius:100px;margin-left:4px;">{_esc(m.get("duration", ""))}</span>
            <div style="font-size:12px;margin-top:8px;"><strong>Participants:</strong> {_esc(m.get("participants", ""))}</div>
            <div style="font-size:12px;margin-top:4px;color:var(--text-secondary);"><strong>Agenda:</strong> {_esc(m.get("agenda", ""))}</div>
            <div style="font-size:11px;margin-top:4px;color:var(--green);"><strong>Output:</strong> {_esc(m.get("output", ""))}</div>
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
        market_html += '<h3 style="font-size:15px;font-weight:700;color:var(--text);margin-bottom:12px;">Customer Segments</h3>'
        market_html += '<div class="card-grid">'
        seg_colors = ["blue", "green", "orange", "purple", "teal", "red"]
        for i, seg in enumerate(segs):
            color = seg_colors[i % len(seg_colors)]
            market_html += f'''<div class="metric-card {color}">
                <h4>{_esc(seg.get("segment", ""))}</h4>
                <div style="font-size:13px;color:var(--text);margin-top:6px;">{_esc(seg.get("description", ""))}</div>
                <div style="font-size:12px;color:var(--text-secondary);margin-top:8px;"><strong>Needs:</strong> {_esc(seg.get("needs", ""))}</div>
                <div style="font-size:12px;color:var(--text-secondary);margin-top:3px;"><strong>Buying Pattern:</strong> {_esc(seg.get("buying_pattern", ""))}</div>
                <div style="font-size:12px;color:var(--text-secondary);margin-top:3px;"><strong>Service Level:</strong> {_esc(seg.get("service_level", ""))}</div>
                <div style="font-size:13px;font-weight:700;color:var(--text);margin-top:8px;">{_esc(seg.get("revenue_share", ""))}</div>
            </div>'''
        market_html += '</div>'

    # Seasonal patterns
    seasons = data.get("seasonal_patterns", [])
    if seasons:
        market_html += '<h3 style="font-size:15px;font-weight:700;color:var(--text);margin:28px 0 12px;">Seasonal Patterns</h3>'
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
        market_html += '<h3 style="font-size:15px;font-weight:700;color:var(--text);margin:28px 0 12px;">Vendor & Partner Relationships</h3>'
        market_html += '<div class="doc-grid">'
        for v in vendors:
            market_html += f'''<div class="doc-card" style="overflow:hidden;">
                <div style="position:absolute;top:0;left:0;right:0;height:3px;background:var(--teal);"></div>
                <h4>{_esc(v.get("vendor_type", ""))}</h4>
                <div class="doc-desc">{_esc(v.get("examples", ""))}</div>
                <div style="font-size:12px;margin-top:6px;"><strong>Relationship:</strong> {_esc(v.get("relationship", ""))}</div>
                <div style="font-size:12px;margin-top:3px;color:var(--text-secondary);"><strong>Terms:</strong> {_esc(v.get("key_terms", ""))}</div>
                <div style="font-size:11px;margin-top:3px;color:var(--brand);"><strong>Management:</strong> {_esc(v.get("management", ""))}</div>
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
        people_html += '<h3 style="font-size:15px;font-weight:700;color:var(--text);margin-bottom:12px;">Career Paths</h3>'
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
                    path_steps += '<span style="color:var(--text-muted);font-weight:400;margin:0 6px;">&rarr;</span>'
                path_steps += f'<span style="background:var(--brand-light);border:1px solid var(--brand);padding:4px 12px;border-radius:6px;font-size:12px;font-weight:600;color:var(--brand);">{_esc(level)}</span>'
            people_html += f'''<div style="background:var(--surface);border-radius:var(--radius);padding:18px;box-shadow:var(--shadow-sm);margin-bottom:12px;border:1px solid var(--border);position:relative;overflow:hidden;">
                <div style="position:absolute;top:0;left:0;right:0;height:3px;background:var(--purple);"></div>
                <div style="font-size:14px;font-weight:700;color:var(--text);margin-bottom:10px;">{track}</div>
                <div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;margin-bottom:10px;">{path_steps}</div>
                <div style="font-size:12px;color:var(--text-secondary);"><strong>Progression:</strong> {progression}</div>
                <div style="font-size:12px;color:var(--text-secondary);margin-top:3px;"><strong>Skills:</strong> {skills}</div>
            </div>'''

    # Insurance
    insurance = data.get("insurance_requirements", [])
    if insurance:
        people_html += '<h3 style="font-size:15px;font-weight:700;color:var(--text);margin:28px 0 12px;">Insurance Requirements</h3>'
        people_html += '<table class="data-table"><thead><tr><th>Type</th><th>Coverage</th><th>Required By</th><th>Typical Value</th></tr></thead><tbody>'
        for ins in insurance:
            people_html += f'''<tr>
                <td style="font-weight:600;">{_esc(ins.get("type", ""))}</td>
                <td>{_esc(ins.get("coverage", ""))}</td>
                <td>{_esc(ins.get("required_by", ""))}</td>
                <td style="font-weight:600;color:var(--text);">{_esc(ins.get("typical_value", ""))}</td>
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
        bench_html += '<h3 style="font-size:15px;font-weight:700;color:var(--text);margin-bottom:12px;">Industry Benchmarks</h3>'
        bench_html += '<div class="kpi-grid">'
        bcolors = ["green", "blue", "orange", "purple", "teal", "red"]
        for i, b in enumerate(benchmarks):
            color = bcolors[i % len(bcolors)]
            bench_html += f'''<div class="kpi-card {color}">
                <div class="kpi-name">{_esc(b.get("metric", ""))}</div>
                <div class="kpi-value">{_esc(b.get("value", ""))}</div>
                <div style="font-size:11px;color:var(--text-secondary);margin-top:6px;">{_esc(b.get("context", ""))}</div>
                <div style="font-size:10px;color:var(--brand);margin-top:4px;">Source: {_esc(b.get("source", ""))}</div>
            </div>'''
        bench_html += '</div>'

    mistakes = data.get("common_mistakes", [])
    if mistakes:
        bench_html += '<h3 style="font-size:15px;font-weight:700;color:var(--text);margin:28px 0 12px;">Common Mistakes to Avoid</h3>'
        for m in mistakes:
            bench_html += f'''<div style="background:var(--surface);border-radius:var(--radius);padding:16px 18px;box-shadow:var(--shadow-sm);margin-bottom:10px;border:1px solid var(--border);position:relative;overflow:hidden;">
                <div style="position:absolute;top:0;left:0;right:0;height:3px;background:var(--red);"></div>
                <div style="font-size:13px;font-weight:600;color:var(--red);">{_esc(m.get("mistake", ""))}</div>
                <div style="font-size:12px;color:var(--text-secondary);margin-top:6px;">
                    <span style="font-size:10px;background:var(--brand-light);padding:3px 10px;border-radius:100px;font-weight:600;color:var(--brand);">{_esc(m.get("department", ""))}</span>
                    <strong style="margin-left:8px;">Impact:</strong> {_esc(m.get("consequence", ""))}
                </div>
                <div style="font-size:12px;color:var(--green);margin-top:6px;"><strong>Prevention:</strong> {_esc(m.get("prevention", ""))}</div>
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
  <div class="header-left">
    <div class="breadcrumb">
      <a href="service-blueprint.html">Master Blueprint</a>
      <span style="margin:0 6px;color:var(--text-muted);">/</span>
      <span>Glossary & Appendix</span>
    </div>
    <h1>Glossary & Appendix</h1>
    <div class="subtitle">{company} &middot; Complete Reference</div>
  </div>
  <div class="header-right">Blueprint</div>
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
