"""Risk Scoring Agent - real weighted model.

Accepts output directly from the Research Agent (Phase 2) and computes
a full 5-dimension weighted risk score with confidence and classification.

Weights per spec:
  Security:    30%
  Compliance:  25%
  Financial:   20%
  Operational: 15%
  ESG:         10%
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import re

router = APIRouter(prefix="/api/risk", tags=["risk"])

WEIGHTS = {
    "security":    0.30,
    "compliance":  0.25,
    "financial":   0.20,
    "operational": 0.15,
    "esg":         0.10,
}

# Keywords that map to each risk dimension
SECURITY_SIGNALS = [
    "breach", "hack", "ransomware", "malware", "vulnerability",
    "exploit", "attack", "cyberattack", "incident", "trojan",
    "phishing", "credential", "api key", "leaked", "exposed"
]
COMPLIANCE_SIGNALS = [
    "fine", "penalty", "ftc", "gdpr", "hipaa", "coppa", "violation",
    "regulatory", "non-compliant", "sanction", "doj", "sec filing",
    "audit", "lawsuit", "class action", "litigation"
]
FINANCIAL_SIGNALS = [
    "bankrupt", "insolvency", "revenue decline", "loss", "debt",
    "downgrade", "credit risk", "layoff", "restructuring", "fraud"
]
OPERATIONAL_SIGNALS = [
    "outage", "downtime", "service disruption", "supply chain",
    "third party", "vendor risk", "dependency", "concentration risk"
]
ESG_SIGNALS = [
    "child labor", "discrimination", "harassment", "environmental",
    "carbon", "esg", "diversity", "bribery", "corruption", "scandal"
]


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
    """Score 0-100 based on how many keywords appear in the signals."""
    combined = " ".join(signals).lower()
    hits = sum(1 for kw in keywords if kw in combined)
    # Each hit adds ~12 points, capped at 100
    return min(100, hits * 12)


def _sentiment_to_score(sentiment: float) -> int:
    """Convert sentiment (-1 to 1) to risk score (0 to 100)."""
    # sentiment -1 = max risk 80, sentiment +1 = min risk 5
    return int(((sentiment * -1) + 1) / 2 * 75 + 5)


def _classify(score: int) -> str:
    if score <= 25:
        return "Low"
    if score <= 50:
        return "Medium"
    if score <= 75:
        return "High"
    return "Critical"


def _routing(score: int, confidence: int, tier: str = "High") -> str:
    if score > 75:
        return "ESCALATE → Risk Committee"
    if score > 50 or confidence < 60:
        return "HUMAN_REVIEW → Action Center"
    if score > 25:
        return "AUTO_APPROVE → Enhanced Monitoring"
    return "AUTO_APPROVE → Standard Monitoring"


@router.post("/score", response_model=RiskResponse)
def score(req: RiskRequest) -> RiskResponse:
    all_signals = req.research_signals + req.compliance_gaps
    if req.sanctions_hits:
        all_signals += req.sanctions_hits

    # Compute dimension scores
    security = _signal_score(all_signals, SECURITY_SIGNALS)
    # Boost security score from negative sentiment
    sentiment_boost = _sentiment_to_score(req.sentiment_score)
    security = min(100, int((security + sentiment_boost) / 2))

    compliance = _signal_score(all_signals, COMPLIANCE_SIGNALS)
    if req.sanctions_hits:
        compliance = min(100, compliance + 40)  # Sanctions = major compliance hit

    financial = 15  # default low
    if req.financial_data:
        financial = int(req.financial_data.bankruptcy_risk * 100)
        if req.financial_data.financial_health in ["weak", "distressed"]:
            financial = min(100, financial + 20)
    # Also check signals for financial keywords
    signal_financial = _signal_score(all_signals, FINANCIAL_SIGNALS)
    financial = min(100, max(financial, signal_financial))

    operational = _signal_score(all_signals, OPERATIONAL_SIGNALS)
    operational = max(15, operational)  # floor at 15 (always some operational risk)

    esg = _signal_score(all_signals, ESG_SIGNALS)
    esg = max(10, esg)  # floor at 10

    dims = DimensionScores(
        security=security,
        compliance=compliance,
        financial=financial,
        operational=operational,
        esg=esg
    )

    # Weighted overall score
    overall = round(
        dims.security    * WEIGHTS["security"] +
        dims.compliance  * WEIGHTS["compliance"] +
        dims.financial   * WEIGHTS["financial"] +
        dims.operational * WEIGHTS["operational"] +
        dims.esg         * WEIGHTS["esg"]
    )

    # Confidence = based on data sources present
    sources = sum([
        bool(req.research_signals),
        bool(req.news_items),
        req.sentiment_score != 0.0,
        bool(req.financial_data),
    ])
    confidence = int(sources / 4 * 100)

    # Flags for human reviewer
    flags = []
    if req.sanctions_hits:
        flags.append("⚠️ SANCTIONS HIT — immediate escalation required")
    if dims.security >= 70:
        flags.append("⚠️ High security risk — breach/attack signals detected")
    if dims.compliance >= 60:
        flags.append("⚠️ Compliance violations detected — review required")
    if confidence < 60:
        flags.append("⚠️ Low confidence — insufficient data, request more information")
    if req.sentiment_score <= -0.7:
        flags.append("⚠️ Very negative public sentiment")

    return RiskResponse(
        vendor_id=req.vendor_id,
        overall_score=overall,
        dimension_scores=dims,
        confidence=confidence,
        classification=_classify(overall),
        routing=_routing(overall, confidence),
        flags=flags
    )
