import json
from pathlib import Path

from componente_ia.production_validation import latency_summary, percentile, run_validation


def test_percentile_math_is_deterministic():
    values = [1, 2, 3, 4, 5]
    assert percentile(values, 50) == 3
    assert percentile(values, 95) == 4.8
    summary = latency_summary(values)
    assert summary["count"] == 5
    assert summary["p99_ms"] == 4.96


def test_short_production_profile_meets_budgets():
    result = run_validation(
        sequential_requests=30,
        concurrent_requests=10,
        catalog_size=1000,
        soak_iterations=20,
        live_web=False,
    )
    assert result["passed"] is True, result
    assert result["local"]["p95_ms"] < 150
    assert result["catalog_10000"]["p95_ms"] < 700
    assert result["web_simulated"]["p95_ms"] < 1500
    assert result["errors"] == []


def test_full_performance_artifact_when_present_is_internally_consistent():
    path = Path(__file__).resolve().parents[2] / "artifacts" / "ia_performance_results.json"
    if not path.exists():
        return
    result = json.loads(path.read_text(encoding="utf-8"))
    assert result["configuration"]["sequential_requests"] == 1000
    assert result["configuration"]["concurrent_requests"] == 100
    assert result["configuration"]["catalog_products"] == 10000
    assert result["local"]["count"] == 1000
    assert result["concurrent_100"]["count"] == 100
    assert result["catalog_10000"]["p95_ms"] < 700
    assert result["memory"]["sessions"] <= result["memory"]["max_sessions"]

