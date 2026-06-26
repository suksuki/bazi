from __future__ import annotations

from copy import deepcopy

from v30.validation.real_business_boundary_blocked_input_regression import (
    REAL_BUSINESS_BOUNDARY_BLOCKED_INPUT_REGRESSION_VERSION,
    build_real_business_boundary_blocked_input_regression,
)


def _b3_ready() -> dict[str, object]:
    return {
        "version": "v30.real_business_answer_refresh_regression.v1",
        "decision": {
            "answer_refresh_regression_ready": True,
        },
    }


def _boundary_case(
    case_id: str,
    *,
    status: str,
    calendar_type: str = "solar",
    unknown_hour: bool = False,
    true_solar: bool = False,
) -> dict[str, object]:
    missing = ["known_birth_hour"] if unknown_hour else ["valid_birth_datetime"]
    missing.extend(["deterministic_calendar_conversion_engine", "solar_term_boundary_table", "late_zi_hour_policy"])
    flags = ["solar_term_boundary_requires_engine", "late_zi_hour_boundary_requires_policy", "timezone_assumption_recorded"]
    if unknown_hour:
        flags.append("unknown_hour_blocks_hour_pillar")
    if true_solar:
        flags.append("true_solar_time_requires_location_resolution")
    return {
        "case_id": case_id,
        "passed": True,
        "failures": [],
        "observed": {
            "production_replay_metadata": {
                "chart_status": status,
                "calendar_type": calendar_type,
                "unknown_hour": unknown_hour,
                "use_true_solar_time": true_solar,
                "has_pillars": False,
                "m4_model_signal_ready": False,
                "m5_ranked_decision_ready": False,
                "m6_practical_contract_ready": False,
                "m6_practical_domain_contract_count": 0,
                "api_projection_contract_ready": False,
                "projection_leak_scan_passed": True,
                "privacy_guard": {
                    "metadata_only": True,
                    "no_private_user_content": True,
                    "no_chart_fact_mutation": True,
                    "forbidden_key_scan_passed": True,
                },
            },
            "birth_chart_conversion_boundary": {
                "status": status,
                "source_type": "birth_input",
                "has_pillars": False,
                "missing_pillars": ["year", "month", "day", "hour"],
                "boundary_flags": flags,
                "missing_requirements": missing,
            },
            "real_case_fixture": {
                "status": status,
                "calendar_type": calendar_type,
                "unknown_hour": unknown_hour,
                "use_true_solar_time": true_solar,
                "has_pillars": False,
                "model_signal_ready": False,
                "ranked_decision_count": 0,
                "practical_domain_count": 0,
                "projection_matrix_ready": False,
                "calibration_drift_summary": {
                    "version": "v30.real_case_calibration_drift_summary.v1",
                    "calibration_status": "stable",
                    "drift_flags": [],
                    "module_adjustment_targets": [],
                },
            },
        },
    }


def _suite(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "suite_id": "v30.synthetic.real_case_calibration_pack",
        "passed": all(row["passed"] for row in rows),
        "case_count": len(rows),
        "passed_count": sum(1 for row in rows if row["passed"]),
        "failed_count": sum(1 for row in rows if not row["passed"]),
        "results": rows,
    }


def _boundary_rows() -> list[dict[str, object]]:
    return [
        _boundary_case("pending_solar_unknown_hour", status="pending", calendar_type="solar", unknown_hour=True),
        _boundary_case("pending_lunar_unknown_hour", status="pending", calendar_type="lunar", unknown_hour=True),
        _boundary_case("pending_true_solar_unknown_hour", status="pending", calendar_type="solar", unknown_hour=True, true_solar=True),
        _boundary_case("blocked_invalid_date", status="blocked", calendar_type="solar"),
        _boundary_case("blocked_invalid_time", status="blocked", calendar_type="solar"),
    ]


def test_b4_boundary_blocked_input_regression_accepts_non_ready_no_fake_fact_cases() -> None:
    result = build_real_business_boundary_blocked_input_regression(
        b3_answer_refresh_regression=_b3_ready(),
        synthetic_result=_suite(_boundary_rows()),
    )

    assert result["version"] == REAL_BUSINESS_BOUNDARY_BLOCKED_INPUT_REGRESSION_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "b4_boundary_blocked_input_regression_ready"
    assert result["boundary_summary"]["pending_count"] == 3
    assert result["boundary_summary"]["blocked_count"] == 2
    assert result["boundary_summary"]["unknown_hour_count"] == 3
    assert result["next_mainline_selection"]["task_id"] == "B5"
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False


def test_b4_blocks_fake_pillars_or_premature_runtime_readiness() -> None:
    rows = _boundary_rows()
    broken = deepcopy(rows[0])
    observed = broken["observed"]
    assert isinstance(observed, dict)
    metadata = observed["production_replay_metadata"]
    conversion = observed["birth_chart_conversion_boundary"]
    assert isinstance(metadata, dict)
    assert isinstance(conversion, dict)
    metadata["has_pillars"] = True
    metadata["m5_ranked_decision_ready"] = True
    conversion["has_pillars"] = True
    rows[0] = broken

    result = build_real_business_boundary_blocked_input_regression(
        b3_answer_refresh_regression=_b3_ready(),
        synthetic_result=_suite(rows),
    )

    failed = result["boundary_rows"][0]
    assert result["status"] == "blocked"
    assert "boundary_input_rows_failed" in result["decision"]["blockers"]
    assert "no_fake_pillars" in failed["failed_check_ids"]
    assert "m4_m5_m6_not_ready" in failed["failed_check_ids"]
