from __future__ import annotations

from copy import deepcopy

from v30.validation.real_business_api_contract_freeze import (
    REAL_BUSINESS_API_CONTRACT_FREEZE_VERSION,
    build_real_business_api_contract_freeze,
)


def _gate(version: str, key: str, status: str) -> dict[str, object]:
    return {
        "version": version,
        "decision": {
            key: True,
            "decision_status": status,
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
    }


def _payloads() -> dict[str, dict[str, object]]:
    return {
        "b1": _gate(
            "v30.real_business_bazi_reading_acceptance.v1",
            "business_bazi_reading_ready",
            "b1_real_business_bazi_reading_accepted",
        ),
        "b2": _gate(
            "v30.real_business_bazi_reading_regression_pack.v1",
            "business_reading_regression_ready",
            "b2_business_reading_regression_pack_ready",
        ),
        "b3": _gate(
            "v30.real_business_answer_refresh_regression.v1",
            "answer_refresh_regression_ready",
            "b3_answer_refresh_regression_ready",
        ),
        "b4": _gate(
            "v30.real_business_boundary_blocked_input_regression.v1",
            "boundary_blocked_input_ready",
            "b4_boundary_blocked_input_regression_ready",
        ),
    }


def test_b5_freezes_business_reading_api_contract_after_b1_b4_pass() -> None:
    payloads = _payloads()
    result = build_real_business_api_contract_freeze(
        b1_acceptance=payloads["b1"],
        b2_regression_pack=payloads["b2"],
        b3_answer_refresh=payloads["b3"],
        b4_boundary_regression=payloads["b4"],
    )

    assert result["version"] == REAL_BUSINESS_API_CONTRACT_FREEZE_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "b5_business_api_contract_frozen"
    assert result["freeze_summary"]["passed_gate_count"] == 4
    assert result["api_contract"]["version"] == "v30.business_reading_api_contract.v1"
    assert "reading_surface" in result["api_contract"]["customer_surface_required_keys"]
    assert result["api_contract"]["additive_api_policy"]["field_removal_allowed"] is False
    assert result["decision"]["external_release_ready"] is False
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "B6"


def test_b5_blocks_when_any_business_gate_fails() -> None:
    payloads = _payloads()
    broken = deepcopy(payloads["b3"])
    broken["decision"]["answer_refresh_regression_ready"] = False  # type: ignore[index]
    payloads["b3"] = broken

    result = build_real_business_api_contract_freeze(
        b1_acceptance=payloads["b1"],
        b2_regression_pack=payloads["b2"],
        b3_answer_refresh=payloads["b3"],
        b4_boundary_regression=payloads["b4"],
    )

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "b5_business_api_contract_freeze_blocked"
    assert result["decision"]["failed_gate_ids"] == ["B3"]
    assert "business_acceptance_gates_failed" in result["decision"]["blockers"]
    assert result["decision"]["chart_fact_mutation_allowed"] is False
