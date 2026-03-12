"""Staged Questionnaire — 3 stages, research between each.

Stage 1 (3 Qs): Identity — who are you, what do you do, how big
  → Research: industry SOPs, org structures, process flows
Stage 2 (3 Qs): Operations — departments, journey, challenges
  → Research: compliance, KPIs, documents, benchmarks
Stage 3 (2 Qs): Systems & Goals — tools, growth
  → Compile: master blueprint context
"""

STAGES = {
    1: {
        "name": "Understanding Your Business",
        "description": "Let's understand who you are and what you do.",
        "questions": [
            {
                "key": "company_name",
                "question": "What's the name of your company?",
                "placeholder": "e.g., CoolTech HVAC Solutions",
            },
            {
                "key": "industry_description",
                "question": "Describe your business — what industry, what services, who are your customers?",
                "placeholder": "e.g., We're a commercial HVAC company. We install, repair, and maintain heating/cooling systems for office buildings, hospitals, and retail spaces in the metro area.",
            },
            {
                "key": "scale_and_team",
                "question": "How big is your operation? Give a rough team size and breakdown.",
                "placeholder": "e.g., 35 people — 12 technicians, 4 helpers, 3 sales, 2 estimators, 2 PMs, 1 dispatcher, 2 warehouse, 3 office staff, 1 safety, 1 GM, 2 customer service, 1 HR, 1 IT",
            },
        ],
    },
    2: {
        "name": "Your Operations",
        "description": "Now let's map your actual operations. We've done some research on your industry.",
        "questions": [],  # Generated dynamically after Stage 1 research
    },
    3: {
        "name": "Systems & Goals",
        "description": "Almost done — just need to know your tools and where you're headed.",
        "questions": [
            {
                "key": "tools_and_systems",
                "question": "What tools, software, or systems do you use? (accounting, scheduling, communication, field management — anything)",
                "placeholder": "e.g., QuickBooks, ServiceTitan for dispatch, Google Sheets for scheduling, WhatsApp for field crews, paper timesheets",
            },
            {
                "key": "growth_goals",
                "question": "Where do you want the business to be in 2-3 years? Any specific goals?",
                "placeholder": "e.g., Double revenue, add 2 service vans, expand into building automation, reduce callbacks to under 2%, get ISO certified",
            },
        ],
    },
}


def generate_stage2_questions(research: dict) -> list:
    """Generate Stage 2 questions based on industry research findings."""
    typical_depts = research.get("typical_departments", [])
    typical_stages = research.get("typical_process_stages", [])
    suggested_qs = research.get("suggested_questions", [])

    # Format research findings into the questions
    dept_list = ", ".join(typical_depts[:10]) if typical_depts else "Sales, Operations, Finance, HR"
    stage_list = " → ".join(typical_stages[:10]) if typical_stages else "Enquiry → Assessment → Quote → Execution → Billing"

    questions = [
        {
            "key": "departments_confirm",
            "question": f"Based on our research, businesses like yours typically have these departments:\n\n{dept_list}\n\nDoes this match your setup? Add, remove, or rename any that don't fit.",
            "placeholder": "e.g., Yes, but we don't have a separate Estimating dept — our PMs do that. And add a Quality Control function.",
        },
        {
            "key": "customer_journey",
            "question": f"Here's a typical customer journey for your industry:\n\n{stage_list}\n\nWalk me through YOUR actual process — what happens from first contact to job completion?",
            "placeholder": "e.g., Mostly right, but we add a 'Warranty Period' stage after completion, and our 'Site Survey' often happens before we even send a quote...",
        },
        {
            "key": "key_challenges",
            "question": suggested_qs[0] if suggested_qs else "What are the 2-3 biggest operational headaches in your business right now? Where do things break down?",
            "placeholder": "e.g., Scheduling conflicts between jobs, materials showing up late, invoices going out weeks after the job is done, field crews not filling out safety forms",
        },
    ]

    return questions


def get_total_questions() -> int:
    return 8  # 3 + 3 + 2


def get_stage_for_step(step: int) -> int:
    """Which stage is this step in?"""
    if step < 3:
        return 1
    elif step < 6:
        return 2
    else:
        return 3


def get_question_for_step(step: int, session: dict) -> dict:
    """Get the question for the given step."""
    stage = get_stage_for_step(step)

    if stage == 1:
        return STAGES[1]["questions"][step]
    elif stage == 2:
        # Use dynamically generated questions
        stage2_qs = session.get("stage2_questions", STAGES[2]["questions"])
        idx = step - 3
        if idx < len(stage2_qs):
            return stage2_qs[idx]
        return {"key": f"extra_{step}", "question": "Any other details about your operations?", "placeholder": ""}
    elif stage == 3:
        idx = step - 6
        return STAGES[3]["questions"][idx]


def compile_stage_answers(session: dict, stage: int) -> dict:
    """Get all answers for a specific stage."""
    answers = session.get("answers", {})
    if stage == 1:
        keys = ["company_name", "industry_description", "scale_and_team"]
    elif stage == 2:
        keys = ["departments_confirm", "customer_journey", "key_challenges"]
    elif stage == 3:
        keys = ["tools_and_systems", "growth_goals"]
    else:
        keys = []
    return {k: answers.get(k, "") for k in keys}
