from __future__ import annotations

from scripts.v50_audit_runtime_authority import audit_runtime_authority


def test_production_runtime_has_one_cognitive_authority_and_no_fixture_answer_leak() -> None:
    report = audit_runtime_authority()

    assert report["status"] == "passed"
    assert report["observed_data"]["forbidden_research_imports"] == []
    assert report["observed_data"]["synthetic_answer_leakage_tokens"] == []
    assert report["observed_data"]["graph_relation_authority_violations"] == []
    assert report["boundary_status"]["retired_brain_restored"] is False
