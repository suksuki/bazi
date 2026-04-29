from __future__ import annotations

from pathlib import Path

import pytest

from v17_rebirth.backend.services import v18_1_predictive_engine as engine


@pytest.fixture()
def kb_service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(engine, "RUNTIME_DIR", tmp_path)
    return engine.V18PredictiveStore()


def _unit_payload(knowledge_id: str = "wealth.test_unit") -> dict:
    return {
        "knowledge_id": knowledge_id,
        "domain": "wealth",
        "category": "output_generate_wealth",
        "title": "测试食伤生财",
        "statement": "食伤与财星形成承接时，可作为输出变现的结构化知识。",
        "classical_source": "owner-reviewed seed",
        "modern_interpretation": "输出能力通过产品、服务或项目形成收入机会。",
        "conditions": {"output_star": "present", "wealth_star": "present"},
        "feature_mapping": {
            "feature_type": "output_generate_wealth",
            "input_requirements": ["ten_gods_runtime", "body_strength"],
            "detection_logic": {"requires": ["食神", "伤官", "财星"]},
            "output_fields": ["strength", "stability", "risk", "uncertainty"],
            "effect_direction": "earning_opportunity",
            "confidence_weight": 0.71,
            "uncertainty_weight": 0.29,
        },
        "effects": {"wealth": 0.66, "earning_opportunity": 0.7},
        "risk_factors": ["食伤太过泄身"],
        "uncertainty_factors": ["需判断日主强弱"],
        "conflicts": ["印星过强"],
        "confidence_prior": 0.71,
        "status": "draft",
    }


def test_wealth_kb_seed_loads_units_and_feature_definitions(kb_service: engine.V18PredictiveStore) -> None:
    units = kb_service.list_bazi_knowledge_units(domain="wealth", limit=100)
    by_id = {item["knowledge_id"]: item for item in units["items"]}

    assert units["total_matched"] >= 20
    assert {
        "wealth.wealth_strength",
        "wealth.output_generate_wealth",
        "wealth.wealth_vault",
        "wealth.peer_competition",
        "wealth.constraint_structure",
    }.issubset(by_id)
    assert all(by_id[knowledge_id]["status"] == "reviewed" for knowledge_id in {
        "wealth.wealth_strength",
        "wealth.output_generate_wealth",
        "wealth.wealth_vault",
        "wealth.peer_competition",
        "wealth.constraint_structure",
    })
    assert {item["category"] for item in units["items"]} >= {
        "wealth_star",
        "wealth_vault",
        "output_generate_wealth",
        "constraint_structure",
        "combination_clash_stability",
        "luck_flow_activation",
    }
    assert {"wealth_strength", "wealth_vault_activation", "output_generate_wealth", "wealth_constraint", "wealth_flow_activation", "wealth_stability", "wealth_risk"}.issubset(
        set(kb_service._bazi_feature_definitions)
    )
    assert {"wealth_vault_state", "peer_competition"}.issubset(set(kb_service._bazi_feature_definitions))


def test_core_wealth_reviewed_units_convert_to_sandbox_candidates(kb_service: engine.V18PredictiveStore) -> None:
    for knowledge_id in [
        "wealth.wealth_strength",
        "wealth.output_generate_wealth",
        "wealth.wealth_vault",
        "wealth.peer_competition",
        "wealth.constraint_structure",
    ]:
        unit = kb_service.get_bazi_knowledge_unit(knowledge_id)
        candidate = kb_service.bazi_knowledge_unit_to_rule_candidate(knowledge_id, {}, actor_role="admin", actor_user_id=1)

        assert unit["status"] == "reviewed"
        assert unit["created_by"] == "owner_codex_reviewed_core_wealth_v1"
        assert unit["conditions"]["knowledge_version"] == "core_wealth_v1"
        assert candidate["candidate_state"] == "sandbox"
        assert candidate["sandbox"] is True
        assert candidate["source_knowledge_id"] == knowledge_id
        assert candidate["rule_payload"]["status"] == "experimental"
        assert candidate["rule_payload"]["condition"]["source_knowledge_id"] == knowledge_id
        assert "ENERGY_CLAMP" in candidate["compiled_rule_logic"]["decorators"]
    assert kb_service.list_rules(status="active") == []


def test_create_review_and_reviewed_unit_is_immutable(kb_service: engine.V18PredictiveStore) -> None:
    created = kb_service.register_bazi_knowledge_unit(_unit_payload(), actor_role="admin", actor_user_id=1)
    assert created["status"] == "draft"

    reviewed = kb_service.review_bazi_knowledge_unit("wealth.test_unit", {"reviewed_by": "owner"}, actor_role="admin", actor_user_id=1)
    assert reviewed["status"] == "reviewed"
    assert reviewed["reviewed_by"] == "owner"

    changed = _unit_payload()
    changed["statement"] = "试图直接修改 reviewed 原文。"
    with pytest.raises(engine.PredictiveServiceError) as exc:
        kb_service.register_bazi_knowledge_unit(changed, actor_role="admin", actor_user_id=1)
    assert exc.value.code == "BAZI_KNOWLEDGE_IMMUTABLE"


def test_knowledge_unit_converts_only_to_sandbox_candidate(kb_service: engine.V18PredictiveStore) -> None:
    kb_service.register_bazi_knowledge_unit(_unit_payload("wealth.test_candidate"), actor_role="admin", actor_user_id=1)
    kb_service.review_bazi_knowledge_unit("wealth.test_candidate", {"reviewed_by": "owner"}, actor_role="admin", actor_user_id=1)

    candidate = kb_service.bazi_knowledge_unit_to_rule_candidate("wealth.test_candidate", {}, actor_role="admin", actor_user_id=1)

    assert candidate["candidate_state"] == "sandbox"
    assert candidate["sandbox"] is True
    assert candidate["source_knowledge_id"] == "wealth.test_candidate"
    assert candidate["conversion_policy"]["requires_rule_test"] is True
    assert candidate["conversion_policy"]["requires_knowledge_pr"] is True
    assert candidate["rule_payload"]["status"] == "experimental"
    assert candidate["rule_payload"]["condition"]["source_knowledge_id"] == "wealth.test_candidate"
    assert kb_service.list_rules(status="active") == []


def test_bootstrap_wealth_core_rule_test_candidate_v1(kb_service: engine.V18PredictiveStore) -> None:
    summary = kb_service.bootstrap_wealth_core_rule_test_candidates_v1(actor_role="manager", actor_user_id=7)
    expected_count = len(engine.WEALTH_CORE_REVIEWED_KNOWLEDGE_UNIT_IDS)

    assert summary["candidate_count"] == expected_count
    assert summary["suite_count"] == expected_count
    assert summary["case_count"] == expected_count

    candidate_index = {
        item["source_knowledge_id"]: item for item in summary["candidates"]
    }
    assert set(candidate_index.keys()) == set(engine.WEALTH_CORE_REVIEWED_KNOWLEDGE_UNIT_IDS)
    for item in summary["candidates"]:
        assert item["candidate_state"] == "sandbox"
        assert item["rule_payload"]["status"] == "experimental"
        assert item["conversion_policy"]["requires_rule_test"] is True
        with pytest.raises(engine.PredictiveServiceError):
            kb_service.get_rule(item["rule_payload"]["rule_id"], version=item["rule_payload"]["version"], allow_inactive=True)

    for relation in summary["suite_candidates"]:
        suite = kb_service.get_rule_test_suite(relation["suite_id"], version="v1", allow_inactive=True)
        assert suite.suite_id == relation["suite_id"]
        assert suite.status == "draft"
        assert suite.rule_id == candidate_index[relation["knowledge_id"]]["rule_payload"]["rule_id"]
        assert suite.rule_version == candidate_index[relation["knowledge_id"]]["rule_payload"]["version"]
        assert suite.test_cases
        assert suite.test_cases[0]["case_id"].startswith("wealth_core_v1_")

    facade = engine.RuleRuntimeFacade(kb_service)
    first = summary["candidates"][0]
    first_case = summary["cases"][0]["case_id"]
    run = facade.run_rule_test_v02(
        {
            "rule_candidate_id": first["candidate_id"],
            "test_case_ids": [first_case],
        },
        "manager",
        7,
    )
    assert run["overall_status"] == "pass"
    assert run["pass_count"] == 1


def test_rule_generator_injects_energy_clamp_and_blocks_inflation(kb_service: engine.V18PredictiveStore) -> None:
    kb_service.register_bazi_knowledge_unit(_unit_payload("wealth.test_energy_clamp"), actor_role="admin", actor_user_id=1)
    unit = kb_service.get_bazi_knowledge_unit("wealth.test_energy_clamp")
    unit["feature_mapping"]["confidence_weight"] = 10**43
    unit["effects"]["wealth"] = 10**43

    compiled = kb_service.compile_bazi_knowledge_rule_logic(unit)
    candidate = kb_service.bazi_knowledge_unit_to_rule_candidate("wealth.test_energy_clamp", {}, actor_role="admin", actor_user_id=1)
    inflated = kb_service.apply_energy_clamp(10**43)

    assert "ENERGY_CLAMP" in compiled["decorators"]
    assert "ENERGY_CLAMP" in candidate["compiled_rule_logic"]["decorators"]
    assert "ENERGY_CLAMP" in candidate["rule_payload"]["condition"]["compiler_guardrails"]
    assert candidate["rule_payload"]["condition"]["compiled_feature_logic"]["energy_clamp"]["overflow_policy"] == "clamp_and_flag"
    assert inflated["clamped"] is True
    assert inflated["value"] <= 1.0


def test_dry_run_audit_persists_conflict_report_for_wealth_019(kb_service: engine.V18PredictiveStore) -> None:
    report = kb_service.dry_run_bazi_knowledge_audit(
        "wealth.019_combination_changes_stability",
        {"local_only": True},
        actor_role="admin",
        actor_user_id=1,
    )

    assert report["audit_status"] == "local_fallback"
    assert report["compiled_rule_logic"]["source_knowledge_id"] == "wealth.019_combination_changes_stability"
    assert any(row["conflict_type"] == "stability_polarity_ambiguous" for row in report["conflicts"])
    assert any(row["knowledge_id"] == "wealth.019_combination_changes_stability" for row in kb_service._bazi_knowledge_conflicts.values())


def test_deprecated_knowledge_unit_cannot_convert_to_candidate(kb_service: engine.V18PredictiveStore) -> None:
    kb_service.register_bazi_knowledge_unit(_unit_payload("wealth.test_deprecated"), actor_role="admin", actor_user_id=1)
    deprecated = kb_service.deprecate_bazi_knowledge_unit("wealth.test_deprecated", {"reason": "test"}, actor_role="admin", actor_user_id=1)

    assert deprecated["status"] == "deprecated"
    with pytest.raises(engine.PredictiveServiceError) as exc:
        kb_service.bazi_knowledge_unit_to_rule_candidate("wealth.test_deprecated", {}, actor_role="admin", actor_user_id=1)
    assert exc.value.code == "BAZI_KNOWLEDGE_DEPRECATED"
