from __future__ import annotations

from core.graph.contracts import GraphAnalysisResult, NodeImportanceMetric
from core.simulation.contracts import AblationResult, MingliState, SimulationReport


def build_mingli_state_from_graph_analysis(analysis: GraphAnalysisResult) -> MingliState:
    active_flows = _detect_active_flows(analysis.node_metrics)
    mechanism_scores = _mechanism_scores(analysis.node_metrics, active_flows)
    return MingliState(
        state_id=f"state:{analysis.reading_id}:original",
        reading_id=analysis.reading_id,
        graph_id=analysis.graph_id,
        analysis_id=analysis.analysis_id,
        policy_version=analysis.policy_version,
        node_metrics=analysis.node_metrics,
        active_flows=active_flows,
        mechanism_scores=mechanism_scores,
        evidence_refs=[analysis.graph_id, analysis.analysis_id],
    )


def run_ablation_simulation(state: MingliState, *, target_node_ids: list[str] | None = None) -> SimulationReport:
    metrics_by_id = {metric.node_id: metric for metric in state.node_metrics}
    targets = target_node_ids or [metric.node_id for metric in state.node_metrics]
    results = [_ablate_metric(state, metrics_by_id[node_id]) for node_id in targets if node_id in metrics_by_id]
    results = sorted(results, key=lambda result: result.state_delta, reverse=True)
    return SimulationReport(
        report_id=f"simulation:{state.reading_id}:ablation_v1",
        reading_id=state.reading_id,
        state_id=state.state_id,
        ablation_results=results,
        ranked_critical_node_ids=[result.target_node_id for result in results],
    )


def _detect_active_flows(metrics: list[NodeImportanceMetric]) -> list[str]:
    labels_by_code = {code for metric in metrics for code in metric.explanation_codes}
    flows: list[str] = []
    if {"node.is_output_converter", "node.is_triple_combination_bridge"}.issubset(labels_by_code):
        flows.append("flow.output_controls_pressure")
    if any(metric.label in {"甲", "乙"} and metric.position == "day_stem" for metric in metrics) and any(
        metric.label in {"戊", "己", "丑", "辰", "未", "戌"} for metric in metrics
    ):
        flows.append("flow.output_to_wealth_potential")
    return flows or ["flow.structural_baseline"]


def _mechanism_scores(metrics: list[NodeImportanceMetric], active_flows: list[str]) -> dict[str, float]:
    by_code = {code: metric for metric in metrics for code in metric.explanation_codes}
    scores: dict[str, float] = {}
    if "flow.output_controls_pressure" in active_flows:
        converter = by_code.get("node.is_output_converter")
        bridge = by_code.get("node.is_triple_combination_bridge")
        if converter and bridge:
            scores["mechanism.output_controls_pressure"] = round((converter.final_importance + bridge.final_importance) / 2, 3)
    if "flow.output_to_wealth_potential" in active_flows:
        scores["mechanism.output_to_wealth"] = 0.52
    return scores or {"mechanism.structural_baseline": 0.4}


def _ablate_metric(state: MingliState, metric: NodeImportanceMetric) -> AblationResult:
    state_delta = _state_delta(metric)
    affected_flows = _affected_flows(metric, state.active_flows)
    mechanism_delta = _mechanism_delta(metric, state.mechanism_scores)
    return AblationResult(
        ablation_id=f"ablation:{state.reading_id}:{metric.node_id}",
        reading_id=state.reading_id,
        state_id=state.state_id,
        target_node_id=metric.node_id,
        target_label=metric.label,
        target_position=metric.position,
        state_delta=state_delta,
        affected_flows=affected_flows,
        mechanism_score_delta=mechanism_delta,
        explanation_codes=[*metric.explanation_codes, "simulation.remove_node.counterfactual"],
        evidence_refs=[state.state_id, metric.metric_id, *metric.evidence_refs],
    )


def _state_delta(metric: NodeImportanceMetric) -> float:
    structural_risk = max(metric.final_importance, metric.criticality_score, metric.bridge_score)
    if "node.is_triple_combination_bridge" in metric.explanation_codes:
        structural_risk = max(structural_risk, 0.91)
    if "node.is_output_converter" in metric.explanation_codes:
        structural_risk = max(structural_risk, 0.87)
    if "node.is_month_environment" in metric.explanation_codes:
        structural_risk = max(structural_risk, 0.73)
    return round(min(1.0, structural_risk), 3)


def _affected_flows(metric: NodeImportanceMetric, active_flows: list[str]) -> list[str]:
    if "node.is_triple_combination_bridge" in metric.explanation_codes:
        return [flow for flow in active_flows if flow == "flow.output_controls_pressure"] or active_flows
    if "node.is_output_converter" in metric.explanation_codes:
        return [flow for flow in active_flows if flow == "flow.output_controls_pressure"] or active_flows
    if "node.is_month_environment" in metric.explanation_codes:
        return active_flows
    return ["flow.local_structure"]


def _mechanism_delta(metric: NodeImportanceMetric, mechanism_scores: dict[str, float]) -> dict[str, float]:
    deltas: dict[str, float] = {}
    for mechanism, score in mechanism_scores.items():
        multiplier = 0.35
        if "node.is_triple_combination_bridge" in metric.explanation_codes:
            multiplier = 0.62
        elif "node.is_output_converter" in metric.explanation_codes:
            multiplier = 0.56
        elif "node.is_month_environment" in metric.explanation_codes:
            multiplier = 0.42
        deltas[mechanism] = round(-score * multiplier, 3)
    return deltas
