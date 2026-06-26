from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.synthetic_archetype_rule_claim_calibration import (
    SYNTHETIC_ARCHETYPE_RULE_CLAIM_CALIBRATION_VERSION,
    run_synthetic_archetype_rule_claim_calibration,
)
from v30.validation.synthetic_case import SYNTHETIC_ARCHETYPE_RULE_CLAIM_CASES, SYNTHETIC_SUITES, run_synthetic_tier


SYNTHETIC_ARCHETYPE_TIER_REGISTRATION_VERSION = "v30.synthetic_archetype_tier_registration.v1"
TARGET_TIER = "synthetic_archetype_rule_claim"


def run_synthetic_archetype_tier_registration() -> dict[str, Any]:
    tier = run_synthetic_tier(TARGET_TIER)
    calibration = run_synthetic_archetype_rule_claim_calibration()
    return build_synthetic_archetype_tier_registration(
        synthetic_tier=tier.model_dump(mode="json"),
        archetype_calibration=calibration,
    )


def build_synthetic_archetype_tier_registration(
    *,
    synthetic_tier: Mapping[str, Any],
    archetype_calibration: Mapping[str, Any],
) -> dict[str, Any]:
    registered_at = datetime.now(timezone.utc)
    tier_summary = _tier_summary(synthetic_tier)
    calibration_summary = _calibration_summary(archetype_calibration)
    queue_items = _queue_items(archetype_calibration)
    checks = _checks(tier_summary, calibration_summary, queue_items)
    decision = _decision(checks, queue_items)
    return {
        "version": SYNTHETIC_ARCHETYPE_TIER_REGISTRATION_VERSION,
        "registered_at": registered_at.isoformat(),
        "status": "completed" if decision["synthetic_archetype_tier_registration_ready"] else "blocked",
        "task": {
            "task_id": "SYN-CAL2",
            "title": "Synthetic Archetype Calibration Queue And Tier Registration",
            "scope": "register_syn_cal1_as_targeted_synthetic_tier_and_wire_readonly_calibration_queue",
        },
        "tier_summary": tier_summary,
        "archetype_calibration_summary": calibration_summary,
        "calibration_queue_items": queue_items,
        "checks": checks,
        "decision": decision,
        "tier_contract": {
            "tier": TARGET_TIER,
            "command": f"python3 scripts/run_synthetic_validation.py --tier {TARGET_TIER}",
            "routine_targeted_gate": True,
            "included_in_synthetic_all": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
            "real_person_truth_label_allowed": False,
            "boundary": "synthetic_archetype_tier_is_targeted_calibration_not_full_release_gate",
        },
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
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "syn_cal2_registers_targeted_archetype_tier_and_readonly_queue_without_mutation",
    }


def _tier_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "suite_id": str(payload.get("suite_id") or ""),
        "passed": bool(payload.get("passed")),
        "case_count": int(payload.get("case_count", 0) or 0),
        "passed_count": int(payload.get("passed_count", 0) or 0),
        "failed_count": int(payload.get("failed_count", 0) or 0),
        "registered_case_count": len(SYNTHETIC_ARCHETYPE_RULE_CLAIM_CASES),
        "suite_registered": TARGET_TIER in SYNTHETIC_SUITES,
        "case_ids": [str(row.get("case_id") or "") for row in _list(payload.get("results"))],
        "failed_case_ids": [
            str(row.get("case_id") or "")
            for row in _list(payload.get("results"))
            if row.get("passed") is not True
        ],
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
        "failed_case_ids": list(decision.get("failed_case_ids") or []),
        "external_release_allowed": bool(decision.get("external_release_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "auto_apply_training_allowed": bool(decision.get("auto_apply_training_allowed")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
    }


def _queue_items(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in _list(payload.get("calibration_queue")):
        item = _mapping(row)
        rows.append(
            {
                "queue_item_id": str(item.get("queue_item_id") or ""),
                "case_id": str(item.get("case_id") or ""),
                "target_modules": _str_list(item.get("target_modules")),
                "failed_check_ids": _str_list(item.get("failed_check_ids")),
                "review_only": item.get("review_only") is True,
                "chart_fact_mutation_allowed": bool(item.get("chart_fact_mutation_allowed")),
                "auto_apply_training_allowed": bool(item.get("auto_apply_training_allowed")),
                "policy_pointer_promotion_allowed": bool(item.get("policy_pointer_promotion_allowed")),
                "boundary": str(item.get("boundary") or ""),
            }
        )
    return rows


def _checks(
    tier: Mapping[str, Any],
    calibration: Mapping[str, Any],
    queue_items: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "synthetic_archetype_tier_registered",
            "passed": tier["suite_registered"] and tier["suite_id"] == f"v30.synthetic.{TARGET_TIER}",
            "observed": {"suite_id": tier["suite_id"], "suite_registered": tier["suite_registered"]},
        },
        {
            "check_id": "synthetic_archetype_tier_passes_current_runtime",
            "passed": tier["passed"] and tier["case_count"] == tier["registered_case_count"] and tier["failed_count"] == 0,
            "observed": tier,
        },
        {
            "check_id": "syn_cal1_artifact_ready",
            "passed": calibration["version"] == SYNTHETIC_ARCHETYPE_RULE_CLAIM_CALIBRATION_VERSION
            and calibration["ready"]
            and calibration["case_count"] == tier["registered_case_count"],
            "observed": calibration,
        },
        {
            "check_id": "calibration_queue_readonly_when_present",
            "passed": all(
                row.get("review_only") is True
                and row.get("chart_fact_mutation_allowed") is False
                and row.get("auto_apply_training_allowed") is False
                and row.get("policy_pointer_promotion_allowed") is False
                for row in queue_items
            ),
            "observed": {"queue_item_count": len(queue_items), "queue_items": queue_items},
        },
        {
            "check_id": "targeted_tier_not_default_heavy_gate",
            "passed": True,
            "observed": {
                "included_in_synthetic_all": False,
                "full_pytest_required": False,
                "full_518k_required": False,
                "live_llm_required": False,
            },
        },
        {
            "check_id": "no_real_person_truth_or_chart_fact_mutation",
            "passed": not calibration["external_release_allowed"]
            and not calibration["chart_fact_mutation_allowed"]
            and not calibration["auto_apply_training_allowed"]
            and not calibration["policy_pointer_promotion_allowed"],
            "observed": calibration,
        },
    ]


def _decision(checks: list[Mapping[str, Any]], queue_items: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "synthetic_archetype_tier_registration_ready": ready,
        "decision_status": "syn_cal2_tier_registration_ready" if ready else "syn_cal2_tier_registration_blocked",
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "calibration_queue_item_count": len(queue_items),
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
    if decision["synthetic_archetype_tier_registration_ready"]:
        return {
            "task_id": "SYN-CAL3",
            "title": "Synthetic Archetype Training Signal Review",
            "selected_track": "synthetic_archetype_calibration",
            "scope": [
                "derive review-only training signals from archetype outcomes",
                "route signal targets to M3/M5/M6 calibration only",
                "keep chart facts, auto-apply training, and pointer promotion disabled",
            ],
        }
    return {
        "task_id": "SYN-CAL2-FR",
        "title": "Synthetic Archetype Tier Registration Failure Review",
        "selected_track": "synthetic_archetype_calibration",
        "scope": [
            "repair tier registration or readonly queue evidence",
            "do not run heavy or live gates while blocked",
            "do not mutate chart facts or promote pointers",
        ],
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _str_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(row) for row in value if str(row)]
    return []
