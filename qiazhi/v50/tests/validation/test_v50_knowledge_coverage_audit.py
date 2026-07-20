from __future__ import annotations

from scripts.v50_run_knowledge_coverage_audit import run_audit


def test_knowledge_coverage_audit_reports_current_gaps() -> None:
    report = run_audit()

    assert report["version"] == "v50.knowledge_coverage_audit.v1"
    assert report["hard_boundary"]["llm_used"] is False
    assert report["hard_boundary"]["rules_added"] is False
    assert report["hard_boundary"]["weights_modified"] is False
    assert report["final_conclusion"]["ready_for_llm_synthetic_validation"] == "partial"
    assert report["final_conclusion"]["allowed_topics"] == ["wealth", "career"]
    assert "relationship" in report["final_conclusion"]["blocked_topics"]
    assert report["coverage_scores"]["Evidence Coverage"]["score"] == 1.0
    assert report["coverage_scores"]["Bazi Mechanism Coverage"]["score"] < 0.5
    assert any(item["knowledge_item"] == "调候" and item["status"] == "missing" for item in report["items"])

