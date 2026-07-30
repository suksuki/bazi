from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DreamPhase(StrEnum):
    OBSERVING = "OBSERVING"
    QUESTION_OPEN = "QUESTION_OPEN"
    WAITING_FOR_WORLD = "WAITING_FOR_WORLD"
    REVEAL_READY = "REVEAL_READY"
    REVEALED = "REVEALED"
    COMPLETED = "COMPLETED"


class NarrativeDisclosure(StrEnum):
    BASELINE_ONLY = "BASELINE_ONLY"
    SEALED_NO_OUTCOME = "SEALED_NO_OUTCOME"
    WORLD_COMMITTED_HIDDEN = "WORLD_COMMITTED_HIDDEN"
    OUTCOME_REVEALED = "OUTCOME_REVEALED"


class DreamCommand(StrEnum):
    OBSERVE_EVIDENCE = "OBSERVE_EVIDENCE"
    OBSERVE_STRUCTURE = "OBSERVE_STRUCTURE"
    OPEN_QUESTION = "OPEN_QUESTION"
    SEAL_ANSWER = "SEAL_ANSWER"
    REVEAL = "REVEAL"
    RECONCILE = "RECONCILE"
    CONTINUE_ENCOUNTER = "CONTINUE_ENCOUNTER"
    RETURN_TO_GROVE = "RETURN_TO_GROVE"
    SELECT_NEXT_ATTENTION = "SELECT_NEXT_ATTENTION"


class DreamCommandEnvelope(BaseModel):
    """One optimistic, replay-safe request to the Dream write owner."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    command: DreamCommand
    encounter_ref: str = Field(min_length=1)
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=180)
    target_ref: str | None = None
    choice_id: str | None = None

    @model_validator(mode="after")
    def validate_command_payload(self) -> DreamCommandEnvelope:
        organ_commands = {
            DreamCommand.OBSERVE_EVIDENCE,
            DreamCommand.OBSERVE_STRUCTURE,
            DreamCommand.OPEN_QUESTION,
        }
        if self.command in organ_commands:
            if not self.target_ref or self.choice_id is not None:
                raise ValueError("organ_command_requires_only_target_ref")
        elif self.command is DreamCommand.SEAL_ANSWER:
            if not self.choice_id or self.target_ref is not None:
                raise ValueError("seal_answer_requires_only_choice_id")
        elif self.command is DreamCommand.SELECT_NEXT_ATTENTION:
            if not self.target_ref or self.choice_id is not None:
                raise ValueError(
                    "select_next_attention_requires_only_target_ref"
                )
        elif self.target_ref is not None or self.choice_id is not None:
            raise ValueError("command_does_not_accept_payload")
        return self


class DreamCommandReceipt(BaseModel):
    """Immutable proof that one exact Dream command reached committed state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    receipt_version: Literal["v60.dream-command-receipt.001"]
    command_receipt_ref: str = Field(min_length=1)
    viewer_account_ref: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=180)
    command: DreamCommand
    envelope: DreamCommandEnvelope
    envelope_hash: str = Field(min_length=64, max_length=64)
    result_encounter_ref: str = Field(min_length=1)
    result_version: int = Field(ge=1)
    result_status: DreamPhase
    result_state_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_envelope_binding(self) -> DreamCommandReceipt:
        from abu_v60.provenance import content_hash

        if self.idempotency_key != self.envelope.idempotency_key:
            raise ValueError("dream_command_receipt_idempotency_mismatch")
        if self.command is not self.envelope.command:
            raise ValueError("dream_command_receipt_command_mismatch")
        if content_hash(self.envelope.model_dump(mode="json")) != self.envelope_hash:
            raise ValueError("dream_command_receipt_envelope_hash_mismatch")
        return self


class EpisodeChapter(StrEnum):
    FIRST_VISIT = "FIRST_VISIT"
    RETURN_VISIT = "RETURN_VISIT"


class TreeOrganRole(StrEnum):
    EVIDENCE_LEAF = "EVIDENCE_LEAF"
    STRUCTURE_BRANCH = "STRUCTURE_BRANCH"
    QUESTION_FLOWER = "QUESTION_FLOWER"
    OUTCOME_FRUIT = "OUTCOME_FRUIT"


class TreeOrganDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    organ_ref: str = Field(min_length=1)
    role: TreeOrganRole
    source_refs: tuple[str, ...] = Field(min_length=1)
    label: str = Field(min_length=1)


class QuestionChoiceDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    choice_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    proposition: dict[str, str] = Field(min_length=1)


class OutcomeEvidenceDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_ref: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    atom: dict[str, str] = Field(min_length=1)


class SealedOutcomeDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    outcome_id: str = Field(min_length=1)
    resolved_proposition: dict[str, str] = Field(min_length=1)
    evidence: tuple[OutcomeEvidenceDefinition, ...] = Field(min_length=1)
    actual_event: str = Field(min_length=1)


class ResolutionRuleDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_version: str = Field(min_length=1)
    compare_atoms: tuple[str, ...] = Field(min_length=1)
    baseline_evidence_credit: Literal[False]
    exact_match: Literal["SUPPORTED"]
    mixed_match: Literal["PARTIAL"]
    no_match: Literal["NOT_SUPPORTED"]
    baseline_event_ref: str = Field(min_length=1)
    npc_choice_id: str = Field(min_length=1)
    flower_name: str = Field(min_length=1)
    fruit_name: str = Field(min_length=1)
    theater_scene_ref: str = Field(min_length=1)
    theater_beat: str = Field(min_length=1)
    return_label: str | None = None


class EntryWorldEventContract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_ref: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    caused_by_event_ref: str = Field(min_length=1)
    evidence: tuple[dict[str, Any], ...] = Field(min_length=1)
    actor_state_delta: dict[str, Any]


class EpisodeRuntimeMetadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    baseline_event_ref: str = Field(min_length=1)
    npc_choice_id: str = Field(min_length=1)
    flower_name: str = Field(min_length=1)
    fruit_name: str = Field(min_length=1)
    return_label: str | None = None


class EpisodeNarrativeMoment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    phase: DreamPhase
    content_key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status_line: str = Field(min_length=1)
    theater_beat: str = Field(min_length=1)
    abu_line: str = Field(min_length=1)
    disclosure: NarrativeDisclosure


class EpisodeNarrativeContract(BaseModel):
    """Authored presentation bound to an Episode without owning its outcome."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    narrative_version: Literal["v60.episode-narrative.001"]
    scene_ref: str = Field(min_length=1)
    moments: tuple[EpisodeNarrativeMoment, ...] = Field(min_length=6, max_length=6)

    @model_validator(mode="after")
    def validate_phase_disclosures(self) -> EpisodeNarrativeContract:
        phases = [moment.phase for moment in self.moments]
        if len(phases) != len(set(phases)) or set(phases) != set(DreamPhase):
            raise ValueError("episode_narrative_requires_exactly_one_moment_per_phase")
        expected_disclosures = {
            DreamPhase.OBSERVING: NarrativeDisclosure.BASELINE_ONLY,
            DreamPhase.QUESTION_OPEN: NarrativeDisclosure.BASELINE_ONLY,
            DreamPhase.WAITING_FOR_WORLD: NarrativeDisclosure.SEALED_NO_OUTCOME,
            DreamPhase.REVEAL_READY: NarrativeDisclosure.WORLD_COMMITTED_HIDDEN,
            DreamPhase.REVEALED: NarrativeDisclosure.OUTCOME_REVEALED,
            DreamPhase.COMPLETED: NarrativeDisclosure.OUTCOME_REVEALED,
        }
        if any(moment.disclosure != expected_disclosures[moment.phase] for moment in self.moments):
            raise ValueError("episode_narrative_phase_disclosure_mismatch")
        content_keys = [moment.content_key for moment in self.moments]
        if len(content_keys) != len(set(content_keys)):
            raise ValueError("episode_narrative_content_keys_must_be_unique")
        return self

    def for_phase(self, phase: DreamPhase) -> EpisodeNarrativeMoment:
        return next(moment for moment in self.moments if moment.phase == phase)


class DreamEpisodeContract(BaseModel):
    """Persisted lifecycle contract for one authored Dream episode."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    episode_ref: str = Field(min_length=1)
    episode_version: int = Field(ge=1)
    runtime_status: Literal["ACTIVE", "RETIRED"]
    gameplay_id: Literal["life_tree_question_v1"]
    content_key: str = Field(min_length=1)
    chapter: EpisodeChapter
    entrypoint: bool
    actor_ref: str = Field(min_length=1)
    tree_ref: str = Field(min_length=1)
    question_ref: str = Field(min_length=1)
    baseline_event_ref: str = Field(min_length=1)
    world_event_ref: str = Field(min_length=1)
    cutoff_tick: int = Field(ge=0)
    due_tick: int = Field(gt=0)
    resolution_rule_hash: str = Field(min_length=64, max_length=64)
    runtime_metadata: EpisodeRuntimeMetadata
    narrative: EpisodeNarrativeContract
    continuation_question_ref: str | None = None
    continuation_label: str | None = None
    entry_world_event: EntryWorldEventContract | None = None
    tree_state_on_entry: str | None = None
    tree_state_after_settlement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_lifecycle(self) -> DreamEpisodeContract:
        if self.due_tick <= self.cutoff_tick:
            raise ValueError("episode_due_tick_must_follow_cutoff")
        if self.runtime_metadata.baseline_event_ref != self.baseline_event_ref:
            raise ValueError("episode_runtime_metadata_baseline_mismatch")
        if self.continuation_question_ref == self.question_ref:
            raise ValueError("episode_cannot_continue_to_itself")
        if self.entrypoint and (
            self.entry_world_event is not None or self.tree_state_on_entry is not None
        ):
            raise ValueError("entrypoint_episode_cannot_commit_entry_transition")
        if not self.entrypoint and (
            self.entry_world_event is None or self.tree_state_on_entry is None
        ):
            raise ValueError("continuation_episode_requires_entry_transition")
        if (
            self.entry_world_event is not None
            and self.entry_world_event.event_ref != self.baseline_event_ref
        ):
            raise ValueError("entry_event_must_be_episode_baseline")
        return self


def runtime_metadata_from_resolution_rule(
    resolution_rule: dict[str, Any],
) -> EpisodeRuntimeMetadata:
    return EpisodeRuntimeMetadata.model_validate(
        {
            key: resolution_rule.get(key)
            for key in (
                "baseline_event_ref",
                "npc_choice_id",
                "flower_name",
                "fruit_name",
                "return_label",
            )
        }
    )


def resolution_rule_for_persistence(
    resolution_rule: ResolutionRuleDefinition | Mapping[str, Any],
) -> dict[str, Any]:
    payload = (
        resolution_rule.model_dump(mode="json")
        if isinstance(resolution_rule, ResolutionRuleDefinition)
        else dict(resolution_rule)
    )
    return {
        key: payload[key]
        for key in (
            "rule_version",
            "compare_atoms",
            "baseline_evidence_credit",
            "exact_match",
            "mixed_match",
            "no_match",
        )
    }


class DreamEpisodeDefinition(BaseModel):
    """Authoring package split into safe question data and sealed world outcome."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    runtime: DreamEpisodeContract
    actor_ref: str = Field(min_length=1)
    tree_ref: str = Field(min_length=1)
    question_version: int = Field(ge=1)
    prompt: str = Field(min_length=1)
    options: tuple[QuestionChoiceDefinition, ...] = Field(min_length=2, max_length=4)
    baseline_evidence: tuple[dict[str, Any], ...] = Field(min_length=1)
    resolution_rule: ResolutionRuleDefinition
    sealed_outcome: SealedOutcomeDefinition
    world_event_type: str = Field(min_length=1)
    world_event_summary: str = Field(min_length=1)
    organ_set: dict[str, TreeOrganDefinition]

    @model_validator(mode="after")
    def validate_episode(self) -> DreamEpisodeDefinition:
        if self.runtime.actor_ref != self.actor_ref or self.runtime.tree_ref != self.tree_ref:
            raise ValueError("episode_actor_and_tree_identity_must_match_runtime")
        expected_keys = {
            "evidence_leaf_world",
            "evidence_leaf_structure",
            "structure_branch",
            "question_flower",
            "outcome_fruit",
        }
        if set(self.organ_set) != expected_keys:
            raise ValueError("episode_requires_two_leaves_branch_flower_and_fruit")
        if self.resolution_rule.baseline_event_ref != self.runtime.baseline_event_ref:
            raise ValueError("resolution_baseline_must_match_episode")

        choice_ids = {option.choice_id for option in self.options}
        if len(choice_ids) != len(self.options):
            raise ValueError("episode_choice_ids_must_be_unique")
        if self.resolution_rule.npc_choice_id not in choice_ids:
            raise ValueError("npc_choice_must_reference_episode_option")

        compare_atoms = set(self.resolution_rule.compare_atoms)
        if any(set(option.proposition) != compare_atoms for option in self.options):
            raise ValueError("all_choices_must_compare_the_same_atoms")
        if set(self.sealed_outcome.resolved_proposition) != compare_atoms:
            raise ValueError("sealed_outcome_must_resolve_all_atoms")
        covered_atoms = {
            atom for evidence in self.sealed_outcome.evidence for atom in evidence.atom
        }
        if covered_atoms != compare_atoms:
            raise ValueError("future_evidence_must_cover_all_atoms")
        if any("atom" in evidence for evidence in self.baseline_evidence):
            raise ValueError("baseline_evidence_cannot_contain_outcome_atoms")

        leaf_sources = {
            source_ref
            for key in ("evidence_leaf_world", "evidence_leaf_structure")
            for source_ref in self.organ_set[key].source_refs
        }
        if set(self.organ_set["structure_branch"].source_refs) != leaf_sources:
            raise ValueError("structure_branch_must_depend_on_both_leaves")
        if self.organ_set["question_flower"].source_refs != (self.runtime.question_ref,):
            raise ValueError("question_flower_must_reference_question")
        if self.organ_set["outcome_fruit"].source_refs != (self.runtime.world_event_ref,):
            raise ValueError("outcome_fruit_must_reference_world_event")

        baseline_refs = {
            str(evidence["evidence_ref"])
            for evidence in self.baseline_evidence
            if evidence.get("evidence_ref")
        }
        future_refs = {evidence.evidence_ref for evidence in self.sealed_outcome.evidence}
        if baseline_refs & future_refs:
            raise ValueError("future_evidence_cannot_appear_before_seal")
        pre_reveal_text = " ".join(
            text
            for moment in self.runtime.narrative.moments
            if moment.disclosure
            in {
                NarrativeDisclosure.BASELINE_ONLY,
                NarrativeDisclosure.SEALED_NO_OUTCOME,
                NarrativeDisclosure.WORLD_COMMITTED_HIDDEN,
            }
            for text in (
                moment.title,
                moment.status_line,
                moment.theater_beat,
                moment.abu_line,
            )
        )
        forbidden_outcome_text = (
            self.sealed_outcome.actual_event,
            *(evidence.summary for evidence in self.sealed_outcome.evidence),
        )
        if any(text in pre_reveal_text for text in forbidden_outcome_text):
            raise ValueError("episode_narrative_leaks_future_outcome")
        return self


class EncounterProgress(BaseModel):
    model_config = ConfigDict(frozen=True)

    observed_organs: tuple[str, ...] = ()
    question_visible: bool = False
    answer_sealed: bool = False
    world_settled: bool = False
    revealed: bool = False
    reconciled: bool = False
    departed_to_grove: bool = False

    def as_state_json(self) -> dict[str, object]:
        return {
            "observed_organs": list(self.observed_organs),
            "question_visible": self.question_visible,
            "answer_sealed": self.answer_sealed,
            "world_settled": self.world_settled,
            "revealed": self.revealed,
            "reconciled": self.reconciled,
            "departed_to_grove": self.departed_to_grove,
        }


class GameMutation(BaseModel):
    model_config = ConfigDict(frozen=True)

    phase: DreamPhase
    progress: EncounterProgress


class GameplayScene(BaseModel):
    model_config = ConfigDict(frozen=True)

    gameplay_id: str
    scene_id: str
    scene_version: int
    layout_key: str
    episode_ref: str
    episode_version: int
    content_key: str
    chapter: EpisodeChapter
    phase: DreamPhase
    available_commands: tuple[DreamCommand, ...]
    organs: tuple[dict[str, Any], ...]
    continuation_available: bool
    continuation_label: str | None
