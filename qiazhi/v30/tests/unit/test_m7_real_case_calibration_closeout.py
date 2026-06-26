from __future__ import annotations

from pathlib import Path

from v30.validation import (
    build_m7_real_case_calibration_closeout,
    run_m7_real_case_calibration_closeout,
)


def _review(
    *,
    blocked: bool = False,
    missing_category: bool = False,
    drift: bool = False,
    metadata_fail: bool = False,
    training_fail: bool = False,
) -> dict[str, object]:
    ready = not blocked
    categories = ["solar", "lunar", "leap_month_lunar", "true_solar", "unknown_hour", "unknown_gender"]
    if missing_category:
        categories = ["solar", "lunar"]
    return {
        "version": "v30.m7_real_case_calibration_steady_state_review.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "m7_real_case_calibration_steady_state_ready" if ready else "m7_real_case_calibration_steady_state_blocked",
            "m7_steady_state_review_ready": ready,
            "m7_real_case_calibration_steady": ready,
            "ready_for_m7_closeout": ready,
            "review_check_count": 7,
            "passed_review_check_count": 7 if ready else 6,
            "real_case_fixture_count": 30,
            "focused_real_case_expansion_recommended": True,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
        },
        "real_case_calibration_summary": {
            "fixture_count": 30,
            "covered_categories": categories,
            "ready_count": 25,
            "pending_or_blocked_count": 5,
            "no_fake_fact_count": 5,
            "drift_summary_count": 30,
            "drift_stable_count": 29 if drift else 30,
            "drift_needs_module_review_count": 1 if drift else 0,
            "drift_flag_counts": {"m7_drift": 1} if drift else {},
            "module_adjustment_counts": {"M7": 1} if drift else {},
        },
        "production_replay_metadata_summary": {
            "row_count": 30,
            "privacy_guard_pass_count": 29 if metadata_fail else 30,
            "projection_leak_scan_pass_count": 29 if metadata_fail else 30,
        },
        "training_signal_summary": {
            "real_case_calibration_signal_present": not training_fail,
            "boundary": (
                "bad_boundary"
                if training_fail
                else "real_case_calibration_pack_trains_validation_policy_not_chart_facts"
            ),
        },
    }


def test_m7_real_case_calibration_closeout_ready(tmp_path: Path) -> None:
    result = build_m7_real_case_calibration_closeout(
        steady_state_review=_review(),
        artifact_dir=tmp_path,
    )
    decision = result["decision"]

    assert result["version"] == "v30.m7_real_case_calibration_closeout.v1"
    assert result["status"] == "completed"
    assert decision["decision_status"] == "m7_real_case_calibration_closed"
    assert decision["m7_calibration_backbone_ready"] is True
    assert decision["focused_real_case_expansion_recommended"] is True
    assert decision["focused_real_case_expansion_blocks_current_flow"] is False
    assert decision["m7_ready_for_m8_projection_api_closeout"] is True
    assert result["next_mainline_selection"]["next_task"] == "M8 Projection/API Contract Closeout"
    assert Path(str(result["artifact_uri"])).exists()


def test_m7_closeout_blocks_missing_s1() -> None:
    result = build_m7_real_case_calibration_closeout(steady_state_review=_review(blocked=True))

    assert result["status"] == "blocked"
    assert "m7_s1_steady_state_review_ready" in result["decision"]["failed_closeout_check_ids"]


def test_m7_closeout_blocks_canonical_gap() -> None:
    result = build_m7_real_case_calibration_closeout(steady_state_review=_review(missing_category=True))

    assert result["status"] == "blocked"
    assert "m7_canonical_backbone_ready" in result["decision"]["failed_closeout_check_ids"]


def test_m7_closeout_blocks_drift_or_metadata_gap() -> None:
    drift_result = build_m7_real_case_calibration_closeout(steady_state_review=_review(drift=True))
    metadata_result = build_m7_real_case_calibration_closeout(steady_state_review=_review(metadata_fail=True))

    assert drift_result["status"] == "blocked"
    assert metadata_result["status"] == "blocked"
    assert "m7_drift_and_metadata_stable" in drift_result["decision"]["failed_closeout_check_ids"]
    assert "m7_drift_and_metadata_stable" in metadata_result["decision"]["failed_closeout_check_ids"]


def test_m7_closeout_blocks_training_boundary_gap() -> None:
    result = build_m7_real_case_calibration_closeout(steady_state_review=_review(training_fail=True))

    assert result["status"] == "blocked"
    assert "m7_training_boundary_locked" in result["decision"]["failed_closeout_check_ids"]


def test_m7_real_case_calibration_closeout_runner_passes_targeted_gates(tmp_path: Path) -> None:
    result = run_m7_real_case_calibration_closeout(sample_limit=8, artifact_dir=tmp_path)

    assert result["decision"]["decision_status"] == "m7_real_case_calibration_closed"
    assert result["decision"]["real_case_fixture_count"] >= 30
    assert result["decision"]["m7_ready_for_m8_projection_api_closeout"] is True
