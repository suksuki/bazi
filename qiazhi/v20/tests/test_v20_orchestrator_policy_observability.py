from __future__ import annotations

from v20.orchestrator.policy_observability import build_policy_observability_summary
from v20.server import _question_source_graph_observability


def test_v20_policy_observability_reports_baseline_fallback() -> None:
    summary = build_policy_observability_summary(
        policy_pointer={
            "active_policy_version": "v20.orchestrator_policy.baseline.v1",
            "candidate_policy_version": "",
            "rollback_policy_version": "v20.orchestrator_policy.baseline.v1",
            "runtime_applied": False,
        },
        mainline_arbitration={"runtime_policy_effect": {"status": "not_applied"}},
        question_mainline_focus={"runtime_policy_effect": {"status": "not_applied"}},
    )

    assert summary["version"] == "v20.orchestrator_policy_observability.v1"
    assert summary["status"] == "baseline_active"
    assert summary["fallback_active"] is True
    assert summary["applied_consumer_count"] == 0
    assert summary["runtime_mutation"] is False


def test_v20_policy_observability_reports_consumed_candidate() -> None:
    summary = build_policy_observability_summary(
        policy_pointer={
            "active_policy_version": "v20.orchestrator_policy.candidate.test",
            "candidate_policy_version": "v20.orchestrator_policy.candidate.test",
            "rollback_policy_version": "v20.orchestrator_policy.baseline.v1",
            "runtime_applied": True,
        },
        mainline_arbitration={
            "runtime_policy_effect": {
                "status": "applied",
                "active_policy_version": "v20.orchestrator_policy.candidate.test",
                "applied_adjustment_count": 2,
            }
        },
        question_mainline_focus={
            "runtime_policy_effect": {
                "status": "applied",
                "active_policy_version": "v20.orchestrator_policy.candidate.test",
                "domain_boost": 0.04,
            }
        },
    )

    assert summary["status"] == "candidate_consumed"
    assert summary["fallback_active"] is False
    assert summary["applied_consumer_count"] == 2
    assert summary["consumers"][0]["module_key"] == "mainline_arbitration"
    assert summary["consumers"][0]["applied_adjustment_count"] == 2
    assert summary["consumers"][1]["module_key"] == "question_mainline_focus"
    assert summary["consumers"][1]["domain_boost"] == 0.04


def test_v20_policy_observability_exposes_question_source_graph_readonly() -> None:
    graph = _question_source_graph_observability()

    assert graph["version"] == "v20.question_source_graph.v1"
    assert graph["runtime_mutation"] is False
    assert graph["selected_paths"]
    assert "QUESTION_SOURCE_GRAPH_OBSERVABILITY_READ_ONLY" in graph["guardrails"]
    assert "NO_ADMIN_WRITE_FROM_SOURCE_GRAPH" in graph["guardrails"]
