from __future__ import annotations

from core.contracts.birth import BirthInputCanonical
from core.engines.bazi.temporal_service import CanonicalTemporalService
from core.engines.bazi.knowledge import BRANCH_ELEMENTS, CONTROLS, GENERATES, SIX_CLASH, SIX_HARMONY, STEM_ELEMENTS
from core.graph.contracts import MingliGraph, MingliGraphNodeType, PathExplorationResult
from core.state.contracts import FlowState, TemporalState
from core.timing.schemas import (
    PersonalTimingAssessment,
    PersonalTimingMaterial,
    TimingEffect,
    TimingInteraction,
    TimingInteractionType,
    TimingLayer,
)


POSITIVE_EFFECTS = {TimingEffect.ACTIVATE, TimingEffect.SUPPORT, TimingEffect.AMPLIFY}
NEGATIVE_EFFECTS = {TimingEffect.SUPPRESS, TimingEffect.CONFLICT}
_TEMPORAL_SERVICE = CanonicalTemporalService()


def build_personal_timing_assessment(
    *,
    reading_id: str,
    birth_input: BirthInputCanonical,
    graph: MingliGraph,
    path_result: PathExplorationResult,
    flow_states: list[FlowState],
    analysis_year: int,
) -> PersonalTimingAssessment:
    material = build_personal_timing_material(
        reading_id=reading_id,
        birth_input=birth_input,
        analysis_year=analysis_year,
    )
    critical_node_refs = _dedupe([ref for flow_state in flow_states for ref in flow_state.node_refs])
    nodes = [node for node in graph.nodes if node.node_id in set(critical_node_refs)]
    interactions: list[TimingInteraction] = []
    if material.luck_pillar:
        interactions.extend(
            _interactions_for_pillar(
                reading_id=reading_id,
                layer=TimingLayer.LUCK,
                pillar=material.luck_pillar,
                nodes=nodes,
                path_result=path_result,
                material=material,
                confidence=0.62,
            )
        )
    interactions.extend(
        _interactions_for_pillar(
            reading_id=reading_id,
            layer=TimingLayer.YEAR,
            pillar=material.annual_pillar,
            nodes=nodes,
            path_result=path_result,
            material=material,
            confidence=0.66,
        )
    )
    activated_paths = _dedupe(
        [
            path_ref
            for interaction in interactions
            if interaction.effect in POSITIVE_EFFECTS
            for path_ref in interaction.target_path_refs
        ]
    )
    weakened_nodes = _dedupe(
        [interaction.target_node_ref for interaction in interactions if interaction.effect in NEGATIVE_EFFECTS]
    )
    shifts = _mechanism_shifts(flow_states=flow_states, interactions=interactions)
    evidence_refs = _dedupe(
        [
            material.material_id,
            "timing.candidate.long_term_field:T001",
            "timing.candidate.year_activation:T006",
            *[interaction.interaction_id for interaction in interactions],
            *[ref for interaction in interactions for ref in interaction.evidence_refs],
        ]
    )
    missing = list(material.missing_inputs)
    if not interactions:
        missing.append("no_direct_timing_interaction_with_critical_nodes")
    confidence_values = [interaction.confidence for interaction in interactions]
    confidence = round(sum(confidence_values) / len(confidence_values), 3) if confidence_values else 0.42
    return PersonalTimingAssessment(
        assessment_id=f"personal_timing:{reading_id}:{analysis_year}",
        reading_id=reading_id,
        material=material,
        interactions=interactions,
        activated_path_refs=activated_paths,
        weakened_node_refs=weakened_nodes,
        mechanism_shifts=shifts,
        evidence_refs=evidence_refs,
        uncertainty={
            "theory_status": "candidate",
            "missing_inputs": _dedupe(missing),
            "interpretation_boundary": "timing_material_is_deterministic_but_path_effect_is_research_candidate",
        },
        confidence=confidence,
    )


def build_personal_timing_material(
    *,
    reading_id: str,
    birth_input: BirthInputCanonical,
    analysis_year: int,
) -> PersonalTimingMaterial:
    resolved_annual_pillar = _TEMPORAL_SERVICE.derive_annual_pillar(analysis_year)
    missing: list[str] = []
    calculation_refs = [
        birth_input.birth_input_id,
        f"calendar.sexagenary_year:{analysis_year}",
    ]
    luck_pillar = ""
    luck_start_year = None
    luck_end_year = None
    luck_start_age = None
    luck_end_age = None
    try:
        timing = _TEMPORAL_SERVICE.resolve_exact_dayun(
            birth_input=birth_input,
            analysis_year=analysis_year,
        )
    except (TypeError, ValueError):
        missing.append("birth_input_not_calendar_resolvable_for_luck")
    else:
        calculation_refs.extend(timing.get("calculation_refs") or [])
        luck_pillar = str(timing.get("luck_pillar") or "")
        luck_range = list(timing.get("luck_year_range") or [])
        luck_age_range = list(timing.get("luck_age_range") or [])
        if len(luck_range) == 2:
            luck_start_year, luck_end_year = luck_range
        if len(luck_age_range) == 2:
            luck_start_age, luck_end_age = luck_age_range
        missing.extend(timing.get("missing_inputs") or [])
    return PersonalTimingMaterial(
        material_id=f"timing_material:{reading_id}:{analysis_year}",
        reading_id=reading_id,
        analysis_year=analysis_year,
        annual_pillar=resolved_annual_pillar,
        luck_pillar=luck_pillar,
        luck_start_year=luck_start_year,
        luck_end_year=luck_end_year,
        luck_start_age=luck_start_age,
        luck_end_age=luck_end_age,
        calculation_refs=_dedupe(calculation_refs),
        missing_inputs=_dedupe(missing),
        confidence=0.94 if luck_pillar else (0.58 if "birth_input_not_calendar_resolvable_for_luck" in missing else 0.82),
    )


def temporal_state_from_personal_timing(
    *,
    assessment: PersonalTimingAssessment,
    primary_flow_state: FlowState,
) -> TemporalState:
    primary_has_conflict = any(
        interaction.effect in NEGATIVE_EFFECTS and interaction.target_node_ref in primary_flow_state.node_refs
        for interaction in assessment.interactions
    )
    return TemporalState(
        state_id=f"temporal_state:{assessment.reading_id}:personal:{assessment.material.analysis_year}",
        reading_id=assessment.reading_id,
        timing_layer="luck_year" if assessment.material.luck_pillar else "year",
        activated_paths=assessment.activated_path_refs,
        weakened_nodes=assessment.weakened_node_refs,
        rerouted_flows=[f"flow.{primary_flow_state.mechanism}.timing_conflict_candidate"] if primary_has_conflict else [],
        mechanism_shifts=assessment.mechanism_shifts,
        state_delta_refs=[assessment.assessment_id],
        evidence_refs=assessment.evidence_refs,
        confidence=assessment.confidence,
    )


def _interactions_for_pillar(
    *,
    reading_id: str,
    layer: TimingLayer,
    pillar: str,
    nodes: list,
    path_result: PathExplorationResult,
    material: PersonalTimingMaterial,
    confidence: float,
) -> list[TimingInteraction]:
    interactions: list[TimingInteraction] = []
    for timing_symbol in pillar:
        for node in nodes:
            relation = _relation(timing_symbol=timing_symbol, target_label=node.label, target_type=node.node_type)
            if relation is None:
                continue
            interaction_type, effect, delta = relation
            path_refs = [path.path_id for path in path_result.paths if node.node_id in path.node_ids]
            interactions.append(
                TimingInteraction(
                    interaction_id=f"timing_interaction:{reading_id}:{layer.value}:{timing_symbol}:{node.node_id}:{interaction_type.value}",
                    reading_id=reading_id,
                    timing_layer=layer,
                    timing_symbol=timing_symbol,
                    timing_pillar=pillar,
                    target_node_ref=node.node_id,
                    target_label=node.label,
                    target_path_refs=path_refs,
                    interaction_type=interaction_type,
                    effect=effect,
                    effect_delta=delta * (1.0 if layer == TimingLayer.LUCK else 0.75),
                    evidence_refs=[material.material_id, *node.evidence_refs, *path_refs[:2]],
                    theory_refs=["T001" if layer == TimingLayer.LUCK else "T006"],
                    confidence=confidence,
                )
            )
    return interactions


def _relation(*, timing_symbol: str, target_label: str, target_type: MingliGraphNodeType):
    timing_is_stem = timing_symbol in STEM_ELEMENTS
    target_is_stem = target_type in {MingliGraphNodeType.STEM, MingliGraphNodeType.HIDDEN_STEM}
    timing_is_branch = timing_symbol in BRANCH_ELEMENTS
    target_is_branch = target_type == MingliGraphNodeType.BRANCH
    if timing_symbol == target_label and ((timing_is_stem and target_is_stem) or (timing_is_branch and target_is_branch)):
        return TimingInteractionType.EXACT, TimingEffect.ACTIVATE, 0.12
    if timing_is_branch and target_is_branch:
        pair = frozenset((timing_symbol, target_label))
        if pair in SIX_CLASH:
            return TimingInteractionType.CLASH, TimingEffect.CONFLICT, -0.12
        if pair in SIX_HARMONY:
            return TimingInteractionType.HARMONY, TimingEffect.SUPPORT, 0.08
    timing_element = STEM_ELEMENTS.get(timing_symbol) or BRANCH_ELEMENTS.get(timing_symbol)
    target_element = STEM_ELEMENTS.get(target_label) or BRANCH_ELEMENTS.get(target_label)
    if not timing_element or not target_element:
        return None
    if timing_element == target_element:
        return TimingInteractionType.SAME_ELEMENT, TimingEffect.AMPLIFY, 0.05
    if GENERATES.get(timing_element) == target_element:
        return TimingInteractionType.GENERATES_TARGET, TimingEffect.SUPPORT, 0.06
    if CONTROLS.get(timing_element) == target_element:
        return TimingInteractionType.CONTROLS_TARGET, TimingEffect.SUPPRESS, -0.08
    if CONTROLS.get(target_element) == timing_element:
        return TimingInteractionType.TARGET_CONTROLS, TimingEffect.RESIST, -0.04
    return None


def _mechanism_shifts(*, flow_states: list[FlowState], interactions: list[TimingInteraction]) -> dict[str, float]:
    shifts: dict[str, float] = {}
    for flow_state in flow_states:
        deltas = [interaction.effect_delta for interaction in interactions if interaction.target_node_ref in flow_state.node_refs]
        if not deltas:
            continue
        shifts[flow_state.mechanism] = round(max(0.0, min(1.0, flow_state.output_strength + sum(deltas))), 3)
    return shifts


def _dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value and value not in output:
            output.append(value)
    return output
