from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.real_business_answer_refresh_regression import run_real_business_answer_refresh_regression
from v30.validation.real_business_bazi_reading_acceptance import run_real_business_bazi_reading_acceptance
from v30.validation.real_business_bazi_reading_regression_pack import run_real_business_bazi_reading_regression_pack
from v30.validation.real_business_boundary_blocked_input_regression import (
    run_real_business_boundary_blocked_input_regression,
)


REAL_BUSINESS_API_CONTRACT_FREEZE_VERSION = "v30.real_business_api_contract_freeze.v1"

REQUIRED_BUSINESS_ENDPOINTS = [
    "GET /api/v30/admin/business/real-bazi-acceptance",
    "GET /api/v30/admin/business/reading-regression-pack",
    "GET /api/v30/admin/business/answer-refresh-regression",
    "GET /api/v30/admin/business/boundary-blocked-input-regression",
    "GET /api/v30/readings/{reading_id}/view",
    "POST /api/v30/readings/{reading_id}/questions/{question_id}/answer",
]

REQUIRED_CUSTOMER_SURFACE_KEYS = [
    "reading_surface",
    "core_bazi_reading",
    "domain_cards",
    "questions",
    "answer_panel",
    "projection_contract",
    "actor_context",
    "llm_runtime_status",
]


def run_real_business_api_contract_freeze() -> dict[str, Any]:
    b1 = run_real_business_bazi_reading_acceptance(case_limit=12)
    b2 = run_real_business_bazi_reading_regression_pack(case_limit=24)
    b3 = run_real_business_answer_refresh_regression(case_limit=5)
    b4 = run_real_business_boundary_blocked_input_regression(case_limit=5)
    return build_real_business_api_contract_freeze(
        b1_acceptance=b1,
        b2_regression_pack=b2,
        b3_answer_refresh=b3,
        b4_boundary_regression=b4,
    )


def build_real_business_api_contract_freeze(
    *,
    b1_acceptance: Mapping[str, Any],
    b2_regression_pack: Mapping[str, Any],
    b3_answer_refresh: Mapping[str, Any],
    b4_boundary_regression: Mapping[str, Any],
) -> dict[str, Any]:
    gates = [
        _gate(
            "B1",
            b1_acceptance,
            expected_version="v30.real_business_bazi_reading_acceptance.v1",
            decision_key="business_bazi_reading_ready",
            expected_status="b1_real_business_bazi_reading_accepted",
        ),
        _gate(
            "B2",
            b2_regression_pack,
            expected_version="v30.real_business_bazi_reading_regression_pack.v1",
            decision_key="business_reading_regression_ready",
            expected_status="b2_business_reading_regression_pack_ready",
        ),
        _gate(
            "B3",
            b3_answer_refresh,
            expected_version="v30.real_business_answer_refresh_regression.v1",
            decision_key="answer_refresh_regression_ready",
            expected_status="b3_answer_refresh_regression_ready",
        ),
        _gate(
            "B4",
            b4_boundary_regression,
            expected_version="v30.real_business_boundary_blocked_input_regression.v1",
            decision_key="boundary_blocked_input_ready",
            expected_status="b4_boundary_blocked_input_regression_ready",
        ),
    ]
    contract = _contract()
    decision = _decision(gates)
    return {
        "version": REAL_BUSINESS_API_CONTRACT_FREEZE_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["api_contract_freeze_ready"] else "blocked",
        "decision": decision,
        "business_acceptance_gates": gates,
        "api_contract": contract,
        "freeze_summary": {
            "gate_count": len(gates),
            "passed_gate_count": sum(1 for gate in gates if gate["passed"]),
            "failed_gate_count": sum(1 for gate in gates if not gate["passed"]),
            "business_endpoint_count": len(REQUIRED_BUSINESS_ENDPOINTS),
            "customer_surface_key_count": len(REQUIRED_CUSTOMER_SURFACE_KEYS),
            "minimum_business_acceptance": ["B1", "B2", "B3", "B4"],
        },
        "policy_boundary": {
            "full_pytest_run_by_default": False,
            "full_518k_run_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "training_signal_may_change_chart_facts": False,
            "external_release_allowed": False,
            "boundary": "b5_freezes_business_api_contract_without_release_or_pointer_promotion",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "b5_records_business_reading_api_contract_after_b1_b4_acceptance",
    }


def _gate(
    gate_id: str,
    payload: Mapping[str, Any],
    *,
    expected_version: str,
    decision_key: str,
    expected_status: str,
) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, Mapping) else {}
    passed = (
        payload.get("version") == expected_version
        and decision.get(decision_key) is True
        and decision.get("decision_status") == expected_status
        and decision.get("full_pytest_required") is False
        and decision.get("full_518k_required") is False
        and decision.get("policy_pointer_promotion_allowed") is False
        and decision.get("chart_fact_mutation_allowed") is False
    )
    return {
        "gate_id": gate_id,
        "version": str(payload.get("version") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "passed": passed,
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "boundary": "business_acceptance_gate_is_read_only_and_non_mutating",
    }


def _contract() -> dict[str, Any]:
    return {
        "version": "v30.business_reading_api_contract.v1",
        "contract_status": "frozen_for_current_business_acceptance_scope",
        "required_endpoints": REQUIRED_BUSINESS_ENDPOINTS,
        "customer_surface_required_keys": REQUIRED_CUSTOMER_SURFACE_KEYS,
        "ready_reading_requirements": {
            "minimum_b1_ready_cases": 12,
            "minimum_b2_regression_cases": 24,
            "minimum_domain_cards": 5,
            "required_domain_cards": ["career", "wealth", "relationship", "health", "timing"],
            "answer_refresh_cases": 5,
            "boundary_non_ready_cases": 5,
        },
        "additive_api_policy": {
            "field_removal_allowed": False,
            "new_fields_allowed": True,
            "must_preserve": REQUIRED_CUSTOMER_SURFACE_KEYS,
            "boundary": "business_api_contract_is_additive_for_customer_reading_surface",
        },
        "forbidden_behaviors": [
            "fabricate_pillars_for_pending_or_blocked_birth_input",
            "promote_m4_m5_m6_ready_state_without_ready_chart",
            "mutate_chart_facts_from_answer_feedback",
            "expose_policy_effect_raw_score_or_training_signal_to_customer",
            "run_full_pytest_or_full_518k_by_default",
            "promote_policy_pointer_from_business_contract_freeze",
        ],
        "boundary": "business_api_contract_freezes_shape_and_non_mutation_policy_not_final_release",
    }


def _decision(gates: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(gate.get("gate_id") or "") for gate in gates if not gate.get("passed")]
    ready = not failed
    return {
        "api_contract_freeze_ready": ready,
        "decision_status": "b5_business_api_contract_frozen" if ready else "b5_business_api_contract_freeze_blocked",
        "failed_gate_ids": failed,
        "blockers": ["business_acceptance_gates_failed"] if failed else [],
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "external_release_ready": False,
        "rationale": (
            "B5 ready: B1-B4 form the frozen minimum business reading API acceptance contract."
            if ready
            else "B5 blocked: all B1-B4 gates must pass before freezing the business reading API contract."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("api_contract_freeze_ready"):
        return {
            "task_id": "B6",
            "title": "Business Reading Acceptance Closeout",
            "selected_track": "business_bazi_acceptance",
            "scope": [
                "record B1-B5 as the default business acceptance gate",
                "decide whether to pause B-track or request an explicit major validation gate",
                "keep release/full-pytest/pointer promotion separate",
            ],
        }
    return {
        "task_id": "B5-FR",
        "title": "Business API Contract Freeze Failure Review",
        "selected_track": "business_bazi_acceptance",
        "scope": [
            "repair failed B1-B4 gates",
            "do not freeze the API contract while acceptance gates fail",
            "do not run full pytest unless release/full-freeze is explicitly requested",
        ],
    }
