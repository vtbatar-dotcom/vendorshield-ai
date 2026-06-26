"""Financial mock endpoint.

WARNING: This is a MOCK that returns canned data.
The REAL financial agent runs on port 8003.
Use POST localhost:8003/assess for live Claude analyst+reviewer results.
"""
from fastapi import APIRouter
from api.models.schemas import FinancialRequest

router = APIRouter(prefix="/api/financial", tags=["mock-financial"])


@router.post("/assess")
def assess(req: FinancialRequest) -> dict:
    weak = "acme" in req.vendor_name.lower()
    return {
        "WARNING": "This is a MOCK. Use port 8003 for real results.",
        "vendor_id": req.vendor_id,
        "credit_score": 42 if weak else 82,
        "financial_health": "weak" if weak else "stable",
        "revenue_trend": "declining" if weak else "growing",
        "bankruptcy_risk": 0.35 if weak else 0.05,
    }
