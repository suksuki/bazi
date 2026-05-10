from __future__ import annotations

from v20.api.runtime import run_runtime_from_pillars
from v20.core.chart import build_chart_facts, chart_input_from_displays
from v20.core.strength import infer_core
from v20.core.time_context import build_time_context
from v20.decision.engine import build_decision_report
from v20.dynamics.engine import build_structure_dynamics
from v20.features.compiler import compile_features
from v20.features.state_model import build_feature_state_model
from v20.graph.chart_graph import build_chart_graph
from v20.graph.rule_graph import select_rule_paths


def test_v20_structure_dynamics_builds_deterministic_dynamic_state() -> None:
    chart_facts = build_chart_facts(chart_input_from_displays("庚午", "辛巳", "丁丑", "乙巳"))
    time_context = build_time_context(chart_facts, flow_year_pillar="丙午", luck_pillar="甲申")
    core = infer_core(chart_facts)
    rule_paths = select_rule_paths(build_chart_graph(chart_facts))
    feature_layer = compile_features(chart_facts, core, rule_paths, time_context)
    decision_report = build_decision_report(chart_facts, core, feature_layer, time_context)
    feature_state_model = build_feature_state_model(feature_layer, decision_report)

    dynamics = build_structure_dynamics(chart_facts, feature_layer, feature_state_model, time_context, decision_report)

    assert dynamics["version"] == "v20.structure_dynamics.v1"
    assert dynamics["status"] == "ready"
    assert dynamics["runtime_mutation"] is False
    assert "SDE_DOES_NOT_CALL_LLM" in dynamics["guardrails"]
    assert dynamics["dynamic_state"]["time_layer_status"] == "ready"
    assert dynamics["dynamic_state"]["energy_strength"] > 0
    assert dynamics["dynamic_state"]["stability_score"] > 0
    assert dynamics["dominant_chain"]["nodes"]
    assert len(dynamics["dominant_chain"]["nodes"]) <= 3
    assert any("系统裁决" in row for row in dynamics["dominant_chain"]["evidence"])
    assert dynamics["chain_state"] in {"closed", "partial", "blocked", "volatile"}
    assert dynamics["activated_structures"]
    assert dynamics["volatility_score"] >= 0
    node_ids = {node["node_id"] for node in dynamics["nodes"]}
    edge_ids = {edge["edge_id"] for edge in dynamics["edges"]}
    assert len(node_ids) == dynamics["node_count"]
    assert len(edge_ids) == dynamics["edge_count"]
    assert all(edge["source"] in node_ids and edge["target"] in node_ids for edge in dynamics["edges"])


def test_v20_runtime_exposes_structure_dynamics_contract() -> None:
    result = run_runtime_from_pillars(
        "庚午",
        "辛巳",
        "丁丑",
        "乙巳",
        input_id="v20.sde.contract",
        flow_year_pillar="丙午",
        luck_pillar="甲申",
    )

    dynamics = result["structure_dynamics"]
    assert dynamics["version"] == "v20.structure_dynamics.v1"
    assert dynamics["source"] == "ChartFacts+FeatureLayer+FeatureStateModel+DecisionReport+PortraitProjection+TimeContext"
    assert dynamics["dynamic_state"]["time_layer_status"] == "ready"
    assert "dominant_chain" in dynamics
    assert len(dynamics["dominant_chain"]["nodes"]) <= 3
    assert any("系统裁决" in row for row in dynamics["dominant_chain"]["evidence"])
    assert "activated_structures" in dynamics
    assert result["runtime_mutation"] is False
