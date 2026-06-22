from __future__ import annotations
import os, json, re
from typing import Optional
from dotenv import load_dotenv
load_dotenv(dotenv_path="../../.env")

import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="VendorShield Financial Agent", version="0.1.0")

MOCK_DB = {
    "microsoft": {"credit_score":95,"revenue_2024":245.1,"revenue_2023":211.9,"revenue_2022":198.3,"net_income_2024":88.1,"debt_ratio":0.18,"current_ratio":2.5,"bankruptcy_risk":0.01,"credit_rating":"AAA","public":True},
    "acme cloud inc": {"credit_score":42,"revenue_2024":12.3,"revenue_2023":15.1,"revenue_2022":18.2,"net_income_2024":-2.1,"debt_ratio":0.72,"current_ratio":0.8,"bankruptcy_risk":0.38,"credit_rating":"B-","public":False},
    "globex saas ltd": {"credit_score":71,"revenue_2024":45.2,"revenue_2023":41.8,"revenue_2022":38.1,"net_income_2024":3.2,"debt_ratio":0.35,"current_ratio":1.6,"bankruptcy_risk":0.08,"credit_rating":"BBB","public":False},
}

class FinancialRequest(BaseModel):
    vendor_id: str
    vendor_name: str
    duns_number: Optional[str] = None

class FinancialResponse(BaseModel):
    vendor_id: str
    credit_score: int
    financial_health: str
    revenue_trend: str
    bankruptcy_risk: float
    risk_score: int
    anomalies: list[str]
    analyst_notes: str
    reviewer_notes: str

def get_data(vendor_name: str) -> dict:
    key = vendor_name.lower()
    for k, v in MOCK_DB.items():
        if k in key or key in k:
            return v
    return {"credit_score":55,"revenue_2024":None,"revenue_2023":None,"revenue_2022":None,"net_income_2024":None,"debt_ratio":None,"current_ratio":None,"bankruptcy_risk":0.15,"credit_rating":"Unknown","public":False}

def classify_health(d: dict) -> str:
    s = d["credit_score"]
    return "strong" if s>=80 else "stable" if s>=60 else "weak" if s>=40 else "distressed"

def classify_trend(d: dict) -> str:
    r22,r23,r24 = d.get("revenue_2022"),d.get("revenue_2023"),d.get("revenue_2024")
    if not all([r22,r23,r24]):
        return "unknown"
    return "growing" if r24>r23>r22 else "declining" if r24<r23 else "flat"

def fin_risk_score(d: dict) -> int:
    s = max(0, 60 - d["credit_score"])
    s += int(d["bankruptcy_risk"] * 40)
    if d.get("debt_ratio") and d["debt_ratio"] > 0.6: s += 20
    if d.get("current_ratio") and d["current_ratio"] < 1.0: s += 15
    if d.get("net_income_2024") and d["net_income_2024"] < 0: s += 10
    return min(100, s)

def call_claude(client, prompt: str) -> str:
    r = client.messages.create(model="claude-sonnet-4-6", max_tokens=512,
        messages=[{"role":"user","content":prompt}])
    return r.content[0].text

@app.get("/health")
def health():
    return {"status":"ok","agent":"financial","pattern":"analyst+reviewer"}

@app.post("/assess", response_model=FinancialResponse)
def assess(req: FinancialRequest) -> FinancialResponse:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    d = get_data(req.vendor_name)

    analyst_prompt = (
        "You are a financial analyst assessing vendor: " + req.vendor_name + "\n"
        "Data: credit_score=" + str(d["credit_score"]) + ", credit_rating=" + str(d["credit_rating"]) + "\n"
        "Revenue 2022/2023/2024: " + str(d["revenue_2022"]) + " / " + str(d["revenue_2023"]) + " / " + str(d["revenue_2024"]) + " ($B)\n"
        "Net income 2024: " + str(d["net_income_2024"]) + " ($B)\n"
        "Debt ratio: " + str(d["debt_ratio"]) + ", Current ratio: " + str(d["current_ratio"]) + "\n"
        "Bankruptcy risk: " + str(d["bankruptcy_risk"]) + "\n\n"
        "Write 2-3 sentences analyzing financial health. Plain text only, no markdown."
    )
    print("Analyst running for " + req.vendor_name + "...")
    analyst_notes = call_claude(client, analyst_prompt)
    print("Analyst done.")

    reviewer_prompt = (
        "You are a senior financial reviewer validating an assessment of: " + req.vendor_name + "\n"
        "Analyst notes: " + analyst_notes + "\n"
        "Key metrics: credit_score=" + str(d["credit_score"]) + ", bankruptcy_risk=" + str(d["bankruptcy_risk"]) + "\n"
        "debt_ratio=" + str(d["debt_ratio"]) + ", current_ratio=" + str(d["current_ratio"]) + "\n"
        "Revenue trend: " + str(d["revenue_2022"]) + " -> " + str(d["revenue_2023"]) + " -> " + str(d["revenue_2024"]) + "\n\n"
        'Return ONLY a JSON object like this (no markdown):\n'
        '{"reviewer_notes": "2 sentence validation", "anomalies": ["anomaly 1", "anomaly 2"]}'
    )
    print("Reviewer running for " + req.vendor_name + "...")
    reviewer_raw = call_claude(client, reviewer_prompt)
    reviewer_raw = re.sub(r"```(?:json)?", "", reviewer_raw).strip()
    print("Reviewer done.")

    try:
        parsed = json.loads(reviewer_raw)
        reviewer_notes = parsed.get("reviewer_notes", "")
        anomalies = parsed.get("anomalies", [])
    except json.JSONDecodeError:
        reviewer_notes = reviewer_raw
        anomalies = []

    return FinancialResponse(
        vendor_id=req.vendor_id,
        credit_score=d["credit_score"],
        financial_health=classify_health(d),
        revenue_trend=classify_trend(d),
        bankruptcy_risk=d["bankruptcy_risk"],
        risk_score=fin_risk_score(d),
        anomalies=anomalies,
        analyst_notes=analyst_notes,
        reviewer_notes=reviewer_notes
    )
