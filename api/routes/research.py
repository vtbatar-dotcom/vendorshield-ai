"""Research mock endpoint.

WARNING: This is a MOCK that returns canned data.
The REAL research agent runs on port 8001.
Use POST localhost:8001/assess for live Claude + Tavily results.
This mock exists only so /docs shows the contract.
"""
from fastapi import APIRouter
from api.models.schemas import ResearchRequest

router = APIRouter(prefix="/api/research", tags=["mock-research"])


@router.post("/assess")
def assess(req: ResearchRequest) -> dict:
    flagged = "acme" in req.vendor_name.lower()
    return {
        "WARNING": "This is a MOCK. Use port 8001 for real results.",
        "vendor_id": req.vendor_id,
        "risk_signals": ["data breach reported 2024"] if flagged else ["no adverse media found"],
        "sentiment_score": -0.4 if flagged else 0.2,
        "news_items": [],
        "sanctions_hits": [],
    }
