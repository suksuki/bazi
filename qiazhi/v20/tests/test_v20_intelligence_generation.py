from __future__ import annotations

from fastapi.testclient import TestClient

from v20.intelligence.generation import build_intelligence_generation_manifest
from v20.intelligence.knowledge_semantic_model import build_knowledge_semantic_model, validate_knowledge_semantic_model
from v20.server import app
from v20.validation.intelligence_generation import validate_intelligence_generation


def test_v20_intelligence_generation_manifest_names_generation_boundaries() -> None:
    manifest = build_intelligence_generation_manifest()

    assert manifest["status"] == "ready"
    assert manifest["knowledge_generation"]["shadow_learning_allowed"] is True
    assert manifest["rule_generation"]["shadow_training_allowed"] is True
    assert manifest["rule_generation"]["user_visible_runtime_allowed"] is False
    assert manifest["rule_generation"]["synthetic_role"] == "primary_rule_collision_validation_and_training_gate"
    assert manifest["rule_generation"]["synthetic_rule_training_status"] == "ready"
    assert manifest["portrait_generation"]["source_policy"] == "feature_first_knowledge_supported"
    assert manifest["feature_discovery_generation"]["runtime_role"] == "central_intelligence_router_for_features_questions_portraits_and_answers"
    assert manifest["knowledge_semantic_modeling"]["runtime_role"] == "semantic_index_for_feature_discovery_portrait_and_interaction"
    assert "knowledge_extraction_draft" in manifest["llm_generation"]["allowed_roles"]
    assert "evidence_bounded_practitioner_answer" in manifest["llm_generation"]["allowed_roles"]
    assert "core_rule_truth_override" in manifest["llm_generation"]["forbidden_roles"]
    assert "rule_shadow_training_gate" in manifest["validation_policy"]["synthetic_required_for"]
    assert "user_visible_rule_promotion" in manifest["validation_policy"]["synthetic_required_for"]
    assert "full_corpus_coverage_priors" in manifest["validation_policy"]["synthetic_not_required_for"]
    assert manifest["runtime_mutation"] is False


def test_v20_intelligence_generation_validation_allows_shadow_but_not_promotion() -> None:
    report = validate_intelligence_generation()

    assert report["ok"] is True
    assert report["status"] == "pass"
    assert report["shadow_training"]["allowed"] is True
    assert report["rule_synthetic"]["ok"] is True
    assert report["shadow_training"]["rule_synthetic_training_status"] == "ready"
    assert report["promotion"]["user_visible_rule_promotion_ready"] is False
    assert report["runtime_mutation"] is False


def test_v20_knowledge_semantic_model_indexes_rules_portraits_and_interaction() -> None:
    model = build_knowledge_semantic_model(user_text="我想看事业和财运")
    validation = validate_knowledge_semantic_model(model)
    domains = {row["domain"]: row for row in model["domain_models"]}

    assert model["status"] == "ready"
    assert model["source_authority"] == "reviewed_bazi_knowledge_base"
    assert {"career", "wealth"} <= set(model["interaction_index"]["matched_domains"])
    assert domains["wealth"]["portrait_label_candidates"]
    assert domains["wealth"]["rule_atom_count"] >= 1
    assert domains["career"]["semantic_weight"] > 0
    assert validation["status"] == "pass"
    assert model["runtime_mutation"] is False


def test_v20_intelligence_generation_endpoints_are_read_only() -> None:
    client = TestClient(app)
    manifest = client.get("/api/v20/intelligence/generation-manifest").json()
    semantic = client.get("/api/v20/intelligence/knowledge-semantic-model").json()
    validation = client.get("/api/v20/validation/intelligence-generation").json()
    semantic_validation = client.get("/api/v20/validation/knowledge-semantic-model").json()

    assert manifest["runtime_mutation"] is False
    assert semantic["runtime_mutation"] is False
    assert semantic["status"] == "ready"
    assert validation["runtime_mutation"] is False
    assert validation["status"] == "pass"
    assert semantic_validation["status"] == "pass"
