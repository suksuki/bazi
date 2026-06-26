from __future__ import annotations

from v20.scripts.release_smoke import build_release_smoke_report


def test_v20_release_smoke_covers_orchestrator_policy_loop_without_http() -> None:
    report = build_release_smoke_report(skip_http=True)

    assert report["version"] == "v20.release_smoke_report.v1"
    assert report["status"] == "pass"
    assert report["runtime_mutation"] is False
    assert {row["check_key"] for row in report["checks"]} >= {
        "active_policy_pointer",
        "policy_observability_training",
        "training_iteration_summary",
        "policy_candidate_traceability",
        "question_source_graph_observability",
        "runtime_question_source_ranking_report",
        "question_source_training_report",
    }
    assert "ORCHESTRATOR_POLICY_LOOP_SMOKE_COVERED" in report["guardrails"]
