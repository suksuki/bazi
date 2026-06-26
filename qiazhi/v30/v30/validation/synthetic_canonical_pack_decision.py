from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.synthetic_canonical_bazi_calibration_review import (
    SYNTHETIC_CANONICAL_BAZI_CALIBRATION_REVIEW_VERSION,
    run_synthetic_canonical_bazi_calibration_review,
)


SYNTHETIC_CANONICAL_PACK_DECISION_VERSION = "v30.synthetic_canonical_pack_decision.v1"

REQUIRED_EXPANSION_FAMILIES: dict[str, str] = {
    "weak_body_many_wealth": "财多身弱",
    "output_generates_wealth": "食伤生财",
    "mixed_officer_killing": "官杀混杂",
    "resource_peer_heavy": "印比过重",
    "wealth_officer_resource_chain": "财官印相生",
    "cold_hot_dry_wet_imbalance": "寒热燥湿偏枯",
    "clash_combine_harm": "刑冲合害明显",
    "follow_strong_candidate": "从强/从弱候选边界",
    "luck_cycle_structure_shift": "大运触发结构变化",
    "flow_year_domain_trigger": "流年触发领域主题",
}


def run_synthetic_canonical_pack_decision() -> dict[str, Any]:
    review = run_synthetic_canonical_bazi_calibration_review()
    return build_synthetic_canonical_pack_decision(canonical_review=review)


def build_synthetic_canonical_pack_decision(*, canonical_review: Mapping[str, Any]) -> dict[str, Any]:
    review = _mapping(canonical_review)
    expansion_summary = _expansion_summary(review)
    cadence = _cadence(expansion_summary)
    checks = _checks(review, expansion_summary, cadence)
    decision = _decision(checks, expansion_summary)
    return {
        "version": SYNTHETIC_CANONICAL_PACK_DECISION_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["synthetic_canonical_pack_decision_ready"] else "blocked",
        "task": {
            "task_id": "SCAL-S2",
            "title": "Synthetic Canonical Pack Expansion Or Cadence Decision",
            "scope": "decide_expanded_synthetic_canonical_bazi_pack_is_ready_for_routine_cadence",
        },
        "canonical_review_summary": _review_summary(review),
        "expansion_summary": expansion_summary,
        "routine_cadence": cadence,
        "checks": checks,
        "decision": decision,
        "policy_boundary": {
            "uses_real_person_truth": False,
            "expanded_pack_mutates_chart_facts": False,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "boundary": "scal_s2_expands_structural_synthetic_coverage_without_truth_label_pollution_or_runtime_writes",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "synthetic_canonical_pack_decision_freezes_expanded_structural_gate_not_real_destiny_truth",
    }


def _expansion_summary(review: Mapping[str, Any]) -> dict[str, Any]:
    rows = _list(review.get("case_rows"))
    case_ids = [str(row.get("case_id") or "") for row in rows if isinstance(row, Mapping)]
    covered = {
        family_id: label
        for family_id, label in REQUIRED_EXPANSION_FAMILIES.items()
        if any(family_id in case_id for case_id in case_ids)
    }
    missing = {
        family_id: label
        for family_id, label in REQUIRED_EXPANSION_FAMILIES.items()
        if family_id not in covered
    }
    return {
        "version": "v30.synthetic_canonical_pack_expansion_summary.v1",
        "case_count": len(rows),
        "passed_case_count": sum(1 for row in rows if isinstance(row, Mapping) and row.get("passed") is True),
        "required_family_count": len(REQUIRED_EXPANSION_FAMILIES),
        "covered_family_count": len(covered),
        "covered_families": covered,
        "missing_families": missing,
        "baseline_case_count": sum(1 for case_id in case_ids if "v30.synthetic.canonical_bazi." in case_id) - len(covered),
        "expanded_family_labels": list(covered.values()),
        "boundary": "expansion_summary_counts_structural_families_not_life_outcome_truth",
    }


def _cadence(expansion_summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "cadence_id": "scal_synthetic_canonical_bazi_cadence",
        "routine_commands": [
            "python3 scripts/run_synthetic_canonical_pack_decision.py",
            "python3 scripts/run_synthetic_canonical_bazi_calibration_review.py",
            "python3 scripts/run_synthetic_validation.py --tier synthetic_canonical_bazi_calibration",
        ],
        "case_count": int(expansion_summary.get("case_count", 0) or 0),
        "covered_family_count": int(expansion_summary.get("covered_family_count", 0) or 0),
        "run_after": [
            "RBD rule/path/portrait/claim changes",
            "M3 knowledge/rule/portrait changes",
            "M5 ranked-decision scoring changes",
            "IQ question-strategy changes",
            "before release-boundary validation",
        ],
        "major_node_commands_explicit_only": [
            "python3 scripts/run_synthetic_validation.py --tier all",
            "pytest -q",
            "python3 scripts/run_518k_validation.py --mode full --confirm-full",
        ],
        "calibration_review_required_before_tuning": True,
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "boundary": "scal_cadence_is_targeted_and_does_not_replace_major_release_gates",
    }


def _checks(
    review: Mapping[str, Any],
    expansion_summary: Mapping[str, Any],
    cadence: Mapping[str, Any],
) -> list[dict[str, Any]]:
    review_decision = _mapping(review.get("decision"))
    policy = _mapping(review.get("policy_boundary"))
    return [
        {
            "check_id": "scal_s1_review_ready",
            "passed": (
                review.get("version") == SYNTHETIC_CANONICAL_BAZI_CALIBRATION_REVIEW_VERSION
                and review_decision.get("synthetic_canonical_calibration_ready") is True
                and review_decision.get("decision_status") == "scal_s1_synthetic_canonical_calibration_ready"
            ),
            "observed": {
                "version": review.get("version"),
                "decision_status": review_decision.get("decision_status"),
            },
        },
        {
            "check_id": "expanded_canonical_pack_case_count_ready",
            "passed": (
                int(expansion_summary.get("case_count", 0) or 0) >= 16
                and int(expansion_summary.get("passed_case_count", 0) or 0) == int(expansion_summary.get("case_count", 0) or 0)
            ),
            "observed": {
                "case_count": expansion_summary.get("case_count"),
                "passed_case_count": expansion_summary.get("passed_case_count"),
            },
        },
        {
            "check_id": "required_expansion_families_covered",
            "passed": (
                int(expansion_summary.get("covered_family_count", 0) or 0) == len(REQUIRED_EXPANSION_FAMILIES)
                and not expansion_summary.get("missing_families")
            ),
            "observed": {
                "covered_families": expansion_summary.get("covered_families"),
                "missing_families": expansion_summary.get("missing_families"),
            },
        },
        {
            "check_id": "expanded_pack_has_no_calibration_failures",
            "passed": int(review_decision.get("queued_item_count", 0) or 0) == 0,
            "observed": {"queued_item_count": review_decision.get("queued_item_count")},
        },
        {
            "check_id": "truth_label_and_write_boundaries_locked",
            "passed": (
                policy.get("uses_real_person_truth") is False
                and policy.get("chart_fact_mutation_allowed") is False
                and policy.get("auto_apply_training_allowed") is False
                and policy.get("policy_pointer_promotion_allowed") is False
            ),
            "observed": policy,
        },
        {
            "check_id": "targeted_cadence_keeps_heavy_gates_explicit",
            "passed": (
                cadence.get("full_pytest_required") is False
                and cadence.get("synthetic_all_required") is False
                and cadence.get("full_518k_required") is False
            ),
            "observed": {
                "full_pytest_required": cadence.get("full_pytest_required"),
                "synthetic_all_required": cadence.get("synthetic_all_required"),
                "full_518k_required": cadence.get("full_518k_required"),
            },
        },
    ]


def _decision(checks: list[Mapping[str, Any]], expansion_summary: Mapping[str, Any]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "synthetic_canonical_pack_decision_ready": ready,
        "decision_status": "scal_s2_expanded_canonical_pack_cadence_ready" if ready else "scal_s2_expanded_canonical_pack_blocked",
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "case_count": int(expansion_summary.get("case_count", 0) or 0),
        "covered_family_count": int(expansion_summary.get("covered_family_count", 0) or 0),
        "missing_families": dict(_mapping(expansion_summary.get("missing_families"))),
        "routine_cadence_ready": ready,
        "chart_fact_mutation_allowed": False,
        "auto_apply_training_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "blockers": ["synthetic_canonical_pack_decision_checks_failed"] if failed else [],
    }


def _review_summary(review: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(review.get("decision"))
    suite = _mapping(review.get("synthetic_suite_summary"))
    return {
        "version": str(review.get("version") or ""),
        "status": str(review.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "ready": bool(decision.get("synthetic_canonical_calibration_ready")),
        "case_count": int(decision.get("case_count", 0) or suite.get("case_count", 0) or 0),
        "passed_case_count": int(decision.get("passed_case_count", 0) or suite.get("passed_count", 0) or 0),
        "queued_item_count": int(decision.get("queued_item_count", 0) or 0),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("synthetic_canonical_pack_decision_ready"):
        return {
            "task_id": "SCAL-S3",
            "title": "Synthetic Canonical Calibration Steady State",
            "selected_track": "synthetic_canonical_calibration",
            "scope": [
                "freeze expanded canonical pack as routine calibration gate",
                "run after RBD/M3/M5/IQ changes and before release",
                "route failures to read-only calibration review",
            ],
        }
    return {
        "task_id": "SCAL-S2-FR",
        "title": "Synthetic Canonical Pack Expansion Failure Review",
        "selected_track": "synthetic_canonical_calibration",
        "scope": [
            "repair missing expansion families or failed canonical cases",
            "keep failed expectations read-only",
            "do not introduce real-person truth labels",
        ],
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
