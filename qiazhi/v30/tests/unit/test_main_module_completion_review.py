from __future__ import annotations

from v30.validation.main_module_completion_review import (
    MAIN_MODULE_COMPLETION_REVIEW_VERSION,
    run_main_module_completion_review,
)


def test_mcr1_main_module_completion_review_selects_next_module() -> None:
    result = run_main_module_completion_review(reading_id="pytest-mcr1")

    assert result["version"] == MAIN_MODULE_COMPLETION_REVIEW_VERSION
    assert result["decision"]["main_module_completion_review_ready"] is True
    assert result["decision"]["decision_status"] == "mcr1_main_module_review_ready"
    assert result["decision"]["passed_count"] == 5
    assert result["decision"]["full_pytest_required"] is False
    assert result["decision"]["synthetic_all_required"] is False
    assert result["decision"]["full_518k_required"] is False
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "MCR2"
    assert result["next_mainline_selection"]["full_pytest_run_now"] is False

    matrix = {row["module_id"]: row for row in result["module_completion_matrix"]}
    assert matrix["M1/M2"]["completion"] == 100
    assert matrix["M3"]["completion"] == 100
    assert matrix["M8"]["completion"] == 100
    assert matrix["IQ"]["completion"] == 98
    assert matrix["SURFACE"]["status"] == "reconcile"
    assert matrix["CTX"]["status"] == "reconcile"


def test_mcr1_admin_endpoint_is_read_only() -> None:
    from v30.api.app import create_app

    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/mainline/main-module-completion-review"
    )
    payload = route.endpoint(reading_id="pytest-mcr1-admin")

    assert payload["version"] == MAIN_MODULE_COMPLETION_REVIEW_VERSION
    assert payload["decision"]["main_module_completion_review_ready"] is True
    assert payload["decision"]["policy_pointer_write_allowed"] is False
    assert payload["decision"]["full_pytest_required"] is False
    assert payload["next_mainline_selection"]["selected_track"] == "main_module_completion_reconciliation"
    assert payload["boundary"] == "main_module_completion_review_selects_next_core_module_work_without_mutating_bazi_facts"
