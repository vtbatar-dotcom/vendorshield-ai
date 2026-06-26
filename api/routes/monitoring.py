"""Continuous monitoring endpoint.

Checks for new risk signals by searching recent news.
In production this runs on a schedule (daily).
For demo: call manually to simulate a monitoring check.
"""
from __future__ import annotations
import urllib.request, json
from fastapi import APIRouter
from api.models.schemas import MonitoringRequest, MonitoringResponse

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

RESEARCH_URL = "http://localhost:8001/assess"

HIGH_RISK_KEYWORDS = [
    "breach", "hack", "ransomware", "lawsuit", "fine", "bankrupt",
    "sanction", "attack", "fraud", "scandal", "investigation"
]


def _check_for_alerts(vendor_name: str, vendor_id: str) -> tuple[list[str], int, bool]:
    """Call research agent and check for new risk signals."""
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

        alerts = []
        for signal in signals:
            if any(kw in signal.lower() for kw in HIGH_RISK_KEYWORDS):
                alerts.append(signal[:200])

        # Risk delta based on sentiment and signal count
        risk_delta = 0
        if sentiment < -0.5:
            risk_delta += int(abs(sentiment) * 20)
        risk_delta += len(alerts) * 5
        risk_delta = min(100, risk_delta)

        requires_reopen = len(alerts) >= 2 or sentiment < -0.7

        return alerts, risk_delta, requires_reopen

    except Exception as e:
        return [f"Monitoring check failed: {str(e)}"], 0, False


@router.post("/check", response_model=MonitoringResponse)
def check(req: MonitoringRequest) -> MonitoringResponse:
    vendor_name = req.vendor_id  # use vendor_id as name fallback
    alerts, risk_delta, requires_reopen = _check_for_alerts(vendor_name, req.vendor_id)

    return MonitoringResponse(
        vendor_id=req.vendor_id,
        alerts=alerts,
        risk_delta=risk_delta,
        requires_reopen=requires_reopen
    )


@router.post("/check/{vendor_name}", response_model=MonitoringResponse)
def check_by_name(vendor_name: str, req: MonitoringRequest) -> MonitoringResponse:
    """Check monitoring with explicit vendor name."""
    alerts, risk_delta, requires_reopen = _check_for_alerts(vendor_name, req.vendor_id)
    return MonitoringResponse(
        vendor_id=req.vendor_id,
        alerts=alerts,
        risk_delta=risk_delta,
        requires_reopen=requires_reopen
    )
