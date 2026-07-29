from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.game import DreamPhase, NarrativeDisclosure
from abu_v60.provenance import content_hash, stable_ref

EXPERIENCE_CONTEXT_VERSION = "v60.experience-context.003"


class ExperienceContextError(ValueError):
    pass


class ExperienceUnit(StrEnum):
    DREAM = "dream"
    MINGLI = "mingli"
    ABU = "abu"
    THEATER = "theater"
    LAB = "lab"


class ContextSourceKind(StrEnum):
    ENCOUNTER = "ENCOUNTER"
    ACTOR = "ACTOR"
    TREE = "TREE"
    WORLD = "WORLD"
    QUESTION = "QUESTION"
    LIFE_CASE = "LIFE_CASE"
    CHART = "CHART"
    SCENE = "SCENE"
    WORLD_EVENT = "WORLD_EVENT"
    WORLD_EVIDENCE = "WORLD_EVIDENCE"
    MINGLI_FACT = "MINGLI_FACT"
    DECISION = "DECISION"


class ExperienceProgress(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    observed_organs: tuple[str, ...] = ()
    question_visible: bool = False
    answer_sealed: bool = False
    world_settled: bool = False
    revealed: bool = False
    reconciled: bool = False

    @model_validator(mode="after")
    def validate_monotonic_progress(self) -> ExperienceProgress:
        if self.answer_sealed and not self.question_visible:
            raise ValueError("sealed_answer_requires_visible_question")
        if self.world_settled and not self.answer_sealed:
            raise ValueError("settled_world_requires_sealed_answer")
        if self.revealed and not self.world_settled:
            raise ValueError("reveal_requires_settled_world")
        if self.reconciled and not self.revealed:
            raise ValueError("reconciliation_requires_reveal")
        return self


class ExperienceLineage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    encounter_ref: str = Field(min_length=1)
    correlation_id: str = Field(min_length=1)
    causation_id: str = Field(min_length=1)
    actor_ref: str = Field(min_length=1)
    tree_ref: str = Field(min_length=1)
    world_ref: str = Field(min_length=1)
    case_ref: str = Field(min_length=1)
    life_case_revision_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    scene_ref: str = Field(min_length=1)
    question_ref: str = Field(min_length=1)
    world_event_ref: str = Field(min_length=1)


class PublicWorldEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_ref: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    observed_at_tick: int = Field(ge=0)
    epistemic_role: Literal["DECISION_BASELINE_NO_CREDIT"]


class RevealedWorldEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_ref: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    committed_at_tick: int = Field(ge=0)
    epistemic_role: Literal["OUTCOME_EVIDENCE"]


class ExperienceFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    fact_ref: str = Field(min_length=1)
    fact_type: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    object_ref: str | None = None
    authority: str = Field(min_length=1)
    fact_json: dict[str, Any]
    source_ref: str = Field(min_length=1)


class ExperienceStoryContext(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    scene_ref: str = Field(min_length=1)
    phase: DreamPhase
    content_key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status_line: str = Field(min_length=1)
    theater_beat: str = Field(min_length=1)
    abu_line: str = Field(min_length=1)
    disclosure: NarrativeDisclosure


class UnitDisclosure(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    unit: ExperienceUnit
    source_kinds: tuple[ContextSourceKind, ...]
    source_refs: tuple[str, ...]


class ExperienceContextEnvelope(BaseModel):
    """Immutable safe input shared by every product-unit projector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    context_ref: str = Field(min_length=1)
    context_version: Literal["v60.experience-context.003"]
    actor_name: str = Field(min_length=1)
    cutoff_tick: int = Field(ge=0)
    current_tick: int = Field(ge=0)
    lineage: ExperienceLineage
    progress: ExperienceProgress
    story: ExperienceStoryContext
    pillars: dict[str, str]
    facts: tuple[ExperienceFact, ...] = ()
    baseline_evidence: tuple[PublicWorldEvidence, ...] = ()
    revealed_evidence: tuple[RevealedWorldEvidence, ...] = ()
    decision_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_safe_projection_boundary(self) -> ExperienceContextEnvelope:
        if self.current_tick < self.cutoff_tick:
            raise ValueError("world_tick_precedes_question_cutoff")
        if any(evidence.observed_at_tick > self.cutoff_tick for evidence in self.baseline_evidence):
            raise ValueError("post_cutoff_evidence_not_allowed_in_experience_context")
        if self.revealed_evidence and not self.progress.revealed:
            raise ValueError("revealed_evidence_requires_revealed_state")
        if any(
            evidence.committed_at_tick <= self.cutoff_tick for evidence in self.revealed_evidence
        ):
            raise ValueError("revealed_evidence_must_follow_question_cutoff")
        if any(
            evidence.committed_at_tick > self.current_tick for evidence in self.revealed_evidence
        ):
            raise ValueError("revealed_evidence_cannot_follow_current_tick")
        if self.decision_refs and not self.progress.revealed:
            raise ValueError("decision_refs_require_revealed_state")
        expected_phase = (
            DreamPhase.COMPLETED
            if self.progress.reconciled
            else DreamPhase.REVEALED
            if self.progress.revealed
            else DreamPhase.REVEAL_READY
            if self.progress.world_settled
            else DreamPhase.WAITING_FOR_WORLD
            if self.progress.answer_sealed
            else DreamPhase.QUESTION_OPEN
            if self.progress.question_visible
            else DreamPhase.OBSERVING
        )
        if self.story.phase != expected_phase:
            raise ValueError("experience_story_phase_progress_mismatch")
        expected_disclosure = {
            DreamPhase.OBSERVING: NarrativeDisclosure.BASELINE_ONLY,
            DreamPhase.QUESTION_OPEN: NarrativeDisclosure.BASELINE_ONLY,
            DreamPhase.WAITING_FOR_WORLD: NarrativeDisclosure.SEALED_NO_OUTCOME,
            DreamPhase.REVEAL_READY: NarrativeDisclosure.WORLD_COMMITTED_HIDDEN,
            DreamPhase.REVEALED: NarrativeDisclosure.OUTCOME_REVEALED,
            DreamPhase.COMPLETED: NarrativeDisclosure.OUTCOME_REVEALED,
        }[expected_phase]
        if self.story.disclosure != expected_disclosure:
            raise ValueError("experience_story_disclosure_progress_mismatch")
        for values, error in (
            (
                [item.evidence_ref for item in self.baseline_evidence],
                "duplicate_context_evidence_ref",
            ),
            (
                [item.evidence_ref for item in self.revealed_evidence],
                "duplicate_context_revealed_evidence_ref",
            ),
            ([item.fact_ref for item in self.facts], "duplicate_context_fact_ref"),
            (list(self.decision_refs), "duplicate_context_decision_ref"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(error)
        baseline_refs = {item.evidence_ref for item in self.baseline_evidence}
        revealed_refs = {item.evidence_ref for item in self.revealed_evidence}
        if baseline_refs & revealed_refs:
            raise ValueError("baseline_and_revealed_evidence_overlap")
        return self

    @property
    def context_hash(self) -> str:
        return content_hash(self.model_dump(mode="json", exclude={"context_ref"}))

    def disclosure_for(self, unit: ExperienceUnit) -> UnitDisclosure:
        lineage = self.lineage
        baseline_evidence_refs = tuple(item.evidence_ref for item in self.baseline_evidence)
        revealed_evidence_refs = tuple(item.evidence_ref for item in self.revealed_evidence)
        theater_evidence_refs = (
            revealed_evidence_refs if self.progress.revealed else baseline_evidence_refs
        )
        fact_refs = tuple(item.fact_ref for item in self.facts)
        mappings = {
            ExperienceUnit.DREAM: (
                (
                    ContextSourceKind.ENCOUNTER,
                    ContextSourceKind.ACTOR,
                    ContextSourceKind.TREE,
                    ContextSourceKind.WORLD,
                    ContextSourceKind.QUESTION,
                    ContextSourceKind.SCENE,
                    *((ContextSourceKind.WORLD_EVENT,) if self.progress.world_settled else ()),
                    ContextSourceKind.WORLD_EVIDENCE,
                ),
                (
                    lineage.encounter_ref,
                    lineage.actor_ref,
                    lineage.tree_ref,
                    lineage.world_ref,
                    lineage.question_ref,
                    self.story.scene_ref,
                    *((lineage.world_event_ref,) if self.progress.world_settled else ()),
                    *baseline_evidence_refs,
                ),
            ),
            ExperienceUnit.MINGLI: (
                (
                    ContextSourceKind.LIFE_CASE,
                    ContextSourceKind.CHART,
                    ContextSourceKind.MINGLI_FACT,
                ),
                (
                    lineage.life_case_revision_ref,
                    lineage.chart_version_ref,
                    *fact_refs,
                ),
            ),
            ExperienceUnit.ABU: (
                (
                    ContextSourceKind.ENCOUNTER,
                    ContextSourceKind.ACTOR,
                    ContextSourceKind.QUESTION,
                    ContextSourceKind.SCENE,
                ),
                (
                    lineage.encounter_ref,
                    lineage.actor_ref,
                    lineage.question_ref,
                    self.story.scene_ref,
                ),
            ),
            ExperienceUnit.THEATER: (
                (
                    ContextSourceKind.WORLD,
                    ContextSourceKind.QUESTION,
                    ContextSourceKind.SCENE,
                    *((ContextSourceKind.WORLD_EVENT,) if self.progress.world_settled else ()),
                    ContextSourceKind.WORLD_EVIDENCE,
                    *((ContextSourceKind.DECISION,) if self.decision_refs else ()),
                ),
                (
                    lineage.world_ref,
                    lineage.question_ref,
                    self.story.scene_ref,
                    *((lineage.world_event_ref,) if self.progress.world_settled else ()),
                    *theater_evidence_refs,
                    *self.decision_refs,
                ),
            ),
            ExperienceUnit.LAB: (
                (
                    ContextSourceKind.CHART,
                    ContextSourceKind.MINGLI_FACT,
                ),
                (lineage.chart_version_ref, *fact_refs),
            ),
        }
        source_kinds, source_refs = mappings[unit]
        return UnitDisclosure(
            unit=unit,
            source_kinds=source_kinds,
            source_refs=source_refs,
        )

    def public_manifest(self) -> dict[str, Any]:
        return {
            "context_ref": self.context_ref,
            "context_version": self.context_version,
            "context_hash": self.context_hash,
            "cutoff_tick": self.cutoff_tick,
            "current_tick": self.current_tick,
            "source_counts": {
                "baseline_evidence": len(self.baseline_evidence),
                "revealed_evidence": len(self.revealed_evidence),
                "formal_facts": len(self.facts),
                "post_reveal_decisions": len(self.decision_refs),
            },
            "story": {
                "phase": self.story.phase.value,
                "content_key": self.story.content_key,
                "disclosure": self.story.disclosure.value,
            },
            "unit_disclosures": {
                unit.value: self.disclosure_for(unit).model_dump(mode="json")
                for unit in ExperienceUnit
            },
            "sealed_outcome_included": False,
            "hidden_npc_choice_included": False,
        }


def build_experience_context(
    *,
    actor_name: str,
    cutoff_tick: int,
    current_tick: int,
    lineage: Mapping[str, Any],
    progress: Mapping[str, Any],
    narrative_scene_ref: str,
    narrative_moment: Mapping[str, Any],
    pillars: Mapping[str, str],
    facts: Sequence[Mapping[str, Any]],
    baseline_evidence: Sequence[Mapping[str, Any]],
    revealed_evidence: Sequence[Mapping[str, Any]] = (),
    decision_refs: Sequence[str] = (),
) -> ExperienceContextEnvelope:
    normalized_facts = tuple(
        sorted(
            (ExperienceFact.model_validate(dict(item)) for item in facts),
            key=lambda item: item.fact_ref,
        )
    )
    normalized_evidence = tuple(
        sorted(
            (
                PublicWorldEvidence.model_validate(
                    {
                        "evidence_ref": item["evidence_ref"],
                        **dict(item["evidence_json"]),
                    }
                    if "evidence_json" in item
                    else dict(item)
                )
                for item in baseline_evidence
            ),
            key=lambda item: item.evidence_ref,
        )
    )
    normalized_revealed_evidence = tuple(
        sorted(
            (RevealedWorldEvidence.model_validate(dict(item)) for item in revealed_evidence),
            key=lambda item: item.evidence_ref,
        )
    )
    payload = {
        "context_version": EXPERIENCE_CONTEXT_VERSION,
        "actor_name": actor_name,
        "cutoff_tick": cutoff_tick,
        "current_tick": current_tick,
        "lineage": ExperienceLineage.model_validate(dict(lineage)),
        "progress": ExperienceProgress.model_validate(dict(progress)),
        "story": ExperienceStoryContext(
            scene_ref=narrative_scene_ref,
            **dict(narrative_moment),
        ),
        "pillars": dict(pillars),
        "facts": normalized_facts,
        "baseline_evidence": normalized_evidence,
        "revealed_evidence": normalized_revealed_evidence,
        "decision_refs": tuple(sorted(str(item) for item in decision_refs)),
    }
    return ExperienceContextEnvelope(
        context_ref=stable_ref("v60-experience-context", payload),
        **payload,
    )
