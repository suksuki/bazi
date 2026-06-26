from __future__ import annotations

from v20.learning_orchestrator.knowledge_rule_orchestrator import build_knowledge_rule_orchestrator_plan
from v20.tests.support_paths import read_v20_text


def test_v20_knowledge_rule_orchestrator_unifies_generation_validation_and_activation() -> None:
    plan = build_knowledge_rule_orchestrator_plan(limit_per_domain=1, synthetic_case_limit=1, overlay_limit=2)

    assert plan["version"] == "v20.knowledge_rule_orchestrator_plan.v1"
    assert plan["status"] == "active_ready"
    assert plan["brain_owner"] == "central_orchestrator"
    assert plan["blockers"] == []
    assert plan["completion_percent"] >= 99
    assert plan["mainline_status"]["training_outputs_apply_directly"] is True
    assert plan["new_knowledge_point_contract"]["generation_policy"] == "knowledge_point_and_rule_candidate_are_created_as_one_unit"
    assert plan["rule_generation"]["preflight_ok"] is True
    assert plan["rule_generation"]["proposal_count"] >= 1
    assert plan["synthetic_validation"]["status"] == "scheduled"
    assert plan["synthetic_validation"]["case_count"] == 1
    assert plan["knowledge_rule_overlay"]["status"] == "scheduled"
    assert plan["parameter_targets"]["knowledge_rule_mapping_weight"] > 0
    assert plan["activation_policy"]["human_review_gate"] is False
    assert plan["activation_policy"]["admin_task_activation_family"] == "training_bundle"
    assert "knowledge_runtime_policy_pointer" in plan["activation_policy"]["runtime_pointer_targets"]
    assert "rule_runtime_policy_pointer" in plan["activation_policy"]["runtime_pointer_targets"]


def test_v20_knowledge_rule_orchestrator_endpoint_and_admin_task_are_declared() -> None:
    server_text = read_v20_text("server.py")
    training_text = read_v20_text("ops/training_tasks.py")

    assert "/api/v20/learning/orchestrator/knowledge-rule-plan" in server_text
    assert "build_knowledge_rule_orchestrator_plan" in server_text
    assert "knowledge_rule_orchestrator" in training_text
    assert "scripts/run_knowledge_rule_orchestrator.py" in training_text
