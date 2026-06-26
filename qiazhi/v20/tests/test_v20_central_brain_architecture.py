from __future__ import annotations

from v20.ops.central_brain_architecture import build_central_brain_architecture_status
from v20.ops.mainline_status import build_mainline_status
from v20.tests.support_paths import read_v20_text, v20_path


def test_v20_central_brain_architecture_defines_control_graph_and_direct_apply() -> None:
    status = build_central_brain_architecture_status()
    nodes = {row["node_key"] for row in status["brain_graph"]["nodes"]}
    modules = {row["module_key"]: row for row in status["modules"]}
    topics = {row["topic_key"]: row for row in status["training_topics"]}
    llm_design = status["llm_prompt_context_design"]
    tuning_contract = status["tuning_package_contract"]

    assert status["version"] == "v20.central_brain_architecture.v1"
    assert status["status"] == "active_ready"
    assert status["completion_percent"] == 100
    assert status["principles"]["central_brain_controls_modules"] is True
    assert status["principles"]["no_human_review_gate"] is True
    assert status["principles"]["training_outputs_apply_directly"] is True
    assert status["principles"]["training_signals_unified_by_tuning_package"] is True
    assert {
        "knowledge_gap_pick",
        "rule_candidate_generation",
        "portrait_mapping_generation",
        "question_policy_generation",
        "role_policy_generation",
        "llm_context_policy_generation",
        "synthetic_validation",
        "corpus_replay_518k",
        "parameter_optimizer",
        "runtime_pointer_publish",
        "ui_observability",
    } <= nodes
    assert {"knowledge", "rule", "portrait", "question", "role_view", "llm_context", "synthetic", "corpus_518k", "orchestrator"} <= set(modules)
    assert modules["corpus_518k"]["runtime_pointer_target"] == "corpus_runtime_policy_pointer"
    assert {"central_brain", "knowledge_rule", "portrait_question_role", "llm_context", "synthetic", "corpus_518k"} <= set(topics)
    assert "knowledge_rule_orchestrator" in topics["central_brain"]["atomic_trainings"]
    assert "answer_governance_training" in topics["llm_context"]["atomic_trainings"]
    assert "role_context_density_weight" in topics["llm_context"]["parameter_targets"]
    assert llm_design["status"] == "complete"
    assert llm_design["completion_percent"] == 100
    assert "context.system_understanding.role_context" in llm_design["context_layers"]
    assert "answer/prompt_context.py" in llm_design["retired_context_paths"]
    assert tuning_contract["owner_node"] == "parameter_optimizer"
    assert "bazi_context_drift_score" in tuning_contract["input_signals"]
    assert "parameter_updates" in tuning_contract["output_contract"]
    assert "context_drift_score == 0" in tuning_contract["direct_apply_requirements"]
    assert "corpus_runtime_policy_pointer" in status["runtime_pointer_targets"]


def test_v20_central_brain_architecture_aligns_ui_and_mainline_status() -> None:
    architecture = build_central_brain_architecture_status()
    mainline = build_mainline_status()
    ui = architecture["ui_alignment"]

    assert "central_brain_graph" in ui["required_panels"]
    assert "runtime_pointer_effects" in ui["required_panels"]
    assert "parameter_targets" in ui["required_task_fields"]
    assert "blocking_machine_reason" in ui["required_task_fields"]
    assert mainline["central_brain_architecture"]["status"] == "active_ready"
    assert mainline["central_brain_architecture"]["brain_graph_node_count"] >= 10
    assert mainline["central_brain_architecture"]["ui_alignment_status"] == "required"
    assert mainline["llm_prompt_context_design"]["completion_percent"] == 100
    assert mainline["llm_prompt_context_design"]["retired_context_count"] == 1


def test_v20_central_brain_architecture_doc_and_endpoint_are_declared() -> None:
    doc = v20_path("docs/V20_CENTRAL_BRAIN_INTELLIGENCE_ARCHITECTURE.md")
    server_text = read_v20_text("server.py")
    mainline_doc = read_v20_text("docs/V20_KNOWLEDGE_BRAIN_MAINLINE.md")

    assert doc.exists()
    assert "中枢大脑统一调配" in doc.read_text(encoding="utf-8")
    assert "/api/v20/admin/central-brain-architecture" in server_text
    assert "build_central_brain_architecture_status" in server_text
    assert "V20_CENTRAL_BRAIN_INTELLIGENCE_ARCHITECTURE.md" in mainline_doc
