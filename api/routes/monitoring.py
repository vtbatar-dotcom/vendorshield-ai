"""Continuous monitoring endpoint.

RESEARCH_URL is env-configurable for docker-compose vs localhost.
"""
from __future__ import annotations
import urllib.request, json, os
from fastapi import APIRouter
from api.models.schemas import MonitoringRequest, MonitoringResponse

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

RESEARCH_URL = os.getenv("RESEARCH_URL", "http://localhost:8001") + "/assess"

HIGH_RISK_KEYWORDS = [
    "breach", "hack", "ransomware", "lawsuit", "fine", "bankrupt",
    "sanction", "attack", "fraud", "scandal", "investigation"
]


def _check_for_alerts(vendor_name: str, vendor_id: str) -> tuple[list[str], int, bool]:
    try:
        req = urllib.request.Request(
            RESEARCH_URL,
            data=json.dumps({
                "vendor_id": vendor_id,
                "vendor_name": vendor_name,
                "vendor_domain": None
            }).encode(),
            headers={"Content-Type": "application/json"}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
        signals = resp.get("risk_signals", [])
        sentiment = resp.get("sentiment_score", 0.0)
        alerts = [s[:200] for s in signals if any(kw in s.lower() for kw in HIGH_RISK_KEYWORDS)]
        risk_delta = min(100, int(abs(sentiment) * 20) + len(alerts) * 5) if sentiment < -0.5 else len(alerts) * 5
        requires_reopen = len(alerts) >= 2 or sentiment < -0.7
        return alerts, risk_delta, requires_reopen
    except Exception as e:
        return [f"Monitoring check failed: {str(e)}"], 0, False


@router.post("/check", response_model=MonitoringResponse)
def check(req: MonitoringRequest) -> MonitoringResponse:
    alerts, risk_delta, requires_reopen = _check_for_alerts(req.vendor_id, req.vendor_id)
    return MonitoringResponse(
        vendor_id=req.vendor_id,
        alerts=alerts,
        risk_delta=risk_delta,
        requires_reopen=requires_reopen
    )


@router.post("/check/{vendor_name}", response_model=MonitoringResponse)
def check_by_name(vendor_name: str, req: MonitoringRequest) -> MonitoringResponse:
    alerts, risk_delta, requires_reopen = _check_for_alerts(vendor_name, req.vendor_id)
    return MonitoringResponse(
        vendor_id=req.vendor_id,
        alerts=alerts,
        risk_delta=risk_delta,
        requires_reopen=requires_reopen
    )
