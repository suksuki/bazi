from __future__ import annotations

from copy import deepcopy

from v30.validation.bazi_backend_api_journey_acceptance import (
    BAZI_BACKEND_API_JOURNEY_ACCEPTANCE_VERSION,
    build_bazi_backend_api_journey_acceptance,
    run_bazi_backend_api_journey_acceptance,
)


def test_ir2_bazi_backend_api_journey_acceptance_ready() -> None:
    result = run_bazi_backend_api_journey_acceptance(reading_id="pytest-ir2-api")

    assert result["version"] == BAZI_BACKEND_API_JOURNEY_ACCEPTANCE_VERSION
    assert result["decision"]["api_journey_ready"] is True
    assert result["decision"]["decision_status"] == "ir2_bazi_backend_api_journey_accepted"
    assert result["decision"]["passed_check_count"] == 6
    assert result["journey_summary"]["created_status"] == "ready"
    assert result["journey_summary"]["core_bazi_reading_version"] == "v30.core_bazi_reading.v1"
    assert result["journey_summary"]["hidden_factor_state_status"] in {
        "amplifier_candidate",
        "dialogue_in_progress",
    }
    assert result["journey_summary"]["ir1_ready"] is True
    assert result["next_mainline_selection"]["task_id"] == "IR-S1"
    assert result["decision"]["full_pytest_required"] is False
    assert result["decision"]["policy_pointer_write_allowed"] is False


def test_ir2_blocks_missing_hidden_factor_rehydration() -> None:
    ready = run_bazi_backend_api_journey_acceptance(reading_id="pytest-ir2-hidden-block")
    evidence = deepcopy(ready["journey_summary"])
    evidence["admin_hidden_factor_state_visible"] = False

    result = build_bazi_backend_api_journey_acceptance(evidence=evidence)

    assert result["decision"]["api_journey_ready"] is False
    assert "hidden_factor_feedback_persists_and_rehydrates_as_calibration_state" in result["decision"]["failed_check_ids"]
    assert result["decision"]["chart_fact_mutation_allowed"] is False


def test_ir2_admin_endpoint_is_read_only() -> None:
    from v30.api.app import create_app

    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/mainline/bazi-backend-api-journey-acceptance"
    )
    payload = route.endpoint(reading_id="pytest-ir2-admin")

    assert payload["version"] == BAZI_BACKEND_API_JOURNEY_ACCEPTANCE_VERSION
    assert payload["decision"]["api_journey_ready"] is True
    assert payload["decision"]["live_llm_required"] is False
    assert payload["decision"]["policy_pointer_write_allowed"] is False
    assert payload["boundary"] == (
        "ir2_validates_backend_api_journey_without_live_llm_full_pytest_or_policy_promotion"
    )
