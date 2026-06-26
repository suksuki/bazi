from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.real_bazi_training_calibration_queue import (
    REAL_BAZI_TRAINING_CALIBRATION_QUEUE_VERSION,
    run_real_bazi_training_calibration_queue,
)


REAL_BAZI_DIAGNOSIS_STEADY_STATE_VERSION = "v30.real_bazi_diagnosis_steady_state.v1"


def run_real_bazi_diagnosis_steady_state(
    *,
    real_case_limit: int = 8,
    sample_518k_limit: int = 8,
) -> dict[str, Any]:
    queue = run_real_bazi_training_calibration_queue(
        real_case_limit=real_case_limit,
        sample_518k_limit=sample_518k_limit,
    )
    return build_real_bazi_diagnosis_steady_state(training_calibration_queue=queue)


def build_real_bazi_diagnosis_steady_state(
    *,
    training_calibration_queue: Mapping[str, Any],
) -> dict[str, Any]:
    closed_at = datetime.now(timezone.utc)
    queue_summary = _queue_summary(training_calibration_queue)
    module_summary = _module_summary(queue_summary)
    routine_cadence = _routine_cadence(queue_summary)
    closeout_checks = _closeout_checks(queue_summary, module_summary, routine_cadence)
    decision = _decision(queue_summary, closeout_checks)
    return {
        "version": REAL_BAZI_DIAGNOSIS_STEADY_STATE_VERSION,
        "closed_at": closed_at.isoformat(),
        "status": "completed" if decision["rbd_steady_state_ready"] else "blocked",
        "task": {
            "task_id": "RBD-S1.13",
            "title": "RBD Mainline Closeout And Steady State",
            "scope": "record_current_real_bazi_diagnosis_spine_as_usable_and_define_readonly_calibration_cadence",
        },
        "decision": decision,
        "training_calibration_queue_summary": queue_summary,
        "rbd_module_summary": module_summary,
        "routine_cadence": routine_cadence,
        "closeout_checks": closeout_checks,
        "reopen_conditions": _reopen_conditions(),
        "policy_boundary": {
            "rbd_mainline_closed_for_current_scope": decision["rbd_steady_state_ready"],
            "routine_replay_allowed": decision["rbd_steady_state_ready"],
            "calibration_queue_readonly": True,
            "new_weight_tuning_requires_explicit_review": True,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "boundary": "rbd_s113_closes_current_mainline_without_reopening_core_modules_or_promoting_pointers",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "rbd_steady_state_records_usable_diagnosis_spine_not_final_bazi_truth",
    }


def _queue_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    policy = _mapping(payload.get("policy_boundary"))
    upstream = _mapping(payload.get("upstream_summary"))
    upstream_decision = _mapping(_mapping(upstream.get("decision")))
    real_case = _mapping(upstream.get("real_case_summary"))
    sample = _mapping(upstream.get("sample_518k_summary"))
    queue_items = _list(payload.get("calibration_queue_items"))
    training_signals = _list(payload.get("training_signals"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "training_calibration_queue_ready": bool(decision.get("training_calibration_queue_ready")),
        "training_signal_count": int(decision.get("training_signal_count", 0) or 0),
        "queued_item_count": int(decision.get("queued_item_count", 0) or 0),
        "training_signal_ids": [
            str(row.get("signal_id") or "") for row in training_signals if isinstance(row, Mapping)
        ],
        "queued_domains": [
            str(row.get("target_domain") or "") for row in queue_items if isinstance(row, Mapping)
        ],
        "queue_items_are_readonly": all(
            isinstance(row, Mapping)
            and row.get("runtime_mutation_allowed") is False
            and row.get("chart_fact_mutation_allowed") is False
            and row.get("policy_pointer_promotion_allowed") is False
            for row in queue_items
        ),
        "signals_are_readonly": all(
            isinstance(row, Mapping)
            and row.get("runtime_mutation_allowed") is False
            and row.get("chart_fact_mutation_allowed") is False
            and row.get("policy_pointer_promotion_allowed") is False
            for row in training_signals
        ),
        "auto_apply_training_allowed": bool(policy.get("auto_apply_training_allowed")),
        "chart_fact_mutation_allowed": bool(policy.get("chart_fact_mutation_allowed")),
        "policy_pointer_promotion_allowed": bool(policy.get("policy_pointer_promotion_allowed")),
        "full_pytest_required": bool(policy.get("full_pytest_required")),
        "synthetic_all_required": bool(policy.get("synthetic_all_required")),
        "full_518k_required": bool(policy.get("full_518k_required")),
        "upstream_distribution_replay_ready": bool(upstream_decision.get("distribution_replay_ready")),
        "real_case_ready_ratio": float(real_case.get("ready_ratio", 0.0) or 0.0),
        "sample_518k_ready_ratio": float(sample.get("ready_ratio", 0.0) or 0.0),
        "real_case_replay_count": int(real_case.get("replay_case_count", 0) or 0),
        "sample_518k_replay_count": int(sample.get("replay_case_count", 0) or 0),
        "generic_language_hit_count": int(real_case.get("generic_language_hit_count", 0) or 0)
        + int(sample.get("generic_language_hit_count", 0) or 0),
        "customer_internal_leak_count": int(real_case.get("customer_internal_leak_count", 0) or 0)
        + int(sample.get("customer_internal_leak_count", 0) or 0),
    }


def _module_summary(queue_summary: Mapping[str, Any]) -> dict[str, Any]:
    completed_stages = [
        "RBD-S1.1 contracts",
        "RBD-S1.2 rule matcher",
        "RBD-S1.3 path engine",
        "RBD-S1.4 feature and portrait engine",
        "RBD-S1.5 claim generator",
        "RBD-S1.6 graph and router",
        "RBD-S1.7 runtime and projection",
        "RBD-S1.8 storage contract",
        "RBD-S1.9 synthetic tier",
        "RBD-S1.10 product reading acceptance",
        "RBD-S1.11 distribution replay",
        "RBD-S1.12 training signal and calibration queue",
    ]
    return {
        "module_id": "RBD",
        "module_name": "Real Bazi Diagnosis Engine",
        "module_status": "steady_core_diagnosis_spine" if queue_summary["training_calibration_queue_ready"] else "blocked",
        "completed_stage_count": len(completed_stages),
        "completed_stages": completed_stages,
        "supported_domains": ["career", "wealth", "relationship", "health", "timing"],
        "usable_for_customer_reading": bool(queue_summary["training_calibration_queue_ready"]),
        "usable_for_practitioner_review": bool(queue_summary["training_calibration_queue_ready"]),
        "admin_diagnostics_available": bool(queue_summary["training_calibration_queue_ready"]),
        "calibration_queue_domains": list(queue_summary["queued_domains"]),
        "boundary": "rbd_supports_real_bazi_diagnosis_claims_paths_portraits_and_readonly_calibration",
    }


def _routine_cadence(queue_summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "cadence_id": "rbd_steady_state_routine_cadence",
        "routine_commands": [
            "python3 scripts/run_real_bazi_training_calibration_queue.py",
            "python3 scripts/run_synthetic_validation.py --tier real_bazi_diagnosis",
        ],
        "major_node_commands_explicit_only": [
            "python3 scripts/run_synthetic_validation.py --tier all",
            "pytest -q",
            "python3 scripts/run_518k_validation.py --mode full --confirm-full",
        ],
        "watched_metrics": {
            "training_signal_count": int(queue_summary.get("training_signal_count", 0) or 0),
            "queued_item_count": int(queue_summary.get("queued_item_count", 0) or 0),
            "queued_domains": list(queue_summary.get("queued_domains", [])),
            "real_case_ready_ratio": queue_summary.get("real_case_ready_ratio"),
            "sample_518k_ready_ratio": queue_summary.get("sample_518k_ready_ratio"),
            "generic_language_hit_count": queue_summary.get("generic_language_hit_count"),
            "customer_internal_leak_count": queue_summary.get("customer_internal_leak_count"),
        },
        "replay_before_release": True,
        "replay_after_new_real_case_pack": True,
        "calibration_review_required_before_tuning": True,
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "boundary": "routine_cadence_uses_targeted_rbd_gates_and_keeps_heavy_gates_explicit",
    }


def _closeout_checks(
    queue_summary: Mapping[str, Any],
    module_summary: Mapping[str, Any],
    routine_cadence: Mapping[str, Any],
) -> list[dict[str, Any]]:
    required_signal_ids = {
        "v30.training_signal.rbd_product_reading_acceptance",
        "v30.training_signal.rbd_distribution_replay_quality",
        "v30.training_signal.rbd_domain_coverage",
        "v30.training_signal.rbd_projection_safety",
    }
    return [
        {
            "check_id": "rbd_s112_training_queue_ready",
            "passed": (
                queue_summary["version"] == REAL_BAZI_TRAINING_CALIBRATION_QUEUE_VERSION
                and queue_summary["training_calibration_queue_ready"]
                and queue_summary["decision_status"] == "rbd_s112_training_calibration_queue_ready"
            ),
            "expected": "S1.12 training/calibration queue is ready",
        },
        {
            "check_id": "rbd_replay_quality_stable",
            "passed": (
                queue_summary["upstream_distribution_replay_ready"]
                and queue_summary["real_case_ready_ratio"] >= 1.0
                and queue_summary["sample_518k_ready_ratio"] >= 1.0
                and queue_summary["real_case_replay_count"] >= 8
                and queue_summary["sample_518k_replay_count"] >= 8
                and queue_summary["generic_language_hit_count"] == 0
                and queue_summary["customer_internal_leak_count"] == 0
            ),
            "expected": "S1.11 replay remains clean for current lightweight real-case and 518K sample gates",
        },
        {
            "check_id": "rbd_training_signals_complete",
            "passed": (
                queue_summary["training_signal_count"] >= 4
                and required_signal_ids.issubset(set(queue_summary["training_signal_ids"]))
                and queue_summary["signals_are_readonly"]
            ),
            "expected": "RBD has complete read-only training signal candidates",
        },
        {
            "check_id": "rbd_calibration_queue_readonly",
            "passed": (
                queue_summary["queued_item_count"] >= 1
                and queue_summary["queue_items_are_readonly"]
                and not queue_summary["auto_apply_training_allowed"]
                and not queue_summary["chart_fact_mutation_allowed"]
                and not queue_summary["policy_pointer_promotion_allowed"]
            ),
            "expected": "calibration queue exists but cannot write runtime facts, train automatically, or promote policy",
        },
        {
            "check_id": "rbd_module_spine_complete_for_current_scope",
            "passed": (
                module_summary["completed_stage_count"] >= 12
                and set(module_summary["supported_domains"]) == {"career", "wealth", "relationship", "health", "timing"}
                and module_summary["usable_for_customer_reading"]
                and module_summary["usable_for_practitioner_review"]
                and module_summary["admin_diagnostics_available"]
            ),
            "expected": "RBD supports customer reading, practitioner review, and admin diagnostics for five domains",
        },
        {
            "check_id": "rbd_heavy_gates_explicit_only",
            "passed": (
                not queue_summary["full_pytest_required"]
                and not queue_summary["synthetic_all_required"]
                and not queue_summary["full_518k_required"]
                and not routine_cadence["full_pytest_required"]
                and not routine_cadence["synthetic_all_required"]
                and not routine_cadence["full_518k_required"]
            ),
            "expected": "full pytest, synthetic all, and full 518K are not routine S1.13 gates",
        },
    ]


def _decision(
    queue_summary: Mapping[str, Any],
    closeout_checks: list[Mapping[str, Any]],
) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in closeout_checks if row.get("passed") is not True]
    ready = not failed
    return {
        "rbd_steady_state_ready": ready,
        "decision_status": "rbd_s113_steady_state_ready" if ready else "rbd_s113_steady_state_blocked",
        "closeout_check_count": len(closeout_checks),
        "passed_closeout_check_count": len(closeout_checks) - len(failed),
        "failed_closeout_check_ids": failed,
        "rbd_mainline_closed_for_current_scope": ready,
        "waiting_for_new_rbd_evidence": ready,
        "routine_replay_ready": ready,
        "training_signal_count": int(queue_summary.get("training_signal_count", 0) or 0),
        "queued_item_count": int(queue_summary.get("queued_item_count", 0) or 0),
        "queued_domains": list(queue_summary.get("queued_domains", [])),
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "chart_fact_mutation_allowed": False,
        "auto_apply_training_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "blockers": ["rbd_steady_state_closeout_checks_failed"] if failed else [],
        "rationale": (
            "RBD is steady for the current core diagnosis scope: serve readings through the RBD spine, run targeted replay routinely, and hold calibration items for explicit evidence review."
            if ready
            else "RBD cannot close out until the training queue and replay quality checks are repaired."
        ),
    }


def _reopen_conditions() -> list[dict[str, Any]]:
    return [
        {
            "condition": "new_real_case_replay_failure",
            "route": "RBD-S1.11 distribution replay failure review",
            "description": "a ready real-case or 518K sample replay produces generic language, projection leak, or insufficient RBD domain evidence",
        },
        {
            "condition": "calibration_queue_item_approved",
            "route": "RBD calibration candidate review",
            "description": "a queued domain gap receives explicit human/evidence approval for tuning review",
        },
        {
            "condition": "diagnosis_claim_regression",
            "route": "RBD-S1.10 product reading acceptance",
            "description": "customer or practitioner answer falls back to generic wording instead of RBD-backed claims and paths",
        },
        {
            "condition": "explicit_major_validation_request",
            "route": "major validation or release-boundary track",
            "description": "full pytest, synthetic all, full 518K, live LLM, or pointer decision remains separate",
        },
    ]


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["rbd_steady_state_ready"]:
        return {
            "task_id": "RBD-S1-WAIT",
            "title": "RBD Steady State Await New Evidence",
            "selected_track": "real_bazi_diagnosis",
            "scope": [
                "use RBD as the current real Bazi diagnosis spine",
                "run targeted replay after new real-case packs or before release",
                "do not tune queued calibration domains until explicit evidence review",
            ],
        }
    return {
        "task_id": "RBD-S1.13-FR",
        "title": "RBD Steady State Failure Review",
        "selected_track": "real_bazi_diagnosis",
        "scope": [
            "repair failed closeout checks",
            "re-run S1.12 training/calibration queue",
            "keep heavy gates and pointer promotion explicit while blocked",
        ],
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
