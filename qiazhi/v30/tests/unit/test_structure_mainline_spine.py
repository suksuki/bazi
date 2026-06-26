from __future__ import annotations

from v30.core.chart_context import build_chart_context_from_displays
from v30.evidence import compile_feature_evidence
from v30.knowledge import build_knowledge_rule_portrait_signals
from v30.mainline import select_mainline_state
from v30.structure import select_structure_state


def test_structure_state_is_bound_to_feature_evidence() -> None:
    context = build_chart_context_from_displays(
        reading_id="spine-structure",
        year="甲子",
        month="戊辰",
        day="甲午",
        hour="辛酉",
    )
    evidence = compile_feature_evidence(context)
    signals = build_knowledge_rule_portrait_signals(evidence)
    structure = select_structure_state(context, evidence, signals)
    assert structure.structure_id.startswith(context.context_id)
    assert structure.evidence_ids
    assert "chart_context" in structure.primary_chain
    assert structure.state == "partial_missing_time"
    assert structure.boundary == "minimal_evidence_bound_structure_until_graph_engine"
    assert "knowledge_signal_review" in structure.primary_chain
    assert "rule_signal_review" in structure.primary_chain
    assert "portrait_signal_review" in structure.primary_chain
    assert "strength_pattern_candidate_review" in structure.primary_chain
    assert "domain_rule_candidate_review" in structure.primary_chain
    assert structure.path_scores["knowledge_signal_count"] == 1.0
    assert structure.path_scores["rule_evidence_count"] >= 4.0
    assert structure.path_scores["mechanism_path_count"] >= 4.0
    assert structure.path_scores["strength_pattern_review_count"] >= 2.0
    assert structure.path_scores["dynamic_path_resolution_family_count"] > 0
    assert structure.path_scores["dynamic_wealth_path_count"] > 0
    assert structure.path_scores["structure_policy_weighted"] == 0.0
    assert structure.graph_nodes


def test_mainline_consumes_structure_and_preserves_time_boundary() -> None:
    context = build_chart_context_from_displays(
        reading_id="spine-mainline",
        year="甲子",
        month="戊辰",
        day="甲午",
        hour="辛酉",
    )
    evidence = compile_feature_evidence(context)
    signals = build_knowledge_rule_portrait_signals(evidence)
    structure = select_structure_state(context, evidence, signals)
    mainline = select_mainline_state(structure, evidence, signals)
    assert mainline.primary_structure_id == structure.structure_id
    assert mainline.evidence_ids == structure.evidence_ids
    assert mainline.quality_gate == "needs_time_context"
    assert "timing claims remain blocked" in mainline.why_selected
    assert "Rule signals are bound" in mainline.why_selected
    assert "Rule evidence is executed and bound" in mainline.why_selected
    assert "Portrait signals remain hypotheses" in mainline.why_selected
    assert "Mechanism paths are scored" in mainline.why_selected
    assert "Strength, 格局, and useful-god family signals remain candidate reviews" in mainline.why_selected
    assert "domain rules remain review candidates" in mainline.why_selected
    assert "Path-resolution families are available" in mainline.why_selected
    assert "Domain rule paths are available" in mainline.why_selected
    assert any(row.startswith("rule_signal:") for row in mainline.supporting_mainlines)
    assert any(row.startswith("rule_evidence:") for row in mainline.supporting_mainlines)
    assert "strength_pattern_candidate_review" in mainline.supporting_mainlines
    assert "domain_rule_candidate_review" in mainline.supporting_mainlines


def test_mainline_accepts_explicit_time_context() -> None:
    context = build_chart_context_from_displays(
        reading_id="spine-mainline-time",
        year="甲子",
        month="戊辰",
        day="甲午",
        hour="辛酉",
        luck_pillar="庚午",
    )
    evidence = compile_feature_evidence(context)
    structure = select_structure_state(context, evidence)
    mainline = select_mainline_state(structure, evidence)
    assert mainline.quality_gate == "evidence_bound"
    assert structure.state in {"evidence_bound_dynamic_review", "evidence_bound_static_review"}
    assert structure.path_scores["rule_countered_count"] >= 1.0
    assert "rule_counterevidence_review" in structure.primary_chain
    assert "Counter-evidence is present" in mainline.why_selected
