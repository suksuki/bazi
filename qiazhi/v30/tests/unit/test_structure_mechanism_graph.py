from __future__ import annotations

from v30.core.chart_context import build_chart_context_from_displays
from v30.evidence import compile_feature_evidence
from v30.knowledge import build_knowledge_rule_portrait_signals
from v30.structure import build_mechanism_paths, select_structure_state


def _runtime_parts():
    context = build_chart_context_from_displays(
        reading_id="mechanism-graph",
        year="甲子",
        month="乙丑",
        day="甲寅",
        hour="丁卯",
    )
    evidence = compile_feature_evidence(context)
    signals = build_knowledge_rule_portrait_signals(evidence)
    return context, evidence, signals


def test_mechanism_graph_builds_scored_paths_from_evidence_and_signals() -> None:
    _context, evidence, signals = _runtime_parts()
    paths = build_mechanism_paths(evidence, signals)
    mechanism_ids = {path.mechanism_id for path in paths}
    assert "mechanism.ten_god_visibility_context" in mechanism_ids
    assert "mechanism.useful_god_candidate_gate" in mechanism_ids
    assert "mechanism.hidden_factor_dialogue_probe" in mechanism_ids
    assert "mechanism.branch_relation_dynamic_review" in mechanism_ids
    assert all(path.score > 0 for path in paths)
    assert any(path.path_state == "blocked" for path in paths)


def test_structure_state_consumes_mechanism_paths() -> None:
    context, evidence, signals = _runtime_parts()
    structure = select_structure_state(context, evidence, signals)
    mechanism_nodes = [node for node in structure.graph_nodes if node["kind"] == "mechanism_path"]
    assert "mechanism_path_review" in structure.primary_chain
    assert structure.path_scores["mechanism_path_count"] >= 4.0
    assert structure.path_scores["top_mechanism_score"] > 0
    assert mechanism_nodes
    assert any(edge["relation"] == "supports_mechanism" for edge in structure.graph_edges)


def test_structure_policy_weights_change_mechanism_scores() -> None:
    _context, evidence, signals = _runtime_parts()
    baseline = build_mechanism_paths(evidence, signals)
    weighted = build_mechanism_paths(
        evidence,
        signals,
        {"weights": {"mechanism.hidden_factor_dialogue_probe": 0.5}},
    )
    baseline_hidden = next(row for row in baseline if row.mechanism_id == "mechanism.hidden_factor_dialogue_probe")
    weighted_hidden = next(row for row in weighted if row.mechanism_id == "mechanism.hidden_factor_dialogue_probe")
    assert weighted_hidden.score < baseline_hidden.score
