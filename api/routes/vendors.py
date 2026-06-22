"""Vendor case lookup endpoint (mock).

Phase 1: returns a static case so the dashboard/UiPath side can render.
Later this reads real case state from UiPath Data Service.
"""
from fastapi import APIRouter
from api.models.schemas import CaseResponse

router = APIRouter(prefix="/api/vendors", tags=["vendors"])


@router.get("/{vendor_id}/case", response_model=CaseResponse)
def get_case(vendor_id: str) -> CaseResponse:
    return CaseResponse(
        case_id=f"CASE-{vendor_id}",
        vendor_id=vendor_id,
        stage="Assessment",
        sla_status="on_track",
        findings=["intake complete", "research signals attached"],
        decisions=[],
    )
