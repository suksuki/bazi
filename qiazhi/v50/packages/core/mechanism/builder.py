from __future__ import annotations

from core.graph.contracts import GraphAnalysisResult, NodeImportanceMetric
from core.mechanism.contracts import (
    MechanismCompleteness,
    MechanismComponent,
    MechanismComponentRole,
    MechanismRepresentation,
    StateDeltaStatus,
)
from core.simulation.contracts import AblationResult, SimulationReport
from core.state.contracts import FlowState


def build_mechanism_representation_from_flow_state(
    *,
    flow_state: FlowState,
    analysis: GraphAnalysisResult,
    simulation_report: SimulationReport | None = None,
) -> MechanismRepresentation:
    """Build a mechanism AST from computational evidence.

    The label is optional presentation. The mechanism itself is represented by
    path, role, critical-node and state-delta components.
    """

    metrics_by_node = {metric.node_id: metric for metric in analysis.node_metrics}
    components: list[MechanismComponent] = []
    components.extend(_path_components(flow_state))
    components.extend(_node_components(flow_state=flow_state, metrics_by_node=metrics_by_node))
    components.extend(_state_delta_components(flow_state=flow_state, simulation_report=simulation_report))
    components = _dedupe_components(components)
    roles = {component.role for component in components}
    state_delta_refs = [component.ref for component in components if component.role == MechanismComponentRole.STATE_DELTA]
    completeness, missing_fields, state_delta_status = _completeness(roles=roles, state_delta_refs=state_delta_refs)
    return MechanismRepresentation(
        representation_id=f"mechanism_representation:{flow_state.reading_id}:{flow_state.mechanism}",
        reading_id=flow_state.reading_id,
        mechanism_code=flow_state.mechanism,
        mechanism_label_code=f"mechanism.label.{flow_state.mechanism}",
        components=components,
        path_refs=list(flow_state.path_refs),
        state_delta_refs=state_delta_refs,
        evidence_refs=_dedupe([*flow_state.evidence_refs, *[ref for component in components for ref in component.evidence_refs]]),
        completeness=completeness,
        missing_fields=missing_fields,
        uncertainty={
            "missing_fields": missing_fields,
            "state_delta_status": state_delta_status.value,
            "source": "path_role_ablation_state_delta",
        },
        ast_shape=_ast_shape(roles),
        state_delta_status=state_delta_status,
        confidence=flow_state.confidence,
    )


def _path_components(flow_state: FlowState) -> list[MechanismComponent]:
    return [
        MechanismComponent(
            component_id=f"mechanism_component:{flow_state.reading_id}:{flow_state.mechanism}:path:{index}",
            reading_id=flow_state.reading_id,
            role=MechanismComponentRole.PATH,
            ref=path_ref,
            reason_codes=["mechanism.path_ref"],
            evidence_refs=[path_ref, *flow_state.evidence_refs[:2]],
            confidence=flow_state.path_score,
        )
        for index, path_ref in enumerate(flow_state.path_refs)
    ]


def _node_components(*, flow_state: FlowState, metrics_by_node: dict[str, NodeImportanceMetric]) -> list[MechanismComponent]:
    components: list[MechanismComponent] = []
    for index, node_ref in enumerate(flow_state.node_refs):
        metric = metrics_by_node.get(node_ref)
        roles = _roles_for_metric(metric=metric, index=index, flow_state=flow_state)
        for role in roles:
            components.append(
                MechanismComponent(
                    component_id=f"mechanism_component:{flow_state.reading_id}:{flow_state.mechanism}:{role.value}:{node_ref}",
                    reading_id=flow_state.reading_id,
                    role=role,
                    ref=node_ref,
                    label=metric.label if metric else "",
                    position=metric.position if metric else "",
                    reason_codes=list(metric.explanation_codes if metric else ["mechanism.node_ref"]),
                    evidence_refs=[*(metric.evidence_refs if metric else []), *flow_state.evidence_refs[:2]],
                    confidence=metric.final_importance if metric else flow_state.confidence,
                )
            )
    if not any(component.role == MechanismComponentRole.SOURCE for component in components) and flow_state.node_refs:
        components.append(_fallback_node_component(flow_state=flow_state, role=MechanismComponentRole.SOURCE, node_ref=flow_state.node_refs[0]))
    if not any(component.role == MechanismComponentRole.TARGET for component in components) and flow_state.node_refs:
        components.append(_fallback_node_component(flow_state=flow_state, role=MechanismComponentRole.TARGET, node_ref=flow_state.node_refs[-1]))
    return components


def _roles_for_metric(*, metric: NodeImportanceMetric | None, index: int, flow_state: FlowState) -> list[MechanismComponentRole]:
    roles: list[MechanismComponentRole] = []
    if index == 0:
        roles.append(MechanismComponentRole.SOURCE)
    if metric is not None:
        codes = set(metric.explanation_codes)
        if "node.is_output_converter" in codes or "role.converter_node" in codes:
            roles.append(MechanismComponentRole.CONVERTER)
        if "node.is_triple_combination_bridge" in codes or "role.bridge_node" in codes:
            roles.append(MechanismComponentRole.BRIDGE)
        if "role.anchor_node" in codes:
            roles.append(MechanismComponentRole.ANCHOR)
        if "metric.high_single_failure_risk" in codes and flow_state.mechanism in {"officer_pressure", "output_controls_pressure"}:
            roles.append(MechanismComponentRole.COUNTER_FORCE)
    if index == len(flow_state.node_refs) - 1:
        roles.append(MechanismComponentRole.TARGET)
    return _dedupe_roles(roles)


def _fallback_node_component(*, flow_state: FlowState, role: MechanismComponentRole, node_ref: str) -> MechanismComponent:
    return MechanismComponent(
        component_id=f"mechanism_component:{flow_state.reading_id}:{flow_state.mechanism}:{role.value}:{node_ref}",
        reading_id=flow_state.reading_id,
        role=role,
        ref=node_ref,
        reason_codes=[f"mechanism.{role.value}.fallback_from_flow_state"],
        evidence_refs=list(flow_state.evidence_refs[:2]),
        confidence=flow_state.confidence,
    )


def _state_delta_components(*, flow_state: FlowState, simulation_report: SimulationReport | None) -> list[MechanismComponent]:
    if simulation_report is None:
        return []
    node_refs = set(flow_state.node_refs)
    path_refs = set(flow_state.path_refs)
    results = [
        result
        for result in simulation_report.ablation_results
        if result.target_node_id in node_refs
        or any(path_ref in result.affected_flows for path_ref in path_refs)
        or f"flow.{flow_state.mechanism}" in result.affected_flows
        or f"mechanism.{flow_state.mechanism}" in result.mechanism_score_delta
    ]
    return [
        MechanismComponent(
            component_id=f"mechanism_component:{flow_state.reading_id}:{flow_state.mechanism}:state_delta:{result.target_node_id}",
            reading_id=flow_state.reading_id,
            role=MechanismComponentRole.STATE_DELTA,
            ref=result.ablation_id,
            label=result.target_label,
            position=result.target_position,
            reason_codes=[*result.explanation_codes, "mechanism.state_delta.from_ablation"],
            evidence_refs=list(result.evidence_refs),
            confidence=result.state_delta,
        )
        for result in results[:3]
    ]


def _dedupe_components(components: list[MechanismComponent]) -> list[MechanismComponent]:
    seen: set[str] = set()
    output: list[MechanismComponent] = []
    for component in components:
        key = component.component_id
        if key in seen:
            continue
        seen.add(key)
        output.append(component)
    return output


def _completeness(
    *,
    roles: set[MechanismComponentRole],
    state_delta_refs: list[str],
) -> tuple[MechanismCompleteness, list[str], StateDeltaStatus]:
    expected = {
        "source": MechanismComponentRole.SOURCE,
        "path": MechanismComponentRole.PATH,
        "target": MechanismComponentRole.TARGET,
        "state_delta": MechanismComponentRole.STATE_DELTA,
    }
    missing = [name for name, role in expected.items() if role not in roles]
    key_roles = {
        MechanismComponentRole.CONVERTER,
        MechanismComponentRole.BRIDGE,
        MechanismComponentRole.ANCHOR,
        MechanismComponentRole.COUNTER_FORCE,
    }
    has_key_role = bool(roles & key_roles)
    if not has_key_role:
        missing.append("key_role")
    state_delta_status = StateDeltaStatus.REAL if state_delta_refs else StateDeltaStatus.MISSING
    if not {MechanismComponentRole.SOURCE, MechanismComponentRole.PATH, MechanismComponentRole.TARGET}.issubset(roles):
        return MechanismCompleteness.REFERENCE_ONLY, sorted(set(missing)), state_delta_status
    if MechanismComponentRole.STATE_DELTA in roles and has_key_role:
        return MechanismCompleteness.COMPLETE, sorted(set(missing)), state_delta_status
    return MechanismCompleteness.PARTIAL, sorted(set(missing)), state_delta_status


def _ast_shape(roles: set[MechanismComponentRole]) -> str:
    ordered = [
        MechanismComponentRole.SOURCE,
        MechanismComponentRole.PATH,
        MechanismComponentRole.CONVERTER,
        MechanismComponentRole.BRIDGE,
        MechanismComponentRole.ANCHOR,
        MechanismComponentRole.TARGET,
        MechanismComponentRole.COUNTER_FORCE,
        MechanismComponentRole.STATE_DELTA,
    ]
    return "+".join(role.value for role in ordered if role in roles)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            output.append(value)
    return output


def _dedupe_roles(values: list[MechanismComponentRole]) -> list[MechanismComponentRole]:
    seen: set[MechanismComponentRole] = set()
    output: list[MechanismComponentRole] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output
