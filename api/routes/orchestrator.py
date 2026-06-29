"""Full pipeline orchestrator.

Agent URLs are env-configurable so they work both under docker-compose
(service names) and under start.sh (localhost).
"""
from __future__ import annotations
import urllib.request, json, concurrent.futures, os
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/assess", tags=["orchestrator"])

# Configurable via env — defaults work for localhost (start.sh)
# For docker-compose set RESEARCH_URL=http://research-agent:8001 etc.
RESEARCH_URL   = os.getenv("RESEARCH_URL",   "http://localhost:8001") + "/assess"
COMPLIANCE_URL = os.getenv("COMPLIANCE_URL", "http://localhost:8002") + "/assess"
FINANCIAL_URL  = os.getenv("FINANCIAL_URL",  "http://localhost:8003") + "/assess"
RISK_URL       = os.getenv("RISK_URL",       "http://localhost:8000") + "/api/risk/score"
STORE_URL      = os.getenv("MAIN_URL",       "http://localhost:8000") + "/api/vendors/{}/store"


class CertItem(BaseModel):
    name: str
    issued: Optional[str] = None
    expiry: Optional[str] = None
    issuer: Optional[str] = None


class FullAssessRequest(BaseModel):
    vendor_id: str
    vendor_name: str
    vendor_domain: Optional[str] = None
    tier: str = "High"
    certifications: list[CertItem] = []
    markets: list[str] = ["US"]
    duns_number: Optional[str] = None


class DimensionScores(BaseModel):
    security: int
    compliance: int
    financial: int
    operational: int
    esg: int


class FullAssessResponse(BaseModel):
    vendor_id: str
    vendor_name: str
    assessed_at: str
    overall_score: int
    classification: str
    routing: str
    confidence: int
    dimension_scores: DimensionScores
    flags: list[str]
    risk_signals: list[str]
    compliance_score: int
    compliance_gaps: list[str]
    financial_health: str
    revenue_trend: str
    bankruptcy_risk: float
    anomalies: list[str]
    risk_summary: str
    next_action: str


def http_post(url: str, data: dict, timeout: int = 90) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def run_research(req: FullAssessRequest) -> dict:
    print("  [1/3] Research Agent...")
    result = http_post(RESEARCH_URL, {
        "vendor_id": req.vendor_id,
        "vendor_name": req.vendor_name,
        "vendor_domain": req.vendor_domain
    })
    print("  [1/3] Research done.")
    return result


def run_compliance(req: FullAssessRequest) -> dict:
    print("  [2/3] Compliance Agent...")
    result = http_post(COMPLIANCE_URL, {
        "vendor_id": req.vendor_id,
        "vendor_name": req.vendor_name,
        "tier": req.tier,
        "certifications": [c.model_dump() for c in req.certifications],
        "markets": req.markets
    })
    print("  [2/3] Compliance done.")
    return result


def run_financial(req: FullAssessRequest) -> dict:
    print("  [3/3] Financial Agent...")
    result = http_post(FINANCIAL_URL, {
        "vendor_id": req.vendor_id,
        "vendor_name": req.vendor_name,
        "duns_number": req.duns_number
    })
    print("  [3/3] Financial done.")
    return result


def next_action(classification: str, routing: str) -> str:
    if "ESCALATE" in routing:
        return "Escalate to Risk Committee within 24 hours"
    if "HUMAN_REVIEW" in routing:
        return "Assign to Risk Analyst for review within 48 hours"
    if classification == "Medium":
        return "Auto-approved with enhanced monitoring — quarterly review"
    return "Auto-approved with standard monitoring — annual review"


@router.post("/full", response_model=FullAssessResponse)
def full_assess(req: FullAssessRequest) -> FullAssessResponse:
    print(f"\nStarting full assessment for {req.vendor_name}...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        f_research   = executor.submit(run_research, req)
        f_compliance = executor.submit(run_compliance, req)
        f_financial  = executor.submit(run_financial, req)
        research   = f_research.result()
        compliance = f_compliance.result()
        financial  = f_financial.result()

    print("All agents done. Scoring...")

    compliance_gaps = [
        g["certification"] + ": " + g["status"]
        for g in compliance.get("gaps", [])
    ]

    risk = http_post(RISK_URL, {
        "vendor_id": req.vendor_id,
        "research_signals": research.get("risk_signals", []),
        "sentiment_score": research.get("sentiment_score", 0.0),
        "news_items": research.get("news_items", []),
        "sanctions_hits": research.get("sanctions_hits", []),
        "compliance_gaps": compliance_gaps,
        "financial_data": {
            "vendor_id": req.vendor_id,
            "credit_score": financial.get("credit_score", 50),
            "financial_health": financial.get("financial_health", "unknown"),
            "revenue_trend": financial.get("revenue_trend", "unknown"),
            "bankruptcy_risk": financial.get("bankruptcy_risk", 0.1)
        }
    })

    dims = risk.get("dimension_scores", {})
    summary_parts = []
    top = research.get("risk_signals", [])[:2]
    if top:
        summary_parts.append("Key risks: " + "; ".join(top[:2]))
    if compliance.get("risk_summary"):
        summary_parts.append(compliance["risk_summary"][:200])
    if financial.get("analyst_notes"):
        summary_parts.append(financial["analyst_notes"][:200])
    risk_summary = " | ".join(summary_parts)

    response = FullAssessResponse(
        vendor_id=req.vendor_id,
        vendor_name=req.vendor_name,
        assessed_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        overall_score=risk.get("overall_score", 0),
        classification=risk.get("classification", "Unknown"),
        routing=risk.get("routing", ""),
        confidence=risk.get("confidence", 0),
        dimension_scores=DimensionScores(
            security=dims.get("security", 0),
            compliance=dims.get("compliance", 0),
            financial=dims.get("financial", 0),
            operational=dims.get("operational", 0),
            esg=dims.get("esg", 0)
        ),
        flags=risk.get("flags", []),
        risk_signals=research.get("risk_signals", []),
        compliance_score=compliance.get("compliance_score", 0),
        compliance_gaps=compliance_gaps,
        financial_health=financial.get("financial_health", "unknown"),
        revenue_trend=financial.get("revenue_trend", "unknown"),
        bankruptcy_risk=financial.get("bankruptcy_risk", 0.0),
        anomalies=financial.get("anomalies", []),
        risk_summary=risk_summary,
        next_action=next_action(
            risk.get("classification", ""),
            risk.get("routing", "")
        )
    )

    # Save to case store
    try:
        http_post(STORE_URL.format(req.vendor_id), {
            "stage": "RiskScoring" if risk.get("overall_score", 0) > 50 else "Decision",
            "overall_score": risk.get("overall_score", 0),
            "classification": risk.get("classification", ""),
            "findings": research.get("risk_signals", [])[:5],
            "decisions": [],
            "sla_status": "on_track"
        }, timeout=5)
    except Exception as e:
        print(f"Case store warning: {e}")

    return response
