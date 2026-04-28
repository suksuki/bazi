from __future__ import annotations

from pathlib import Path

import pytest

from v17_rebirth.backend.services import v18_1_predictive_engine as engine


@pytest.fixture()
def explanation_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(engine, "RUNTIME_DIR", tmp_path)
    service = engine.V18PredictiveStore()
    facade = engine.RuleRuntimeFacade(service)
    return service, facade


def _rule_payload(rule_id: str = "explain.wealth.rule", owner_plugin: str = "plugin.explain"):
    return {
        "rule_id": rule_id,
        "theory_family": "explain_family",
        "condition": {"wealth_visible": True},
        "effect": {"wealth": 0.72},
        "priority": 0.82,
        "evidence_strength": 0.9,
        "conflict_policy": "merge",
        "version": "v1",
        "owner_plugin": owner_plugin,
        "status": "experimental",
        "effect_scope": ["wealth"],
        "allowed_topics": ["wealth"],
    }


def _activate(service: engine.V18PredictiveStore):
    service.register_rule(_rule_payload(), actor_role="manager", actor_user_id=1)
    service.update_rule_status("explain.wealth.rule", "validated", actor_role="manager", actor_user_id=1, version="v1")
    service.activate_rule(rule_id="explain.wealth.rule", target_version="v1", actor_role="manager", actor_user_id=1)
    return service.get_rule("explain.wealth.rule")


def _pipeline(service: engine.V18PredictiveStore, facade: engine.RuleRuntimeFacade, prediction_id: str = "pred-explain"):
    rule = _activate(service)
    return facade.run_prediction_contract_pipeline(
        {
            "prediction_id": prediction_id,
            "user_query": "解释一下财运判断",
            "topic": "wealth",
            "debug": True,
            "plugin_claims": [{"plugin_id": "plugin.explain", "claim_id": "c1"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "chart_snapshot": {"matched_facts": ["wealth_visible"], "four_pillars": {"year": "甲子"}},
        },
        "system",
        0,
    )


def _empty_contract(service: engine.V18PredictiveStore, facade: engine.RuleRuntimeFacade):
    _activate(service)
    resolved = facade.run_resolver(
        {
            "prediction_id": "pred-empty-explain",
            "topic": "wealth",
            "plugin_claims": [{"plugin_id": "plugin.explain", "claim_id": "c1"}],
            "rule_candidates": [{"rule_id": "explain.wealth.rule", "version": "v1", "activation_score": 1.0}],
            "runtime_context": {"time_weight": {"natal": 0.5, "decade": 0.3, "year": 0.2}},
        },
        "system",
        0,
    )
    payload = {
        "prediction_id": "pred-empty-explain",
        "user_query": "信息不足时解释",
        "normalized_intent": {"topic": "wealth", "intent": "prediction"},
        "chart_snapshot": {},
        "topic": "wealth",
        "chain_id": "wealth_contract_v1",
        "causal_path": ["insufficient_evidence"],
        "rule_ids": [],
        "chain_state": "insufficient_evidence",
        "confidence": 0.0,
        "period": {"start_at": "2026-01-01", "end_at": "2026-12-31"},
        "evidence_ids": [],
        "rule_evidence": [],
        "inference_steps": [],
        "conclusions": [],
        "verifiable_indicators": {"outcome": []},
        "risk_modes": ["uncertainty"],
        "data_sources": ["prediction_contract_engine"],
        "model_version": "v18.1",
        "schema_version": "v18.1",
        "display_policy": {"contract_only": True},
        "allowed_output_scope": {"conclusion_ids": [], "evidence_ids": []},
        "resolver_snapshot": resolved["resolver_snapshot"],
        "uncertainty": {"score": 1.0},
    }
    contract = service.build_contract(payload, resolved_rules=resolved)
    service.write_ledger_record({"prediction_id": "pred-empty-explain"}, contract.to_dict())
    return contract.to_dict()


def test_explanation_is_based_only_on_contract(explanation_runtime) -> None:
    service, facade = explanation_runtime
    result = _pipeline(service, facade)

    explanation = service.explain_prediction(
        "pred-explain",
        {"contract_id": "contract_pred-explain", "include_uncertainty": True, "include_evidence_trace": True},
    )

    assert explanation["verifier"]["result"] == "pass"
    assert explanation["safe_output"]["sections"]["conclusion_ids"] == ["conclusion_1"]
    assert explanation["evidence_trace"]
    assert result["contract"]["conclusions"][0]["claim"] in explanation["explanation"]


def test_empty_conclusion_only_outputs_insufficient_evidence(explanation_runtime) -> None:
    service, facade = explanation_runtime
    _empty_contract(service, facade)

    explanation = service.explain_prediction("pred-empty-explain", {"include_uncertainty": True})

    assert explanation["safe_output"]["is_prediction"] is False
    assert "证据不足" in explanation["explanation"]
    assert explanation["safe_output"]["sections"]["conclusion_ids"] == []


def test_contract_external_conclusion_is_blocked(explanation_runtime) -> None:
    service, facade = explanation_runtime
    result = _pipeline(service, facade)
    contract = result["contract"]

    with pytest.raises(engine.PredictiveServiceError) as blocked:
        service.explain_prediction(
            "pred-explain",
            {
                "candidate_output": {
                    "text": "新增一个 Contract 外判断。",
                    "is_prediction": True,
                    "max_confidence": contract["confidence"],
                    "sections": {
                        "conclusion": ["新增一个 Contract 外判断"],
                        "conclusion_ids": ["outside_contract"],
                        "evidence": contract["evidence_ids"],
                        "causal": contract["causal_path"],
                        "risk": contract["risk_modes"],
                        "suggestion": [],
                    },
                    "sources": contract["data_sources"],
                }
            },
        )
    assert blocked.value.code == "EXPLANATION_VERIFIER_FAILED"


def test_confidence_exaggeration_is_blocked(explanation_runtime) -> None:
    service, facade = explanation_runtime
    result = _pipeline(service, facade)
    contract = result["contract"]

    with pytest.raises(engine.PredictiveServiceError) as blocked:
        service.explain_prediction(
            "pred-explain",
            {
                "candidate_output": {
                    "text": "结论成立，但不确定性需保留。",
                    "is_prediction": True,
                    "max_confidence": 1.0,
                    "sections": {
                        "conclusion": [contract["conclusions"][0]["claim"]],
                        "conclusion_ids": ["conclusion_1"],
                        "evidence": contract["evidence_ids"],
                        "causal": contract["causal_path"],
                        "risk": contract["risk_modes"],
                        "suggestion": [],
                    },
                    "sources": contract["data_sources"],
                }
            },
        )
    assert blocked.value.code == "EXPLANATION_VERIFIER_FAILED"
    assert "confidence_exaggeration" in blocked.value.message


def test_sandbox_rule_cannot_be_used_by_explanation(explanation_runtime) -> None:
    service, facade = explanation_runtime
    _pipeline(service, facade)
    sandbox = service.build_sandbox_rule_candidate(
        {"rule_candidate": _rule_payload(rule_id="sandbox.explain.rule", owner_plugin="plugin.sandbox")},
        actor_role="practitioner",
        actor_user_id=3,
    )

    explanation = service.explain_prediction(
        "pred-explain",
        {
            "rule_candidates": [sandbox],
            "include_evidence_trace": True,
        },
    )

    assert "sandbox.explain.rule" not in explanation["explanation"]
    assert all(row["rule_id"] != "sandbox.explain.rule" for row in explanation["evidence_trace"])


def test_include_evidence_trace_returns_contract_evidence(explanation_runtime) -> None:
    service, facade = explanation_runtime
    result = _pipeline(service, facade)

    explanation = service.explain_prediction("pred-explain", {"include_evidence_trace": True})

    assert explanation["evidence_trace"]
    assert explanation["evidence_trace"][0]["evidence_id"] == result["contract"]["rule_evidence"][0]["evidence_id"]
    assert explanation["evidence_trace"][0]["content_hash"] == result["contract"]["rule_evidence"][0]["content_hash"]
