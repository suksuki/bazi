from __future__ import annotations

from v20.learning.role_view_policy_promotion import build_role_view_policy_promotion_gate


def test_v20_role_view_policy_promotion_gate_blocks_without_runtime_switch() -> None:
    gate = build_role_view_policy_promotion_gate(
        replay_report={
            "status": "ready_for_review",
            "candidate_policy_version": "v20.role_view_policy.candidate.test",
            "baseline_policy_version": "v20.role_view_policy.v1",
            "comparison_count": 4,
            "replay_result": {
                "positive_score_count": 3,
                "negative_score_count": 0,
            },
            "impact_summary": {
                "offline_score_average": 0.5,
            },
            "ab_test_summary": {
                "net_lift": 2.0,
                "risk_count": 0,
            },
        }
    )

    assert gate["version"] == "v20.role_view_policy_promotion_gate.v1"
    assert gate["status"] == "blocked"
    assert gate["eligible_for_runtime"] is False
    assert gate["blocking_gate"] == "runtime_rollout_switch"
    assert "NO_RUNTIME_POINTER_WRITE_FROM_GATE" in gate["guardrails"]


def test_v20_role_view_policy_promotion_gate_allows_explicit_runtime_switch() -> None:
    gate = build_role_view_policy_promotion_gate(
        replay_report={
            "status": "ready_for_review",
            "candidate_policy_version": "v20.role_view_policy.candidate.test",
            "baseline_policy_version": "v20.role_view_policy.v1",
            "comparison_count": 4,
            "replay_result": {
                "positive_score_count": 3,
                "negative_score_count": 0,
            },
            "impact_summary": {
                "offline_score_average": 0.5,
            },
            "ab_test_summary": {
                "net_lift": 2.0,
                "risk_count": 0,
            },
        },
        runtime_rollout_switch=True,
    )

    assert gate["status"] == "eligible"
    assert gate["eligible_for_runtime"] is True
    assert gate["blocking_gate"] == ""


def test_v20_role_view_policy_promotion_gate_reports_scoring_gaps() -> None:
    gate = build_role_view_policy_promotion_gate(
        replay_report={
            "status": "not_enough_data",
            "comparison_count": 1,
            "replay_result": {
                "positive_score_count": 0,
                "negative_score_count": 2,
            },
            "impact_summary": {
                "offline_score_average": -0.5,
            },
            "ab_test_summary": {
                "net_lift": -1.0,
                "risk_count": 2,
            },
        }
    )

    failures = set(gate["failures"])
    assert gate["eligible_for_runtime"] is False
    assert "candidate_replay_ready" in failures
    assert "minimum_comparisons" in failures
    assert "positive_reward_margin" in failures
    assert "offline_score_average" in failures
    assert "ab_candidate_lift" in failures
    assert "ab_no_negative_risk" in failures
