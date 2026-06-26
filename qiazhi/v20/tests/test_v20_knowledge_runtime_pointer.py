from __future__ import annotations

import json

from v20.learning.knowledge_runtime_pointer import (
    KNOWLEDGE_ACTIVE_POINTER_VERSION,
    build_knowledge_runtime_pointer,
    write_knowledge_runtime_pointer_activate_candidate,
)
from v20.storage.local_jsonl import local_jsonl_store_from_env


def test_v20_knowledge_runtime_pointer_blocks_without_overlay_artifact(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))

    pointer = build_knowledge_runtime_pointer()

    assert pointer["status"] == "blocked"
    assert pointer["runtime_applied"] is False
    assert pointer["blocking_gate"] == "knowledge_rule_review_overlay_not_ready"


def test_v20_knowledge_runtime_pointer_activates_candidate_from_overlay(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    runtime = local_jsonl_store_from_env().runtime_dir
    overlay_dir = runtime / "training" / "knowledge_rule_review_overlay"
    overlay_dir.mkdir(parents=True, exist_ok=True)
    iteration_dir = runtime / "training" / "iteration"
    iteration_dir.mkdir(parents=True, exist_ok=True)
    overlay = {
        "version": "v20.knowledge_rule_review_overlay.v1",
        "status": "ready",
        "rule_count": 1,
        "active_weight_candidate_count": 1,
        "runtime_activation_candidate_count": 1,
        "rules": [
            {
                "rule_key": "rule.strength.capacity",
                "source_knowledge_id": "v20.core.strength_boundary",
                "domain": "strength",
                "validation_state": "active_ready",
                "synthetic_state": "synthetic_passed",
                "synthetic_case_count": 4,
                "support_quality": "strong",
                "active_weight_candidate": True,
                "runtime_activation_candidate": True,
            }
        ],
    }
    (overlay_dir / "latest.json").write_text(json.dumps(overlay), encoding="utf-8")
    (iteration_dir / "latest.json").write_text(
        json.dumps(
            {
                "version": "v20.training_iteration_report.v1",
                "status": "pass",
                "results": {
                    "answer_governance_training": {
                        "version": "v20.answer_governance_training_report.v1",
                        "status": "ready",
                        "average_quality_score": 1.0,
                        "parameter_targets": {"answer_guidance_weight": 0.014},
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    result = write_knowledge_runtime_pointer_activate_candidate(source_role="system", reason="test")
    pointer = build_knowledge_runtime_pointer()

    assert result["status"] == "candidate_active"
    assert result["runtime_mutation"] is True
    assert result["candidate"]["knowledge_policy_count"] == 1
    assert pointer["status"] == "candidate_active"
    assert pointer["runtime_applied"] is True
    policy = pointer["policy_payload"]["knowledge_rule_mapping_policy"][0]
    assert policy["rule_key"] == "rule.strength.capacity"
    assert policy["source_knowledge_id"] == "v20.core.strength_boundary"
    assert policy["mapping_weight_delta"] > 0
    assert policy["answer_governance_quality_score"] == 1.0
    assert policy["answer_governance_quality_delta"] == 0.014
    assert policy["answer_guidance_delta"] > 0.02
    assert result["candidate"]["source_reports"]["answer_governance_weight_delta"] == 0.014
    active_path = runtime / "training" / "knowledge_policy_versions" / "active_pointer.json"
    active = json.loads(active_path.read_text(encoding="utf-8"))
    assert active["version"] == KNOWLEDGE_ACTIVE_POINTER_VERSION
