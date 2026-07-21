from __future__ import annotations

from core.graph.contracts import GraphAnalysisResult, MingliPath, PathExplorationResult
from core.simulation.contracts import MingliState, SimulationReport
from core.state.contracts import FlowState


def build_bazi_flow_states(
    *,
    analysis: GraphAnalysisResult,
    path_result: PathExplorationResult,
    state: MingliState,
    simulation_report: SimulationReport | None = None,
    include_secondary_mechanisms: bool = False,
) -> list[FlowState]:
    """Convert Bazi graph/simulation evidence into Unified State language."""

    _assert_same_reading(analysis.reading_id, path_result.reading_id, state.reading_id)
    if simulation_report is not None:
        _assert_same_reading(analysis.reading_id, simulation_report.reading_id)
    if analysis.graph_id != path_result.graph_id:
        raise ValueError("Bazi FlowState adapter requires matching graph_id")
    if analysis.analysis_id != state.analysis_id:
        raise ValueError("Bazi FlowState adapter requires MingliState from the same analysis")

    active_flows = list(state.active_flows)
    if include_secondary_mechanisms:
        active_flows = _dedupe([*active_flows, *_secondary_active_flows(analysis=analysis, path_result=path_result)])

    flow_states: list[FlowState] = []
    for active_flow in active_flows:
        mechanism = _mechanism_from_flow(active_flow)
        matching_paths = _paths_for_mechanism(path_result.paths, mechanism)
        if not matching_paths and path_result.paths:
            matching_paths = path_result.paths[:1]
        top_nodes = _top_node_refs(
            analysis,
            mechanism=mechanism,
            simulation_report=simulation_report,
            matching_paths=matching_paths,
        )
        evidence_refs = _evidence_refs(
            analysis=analysis,
            path_result=path_result,
            state=state,
            simulation_report=simulation_report,
            matching_paths=matching_paths,
        )
        mechanism_key = f"mechanism.{mechanism}"
        mechanism_score = state.mechanism_scores.get(mechanism_key, 0.0)
        path_score = max((path.path_score for path in matching_paths), default=mechanism_score)
        ablation_sensitivity = _ablation_sensitivity(active_flow, simulation_report)
        confidence = round(max(mechanism_score, min(1.0, (path_score + ablation_sensitivity) / 2)), 3)
        flow_states.append(
            FlowState(
                state_id=f"flow_state:{state.reading_id}:{mechanism}",
                reading_id=state.reading_id,
                mechanism=mechanism,
                path_refs=[path.path_id for path in matching_paths] or [active_flow],
                node_refs=top_nodes,
                mechanism_refs=[mechanism_key],
                output_strength=mechanism_score,
                path_score=path_score,
                ablation_sensitivity=ablation_sensitivity,
                evidence_refs=evidence_refs,
                confidence=confidence,
            )
        )
    return flow_states


def _assert_same_reading(*reading_ids: str) -> None:
    if len(set(reading_ids)) != 1:
        raise ValueError("Bazi FlowState adapter cannot mix readings")


def _mechanism_from_flow(flow_code: str) -> str:
    if flow_code.startswith("flow."):
        flow_code = flow_code.removeprefix("flow.")
    if flow_code.endswith("_potential"):
        return flow_code.removesuffix("_potential")
    return flow_code


def _paths_for_mechanism(paths: list[MingliPath], mechanism: str) -> list[MingliPath]:
    direct = [path for path in paths if mechanism in path.mechanism_hints or f"mechanism.{mechanism}" in path.mechanism_hints]
    if direct:
        return direct
    if mechanism == "branch_relation_movement":
        return [
            path
            for path in paths
            if "mechanism_hint.combination_bridge" in path.mechanism_hints
            or any(relation in {"forms_half_combination", "forms_triple_combination", "clashes", "harmonizes"} for relation in path.relation_types)
        ]
    if mechanism == "officer_pressure":
        return [
            path
            for path in paths
            if "controls" in path.relation_types
            or any("metal" in ref or "geng" in ref or "xin" in ref for ref in path.evidence_refs)
        ]
    if mechanism == "resource_support":
        return [
            path
            for path in paths
            if any("water" in ref or "ren" in ref or "gui" in ref for ref in path.evidence_refs)
        ]
    if mechanism == "element_balance":
        return paths[:5]
    return []


def _secondary_active_flows(*, analysis: GraphAnalysisResult, path_result: PathExplorationResult) -> list[str]:
    flows: list[str] = []
    labels = {metric.label for metric in analysis.node_metrics}
    explanation_codes = {code for metric in analysis.node_metrics for code in metric.explanation_codes}
    relation_types = {relation for path in path_result.paths for relation in path.relation_types}
    mechanism_hints = {hint for path in path_result.paths for hint in path.mechanism_hints}
    if "mechanism_hint.output_controls_pressure" in mechanism_hints:
        flows.append("flow.output_controls_pressure")
    if "mechanism_hint.output_to_wealth" in mechanism_hints:
        flows.append("flow.output_to_wealth_potential")
    if labels & {"庚", "辛", "申", "酉"} and ("controls" in relation_types or "metric.high_single_failure_risk" in explanation_codes):
        flows.append("flow.officer_pressure")
    if labels & {"壬", "癸", "子", "亥"}:
        flows.append("flow.resource_support")
    if relation_types & {"forms_half_combination", "forms_triple_combination", "clashes", "harmonizes"}:
        flows.append("flow.branch_relation_movement")
    if len({metric.label for metric in analysis.node_metrics}) >= 5:
        flows.append("flow.element_balance")
    return flows


def _top_node_refs(
    analysis: GraphAnalysisResult,
    *,
    mechanism: str,
    simulation_report: SimulationReport | None,
    matching_paths: list[MingliPath],
) -> list[str]:
    path_node_ids = [node_id for path in matching_paths for node_id in path.node_ids]
    ranked = simulation_report.ranked_critical_node_ids if simulation_report else analysis.ranked_node_ids
    refs = [node_id for node_id in ranked if node_id in path_node_ids]
    if mechanism == "structural_baseline":
        anchors = [
            metric.node_id
            for metric in analysis.node_metrics
            if metric.position in {"day_stem", "day_branch"}
        ]
        refs = _dedupe([*anchors, *refs])
    if len(refs) < 2:
        refs.extend(node_id for node_id in ranked if node_id not in refs)
    if len(refs) < 2:
        refs.extend(node_id for node_id in path_node_ids if node_id not in refs)
    return refs[:4]


def _ablation_sensitivity(active_flow: str, simulation_report: SimulationReport | None) -> float:
    if simulation_report is None:
        return 0.0
    deltas = [result.state_delta for result in simulation_report.ablation_results if active_flow in result.affected_flows]
    if not deltas:
        deltas = [result.state_delta for result in simulation_report.ablation_results]
    return max(deltas, default=0.0)


def _evidence_refs(
    *,
    analysis: GraphAnalysisResult,
    path_result: PathExplorationResult,
    state: MingliState,
    simulation_report: SimulationReport | None,
    matching_paths: list[MingliPath],
) -> list[str]:
    refs = [analysis.graph_id, analysis.analysis_id, path_result.exploration_id, state.state_id]
    if simulation_report is not None:
        refs.append(simulation_report.report_id)
    for path in matching_paths:
        refs.extend(path.evidence_refs)
        refs.append(path.path_id)
    for metric in analysis.node_metrics[:4]:
        refs.append(metric.metric_id)
    seen: set[str] = set()
    ordered_refs: list[str] = []
    for ref in refs:
        if ref and ref not in seen:
            seen.add(ref)
            ordered_refs.append(ref)
    return ordered_refs


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            output.append(value)
    return output
