from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.synthetic_typical_answer_training_signal_review import (
    SYNTHETIC_TYPICAL_ANSWER_TRAINING_SIGNAL_REVIEW_VERSION,
    run_synthetic_typical_answer_training_signal_review,
)
from v30.validation.synthetic_typical_bazi_answer_calibration import SYNTHETIC_TYPICAL_BAZI_ANSWER_CALIBRATION_VERSION


SYNTHETIC_TYPICAL_ANSWER_CALIBRATION_CLOSEOUT_VERSION = "v30.synthetic_typical_answer_calibration_closeout.v1"


def run_synthetic_typical_answer_calibration_closeout() -> dict[str, Any]:
    return build_synthetic_typical_answer_calibration_closeout(
        training_signal_review=run_synthetic_typical_answer_training_signal_review()
    )


def build_synthetic_typical_answer_calibration_closeout(
    *,
    training_signal_review: Mapping[str, Any],
) -> dict[str, Any]:
    closed_at = datetime.now(timezone.utc)
    core_cal_s2 = _training_signal_review_summary(training_signal_review)
    upstream = _mapping(training_signal_review.get("upstream_summary"))
    core_cal_s1 = _mapping(upstream.get("typical_answer_calibration"))
    synthetic_tier = _mapping(upstream.get("synthetic_tier"))
    case_summary = _mapping(upstream.get("case_summary"))
    cadence = _routine_cadence(core_cal_s2)
    closeout_checks = _closeout_checks(
        core_cal_s1=core_cal_s1,
        core_cal_s2=core_cal_s2,
        synthetic_tier=synthetic_tier,
        case_summary=case_summary,
        cadence=cadence,
    )
    decision = _decision(closeout_checks, core_cal_s2)
    return {
        "version": SYNTHETIC_TYPICAL_ANSWER_CALIBRATION_CLOSEOUT_VERSION,
        "closed_at": closed_at.isoformat(),
        "status": "completed" if decision["synthetic_typical_answer_calibration_closed"] else "blocked",
        "task": {
            "task_id": "CORE-CAL-S3",
            "title": "Synthetic Typical Answer Calibration Closeout",
            "scope": "freeze_CORE_CAL_S1_to_S2_evidence_and_define_answer_calibration_cadence",
        },
        "frozen_evidence": {
            "core_cal_s1_typical_answer_calibration": core_cal_s1,
            "core_cal_s2_training_signal_review": core_cal_s2,
            "synthetic_typical_bazi_answer_tier": synthetic_tier,
            "case_summary": case_summary,
        },
        "routine_cadence": cadence,
        "closeout_checks": closeout_checks,
        "decision": decision,
        "policy_boundary": {
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "external_release_allowed": False,
            "real_person_truth_label_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
            "boundary": "core_cal_s3_closes_answer_calibration_without_runtime_mutation_or_release_authorization",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "core_cal_s3_closes_synthetic_typical_answer_calibration_as_targeted_validation_not_truth_training",
    }


def _training_signal_review_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    signals = [_mapping(row) for row in _list(payload.get("training_signals"))]
    queue_rows = [_mapping(row) for row in _list(payload.get("calibration_queue_items"))]
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "ready": bool(decision.get("synthetic_typical_answer_training_signal_review_ready")),
        "check_count": int(decision.get("check_count", 0) or 0),
        "passed_check_count": int(decision.get("passed_check_count", 0) or 0),
        "training_signal_count": int(decision.get("training_signal_count", len(signals)) or 0),
        "queued_item_count": int(decision.get("queued_item_count", len(queue_rows)) or 0),
        "signal_ids": sorted(str(row.get("signal_id") or "") for row in signals if row.get("signal_id")),
        "target_modules": sorted(
            {str(module) for row in signals for module in _str_list(row.get("target_modules"))}
        ),
        "signals_review_only": all(_readonly(row) for row in signals),
        "queue_review_only": all(_readonly(row) for row in queue_rows),
        "external_release_allowed": bool(decision.get("external_release_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "auto_apply_training_allowed": bool(decision.get("auto_apply_training_allowed")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "synthetic_all_required": bool(decision.get("synthetic_all_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "live_llm_required": bool(decision.get("live_llm_required")),
    }


def _routine_cadence(core_cal_s2: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "version": "v30.synthetic_typical_answer_calibration_cadence.v1",
        "routine_targeted_commands": [
            "python3 scripts/run_synthetic_typical_bazi_answer_calibration.py",
            "python3 scripts/run_synthetic_validation.py --tier synthetic_typical_bazi_answer",
            "python3 scripts/run_synthetic_typical_answer_training_signal_review.py",
            "python3 scripts/run_synthetic_typical_answer_calibration_closeout.py",
        ],
        "run_when": [
            "M3 knowledge/rule/portrait guidance text changes",
            "M6 practical reading or answer composer wording changes",
            "LLM prompt/context or acceptance boundary changes",
            "interaction answer refresh or question outcome changes",
            "before major-node full validation",
        ],
        "heavy_gates_explicit_only": [
            "pytest -q",
            "python3 scripts/run_synthetic_validation.py --tier all",
            "python3 scripts/run_518k_validation.py --mode full",
            "live LLM smoke",
        ],
        "calibration_queue_policy": {
            "queue_item_count": int(core_cal_s2.get("queued_item_count", 0) or 0),
            "review_only": True,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
        },
        "boundary": "routine_cadence_targets_typical_answer_quality_without_default_heavy_gates",
    }


def _closeout_checks(
    *,
    core_cal_s1: Mapping[str, Any],
    core_cal_s2: Mapping[str, Any],
    synthetic_tier: Mapping[str, Any],
    case_summary: Mapping[str, Any],
    cadence: Mapping[str, Any],
) -> list[dict[str, Any]]:
    required_signals = {
        "v30.training_signal.synthetic_typical_answer_m3_guidance_sanitization",
        "v30.training_signal.synthetic_typical_answer_m6_domain_mechanism_specificity",
        "v30.training_signal.synthetic_typical_answer_llm_expression_boundary",
        "v30.training_signal.synthetic_typical_answer_interaction_answer_alignment",
        "v30.training_signal.synthetic_typical_answer_review_boundary_safety",
    }
    return [
        {
            "check_id": "core_cal_s1_evidence_frozen_ready",
            "passed": core_cal_s1.get("version") == SYNTHETIC_TYPICAL_BAZI_ANSWER_CALIBRATION_VERSION
            and core_cal_s1.get("ready") is True
            and int(core_cal_s1.get("case_count", 0) or 0) >= 5
            and int(core_cal_s1.get("failed_case_count", 0) or 0) == 0,
            "observed": core_cal_s1,
        },
        {
            "check_id": "synthetic_typical_answer_tier_frozen_ready",
            "passed": synthetic_tier.get("suite_id") == "v30.synthetic.synthetic_typical_bazi_answer"
            and synthetic_tier.get("passed") is True
            and int(synthetic_tier.get("case_count", 0) or 0) >= 3,
            "observed": synthetic_tier,
        },
        {
            "check_id": "core_cal_s2_training_signals_frozen_ready",
            "passed": core_cal_s2.get("version") == SYNTHETIC_TYPICAL_ANSWER_TRAINING_SIGNAL_REVIEW_VERSION
            and core_cal_s2.get("ready") is True
            and required_signals <= set(_str_list(core_cal_s2.get("signal_ids")))
            and set(_str_list(core_cal_s2.get("target_modules"))) <= {"M3", "M6", "LLM", "interaction"}
            and core_cal_s2.get("signals_review_only") is True,
            "observed": core_cal_s2,
        },
        {
            "check_id": "case_summary_has_complete_typical_answer_pass",
            "passed": int(case_summary.get("case_count", 0) or 0) >= 5
            and int(case_summary.get("failed_case_count", 0) or 0) == 0
            and float(case_summary.get("pass_ratio", 0.0) or 0.0) >= 1.0,
            "observed": case_summary,
        },
        {
            "check_id": "routine_cadence_defined",
            "passed": cadence.get("version") == "v30.synthetic_typical_answer_calibration_cadence.v1"
            and len(_list(cadence.get("routine_targeted_commands"))) >= 4
            and len(_list(cadence.get("heavy_gates_explicit_only"))) >= 4
            and _mapping(cadence.get("calibration_queue_policy")).get("review_only") is True,
            "observed": cadence,
        },
        {
            "check_id": "mutation_release_heavy_boundaries_locked",
            "passed": core_cal_s2.get("external_release_allowed") is False
            and core_cal_s2.get("chart_fact_mutation_allowed") is False
            and core_cal_s2.get("auto_apply_training_allowed") is False
            and core_cal_s2.get("policy_pointer_promotion_allowed") is False
            and core_cal_s2.get("full_pytest_required") is False
            and core_cal_s2.get("synthetic_all_required") is False
            and core_cal_s2.get("full_518k_required") is False
            and core_cal_s2.get("live_llm_required") is False,
            "observed": {
                "external_release_allowed": core_cal_s2.get("external_release_allowed"),
                "chart_fact_mutation_allowed": core_cal_s2.get("chart_fact_mutation_allowed"),
                "auto_apply_training_allowed": core_cal_s2.get("auto_apply_training_allowed"),
                "policy_pointer_promotion_allowed": core_cal_s2.get("policy_pointer_promotion_allowed"),
                "full_pytest_required": core_cal_s2.get("full_pytest_required"),
                "synthetic_all_required": core_cal_s2.get("synthetic_all_required"),
                "full_518k_required": core_cal_s2.get("full_518k_required"),
                "live_llm_required": core_cal_s2.get("live_llm_required"),
            },
        },
    ]


def _decision(checks: list[Mapping[str, Any]], core_cal_s2: Mapping[str, Any]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "synthetic_typical_answer_calibration_closed": ready,
        "decision_status": "core_cal_s3_synthetic_typical_answer_calibration_closed"
        if ready
        else "core_cal_s3_synthetic_typical_answer_calibration_blocked",
        "closeout_check_count": len(checks),
        "passed_closeout_check_count": len(checks) - len(failed),
        "failed_closeout_check_ids": failed,
        "blockers": ["synthetic_typical_answer_closeout_checks_failed"] if failed else [],
        "training_signal_count": int(core_cal_s2.get("training_signal_count", 0) or 0),
        "queued_item_count": int(core_cal_s2.get("queued_item_count", 0) or 0),
        "external_release_allowed": False,
        "chart_fact_mutation_allowed": False,
        "auto_apply_training_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "live_llm_required": False,
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("synthetic_typical_answer_calibration_closed") is True:
        return {
            "task_id": "CORE-CAL-S4",
            "title": "Core Answer Calibration Steady-State Queue",
            "selected_track": "core_answer_calibration",
            "scope": [
                "keep typical-answer tier as routine targeted gate",
                "wait for new answer-quality evidence before changing M3/M6/LLM/interaction logic",
                "run full pytest/synthetic-all/518K only at major nodes",
            ],
        }
    return {
        "task_id": "CORE-CAL-S3-FR",
        "title": "Synthetic Typical Answer Closeout Failure Review",
        "selected_track": "core_answer_calibration",
        "scope": [
            "repair failed closeout checks",
            "do not promote pointers or mutate chart facts while blocked",
        ],
    }


def _readonly(row: Mapping[str, Any]) -> bool:
    return (
        row.get("review_only") is True
        and row.get("chart_fact_mutation_allowed") is False
        and row.get("auto_apply_training_allowed") is False
        and row.get("policy_pointer_promotion_allowed") is False
        and row.get("external_release_allowed") is False
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _str_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(row) for row in value if str(row)]
    return []
