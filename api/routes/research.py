"""Research agent endpoint (mock).

Phase 1: returns deterministic OSINT-style signals so the case flow can be
wired and demoed. Phase 3 replaces the body with a real LangChain call.
"""
from fastapi import APIRouter
from api.models.schemas import ResearchRequest, ResearchResponse, NewsItem

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("/assess", response_model=ResearchResponse)
def assess(req: ResearchRequest) -> ResearchResponse:
    # Deterministic mock keyed off the vendor name so demos are repeatable.
    flagged = "acme" in req.vendor_name.lower()
    return ResearchResponse(
        vendor_id=req.vendor_id,
        risk_signals=(
            ["data breach reported 2024", "pending class-action lawsuit"]
            if flagged
            else ["no adverse media found"]
        ),
        sentiment_score=-0.4 if flagged else 0.2,
        news_items=[
            NewsItem(
                title=f"{req.vendor_name} security review",
                url="https://news.example.com/article/1",
                published="2024-11-02",
                sentiment=-0.4 if flagged else 0.1,
            )
        ],
        sanctions_hits=[],
    )
