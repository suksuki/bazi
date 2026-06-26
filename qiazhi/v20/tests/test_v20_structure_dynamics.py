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


def _build_dynamics(
    year: str,
    month: str,
    day: str,
    hour: str,
    *,
    flow_year_pillar: str = "",
    luck_pillar: str = "",
) -> dict:
    chart_facts = build_chart_facts(chart_input_from_displays(year, month, day, hour))
    time_context = build_time_context(chart_facts, flow_year_pillar=flow_year_pillar, luck_pillar=luck_pillar)
    core = infer_core(chart_facts)
    rule_paths = select_rule_paths(build_chart_graph(chart_facts))
    feature_layer = compile_features(chart_facts, core, rule_paths, time_context)
    decision_report = build_decision_report(chart_facts, core, feature_layer, time_context)
    feature_state_model = build_feature_state_model(feature_layer, decision_report)
    return build_structure_dynamics(chart_facts, feature_layer, feature_state_model, time_context, decision_report)


def test_v20_structure_dynamics_builds_deterministic_dynamic_state() -> None:
    dynamics = _build_dynamics("庚午", "辛巳", "丁丑", "乙巳", flow_year_pillar="丙午", luck_pillar="甲申")

    assert dynamics["version"] == "v20.structure_dynamics.v1"
    assert dynamics["status"] == "ready"
    assert dynamics["runtime_mutation"] is False
    assert "SDE_DOES_NOT_CALL_LLM" in dynamics["guardrails"]
    assert dynamics["dynamic_state"]["time_layer_status"] == "ready"
    assert dynamics["dynamic_state"]["energy_strength"] > 0
    assert dynamics["dynamic_state"]["stability_score"] > 0
    assert dynamics["legacy_dynamic_chain"]["nodes"]
    assert len(dynamics["legacy_dynamic_chain"]["nodes"]) <= 3
    assert any("系统裁决" in row for row in dynamics["legacy_dynamic_chain"]["evidence"])
    assert dynamics["chain_state"] in {"closed", "partial", "blocked", "volatile"}
    assert dynamics["activated_structures"]
    assert dynamics["volatility_score"] >= 0
    assert dynamics["sde_v2"]["version"] == "v20.structure_dynamics_graph.v2"
    assert dynamics["sde_algorithm"] == "weighted_dynamic_graph_path_extraction_v2_primary"
    assert dynamics["dominant_path"]["node_labels"]
    assert dynamics["dominant_chain_v2"]["path_id"] == dynamics["dominant_path"]["path_id"]
    assert dynamics["primary_dynamic_chain"]["source_field"] == "dominant_chain_v2"
    assert dynamics["primary_dynamic_chain_source"] == "dominant_chain_v2"
    assert dynamics["primary_dynamic_chain"]["chain_key"] == dynamics["dominant_chain_v2"]["chain_key"]
    assert dynamics["dominant_chain_v2"]["nodes"]
    assert len(dynamics["dominant_chain_v2"]["nodes"]) <= 3
    assert dynamics["dominant_chain_v2"]["selection_basis"] in {"dominant_path_semantic", "top_semantic_candidate"}
    assert dynamics["sde_v2"]["path_diagnostics"]["candidate_path_count"] >= 1
    assert dynamics["sde_v2"]["path_diagnostics"]["continuity_edge_count"] >= 1
    assert dynamics["candidate_paths"]
    assert dynamics["semantic_candidates"]
    node_ids = {node["node_id"] for node in dynamics["nodes"]}
    edge_ids = {edge["edge_id"] for edge in dynamics["edges"]}
    assert len(node_ids) == dynamics["node_count"]
    assert len(edge_ids) == dynamics["edge_count"]
    assert all(edge["source"] in node_ids and edge["target"] in node_ids for edge in dynamics["edges"])


def test_v20_structure_dynamics_preserves_food_controls_killing_pattern() -> None:
    dynamics = _build_dynamics("辛酉", "癸巳", "乙卯", "丁丑")

    chain = dynamics["legacy_dynamic_chain"]
    semantics = {row["label"] for row in dynamics["semantic_candidates"]}
    assert chain["pattern_key"] == "food_controls_killing"
    assert chain["pattern_label"] == "食神制杀"
    assert chain["nodes"][:2] == ("output", "authority")
    assert any("食神制杀" in row for row in chain["evidence"])
    assert "食伤生财" not in chain["pattern_label"]
    assert "食神制杀" in semantics
    candidate_labels = " ".join(" ".join(row["node_labels"]) for row in dynamics["candidate_paths"])
    assert "食神" in candidate_labels
    assert "七杀" in candidate_labels
    assert dynamics["dominant_chain_v2"]["pattern_label"] == "食神制杀"
    assert dynamics["dominant_chain_v2"]["node_labels"] == ["丁食神", "辛七杀", "癸偏印", "乙日主"]
    assert dynamics["dominant_chain_v2"]["edge_labels"] == ["制约", "相生", "承接日主"]


def test_v20_structure_dynamics_can_promote_hidden_food_killing_work_path() -> None:
    dynamics = _build_dynamics("庚午", "辛巳", "丁丑", "乙巳")

    chain = dynamics["legacy_dynamic_chain"]
    semantics = {row["label"] for row in dynamics["semantic_candidates"]}
    assert chain["pattern_key"] == "output_to_wealth"
    assert chain["pattern_label"] == "食伤生财"
    assert chain["nodes"][:2] == ("output", "wealth")
    assert "食伤生财" in semantics
    assert dynamics["dominant_chain_v2"]["pattern_label"] in {"食神制杀", "食伤生财", "财生官/财滋杀", "官印/杀印相生"}
    if dynamics["dominant_chain_v2"]["pattern_label"] == "食神制杀":
        assert dynamics["dominant_chain_v2"]["node_labels"] == ["己食神", "癸七杀", "乙偏印", "丁日主"]


def test_v20_structure_dynamics_dominant_label_uses_mechanism_below_runtime_threshold(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    pointer_dir = tmp_path / "training" / "structure_dynamics_policy_versions"
    pointer_dir.mkdir(parents=True)
    (pointer_dir / "active_pointer.json").write_text(
        """
{
  "version": "v20.structure_dynamics_runtime_active_pointer.v1",
  "status": "active",
  "active_policy_version": "v20.structure_dynamics_policy.high_threshold",
  "policy_payload": {
    "semantic_match_policy": {"semantic_match_threshold": 0.92}
  }
}
""".strip(),
        encoding="utf-8",
    )

    dynamics = _build_dynamics("壬寅", "癸卯", "甲辰", "乙亥")
    chain = dynamics["dominant_chain_v2"]

    assert chain["pattern_label"] != "核心做功链"
    assert chain["pattern_label"] == "印星承身"
    assert chain["selection_basis"] in {"dominant_path_semantic", "dominant_path_mechanism_below_runtime_threshold"}


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
    assert "dominant_chain" not in dynamics
    assert "legacy_dynamic_chain" in dynamics
    assert "dominant_path" in dynamics
    assert "dominant_chain_v2" in dynamics
    assert "primary_dynamic_chain" in dynamics
    assert dynamics["dominant_path"]["path_id"].startswith("dynamic_path.")
    assert dynamics["dominant_chain_v2"]["chain_key"]
    assert dynamics["primary_dynamic_chain"]["source_field"] == "dominant_chain_v2"
    assert len(dynamics["legacy_dynamic_chain"]["nodes"]) <= 3
    assert any("系统裁决" in row for row in dynamics["legacy_dynamic_chain"]["evidence"])
    assert "activated_structures" in dynamics
    assert result["runtime_mutation"] is False
