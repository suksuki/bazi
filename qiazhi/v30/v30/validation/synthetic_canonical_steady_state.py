from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.synthetic_canonical_pack_decision import (
    REQUIRED_EXPANSION_FAMILIES,
    SYNTHETIC_CANONICAL_PACK_DECISION_VERSION,
    run_synthetic_canonical_pack_decision,
)


SYNTHETIC_CANONICAL_STEADY_STATE_VERSION = "v30.synthetic_canonical_steady_state.v1"


def run_synthetic_canonical_steady_state() -> dict[str, Any]:
    pack_decision = run_synthetic_canonical_pack_decision()
    return build_synthetic_canonical_steady_state(canonical_pack_decision=pack_decision)


def build_synthetic_canonical_steady_state(*, canonical_pack_decision: Mapping[str, Any]) -> dict[str, Any]:
    payload = _mapping(canonical_pack_decision)
    pack_summary = _pack_summary(payload)
    routine_gate = _routine_gate(pack_summary)
    failure_routing = _failure_routing()
    checks = _checks(pack_summary, routine_gate, failure_routing)
    decision = _decision(checks, pack_summary)
    return {
        "version": SYNTHETIC_CANONICAL_STEADY_STATE_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["synthetic_canonical_steady_state_ready"] else "blocked",
        "task": {
            "task_id": "SCAL-S3",
            "title": "Synthetic Canonical Calibration Steady State",
            "scope": "freeze_expanded_synthetic_canonical_bazi_pack_as_routine_targeted_calibration_gate",
        },
        "canonical_pack_summary": pack_summary,
        "routine_gate": routine_gate,
        "failure_routing": failure_routing,
        "checks": checks,
        "decision": decision,
        "policy_boundary": {
            "uses_real_person_truth": False,
            "routine_gate_mutates_chart_facts": False,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "release_boundary_required": False,
            "boundary": "scal_s3_freezes_targeted_synthetic_structural_gate_without_real_truth_labels_or_runtime_writes",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "synthetic_canonical_steady_state_is_a_routine_gate_not_a_fortune_truth_or_release_gate",
    }


def _pack_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    expansion = _mapping(payload.get("expansion_summary"))
    policy = _mapping(payload.get("policy_boundary"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "pack_decision_ready": bool(decision.get("synthetic_canonical_pack_decision_ready")),
        "case_count": int(decision.get("case_count", 0) or expansion.get("case_count", 0) or 0),
        "covered_family_count": int(decision.get("covered_family_count", 0) or expansion.get("covered_family_count", 0) or 0),
        "required_family_count": len(REQUIRED_EXPANSION_FAMILIES),
        "covered_families": dict(_mapping(expansion.get("covered_families"))),
        "missing_families": dict(_mapping(decision.get("missing_families")) or _mapping(expansion.get("missing_families"))),
        "uses_real_person_truth": bool(policy.get("uses_real_person_truth")),
        "chart_fact_mutation_allowed": bool(policy.get("chart_fact_mutation_allowed")),
        "auto_apply_training_allowed": bool(policy.get("auto_apply_training_allowed")),
        "policy_pointer_promotion_allowed": bool(policy.get("policy_pointer_promotion_allowed")),
        "full_pytest_required": bool(policy.get("full_pytest_required")),
        "synthetic_all_required": bool(policy.get("synthetic_all_required")),
        "full_518k_required": bool(policy.get("full_518k_required")),
    }


def _routine_gate(pack_summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "gate_id": "scal_synthetic_canonical_bazi_routine_gate",
        "gate_status": "frozen_targeted_gate" if pack_summary.get("pack_decision_ready") else "blocked",
        "case_count": int(pack_summary.get("case_count", 0) or 0),
        "family_count": int(pack_summary.get("covered_family_count", 0) or 0),
        "required_trigger_events": [
            "RBD rule/path/portrait/claim changes",
            "M3 knowledge/rule/portrait changes",
            "M5 ranked-decision scoring changes",
            "IQ question-strategy changes",
            "before release-boundary validation",
        ],
        "routine_commands": [
            "python3 scripts/run_synthetic_canonical_steady_state.py",
            "python3 scripts/run_synthetic_canonical_pack_decision.py",
            "python3 scripts/run_synthetic_validation.py --tier synthetic_canonical_bazi_calibration",
        ],
        "failure_route": "SCAL-FR Synthetic Canonical Calibration Failure Review",
        "calibration_queue_mode": "read_only",
        "major_node_commands_explicit_only": [
            "python3 scripts/run_synthetic_validation.py --tier all",
            "pytest -q",
            "python3 scripts/run_518k_validation.py --mode full --confirm-full",
        ],
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "boundary": "routine_gate_runs_targeted_synthetic_structural_cases_and_routes_failures_readonly",
    }


def _failure_routing() -> dict[str, Any]:
    return {
        "route_id": "scal_failure_to_readonly_calibration_review",
        "failure_inputs": [
            "canonical case failure",
            "missing structural family",
            "generic-language regression",
            "untraceable diagnosis claim",
            "customer internal leak",
            "fixed-event prediction",
            "chart-fact mutation flag",
        ],
        "queue_item_policy": {
            "target_module_candidates": ["RBD", "M3", "M5", "IQ"],
            "status": "queued_for_review",
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "auto_apply_training_allowed": False,
        },
        "operator_review_required_before_tuning": True,
        "boundary": "scal_failures_create_review_candidates_not_training_or_policy_writes",
    }


def _checks(
    pack_summary: Mapping[str, Any],
    routine_gate: Mapping[str, Any],
    failure_routing: Mapping[str, Any],
) -> list[dict[str, Any]]:
    queue_policy = _mapping(failure_routing.get("queue_item_policy"))
    return [
        {
            "check_id": "scal_s2_pack_decision_ready",
            "passed": (
                pack_summary.get("version") == SYNTHETIC_CANONICAL_PACK_DECISION_VERSION
                and pack_summary.get("pack_decision_ready") is True
                and pack_summary.get("decision_status") == "scal_s2_expanded_canonical_pack_cadence_ready"
            ),
            "observed": {
                "version": pack_summary.get("version"),
                "decision_status": pack_summary.get("decision_status"),
            },
        },
        {
            "check_id": "expanded_pack_frozen_as_routine_gate",
            "passed": (
                routine_gate.get("gate_status") == "frozen_targeted_gate"
                and int(routine_gate.get("case_count", 0) or 0) >= 16
                and int(routine_gate.get("family_count", 0) or 0) == len(REQUIRED_EXPANSION_FAMILIES)
                and len(routine_gate.get("required_trigger_events", [])) >= 5
            ),
            "observed": {
                "gate_status": routine_gate.get("gate_status"),
                "case_count": routine_gate.get("case_count"),
                "family_count": routine_gate.get("family_count"),
                "required_trigger_events": routine_gate.get("required_trigger_events"),
            },
        },
        {
            "check_id": "all_required_structural_families_remain_covered",
            "passed": (
                int(pack_summary.get("covered_family_count", 0) or 0) == len(REQUIRED_EXPANSION_FAMILIES)
                and not pack_summary.get("missing_families")
            ),
            "observed": {
                "covered_families": pack_summary.get("covered_families"),
                "missing_families": pack_summary.get("missing_families"),
            },
        },
        {
            "check_id": "failure_route_is_readonly_and_review_gated",
            "passed": (
                failure_routing.get("operator_review_required_before_tuning") is True
                and queue_policy.get("runtime_mutation_allowed") is False
                and queue_policy.get("chart_fact_mutation_allowed") is False
                and queue_policy.get("policy_pointer_promotion_allowed") is False
                and queue_policy.get("auto_apply_training_allowed") is False
            ),
            "observed": failure_routing,
        },
        {
            "check_id": "truth_label_and_write_boundaries_locked",
            "passed": (
                pack_summary.get("uses_real_person_truth") is False
                and pack_summary.get("chart_fact_mutation_allowed") is False
                and pack_summary.get("auto_apply_training_allowed") is False
                and pack_summary.get("policy_pointer_promotion_allowed") is False
            ),
            "observed": {
                "uses_real_person_truth": pack_summary.get("uses_real_person_truth"),
                "chart_fact_mutation_allowed": pack_summary.get("chart_fact_mutation_allowed"),
                "auto_apply_training_allowed": pack_summary.get("auto_apply_training_allowed"),
                "policy_pointer_promotion_allowed": pack_summary.get("policy_pointer_promotion_allowed"),
            },
        },
        {
            "check_id": "heavy_gates_explicit_only",
            "passed": (
                routine_gate.get("full_pytest_required") is False
                and routine_gate.get("synthetic_all_required") is False
                and routine_gate.get("full_518k_required") is False
                and pack_summary.get("full_pytest_required") is False
                and pack_summary.get("synthetic_all_required") is False
                and pack_summary.get("full_518k_required") is False
            ),
            "observed": {
                "routine_full_pytest_required": routine_gate.get("full_pytest_required"),
                "routine_synthetic_all_required": routine_gate.get("synthetic_all_required"),
                "routine_full_518k_required": routine_gate.get("full_518k_required"),
            },
        },
    ]


def _decision(checks: list[Mapping[str, Any]], pack_summary: Mapping[str, Any]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "synthetic_canonical_steady_state_ready": ready,
        "decision_status": "scal_s3_synthetic_canonical_steady_state_ready" if ready else "scal_s3_synthetic_canonical_steady_state_blocked",
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "case_count": int(pack_summary.get("case_count", 0) or 0),
        "covered_family_count": int(pack_summary.get("covered_family_count", 0) or 0),
        "routine_gate_ready": ready,
        "waiting_for_synthetic_canonical_trigger": ready,
        "chart_fact_mutation_allowed": False,
        "auto_apply_training_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "blockers": ["synthetic_canonical_steady_state_checks_failed"] if failed else [],
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("synthetic_canonical_steady_state_ready"):
        return {
            "task_id": "SCAL-S3-WAIT",
            "title": "Synthetic Canonical Calibration Await Trigger",
            "selected_track": "synthetic_canonical_calibration",
            "scope": [
                "run the frozen 16-case gate after RBD/M3/M5/IQ changes",
                "run before release-boundary validation",
                "route failures to read-only calibration review",
            ],
        }
    return {
        "task_id": "SCAL-S3-FR",
        "title": "Synthetic Canonical Steady State Failure Review",
        "selected_track": "synthetic_canonical_calibration",
        "scope": [
            "repair SCAL-S2 pack decision or routine gate blockers",
            "keep failures read-only",
            "do not introduce real-person truth labels",
        ],
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
