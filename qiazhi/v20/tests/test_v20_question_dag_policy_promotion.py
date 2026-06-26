from __future__ import annotations

from v20.learning.question_dag_policy_promotion import build_question_dag_policy_promotion_gate
from v20.tests.support_paths import read_v20_text


def test_v20_question_dag_policy_promotion_gate_blocks_without_runtime_switch() -> None:
    gate = build_question_dag_policy_promotion_gate(
        replay_report={
            "status": "ready_for_review",
            "policy_key": "next_question_policy",
            "comparison_count": 4,
            "impact_summary": {
                "offline_score_average": 0.75,
                "risk_count": 0,
                "candidate_win": True,
            },
        }
    )

    assert gate["version"] == "v20.question_dag_policy_promotion_gate.v1"
    assert gate["status"] == "blocked"
    assert gate["eligible_for_runtime"] is False
    assert gate["blocking_gate"] == "runtime_rollout_switch"
    assert "NO_RUNTIME_POINTER_WRITE_FROM_GATE" in gate["guardrails"]


def test_v20_question_dag_policy_promotion_gate_allows_explicit_rollout_switch() -> None:
    gate = build_question_dag_policy_promotion_gate(
        replay_report={
            "status": "ready_for_review",
            "policy_key": "next_question_policy",
            "comparison_count": 4,
            "impact_summary": {
                "offline_score_average": 0.75,
                "risk_count": 0,
                "candidate_win": True,
            },
        },
        runtime_rollout_switch=True,
    )

    assert gate["status"] == "eligible"
    assert gate["eligible_for_runtime"] is True
    assert gate["blocking_gate"] == ""


def test_v20_question_dag_policy_promotion_gate_reports_replay_risks() -> None:
    gate = build_question_dag_policy_promotion_gate(
        replay_report={
            "status": "needs_review",
            "policy_key": "next_question_policy",
            "comparison_count": 2,
            "impact_summary": {
                "offline_score_average": 0.1,
                "risk_count": 1,
                "candidate_win": False,
            },
        },
        runtime_rollout_switch=True,
    )

    failures = set(gate["failures"])
    assert gate["eligible_for_runtime"] is False
    assert "candidate_replay_ready" in failures
    assert "minimum_comparisons" in failures
    assert "offline_score_average" in failures
    assert "no_replay_risk" in failures
    assert "candidate_win" in failures


def test_v20_question_dag_policy_promotion_endpoint_is_declared() -> None:
    server_text = read_v20_text("server.py")

    assert "/api/v20/learning/question-dag-promotion" in server_text
    assert "build_question_dag_policy_promotion_gate" in server_text
