"""Full pipeline orchestrator.

Single endpoint that runs all 4 agents and returns a complete vendor risk report.
POST /api/assess/full

Flow:
  Research Agent (8001) ─┐
  Compliance Agent (8002) ├─→ Risk Scoring (8000) → Final Report
  Financial Agent (8003) ─┘
"""
from __future__ import annotations
import urllib.request, json, concurrent.futures, os
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/assess", tags=["orchestrator"])

RESEARCH_URL   = "http://localhost:8001/assess"
COMPLIANCE_URL = "http://localhost:8002/assess"
FINANCIAL_URL  = "http://localhost:8003/assess"
RISK_URL       = "http://localhost:8000/api/risk/score"


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


def http_post(url: str, data: dict, timeout: int = 60) -> dict:
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
    print("  [1/3] Research Agent starting...")
    result = http_post(RESEARCH_URL, {
        "vendor_id": req.vendor_id,
        "vendor_name": req.vendor_name,
        "vendor_domain": req.vendor_domain
    })
    print("  [1/3] Research Agent done.")
    return result


def run_compliance(req: FullAssessRequest) -> dict:
    print("  [2/3] Compliance Agent starting...")
    result = http_post(COMPLIANCE_URL, {
        "vendor_id": req.vendor_id,
        "vendor_name": req.vendor_name,
        "tier": req.tier,
        "certifications": [c.model_dump() for c in req.certifications],
        "markets": req.markets
    })
    print("  [2/3] Compliance Agent done.")
    return result


def run_financial(req: FullAssessRequest) -> dict:
    print("  [3/3] Financial Agent starting...")
    result = http_post(FINANCIAL_URL, {
        "vendor_id": req.vendor_id,
        "vendor_name": req.vendor_name,
        "duns_number": req.duns_number
    })
    print("  [3/3] Financial Agent done.")
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

    # Run all 3 agents in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        f_research    = executor.submit(run_research, req)
        f_compliance  = executor.submit(run_compliance, req)
        f_financial   = executor.submit(run_financial, req)

        research   = f_research.result()
        compliance = f_compliance.result()
        financial  = f_financial.result()

    print("All agents complete. Running risk scoring...")

    # Build compliance gaps list
    compliance_gaps = []
    if "gaps" in compliance:
        compliance_gaps = [
            g["certification"] + ": " + g["status"]
            for g in compliance.get("gaps", [])
        ]

    # Run risk scoring with all signals combined
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

    print(f"Assessment complete. Score: {risk.get('overall_score')}/100")

    # Build risk summary
    analyst = financial.get("analyst_notes", "")
    comp_summary = compliance.get("risk_summary", "")
    top_signals = research.get("risk_signals", [])[:2]
    summary_parts = []
    if top_signals:
        summary_parts.append("Key risks: " + "; ".join(top_signals[:2]))
    if comp_summary:
        summary_parts.append(comp_summary[:200])
    if analyst:
        summary_parts.append(analyst[:200])
    risk_summary = " | ".join(summary_parts)

    dims = risk.get("dimension_scores", {})

    return FullAssessResponse(
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
