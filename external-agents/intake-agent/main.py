"""Intake Agent — vendor onboarding and document parsing.

Phase 1 stub: accepts vendor info and classifies tier.
Full implementation requires UiPath Document Understanding for SOC2/ISO cert parsing.

Runs on port 8005.
"""
from __future__ import annotations
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path="../../.env")

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import anthropic

app = FastAPI(title="VendorShield Intake Agent", version="0.1.0")


class IntakeRequest(BaseModel):
    vendor_name: str
    vendor_domain: Optional[str] = None
    vendor_description: Optional[str] = None
    annual_spend_usd: Optional[int] = None
    data_access: Optional[str] = None
    services: list[str] = []


class IntakeResponse(BaseModel):
    vendor_id: str
    vendor_name: str
    tier: str
    tier_reason: str
    next_stage: str
    required_certs: list[str]


TIER_CERTS = {
    "Critical": ["SOC2", "ISO27001", "HIPAA", "PCI-DSS", "GDPR", "DORA"],
    "High":     ["SOC2", "ISO27001", "GDPR"],
    "Medium":   ["SOC2", "GDPR"],
    "Low":      ["SOC2"],
}


def classify_tier(req: IntakeRequest) -> tuple[str, str]:
    """Rule-based tier classification."""
    spend = req.annual_spend_usd or 0
    data = (req.data_access or "").lower()

    if spend > 1_000_000 or "pii" in data or "phi" in data or "payment" in data:
        return "Critical", "High spend or sensitive data access"
    if spend > 100_000 or "confidential" in data:
        return "High", "Significant spend or confidential data"
    if spend > 10_000:
        return "Medium", "Moderate spend"
    return "Low", "Low spend and limited data access"


def generate_vendor_id(vendor_name: str) -> str:
    import hashlib
    return "V" + hashlib.md5(vendor_name.encode()).hexdigest()[:6].upper()


@app.get("/health")
def health():
    return {"status": "ok", "agent": "intake", "version": "0.1.0",
            "note": "Document Understanding integration pending"}


@app.post("/intake", response_model=IntakeResponse)
def intake(req: IntakeRequest) -> IntakeResponse:
    tier, reason = classify_tier(req)
    vendor_id = generate_vendor_id(req.vendor_name)

    return IntakeResponse(
        vendor_id=vendor_id,
        vendor_name=req.vendor_name,
        tier=tier,
        tier_reason=reason,
        next_stage="Automated Assessment",
        required_certs=TIER_CERTS[tier]
    )
