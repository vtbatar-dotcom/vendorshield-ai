"""Risk Scoring Agent — real weighted model.

Weights: Security 30%, Compliance 25%, Financial 20%, Operational 15%, ESG 10%
"""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/risk", tags=["risk"])

WEIGHTS = {"security": 0.30, "compliance": 0.25, "financial": 0.20, "operational": 0.15, "esg": 0.10}

SECURITY_SIGNALS = ["breach", "hack", "ransomware", "malware", "vulnerability", "exploit",
    "attack", "cyberattack", "incident", "trojan", "phishing", "credential", "api key", "leaked", "exposed"]
COMPLIANCE_SIGNALS = ["fine", "penalty", "ftc", "gdpr", "hipaa", "coppa", "violation",
    "regulatory", "non-compliant", "lawsuit", "class action", "litigation", "audit",
    "missing", "expired", "soc2", "iso27001", "pci", "dora", "ccpa"]
FINANCIAL_SIGNALS = ["bankrupt", "insolvency", "revenue decline", "loss", "debt",
    "downgrade", "credit risk", "layoff", "restructuring", "fraud"]
OPERATIONAL_SIGNALS = ["outage", "downtime", "disruption", "supply chain", "dependency"]
ESG_SIGNALS = ["discrimination", "harassment", "environmental", "bribery", "corruption", "scandal"]


class NewsItem(BaseModel):
    title: str
    url: str
    published: str
    sentiment: float


class FinancialData(BaseModel):
    vendor_id: str
    credit_score: int
    financial_health: str
    revenue_trend: str
    bankruptcy_risk: float


class RiskRequest(BaseModel):
    vendor_id: str
    research_signals: list[str] = []
    news_items: list[NewsItem] = []
    sentiment_score: float = 0.0
    compliance_gaps: list[str] = []
    financial_data: Optional[FinancialData] = None
    sanctions_hits: list[str] = []


class DimensionScores(BaseModel):
    security: int
    compliance: int
    financial: int
    operational: int
    esg: int


class RiskResponse(BaseModel):
    vendor_id: str
    overall_score: int
    dimension_scores: DimensionScores
    confidence: int
    classification: str
    routing: str
    flags: list[str]


def _signal_score(signals: list[str], keywords: list[str]) -> int:
    combined = " ".join(signals).lower()
    hits = sum(1 for kw in keywords if kw in combined)
    return min(100, hits * 12)


def _sentiment_to_boost(sentiment: float) -> int:
    """Only boost security score for clearly negative sentiment (below -0.3)."""
    if sentiment >= -0.3:
        return 0
    return int(abs(sentiment + 0.3) / 0.7 * 40)


def _classify(score: int) -> str:
    if score <= 25: return "Low"
    if score <= 50: return "Medium"
    if score <= 75: return "High"
    return "Critical"


def _routing(score: int, confidence: int) -> str:
    if score > 75: return "ESCALATE → Risk Committee"
    if score > 50 or confidence < 60: return "HUMAN_REVIEW → Action Center"
    if score > 25: return "AUTO_APPROVE → Enhanced Monitoring"
    return "AUTO_APPROVE → Standard Monitoring"


@router.post("/score", response_model=RiskResponse)
def score(req: RiskRequest) -> RiskResponse:
    all_signals = req.research_signals + req.compliance_gaps
    if req.sanctions_hits:
        all_signals += req.sanctions_hits

    # Security: from signals + sentiment boost (only for clearly negative)
    security = _signal_score(all_signals, SECURITY_SIGNALS)
    security = min(100, security + _sentiment_to_boost(req.sentiment_score))

    # Compliance: signals + direct penalty per gap
    compliance = _signal_score(all_signals, COMPLIANCE_SIGNALS)
    # Each missing/expired cert = +25 points
    gap_penalty = sum(25 for g in req.compliance_gaps
                      if any(s in g.upper() for s in ["MISSING", "EXPIRED", "EXPIRING"]))
    compliance = min(100, compliance + gap_penalty)
    if req.sanctions_hits:
        compliance = min(100, compliance + 40)

    # Financial: from financial_data or signals
    financial = 10
    if req.financial_data:
        financial = int(req.financial_data.bankruptcy_risk * 100)
        if req.financial_data.financial_health in ["weak", "distressed"]:
            financial = min(100, financial + 20)
    signal_financial = _signal_score(all_signals, FINANCIAL_SIGNALS)
    financial = min(100, max(financial, signal_financial))

    operational = max(15, _signal_score(all_signals, OPERATIONAL_SIGNALS))
    esg = max(10, _signal_score(all_signals, ESG_SIGNALS))

    dims = DimensionScores(
        security=security, compliance=compliance,
        financial=financial, operational=operational, esg=esg
    )

    overall = round(
        dims.security * WEIGHTS["security"] +
        dims.compliance * WEIGHTS["compliance"] +
        dims.financial * WEIGHTS["financial"] +
        dims.operational * WEIGHTS["operational"] +
        dims.esg * WEIGHTS["esg"]
    )

    sources = sum([
        bool(req.research_signals),
        bool(req.news_items),
        req.sentiment_score != 0.0,
        bool(req.financial_data),
    ])
    confidence = int(sources / 4 * 100)

    flags = []
    if req.sanctions_hits:
        flags.append("⚠️ SANCTIONS HIT — immediate escalation required")
    if dims.security >= 70:
        flags.append("⚠️ High security risk — breach/attack signals detected")
    if dims.compliance >= 60:
        flags.append("⚠️ Compliance violations detected — review required")
    if confidence < 60:
        flags.append("⚠️ Low confidence — insufficient data")
    if req.sentiment_score <= -0.7:
        flags.append("⚠️ Very negative public sentiment")
    if any("MISSING" in g for g in req.compliance_gaps):
        flags.append("⚠️ Missing required certifications")

    return RiskResponse(
        vendor_id=req.vendor_id,
        overall_score=overall,
        dimension_scores=dims,
        confidence=confidence,
        classification=_classify(overall),
        routing=_routing(overall, confidence),
        flags=flags
    )
