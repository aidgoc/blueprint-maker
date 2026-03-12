"""End-to-end test of the blueprint generation pipeline."""
import asyncio
import json
import sys
sys.path.insert(0, '.')

from questionnaire import QUESTIONS, compile_business_profile
from generator import generate_blueprint_kit

async def main():
    # Simulate a completed questionnaire for an HVAC company
    session = {
        "business_description": "HVAC installation and service company",
        "answers": {
            "company_name": "CoolTech HVAC Solutions",
            "industry": "We install, repair and maintain HVAC systems for commercial buildings, offices and retail. We serve the greater metro area.",
            "services": "1) New HVAC installation 2) Preventive maintenance contracts 3) Emergency repairs 4) Duct cleaning 5) Energy audits",
            "team_size": "35 people - 2 PMs, 12 technicians, 4 helpers, 3 sales, 2 estimators, 1 dispatcher, 2 warehouse, 3 accounting, 2 customer service, 1 HR, 1 GM, 1 safety, 1 IT",
            "departments": "Sales, Estimating, Operations/Dispatch, Field Service, Warehouse/Procurement, Accounting, HR, Customer Service, Safety",
            "customer_journey": "Customer calls -> qualify lead -> site survey -> estimate/proposal -> approval -> plan job & order materials -> dispatch crew -> install/service -> inspection -> invoice -> payment -> follow up for maintenance contract",
            "documents": "Proposals, work orders, POs, material requisitions, timesheets, daily job reports, inspection checklists, permits, change orders, invoices, service reports, maintenance schedules, safety toolbox talk sheets",
            "pain_points": "Scheduling conflicts, delayed procurement, poor office-field communication, warranty tracking, maintenance contract renewals, inventory accuracy",
            "compliance": "EPA 608 certification, OSHA safety, state mechanical contractor license, building permits, ASHRAE standards, NFPA fire codes",
            "tools_software": "QuickBooks, ServiceTitan, Google Sheets, WhatsApp, paper timesheets",
            "scale_goals": "Double revenue in 3 years, add 2 vans, expand into building automation, reduce callbacks to under 2%",
        },
        "current_step": len(QUESTIONS),
        "status": "ready",
    }

    profile = compile_business_profile(session)
    session["profile"] = profile

    print(f"Company: {profile['company_name']}")
    print(f"Departments: {profile['departments']}")
    print(f"Stages: {profile['stages']}")
    print(f"Services: {profile['services']}")
    print()

    print("Generating blueprint kit...")
    files = await generate_blueprint_kit(profile)

    print(f"\nGenerated {len(files)} files:")
    for f in files:
        print(f"  - {f['name']} ({len(f['content'])} bytes)")

    # Save files to output dir for inspection
    import os
    os.makedirs("output", exist_ok=True)
    for f in files:
        with open(f"output/{f['name']}", "w") as fh:
            fh.write(f["content"])
    print(f"\nFiles saved to output/ directory")

if __name__ == "__main__":
    asyncio.run(main())
