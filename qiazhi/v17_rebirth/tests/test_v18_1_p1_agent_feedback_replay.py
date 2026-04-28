from __future__ import annotations

from pathlib import Path

import pytest

from v17_rebirth.backend.services import v18_1_predictive_engine as engine


@pytest.fixture()
def p1_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(engine, "RUNTIME_DIR", tmp_path)
    service = engine.V18PredictiveStore()
    facade = engine.RuleRuntimeFacade(service)
    return service, facade


def _rule_payload(version: str = "v1", effect: float = 0.6):
    return {
        "rule_id": "agent.wealth.rule",
        "theory_family": "agent_wealth",
        "condition": {"wealth_visible": True},
        "effect": {"wealth": effect},
        "priority": 0.8,
        "evidence_strength": 0.9,
        "conflict_policy": "merge",
        "version": version,
        "owner_plugin": "plugin.agent",
        "status": "experimental",
        "effect_scope": ["wealth"],
        "allowed_topics": ["wealth"],
    }


def _activate_rule(service: engine.V18PredictiveStore):
    service.register_rule(_rule_payload(), actor_role="manager", actor_user_id=1)
    service.update_rule_status("agent.wealth.rule", "validated", actor_role="manager", actor_user_id=1, version="v1")
    service.activate_rule(rule_id="agent.wealth.rule", target_version="v1", actor_role="manager", actor_user_id=1)
    return service.get_rule("agent.wealth.rule")


def _run_pipeline(service: engine.V18PredictiveStore, facade: engine.RuleRuntimeFacade):
    rule = _activate_rule(service)
    return facade.run_prediction_contract_pipeline(
        {
            "prediction_id": "pred-p1-full",
            "user_query": "今年财运如何？",
            "topic": "wealth",
            "debug": True,
            "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "c1"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "chart_snapshot": {"matched_facts": ["wealth_visible"], "four_pillars": {"year": "甲子"}},
        },
        "system",
        0,
    )


def test_ledger_contract_hash_is_server_owned_stable_and_sensitive(p1_runtime) -> None:
    service, facade = p1_runtime
    result = _run_pipeline(service, facade)
    ledger = service.get_ledger("pred-p1-full")

    assert ledger["ledger_id"] == "led_pred-p1-full"
    assert ledger["contract_hash"].startswith("sha256:")
    assert ledger["user_query"] == "今年财运如何？"
    assert ledger["conclusion_refs"]
    assert ledger["evidence_refs"]
    assert ledger["chart_snapshot_hash"].startswith("sha256:")

    contract = dict(result["contract"])
    stable_hash = engine._contract_hash(contract)
    assert stable_hash == ledger["contract_hash"]
    tampered = dict(contract)
    tampered["user_query"] = "tampered"
    assert engine._contract_hash(tampered) != stable_hash
    tampered["contract_hash"] = "external-forgery"
    assert engine._contract_hash(contract) == stable_hash


def test_feedback_binds_prediction_preserves_contract_and_generates_learning_signal(p1_runtime) -> None:
    service, facade = p1_runtime
    _run_pipeline(service, facade)
    before_contract_hash = service.get_ledger("pred-p1-full")["contract_hash"]
    active_rule_hash = service.get_rule("agent.wealth.rule").content_hash
    conclusion_ref = service.get_ledger("pred-p1-full")["conclusion_refs"][0]

    with pytest.raises(engine.PredictiveServiceError) as missing:
        service.append_prediction_feedback("missing-prediction", {"feedback_type": "miss"})
    assert missing.value.code == "LEDGER_NOT_FOUND"

    result = service.append_prediction_feedback(
        "pred-p1-full",
        {
            "conclusion_ref": conclusion_ref,
            "feedback_type": "miss",
            "user_comment": "没有发生",
            "observed_event": {"revenue": "flat"},
        },
    )
    assert result["feedback"]["feedback_type"] == "miss"
    assert result["learning_signal"]["suggested_action"] in {"review_rule", "create_candidate"}
    assert service.get_ledger("pred-p1-full")["contract_hash"] == before_contract_hash
    assert service.get_rule("agent.wealth.rule").content_hash == active_rule_hash
    assert service.query_feedback(prediction_id="pred-p1-full")["total_matched"] == 1
    assert service.query_learning_signals(prediction_id="pred-p1-full")


def test_agent_session_clarifies_missing_info_and_uses_contract_when_complete(p1_runtime) -> None:
    service, facade = p1_runtime
    rule = _activate_rule(service)
    session = facade.create_agent_session({"agent_session_id": "agent-p1"}, "user", 42)
    assert session["agent_session_id"] == "agent-p1"

    clarification = facade.append_agent_turn(
        "agent-p1",
        {"user_message": "今年财运如何？", "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "c1"}]},
        "user",
        42,
    )
    assert clarification["safe_output"]["type"] == "clarification_question"
    assert clarification["safe_output"]["is_prediction"] is False
    assert not clarification["prediction_id"]

    predicted = facade.append_agent_turn(
        "agent-p1",
        {
            "user_message": "今年财运如何？",
            "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "c1"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "chart_snapshot": {"matched_facts": ["wealth_visible"], "four_pillars": {"year": "甲子"}},
        },
        "user",
        42,
    )
    assert predicted["prediction_id"]
    assert predicted["contract_id"]
    assert predicted["minimal_trace"]["conclusion_count"] == 1
    assert "conclusion_ids" in predicted["safe_output"]
    stored = facade.get_agent_session("agent-p1")
    assert len(stored["agent_turns"]) == 2


def test_agent_does_not_use_sandbox_candidate_for_formal_prediction(p1_runtime) -> None:
    service, facade = p1_runtime
    sandbox = service.build_sandbox_rule_candidate(
        {"rule_candidate": _rule_payload(version="sandbox-v1")},
        actor_role="practitioner",
        actor_user_id=3,
    )
    session = facade.create_agent_session({"agent_session_id": "agent-sandbox"}, "user", 1)
    assert session["agent_session_id"] == "agent-sandbox"

    with pytest.raises(engine.PredictiveServiceError) as exc:
        facade.append_agent_turn(
            "agent-sandbox",
            {
                "user_message": "今年财运如何？",
                "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "c1"}],
                "rule_candidates": [
                    {
                        "rule_id": sandbox["rule_payload"]["rule_id"],
                        "version": sandbox["rule_payload"]["version"],
                        "activation_score": 1.0,
                        "rule_payload": sandbox["rule_payload"],
                    }
                ],
                "chart_snapshot": {"matched_facts": ["wealth_visible"], "four_pillars": {"year": "甲子"}},
                "allow_sandbox": True,
            },
            "user",
            1,
        )
    assert exc.value.code == "RULE_SCOPE_VIOLATION"


def test_replay_returns_contract_feedback_signals_and_rule_drift(p1_runtime) -> None:
    service, facade = p1_runtime
    _run_pipeline(service, facade)
    conclusion_ref = service.get_ledger("pred-p1-full")["conclusion_refs"][0]
    service.append_prediction_feedback("pred-p1-full", {"conclusion_ref": conclusion_ref, "feedback_type": "hit"})

    replay = service.replay_prediction("pred-p1-full")
    assert replay["ledger"]["prediction_id"] == "pred-p1-full"
    assert replay["contract"]["prediction_id"] == "pred-p1-full"
    assert replay["evidence"]
    assert replay["feedback"]
    assert replay["learning_signals"]
    assert replay["rule_drift"] is False

    rule = service.get_rule("agent.wealth.rule", version="v1")
    rule.content_hash = "sha256:changed"
    service._rule_kernels[service._normalize_rule_key(rule.rule_id, rule.version)] = rule
    drifted = service.replay_prediction("pred-p1-full")
    assert drifted["rule_drift"] is True
