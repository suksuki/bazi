from __future__ import annotations

from statistics import fmean

from core.contracts.base import Topic
from core.graph.contracts import GraphAnalysisResult
from core.mechanism.builder import build_mechanism_representation_from_flow_state
from core.mechanism.contracts import (
    MechanismCandidateRole,
    MechanismDomainFit,
    MechanismRecognitionCandidate,
    MechanismRecognitionResult,
)
from core.simulation.contracts import SimulationReport
from core.state.contracts import FlowState


DIRECT_FIT: dict[Topic, set[str]] = {
    Topic.CAREER: {
        "output_controls_pressure",
        "officer_pressure",
        "resource_support",
    },
    Topic.WEALTH: {
        "output_to_wealth",
        "peer_competes_for_wealth",
    },
}

SUPPORTING_FIT: dict[Topic, set[str]] = {
    Topic.CAREER: {"branch_relation_movement", "output_to_wealth", "peer_competes_for_wealth"},
    Topic.WEALTH: {"branch_relation_movement", "output_controls_pressure", "officer_pressure", "resource_support"},
}


def recognize_mechanism_candidates(
    *,
    flow_states: list[FlowState],
    analysis: GraphAnalysisResult,
    simulation_report: SimulationReport | None,
    domain: Topic,
) -> MechanismRecognitionResult:
    if not flow_states:
        raise ValueError("Mechanism recognition requires FlowState candidates")
    if domain not in {Topic.CAREER, Topic.WEALTH}:
        raise ValueError("Mechanism recognition v1 supports career / wealth")

    rows: list[tuple[FlowState, MechanismDomainFit, float, object, list[str]]] = []
    for flow_state in flow_states:
        representation = build_mechanism_representation_from_flow_state(
            flow_state=flow_state,
            analysis=analysis,
            simulation_report=simulation_report,
        )
        fit = _domain_fit(domain=domain, mechanism_code=flow_state.mechanism)
        evidence_score = round(
            fmean(
                [
                    flow_state.output_strength,
                    flow_state.path_score,
                    flow_state.ablation_sensitivity,
                    flow_state.confidence,
                ]
            ),
            3,
        )
        counter = _counter_evidence(flow_state=flow_state, fit=fit, missing_fields=representation.missing_fields)
        rows.append((flow_state, fit, evidence_score, representation, counter))

    rows.sort(key=lambda row: (_fit_order(row[1]), row[2], row[0].confidence, row[0].mechanism), reverse=True)
    primary_index = _primary_index(rows)
    candidates: list[MechanismRecognitionCandidate] = []
    for index, (flow_state, fit, evidence_score, representation, counter) in enumerate(rows):
        role = _candidate_role(index=index, primary_index=primary_index, fit=fit)
        if index != primary_index:
            counter = [*counter, f"competes_with:{rows[primary_index][0].mechanism}"]
        candidates.append(
            MechanismRecognitionCandidate(
                candidate_id=f"mechanism_candidate:{flow_state.reading_id}:{domain.value}:{flow_state.mechanism}",
                reading_id=flow_state.reading_id,
                domain=domain.value,
                flow_state_id=flow_state.state_id,
                mechanism_code=flow_state.mechanism,
                domain_fit=fit,
                candidate_role=role,
                structural_evidence_score=evidence_score,
                rank=index + 1,
                representation=representation,
                supporting_evidence_refs=_dedupe([*flow_state.evidence_refs, *representation.evidence_refs]),
                counter_evidence_codes=_dedupe(counter),
            )
        )

    primary = candidates[primary_index]
    return MechanismRecognitionResult(
        result_id=f"mechanism_recognition:{analysis.reading_id}:{domain.value}",
        reading_id=analysis.reading_id,
        domain=domain.value,
        candidates=candidates,
        primary_candidate_id=primary.candidate_id,
        evidence_refs=_dedupe([ref for candidate in candidates for ref in candidate.supporting_evidence_refs]),
    )


def _domain_fit(*, domain: Topic, mechanism_code: str) -> MechanismDomainFit:
    if mechanism_code in DIRECT_FIT[domain]:
        return MechanismDomainFit.DIRECT
    if mechanism_code in SUPPORTING_FIT[domain]:
        return MechanismDomainFit.SUPPORTING
    if mechanism_code == "element_balance":
        return MechanismDomainFit.STRUCTURAL_BASELINE
    return MechanismDomainFit.OUT_OF_SCOPE


def _fit_order(fit: MechanismDomainFit) -> int:
    return {
        MechanismDomainFit.DIRECT: 3,
        MechanismDomainFit.SUPPORTING: 2,
        MechanismDomainFit.STRUCTURAL_BASELINE: 1,
        MechanismDomainFit.OUT_OF_SCOPE: 0,
    }[fit]


def _primary_index(rows: list[tuple[FlowState, MechanismDomainFit, float, object, list[str]]]) -> int:
    for index, row in enumerate(rows):
        if row[1] in {MechanismDomainFit.DIRECT, MechanismDomainFit.SUPPORTING}:
            return index
    return 0


def _candidate_role(*, index: int, primary_index: int, fit: MechanismDomainFit) -> MechanismCandidateRole:
    if index == primary_index:
        return MechanismCandidateRole.PRIMARY
    if fit == MechanismDomainFit.SUPPORTING:
        return MechanismCandidateRole.SUPPORTING
    if fit in {MechanismDomainFit.STRUCTURAL_BASELINE, MechanismDomainFit.OUT_OF_SCOPE}:
        return MechanismCandidateRole.FALLBACK
    return MechanismCandidateRole.ALTERNATIVE


def _counter_evidence(*, flow_state: FlowState, fit: MechanismDomainFit, missing_fields: list[str]) -> list[str]:
    counter: list[str] = []
    if fit == MechanismDomainFit.SUPPORTING:
        counter.append("domain_fit:supporting_not_primary_by_itself")
    elif fit == MechanismDomainFit.STRUCTURAL_BASELINE:
        counter.append("domain_fit:structural_baseline_not_domain_mechanism")
    elif fit == MechanismDomainFit.OUT_OF_SCOPE:
        counter.append("domain_fit:out_of_scope")
    if flow_state.output_strength < 0.45:
        counter.append("evidence:low_output_strength")
    if flow_state.path_score < 0.5:
        counter.append("evidence:low_path_score")
    if flow_state.ablation_sensitivity < 0.45:
        counter.append("evidence:low_ablation_sensitivity")
    counter.extend(f"ast_missing:{field}" for field in missing_fields)
    return counter


def _dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value and value not in output:
            output.append(value)
    return output
