"""VendorShield AI - End-to-end demo script.

Usage:
  python3 demo.py                        # runs with default vendor (Acme Cloud Inc)
  python3 demo.py "Microsoft"            # runs with any vendor name
  python3 demo.py "Acme Cloud Inc" High  # with tier
"""
from __future__ import annotations
import sys, json, time, urllib.request
from datetime import datetime

VENDOR_NAME   = sys.argv[1] if len(sys.argv) > 1 else "Acme Cloud Inc"
VENDOR_TIER   = sys.argv[2] if len(sys.argv) > 2 else "High"
VENDOR_ID     = "DEMO-001"
VENDOR_DOMAIN = VENDOR_NAME.lower().replace(" ", "") + ".com"

PORTS = {
    "main":        "http://localhost:8000",
    "research":    "http://localhost:8001",
    "compliance":  "http://localhost:8002",
    "financial":   "http://localhost:8003",
    "remediation": "http://localhost:8004",
}

def post(url: str, data: dict, timeout: int = 90) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(resp.read())

def get(url: str) -> dict:
    resp = urllib.request.urlopen(url, timeout=10)
    return json.loads(resp.read())

def bar(score: int, width: int = 20) -> str:
    filled = int(score / 100 * width)
    return "█" * filled + "░" * (width - filled)

def color_class(c: str) -> str:
    return {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Critical": "🔴"}.get(c, "⚪")

def sep(char: str = "=", width: int = 60) -> str:
    return char * width

print()
print(sep())
print("  VENDORSHIELD AI — Vendor Risk Assessment")
print(sep())
print(f"  Vendor:  {VENDOR_NAME}")
print(f"  Tier:    {VENDOR_TIER}")
print(f"  Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
print(sep())

# Check all services are up
print("\n📡 Checking services...")
all_up = True
for name, base in PORTS.items():
    try:
        h = get(base + "/health")
        print(f"  ✅ {name:<12} {base}")
    except Exception as e:
        print(f"  ❌ {name:<12} {base} — DOWN ({e})")
        all_up = False

if not all_up:
    print("\n❌ Some services are down. Start all agents before running demo.")
    sys.exit(1)

# STEP 1: Research
print(f"\n{sep('-')}")
print("STEP 1/4 — Research Agent (Claude + Tavily web search)")
print(sep("-"))
t0 = time.time()
research = post(PORTS["research"] + "/assess", {
    "vendor_id": VENDOR_ID,
    "vendor_name": VENDOR_NAME,
    "vendor_domain": VENDOR_DOMAIN
})
t1 = time.time()
print(f"  ⏱  {t1-t0:.1f}s")
print(f"  📰 Risk signals found: {len(research.get('risk_signals', []))}")
print(f"  📊 Sentiment score:    {research.get('sentiment_score', 0)}")
print(f"  📰 News items:         {len(research.get('news_items', []))}")
print(f"  🚫 Sanctions hits:     {research.get('sanctions_hits', []) or 'None'}")
print("\n  Top signals:")
for s in research.get("risk_signals", [])[:3]:
    print(f"    • {s[:80]}...")

# STEP 2: Compliance
print(f"\n{sep('-')}")
print("STEP 2/4 — Compliance Agent")
print(sep("-"))
t0 = time.time()
# Known certs for demo vendors
KNOWN_CERTS = {
    "microsoft": [
        {"name": "SOC2", "issued": "2024-01-01", "expiry": "2027-01-01", "issuer": "Deloitte"},
        {"name": "ISO27001", "issued": "2023-06-01", "expiry": "2027-06-01", "issuer": "BSI"},
        {"name": "GDPR", "issued": "2023-01-01", "expiry": "2027-01-01", "issuer": "TUV"},
    ],
    "globex saas ltd": [
        {"name": "SOC2", "issued": "2024-06-01", "expiry": "2027-06-01", "issuer": "PwC"},
    ],
}
vendor_certs = KNOWN_CERTS.get(VENDOR_NAME.lower(), [])
compliance = post(PORTS["compliance"] + "/assess", {
    "vendor_id": VENDOR_ID,
    "vendor_name": VENDOR_NAME,
    "tier": VENDOR_TIER,
    "certifications": vendor_certs,
    "markets": ["US", "EU"]
})
t1 = time.time()
print(f"  ⏱  {t1-t0:.1f}s")
print(f"  📋 Compliance score: {compliance.get('compliance_score', 0)}/100")
print(f"  ✅ Passed: {compliance.get('passed', []) or 'None'}")
print(f"  ❌ Gaps:")
for g in compliance.get("gaps", []):
    print(f"    • {g['certification']}: {g['status']} [{g['severity']}]")

# STEP 3: Financial
print(f"\n{sep('-')}")
print("STEP 3/4 — Financial Agent (analyst + reviewer)")
print(sep("-"))
t0 = time.time()
financial = post(PORTS["financial"] + "/assess", {
    "vendor_id": VENDOR_ID,
    "vendor_name": VENDOR_NAME
})
t1 = time.time()
print(f"  ⏱  {t1-t0:.1f}s")
print(f"  💳 Credit score:    {financial.get('credit_score', 0)}/100")
print(f"  🏥 Health:          {financial.get('financial_health', 'unknown')}")
print(f"  📈 Revenue trend:   {financial.get('revenue_trend', 'unknown')}")
print(f"  ⚠️  Bankruptcy risk: {financial.get('bankruptcy_risk', 0)}")
print(f"  🚨 Anomalies:       {len(financial.get('anomalies', []))}")

# STEP 4: Risk Scoring
print(f"\n{sep('-')}")
print("STEP 4/4 — Risk Scoring (weighted model)")
print(sep("-"))
compliance_gaps = [
    g["certification"] + ": " + g["status"]
    for g in compliance.get("gaps", [])
]
t0 = time.time()
risk = post(PORTS["main"] + "/api/risk/score", {
    "vendor_id": VENDOR_ID,
    "research_signals": research.get("risk_signals", []),
    "sentiment_score": research.get("sentiment_score", 0.0),
    "news_items": research.get("news_items", []),
    "sanctions_hits": research.get("sanctions_hits", []),
    "compliance_gaps": compliance_gaps,
    "financial_data": {
        "vendor_id": VENDOR_ID,
        "credit_score": financial.get("credit_score", 50),
        "financial_health": financial.get("financial_health", "unknown"),
        "revenue_trend": financial.get("revenue_trend", "unknown"),
        "bankruptcy_risk": financial.get("bankruptcy_risk", 0.1)
    }
})
t1 = time.time()
print(f"  ⏱  {t1-t0:.1f}s")

# STEP 5: Remediation
print(f"\n{sep('-')}")
print("STEP 5/5 — Remediation Agent")
print(sep("-"))
t0 = time.time()
remediation = post(PORTS["remediation"] + "/remediate", {
    "vendor_id": VENDOR_ID,
    "vendor_name": VENDOR_NAME,
    "overall_score": risk.get("overall_score", 0),
    "classification": risk.get("classification", ""),
    "flags": risk.get("flags", []),
    "risk_signals": research.get("risk_signals", []),
    "compliance_gaps": compliance_gaps,
    "financial_health": financial.get("financial_health", "unknown"),
    "bankruptcy_risk": financial.get("bankruptcy_risk", 0.0),
    "anomalies": financial.get("anomalies", []),
    "tier": VENDOR_TIER
})
t1 = time.time()
print(f"  ⏱  {t1-t0:.1f}s")
print(f"  📋 Tasks generated: {remediation.get('total_tasks', 0)}")
print(f"  🚨 Critical tasks:  {remediation.get('critical_tasks', 0)}")
print(f"  📅 Est. resolution: {remediation.get('estimated_resolution_days', 0)} days")

# FINAL REPORT
dims = risk.get("dimension_scores", {})
print()
print(sep())
print(f"  FINAL VENDOR RISK REPORT")
print(sep())
print(f"  Vendor:         {VENDOR_NAME}")
print(f"  Assessment ID:  {VENDOR_ID}")
print(f"  Assessed at:    {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
print(sep("-"))
print(f"  Overall Score:  {risk.get('overall_score')}/100  {bar(risk.get('overall_score', 0))}")
print(f"  Classification: {color_class(risk.get('classification',''))} {risk.get('classification')}")
print(f"  Decision:       {remediation.get('decision')}")
print(f"  Routing:        {risk.get('routing')}")
print(f"  Confidence:     {risk.get('confidence')}%")
print(sep("-"))
print("  Dimension Scores:")
for k, v in dims.items():
    print(f"    {k:<12} {bar(v, 15)} {v}/100")
print(sep("-"))
print("  Flags:")
for f in risk.get("flags", []):
    print(f"    {f}")
print(sep("-"))
print("  Remediation Tasks:")
for t in remediation.get("tasks", []):
    icon = "🔴" if t["priority"] == "CRITICAL" else "🟠" if t["priority"] == "HIGH" else "🟡"
    print(f"    {icon} [{t['id']}] {t['title']}")
    print(f"         Owner: {t['owner']} | Due: {t['deadline_date']}")
print(sep("-"))
print("  Executive Summary:")
summary = remediation.get("executive_summary", "")
words = summary.split()
line = "  "
for word in words:
    if len(line) + len(word) > 58:
        print(line)
        line = "  " + word + " "
    else:
        line += word + " "
if line.strip():
    print(line)
print(sep())
print(f"  Assessment complete.")
print(sep())
