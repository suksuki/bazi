from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.synthetic_archetype_rule_claim_calibration import (
    SYNTHETIC_ARCHETYPE_RULE_CLAIM_CALIBRATION_VERSION,
)
from v30.validation.synthetic_archetype_tier_registration import SYNTHETIC_ARCHETYPE_TIER_REGISTRATION_VERSION
from v30.validation.synthetic_archetype_training_signal_review import (
    SYNTHETIC_ARCHETYPE_TRAINING_SIGNAL_REVIEW_VERSION,
    run_synthetic_archetype_training_signal_review,
)


SYNTHETIC_ARCHETYPE_CALIBRATION_CLOSEOUT_VERSION = "v30.synthetic_archetype_calibration_closeout.v1"


def run_synthetic_archetype_calibration_closeout() -> dict[str, Any]:
    training_signal_review = run_synthetic_archetype_training_signal_review()
    return build_synthetic_archetype_calibration_closeout(training_signal_review=training_signal_review)


def build_synthetic_archetype_calibration_closeout(
    *,
    training_signal_review: Mapping[str, Any],
) -> dict[str, Any]:
    closed_at = datetime.now(timezone.utc)
    syn_cal3 = _training_signal_review_summary(training_signal_review)
    upstream = _mapping(training_signal_review.get("upstream_summary"))
    syn_cal2 = _mapping(upstream.get("tier_registration"))
    syn_cal1 = _mapping(upstream.get("archetype_calibration"))
    case_summary = _mapping(upstream.get("case_summary"))
    cadence = _routine_cadence(syn_cal3)
    closeout_checks = _closeout_checks(
        syn_cal1=syn_cal1,
        syn_cal2=syn_cal2,
        syn_cal3=syn_cal3,
        case_summary=case_summary,
        cadence=cadence,
    )
    decision = _decision(closeout_checks, syn_cal3)
    return {
        "version": SYNTHETIC_ARCHETYPE_CALIBRATION_CLOSEOUT_VERSION,
        "closed_at": closed_at.isoformat(),
        "status": "completed" if decision["synthetic_archetype_calibration_closed"] else "blocked",
        "task": {
            "task_id": "SYN-CAL4",
            "title": "Synthetic Archetype Calibration Closeout",
            "scope": "freeze_SYN_CAL1_to_SYN_CAL3_evidence_and_define_targeted_routine_cadence",
        },
        "frozen_evidence": {
            "syn_cal1_archetype_calibration": syn_cal1,
            "syn_cal2_tier_registration": syn_cal2,
            "syn_cal3_training_signal_review": syn_cal3,
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
            "boundary": "syn_cal4_closeout_freezes_synthetic_archetype_evidence_without_runtime_mutation_or_release_authorization",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "syn_cal4_closes_synthetic_archetype_calibration_as_targeted_validation_not_truth_label_training",
    }


def _training_signal_review_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    signal_rows = [_mapping(row) for row in _list(payload.get("training_signals"))]
    queue_rows = [_mapping(row) for row in _list(payload.get("calibration_queue_items"))]
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "ready": bool(decision.get("synthetic_archetype_training_signal_review_ready")),
        "check_count": int(decision.get("check_count", 0) or 0),
        "passed_check_count": int(decision.get("passed_check_count", 0) or 0),
        "training_signal_count": int(decision.get("training_signal_count", len(signal_rows)) or 0),
        "queued_item_count": int(decision.get("queued_item_count", len(queue_rows)) or 0),
        "signal_ids": sorted(str(row.get("signal_id") or "") for row in signal_rows if row.get("signal_id")),
        "target_modules": sorted({
            str(module)
            for row in signal_rows
            for module in _str_list(row.get("target_modules"))
        }),
        "signals_review_only": all(_readonly(row) for row in signal_rows),
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


def _routine_cadence(syn_cal3: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "version": "v30.synthetic_archetype_calibration_cadence.v1",
        "routine_targeted_commands": [
            "python3 scripts/run_synthetic_validation.py --tier synthetic_archetype_rule_claim",
            "python3 scripts/run_synthetic_archetype_training_signal_review.py",
            "python3 scripts/run_synthetic_archetype_calibration_closeout.py",
        ],
        "run_when": [
            "M3 knowledge/rule/portrait/path logic changes",
            "M5 ranked decision scoring or candidate policy changes",
            "M6 practical reading claim specificity changes",
            "training signal routing changes",
            "before major-node full validation",
        ],
        "heavy_gates_explicit_only": [
            "pytest -q",
            "python3 scripts/run_synthetic_validation.py --tier all",
            "python3 scripts/run_518k_validation.py --mode full",
            "live LLM smoke",
        ],
        "calibration_queue_policy": {
            "queue_item_count": int(syn_cal3.get("queued_item_count", 0) or 0),
            "review_only": True,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
        },
        "boundary": "routine_cadence_targets_synthetic_archetypes_without_default_heavy_gates",
    }


def _closeout_checks(
    *,
    syn_cal1: Mapping[str, Any],
    syn_cal2: Mapping[str, Any],
    syn_cal3: Mapping[str, Any],
    case_summary: Mapping[str, Any],
    cadence: Mapping[str, Any],
) -> list[dict[str, Any]]:
    required_signals = {
        "v30.training_signal.synthetic_archetype_m3_rule_claim_coverage",
        "v30.training_signal.synthetic_archetype_m5_ranked_candidate_alignment",
        "v30.training_signal.synthetic_archetype_m6_practical_claim_specificity",
        "v30.training_signal.synthetic_archetype_review_boundary_safety",
    }
    return [
        {
            "check_id": "syn_cal1_evidence_frozen_ready",
            "passed": syn_cal1.get("version") == SYNTHETIC_ARCHETYPE_RULE_CLAIM_CALIBRATION_VERSION
            and syn_cal1.get("ready") is True
            and int(syn_cal1.get("case_count", 0) or 0) >= 4
            and int(syn_cal1.get("passed_case_count", 0) or 0) >= 4,
            "observed": syn_cal1,
        },
        {
            "check_id": "syn_cal2_tier_frozen_ready",
            "passed": syn_cal2.get("version") == SYNTHETIC_ARCHETYPE_TIER_REGISTRATION_VERSION
            and syn_cal2.get("ready") is True
            and syn_cal2.get("targeted_tier") == "synthetic_archetype_rule_claim"
            and syn_cal2.get("routine_targeted_gate") is True
            and syn_cal2.get("included_in_synthetic_all") is False,
            "observed": syn_cal2,
        },
        {
            "check_id": "syn_cal3_training_signals_frozen_ready",
            "passed": syn_cal3.get("version") == SYNTHETIC_ARCHETYPE_TRAINING_SIGNAL_REVIEW_VERSION
            and syn_cal3.get("ready") is True
            and required_signals <= set(_str_list(syn_cal3.get("signal_ids")))
            and set(_str_list(syn_cal3.get("target_modules"))) <= {"M3", "M5", "M6"}
            and syn_cal3.get("signals_review_only") is True,
            "observed": syn_cal3,
        },
        {
            "check_id": "case_summary_has_complete_archetype_pass",
            "passed": int(case_summary.get("case_count", 0) or 0) >= 4
            and int(case_summary.get("failed_case_count", 0) or 0) == 0
            and float(case_summary.get("pass_ratio", 0.0) or 0.0) >= 1.0,
            "observed": case_summary,
        },
        {
            "check_id": "routine_cadence_defined",
            "passed": cadence.get("version") == "v30.synthetic_archetype_calibration_cadence.v1"
            and len(_list(cadence.get("routine_targeted_commands"))) >= 3
            and len(_list(cadence.get("heavy_gates_explicit_only"))) >= 4
            and _mapping(cadence.get("calibration_queue_policy")).get("review_only") is True,
            "observed": cadence,
        },
        {
            "check_id": "mutation_release_heavy_boundaries_locked",
            "passed": syn_cal3.get("external_release_allowed") is False
            and syn_cal3.get("chart_fact_mutation_allowed") is False
            and syn_cal3.get("auto_apply_training_allowed") is False
            and syn_cal3.get("policy_pointer_promotion_allowed") is False
            and syn_cal3.get("full_pytest_required") is False
            and syn_cal3.get("synthetic_all_required") is False
            and syn_cal3.get("full_518k_required") is False
            and syn_cal3.get("live_llm_required") is False,
            "observed": {
                "external_release_allowed": syn_cal3.get("external_release_allowed"),
                "chart_fact_mutation_allowed": syn_cal3.get("chart_fact_mutation_allowed"),
                "auto_apply_training_allowed": syn_cal3.get("auto_apply_training_allowed"),
                "policy_pointer_promotion_allowed": syn_cal3.get("policy_pointer_promotion_allowed"),
                "full_pytest_required": syn_cal3.get("full_pytest_required"),
                "synthetic_all_required": syn_cal3.get("synthetic_all_required"),
                "full_518k_required": syn_cal3.get("full_518k_required"),
                "live_llm_required": syn_cal3.get("live_llm_required"),
            },
        },
    ]


def _decision(checks: list[Mapping[str, Any]], syn_cal3: Mapping[str, Any]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "synthetic_archetype_calibration_closed": ready,
        "decision_status": "syn_cal4_synthetic_archetype_calibration_closed" if ready else "syn_cal4_synthetic_archetype_calibration_blocked",
        "closeout_check_count": len(checks),
        "passed_closeout_check_count": len(checks) - len(failed),
        "failed_closeout_check_ids": failed,
        "blockers": ["synthetic_archetype_closeout_checks_failed"] if failed else [],
        "training_signal_count": int(syn_cal3.get("training_signal_count", 0) or 0),
        "queued_item_count": int(syn_cal3.get("queued_item_count", 0) or 0),
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
    if decision.get("synthetic_archetype_calibration_closed") is True:
        return {
            "task_id": "CORE-CAL-S0",
            "title": "Core Calibration Steady-State Queue",
            "selected_track": "core_bazi_calibration",
            "scope": [
                "keep synthetic archetype tier as routine targeted gate",
                "wait for new focused evidence before reopening core modules",
                "run full pytest/synthetic-all/518K only at major nodes",
            ],
        }
    return {
        "task_id": "SYN-CAL4-FR",
        "title": "Synthetic Archetype Closeout Failure Review",
        "selected_track": "synthetic_archetype_calibration",
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
