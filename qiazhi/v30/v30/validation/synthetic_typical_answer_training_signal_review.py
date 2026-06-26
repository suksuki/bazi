from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.synthetic_typical_bazi_answer_calibration import (
    SYNTHETIC_TYPICAL_BAZI_ANSWER_CALIBRATION_VERSION,
    run_synthetic_typical_bazi_answer_calibration,
)


SYNTHETIC_TYPICAL_ANSWER_TRAINING_SIGNAL_REVIEW_VERSION = (
    "v30.synthetic_typical_answer_training_signal_review.v1"
)


def run_synthetic_typical_answer_training_signal_review() -> dict[str, Any]:
    return build_synthetic_typical_answer_training_signal_review(
        typical_answer_calibration=run_synthetic_typical_bazi_answer_calibration(),
        synthetic_tier=run_synthetic_tier("synthetic_typical_bazi_answer"),
    )


def build_synthetic_typical_answer_training_signal_review(
    *,
    typical_answer_calibration: Mapping[str, Any],
    synthetic_tier: object,
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    calibration_summary = _calibration_summary(typical_answer_calibration)
    tier_summary = _tier_summary(synthetic_tier)
    case_summary = _case_summary(typical_answer_calibration)
    training_signals = _training_signals(calibration_summary, tier_summary, case_summary)
    queue_items = _queue_items(typical_answer_calibration, synthetic_tier)
    checks = _checks(calibration_summary, tier_summary, training_signals, queue_items)
    decision = _decision(checks, training_signals, queue_items)
    return {
        "version": SYNTHETIC_TYPICAL_ANSWER_TRAINING_SIGNAL_REVIEW_VERSION,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["synthetic_typical_answer_training_signal_review_ready"] else "blocked",
        "task": {
            "task_id": "CORE-CAL-S2",
            "title": "Synthetic Typical Answer Tier Registration And Training Signals",
            "scope": "derive_review_only_training_signals_from_typical_bazi_answer_calibration",
        },
        "upstream_summary": {
            "typical_answer_calibration": calibration_summary,
            "synthetic_tier": tier_summary,
            "case_summary": case_summary,
        },
        "training_signals": training_signals,
        "calibration_queue_items": queue_items,
        "checks": checks,
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
            "boundary": "core_cal_s2_training_signals_are_review_only_answer_calibration_candidates",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "core_cal_s2_does_not_mutate_chart_facts_or_runtime_policy",
    }


def _calibration_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "ready": bool(decision.get("synthetic_typical_answer_calibration_ready")),
        "decision_status": str(decision.get("decision_status") or ""),
        "case_count": int(decision.get("case_count", 0) or 0),
        "passed_case_count": int(decision.get("passed_case_count", 0) or 0),
        "failed_case_count": int(decision.get("failed_case_count", 0) or 0),
        "failed_case_ids": _str_list(decision.get("failed_case_ids")),
        "failed_check_ids": _str_list(decision.get("failed_check_ids")),
    }


def _tier_summary(payload: object) -> dict[str, Any]:
    if isinstance(payload, Mapping):
        return {
            "suite_id": str(payload.get("suite_id") or ""),
            "passed": bool(payload.get("passed")),
            "case_count": int(payload.get("case_count", 0) or 0),
            "passed_count": int(payload.get("passed_count", 0) or 0),
            "failed_count": int(payload.get("failed_count", 0) or 0),
        }
    return {
        "suite_id": str(getattr(payload, "suite_id", "") or ""),
        "passed": bool(getattr(payload, "passed", False)),
        "case_count": int(getattr(payload, "case_count", 0) or 0),
        "passed_count": int(getattr(payload, "passed_count", 0) or 0),
        "failed_count": int(getattr(payload, "failed_count", 0) or 0),
    }


def _case_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    rows = [_mapping(row) for row in _list(payload.get("case_reviews"))]
    check_counts: Counter[str] = Counter()
    failed_check_counts: Counter[str] = Counter()
    target_modules: Counter[str] = Counter()
    question_counts: Counter[str] = Counter()
    for row in rows:
        question_id = str(row.get("question_id") or "")
        if question_id:
            question_counts[question_id] += 1
        for check_id, passed in _mapping(row.get("checks")).items():
            check_counts[str(check_id)] += 1
            if passed is not True:
                failed_check_counts[str(check_id)] += 1
        for module in _str_list(row.get("calibration_target_modules")):
            target_modules[module] += 1
    case_count = len(rows)
    passed_count = sum(1 for row in rows if row.get("passed") is True)
    return {
        "case_count": case_count,
        "passed_case_count": passed_count,
        "failed_case_count": case_count - passed_count,
        "pass_ratio": round(passed_count / case_count, 3) if case_count else 0.0,
        "check_counts": dict(sorted(check_counts.items())),
        "failed_check_counts": dict(sorted(failed_check_counts.items())),
        "target_module_counts": dict(sorted(target_modules.items())),
        "question_case_counts": dict(sorted(question_counts.items())),
    }


def _training_signals(
    calibration: Mapping[str, Any],
    tier: Mapping[str, Any],
    case_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    check_counts = _mapping(case_summary.get("check_counts"))
    failed_counts = _mapping(case_summary.get("failed_check_counts"))
    pass_ratio = _float(case_summary.get("pass_ratio"))
    return [
        _signal(
            signal_id="v30.training_signal.synthetic_typical_answer_m3_guidance_sanitization",
            signal_type="synthetic_typical_answer_guidance_sanitization",
            target_modules=["M3"],
            strength=_ratio_without_failures(check_counts, failed_counts, ["no_internal_or_english_leak"]),
            payload={
                "failed_check_counts": dict(failed_counts),
                "boundary": "m3_guidance_must_not_leak_policy_or_rule_ids_to_customer_text",
            },
        ),
        _signal(
            signal_id="v30.training_signal.synthetic_typical_answer_m6_domain_mechanism_specificity",
            signal_type="synthetic_typical_answer_domain_mechanism_specificity",
            target_modules=["M6"],
            strength=_ratio_without_failures(
                check_counts,
                failed_counts,
                ["domain_tokens_covered", "mechanism_tokens_covered", "boundary_language_present"],
            ),
            payload={
                "question_case_counts": dict(_mapping(case_summary.get("question_case_counts"))),
                "failed_check_counts": dict(failed_counts),
            },
        ),
        _signal(
            signal_id="v30.training_signal.synthetic_typical_answer_llm_expression_boundary",
            signal_type="synthetic_typical_answer_llm_expression_boundary",
            target_modules=["LLM"],
            strength=_ratio_without_failures(
                check_counts,
                failed_counts,
                ["answer_mentions_day_master_or_chart", "no_internal_or_english_leak", "answer_boundary_non_mutating"],
            ),
            payload={
                "live_llm_required": False,
                "llm_role": "expression_only_after_rule_bound_answer",
                "chart_fact_mutation_allowed": False,
            },
        ),
        _signal(
            signal_id="v30.training_signal.synthetic_typical_answer_interaction_answer_alignment",
            signal_type="synthetic_typical_answer_interaction_answer_alignment",
            target_modules=["interaction"],
            strength=_ratio_without_failures(check_counts, failed_counts, ["answer_present", "evidence_trace_present"]),
            payload={
                "answer_cases": case_summary.get("case_count"),
                "passed_answer_cases": case_summary.get("passed_case_count"),
                "interaction_scope": "question_outcome_answers_remain_bazi_specific_and_evidence_backed",
            },
        ),
        _signal(
            signal_id="v30.training_signal.synthetic_typical_answer_review_boundary_safety",
            signal_type="synthetic_typical_answer_review_boundary_safety",
            target_modules=["M3", "M6", "LLM", "interaction"],
            strength=1.0 if calibration.get("ready") and tier.get("passed") and pass_ratio >= 1.0 else 0.0,
            payload={
                "calibration_ready": calibration.get("ready"),
                "synthetic_tier_passed": tier.get("passed"),
                "pass_ratio": pass_ratio,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
            },
        ),
    ]


def _signal(
    *,
    signal_id: str,
    signal_type: str,
    target_modules: list[str],
    strength: float,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "signal_id": signal_id,
        "signal_type": signal_type,
        "domain": "synthetic_typical_bazi_answer",
        "target_modules": target_modules,
        "strength": round(max(0.0, min(1.0, strength)), 3),
        "source_versions": [SYNTHETIC_TYPICAL_BAZI_ANSWER_CALIBRATION_VERSION],
        "payload": dict(payload),
        "review_only": True,
        "runtime_mutation_allowed": False,
        "chart_fact_mutation_allowed": False,
        "auto_apply_training_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "external_release_allowed": False,
    }


def _queue_items(calibration_payload: Mapping[str, Any], synthetic_tier: object) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in _list(calibration_payload.get("calibration_queue")):
        row = _mapping(item)
        rows.append(
            {
                "queue_item_id": f"core_cal_s2.typical_answer.{row.get('case_id')}",
                "case_id": str(row.get("case_id") or ""),
                "target_modules": _normalize_targets(row.get("target_modules")),
                "issue_type": "synthetic_typical_answer_calibration_gap",
                "failed_check_ids": _str_list(row.get("failed_check_ids")),
                "review_only": True,
                "chart_fact_mutation_allowed": False,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "external_release_allowed": False,
            }
        )
    tier = _tier_summary(synthetic_tier)
    if tier.get("passed") is not True:
        rows.append(
            {
                "queue_item_id": "core_cal_s2.synthetic_typical_bazi_answer.tier_failure",
                "case_id": "synthetic_typical_bazi_answer",
                "target_modules": ["M3", "M6", "LLM", "interaction"],
                "issue_type": "synthetic_typical_answer_tier_failure",
                "failed_check_ids": ["synthetic_typical_bazi_answer_tier_passed"],
                "review_only": True,
                "chart_fact_mutation_allowed": False,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "external_release_allowed": False,
            }
        )
    return sorted(rows, key=lambda item: str(item["queue_item_id"]))


def _checks(
    calibration: Mapping[str, Any],
    tier: Mapping[str, Any],
    signals: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    required_signal_ids = {
        "v30.training_signal.synthetic_typical_answer_m3_guidance_sanitization",
        "v30.training_signal.synthetic_typical_answer_m6_domain_mechanism_specificity",
        "v30.training_signal.synthetic_typical_answer_llm_expression_boundary",
        "v30.training_signal.synthetic_typical_answer_interaction_answer_alignment",
        "v30.training_signal.synthetic_typical_answer_review_boundary_safety",
    }
    signal_ids = {str(row.get("signal_id") or "") for row in signals}
    allowed_targets = {"M3", "M6", "LLM", "interaction"}
    return [
        {
            "check_id": "core_cal_s1_typical_answer_calibration_ready",
            "passed": calibration.get("version") == SYNTHETIC_TYPICAL_BAZI_ANSWER_CALIBRATION_VERSION
            and calibration.get("ready") is True
            and int(calibration.get("case_count", 0) or 0) >= 5,
            "observed": calibration,
        },
        {
            "check_id": "synthetic_typical_bazi_answer_tier_passed",
            "passed": tier.get("suite_id") == "v30.synthetic.synthetic_typical_bazi_answer"
            and tier.get("passed") is True
            and int(tier.get("case_count", 0) or 0) >= 3,
            "observed": tier,
        },
        {
            "check_id": "required_training_signals_present",
            "passed": required_signal_ids <= signal_ids and len(signals) >= len(required_signal_ids),
            "observed": {"signal_ids": sorted(signal_ids), "signal_count": len(signals)},
        },
        {
            "check_id": "signals_route_to_m3_m6_llm_interaction_only",
            "passed": all(set(_str_list(row.get("target_modules"))) <= allowed_targets for row in signals + queue_items),
            "observed": {
                "allowed_targets": sorted(allowed_targets),
                "signal_targets": [row.get("target_modules") for row in signals],
                "queue_targets": [row.get("target_modules") for row in queue_items],
            },
        },
        {
            "check_id": "signals_and_queue_are_review_only",
            "passed": all(_is_readonly(row) for row in signals + queue_items),
            "observed": {"auto_apply_training_allowed": False, "queue_item_count": len(queue_items)},
        },
        {
            "check_id": "heavy_live_release_gates_remain_explicit",
            "passed": True,
            "observed": {
                "full_pytest_required": False,
                "synthetic_all_required": False,
                "full_518k_required": False,
                "live_llm_required": False,
                "external_release_allowed": False,
            },
        },
    ]


def _decision(
    checks: list[Mapping[str, Any]],
    signals: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "synthetic_typical_answer_training_signal_review_ready": ready,
        "decision_status": "core_cal_s2_training_signal_review_ready"
        if ready
        else "core_cal_s2_training_signal_review_blocked",
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "blockers": ["core_cal_s2_training_signal_checks_failed"] if failed else [],
        "training_signal_count": len(signals),
        "queued_item_count": len(queue_items),
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
    if decision.get("synthetic_typical_answer_training_signal_review_ready") is True:
        return {
            "task_id": "CORE-CAL-S3",
            "title": "Synthetic Typical Answer Calibration Closeout",
            "selected_track": "core_answer_calibration",
            "scope": [
                "record CORE-CAL-S1 and CORE-CAL-S2 evidence",
                "define routine cadence for typical-answer calibration",
                "keep training signals review-only until explicit calibration work is selected",
            ],
        }
    return {
        "task_id": "CORE-CAL-S2-FR",
        "title": "Synthetic Typical Answer Training Signal Failure Review",
        "selected_track": "core_answer_calibration",
        "scope": [
            "repair S1 calibration or synthetic tier registration evidence",
            "do not mutate chart facts or promote policy pointers while blocked",
        ],
    }


def _ratio_without_failures(check_counts: Mapping[str, Any], failed_counts: Mapping[str, Any], check_ids: list[str]) -> float:
    total = sum(int(check_counts.get(check_id, 0) or 0) for check_id in check_ids)
    failed = sum(int(failed_counts.get(check_id, 0) or 0) for check_id in check_ids)
    if total <= 0:
        return 0.0
    return (total - failed) / total


def _normalize_targets(value: object) -> list[str]:
    targets: set[str] = set()
    for item in _str_list(value):
        if item.startswith("M3"):
            targets.add("M3")
        elif item.startswith("M6") or item == "runtime_answer_composer":
            targets.add("M6")
        elif "llm" in item.lower():
            targets.add("LLM")
        elif "interaction" in item.lower():
            targets.add("interaction")
        else:
            targets.add("M6")
    return sorted(targets or {"M6"})


def _is_readonly(row: Mapping[str, Any]) -> bool:
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


def _float(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
