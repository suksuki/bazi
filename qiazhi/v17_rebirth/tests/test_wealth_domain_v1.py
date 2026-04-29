from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from v17_rebirth.backend.api import v18_1_predictive as api_module
from v17_rebirth.backend.api.app import app
from v17_rebirth.backend.services import core_bazi_feature_layer as feature_layer
from v17_rebirth.backend.services import core_bazi_strength_model as strength_model
from v17_rebirth.backend.services import core_bazi_structure_effect_layer as structure_layer
from v17_rebirth.backend.services import core_bazi_wealth_domain as wealth_domain
from v17_rebirth.backend.services import v18_1_predictive_engine as engine


def _chart(year: str, month: str, day: str, hour: str, *, luck: str | None = None, flow: str | None = None) -> dict:
    chart = {
        "chart_id": f"chart-wealth-{year}-{month}-{day}-{hour}",
        "four_pillars": {"year": year, "month": month, "day": day, "hour": hour},
        "matched_facts": ["complete_birth_fields"],
    }
    if luck:
        chart["luck_pillar"] = luck
    if flow:
        chart["flow_pillar"] = flow
    return {"chart_snapshot": chart}


def _bundles(chart: dict) -> tuple[dict, dict, dict]:
    core = feature_layer.extract_core_bazi_features(chart)
    strength = strength_model.evaluate_core_strength({"core_feature_bundle": core})
    structure = structure_layer.evaluate_core_structure_effect({"core_feature_bundle": core, "core_strength_bundle": strength})
    return core, strength, structure


def _rule_payload(rule_id: str = "wealth.domain.rule") -> dict:
    return {
        "rule_id": rule_id,
        "theory_family": "wealth_domain_v1",
        "condition": {"wealth_domain_evidence": True},
        "effect": {"wealth": 0.72},
        "priority": 0.86,
        "evidence_strength": 0.88,
        "conflict_policy": "merge",
        "version": "v1",
        "owner_plugin": "plugin.wealth-domain",
        "status": "experimental",
        "effect_scope": ["wealth"],
        "allowed_topics": ["wealth"],
    }


def _activate_rule(service: engine.V18PredictiveStore) -> engine.RuleKernel:
    service.register_rule(_rule_payload(), actor_role="manager", actor_user_id=1)
    service.update_rule_status("wealth.domain.rule", "validated", actor_role="manager", actor_user_id=1, version="v1")
    service.activate_rule(rule_id="wealth.domain.rule", target_version="v1", actor_role="manager", actor_user_id=1)
    return service.get_rule("wealth.domain.rule")


def test_wealth_domain_outputs_multiple_evidence_and_guardrails() -> None:
    core, strength, structure = _bundles(_chart("丁巳", "丙午", "乙卯", "丁巳"))
    bundle = wealth_domain.evaluate_wealth_domain(
        {
            "core_feature_bundle": core,
            "core_strength_bundle": strength,
            "structure_effect_bundle": structure,
            "user_intent": "wealth_prediction",
        }
    )

    assert bundle["wealth_bundle_id"].startswith("wealth_domain_bundle_")
    assert len(bundle["wealth_evidence"]) >= 5
    assert {"wealth_strength", "output_generate_wealth", "peer_competition", "constraint_structure", "flow_activation"} <= {
        item["feature_type"] for item in bundle["wealth_evidence"]
    }
    assert bundle["wealth_conclusions"]
    assert all(len(item["evidence_ids"]) >= 3 for item in bundle["wealth_conclusions"])
    assert bundle["guardrails"]["wealth_domain_only"] is True
    assert bundle["guardrails"]["no_general_life_verdict"] is True


def test_wealth_domain_kb_augmented_calibration_only_enters_evidence_and_verifier(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    core, strength, structure = _bundles(_chart("丁巳", "丙午", "乙卯", "丁巳"))
    baseline = wealth_domain.evaluate_wealth_domain(
        {
            "core_feature_bundle": core,
            "core_strength_bundle": strength,
            "structure_effect_bundle": structure,
            "user_intent": "wealth_prediction",
        }
    )
    augmented = wealth_domain.evaluate_wealth_domain(
        {
            "core_feature_bundle": core,
            "core_strength_bundle": strength,
            "structure_effect_bundle": structure,
            "user_intent": "wealth_prediction",
            "knowledge_mode": "kb_augmented",
        }
    )

    assert baseline["knowledge_mode"] == "baseline_only"
    assert baseline["experimental"] is False
    assert augmented["knowledge_mode"] == "kb_augmented"
    assert augmented["experimental"] is True
    assert len(augmented["wealth_evidence"]) > len(baseline["wealth_evidence"])
    kb_rows = [row for row in augmented["wealth_evidence"] if row["source"] == wealth_domain.WEALTH_KB_CALIBRATION_SOURCE]
    assert len(kb_rows) >= 1
    assert all(row["experimental"] is True for row in kb_rows)

    comparison = augmented["knowledge_integration"]["comparison"]
    assert comparison["evidence_count_after"] > comparison["evidence_count_before"]
    assert comparison["kb_source_present"] is True
    assert "wealth_type_before" in comparison
    assert "wealth_type_after" in comparison
    assert any("知识库校准补充" in row["claim"] for row in augmented["wealth_conclusions"])

    monkeypatch.setattr(engine, "RUNTIME_DIR", tmp_path)
    service = engine.V18PredictiveStore()
    rule = _activate_rule(service)
    rule_evidence = service._rule_evidence_from_resolver(
        {"active_rules": [rule.rule_id], "resolved_effect": {}},
        chart_snapshot={
            "topic": "wealth",
            "matched_facts": ["complete_birth_fields"],
            "wealth_domain_bundle": augmented,
            "wealth_features": augmented["wealth_evidence"],
        },
    )
    conclusions = service._conclusions_from_evidence(topic="wealth", rule_evidence=rule_evidence)
    contract = {
        "prediction_id": "pred-wealth-kb-calibration-only",
        "topic": "wealth",
        "chain_id": "wealth_kb_calibration_only",
        "causal_path": ["wealth_domain_baseline", "kb_evidence_calibration", "contract_conclusion"],
        "rule_ids": [rule.rule_id],
        "chain_state": "resolved",
        "confidence": 0.7,
        "period": {"start_at": "2026-01-01", "end_at": "2026-12-31"},
        "evidence_ids": [row["evidence_id"] for row in rule_evidence],
        "verifiable_indicators": {"outcome": ["wealth"]},
        "risk_modes": ["uncertainty"],
        "data_sources": ["wealth_domain_v1", wealth_domain.WEALTH_KB_CALIBRATION_SOURCE],
        "model_version": "v18.1",
        "schema_version": "v18.1",
        "display_policy": {"experimental": True},
        "resolver_snapshot": {"resolver_lifecycle": {"gatekeeper_protocol": engine.RULE_GATEKEEPER_PROTOCOL}},
        "rule_evidence": rule_evidence,
        "conclusions": conclusions,
    }
    verification = service.verify_prediction_contract(contract)

    assert verification["result"] == "pass"
    assert any(row.get("feature", {}).get("source") == wealth_domain.WEALTH_KB_CALIBRATION_SOURCE for row in rule_evidence)
    assert service._ledger == {}


def test_weak_wealth_with_output_signal_is_opportunity_or_volatile() -> None:
    core, strength, structure = _bundles(_chart("丁巳", "丙午", "乙卯", "丁巳"))
    bundle = wealth_domain.evaluate_wealth_domain(
        {"core_feature_bundle": core, "core_strength_bundle": strength, "structure_effect_bundle": structure}
    )

    assert bundle["wealth_profile"]["wealth_type"] in {"opportunity", "volatile"}
    output = next(item for item in bundle["wealth_evidence"] if item["feature_id"] == "output_generate_wealth")
    wealth = next(item for item in bundle["wealth_evidence"] if item["feature_id"] == "wealth_strength")
    assert output["strength"] >= wealth["strength"]


def test_wealth_vault_clash_raises_liquidity_risk_and_lowers_stability() -> None:
    core, strength, structure = _bundles(_chart("甲未", "庚申", "庚丑", "戊辰"))
    bundle = wealth_domain.evaluate_wealth_domain(
        {"core_feature_bundle": core, "core_strength_bundle": strength, "structure_effect_bundle": structure}
    )

    vault = next(item for item in bundle["wealth_evidence"] if item["feature_id"] == "wealth_vault_state")
    assert "opened_by_clash" in " ".join(vault["matched_facts"])
    assert vault["effect"]["liquidity"] > 0.45
    assert vault["risk"] > 0.4
    assert bundle["wealth_profile"]["liquidity_score"] > 0.4


def test_locked_wealth_vault_raises_stability_and_lowers_liquidity() -> None:
    core, strength, structure = _bundles(_chart("甲未", "庚申", "庚午", "戊辰"))
    bundle = wealth_domain.evaluate_wealth_domain(
        {"core_feature_bundle": core, "core_strength_bundle": strength, "structure_effect_bundle": structure}
    )

    vault = next(item for item in bundle["wealth_evidence"] if item["feature_id"] == "wealth_vault_state")
    assert "locked_by_combination" in " ".join(vault["matched_facts"])
    assert vault["stability"] >= 0.5
    assert bundle["wealth_profile"]["liquidity_score"] < 0.7


def test_wealth_domain_rejects_unsupported_intent() -> None:
    core, strength, structure = _bundles(_chart("丁巳", "乙酉", "乙丑", "乙卯"))
    with pytest.raises(engine.PredictiveServiceError) as exc:
        wealth_domain.evaluate_wealth_domain(
            {
                "core_feature_bundle": core,
                "core_strength_bundle": strength,
                "structure_effect_bundle": structure,
                "user_intent": "relationship_prediction",
            }
        )
    assert exc.value.code == "WEALTH_DOMAIN_UNSUPPORTED_INTENT"


def test_wealth_domain_api_round_trip(tmp_path: Path, monkeypatch) -> None:
    store = wealth_domain.WealthDomainStore(tmp_path / "wealth.json")
    monkeypatch.setattr(api_module, "wealth_domain_service", store)
    core, strength, structure = _bundles(_chart("丁巳", "乙酉", "乙丑", "乙卯", luck="壬子", flow="己未"))

    client = TestClient(app)
    resp = client.post(
        "/api/v18.1/domain/wealth/evaluate",
        json={"core_feature_bundle": core, "core_strength_bundle": strength, "structure_effect_bundle": structure},
    )
    assert resp.status_code == 200
    wealth_bundle_id = resp.json()["data"]["wealth_bundle_id"]
    get_resp = client.get(f"/api/v18.1/domain/wealth/{wealth_bundle_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["wealth_bundle_id"] == wealth_bundle_id


def test_wealth_domain_enters_contract_verifier_ledger_chain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(engine, "RUNTIME_DIR", tmp_path)
    service = engine.V18PredictiveStore()
    facade = engine.RuleRuntimeFacade(service)
    rule = _activate_rule(service)

    result = facade.run_prediction_contract_pipeline(
        {
            "prediction_id": "pred-wealth-domain-v1",
            "user_query": "我未来两年财运怎么样？",
            "topic": "wealth",
            "debug": True,
            "plugin_claims": [{"plugin_id": "plugin.wealth-domain", "claim_id": "domain-v1"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "chart_snapshot": _chart("丁巳", "乙酉", "乙丑", "乙卯", luck="壬子", flow="己未")["chart_snapshot"],
        },
        "system",
        0,
    )

    contract = result["contract"]
    evidence = contract["rule_evidence"]
    conclusions = contract["conclusions"]

    assert result["verifier"]["result"] == "pass"
    assert service.get_ledger("pred-wealth-domain-v1")["contract_hash"].startswith("sha256:")
    assert len(evidence) >= 3
    assert "wealth_domain_v1" in contract["data_sources"]
    assert all(row["topic"] == "wealth" for row in conclusions)
    assert all(row["evidence_ids"] for row in conclusions)
    assert all(
        ref in {row["evidence_id"] for row in evidence}
        for conclusion in conclusions
        for ref in conclusion["evidence_ids"]
    )
    assert not any("一生" in row["claim"] or "命好" in row["claim"] or "命差" in row["claim"] for row in conclusions)


def test_unsupported_intent_still_returns_capability_boundary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(engine, "RUNTIME_DIR", tmp_path)
    service = engine.V18PredictiveStore()
    facade = engine.RuleRuntimeFacade(service)
    _activate_rule(service)
    session = facade.create_agent_session({"agent_session_id": "agent-unsupported"}, "user", 1)

    turn = facade.append_agent_turn(
        session["agent_session_id"],
        {"user_message": "我今年感情婚姻怎么样？", "plugin_claims": [{"plugin_id": "plugin.wealth-domain", "claim_id": "domain-v1"}]},
        "user",
        1,
    )

    assert turn["capability_boundary"] is True
    assert turn["safe_output"]["is_prediction"] is False
    assert not turn["prediction_id"]
