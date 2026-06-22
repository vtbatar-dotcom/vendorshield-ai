"""Financial agent endpoint (mock).

Phase 1: deterministic financial health. Phase 5 replaces with a real CrewAI
crew calling the Dun & Bradstreet API.
"""
from fastapi import APIRouter
from api.models.schemas import FinancialRequest, FinancialResponse

router = APIRouter(prefix="/api/financial", tags=["financial"])


@router.post("/assess", response_model=FinancialResponse)
def assess(req: FinancialRequest) -> FinancialResponse:
    weak = "acme" in req.vendor_name.lower()
    return FinancialResponse(
        vendor_id=req.vendor_id,
        credit_score=48 if weak else 82,
        financial_health="weak" if weak else "stable",
        revenue_trend="declining" if weak else "growing",
        bankruptcy_risk=0.35 if weak else 0.05,
    )
