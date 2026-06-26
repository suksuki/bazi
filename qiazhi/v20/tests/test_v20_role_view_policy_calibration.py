from __future__ import annotations

from pathlib import Path

from v20.interaction.role_question_click import record_role_question_click
from v20.learning.role_question_click_training import build_role_question_click_training_report
from v20.learning.role_view_policy_calibration import build_role_view_policy_calibration_report
from v20.learning.role_view_policy_candidates import build_role_view_policy_candidate_report
from v20.learning.role_view_policy_promotion import build_role_view_policy_promotion_gate
from v20.learning.role_view_policy_replay import build_role_view_policy_replay_report
from v20.storage.local_jsonl import LocalJsonlStore


def test_v20_role_view_policy_calibration_suggests_thresholds_from_rewards_and_ab_replay(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    for index in range(4):
        record_role_question_click(
            input_id=f"role.calibration.{index}",
            source_role="user",
            question={
                "question_key": "q_income_factors",
                "domain": "wealth",
                "role_view_level": "guided",
                "question_strategy": "guided_user_question",
                "question_group": "domain",
                "seed_source_key": "seed.wealth.opportunity_pressure",
                "action_type": "answer_helpful",
            },
            store=store,
        )

    clicks = build_role_question_click_training_report(store=store)
    candidate = build_role_view_policy_candidate_report(click_training_report=clicks)
    replay = build_role_view_policy_replay_report(policy_candidate_report=candidate)
    calibration = build_role_view_policy_calibration_report(click_training_report=clicks, replay_report=replay)
    gate = build_role_view_policy_promotion_gate(
        replay_report=replay,
        calibration_report=calibration,
        runtime_rollout_switch=True,
    )

    assert calibration["version"] == "v20.role_view_policy_calibration_report.v1"
    assert calibration["status"] == "ready"
    assert calibration["reward_observation"]["sample_count"] == 4
    assert calibration["reward_observation"]["reward_average"] == 1.0
    assert calibration["ab_observation"]["net_lift"] > 0
    assert calibration["suggested_thresholds"]["min_promotion_comparisons"] >= 3
    assert calibration["suggested_thresholds"]["max_ab_risk_count"] == 0
    assert calibration["runtime_mutation"] is False
    assert "CALIBRATION_SUGGESTS_THRESHOLDS_ONLY" in calibration["guardrails"]
    assert gate["calibration_version"] == "v20.role_view_policy_calibration_report.v1"
    assert gate["applied_thresholds"]["min_promotion_comparisons"] == calibration["suggested_thresholds"]["min_promotion_comparisons"]
    assert gate["eligible_for_runtime"] is True


def test_v20_role_view_policy_calibration_blocks_risky_ab_replay() -> None:
    replay = {
        "status": "ready_for_review",
        "candidate_policy_version": "v20.role_view_policy.candidate.risky",
        "baseline_policy_version": "v20.role_view_policy.v1",
        "comparison_count": 4,
        "replay_result": {
            "positive_score_count": 2,
            "negative_score_count": 1,
        },
        "impact_summary": {
            "offline_score_average": 0.3,
        },
        "ab_test_summary": {
            "net_lift": 0.4,
            "risk_count": 1,
        },
    }
    calibration = build_role_view_policy_calibration_report(
        click_training_report={
            "status": "ready",
            "click_count": 4,
            "reward_summaries": [
                {
                    "sample_count": 4,
                    "reward_total": 1.2,
                    "positive_count": 2,
                    "negative_count": 1,
                }
            ],
        },
        replay_report=replay,
    )
    gate = build_role_view_policy_promotion_gate(
        replay_report=replay,
        calibration_report=calibration,
        runtime_rollout_switch=True,
    )

    assert calibration["suggested_thresholds"]["min_offline_score_average"] == 0.3
    assert calibration["ab_observation"]["risk_count"] == 1
    assert gate["eligible_for_runtime"] is False
    assert "ab_no_negative_risk" in gate["failures"]


def test_v20_role_view_policy_calibration_is_in_training_iteration_contract() -> None:
    source = Path(__file__).resolve().parents[1].joinpath("learning", "training_iteration.py").read_text(encoding="utf-8")

    assert "role_view_policy_calibration" in source
    assert "build_role_view_policy_calibration_report" in source
