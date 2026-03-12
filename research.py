"""Research Engine — subagents that do real web research between question stages.

Architecture:
  After Stage 1 (3 Qs): Industry research — SOPs, org structures, process flows
  After Stage 2 (3 Qs): Deep research — compliance, documents, KPIs, benchmarks
  After Stage 3 (2 Qs): Final synthesis — compile everything into master blueprint data
"""
import json
import asyncio
import httpx

from config import OPENROUTER_API_KEY, PLANNER_MODEL, RENDERER_MODEL


async def call_llm(system: str, prompt: str, model: str = None, max_tokens: int = 4000) -> str:
    """Call OpenRouter."""
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model or RENDERER_MODEL,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def web_search(query: str) -> list[dict]:
    """Search the web via DuckDuckGo HTML (no API key needed)."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
            )
            resp.raise_for_status()
            html = resp.text

            # Extract result snippets from DDG HTML
            results = []
            parts = html.split('class="result__body"')
            for part in parts[1:6]:  # top 5 results
                # Extract title
                title = ""
                if 'class="result__a"' in part:
                    t = part.split('class="result__a"')[1]
                    if ">" in t and "<" in t:
                        title = t.split(">", 1)[1].split("<", 1)[0].strip()

                # Extract snippet
                snippet = ""
                if 'class="result__snippet"' in part:
                    s = part.split('class="result__snippet"')[1]
                    if ">" in s and "<" in s:
                        snippet = s.split(">", 1)[1].split("<", 1)[0].strip()

                # Extract URL
                url = ""
                if 'class="result__url"' in part:
                    u = part.split('class="result__url"')[1]
                    if ">" in u and "<" in u:
                        url = u.split(">", 1)[1].split("<", 1)[0].strip()

                if title or snippet:
                    results.append({"title": title, "snippet": snippet, "url": url})

            return results
    except Exception as e:
        return [{"title": "Search failed", "snippet": str(e), "url": ""}]


async def fetch_url_content(url: str) -> str:
    """Fetch and extract text content from a URL."""
    try:
        if not url.startswith("http"):
            url = "https://" + url
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
            )
            resp.raise_for_status()
            html = resp.text

            # Basic HTML to text
            import re
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:8000]  # first 8K chars
    except Exception as e:
        return f"[Failed to fetch: {e}]"


# ─── Research Agents ──────────────────────────────────────────────────

async def research_industry(industry: str, services: str, company: str) -> dict:
    """Stage 1 research: Deep industry analysis.
    Runs 4 parallel search queries to understand the industry."""

    searches = await asyncio.gather(
        web_search(f"{industry} business operations process flow SOP"),
        web_search(f"{industry} company departments organizational structure roles"),
        web_search(f"{industry} standard operating procedures workflow"),
        web_search(f"{industry} {services} business model key processes"),
    )

    # Combine all search results
    all_results = []
    for results in searches:
        all_results.extend(results)

    search_context = "\n".join([
        f"- {r['title']}: {r['snippet']}" for r in all_results if r.get('snippet')
    ])

    # Fetch top 2-3 most relevant URLs for deeper content
    urls_to_fetch = []
    for r in all_results:
        if r.get("url") and len(urls_to_fetch) < 3:
            url = r["url"]
            # Skip PDFs, videos, social media
            if not any(x in url.lower() for x in [".pdf", "youtube", "facebook", "twitter", "linkedin", "instagram"]):
                urls_to_fetch.append(url)

    fetched_content = []
    if urls_to_fetch:
        fetch_tasks = [fetch_url_content(url) for url in urls_to_fetch]
        fetch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        for url, content in zip(urls_to_fetch, fetch_results):
            if isinstance(content, str) and not content.startswith("[Failed"):
                fetched_content.append(f"[FROM {url}]:\n{content[:3000]}")

    deep_context = "\n\n".join(fetched_content) if fetched_content else ""

    # Now use LLM to synthesize the research into structured findings
    synthesis = await call_llm(
        system="You are an industry research analyst. Synthesize web research into actionable business intelligence. Be specific and factual. Output JSON only.",
        prompt=f"""Based on this research about the "{industry}" industry (company: {company}, services: {services}):

SEARCH RESULTS:
{search_context}

DETAILED CONTENT:
{deep_context[:6000]}

Synthesize into this JSON:
{{
  "industry_overview": "2-3 sentence summary of how this industry typically operates",
  "typical_departments": ["list of 8-12 departments common in this industry"],
  "typical_process_stages": ["list of 8-12 stages from customer contact to job completion"],
  "key_roles": ["list of key job titles/roles"],
  "common_documents": ["list of 10-15 documents/forms typically used"],
  "industry_terminology": ["list of 10-15 industry-specific terms and their meanings"],
  "typical_pain_points": ["list of 5-8 common operational challenges"],
  "suggested_questions": ["3 specific follow-up questions to ask the user based on what we learned"]
}}

Be SPECIFIC to {industry}, not generic business advice. Use real terminology found in the research.""",
        model=PLANNER_MODEL,
        max_tokens=4000,
    )

    try:
        return json.loads(synthesis.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        # Try to extract JSON from response
        if "```json" in synthesis:
            synthesis = synthesis.split("```json")[1].split("```")[0]
        elif "```" in synthesis:
            synthesis = synthesis.split("```")[1].split("```")[0]
        return json.loads(synthesis.strip())


async def research_compliance_and_kpis(industry: str, services: str, departments: list, region: str) -> dict:
    """Stage 2 research: Compliance, regulations, KPIs, document templates."""

    searches = await asyncio.gather(
        web_search(f"{industry} regulatory compliance requirements {region}"),
        web_search(f"{industry} KPI metrics benchmarks performance"),
        web_search(f"{industry} safety standards certifications required"),
        web_search(f"{industry} document templates forms checklists"),
        web_search(f"{industry} escalation matrix incident management"),
    )

    all_results = []
    for results in searches:
        all_results.extend(results)

    search_context = "\n".join([
        f"- {r['title']}: {r['snippet']}" for r in all_results if r.get('snippet')
    ])

    # Fetch top URLs
    urls_to_fetch = []
    for r in all_results:
        if r.get("url") and len(urls_to_fetch) < 3:
            url = r["url"]
            if not any(x in url.lower() for x in [".pdf", "youtube", "facebook", "twitter"]):
                urls_to_fetch.append(url)

    fetched_content = []
    if urls_to_fetch:
        fetch_tasks = [fetch_url_content(url) for url in urls_to_fetch]
        fetch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        for url, content in zip(urls_to_fetch, fetch_results):
            if isinstance(content, str) and not content.startswith("[Failed"):
                fetched_content.append(f"[FROM {url}]:\n{content[:3000]}")

    deep_context = "\n\n".join(fetched_content) if fetched_content else ""

    synthesis = await call_llm(
        system="You are a compliance and operations research analyst. Extract specific, factual regulatory and operational data. Output JSON only.",
        prompt=f"""Research findings for "{industry}" industry:

SEARCH RESULTS:
{search_context}

DETAILED CONTENT:
{deep_context[:6000]}

DEPARTMENTS: {', '.join(departments)}

Extract into this JSON:
{{
  "compliance_requirements": [
    {{"name": "Standard/Regulation Name", "description": "What it requires", "applies_to": "Which department", "frequency": "How often to check"}}
  ],
  "industry_kpis": [
    {{"name": "KPI Name", "target": "Industry benchmark value", "unit": "%/days/count", "department": "Which dept", "description": "What it measures"}}
  ],
  "safety_standards": [
    {{"name": "Standard", "description": "What it covers"}}
  ],
  "document_templates": [
    {{"name": "Document", "purpose": "Why it exists", "key_fields": "field1, field2, field3", "department": "Who owns it", "frequency": "When created"}}
  ],
  "escalation_patterns": [
    {{"scenario": "What goes wrong", "levels": ["Level 1: action", "Level 2: action", "Level 3: action"]}}
  ],
  "workflow_patterns": [
    {{"name": "Workflow name", "trigger": "What starts it", "steps": ["step1", "step2", "step3"], "department": "Primary dept"}}
  ]
}}

Use REAL regulation names, REAL standards, REAL KPI benchmarks from the research. Not generic placeholders.""",
        model=PLANNER_MODEL,
        max_tokens=6000,
    )

    try:
        return json.loads(synthesis.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        if "```json" in synthesis:
            synthesis = synthesis.split("```json")[1].split("```")[0]
        elif "```" in synthesis:
            synthesis = synthesis.split("```")[1].split("```")[0]
        return json.loads(synthesis.strip())


async def compile_master_context(
    stage1_answers: dict,
    stage1_research: dict,
    stage2_answers: dict,
    stage2_research: dict,
    stage3_answers: dict,
) -> str:
    """Compile all research and answers into a comprehensive context document
    that will drive the blueprint generation."""

    context = f"""# BUSINESS BLUEPRINT CONTEXT
## Compiled from user interviews and industry research

### Company Profile
- Company: {stage1_answers.get('company_name', 'Unknown')}
- Industry: {stage1_answers.get('industry_description', 'Unknown')}
- Scale: {stage1_answers.get('scale_and_team', 'Unknown')}

### Industry Research Findings
{json.dumps(stage1_research, indent=2)}

### Operational Details (from user)
- Departments: {stage2_answers.get('departments_confirm', 'Not specified')}
- Customer Journey: {stage2_answers.get('customer_journey', 'Not specified')}
- Key Challenges: {stage2_answers.get('key_challenges', 'Not specified')}

### Compliance & Standards Research
{json.dumps(stage2_research, indent=2)}

### Final Details (from user)
- Tools & Systems: {stage3_answers.get('tools_and_systems', 'Not specified')}
- Growth Goals: {stage3_answers.get('growth_goals', 'Not specified')}
"""
    return context
