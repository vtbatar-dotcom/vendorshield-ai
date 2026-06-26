"""Smoke tests for the risk scoring engine."""
import sys
sys.path.insert(0, ".")

from api.routes.risk import score
from api.models.schemas import RiskRequest, FinancialData


def make_request(**kwargs) -> RiskRequest:
    defaults = {
        "vendor_id": "TEST-001",
        "research_signals": [],
        "news_items": [],
        "sentiment_score": 0.0,
        "compliance_gaps": [],
        "financial_data": None,
        "sanctions_hits": [],
    }
    defaults.update(kwargs)
    return RiskRequest(**defaults)


def test_clean_vendor_is_low_or_medium():
    """A vendor with no signals should score low-medium (floor values exist)."""
    req = make_request()
    result = score(req)
    assert result.overall_score <= 50, f"Expected <=50, got {result.overall_score}"
    assert result.classification in ["Low", "Medium"]
    print(f"  ✅ Clean vendor: score={result.overall_score}, class={result.classification}")


def test_missing_certs_drive_compliance():
    req = make_request(compliance_gaps=["SOC2: MISSING", "ISO27001: MISSING", "GDPR: MISSING"])
    result = score(req)
    assert result.dimension_scores.compliance >= 75
    assert any("Missing" in f for f in result.flags)
    print(f"  ✅ Missing certs: compliance={result.dimension_scores.compliance}")


def test_breach_signals_drive_security():
    req = make_request(
        research_signals=["data breach confirmed", "ransomware attack", "credentials leaked"],
        sentiment_score=-0.9
    )
    result = score(req)
    assert result.dimension_scores.security >= 50
    print(f"  ✅ Breach signals: security={result.dimension_scores.security}")


def test_financial_data_used():
    req = make_request(financial_data=FinancialData(
        vendor_id="TEST-001",
        credit_score=40,
        financial_health="weak",
        revenue_trend="declining",
        bankruptcy_risk=0.45
    ))
    result = score(req)
    assert result.dimension_scores.financial >= 40
    print(f"  ✅ Financial data: financial={result.dimension_scores.financial}")


def test_sanctions_hit_escalates():
    req = make_request(sanctions_hits=["OFAC match: vendor entity"])
    result = score(req)
    assert "SANCTIONS HIT" in result.flags[0]
    assert result.dimension_scores.compliance >= 40
    print(f"  ✅ Sanctions: flags={result.flags[0][:40]}")


def test_high_risk_routes_to_human_review():
    req = make_request(
        research_signals=["breach", "hack", "ransomware", "attack", "lawsuit"],
        compliance_gaps=["SOC2: MISSING", "ISO27001: MISSING"],
        sentiment_score=-1.0
    )
    result = score(req)
    assert "HUMAN_REVIEW" in result.routing or "ESCALATE" in result.routing
    print(f"  ✅ High risk routing: {result.routing}")


def test_confidence_based_on_sources():
    req_low = make_request(research_signals=["breach"])
    req_high = make_request(
        research_signals=["breach"],
        news_items=[{"title":"t","url":"u","published":"2024","sentiment":-0.5}],
        sentiment_score=-0.5,
        financial_data=FinancialData(
            vendor_id="T", credit_score=50,
            financial_health="stable", revenue_trend="flat", bankruptcy_risk=0.1
        )
    )
    assert score(req_low).confidence < score(req_high).confidence
    print(f"  ✅ Confidence: low={score(req_low).confidence}% high={score(req_high).confidence}%")


def test_weights_sum_correctly():
    req = make_request(
        research_signals=["breach"] * 5,
        compliance_gaps=["SOC2: MISSING"] * 3,
        sentiment_score=-1.0
    )
    result = score(req)
    assert 0 <= result.overall_score <= 100
    print(f"  ✅ Score bounds: {result.overall_score}/100")


def test_high_risk_scores_higher_than_clean():
    clean = make_request()
    risky = make_request(
        research_signals=["breach", "ransomware", "lawsuit"],
        compliance_gaps=["SOC2: MISSING"],
        sentiment_score=-0.9
    )
    assert score(risky).overall_score > score(clean).overall_score
    print(f"  ✅ Risky > clean: {score(risky).overall_score} > {score(clean).overall_score}")


if __name__ == "__main__":
    tests = [
        test_clean_vendor_is_low_or_medium,
        test_missing_certs_drive_compliance,
        test_breach_signals_drive_security,
        test_financial_data_used,
        test_sanctions_hit_escalates,
        test_high_risk_routes_to_human_review,
        test_confidence_based_on_sources,
        test_weights_sum_correctly,
        test_high_risk_scores_higher_than_clean,
    ]
    print("\nVendorShield AI — Risk Scoring Tests")
    print("=" * 40)
    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  ❌ {t.__name__}: {e}")
            failed += 1
    print("=" * 40)
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
