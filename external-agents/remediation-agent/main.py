from __future__ import annotations
import os, json, re
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
load_dotenv(dotenv_path="../../.env")

import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="VendorShield Remediation Agent", version="0.1.0")


class AssessmentInput(BaseModel):
    vendor_id: str
    vendor_name: str
    overall_score: int
    classification: str
    flags: list[str] = []
    risk_signals: list[str] = []
    compliance_gaps: list[str] = []
    financial_health: str = "unknown"
    bankruptcy_risk: float = 0.0
    anomalies: list[str] = []
    tier: str = "High"


class RemediationTask(BaseModel):
    id: str
    priority: str
    category: str
    title: str
    description: str
    owner: str
    deadline_days: int
    deadline_date: str
    success_criteria: str
    status: str = "OPEN"


class RemediationResponse(BaseModel):
    vendor_id: str
    vendor_name: str
    generated_at: str
    decision: str
    tasks: list[RemediationTask]
    total_tasks: int
    critical_tasks: int
    estimated_resolution_days: int
    executive_summary: str


def get_decision(classification: str, score: int, flags: list[str]) -> str:
    if any("SANCTIONS" in f for f in flags):
        return "REJECT"
    if classification == "Critical" or score > 75:
        return "ESCALATE"
    if classification == "High" or score > 50:
        return "CONDITIONAL_APPROVE"
    return "CONDITIONAL_APPROVE"


def build_task(task_id: str, priority: str, category: str, title: str,
               description: str, owner: str, deadline_days: int, success: str) -> RemediationTask:
    deadline = (datetime.utcnow() + timedelta(days=deadline_days)).strftime("%Y-%m-%d")
    return RemediationTask(
        id=task_id,
        priority=priority,
        category=category,
        title=title,
        description=description,
        owner=owner,
        deadline_days=deadline_days,
        deadline_date=deadline,
        success_criteria=success,
        status="OPEN"
    )


def generate_tasks(req: AssessmentInput) -> list[RemediationTask]:
    tasks = []
    task_num = 1

    for gap in req.compliance_gaps:
        cert = gap.split(":")[0].strip()
        status = gap.split(":")[-1].strip() if ":" in gap else "MISSING"
        is_expired = "EXPIRED" in status
        deadline = 30 if is_expired else 90
        priority = "CRITICAL" if is_expired else "HIGH"
        tasks.append(build_task(
            f"REM-{task_num:03d}", priority, "COMPLIANCE",
            f"{'Renew' if is_expired else 'Obtain'} {cert} certification",
            f"{cert} is {status}. {'Immediate renewal required.' if is_expired else 'Obtain certification from accredited body.'}",
            "Vendor Relationship Manager",
            deadline,
            f"Valid {cert} certificate uploaded to vendor portal"
        ))
        task_num += 1

    for signal in req.risk_signals[:3]:
        if any(kw in signal.lower() for kw in ["breach", "hack", "ransomware", "attack"]):
            tasks.append(build_task(
                f"REM-{task_num:03d}", "CRITICAL", "SECURITY",
                "Security incident investigation required",
                "Vendor must provide root cause analysis and remediation report for: " + signal[:150],
                "Security Team",
                14,
                "Written RCA received and reviewed by security team"
            ))
            task_num += 1
            break

    if any(kw in signal.lower() for signal in req.risk_signals for kw in ["lawsuit", "litigation", "class action"]):
        tasks.append(build_task(
            f"REM-{task_num:03d}", "HIGH", "LEGAL",
            "Legal exposure review",
            "Active litigation detected. Legal team must review contractual exposure and indemnification clauses.",
            "Legal Team",
            21,
            "Legal review memo completed and filed"
        ))
        task_num += 1

    if req.financial_health in ["weak", "distressed"]:
        tasks.append(build_task(
            f"REM-{task_num:03d}", "HIGH", "FINANCIAL",
            "Financial stability monitoring",
            "Vendor shows financial distress (health: " + req.financial_health + ", bankruptcy risk: " + str(req.bankruptcy_risk) + "). Implement enhanced financial monitoring.",
            "Procurement Team",
            30,
            "Quarterly financial review process established, escrow or performance bond obtained"
        ))
        task_num += 1

    if req.bankruptcy_risk > 0.3:
        tasks.append(build_task(
            f"REM-{task_num:03d}", "CRITICAL", "FINANCIAL",
            "Business continuity plan required",
            "High bankruptcy risk (" + str(req.bankruptcy_risk) + "). Identify and qualify backup vendors immediately.",
            "Procurement Team",
            14,
            "Alternative vendor shortlist approved by procurement"
        ))
        task_num += 1

    tasks.append(build_task(
        f"REM-{task_num:03d}", "MEDIUM", "GOVERNANCE",
        "Enhanced vendor questionnaire",
        "Vendor must complete enhanced due diligence questionnaire covering all flagged risk areas.",
        "Vendor Relationship Manager",
        14,
        "Completed questionnaire received and reviewed"
    ))
    task_num += 1

    tasks.append(build_task(
        f"REM-{task_num:03d}", "MEDIUM", "MONITORING",
        "Set up continuous monitoring",
        "Configure automated monitoring for news alerts, cert expiry, and financial signals for this vendor.",
        "Risk Operations Team",
        7,
        "Monitoring alerts configured and tested"
    ))

    return tasks


def generate_summary(client: anthropic.Anthropic, req: AssessmentInput,
                     tasks: list[RemediationTask], decision: str) -> str:
    critical = [t for t in tasks if t.priority == "CRITICAL"]
    high = [t for t in tasks if t.priority == "HIGH"]

    task_list = "\n".join([
        t.priority + ": " + t.title + " (due in " + str(t.deadline_days) + " days, owner: " + t.owner + ")"
        for t in tasks[:6]
    ])

    prompt = (
        "You are a risk management advisor writing an executive summary for vendor: " + req.vendor_name + "\n\n"
        "Assessment: score=" + str(req.overall_score) + "/100, classification=" + req.classification + "\n"
        "Decision: " + decision + "\n"
        "Critical tasks: " + str(len(critical)) + ", High tasks: " + str(len(high)) + "\n\n"
        "Remediation tasks:\n" + task_list + "\n\n"
        "Write a 3-sentence executive summary for a risk committee. "
        "Include the decision, the most critical actions required, and the timeline. "
        "Plain text only, no markdown, no bullet points."
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


@app.get("/health")
def health():
    return {"status": "ok", "agent": "remediation", "version": "0.1.0"}


@app.post("/remediate", response_model=RemediationResponse)
def remediate(req: AssessmentInput) -> RemediationResponse:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    decision = get_decision(req.classification, req.overall_score, req.flags)
    tasks = generate_tasks(req)

    print("Generating executive summary for " + req.vendor_name + "...")
    summary = generate_summary(client, req, tasks, decision)

    critical_tasks = sum(1 for t in tasks if t.priority == "CRITICAL")
    max_deadline = max(t.deadline_days for t in tasks) if tasks else 90

    return RemediationResponse(
        vendor_id=req.vendor_id,
        vendor_name=req.vendor_name,
        generated_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        decision=decision,
        tasks=tasks,
        total_tasks=len(tasks),
        critical_tasks=critical_tasks,
        estimated_resolution_days=max_deadline,
        executive_summary=summary
    )
