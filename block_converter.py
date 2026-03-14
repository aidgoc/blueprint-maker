# block_converter.py
"""Convert generator JSON output into typed blocks.

IMPORTANT: Data shapes must match the ACTUAL LLM prompt templates in generator.py.
See the Key Data Shape Reference in the plan for exact field names.
"""

from block_types import create_block, generate_block_id


def convert_department_to_blocks(dept: dict) -> list[dict]:
    """Convert a department JSON from generator into a list of blocks."""
    blocks = []
    dept_name = dept.get("department", "Department")

    # Heading
    blocks.append(create_block("heading", {"text": dept_name, "level": 1}))

    # Mission as rich text
    if dept.get("mission"):
        blocks.append(create_block("rich-text", {"html": f"<p><strong>Mission:</strong> {dept['mission']}</p>"}))

    # KPIs -- generator shape: {name, target, unit, description, measurement, accountable, color}
    if dept.get("kpis"):
        normalized = []
        for kpi in dept["kpis"]:
            normalized.append({
                "name": kpi.get("name", ""),
                "value": str(kpi.get("value", kpi.get("target", ""))),  # generator uses "target" not "value"
                "target": str(kpi.get("target", "")),
                "unit": kpi.get("unit", ""),
                "trend": kpi.get("trend", "stable"),
            })
        blocks.append(create_block("kpi-grid", normalized))

    # Team structure -- generator shape: {role, count, reports_to, key_responsibilities (string)}
    if dept.get("team_structure"):
        roles = []
        for member in dept["team_structure"]:
            # key_responsibilities is a string of bullet points, split it
            resp_str = member.get("key_responsibilities", "")
            if isinstance(resp_str, str):
                responsibilities = [r.strip() for r in resp_str.split(",") if r.strip()]
            else:
                responsibilities = resp_str if isinstance(resp_str, list) else []
            roles.append({
                "id": generate_block_id(),
                "title": member.get("role", member.get("title", "")),
                "reports_to": member.get("reports_to", None),
                "responsibilities": responsibilities,
            })
        blocks.append(create_block("org-chart", {"roles": roles}))

    # Daily timeline -- generator shape: {time, block_title, activities: [{title, description, tags, icon}]}
    if dept.get("daily_timeline"):
        timeline_data = []
        for item in dept["daily_timeline"]:
            time_str = item.get("time", "")
            block_title = item.get("block_title", "")
            phase_label = f"{time_str} \u2014 {block_title}" if block_title else time_str

            # Activities is a list of {title, description} objects
            activity_strings = []
            for act in item.get("activities", []):
                if isinstance(act, dict):
                    activity_strings.append(f"{act.get('title', '')}: {act.get('description', '')}")
                elif isinstance(act, str):
                    activity_strings.append(act)

            timeline_data.append({
                "phase": phase_label,
                "duration": "",
                "activities": activity_strings,
            })
        blocks.append(create_block("timeline", timeline_data))

    # Workflows -- generator shape: {title, target_time, steps: [{title, description, role, color, time, documents, decision_criteria}]}
    for workflow in dept.get("workflows", []):
        wf_name = workflow.get("title", workflow.get("name", "Workflow"))
        blocks.append(create_block("heading", {"text": wf_name, "level": 2}))
        steps = []
        for step in workflow.get("steps", []):
            steps.append({
                "id": step.get("id", generate_block_id()),
                "title": step.get("title", step.get("name", "")),
                "description": step.get("description", ""),
                "type": step.get("color", step.get("type", "activity")),  # generator uses "color" as type indicator
                "assignee": step.get("role", step.get("assignee", "")),
            })
        blocks.append(create_block("workflow", {"steps": steps, "connections": []}))

    # Documents -- generator shape: {name, description, fields, frequency, flow, retention, format}
    if dept.get("documents"):
        blocks.append(create_block("heading", {"text": "Documents & Templates", "level": 2}))
        items = []
        for doc in dept["documents"]:
            items.append({
                "text": f"{doc.get('name', '')}: {doc.get('description', '')}",
                "checked": False,
                "priority": "normal",
            })
        blocks.append(create_block("checklist", items))

    # Interactions -- generator shape: [{department, inbound: [str], outbound: [str]}]
    # NOTE: This is a LIST of department objects. inbound/outbound contain plain strings, not dicts.
    if dept.get("interactions"):
        nodes = [{"id": "self", "label": dept_name, "type": "center"}]
        edges = []
        node_ids = {"self"}

        for interaction in dept["interactions"]:
            other_dept = interaction.get("department", "Unknown")
            node_id = other_dept.lower().replace(" ", "_")
            if node_id not in node_ids:
                nodes.append({"id": node_id, "label": other_dept, "type": "external"})
                node_ids.add(node_id)

            # inbound is a list of strings like "Receives daily stock reorder alerts..."
            for flow_desc in interaction.get("inbound", []):
                label = flow_desc[:80] + "..." if len(flow_desc) > 80 else flow_desc
                edges.append({"from": node_id, "to": "self", "label": label})

            # outbound is a list of strings
            for flow_desc in interaction.get("outbound", []):
                label = flow_desc[:80] + "..." if len(flow_desc) > 80 else flow_desc
                edges.append({"from": "self", "to": node_id, "label": label})

        blocks.append(create_block("flow-diagram", {"nodes": nodes, "edges": edges}))

    # Escalation matrix -- generator shape: {level, title, trigger, description, response_time, resolution_time, authority, actions, examples}
    if dept.get("escalation_matrix"):
        blocks.append(create_block("heading", {"text": "Escalation Matrix", "level": 2}))
        columns = ["Level", "Title", "Trigger", "Response Time", "Authority", "Actions"]
        rows = []
        for esc in dept["escalation_matrix"]:
            actions = esc.get("actions", [])
            actions_str = "; ".join(actions) if isinstance(actions, list) else str(actions)
            rows.append([
                str(esc.get("level", "")),
                esc.get("title", ""),
                esc.get("trigger", ""),
                esc.get("response_time", ""),
                esc.get("authority", ""),
                actions_str,
            ])
        blocks.append(create_block("table", {"columns": columns, "rows": rows}))

    # Compliance items -- generator shape: {name, description, frequency, responsible, documentation}
    if dept.get("compliance_items"):
        blocks.append(create_block("heading", {"text": "Compliance Requirements", "level": 2}))
        items = []
        for item in dept["compliance_items"]:
            if isinstance(item, dict):
                text = f"{item.get('name', '')}: {item.get('description', '')}"
            else:
                text = str(item)
            items.append({"text": text, "checked": False, "priority": "high"})
        blocks.append(create_block("checklist", items))

    return blocks


def convert_master_to_blocks(master: dict) -> list[dict]:
    """Convert master blueprint JSON into blocks for the master section."""
    blocks = []
    company = master.get("company_name", "Company")
    blocks.append(create_block("heading", {"text": f"{company} \u2014 Service Blueprint", "level": 1}))

    # Stages as timeline
    if master.get("stages"):
        timeline = [{"phase": s.get("name", ""), "duration": s.get("duration", ""), "activities": []} for s in master["stages"]]
        blocks.append(create_block("timeline", timeline))

    # Matrix as card-grid, grouped by role
    matrix = master.get("matrix", {})
    for role in master.get("roles", []):
        role_id = role.get("id", "")
        cards = []
        for stage in master.get("stages", []):
            stage_id = stage.get("id", "")
            items_data = matrix.get(f"{role_id}-{stage_id}", [])
            items = [item.get("text", "") for item in items_data] if items_data else []
            card_type = items_data[0].get("type", "activity") if items_data else "activity"
            cards.append({"title": stage.get("name", ""), "type": card_type, "items": items})
        blocks.append(create_block("heading", {"text": role.get("name", ""), "level": 2}))
        blocks.append(create_block("card-grid", cards))

    return blocks


def convert_glossary_to_blocks(glossary: dict) -> list[dict]:
    """Convert glossary JSON into blocks.
    NOTE: Generator uses key "glossary" not "terms".
    Shape: [{term, full_form, definition, category}]
    """
    blocks = []
    blocks.append(create_block("heading", {"text": "Glossary", "level": 1}))

    # Generator uses "glossary" key, not "terms"
    terms = glossary.get("glossary", glossary.get("terms", []))
    glossary_data = []
    for term in terms:
        glossary_data.append({
            "term": term.get("term", ""),
            "definition": term.get("definition", ""),
            "related": term.get("related", []),
        })
    if glossary_data:
        blocks.append(create_block("glossary", glossary_data))

    # Additional glossary sections as rich text
    for key in ["cross_department_processes", "general_policies", "technology_landscape",
                "risk_register", "meeting_cadences"]:
        items = glossary.get(key, [])
        if items and isinstance(items, list):
            heading = key.replace("_", " ").title()
            blocks.append(create_block("heading", {"text": heading, "level": 2}))
            html_parts = []
            for item in items:
                if isinstance(item, dict):
                    name = item.get("name", item.get("term", item.get("meeting", item.get("risk", ""))))
                    desc = item.get("description", item.get("definition", item.get("agenda", "")))
                    html_parts.append(f"<p><strong>{name}</strong>: {desc}</p>")
            if html_parts:
                blocks.append(create_block("rich-text", {"html": "\n".join(html_parts)}))

    return blocks
