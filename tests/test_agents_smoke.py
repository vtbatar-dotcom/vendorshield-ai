"""Smoke tests for all agent health endpoints.

Requires all agents to be running (bash start.sh first).
Run: python3 tests/test_agents_smoke.py
"""
import sys
import urllib.request
import json

AGENTS = {
    "main-api":         "http://localhost:8000/health",
    "research-agent":   "http://localhost:8001/health",
    "compliance-agent": "http://localhost:8002/health",
    "financial-agent":  "http://localhost:8003/health",
    "remediation-agent":"http://localhost:8004/health",
    "intake-agent":     "http://localhost:8005/health",
}


def get(url: str, timeout: int = 5) -> dict:
    resp = urllib.request.urlopen(url, timeout=timeout)
    return json.loads(resp.read())


def post(url: str, data: dict, timeout: int = 10) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(resp.read())


print("\nVendorShield AI — Agent Smoke Tests")
print("=" * 40)

passed = failed = 0

# Test 1: all health endpoints
for name, url in AGENTS.items():
    try:
        r = get(url)
        assert r.get("status") == "ok"
        print(f"  ✅ {name}: health ok")
        passed += 1
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        failed += 1

# Test 2: compliance agent assess
try:
    r = post("http://localhost:8002/assess", {
        "vendor_id": "SMOKE-001",
        "vendor_name": "Test Vendor",
        "tier": "High",
        "certifications": [],
        "markets": ["US"]
    })
    assert "compliance_score" in r
    assert "gaps" in r
    print(f"  ✅ compliance /assess: score={r['compliance_score']}, gaps={len(r['gaps'])}")
    passed += 1
except Exception as e:
    print(f"  ❌ compliance /assess: {e}")
    failed += 1

# Test 3: financial agent assess
try:
    r = post("http://localhost:8003/assess", {
        "vendor_id": "SMOKE-001",
        "vendor_name": "Globex SaaS Ltd"
    }, timeout=60)
    assert "credit_score" in r
    assert "financial_health" in r
    print(f"  ✅ financial /assess: health={r['financial_health']}, score={r['credit_score']}")
    passed += 1
except Exception as e:
    print(f"  ❌ financial /assess: {e}")
    failed += 1

# Test 4: risk scoring
try:
    r = post("http://localhost:8000/api/risk/score", {
        "vendor_id": "SMOKE-001",
        "research_signals": ["test signal"],
        "compliance_gaps": ["SOC2: MISSING"],
        "sentiment_score": -0.5
    })
    assert "overall_score" in r
    assert "classification" in r
    print(f"  ✅ risk /score: score={r['overall_score']}, class={r['classification']}")
    passed += 1
except Exception as e:
    print(f"  ❌ risk /score: {e}")
    failed += 1

# Test 5: intake agent
try:
    r = post("http://localhost:8005/intake", {
        "vendor_name": "Test Corp",
        "annual_spend_usd": 500000,
        "data_access": "confidential"
    })
    assert "tier" in r
    assert "vendor_id" in r
    print(f"  ✅ intake /intake: tier={r['tier']}, id={r['vendor_id']}")
    passed += 1
except Exception as e:
    print(f"  ❌ intake /intake: {e}")
    failed += 1

# Test 6: case store round-trip
try:
    post("http://localhost:8000/api/vendors/SMOKE-001/store", {
        "stage": "Assessment",
        "overall_score": 45,
        "classification": "Medium",
        "findings": ["test finding"],
        "decisions": [],
        "sla_status": "on_track"
    })
    r = get("http://localhost:8000/api/vendors/SMOKE-001/case")
    assert r["vendor_id"] == "SMOKE-001"
    assert r["stage"] == "Assessment"
    print(f"  ✅ case store round-trip: stage={r['stage']}")
    passed += 1
except Exception as e:
    print(f"  ❌ case store: {e}")
    failed += 1

print("=" * 40)
print(f"Results: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
