from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import Field

from core.contracts.base import V50Model
from core.mingli_agent.contracts import MingliCognitiveRecord
from core.mingli_agent.probe import ProbePlan


class HypothesisBelief(V50Model):
    hypothesis_id: str
    initial_status: str
    confidence: str
    strengthen_count: int = 0
    weaken_count: int = 0
    current_direction: Literal["strengthened", "weakened", "unchanged"] = "unchanged"


class AssertionBelief(V50Model):
    assertion_id: str
    strengthen_count: int = 0
    weaken_count: int = 0
    current_direction: Literal["strengthened", "weakened", "unchanged"] = "unchanged"


class HiddenAttributeBelief(V50Model):
    attribute_id: str
    current_state: str = "unknown"
    state_counts: dict[str, int] = Field(default_factory=dict)
    lifecycle: Literal["unknown", "candidate", "supported", "stable", "contradicted", "stale"] = "unknown"
    confidence: Literal["low", "medium", "high"] = "low"
    evidence_ids: list[str] = Field(default_factory=list)
    observed_years: list[int] = Field(default_factory=list)
    last_observed_at: str = ""


class ProbeResponseEvidence(V50Model):
    evidence_id: str = ""
    plan_id: str
    source_probe_id: str = ""
    option_id: str
    option_label: str
    recorded_at: str
    evidence_kind: str = "behavior"
    scenario: str = "recognition"
    domain: str = "whole_chart"
    hidden_attribute_observations: dict[str, str] = Field(default_factory=dict)
    evidence_strength: Literal["weak", "medium", "strong"] = "medium"
    reliability: float = Field(default=0.55, ge=0.0, le=1.0)
    relevance: float = Field(default=0.8, ge=0.0, le=1.0)
    year_value: int | None = None
    event_note: str = ""
    recurrence_count: int | None = None
    hypothesis_updates: dict[str, str] = Field(default_factory=dict)
    assertion_updates: dict[str, str] = Field(default_factory=dict)
    source: Literal["user_reported", "practitioner_reported", "research_observation"] = "user_reported"


class CaseDeliberationSelection(V50Model):
    selection_id: str
    stage_key: str
    stage_id: str
    option_id: str
    action: Literal["select", "support", "challenge", "defer", "research_fork"]
    role_mode: Literal["practitioner", "research"]
    actor_id: str = ""
    domain: str = "whole_chart"
    rationale: str = ""
    selected_at: str
    support_before: int = Field(ge=0, le=100)
    active: bool = True


class CaseDeliberationRevision(V50Model):
    revision_id: str
    selection_id: str = ""
    stage_key: str
    kind: Literal["selection", "undo"] = "selection"
    summary: str
    changed_surfaces: list[str] = Field(default_factory=list)
    unchanged_surfaces: list[str] = Field(default_factory=lambda: [
        "birth_facts",
        "chart_world",
        "global_theory",
        "runtime_rules",
        "confidence_without_evidence",
    ])
    created_at: str


class CaseBeliefState(V50Model):
    """Case-local belief and deliberation state, never product layout state."""

    version: str = "deepbazi.case_belief_state.v1"
    case_id: str
    active_hypothesis_id: str
    hypothesis_beliefs: list[HypothesisBelief]
    assertion_ids: list[str]
    assertion_beliefs: list[AssertionBelief] = Field(default_factory=list)
    hidden_attribute_beliefs: list[HiddenAttributeBelief] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    answered_probe_ids: list[str] = Field(default_factory=list)
    probe_history: list[ProbeResponseEvidence] = Field(default_factory=list)
    deliberation_selections: list[CaseDeliberationSelection] = Field(default_factory=list)
    deliberation_revisions: list[CaseDeliberationRevision] = Field(default_factory=list)
    revision_count: int = 0
    chart_facts_locked: bool = True
    global_update_allowed: bool = False


class ProbeUpdateReceipt(V50Model):
    case_id: str
    plan_id: str
    applied: bool
    updated_hypothesis_ids: list[str]
    updated_assertion_ids: list[str] = Field(default_factory=list)
    updated_hidden_attribute_ids: list[str] = Field(default_factory=list)
    evidence_id: str = ""
    chart_facts_modified: bool = False
    global_policy_modified: bool = False
    theory_modified: bool = False
    message: str


def build_case_belief_state(record: MingliCognitiveRecord) -> CaseBeliefState:
    assertions = [
        *record.cognition.portrait,
        *(
            record.cognition.career.assertions
            if record.cognition.career is not None
            else []
        ),
        *(
            record.cognition.wealth.assertions
            if record.cognition.wealth is not None
            else []
        ),
        *[
            assertion
            for exploration in record.domain_explorations.values()
            for assertion in exploration.reading.assertions
        ],
    ]
    return CaseBeliefState(
        case_id=record.case_id,
        active_hypothesis_id=record.cognition.selected_hypothesis_id,
        hypothesis_beliefs=[
            HypothesisBelief(
                hypothesis_id=item.hypothesis_id,
                initial_status=item.status,
                confidence=item.confidence,
            )
            for item in record.cognition.hypotheses
        ],
        assertion_ids=[item.assertion_id for item in assertions],
        assertion_beliefs=[AssertionBelief(assertion_id=item.assertion_id) for item in assertions],
    )


def apply_probe_response(
    *,
    workspace: CaseBeliefState,
    plan: ProbePlan,
    option_id: str,
    source: Literal["user_reported", "practitioner_reported", "research_observation"] = "user_reported",
    year_value: int | None = None,
    event_note: str = "",
    recurrence_count: int | None = None,
    evidence_id: str | None = None,
    recorded_at: str | None = None,
    persist_legacy_history: bool = True,
) -> tuple[CaseBeliefState, ProbeUpdateReceipt]:
    option = next((item for item in plan.options if item.option_id == option_id), None)
    if option is None:
        raise ValueError("probe_option_not_found")
    resolved_evidence_id = evidence_id or f"evidence-{uuid4().hex[:16]}"
    if resolved_evidence_id in workspace.evidence_refs or plan.source_probe_id in workspace.answered_probe_ids:
        return workspace, ProbeUpdateReceipt(
            case_id=workspace.case_id,
            plan_id=plan.plan_id,
            applied=False,
            updated_hypothesis_ids=[],
            evidence_id=resolved_evidence_id,
            message="这条 Probe 已经记录，本次幂等重放没有再次修改案例。",
        )
    beliefs = []
    updated_ids: list[str] = []
    for belief in workspace.hypothesis_beliefs:
        delta = option.hypothesis_updates.get(belief.hypothesis_id, "unchanged")
        strengthen_count = belief.strengthen_count + (1 if delta == "strengthen" else 0)
        weaken_count = belief.weaken_count + (1 if delta == "weaken" else 0)
        direction: Literal["strengthened", "weakened", "unchanged"] = "unchanged"
        if strengthen_count > weaken_count:
            direction = "strengthened"
        elif weaken_count > strengthen_count:
            direction = "weakened"
        if delta != "unchanged":
            updated_ids.append(belief.hypothesis_id)
        beliefs.append(belief.model_copy(update={
            "strengthen_count": strengthen_count,
            "weaken_count": weaken_count,
            "current_direction": direction,
        }))
    known_assertion_ids = {item.assertion_id for item in workspace.assertion_beliefs}
    source_assertion_beliefs = [
        *workspace.assertion_beliefs,
        *[
            AssertionBelief(assertion_id=assertion_id)
            for assertion_id in plan.target_assertion_ids
            if assertion_id not in known_assertion_ids
        ],
    ]
    assertion_beliefs = []
    updated_assertion_ids: list[str] = []
    for belief in source_assertion_beliefs:
        delta = option.assertion_updates.get(belief.assertion_id, "unchanged")
        strengthen_count = belief.strengthen_count + (1 if delta == "strengthen" else 0)
        weaken_count = belief.weaken_count + (1 if delta == "weaken" else 0)
        direction: Literal["strengthened", "weakened", "unchanged"] = "unchanged"
        if strengthen_count > weaken_count:
            direction = "strengthened"
        elif weaken_count > strengthen_count:
            direction = "weakened"
        if delta != "unchanged":
            updated_assertion_ids.append(belief.assertion_id)
        assertion_beliefs.append(belief.model_copy(update={
            "strengthen_count": strengthen_count,
            "weaken_count": weaken_count,
            "current_direction": direction,
        }))
    resolved_recorded_at = recorded_at or datetime.now(timezone.utc).isoformat()
    evidence = ProbeResponseEvidence(
        evidence_id=resolved_evidence_id,
        plan_id=plan.plan_id,
        source_probe_id=plan.source_probe_id,
        option_id=option.option_id,
        option_label=option.label,
        recorded_at=resolved_recorded_at,
        evidence_kind=plan.evidence_kind,
        scenario=plan.scenario,
        domain=plan.domain.value,
        hidden_attribute_observations=option.hidden_attribute_observations,
        evidence_strength=option.evidence_strength,
        reliability=_evidence_reliability(plan=plan, source=source, year_value=year_value),
        relevance=0.95 if plan.expected_information_gain == "high" else 0.7,
        year_value=year_value,
        event_note=event_note,
        recurrence_count=recurrence_count,
        hypothesis_updates=option.hypothesis_updates,
        assertion_updates=option.assertion_updates,
        source=source,
    )
    history = [*workspace.probe_history, evidence]
    hidden_attribute_beliefs = _update_hidden_attributes(
        existing=workspace.hidden_attribute_beliefs,
        evidence=evidence,
    )
    updated = workspace.model_copy(update={
        "hypothesis_beliefs": beliefs,
        "assertion_beliefs": assertion_beliefs,
        "assertion_ids": list(dict.fromkeys([*workspace.assertion_ids, *plan.target_assertion_ids])),
        "hidden_attribute_beliefs": hidden_attribute_beliefs,
        "evidence_refs": list(dict.fromkeys([*workspace.evidence_refs, evidence.evidence_id])),
        "answered_probe_ids": list(dict.fromkeys([*workspace.answered_probe_ids, plan.source_probe_id])),
        "probe_history": history if persist_legacy_history else workspace.probe_history,
        "revision_count": workspace.revision_count + 1,
    })
    return updated, ProbeUpdateReceipt(
        case_id=workspace.case_id,
        plan_id=plan.plan_id,
        applied=True,
        updated_hypothesis_ids=updated_ids,
        updated_assertion_ids=updated_assertion_ids,
        updated_hidden_attribute_ids=list(option.hidden_attribute_observations),
        evidence_id=evidence.evidence_id,
        message="现实证据已用于修正当前案例理解；原局事实和全局理论没有改变。",
    )


def _update_hidden_attributes(
    *,
    existing: list[HiddenAttributeBelief],
    evidence: ProbeResponseEvidence,
) -> list[HiddenAttributeBelief]:
    beliefs = {item.attribute_id: item for item in existing}
    for attribute_id, state in evidence.hidden_attribute_observations.items():
        current = beliefs.get(attribute_id, HiddenAttributeBelief(attribute_id=attribute_id))
        if state == "mixed_or_uncertain" or evidence.evidence_strength == "weak":
            observed_years = set(current.observed_years)
            if evidence.year_value is not None:
                observed_years.add(evidence.year_value)
            beliefs[attribute_id] = current.model_copy(update={
                "evidence_ids": [*current.evidence_ids, evidence.evidence_id],
                "observed_years": sorted(observed_years),
                "last_observed_at": evidence.recorded_at,
            })
            continue
        counts = dict(current.state_counts)
        counts[state] = counts.get(state, 0) + 1
        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        top_state, top_count = ordered[0]
        second_count = ordered[1][1] if len(ordered) > 1 else 0
        independent_years = set(current.observed_years)
        if evidence.year_value is not None:
            independent_years.add(evidence.year_value)
        lifecycle: Literal["candidate", "supported", "stable", "contradicted"] = "candidate"
        confidence: Literal["low", "medium", "high"] = "low"
        if top_count == second_count:
            lifecycle = "contradicted"
        elif top_count >= 3 and len(independent_years) >= 2:
            lifecycle, confidence = "stable", "high"
        elif top_count >= 2:
            lifecycle, confidence = "supported", "medium"
        beliefs[attribute_id] = current.model_copy(update={
            "current_state": top_state,
            "state_counts": counts,
            "lifecycle": lifecycle,
            "confidence": confidence,
            "evidence_ids": [*current.evidence_ids, evidence.evidence_id],
            "observed_years": sorted(independent_years),
            "last_observed_at": evidence.recorded_at,
        })
    return list(beliefs.values())


def _evidence_reliability(*, plan: ProbePlan, source: str, year_value: int | None) -> float:
    if source == "research_observation":
        return 0.82
    if source == "practitioner_reported":
        return 0.72
    if plan.evidence_kind == "historical_timeline" and year_value is not None:
        return 0.74
    return 0.55
