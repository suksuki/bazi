from __future__ import annotations

from v30.validation.intelligent_question_chain_readiness import (
    INTELLIGENT_QUESTION_CHAIN_READINESS_VERSION,
    run_intelligent_question_chain_readiness,
)


def test_iq4_intelligent_question_chain_readiness_ready() -> None:
    result = run_intelligent_question_chain_readiness(reading_id="pytest-iq4")

    assert result["version"] == INTELLIGENT_QUESTION_CHAIN_READINESS_VERSION
    assert result["decision"]["intelligent_question_chain_ready"] is True
    assert result["decision"]["decision_status"] == "iq4_intelligent_question_chain_ready"
    assert result["decision"]["passed_count"] == 6
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["policy_boundary"]["llm_fact_generation_allowed"] is False
    assert result["chain_summary"]["chain"]["outcome_count"] >= 2
    assert result["chain_summary"]["core_boundary"]["core_fingerprint_unchanged"] is True
    assert result["chain_summary"]["llm"]["answer_task_type"] == "domain_followup"
    assert result["next_mainline_selection"]["task_id"] == "IQ-S1"


def test_iq4_admin_endpoint_is_read_only() -> None:
    from v30.api.app import create_app

    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/mainline/intelligent-question-chain-readiness"
    )
    payload = route.endpoint(reading_id="pytest-iq4-admin")

    assert payload["version"] == INTELLIGENT_QUESTION_CHAIN_READINESS_VERSION
    assert payload["decision"]["intelligent_question_chain_ready"] is True
    assert payload["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert payload["policy_boundary"]["boundary"] == "iq4_question_chain_trains_interaction_strategy_not_chart_facts"
