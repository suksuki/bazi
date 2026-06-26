from __future__ import annotations

from pathlib import Path

from v30.validation import (
    build_m7_real_case_calibration_steady_state_review,
    run_m7_real_case_calibration_steady_state_review,
)


def _m6_closeout(*, blocked: bool = False) -> dict[str, object]:
    ready = not blocked
    return {
        "version": "v30.m6_practical_reading_closeout.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "m6_practical_reading_closed" if ready else "m6_practical_reading_closeout_blocked",
            "m6_practical_reading_closed": ready,
            "m6_ready_for_release_acceptance": ready,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
        },
    }


def _fixture(index: int, *, missing_category: bool = False, drift: bool = False) -> dict[str, object]:
    categories = [
        ("solar", False, False, False, "known"),
        ("lunar", False, False, False, "known"),
        ("lunar", True, False, False, "known"),
        ("solar", False, True, False, "known"),
        ("solar", False, False, True, "known"),
        ("solar", False, False, False, "unknown"),
    ]
    calendar_type, leap, true_solar, unknown_hour, gender_status = categories[index % len(categories)]
    if missing_category:
        calendar_type, leap, true_solar, unknown_hour, gender_status = ("solar", False, False, False, "known")
    ready = not unknown_hour
    contracts = {
        domain: {"raw_score_leak": False}
        for domain in ("career", "wealth", "relationship", "health", "timing")
    } if ready else {}
    return {
        "case_id": f"case-{index}",
        "status": "ready" if ready else "pending",
        "calendar_type": calendar_type,
        "lunar_is_leap_month": leap,
        "use_true_solar_time": true_solar,
        "unknown_hour": unknown_hour,
        "gender_status": gender_status,
        "has_pillars": ready,
        "model_signal_ready": ready,
        "ranked_decision_count": 3 if ready else 0,
        "six_pillar_status": "ready" if ready else "pending",
        "practical_reading_status": "ready" if ready else "natal_only",
        "practical_domain_contracts": contracts,
        "calibration_drift_summary": {
            "version": "v30.real_case_calibration_drift_summary.v1",
            "calibration_status": "needs_module_review" if drift else "stable",
            "drift_flags": ["m7_fixture_drift"] if drift else [],
            "module_adjustment_targets": ["M7"] if drift else [],
            "module_readiness": {"M7_real_case_calibration": not drift},
            "boundary": "real_case_calibration_drift_routes_to_module_adjustments_not_chart_fact_mutation",
        },
    }


def _metadata(index: int, *, privacy_fail: bool = False) -> dict[str, object]:
    statuses = ["ready"] * 24 + ["pending"] * 3 + ["blocked"] * 3
    calendars = ["solar", "lunar"] * 15
    return {
        "version": "v30.production_replay_metadata.v1",
        "calendar_type": calendars[index % len(calendars)],
        "lunar_is_leap_month": index == 2,
        "use_true_solar_time": index == 3,
        "unknown_hour": index == 4,
        "unknown_gender": index == 5,
        "chart_status": statuses[index % len(statuses)],
        "m4_model_signal_ready": index < 24,
        "m5_ranked_decision_ready": index < 24,
        "m6_practical_contract_ready": index < 24,
        "api_projection_contract_ready": True,
        "projection_leak_scan_passed": not privacy_fail,
        "privacy_guard": {
            "metadata_only": True,
            "no_private_user_content": True,
            "no_chart_fact_mutation": True,
            "forbidden_key_scan_passed": not privacy_fail,
        },
        "boundary": "production_replay_metadata_tags_do_not_import_private_content_or_mutate_chart_facts",
    }


def _suite(*, missing_category: bool = False, privacy_fail: bool = False, drift: bool = False) -> dict[str, object]:
    return {
        "suite_id": "v30.synthetic.real_case_calibration_pack",
        "passed": True,
        "case_count": 30,
        "passed_count": 30,
        "failed_count": 0,
        "results": [
            {
                "case_id": f"case-{index}",
                "passed": True,
                "failures": [],
                "observed": {
                    "real_case_fixture": _fixture(index, missing_category=missing_category, drift=drift),
                    "production_replay_metadata": _metadata(index, privacy_fail=privacy_fail),
                },
            }
            for index in range(30)
        ],
    }


def _signals(*, missing: bool = False) -> list[dict[str, object]]:
    if missing:
        return []
    return [
        {
            "signal_id": "v30.training_signal.real_case_calibration_pack",
            "domain": "real_case_validation",
            "signal_type": "canonical_fixture_calibration_coverage",
            "strength": 1.0,
            "source_case_ids": ["case-1"],
            "payload": {
                "case_count": 30,
                "ready_count": 24,
                "m7_calibration_drift_summary_count": 30,
                "m7_calibration_stable_count": 30,
                "m7_calibration_needs_module_review_count": 0,
                "production_replay_metadata_count": 30,
                "production_replay_metadata_privacy_guard_pass_count": 30,
                "production_replay_metadata_projection_leak_pass_count": 30,
                "boundary": "real_case_calibration_pack_trains_validation_policy_not_chart_facts",
            },
        }
    ]


def _build(**overrides):
    payload = {
        "m6_closeout": _m6_closeout(),
        "real_case_synthetic": _suite(),
        "training_signals": _signals(),
    }
    payload.update(overrides)
    return build_m7_real_case_calibration_steady_state_review(**payload)


def test_m7_real_case_calibration_steady_state_review_ready(tmp_path: Path) -> None:
    result = _build(artifact_dir=tmp_path)
    decision = result["decision"]

    assert result["version"] == "v30.m7_real_case_calibration_steady_state_review.v1"
    assert result["status"] == "completed"
    assert decision["decision_status"] == "m7_real_case_calibration_steady_state_ready"
    assert decision["ready_for_m7_closeout"] is True
    assert decision["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["next_task"] == "M7 Real-Case Calibration Closeout"
    assert Path(str(result["artifact_uri"])).exists()


def test_m7_review_blocks_missing_m6_closeout() -> None:
    result = _build(m6_closeout=_m6_closeout(blocked=True))

    assert result["status"] == "blocked"
    assert "m6_closeout_ready_for_m7" in result["decision"]["failed_review_check_ids"]


def test_m7_review_blocks_missing_canonical_category() -> None:
    result = _build(real_case_synthetic=_suite(missing_category=True))

    assert result["status"] == "blocked"
    assert "real_case_pack_canonical_coverage_complete" in result["decision"]["failed_review_check_ids"]


def test_m7_review_blocks_metadata_privacy_failure() -> None:
    result = _build(real_case_synthetic=_suite(privacy_fail=True))

    assert result["status"] == "blocked"
    assert "production_replay_metadata_privacy_ready" in result["decision"]["failed_review_check_ids"]


def test_m7_review_blocks_drift_request() -> None:
    result = _build(real_case_synthetic=_suite(drift=True))

    assert result["status"] == "blocked"
    assert "real_case_drift_stable_no_module_adjustment" in result["decision"]["failed_review_check_ids"]


def test_m7_review_blocks_missing_training_signal() -> None:
    result = _build(training_signals=_signals(missing=True))

    assert result["status"] == "blocked"
    assert "real_case_training_signal_boundary_locked" in result["decision"]["failed_review_check_ids"]


def test_m7_real_case_calibration_runner_passes_targeted_gates(tmp_path: Path) -> None:
    result = run_m7_real_case_calibration_steady_state_review(sample_limit=8, artifact_dir=tmp_path)

    assert result["decision"]["decision_status"] == "m7_real_case_calibration_steady_state_ready"
    assert result["decision"]["real_case_fixture_count"] >= 30
