from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.real_business_api_contract_freeze import run_real_business_api_contract_freeze


REAL_BUSINESS_ACCEPTANCE_CLOSEOUT_VERSION = "v30.real_business_acceptance_closeout.v1"


def run_real_business_acceptance_closeout() -> dict[str, Any]:
    b5 = run_real_business_api_contract_freeze()
    return build_real_business_acceptance_closeout(b5_api_contract_freeze=b5)


def build_real_business_acceptance_closeout(*, b5_api_contract_freeze: Mapping[str, Any]) -> dict[str, Any]:
    selected_at = datetime.now(timezone.utc)
    b5_summary = _b5_summary(b5_api_contract_freeze)
    closeout_checks = _closeout_checks(b5_summary)
    decision = _decision(b5_summary, closeout_checks)
    return {
        "version": REAL_BUSINESS_ACCEPTANCE_CLOSEOUT_VERSION,
        "selected_at": selected_at.isoformat(),
        "status": "completed" if decision["business_acceptance_closeout_ready"] else "blocked",
        "decision": decision,
        "b5_contract_summary": b5_summary,
        "closeout_checks": closeout_checks,
        "accepted_business_gate": {
            "version": "v30.business_reading_acceptance_gate.v1",
            "gate_status": "frozen_default_gate" if decision["business_acceptance_closeout_ready"] else "blocked",
            "required_tasks": ["B1", "B2", "B3", "B4", "B5"],
            "default_validation_command": "python3 scripts/run_real_business_api_contract_freeze.py",
            "major_validation_requires_explicit_request": True,
            "full_pytest_default": False,
            "full_518k_default": False,
            "external_release_default": False,
            "policy_pointer_promotion_default": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "business_acceptance_gate_is_default_product_gate_not_release_gate",
        },
        "deferred_tracks": _deferred_tracks(),
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "business_track_auto_continue_allowed": False,
            "boundary": "b6_closeout_pauses_business_track_without_release_or_pointer_promotion",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "b6_records_business_acceptance_closeout_after_contract_freeze",
    }


def _b5_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, Mapping) else {}
    freeze = payload.get("freeze_summary", {})
    freeze = freeze if isinstance(freeze, Mapping) else {}
    contract = payload.get("api_contract", {})
    contract = contract if isinstance(contract, Mapping) else {}
    additive = contract.get("additive_api_policy", {})
    additive = additive if isinstance(additive, Mapping) else {}
    policy = payload.get("policy_boundary", {})
    policy = policy if isinstance(policy, Mapping) else {}
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "api_contract_freeze_ready": bool(decision.get("api_contract_freeze_ready")),
        "gate_count": int(freeze.get("gate_count", 0) or 0),
        "passed_gate_count": int(freeze.get("passed_gate_count", 0) or 0),
        "failed_gate_count": int(freeze.get("failed_gate_count", 0) or 0),
        "minimum_business_acceptance": [str(row) for row in freeze.get("minimum_business_acceptance", [])]
        if isinstance(freeze.get("minimum_business_acceptance"), list) else [],
        "api_contract_version": str(contract.get("version") or ""),
        "contract_status": str(contract.get("contract_status") or ""),
        "field_removal_allowed": bool(additive.get("field_removal_allowed")),
        "new_fields_allowed": bool(additive.get("new_fields_allowed")),
        "forbidden_behavior_count": len(contract.get("forbidden_behaviors", []))
        if isinstance(contract.get("forbidden_behaviors"), list) else 0,
        "external_release_ready": bool(decision.get("external_release_ready")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "external_release_allowed": bool(policy.get("external_release_allowed")),
    }


def _closeout_checks(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "b5_contract_freeze_ready",
            "passed": (
                summary["version"] == "v30.real_business_api_contract_freeze.v1"
                and summary["api_contract_freeze_ready"]
                and summary["decision_status"] == "b5_business_api_contract_frozen"
            ),
            "expected": "B5 contract freeze ready",
        },
        {
            "check_id": "b1_b5_gate_complete",
            "passed": (
                summary["gate_count"] == 4
                and summary["passed_gate_count"] == 4
                and summary["failed_gate_count"] == 0
                and summary["minimum_business_acceptance"] == ["B1", "B2", "B3", "B4"]
            ),
            "expected": "B1-B4 passed and frozen by B5",
        },
        {
            "check_id": "api_contract_frozen_additive",
            "passed": (
                summary["api_contract_version"] == "v30.business_reading_api_contract.v1"
                and summary["contract_status"] == "frozen_for_current_business_acceptance_scope"
                and summary["field_removal_allowed"] is False
                and summary["new_fields_allowed"] is True
                and summary["forbidden_behavior_count"] >= 6
            ),
            "expected": "business API contract frozen and additive",
        },
        {
            "check_id": "no_release_heavy_pointer_or_fact_mutation",
            "passed": (
                not summary["external_release_ready"]
                and not summary["external_release_allowed"]
                and not summary["full_pytest_required"]
                and not summary["full_518k_required"]
                and not summary["policy_pointer_promotion_allowed"]
                and not summary["chart_fact_mutation_allowed"]
            ),
            "expected": "closeout does not authorize release, heavy validation, pointer promotion, or chart mutation",
        },
    ]


def _decision(summary: Mapping[str, Any], checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if not row.get("passed")]
    blockers: list[str] = []
    if failed:
        blockers.append("business_acceptance_closeout_checks_failed")
    ready = not blockers
    return {
        "business_acceptance_closeout_ready": ready,
        "decision_status": "b6_business_acceptance_closed" if ready else "b6_business_acceptance_closeout_blocked",
        "failed_check_ids": failed,
        "blockers": blockers,
        "business_track_paused": ready,
        "major_validation_requires_explicit_request": True,
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "rationale": (
            "B1-B5 are accepted as the default business Bazi reading gate; pause B-track unless a major validation gate is explicitly requested."
            if ready
            else "B6 cannot close until B5 contract-freeze blockers are resolved."
        ),
    }


def _deferred_tracks() -> list[dict[str, Any]]:
    return [
        {
            "track": "major_validation_gate",
            "reason": "requires explicit request because it may include synthetic all, 518K sample/full, or broader pytest",
        },
        {
            "track": "external_release",
            "reason": "business acceptance is not external release approval",
        },
        {
            "track": "policy_pointer_promotion",
            "reason": "business acceptance never writes active policy pointers",
        },
        {
            "track": "ui_expansion",
            "reason": "UI remains concise; business acceptance focuses on API/runtime measurement support",
        },
    ]


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("business_acceptance_closeout_ready"):
        return {
            "task_id": "S1",
            "title": "Business Acceptance Steady State",
            "selected_track": "business_bazi_acceptance",
            "scope": [
                "do not start another B-track task by default",
                "use B1-B5 gate for routine business reading acceptance",
                "request major validation explicitly when needed",
            ],
        }
    return {
        "task_id": "B6-FR",
        "title": "Business Acceptance Closeout Failure Review",
        "selected_track": "business_bazi_acceptance",
        "scope": [
            "repair B6 closeout blockers",
            "rerun B5 contract freeze",
            "keep full pytest and pointer promotion disabled while blocked",
        ],
    }
