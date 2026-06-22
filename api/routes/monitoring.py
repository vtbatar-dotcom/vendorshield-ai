"""Continuous monitoring endpoint (mock).

Phase 1: deterministic 'no change'. Phase 10 wires the real daily scan that
can flip requires_reopen to True and push the case back to Assessment.
"""
from fastapi import APIRouter
from api.models.schemas import MonitoringRequest, MonitoringResponse

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.post("/check", response_model=MonitoringResponse)
def check(req: MonitoringRequest) -> MonitoringResponse:
    return MonitoringResponse(
        vendor_id=req.vendor_id,
        alerts=[],
        risk_delta=0,
        requires_reopen=False,
    )
