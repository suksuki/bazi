from __future__ import annotations

from v30.contracts import ChartContext, FeatureEvidence, StructureState
from v30.knowledge import KnowledgeRulePortraitSignal
from v30.structure.dynamic_graph import (
    build_dynamic_graph,
    dynamic_graph_edges,
    dynamic_graph_nodes,
    dynamic_path_edges,
    dynamic_path_nodes,
)
from v30.structure.mechanism_graph import MechanismPath, build_mechanism_paths, mechanism_graph_edges, mechanism_graph_nodes


STRUCTURE_SELECTOR_VERSION = "v30.structure_selector.v1"


def select_structure_state(
    context: ChartContext,
    evidence: list[FeatureEvidence],
    knowledge_rule_portrait_signals: list[KnowledgeRulePortraitSignal] | None = None,
    structure_policy: dict[str, object] | None = None,
    model_signal_summary: dict[str, object] | None = None,
) -> StructureState:
    signals = knowledge_rule_portrait_signals or []
    model_signal_summary = model_signal_summary if isinstance(model_signal_summary, dict) else {}
    mechanisms = build_mechanism_paths(evidence, signals, structure_policy)
    dynamic_nodes, dynamic_edges, dynamic_paths = build_dynamic_graph(evidence, structure_policy)
    evidence_by_domain = _by_domain(evidence)
    primary_chain = _primary_chain(evidence_by_domain, signals, mechanisms)
    state = _state(evidence_by_domain)
    confidence = _confidence(evidence)
    evidence_ids = [
        row.evidence_id
        for row in evidence
        if row.domain in {"chart", "ten_god", "ten_god_energy", "element", "structure_pattern", "domain_rule", "branch_relation", "time_context", "rule"}
    ]
    return StructureState(
        structure_id=f"{context.context_id}:structure:primary",
        primary_chain=primary_chain,
        candidate_chains=_candidate_chains(evidence_by_domain, mechanisms),
        graph_nodes=(
            _graph_nodes(signals)
            + mechanism_graph_nodes(mechanisms)
            + dynamic_graph_nodes(dynamic_nodes)
            + dynamic_path_nodes(dynamic_paths)
        ),
        graph_edges=(
            _graph_edges(signals)
            + mechanism_graph_edges(mechanisms)
            + dynamic_graph_edges(dynamic_edges)
            + dynamic_path_edges(dynamic_paths)
        ),
        path_scores={
            "evidence_coverage": round(min(1.0, len(evidence_ids) / 6), 3),
            "confidence": confidence,
            "knowledge_signal_count": float(_signal_count(signals, "knowledge")),
            "rule_signal_count": float(_signal_count(signals, "rule")),
            "portrait_signal_count": float(_signal_count(signals, "portrait")),
            "rule_evidence_count": float(len(evidence_by_domain.get("rule", []))),
            "rule_countered_count": float(_rule_state_count(evidence_by_domain, "countered")),
            "rule_blocked_count": float(_rule_state_count(evidence_by_domain, "blocked")),
            "ten_god_energy_ready": 1.0 if "ten_god_energy" in evidence_by_domain else 0.0,
            "ten_god_energy_dominant_count": float(_support_bucket_count(evidence_by_domain, "ten_god_energy:", "high")),
            "ten_god_energy_high_volatility_count": float(_support_bucket_count(evidence_by_domain, "ten_god_volatility:", "high")),
            "ten_god_energy_low_stability_count": float(_support_bucket_count(evidence_by_domain, "ten_god_stability:", "low")),
            "model_signal_summary_ready": 1.0 if model_signal_summary.get("status") == "ready" else 0.0,
            "model_signal_energy_band_count": float(_model_signal_energy_band_count(model_signal_summary)),
            "model_signal_volatility_alert_count": float(_model_signal_list_count(model_signal_summary, "volatility_alerts")),
            "model_signal_stability_alert_count": float(_model_signal_list_count(model_signal_summary, "stability_alerts")),
            "model_signal_structure_path_adjustment": _model_signal_structure_path_adjustment(
                model_signal_summary,
                structure_policy,
            ),
            "structure_policy_model_signal_fusion": _structure_policy_weight(
                structure_policy,
                "dynamic_graph.model_signal_fusion",
            ),
            "top_dynamic_path_model_signal_adjusted_score": _model_signal_adjusted_top_score(
                dynamic_paths[0].score if dynamic_paths else 0.0,
                model_signal_summary,
                structure_policy,
            ),
            "mechanism_path_count": float(len(mechanisms)),
            "top_mechanism_score": mechanisms[0].score if mechanisms else 0.0,
            "dynamic_graph_node_count": float(len(dynamic_nodes)),
            "dynamic_graph_edge_count": float(len(dynamic_edges)),
            "dynamic_path_count": float(len(dynamic_paths)),
            "top_dynamic_path_score": dynamic_paths[0].score if dynamic_paths else 0.0,
            "dynamic_competing_path_count": float(sum(1 for path in dynamic_paths if path.competition_rank > 1)),
            "dynamic_suppressed_path_count": float(sum(1 for path in dynamic_paths if path.suppression > 0)),
            "dynamic_blocked_path_count": float(sum(1 for path in dynamic_paths if path.state == "blocked")),
            "dynamic_countered_path_count": float(sum(1 for path in dynamic_paths if path.state == "countered")),
            "dynamic_conflict_path_count": float(sum(1 for path in dynamic_paths if path.state == "conflict")),
            "dynamic_conflict_family_count": float(len({
                family
                for path in dynamic_paths
                for family in path.conflict_families
            })),
            "dynamic_path_resolution_family_count": float(len({
                family
                for path in dynamic_paths
                for family in path.resolution_families
            })),
            "dynamic_branch_conflict_edge_count": float(sum(1 for edge in dynamic_edges if edge.role == "conflict")),
            "dynamic_branch_alignment_edge_count": float(sum(
                1
                for edge in dynamic_edges
                if edge.role == "continuity" and edge.edge_type.startswith("branch_")
            )),
            "top_dynamic_path_suppression": dynamic_paths[0].suppression if dynamic_paths else 0.0,
            "strength_pattern_review_count": float(len(evidence_by_domain.get("structure_pattern", []))),
            "dynamic_wealth_path_count": float(_domain_path_count(dynamic_paths, "wealth")),
            "dynamic_wealth_competition_path_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:wealth_competition")),
            "dynamic_wealth_output_generation_path_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:wealth_output_generation_path")),
            "dynamic_wealth_authority_bridge_path_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:wealth_authority_bridge_path")),
            "dynamic_career_path_count": float(_domain_path_count(dynamic_paths, "career")),
            "dynamic_career_authority_pressure_path_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:career_authority_pressure_path")),
            "dynamic_career_resource_resolution_path_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:career_resource_resolution_path")),
            "dynamic_relationship_path_count": float(_relationship_path_count(dynamic_paths, evidence_by_domain)),
            "dynamic_relationship_conflict_path_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:relationship_conflict_path")),
            "dynamic_relationship_alignment_path_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:relationship_alignment_review_path")),
            "dynamic_relationship_marker_path_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:relationship_authority_or_wealth_marker_path")),
            "dynamic_health_review_path_count": float(_health_path_count(dynamic_paths, evidence_by_domain)),
            "dynamic_health_element_excess_review_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:health_element_excess_review")),
            "dynamic_health_element_thin_review_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:health_element_thin_review")),
            "dynamic_health_conflict_pressure_review_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:health_conflict_pressure_review")),
            "dynamic_useful_god_candidate_path_count": float(_useful_god_candidate_path_count(dynamic_paths, evidence_by_domain)),
            "dynamic_useful_god_ranked_candidate_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:useful_god_candidate_path")),
            "dynamic_tongguan_path_count": float(_resolution_family_count(dynamic_paths, "tongguan") + _support_prefix_count(evidence_by_domain, "domain_rule_family:tongguan_")),
            "dynamic_tongguan_resource_mediator_path_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:tongguan_resource_mediator_path")),
            "dynamic_tongguan_output_wealth_bridge_path_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:tongguan_output_wealth_bridge_path")),
            "dynamic_zhihua_path_count": float(_resolution_family_count(dynamic_paths, "zhihua") + _support_prefix_count(evidence_by_domain, "domain_rule_family:zhihua_")),
            "dynamic_zhihua_output_authority_path_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:zhihua_output_controls_authority_path")),
            "dynamic_zhihua_wealth_authority_resource_path_count": float(_support_path_count(evidence_by_domain, "domain_rule_family:zhihua_wealth_authority_resource_path")),
            "structure_policy_weighted": 1.0 if _has_weights(structure_policy) else 0.0,
        },
        semantic_label=_semantic_label(evidence_by_domain, signals, mechanisms),
        state=state,
        confidence=confidence,
        evidence_ids=evidence_ids,
        boundary="minimal_evidence_bound_structure_until_graph_engine",
    )


def _by_domain(evidence: list[FeatureEvidence]) -> dict[str, list[FeatureEvidence]]:
    rows: dict[str, list[FeatureEvidence]] = {}
    for item in evidence:
        rows.setdefault(item.domain, []).append(item)
    return rows


def _primary_chain(
    evidence_by_domain: dict[str, list[FeatureEvidence]],
    signals: list[KnowledgeRulePortraitSignal],
    mechanisms: list[MechanismPath],
) -> list[str]:
    chain = ["chart_context"]
    if "ten_god" in evidence_by_domain:
        chain.append("ten_god_visibility")
    if "ten_god_energy" in evidence_by_domain:
        chain.append("ten_god_energy_model")
    if "element" in evidence_by_domain:
        chain.append("element_distribution")
    if "branch_relation" in evidence_by_domain:
        chain.append("branch_relation_review")
    if "structure_pattern" in evidence_by_domain:
        chain.append("strength_pattern_candidate_review")
    if "domain_rule" in evidence_by_domain:
        chain.append("domain_rule_candidate_review")
    if "time_context" in evidence_by_domain:
        chain.append("time_context_boundary")
    if "rule" in evidence_by_domain:
        chain.append("rule_evidence_review")
    if _rule_state_count(evidence_by_domain, "countered"):
        chain.append("rule_counterevidence_review")
    if _signal_count(signals, "knowledge"):
        chain.append("knowledge_signal_review")
    if _signal_count(signals, "rule"):
        chain.append("rule_signal_review")
    if _signal_count(signals, "portrait"):
        chain.append("portrait_signal_review")
    if mechanisms:
        chain.append("mechanism_path_review")
    if "rule" in evidence_by_domain:
        chain.append("dynamic_graph_review")
    return chain


def _candidate_chains(
    evidence_by_domain: dict[str, list[FeatureEvidence]],
    mechanisms: list[MechanismPath],
) -> list[list[str]]:
    rows: list[list[str]] = []
    if "useful_god" in evidence_by_domain:
        rows.append(["chart_context", "useful_god_evidence_gate"])
    if "branch_relation" in evidence_by_domain:
        rows.append(["chart_context", "branch_relation_review", "structure_dynamic_review"])
    if "structure_pattern" in evidence_by_domain:
        rows.append(["chart_context", "strength_pattern_review", "pattern_candidate_boundary"])
    if "domain_rule" in evidence_by_domain:
        rows.append(["chart_context", "domain_rule_review", "life_domain_outcome_boundary"])
    if "ten_god_energy" in evidence_by_domain:
        rows.append(["chart_context", "ten_god_energy_model", "energy_stability_volatility_review"])
    if "time_context" in evidence_by_domain:
        rows.append(["chart_context", "time_context_boundary"])
    for row in evidence_by_domain.get("rule", []):
        rows.append(["chart_context", "rule_evidence", row.kind])
    rows.extend([["chart_context", mechanism.mechanism_id, mechanism.path_state] for mechanism in mechanisms])
    return rows


def _state(evidence_by_domain: dict[str, list[FeatureEvidence]]) -> str:
    time_rows = evidence_by_domain.get("time_context", [])
    if any(row.kind == "missing_requirement" for row in time_rows):
        return "partial_missing_time"
    if "branch_relation" in evidence_by_domain:
        return "evidence_bound_dynamic_review"
    return "evidence_bound_static_review"


def _semantic_label(
    evidence_by_domain: dict[str, list[FeatureEvidence]],
    signals: list[KnowledgeRulePortraitSignal],
    mechanisms: list[MechanismPath],
) -> str:
    parts = ["evidence-bound chart structure"]
    if "branch_relation" in evidence_by_domain:
        parts.append("branch relations require dynamic review")
    if "structure_pattern" in evidence_by_domain:
        parts.append("strength and pattern review remains candidate-bound")
    if "ten_god_energy" in evidence_by_domain:
        parts.append("ten-god energy model scored")
    if "domain_rule" in evidence_by_domain:
        parts.append("domain rules remain review candidates")
    if any(row.kind == "missing_requirement" for row in evidence_by_domain.get("time_context", [])):
        parts.append("time layer missing")
    if signals:
        parts.append("knowledge/rule/portrait signals bound")
    if "rule" in evidence_by_domain:
        parts.append("rule evidence executed")
    if _rule_state_count(evidence_by_domain, "countered"):
        parts.append("counter-evidence present")
    if mechanisms:
        parts.append("mechanism paths scored")
    return "; ".join(parts)


def _confidence(evidence: list[FeatureEvidence]) -> float:
    if not evidence:
        return 0.0
    relevant = [row.confidence for row in evidence if row.domain != "useful_god"]
    if not relevant:
        relevant = [row.confidence for row in evidence]
    return round(sum(relevant) / len(relevant), 3)


def _signal_count(signals: list[KnowledgeRulePortraitSignal], signal_type: str) -> int:
    return sum(1 for signal in signals if signal.signal_type == signal_type)


def _rule_state_count(evidence_by_domain: dict[str, list[FeatureEvidence]], state: str) -> int:
    return sum(
        1
        for row in evidence_by_domain.get("rule", [])
        if f"rule_decision_state:{state}" in row.supports
    )


def _graph_nodes(signals: list[KnowledgeRulePortraitSignal]) -> list[dict[str, object]]:
    return [
        {
            "node_id": signal.signal_id,
            "kind": signal.signal_type,
            "source_id": signal.source_id,
            "boundary": signal.boundary,
        }
        for signal in signals
    ]


def _graph_edges(signals: list[KnowledgeRulePortraitSignal]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for signal in signals:
        for evidence_id in signal.evidence_ids:
            rows.append(
                {
                    "from": evidence_id,
                    "to": signal.signal_id,
                    "relation": "supports_signal",
                }
            )
    return rows


def _model_signal_energy_band_count(model_signal_summary: dict[str, object]) -> int:
    rows = model_signal_summary.get("energy_bands", [])
    return len(rows) if isinstance(rows, list) else 0


def _model_signal_list_count(model_signal_summary: dict[str, object], key: str) -> int:
    rows = model_signal_summary.get(key, [])
    return len(rows) if isinstance(rows, list) else 0


def _model_signal_structure_path_adjustment(
    model_signal_summary: dict[str, object],
    structure_policy: dict[str, object] | None = None,
) -> float:
    if not model_signal_summary:
        return 0.0
    energy_count = _model_signal_energy_band_count(model_signal_summary)
    volatility_count = _model_signal_list_count(model_signal_summary, "volatility_alerts")
    stability_count = _model_signal_list_count(model_signal_summary, "stability_alerts")
    policy_weight = _structure_policy_weight(structure_policy, "dynamic_graph.model_signal_fusion")
    support = min(0.08, energy_count * 0.02 * policy_weight)
    review_penalty = min(0.06, (volatility_count + stability_count) * 0.015)
    return round(support - review_penalty, 3)


def _model_signal_adjusted_top_score(
    base_score: float,
    model_signal_summary: dict[str, object],
    structure_policy: dict[str, object] | None = None,
) -> float:
    if base_score <= 0:
        return 0.0
    return round(max(0.0, base_score + _model_signal_structure_path_adjustment(model_signal_summary, structure_policy)), 3)


def _structure_policy_weight(structure_policy: dict[str, object] | None, key: str) -> float:
    weights = (structure_policy or {}).get("weights", {})
    if not isinstance(weights, dict):
        return 1.0
    try:
        return float(weights.get(key, weights.get("*", 1.0)))
    except (TypeError, ValueError):
        return 1.0


def _has_weights(structure_policy: dict[str, object] | None) -> bool:
    return isinstance((structure_policy or {}).get("weights"), dict)


def _domain_path_count(dynamic_paths, domain: str) -> int:
    family_by_domain = {
        "wealth": {"wealth", "self"},
        "career": {"authority", "resource"},
    }.get(domain, set())
    return sum(1 for path in dynamic_paths if family_by_domain & set(path.family_chain))


def _relationship_path_count(dynamic_paths, evidence_by_domain: dict[str, list[FeatureEvidence]]) -> int:
    if "branch_relation" not in evidence_by_domain:
        return 0
    return sum(1 for path in dynamic_paths if {"wealth", "authority", "self"} & set(path.family_chain))


def _health_path_count(dynamic_paths, evidence_by_domain: dict[str, list[FeatureEvidence]]) -> int:
    if "structure_pattern" not in evidence_by_domain:
        return 0
    return sum(1 for path in dynamic_paths if path.conflict_families or path.resolution_families)


def _useful_god_candidate_path_count(dynamic_paths, evidence_by_domain: dict[str, list[FeatureEvidence]]) -> int:
    if "structure_pattern" not in evidence_by_domain or "useful_god" not in evidence_by_domain:
        return 0
    return sum(1 for path in dynamic_paths if path.resolution_families)


def _support_path_count(evidence_by_domain: dict[str, list[FeatureEvidence]], support: str) -> int:
    return sum(
        1
        for row in evidence_by_domain.get("domain_rule", [])
        if support in row.supports
    )


def _support_prefix_count(evidence_by_domain: dict[str, list[FeatureEvidence]], prefix: str) -> int:
    return sum(
        1
        for rows in evidence_by_domain.values()
        for row in rows
        for support in row.supports
        if support.startswith(prefix)
    )


def _support_bucket_count(evidence_by_domain: dict[str, list[FeatureEvidence]], prefix: str, bucket: str) -> int:
    return sum(
        1
        for rows in evidence_by_domain.values()
        for row in rows
        for support in row.supports
        if support.startswith(prefix) and support.endswith(f":{bucket}")
    )


def _resolution_family_count(dynamic_paths, prefix: str) -> int:
    return sum(
        1
        for path in dynamic_paths
        for family in path.resolution_families
        if str(family).startswith(prefix)
    )
