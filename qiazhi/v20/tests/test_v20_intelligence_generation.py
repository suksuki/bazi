from __future__ import annotations

from fastapi.testclient import TestClient

from v20.intelligence.generation import build_intelligence_generation_manifest
from v20.intelligence.knowledge_semantic_model import build_knowledge_semantic_model, validate_knowledge_semantic_model
from v20.server import app
from v20.validation.intelligence_generation import validate_intelligence_generation


def test_v20_intelligence_generation_manifest_names_generation_boundaries() -> None:
    manifest = build_intelligence_generation_manifest()

    assert manifest["status"] == "ready"
    assert manifest["knowledge_generation"]["active_learning_allowed"] is True
    assert manifest["rule_generation"]["active_training_allowed"] is True
    assert manifest["rule_generation"]["user_visible_runtime_allowed"] is True
    assert manifest["rule_generation"]["synthetic_role"] == "primary_rule_collision_validation_and_iteration_signal"
    assert manifest["rule_generation"]["synthetic_rule_training_status"] == "ready"
    assert manifest["portrait_generation"]["source_policy"] == "dynamic_rule_decision_supported"
    assert manifest["portrait_generation"]["bazi_alignment_required"] is True
    assert manifest["decision_generation"]["runtime_role"] == "central_runtime_intelligence_for_portraits_questions_and_llm_context"
    assert manifest["decision_generation"]["question_alignment_policy"] == "v20.bazi_domain_alignment_manifest.v1"
    assert manifest["bazi_domain_alignment"]["core_domains"]
    assert "career" in manifest["bazi_domain_alignment"]["applied_domains"]
    assert manifest["knowledge_semantic_modeling"]["runtime_role"] == "semantic_index_for_dynamic_decision_knowledge_and_interaction"
    assert "knowledge_extraction_draft" in manifest["llm_generation"]["allowed_roles"]
    assert "evidence_bounded_practitioner_answer" in manifest["llm_generation"]["allowed_roles"]
    assert "core_rule_truth_override" in manifest["llm_generation"]["forbidden_roles"]
    assert "rule_active_iteration" in manifest["validation_policy"]["synthetic_required_for_iteration_signals"]
    assert "full_corpus_coverage_priors" in manifest["validation_policy"]["synthetic_not_required_for"]
    assert manifest["runtime_mutation"] is False


def test_v20_intelligence_generation_validation_allows_active_iteration() -> None:
    report = validate_intelligence_generation()

    assert report["ok"] is True
    assert report["status"] == "pass"
    assert report["active_training"]["allowed"] is True
    assert report["rule_synthetic"]["ok"] is True
    assert report["bazi_domain_alignment"]["status"] == "ready"
    assert report["active_training"]["rule_synthetic_training_status"] == "ready"
    assert report["runtime_iteration"]["user_visible_runtime_ready"] is True
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
