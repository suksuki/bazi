from __future__ import annotations

from pathlib import Path

from v30.validation import (
    build_m5_calibration_replay_closeout,
    run_m5_calibration_replay_closeout,
)


def _review(
    *,
    blocked: bool = False,
    bad_training_boundary: bool = False,
    threshold_write: bool = False,
) -> dict[str, object]:
    ready = not blocked
    return {
        "version": "v30.m5_calibration_replay_review.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "m5_calibration_replay_review_ready" if ready else "m5_calibration_replay_review_blocked",
            "m5_calibration_replay_review_ready": ready,
            "ready_for_m5_calibration_replay_closeout": ready,
            "ready_for_threshold_change": False,
            "ranked_observation_count": 51,
            "complete_domain_observation_count": 51,
            "close_candidate_count": 51,
            "review_check_count": 6,
            "passed_review_check_count": 6 if ready else 5,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "threshold_write_performed": threshold_write,
        },
        "evidence_hardening_summary": {
            "m5_evidence_consumption_ready": True,
        },
        "synthetic_summary": {
            "required_tier_count": 3,
            "passed_tier_count": 3,
            "case_count_total": 61,
        },
        "ranked_decision_replay_summary": {
            "ranked_observation_count": 51,
            "complete_domain_observation_count": 51,
            "close_candidate_count": 51,
            "domains_with_primary_candidates": ["strength", "structure_pattern", "useful_god"],
            "domains_with_candidate_scores": ["strength", "structure_pattern", "useful_god"],
            "basis_signal_counts": {
                "follow_structure_boundary_signal": 18,
                "disputed_structure_signal": 9,
                "non_unique_candidate_signal": 51,
            },
            "top_gap_summary": {
                "strength": {"count": 51, "min": 0.01, "average": 0.04, "close_count": 51},
                "structure_pattern": {"count": 51, "min": 0.02, "average": 0.05, "close_count": 51},
                "useful_god": {"count": 51, "min": 0.01, "average": 0.04, "close_count": 51},
            },
        },
        "training_signal_summary": {
            "m5_weight_replay_present": True,
            "m5_weight_replay_boundary": (
                "bad_boundary"
                if bad_training_boundary
                else "m5_weight_replay_trains_candidate_weights_not_chart_facts"
            ),
        },
    }


def test_m5_calibration_replay_closeout_ready(tmp_path: Path) -> None:
    result = build_m5_calibration_replay_closeout(
        replay_review=_review(),
        artifact_dir=tmp_path,
    )
    decision = result["decision"]

    assert result["version"] == "v30.m5_calibration_replay_closeout.v1"
    assert result["status"] == "completed"
    assert decision["decision_status"] == "m5_calibration_replay_closed"
    assert decision["m5_ranked_decision_steady_support_ready"] is True
    assert decision["m5_ready_for_m6_consumption"] is True
    assert decision["threshold_change_allowed"] is False
    assert result["next_mainline_selection"]["next_task"] == "M6 Practical Reading Consumption Hardening"
    assert Path(str(result["artifact_uri"])).exists()


def test_m5_calibration_replay_closeout_blocks_missing_h2() -> None:
    result = build_m5_calibration_replay_closeout(replay_review=_review(blocked=True))

    assert result["status"] == "blocked"
    assert result["decision"]["m5_calibration_replay_closed"] is False
    assert "m5_h2_replay_review_ready" in result["decision"]["failed_closeout_check_ids"]


def test_m5_calibration_replay_closeout_blocks_bad_training_boundary() -> None:
    result = build_m5_calibration_replay_closeout(
        replay_review=_review(bad_training_boundary=True)
    )

    assert result["status"] == "blocked"
    assert "m5_training_signal_boundary_locked" in result["decision"]["failed_closeout_check_ids"]


def test_m5_calibration_replay_closeout_blocks_threshold_write() -> None:
    result = build_m5_calibration_replay_closeout(
        replay_review=_review(threshold_write=True)
    )

    assert result["status"] == "blocked"
    assert "m5_no_write_boundary_preserved" in result["decision"]["failed_closeout_check_ids"]


def test_m5_calibration_replay_closeout_runner_passes_targeted_gates(tmp_path: Path) -> None:
    result = run_m5_calibration_replay_closeout(sample_limit=8, artifact_dir=tmp_path)

    assert result["decision"]["decision_status"] == "m5_calibration_replay_closed"
    assert result["decision"]["m5_ready_for_m6_consumption"] is True
    assert result["decision"]["ranked_observation_count"] >= 30
