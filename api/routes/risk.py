"""Risk scoring endpoint.

Unlike the other mocks, this implements the REAL weighted model from the spec,
because it is pure Python and deterministic - which makes it the most reliable
piece to demo. Phase 6 moves this logic into a UiPath Coded Agent.
"""
from fastapi import APIRouter
from api.models.schemas import RiskRequest, RiskResponse, DimensionScores

router = APIRouter(prefix="/api/risk", tags=["risk"])

# Dimension weights from the spec (must sum to 1.0).
WEIGHTS = {
    "security": 0.30,
    "compliance": 0.25,
    "financial": 0.20,
    "operational": 0.15,
    "esg": 0.10,
}


def _classify(score: int) -> str:
    if score <= 25:
        return "Low"
    if score <= 50:
        return "Medium"
    if score <= 75:
        return "High"
    return "Critical"


@router.post("/score", response_model=RiskResponse)
def score(req: RiskRequest) -> RiskResponse:
    # Derive crude per-dimension risk from the inputs we have.
    security = min(100, len(req.research_signals) * 25)
    compliance = min(100, len(req.compliance_gaps) * 30)

    financial = 10
    if req.financial_data:
        financial = int(req.financial_data.bankruptcy_risk * 100)

    operational = 20  # placeholder until operational signals exist
    esg = 15          # placeholder until ESG signals exist

    dims = DimensionScores(
        security=security,
        compliance=compliance,
        financial=financial,
        operational=operational,
        esg=esg,
    )

    overall = round(
        dims.security * WEIGHTS["security"]
        + dims.compliance * WEIGHTS["compliance"]
        + dims.financial * WEIGHTS["financial"]
        + dims.operational * WEIGHTS["operational"]
        + dims.esg * WEIGHTS["esg"]
    )

    # Confidence = share of signal sources that returned data.
    sources_present = sum(
        [bool(req.research_signals), bool(req.compliance_gaps), bool(req.financial_data)]
    )
    confidence = int(sources_present / 3 * 100)

    return RiskResponse(
        vendor_id=req.vendor_id,
        overall_score=overall,
        dimension_scores=dims,
        confidence=confidence,
        classification=_classify(overall),
    )
