from __future__ import annotations

from v30.presentation import build_presentation_model
from v30.runtime import create_smoke_runtime
from v30.validation.intelligent_question_interaction_audit import (
    INTELLIGENT_QUESTION_INTERACTION_AUDIT_VERSION,
    run_intelligent_question_interaction_audit,
)


def test_question_order_is_personalized_by_bazi_model_signal() -> None:
    cases = [
        ("wood", "甲", "wood"),
        ("metal", "庚", "metal"),
        ("earth", "戊", "earth"),
        ("water", "壬", "water"),
    ]
    top_topics: dict[str, str] = {}
    top_reasons: dict[str, list[str]] = {}
    for name, day_master, element in cases:
        runtime = create_smoke_runtime(
            f"pytest-iq-personalized-{name}",
            day_master=day_master,
            day_master_element=element,
        )
        view = build_presentation_model(runtime, role_key="user").model_dump(mode="json")
        next_question = view["reading_surface"]["next_question"]
        top_topics[name] = next_question["topic"]
        row = next(
            question for question in runtime.question_plan.recommended_questions
            if question["question_id"] == next_question["question_id"]
        )
        top_reasons[name] = [
            str(reason) for reason in row["reasons"]
            if str(reason).startswith("model_signal_question_focus:")
        ]

    assert len(set(top_topics.values())) >= 3
    assert top_topics["metal"] == "wealth"
    assert top_topics["earth"] == "career"
    assert top_topics["water"] == "timing"
    assert all(top_reasons.values())


def test_iq1_intelligent_question_interaction_audit_ready() -> None:
    result = run_intelligent_question_interaction_audit(reading_id="pytest-iq1")

    assert result["version"] == INTELLIGENT_QUESTION_INTERACTION_AUDIT_VERSION
    assert result["decision"]["intelligent_question_interaction_ready"] is True
    assert result["decision"]["decision_status"] == "iq1_intelligent_question_interaction_ready"
    assert result["decision"]["passed_check_count"] == 8
    assert result["audit_summary"]["personalization"]["distinct_top_topic_count"] >= 3
    assert result["audit_summary"]["training"]["suite_id"] == "v30.synthetic.interaction_loop"
    assert result["audit_summary"]["training"]["passed_count"] == 5
    assert result["next_mainline_selection"]["task_id"] == "IQ-S1"
    assert result["decision"]["chart_fact_mutation_allowed"] is False


def test_iq1_admin_endpoint_is_read_only() -> None:
    from v30.api.app import create_app

    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/mainline/intelligent-question-interaction-audit"
    )
    payload = route.endpoint(reading_id="pytest-iq1-admin")

    assert payload["version"] == INTELLIGENT_QUESTION_INTERACTION_AUDIT_VERSION
    assert payload["decision"]["intelligent_question_interaction_ready"] is True
    assert payload["decision"]["live_llm_required"] is False
    assert payload["decision"]["policy_pointer_write_allowed"] is False
