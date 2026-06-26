from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.validation.real_business_answer_refresh_regression import run_real_business_answer_refresh_regression
from v30.validation.synthetic_case import SyntheticValidationSuiteResult, run_synthetic_tier


REAL_BUSINESS_BOUNDARY_BLOCKED_INPUT_REGRESSION_VERSION = "v30.real_business_boundary_blocked_input_regression.v1"


def run_real_business_boundary_blocked_input_regression(*, case_limit: int = 5) -> dict[str, Any]:
    b3 = run_real_business_answer_refresh_regression(case_limit=5)
    synthetic = run_synthetic_tier("real_case_calibration_pack")
    return build_real_business_boundary_blocked_input_regression(
        b3_answer_refresh_regression=b3,
        synthetic_result=synthetic,
        case_limit=case_limit,
    )


def build_real_business_boundary_blocked_input_regression(
    *,
    b3_answer_refresh_regression: Mapping[str, Any],
    synthetic_result: SyntheticValidationSuiteResult | Mapping[str, Any],
    case_limit: int = 5,
) -> dict[str, Any]:
    payload = (
        synthetic_result.model_dump(mode="json")
        if hasattr(synthetic_result, "model_dump")
        else dict(synthetic_result)
    )
    rows = _non_ready_rows(payload)[: max(1, min(int(case_limit or 5), 5))]
    boundary_rows = [_boundary_row(row) for row in rows]
    summary = _summary(b3_answer_refresh_regression, payload, boundary_rows)
    decision = _decision(summary, boundary_rows)
    return {
        "version": REAL_BUSINESS_BOUNDARY_BLOCKED_INPUT_REGRESSION_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["boundary_blocked_input_ready"] else "blocked",
        "decision": decision,
        "boundary_summary": summary,
        "boundary_rows": boundary_rows,
        "business_scope": {
            "task_id": "B4",
            "title": "Business Reading Boundary And Blocked Input Regression",
            "acceptance_target": "pending and blocked BirthInput states explain missing chart facts without fabrication",
            "required_checks": [
                "b3_answer_refresh_ready",
                "non_ready_cases_metadata_only",
                "no_fake_pillars",
                "no_m4_m5_m6_projection_readiness",
                "conversion_boundary_explainable",
                "privacy_and_no_mutation",
            ],
            "boundary": "b4_regresses_boundary_inputs_not_customer_ui_polish",
        },
        "policy_boundary": {
            "full_pytest_run_by_default": False,
            "full_518k_run_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "training_signal_may_change_chart_facts": False,
            "boundary": "b4_is_read_only_boundary_regression_and_does_not_mutate_chart_facts",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "b4_validates_missing_chart_facts_are_explained_not_fabricated",
    }


def _non_ready_rows(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = payload.get("results", [])
    if not isinstance(rows, list):
        return []
    selected: list[Mapping[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        observed = _mapping(row.get("observed", {}))
        metadata = _mapping(observed.get("production_replay_metadata", {}))
        if str(metadata.get("chart_status") or "") in {"pending", "blocked"}:
            selected.append(row)
    return selected


def _boundary_row(row: Mapping[str, Any]) -> dict[str, Any]:
    observed = _mapping(row.get("observed", {}))
    metadata = _mapping(observed.get("production_replay_metadata", {}))
    fixture = _mapping(observed.get("real_case_fixture", {}))
    conversion = _mapping(observed.get("birth_chart_conversion_boundary", {}))
    drift = _mapping(fixture.get("calibration_drift_summary", {}))
    privacy = _mapping(metadata.get("privacy_guard", {}))
    status = str(metadata.get("chart_status") or fixture.get("status") or conversion.get("status") or "")
    missing_requirements = _str_list(conversion.get("missing_requirements", []))
    boundary_flags = _str_list(conversion.get("boundary_flags", []))
    checks = {
        "synthetic_case_passed": bool(row.get("passed")),
        "status_is_pending_or_blocked": status in {"pending", "blocked"},
        "no_fake_pillars": metadata.get("has_pillars") is False and fixture.get("has_pillars") is False and conversion.get("has_pillars") is False,
        "all_pillars_missing": set(_str_list(conversion.get("missing_pillars", []))) == {"year", "month", "day", "hour"},
        "m4_m5_m6_not_ready": (
            metadata.get("m4_model_signal_ready") is False
            and metadata.get("m5_ranked_decision_ready") is False
            and metadata.get("m6_practical_contract_ready") is False
            and int(metadata.get("m6_practical_domain_contract_count", 0) or 0) == 0
        ),
        "api_projection_not_ready_but_leak_scan_passes": (
            metadata.get("api_projection_contract_ready") is False
            and metadata.get("projection_leak_scan_passed") is True
        ),
        "fixture_no_runtime_outputs": (
            fixture.get("model_signal_ready") is False
            and int(fixture.get("ranked_decision_count", 0) or 0) == 0
            and int(fixture.get("practical_domain_count", 0) or 0) == 0
            and fixture.get("projection_matrix_ready") is False
        ),
        "conversion_boundary_explainable": (
            conversion.get("source_type") == "birth_input"
            and bool(boundary_flags)
            and bool(missing_requirements)
        ),
        "unknown_hour_pending_has_known_hour_requirement": (
            not bool(metadata.get("unknown_hour"))
            or (status == "pending" and "known_birth_hour" in missing_requirements and "unknown_hour_blocks_hour_pillar" in boundary_flags)
        ),
        "blocked_input_has_valid_birth_datetime_requirement": (
            status != "blocked" or "valid_birth_datetime" in missing_requirements
        ),
        "metadata_privacy_no_mutation": (
            privacy.get("metadata_only") is True
            and privacy.get("no_private_user_content") is True
            and privacy.get("no_chart_fact_mutation") is True
            and privacy.get("forbidden_key_scan_passed") is True
        ),
        "drift_summary_stable_no_adjustment": (
            drift.get("version") == "v30.real_case_calibration_drift_summary.v1"
            and drift.get("calibration_status") == "stable"
            and drift.get("drift_flags") == []
            and drift.get("module_adjustment_targets") == []
        ),
    }
    failed = [check_id for check_id, passed in checks.items() if not passed]
    return {
        "case_id": str(row.get("case_id") or ""),
        "chart_status": status,
        "calendar_type": str(metadata.get("calendar_type") or fixture.get("calendar_type") or ""),
        "unknown_hour": bool(metadata.get("unknown_hour") or fixture.get("unknown_hour")),
        "use_true_solar_time": bool(metadata.get("use_true_solar_time") or fixture.get("use_true_solar_time")),
        "boundary_flags": boundary_flags,
        "missing_requirements": missing_requirements,
        "boundary_input_ready": not failed,
        "checks": checks,
        "failed_check_ids": failed,
        "boundary": "b4_case_checks_boundary_input_no_fake_chart_facts",
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _str_list(value: object) -> list[str]:
    return [str(row) for row in value] if isinstance(value, list) else []


def _summary(
    b3: Mapping[str, Any],
    synthetic: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    b3_decision = _mapping(b3.get("decision", {}))
    return {
        "b3_version": str(b3.get("version") or ""),
        "b3_ready": bool(b3_decision.get("answer_refresh_regression_ready")),
        "source_suite_id": str(synthetic.get("suite_id") or ""),
        "source_suite_passed": bool(synthetic.get("passed")),
        "boundary_case_count": len(rows),
        "passed_boundary_case_count": sum(1 for row in rows if row.get("boundary_input_ready")),
        "failed_boundary_case_count": sum(1 for row in rows if not row.get("boundary_input_ready")),
        "pending_count": sum(1 for row in rows if row.get("chart_status") == "pending"),
        "blocked_count": sum(1 for row in rows if row.get("chart_status") == "blocked"),
        "unknown_hour_count": sum(1 for row in rows if row.get("unknown_hour")),
        "true_solar_pending_count": sum(1 for row in rows if row.get("use_true_solar_time")),
        "calendar_types": sorted({str(row.get("calendar_type") or "") for row in rows if row.get("calendar_type")}),
    }


def _decision(summary: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    failed_rows = [row for row in rows if not row.get("boundary_input_ready")]
    blockers: list[str] = []
    if summary.get("b3_version") != "v30.real_business_answer_refresh_regression.v1":
        blockers.append("b3_answer_refresh_regression_missing")
    if not summary.get("b3_ready"):
        blockers.append("b3_answer_refresh_regression_not_ready")
    if summary.get("source_suite_id") != "v30.synthetic.real_case_calibration_pack":
        blockers.append("source_real_case_calibration_pack_missing")
    if not summary.get("source_suite_passed"):
        blockers.append("source_real_case_calibration_pack_not_passing")
    if int(summary.get("boundary_case_count", 0) or 0) < 5:
        blockers.append("boundary_case_count_below_minimum")
    if int(summary.get("pending_count", 0) or 0) < 3:
        blockers.append("pending_boundary_coverage_missing")
    if int(summary.get("blocked_count", 0) or 0) < 2:
        blockers.append("blocked_boundary_coverage_missing")
    if not {"solar", "lunar"}.issubset(set(summary.get("calendar_types", []))):
        blockers.append("calendar_boundary_coverage_missing")
    if int(summary.get("unknown_hour_count", 0) or 0) < 3:
        blockers.append("unknown_hour_boundary_coverage_missing")
    if failed_rows:
        blockers.append("boundary_input_rows_failed")
    ready = not blockers
    return {
        "boundary_blocked_input_ready": ready,
        "decision_status": "b4_boundary_blocked_input_regression_ready" if ready else "b4_boundary_blocked_input_regression_blocked",
        "blockers": blockers,
        "failed_case_ids": [str(row.get("case_id") or "") for row in failed_rows],
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "rationale": (
            "B4 ready: pending and blocked BirthInput states explain missing chart facts without fabricated readings."
            if ready
            else "B4 blocked: repair boundary input explanation or no-fake-fact guard failures."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("boundary_blocked_input_ready"):
        return {
            "task_id": "B5",
            "title": "Business Reading API Contract Freeze",
            "selected_track": "business_bazi_acceptance",
            "scope": [
                "freeze the customer-facing business reading API contract",
                "record B1-B4 as the minimum business acceptance gate",
                "keep full pytest and release promotion explicit",
            ],
        }
    return {
        "task_id": "B4-FR",
        "title": "Boundary And Blocked Input Failure Review",
        "selected_track": "business_bazi_acceptance",
        "scope": [
            "repair failed boundary input rows",
            "do not fabricate chart facts for pending or blocked BirthInput",
            "do not run full pytest unless release/full-freeze is explicitly requested",
        ],
    }
