from __future__ import annotations

from v30.validation.customer_surface_bazi_context_reconciliation import (
    CUSTOMER_SURFACE_BAZI_CONTEXT_RECONCILIATION_VERSION,
    run_customer_surface_bazi_context_reconciliation,
)


def test_mcr2_reconciles_customer_surface_and_bazi_context() -> None:
    result = run_customer_surface_bazi_context_reconciliation(reading_id="pytest-mcr2")

    assert result["version"] == CUSTOMER_SURFACE_BAZI_CONTEXT_RECONCILIATION_VERSION
    assert result["decision"]["customer_surface_bazi_context_reconciled"] is True
    assert result["decision"]["decision_status"] == "mcr2_customer_surface_bazi_context_reconciled"
    assert result["decision"]["passed_count"] == 6
    assert result["decision"]["full_pytest_required"] is False
    assert result["decision"]["synthetic_all_required"] is False
    assert result["decision"]["full_518k_required"] is False
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "M3-G1"
    assert result["next_mainline_selection"]["full_pytest_run_now"] is False

    matrix = {row["module_id"]: row for row in result["module_completion_matrix"]}
    assert matrix["SURFACE"]["completion"] == 100
    assert matrix["SURFACE"]["status"] == "steady"
    assert matrix["CTX"]["completion"] == 100
    assert matrix["CTX"]["status"] == "steady"

    customer = result["evidence"]["customer_surface"]
    assert customer["core_bazi_reading_type"] == "core_bazi_calculation"
    assert customer["calculation_before_questions"] is True

    boundary = result["evidence"]["customer_boundary"]
    assert boundary["diagnostics_hidden"] is True
    assert boundary["forbidden_token_hits"] == []

    diagnostic = result["evidence"]["diagnostic_projection"]
    assert diagnostic["admin_has_bazi_context"] is True
    assert diagnostic["practitioner_has_bazi_context"] is True


def test_mcr2_admin_endpoint_is_read_only() -> None:
    from v30.api.app import create_app

    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/mainline/customer-surface-bazi-context-reconciliation"
    )
    payload = route.endpoint(reading_id="pytest-mcr2-admin")

    assert payload["version"] == CUSTOMER_SURFACE_BAZI_CONTEXT_RECONCILIATION_VERSION
    assert payload["decision"]["customer_surface_bazi_context_reconciled"] is True
    assert payload["decision"]["policy_pointer_write_allowed"] is False
    assert payload["decision"]["full_pytest_required"] is False
    assert payload["next_mainline_selection"]["selected_track"] == "core_m3_knowledge_depth"
    assert payload["boundary"] == "mcr2_reconciles_projection_and_internal_context_without_mutating_bazi_facts"
