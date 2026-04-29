from __future__ import annotations

from pathlib import Path

import pytest

from v17_rebirth.backend.services import v18_1_predictive_engine as engine


@pytest.fixture()
def contract_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(engine, "RUNTIME_DIR", tmp_path)
    service = engine.V18PredictiveStore()
    facade = engine.RuleRuntimeFacade(service)
    return service, facade


def _rule_payload():
    return {
        "rule_id": "contract.wealth.output",
        "theory_family": "wealth_contract",
        "condition": {"output_visible": True},
        "effect": {"wealth": 0.6},
        "priority": 0.8,
        "evidence_strength": 0.9,
        "conflict_policy": "merge",
        "version": "v1",
        "owner_plugin": "plugin.contract",
        "status": "experimental",
        "effect_scope": ["wealth"],
        "allowed_topics": ["wealth"],
    }


def _activate_contract_rule(service: engine.V18PredictiveStore):
    service.register_rule(_rule_payload(), actor_role="manager", actor_user_id=1)
    service.update_rule_status("contract.wealth.output", "validated", actor_role="manager", actor_user_id=1, version="v1")
    service.activate_rule(rule_id="contract.wealth.output", target_version="v1", actor_role="manager", actor_user_id=1)
    return service.get_rule("contract.wealth.output")


def _resolved_contract_payload(service: engine.V18PredictiveStore, facade: engine.RuleRuntimeFacade):
    rule = _activate_contract_rule(service)
    resolved = facade.run_resolver(
        {
            "prediction_id": "pred-contract",
            "topic": "wealth",
            "plugin_claims": [{"plugin_id": "plugin.contract", "claim_id": "c1"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "runtime_context": {"time_weight": {"natal": 0.5, "decade": 0.3, "year": 0.2}},
        },
        "system",
        0,
    )
    evidence_id = f"ev_{rule.rule_id}_{rule.version}_{rule.content_hash[:12]}"
    contract = {
        "prediction_id": "pred-contract",
        "user_query": "今年财运如何？",
        "normalized_intent": {"topic": "wealth", "intent": "prediction"},
        "chart_snapshot": {"matched_facts": ["output_visible"]},
        "topic": "wealth",
        "chain_id": "wealth_contract_v1",
        "causal_path": ["rule_match", "effect_resolution"],
        "rule_ids": [rule.rule_id],
        "chain_state": "resolved",
        "confidence": 0.72,
        "period": {"start_at": "2026-01-01", "end_at": "2026-12-31"},
        "evidence_ids": [evidence_id],
        "rule_evidence": [
            {
                "evidence_id": evidence_id,
                "rule_id": rule.rule_id,
                "version": rule.version,
                "content_hash": rule.content_hash,
                "matched_facts": ["output_visible"],
                "effect": rule.effect,
                "confidence_delta": 0.72,
            }
        ],
        "inference_steps": [{"step": "rule_match", "output": [evidence_id]}],
        "conclusions": [
            {
                "conclusion_id": "conclusion_1",
                "topic": "wealth",
                "claim": "wealth signal is supported",
                "confidence": 0.72,
                "evidence_ids": [evidence_id],
                "generated_by": "engine",
            }
        ],
        "verifiable_indicators": {"outcome": ["wealth"]},
        "risk_modes": ["uncertainty"],
        "data_sources": ["prediction_contract_engine"],
        "model_version": "v18.1",
        "schema_version": "v18.1",
        "display_policy": {"contract_only": True},
        "allowed_output_scope": {"conclusion_ids": ["conclusion_1"], "evidence_ids": [evidence_id]},
        "resolver_snapshot": resolved["resolver_snapshot"],
        "uncertainty": {"score": 0.3},
    }
    return resolved, contract


def test_contract_rejects_conclusion_without_evidence(contract_runtime) -> None:
    service, facade = contract_runtime
    resolved, contract = _resolved_contract_payload(service, facade)
    contract["rule_evidence"] = []
    contract["evidence_ids"] = []

    with pytest.raises(engine.PredictiveServiceError) as exc:
        service.build_contract(contract, resolved_rules=resolved)
    assert exc.value.code == "CONTRACT_VERIFIER_FAILED"


def test_contract_rejects_missing_or_mismatched_rule_identity(contract_runtime) -> None:
    service, facade = contract_runtime
    resolved, contract = _resolved_contract_payload(service, facade)
    contract["rule_evidence"][0]["content_hash"] = "sha256:wrong"

    with pytest.raises(engine.PredictiveServiceError) as exc:
        service.build_contract(contract, resolved_rules=resolved)
    assert exc.value.code == "CONTRACT_VERIFIER_FAILED"
    assert "RULE_EVIDENCE_HASH_MISMATCH" in exc.value.message


def test_llm_output_cannot_add_contract_external_conclusion(contract_runtime) -> None:
    service, facade = contract_runtime
    resolved, contract_payload = _resolved_contract_payload(service, facade)
    contract = service.build_contract(contract_payload, resolved_rules=resolved)
    record = service.write_ledger_record({"prediction_id": "pred-contract"}, contract.to_dict())
    assert record.prediction_hash.startswith("sha256:")

    verifier = service.run_verifier(
        {
            "prediction_id": "pred-contract",
            "contract": contract.to_dict(),
            "llm_output": {
                "text": "wealth signal is supported; another new fate claim",
                "sections": {
                    "conclusion": ["wealth signal is supported", "another new fate claim"],
                    "conclusion_ids": ["conclusion_1", "outside_contract"],
                    "evidence": contract.evidence_ids,
                    "causal": contract.causal_path,
                    "risk": contract.risk_modes,
                    "suggestion": [],
                },
                "sources": contract.data_sources,
            },
        }
    )
    assert verifier["result"] == "fail"
    assert "contract_conclusion_scope" in verifier["degraded_fields"]


def test_empty_conclusion_only_allows_insufficient_evidence_output(contract_runtime) -> None:
    service, facade = contract_runtime
    resolved, contract_payload = _resolved_contract_payload(service, facade)
    contract_payload["rule_evidence"] = []
    contract_payload["evidence_ids"] = []
    contract_payload["conclusions"] = []
    contract_payload["chain_state"] = "insufficient_evidence"
    contract = service.build_contract(contract_payload, resolved_rules=resolved)
    service.write_ledger_record({"prediction_id": "pred-empty"}, {**contract.to_dict(), "prediction_id": "pred-empty"})

    verifier = service.run_verifier(
        {
            "prediction_id": "pred-empty",
            "contract": {**contract.to_dict(), "prediction_id": "pred-empty"},
            "llm_output": {
                "text": "证据不足，不足以判断。",
                "sections": {"conclusion": [], "evidence": [], "causal": contract.causal_path, "risk": contract.risk_modes, "suggestion": []},
                "sources": contract.data_sources,
            },
        }
    )
    assert verifier["result"] == "pass"


def test_prediction_contract_pipeline_runs_complete_sample(contract_runtime) -> None:
    service, facade = contract_runtime
    rule = _activate_contract_rule(service)
    result = facade.run_prediction_contract_pipeline(
        {
            "prediction_id": "pred-pipeline",
            "user_query": "今年财运如何？",
            "topic": "wealth",
            "debug": True,
            "plugin_claims": [{"plugin_id": "plugin.contract", "claim_id": "c1"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "chart_snapshot": {"matched_facts": ["output_visible"]},
        },
        "system",
        0,
    )

    assert result["prediction_id"] == "pred-pipeline"
    assert result["contract_id"] == "contract_pred-pipeline"
    assert result["verifier"]["result"] == "pass"
    assert result["minimal_trace"]["evidence_count"] >= 2
    assert result["contract"]["conclusions"][0]["generated_by"] == "engine"
