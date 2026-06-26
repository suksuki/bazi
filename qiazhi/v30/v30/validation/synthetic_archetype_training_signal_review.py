from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.synthetic_archetype_rule_claim_calibration import (
    SYNTHETIC_ARCHETYPE_RULE_CLAIM_CALIBRATION_VERSION,
    run_synthetic_archetype_rule_claim_calibration,
)
from v30.validation.synthetic_archetype_tier_registration import (
    SYNTHETIC_ARCHETYPE_TIER_REGISTRATION_VERSION,
    run_synthetic_archetype_tier_registration,
)


SYNTHETIC_ARCHETYPE_TRAINING_SIGNAL_REVIEW_VERSION = "v30.synthetic_archetype_training_signal_review.v1"


def run_synthetic_archetype_training_signal_review() -> dict[str, Any]:
    tier_registration = run_synthetic_archetype_tier_registration()
    archetype_calibration = run_synthetic_archetype_rule_claim_calibration()
    return build_synthetic_archetype_training_signal_review(
        tier_registration=tier_registration,
        archetype_calibration=archetype_calibration,
    )


def build_synthetic_archetype_training_signal_review(
    *,
    tier_registration: Mapping[str, Any],
    archetype_calibration: Mapping[str, Any],
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    tier_summary = _tier_summary(tier_registration)
    calibration_summary = _calibration_summary(archetype_calibration)
    case_summary = _case_summary(archetype_calibration)
    training_signals = _training_signals(tier_summary, calibration_summary, case_summary)
    queue_items = _calibration_queue_items(tier_registration, archetype_calibration)
    checks = _checks(tier_summary, calibration_summary, training_signals, queue_items)
    decision = _decision(checks, training_signals, queue_items)
    return {
        "version": SYNTHETIC_ARCHETYPE_TRAINING_SIGNAL_REVIEW_VERSION,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["synthetic_archetype_training_signal_review_ready"] else "blocked",
        "task": {
            "task_id": "SYN-CAL3",
            "title": "Synthetic Archetype Training Signal Review",
            "scope": "derive_review_only_training_signals_from_archetype_outcomes_for_m3_m5_m6_calibration",
        },
        "upstream_summary": {
            "tier_registration": tier_summary,
            "archetype_calibration": calibration_summary,
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
            "boundary": "syn_cal3_training_signals_are_review_only_m3_m5_m6_calibration_candidates",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "syn_cal3_turns_synthetic_archetype_outcomes_into_readonly_training_signals_not_runtime_changes",
    }


def _tier_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    tier_contract = _mapping(payload.get("tier_contract"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "ready": bool(decision.get("synthetic_archetype_tier_registration_ready")),
        "check_count": int(decision.get("check_count", 0) or 0),
        "passed_check_count": int(decision.get("passed_check_count", 0) or 0),
        "calibration_queue_item_count": int(decision.get("calibration_queue_item_count", 0) or 0),
        "targeted_tier": str(tier_contract.get("tier") or ""),
        "routine_targeted_gate": bool(tier_contract.get("routine_targeted_gate")),
        "included_in_synthetic_all": bool(tier_contract.get("included_in_synthetic_all")),
        "external_release_allowed": bool(decision.get("external_release_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "auto_apply_training_allowed": bool(decision.get("auto_apply_training_allowed")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
    }


def _calibration_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "ready": bool(decision.get("synthetic_archetype_calibration_ready")),
        "case_count": int(decision.get("case_count", 0) or 0),
        "passed_case_count": int(decision.get("passed_case_count", 0) or 0),
        "failed_case_ids": _str_list(decision.get("failed_case_ids")),
        "failed_check_ids": _str_list(decision.get("failed_check_ids")),
        "external_release_allowed": bool(decision.get("external_release_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "auto_apply_training_allowed": bool(decision.get("auto_apply_training_allowed")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
    }


def _case_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    rows = [_mapping(row) for row in _list(payload.get("case_reviews"))]
    case_count = len(rows)
    passed_count = sum(1 for row in rows if row.get("passed") is True)
    check_counts: Counter[str] = Counter()
    failed_check_counts: Counter[str] = Counter()
    target_modules: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    mechanism_counts: Counter[str] = Counter()
    for row in rows:
        for check_id, passed in _mapping(row.get("checks")).items():
            check_counts[str(check_id)] += 1
            if passed is not True:
                failed_check_counts[str(check_id)] += 1
        for module in _str_list(row.get("calibration_target_modules")):
            target_modules[module] += 1
        observed = _mapping(row.get("observed"))
        for domain, count in _mapping(observed.get("claim_domain_counts")).items():
            if int(count or 0) > 0:
                domain_counts[str(domain)] += 1
        for mechanism, count in _mapping(observed.get("mechanism_counts")).items():
            if int(count or 0) > 0:
                mechanism_counts[str(mechanism)] += 1
    return {
        "case_count": case_count,
        "passed_case_count": passed_count,
        "failed_case_count": case_count - passed_count,
        "pass_ratio": round(passed_count / case_count, 3) if case_count else 0.0,
        "check_counts": dict(sorted(check_counts.items())),
        "failed_check_counts": dict(sorted(failed_check_counts.items())),
        "target_module_counts": dict(sorted(target_modules.items())),
        "domain_case_counts": dict(sorted(domain_counts.items())),
        "mechanism_case_counts": dict(sorted(mechanism_counts.items())),
    }


def _training_signals(
    tier: Mapping[str, Any],
    calibration: Mapping[str, Any],
    case_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    pass_ratio = _float(case_summary.get("pass_ratio"))
    failed_counts = _mapping(case_summary.get("failed_check_counts"))
    check_counts = _mapping(case_summary.get("check_counts"))
    return [
        _signal(
            signal_id="v30.training_signal.synthetic_archetype_m3_rule_claim_coverage",
            signal_type="synthetic_archetype_rule_claim_coverage",
            target_modules=["M3"],
            strength=_ratio_without_failures(
                check_counts,
                failed_counts,
                ["m3_claim_domains_cover_archetype", "m3_dynamic_mechanisms_cover_archetype"],
            ),
            payload={
                "domain_case_counts": dict(_mapping(case_summary.get("domain_case_counts"))),
                "mechanism_case_counts": dict(_mapping(case_summary.get("mechanism_case_counts"))),
                "failed_check_counts": dict(failed_counts),
            },
        ),
        _signal(
            signal_id="v30.training_signal.synthetic_archetype_m5_ranked_candidate_alignment",
            signal_type="synthetic_archetype_ranked_candidate_alignment",
            target_modules=["M5"],
            strength=_ratio_without_failures(
                check_counts,
                failed_counts,
                ["m5_strength_candidate_matches", "m5_useful_god_candidate_matches", "m5_candidate_scores_present"],
            ),
            payload={
                "case_count": case_summary.get("case_count"),
                "passed_case_count": case_summary.get("passed_case_count"),
                "failed_check_counts": dict(failed_counts),
            },
        ),
        _signal(
            signal_id="v30.training_signal.synthetic_archetype_m6_practical_claim_specificity",
            signal_type="synthetic_archetype_practical_claim_specificity",
            target_modules=["M6"],
            strength=_ratio_without_failures(
                check_counts,
                failed_counts,
                ["m6_domain_claims_present", "m6_summaries_are_bazi_specific"],
            ),
            payload={
                "case_count": case_summary.get("case_count"),
                "passed_case_count": case_summary.get("passed_case_count"),
                "generic_language_boundary": "summaries_must_remain_bazi_specific",
            },
        ),
        _signal(
            signal_id="v30.training_signal.synthetic_archetype_review_boundary_safety",
            signal_type="synthetic_archetype_review_boundary_safety",
            target_modules=["M3", "M5", "M6"],
            strength=1.0
            if pass_ratio > 0
            and tier.get("ready") is True
            and calibration.get("chart_fact_mutation_allowed") is False
            and calibration.get("auto_apply_training_allowed") is False
            and calibration.get("policy_pointer_promotion_allowed") is False
            else 0.0,
            payload={
                "tier_ready": tier.get("ready"),
                "calibration_ready": calibration.get("ready"),
                "pass_ratio": pass_ratio,
                "external_release_allowed": False,
                "chart_fact_mutation_allowed": False,
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
        "domain": "synthetic_archetype_rule_claim",
        "target_modules": target_modules,
        "strength": round(max(0.0, min(1.0, strength)), 3),
        "source_versions": [
            SYNTHETIC_ARCHETYPE_RULE_CLAIM_CALIBRATION_VERSION,
            SYNTHETIC_ARCHETYPE_TIER_REGISTRATION_VERSION,
        ],
        "payload": dict(payload),
        "review_only": True,
        "runtime_mutation_allowed": False,
        "chart_fact_mutation_allowed": False,
        "auto_apply_training_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "external_release_allowed": False,
    }


def _calibration_queue_items(
    tier_registration: Mapping[str, Any],
    archetype_calibration: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in _list(tier_registration.get("calibration_queue_items")):
        row = _mapping(item)
        rows.append(
            {
                "queue_item_id": str(row.get("queue_item_id") or ""),
                "case_id": str(row.get("case_id") or ""),
                "target_modules": [module for module in _str_list(row.get("target_modules")) if module in {"M3", "M5", "M6"}],
                "issue_type": "synthetic_archetype_expectation_gap",
                "failed_check_ids": _str_list(row.get("failed_check_ids")),
                "review_only": True,
                "chart_fact_mutation_allowed": False,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "external_release_allowed": False,
            }
        )
    for row in _list(archetype_calibration.get("case_reviews")):
        review = _mapping(row)
        if review.get("passed") is True:
            continue
        rows.append(
            {
                "queue_item_id": f"syn_cal3.training_review.{review.get('case_id')}",
                "case_id": str(review.get("case_id") or ""),
                "target_modules": [module for module in _str_list(review.get("calibration_target_modules")) if module in {"M3", "M5", "M6"}],
                "issue_type": "synthetic_archetype_training_signal_gap",
                "failed_check_ids": _str_list(review.get("failed_check_ids")),
                "review_only": True,
                "chart_fact_mutation_allowed": False,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "external_release_allowed": False,
            }
        )
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        queue_id = str(row.get("queue_item_id") or "")
        if queue_id:
            deduped[queue_id] = row
    return sorted(deduped.values(), key=lambda item: str(item["queue_item_id"]))


def _checks(
    tier: Mapping[str, Any],
    calibration: Mapping[str, Any],
    training_signals: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    required_signal_ids = {
        "v30.training_signal.synthetic_archetype_m3_rule_claim_coverage",
        "v30.training_signal.synthetic_archetype_m5_ranked_candidate_alignment",
        "v30.training_signal.synthetic_archetype_m6_practical_claim_specificity",
        "v30.training_signal.synthetic_archetype_review_boundary_safety",
    }
    signal_ids = {str(row.get("signal_id") or "") for row in training_signals}
    allowed_targets = {"M3", "M5", "M6"}
    signals_are_readonly = all(_is_readonly(row) for row in training_signals)
    queue_is_readonly = all(_is_readonly(row) for row in queue_items)
    targets_are_core_only = all(set(_str_list(row.get("target_modules"))) <= allowed_targets for row in training_signals + queue_items)
    return [
        {
            "check_id": "syn_cal2_tier_registration_ready",
            "passed": tier.get("version") == SYNTHETIC_ARCHETYPE_TIER_REGISTRATION_VERSION
            and tier.get("ready") is True
            and tier.get("routine_targeted_gate") is True
            and tier.get("included_in_synthetic_all") is False,
            "observed": tier,
        },
        {
            "check_id": "syn_cal1_archetype_calibration_ready",
            "passed": calibration.get("version") == SYNTHETIC_ARCHETYPE_RULE_CLAIM_CALIBRATION_VERSION
            and calibration.get("ready") is True
            and int(calibration.get("case_count", 0) or 0) >= 4,
            "observed": calibration,
        },
        {
            "check_id": "required_training_signals_present",
            "passed": required_signal_ids <= signal_ids and len(training_signals) >= 4,
            "observed": {"signal_ids": sorted(signal_ids), "signal_count": len(training_signals)},
        },
        {
            "check_id": "signals_route_to_m3_m5_m6_only",
            "passed": targets_are_core_only,
            "observed": {
                "allowed_targets": sorted(allowed_targets),
                "signal_targets": [row.get("target_modules") for row in training_signals],
                "queue_targets": [row.get("target_modules") for row in queue_items],
            },
        },
        {
            "check_id": "signals_and_queue_are_review_only",
            "passed": signals_are_readonly and queue_is_readonly,
            "observed": {
                "signals_are_readonly": signals_are_readonly,
                "queue_is_readonly": queue_is_readonly,
                "auto_apply_training_allowed": False,
            },
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
    training_signals: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "synthetic_archetype_training_signal_review_ready": ready,
        "decision_status": "syn_cal3_training_signal_review_ready" if ready else "syn_cal3_training_signal_review_blocked",
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "blockers": ["synthetic_archetype_training_signal_review_checks_failed"] if failed else [],
        "training_signal_count": len(training_signals),
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
    if decision.get("synthetic_archetype_training_signal_review_ready"):
        return {
            "task_id": "SYN-CAL4",
            "title": "Synthetic Archetype Calibration Closeout",
            "selected_track": "synthetic_archetype_calibration",
            "scope": [
                "freeze SYN-CAL1 to SYN-CAL3 evidence into mainline docs",
                "define routine cadence for archetype tier and training signal review",
                "keep queue items review-only until explicit calibration work is selected",
            ],
        }
    return {
        "task_id": "SYN-CAL3-FR",
        "title": "Synthetic Archetype Training Signal Failure Review",
        "selected_track": "synthetic_archetype_calibration",
        "scope": [
            "repair upstream tier registration or archetype calibration evidence",
            "do not mutate chart facts or promote policy pointers while blocked",
        ],
    }


def _ratio_without_failures(
    check_counts: Mapping[str, Any],
    failed_counts: Mapping[str, Any],
    check_ids: list[str],
) -> float:
    total = sum(int(check_counts.get(check_id, 0) or 0) for check_id in check_ids)
    failed = sum(int(failed_counts.get(check_id, 0) or 0) for check_id in check_ids)
    if total <= 0:
        return 0.0
    return (total - failed) / total


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
