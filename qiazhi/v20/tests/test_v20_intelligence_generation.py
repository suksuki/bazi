from __future__ import annotations

from fastapi.testclient import TestClient

from v20.intelligence.generation import build_intelligence_generation_manifest
from v20.server import app
from v20.validation.intelligence_generation import validate_intelligence_generation


def test_v20_intelligence_generation_manifest_names_generation_boundaries() -> None:
    manifest = build_intelligence_generation_manifest()

    assert manifest["status"] == "ready"
    assert manifest["knowledge_generation"]["shadow_learning_allowed"] is True
    assert manifest["rule_generation"]["shadow_training_allowed"] is True
    assert manifest["rule_generation"]["user_visible_runtime_allowed"] is False
    assert manifest["portrait_generation"]["source_policy"] == "feature_first_knowledge_supported"
    assert "knowledge_extraction_draft" in manifest["llm_generation"]["allowed_roles"]
    assert "core_rule_truth_override" in manifest["llm_generation"]["forbidden_roles"]
    assert "user_visible_rule_promotion" in manifest["validation_policy"]["synthetic_required_for"]
    assert "shadow_training" in manifest["validation_policy"]["synthetic_not_required_for"]
    assert manifest["runtime_mutation"] is False


def test_v20_intelligence_generation_validation_allows_shadow_but_not_promotion() -> None:
    report = validate_intelligence_generation()

    assert report["ok"] is True
    assert report["status"] == "pass"
    assert report["shadow_training"]["allowed"] is True
    assert report["promotion"]["user_visible_rule_promotion_ready"] is False
    assert report["runtime_mutation"] is False


def test_v20_intelligence_generation_endpoints_are_read_only() -> None:
    client = TestClient(app)
    manifest = client.get("/api/v20/intelligence/generation-manifest").json()
    validation = client.get("/api/v20/validation/intelligence-generation").json()

    assert manifest["runtime_mutation"] is False
    assert validation["runtime_mutation"] is False
    assert validation["status"] == "pass"
