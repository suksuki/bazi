from __future__ import annotations

from v30.validation.intelligent_question_closeout import (
    INTELLIGENT_QUESTION_CLOSEOUT_VERSION,
    run_intelligent_question_closeout,
)


def test_iq5_intelligent_question_closeout_ready() -> None:
    result = run_intelligent_question_closeout(reading_id="pytest-iq5")

    assert result["version"] == INTELLIGENT_QUESTION_CLOSEOUT_VERSION
    assert result["decision"]["intelligent_question_closeout_ready"] is True
    assert result["decision"]["decision_status"] == "iq5_intelligent_question_closeout_ready"
    assert result["decision"]["passed_count"] == 6
    assert result["module_completion"]["question_dialogue_graph"] == 98
    assert result["module_completion"]["question_policy_training"] == 92
    assert result["module_completion"]["status"] == "IQ-S1 steady state"
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "IQ-S1"


def test_iq5_admin_endpoint_is_read_only() -> None:
    from v30.api.app import create_app

    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/mainline/intelligent-question-closeout"
    )
    payload = route.endpoint(reading_id="pytest-iq5-admin")

    assert payload["version"] == INTELLIGENT_QUESTION_CLOSEOUT_VERSION
    assert payload["decision"]["intelligent_question_closeout_ready"] is True
    assert payload["decision"]["policy_pointer_write_allowed"] is False
    assert payload["decision"]["full_pytest_required"] is False
    assert payload["policy_boundary"]["boundary"] == (
        "iq5_question_closeout_keeps_interaction_auxiliary_to_core_bazi_calculation"
    )
