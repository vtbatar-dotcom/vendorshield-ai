"""Compliance Agent — checks vendor certifications and produces gap reports.

Runs on port 8002.
Checks: SOC2, ISO27001, HIPAA, PCI-DSS, GDPR, CCPA, DORA
"""
from __future__ import annotations
import os, json
from dotenv import load_dotenv
load_dotenv(dotenv_path="../../.env")

import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="VendorShield Compliance Agent", version="0.1.0")

# Required certs per vendor tier
TIER_REQUIREMENTS = {
    "Critical": ["SOC2", "ISO27001", "HIPAA", "PCI-DSS", "GDPR", "DORA"],
    "High":     ["SOC2", "ISO27001", "GDPR"],
    "Medium":   ["SOC2", "GDPR"],
    "Low":      ["SOC2"],
}

# Known cert validity periods in months
CERT_VALIDITY = {
    "SOC2": 12,
    "ISO27001": 36,
    "HIPAA": 12,
    "PCI-DSS": 12,
    "GDPR": 24,
    "CCPA": 12,
    "DORA": 12,
}


class CertItem(BaseModel):
    name: str
    issued: str | None = None
    expiry: str | None = None
    issuer: str | None = None


class ComplianceRequest(BaseModel):
    vendor_id: str
    vendor_name: str
    tier: str = "High"
    certifications: list[CertItem] = []
    markets: list[str] = []


class GapItem(BaseModel):
    certification: str
    status: str
    severity: str
    recommendation: str


class ComplianceResponse(BaseModel):
    vendor_id: str
    compliance_score: int
    gaps: list[GapItem]
    passed: list[str]
    risk_summary: str
    requires_review: bool


def analyze_with_claude(vendor_name: str, tier: str, certs: list[CertItem], gaps: list[str], passed: list[str]) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    cert_details = "\n".join([
        f"- {c.name}: issued={c.issued or 'unknown'}, expiry={c.expiry or 'unknown'}, issuer={c.issuer or 'unknown'}"
        for c in certs
    ]) or "No certifications provided"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"""You are a compliance expert reviewing vendor "{vendor_name}" (tier: {tier}).

Certifications provided:
{cert_details}

Passed checks: {passed}
Gaps identified: {gaps}

Write a 2-3 sentence compliance risk summary for a risk analyst. Be specific and actionable.
Focus on the most critical gaps and their business impact. No markdown, plain text only."""}]
    )
    return response.content[0].text


@app.get("/health")
def health():
    return {"status": "ok", "agent": "compliance", "version": "0.1.0"}


@app.post("/assess", response_model=ComplianceResponse)
def assess(req: ComplianceRequest) -> ComplianceResponse:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    required = TIER_REQUIREMENTS.get(req.tier, TIER_REQUIREMENTS["High"])
    provided_names = [c.name.upper() for c in req.certifications]

    passed = []
    gaps = []
    gap_items = []

    for cert in required:
        if cert in provided_names:
            passed.append(cert)
        else:
            gaps.append(cert)
            gap_items.append(GapItem(
                certification=cert,
                status="MISSING",
                severity="High" if cert in ["SOC2", "ISO27001"] else "Medium",
                recommendation=f"Obtain {cert} certification within 90 days"
            ))

    # Check expiry on provided certs
    for c in req.certifications:
        if c.expiry and c.name.upper() in required:
            from datetime import datetime
            try:
                expiry_date = datetime.strptime(c.expiry, "%Y-%m-%d")
                days_left = (expiry_date - datetime.now()).days
                if days_left < 0:
                    gap_items.append(GapItem(
                        certification=c.name,
                        status="EXPIRED",
                        severity="Critical",
                        recommendation=f"{c.name} expired — renew immediately"
                    ))
                    if c.name in passed:
                        passed.remove(c.name)
                elif days_left < 90:
                    gap_items.append(GapItem(
                        certification=c.name,
                        status=f"EXPIRING_SOON ({days_left} days)",
                        severity="Medium",
                        recommendation=f"Renew {c.name} within {days_left} days"
                    ))
            except ValueError:
                pass

    # Compliance score = % of required certs passed
    score = int(len(passed) / len(required) * 100) if required else 100

    # Claude generates the risk summary
    print(f"Analyzing compliance for {req.vendor_name}...")
    summary = analyze_with_claude(req.vendor_name, req.tier, req.certifications, gaps, passed)
    print(f"Summary: {summary[:100]}...")

    return ComplianceResponse(
        vendor_id=req.vendor_id,
        compliance_score=score,
        gaps=gap_items,
        passed=passed,
        risk_summary=summary,
        requires_review=score < 70 or any(g.severity == "Critical" for g in gap_items)
    )
