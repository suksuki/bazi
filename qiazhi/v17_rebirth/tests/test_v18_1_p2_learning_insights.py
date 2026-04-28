from __future__ import annotations

from pathlib import Path

from v17_rebirth.backend.services import v18_1_predictive_engine as engine


def _rule_payload():
    return {
        "rule_id": "learning.wealth.rule",
        "theory_family": "learning_wealth",
        "condition": {"wealth_visible": True, "segment": "cashflow"},
        "effect": {"wealth": 0.8},
        "priority": 0.86,
        "evidence_strength": 0.92,
        "conflict_policy": "merge",
        "version": "v1",
        "owner_plugin": "plugin.learning",
        "status": "experimental",
        "effect_scope": ["wealth"],
        "allowed_topics": ["wealth"],
    }


def _runtime(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(engine, "RUNTIME_DIR", tmp_path)
    service = engine.V18PredictiveStore()
    facade = engine.RuleRuntimeFacade(service)
    service.register_rule(_rule_payload(), actor_role="manager", actor_user_id=1)
    service.update_rule_status("learning.wealth.rule", "validated", actor_role="manager", actor_user_id=1, version="v1")
    service.activate_rule(rule_id="learning.wealth.rule", target_version="v1", actor_role="manager", actor_user_id=1)
    return service, facade, service.get_rule("learning.wealth.rule")


def _prediction(service: engine.V18PredictiveStore, facade: engine.RuleRuntimeFacade, rule, prediction_id: str):
    return facade.run_prediction_contract_pipeline(
        {
            "prediction_id": prediction_id,
            "user_query": "这类现金流会不会改善？",
            "topic": "wealth",
            "debug": True,
            "plugin_claims": [{"plugin_id": "plugin.learning", "claim_id": "c1"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "chart_snapshot": {
                "matched_facts": ["wealth_visible", "cashflow_segment"],
                "four_pillars": {"year": "甲子"},
            },
        },
        "system",
        0,
    )


def _add_feedback(service: engine.V18PredictiveStore, prediction_id: str, feedback_type: str):
    conclusion_ref = service.get_ledger(prediction_id)["conclusion_refs"][0]
    return service.append_prediction_feedback(
        prediction_id,
        {
            "conclusion_ref": conclusion_ref,
            "feedback_type": feedback_type,
            "user_comment": f"{feedback_type} observed",
            "observed_event": {"cashflow": feedback_type},
        },
    )


def test_multiple_miss_feedback_aggregates_into_insight(tmp_path: Path, monkeypatch) -> None:
    service, facade, rule = _runtime(tmp_path, monkeypatch)
    active_hash = rule.content_hash
    for idx in range(3):
        prediction_id = f"pred-learning-miss-{idx}"
        _prediction(service, facade, rule, prediction_id)
        _add_feedback(service, prediction_id, "miss")

    result = service.query_learning_insights()
    insight = result["items"][0]

    assert insight["signal_count"] == 3
    assert insight["miss_count"] == 3
    assert insight["related_rule_ids"] == ["learning.wealth.rule"]
    assert insight["source_signal_ids"]
    assert insight["evidence_refs"]
    assert service.get_rule("learning.wealth.rule").content_hash == active_hash


def test_insight_detects_dominant_failure_pattern_and_action(tmp_path: Path, monkeypatch) -> None:
    service, facade, rule = _runtime(tmp_path, monkeypatch)
    for idx in range(2):
        prediction_id = f"pred-learning-danger-{idx}"
        _prediction(service, facade, rule, prediction_id)
        _add_feedback(service, prediction_id, "miss")

    insight = service.query_learning_insights()["items"][0]

    assert insight["dominant_failure_pattern"] == "high_confidence_miss"
    assert insight["confidence_trend"] == "overconfident"
    assert insight["suggested_action"] == "adjust_confidence"


def test_partial_feedback_classifies_refine_condition(tmp_path: Path, monkeypatch) -> None:
    service, facade, rule = _runtime(tmp_path, monkeypatch)
    for idx in range(2):
        prediction_id = f"pred-learning-partial-{idx}"
        _prediction(service, facade, rule, prediction_id)
        _add_feedback(service, prediction_id, "partial")

    insight = service.query_learning_insights()["items"][0]

    assert insight["partial_count"] == 2
    assert insight["dominant_failure_pattern"].startswith("partial_condition:")
    assert insight["suggested_action"] == "refine_condition"


def test_suggestion_references_insight_and_does_not_create_active_rule(tmp_path: Path, monkeypatch) -> None:
    service, facade, rule = _runtime(tmp_path, monkeypatch)
    active_version_before = service.get_rule("learning.wealth.rule").version
    for idx in range(2):
        prediction_id = f"pred-learning-suggestion-{idx}"
        _prediction(service, facade, rule, prediction_id)
        _add_feedback(service, prediction_id, "miss")

    insights = service.query_learning_insights()["items"]
    suggestions = service.query_candidate_rule_suggestions()["items"]

    assert suggestions
    assert suggestions[0]["based_on_insight_id"] == insights[0]["insight_id"]
    assert suggestions[0]["requires_human_review"] is True
    assert suggestions[0]["suggested_rule_diff"]["action"] == insights[0]["suggested_action"]
    assert service.get_rule("learning.wealth.rule").version == active_version_before
    assert service.get_rule("learning.wealth.rule").status == "active"


def test_suggestion_can_create_draft_knowledge_card_only(tmp_path: Path, monkeypatch) -> None:
    service, facade, rule = _runtime(tmp_path, monkeypatch)
    for idx in range(2):
        prediction_id = f"pred-learning-card-{idx}"
        _prediction(service, facade, rule, prediction_id)
        _add_feedback(service, prediction_id, "miss")

    suggestion = service.query_candidate_rule_suggestions()["items"][0]
    card = service.create_knowledge_card_from_suggestion(
        suggestion["suggestion_id"],
        {"card_id": "kc.learning.suggestion", "knowledge_domain": "wealth"},
        actor_role="manager",
        actor_user_id=7,
    )

    stored = service.get_knowledge_card(card["card_id"], allow_inactive=True).to_dict()
    assert stored["status"] == "draft"
    assert suggestion["suggestion_id"] in stored["source_refs"]
    assert not service.query_rule_candidates(knowledge_card_id="kc.learning.suggestion")["items"]
