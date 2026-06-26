from __future__ import annotations

from v20.ops.mainline_status import build_mainline_status
from v20.tests.support_paths import read_v20_text


def test_v20_mainline_status_reports_continuous_iteration_ready() -> None:
    status = build_mainline_status()

    assert status["version"] == "v20.mainline_status.v1"
    assert status["status"] == "continuous_iteration_ready"
    assert status["completion_percent"] == 100
    assert status["completion_label"] == "100%"
    assert status["blockers"] == []
    assert status["runtime_mutation"] is False
    assert status["principle"]["training_outputs_apply_directly"] is True
    assert status["principle"]["no_human_review_gate_for_training"] is True


def test_v20_mainline_status_aligns_knowledge_and_direct_training_targets() -> None:
    status = build_mainline_status()
    knowledge = status["knowledge"]
    answer_training = status["answer_governance_training"]
    role_view = status["role_view"]
    runtime_consumption = status["runtime_consumption"]
    llm_design = status["llm_prompt_context_design"]

    assert knowledge["status"] == "complete"
    assert knowledge["rule_count"] >= 489
    assert knowledge["runtime_allowed_count"] == knowledge["rule_count"]
    assert knowledge["synthetic_case_count"] >= 50
    assert knowledge["external_topic_covered_count"] == knowledge["external_topic_count"]
    assert knowledge["p0_gap_count"] == 0
    for node_key in ("L7", "L8", "L12"):
        assert knowledge["key_nodes"][node_key]["synthetic_case_count"] >= 3

    assert answer_training["status"] == "ready"
    assert answer_training["direct_parameter_targets_ready"] is True
    assert answer_training["answer_guidance_weight"] > 0
    assert answer_training["role_answer_governance_weight"] > 0
    assert role_view["direct_strategy_path_ready"] is True
    assert runtime_consumption["status"] == "complete"
    assert llm_design["completion_percent"] == 100
    assert llm_design["context_layer_count"] >= 6
    assert llm_design["retired_context_count"] == 1


def test_v20_mainline_status_endpoint_is_declared() -> None:
    server_text = read_v20_text("server.py")

    assert "/api/v20/admin/mainline-status" in server_text
    assert "build_mainline_status" in server_text
