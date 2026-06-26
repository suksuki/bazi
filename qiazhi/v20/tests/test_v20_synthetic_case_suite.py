from __future__ import annotations

from v20.scripts.run_synthetic_case_suite import _run_suite


def test_v20_synthetic_case_suite_smoke_passes_without_runtime_mutation() -> None:
    report = _run_suite(max_cases=1, summary=True)

    assert report["version"] == "v20.synthetic_case_suite_report.v1"
    assert report["status"] == "pass"
    assert report["ok"] is True
    assert report["case_count"] == 1
    assert report["failure_count"] == 0
    assert report["coverage_gap_count"] == 0
    assert report["coverage_report"]["status"] == "pass"
    assert report["coverage_report"]["case_count"] >= 14
    assert report["runtime_mutation"] is False
    assert "NO_POLICY_POINTER_MUTATION" in report["guardrails"]
