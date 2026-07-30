from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.dream.return_attention_contracts import (
    DreamReturnAttentionApplication,
    DreamReturnAttentionRecord,
)

DREAM_PENDING_ATTENTION_VERSION = "v60.dream-pending-attention.001"
DREAM_ATTENTION_FOLLOW_THROUGH_VERSION = (
    "v60.dream-attention-follow-through.001"
)


class DreamPendingAttention(BaseModel):
    """One oldest unapplied selection that the Grove can make visible."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal[
        "v60.dream-pending-attention.001"
    ] = DREAM_PENDING_ATTENTION_VERSION
    attention_ref: str = Field(min_length=1)
    attention_hash: str = Field(min_length=64, max_length=64)
    source_encounter_ref: str = Field(min_length=1)
    source_encounter_version: int = Field(ge=1)
    source_echo_ref: str = Field(min_length=1)
    source_echo_hash: str = Field(min_length=64, max_length=64)
    source_candidate_ref: str = Field(min_length=1)
    source_candidate_hash: str = Field(min_length=64, max_length=64)
    tree_ref: str = Field(min_length=1)
    observation_ref: str = Field(min_length=1)
    label: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    status: Literal["PENDING_SAME_TREE_RETURN"]
    semantics: Literal["DREAM_RETURN_ATTENTION_ONLY"]
    evidence_role: Literal["NOT_EVIDENCE"]
    tree_candidate_set_or_order_changed: Literal[False]
    question_changed: Literal[False]
    answer_changed: Literal[False]
    npc_choice_changed: Literal[False]
    outcome_changed: Literal[False]
    mingli_write_allowed: Literal[False]
    decision_write_allowed: Literal[False]
    knowledge_write_allowed: Literal[False]
    read_only: Literal[True]

    @classmethod
    def issue(
        cls,
        *,
        record: DreamReturnAttentionRecord,
    ) -> DreamPendingAttention:
        return cls(
            attention_ref=record.attention_ref,
            attention_hash=record.attention_hash,
            source_encounter_ref=record.source_encounter_ref,
            source_encounter_version=record.source_encounter_version,
            source_echo_ref=record.source_echo_ref,
            source_echo_hash=record.source_echo_hash,
            source_candidate_ref=record.source_candidate_ref,
            source_candidate_hash=record.source_candidate_hash,
            tree_ref=record.tree_ref,
            observation_ref=record.observation.observation_ref,
            label=record.observation.label,
            summary=record.observation.summary,
            status="PENDING_SAME_TREE_RETURN",
            semantics="DREAM_RETURN_ATTENTION_ONLY",
            evidence_role="NOT_EVIDENCE",
            tree_candidate_set_or_order_changed=False,
            question_changed=False,
            answer_changed=False,
            npc_choice_changed=False,
            outcome_changed=False,
            mingli_write_allowed=False,
            decision_write_allowed=False,
            knowledge_write_allowed=False,
            read_only=True,
        )


class DreamAttentionProgress(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    required_count: Literal[3]
    observed_count: int = Field(ge=0, le=3)
    required_organ_refs: tuple[str, ...] = Field(min_length=3, max_length=3)
    observed_organ_refs: tuple[str, ...] = Field(max_length=3)

    @model_validator(mode="after")
    def progress_is_an_exact_subset(self) -> DreamAttentionProgress:
        if self.required_organ_refs != tuple(
            dict.fromkeys(self.required_organ_refs)
        ):
            raise ValueError(
                "dream_attention_required_organs_not_unique"
            )
        if self.observed_organ_refs != tuple(
            ref
            for ref in self.required_organ_refs
            if ref in set(self.observed_organ_refs)
        ):
            raise ValueError(
                "dream_attention_observed_organs_not_ordered_subset"
            )
        if self.observed_count != len(self.observed_organ_refs):
            raise ValueError("dream_attention_observed_count_mismatch")
        return self


class DreamAttentionWorldResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    actual_event: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    evidence_summaries: tuple[str, ...] = Field(min_length=1)
    material_count: int = Field(ge=1)

    @model_validator(mode="after")
    def response_material_is_complete(
        self,
    ) -> DreamAttentionWorldResponse:
        if self.evidence_refs != tuple(sorted(set(self.evidence_refs))):
            raise ValueError(
                "dream_attention_response_evidence_not_ordered_unique"
            )
        if (
            self.material_count != len(self.evidence_refs)
            or self.material_count != len(self.evidence_summaries)
        ):
            raise ValueError(
                "dream_attention_response_material_count_mismatch"
            )
        return self


DreamAttentionFollowThroughStatus = Literal[
    "OBSERVING",
    "OBSERVATIONS_COMPLETE",
    "AWAITING_WORLD_RESPONSE",
    "WORLD_RESPONSE_READY_HIDDEN",
    "WORLD_RESPONSE_AVAILABLE",
    "RECONCILED_NOT_EVALUATED",
    "RETURNED_NOT_EVALUATED",
]


class DreamAttentionFollowThrough(BaseModel):
    """Read-only progress and feedback over an already applied selection."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal[
        "v60.dream-attention-follow-through.001"
    ] = DREAM_ATTENTION_FOLLOW_THROUGH_VERSION
    application_ref: str = Field(min_length=1)
    application_hash: str = Field(min_length=64, max_length=64)
    attention_ref: str = Field(min_length=1)
    attention_hash: str = Field(min_length=64, max_length=64)
    source_encounter_ref: str = Field(min_length=1)
    source_encounter_version: int = Field(ge=1)
    source_echo_ref: str = Field(min_length=1)
    source_echo_hash: str = Field(min_length=64, max_length=64)
    source_candidate_ref: str = Field(min_length=1)
    source_candidate_hash: str = Field(min_length=64, max_length=64)
    source_tree_ref: str = Field(min_length=1)
    target_tree_ref: str = Field(min_length=1)
    target_encounter_ref: str = Field(min_length=1)
    observation_ref: str = Field(min_length=1)
    label: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    status: DreamAttentionFollowThroughStatus
    progress: DreamAttentionProgress
    world_response: DreamAttentionWorldResponse | None
    semantic_match_status: Literal[
        "NOT_AVAILABLE_BEFORE_REVEAL",
        "SEMANTIC_MATCH_NOT_EVALUATED",
    ]
    answer_status: Literal["NOT_EVALUATED"]
    semantics: Literal["DREAM_ATTENTION_FOLLOW_THROUGH_ONLY"]
    evidence_role: Literal["NOT_EVIDENCE"]
    tree_candidate_set_or_order_changed: Literal[False]
    question_changed: Literal[False]
    answer_changed: Literal[False]
    npc_choice_changed: Literal[False]
    outcome_changed: Literal[False]
    mingli_write_allowed: Literal[False]
    decision_write_allowed: Literal[False]
    knowledge_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def phase_boundary_is_consistent(
        self,
    ) -> DreamAttentionFollowThrough:
        if self.source_tree_ref != self.target_tree_ref:
            raise ValueError("dream_attention_follow_through_tree_mismatch")
        response_visible = self.status in {
            "WORLD_RESPONSE_AVAILABLE",
            "RECONCILED_NOT_EVALUATED",
            "RETURNED_NOT_EVALUATED",
        }
        if response_visible != (self.world_response is not None):
            raise ValueError(
                "dream_attention_follow_through_response_boundary_mismatch"
            )
        expected_semantics = (
            "SEMANTIC_MATCH_NOT_EVALUATED"
            if response_visible
            else "NOT_AVAILABLE_BEFORE_REVEAL"
        )
        if self.semantic_match_status != expected_semantics:
            raise ValueError(
                "dream_attention_follow_through_semantic_status_mismatch"
            )
        if self.status == "OBSERVING":
            if self.progress.observed_count >= self.progress.required_count:
                raise ValueError(
                    "dream_attention_follow_through_observing_complete"
                )
        elif self.progress.observed_count != self.progress.required_count:
            raise ValueError(
                "dream_attention_follow_through_progress_incomplete"
            )
        return self

    @classmethod
    def issue(
        cls,
        *,
        record: DreamReturnAttentionRecord,
        application: DreamReturnAttentionApplication,
        status: DreamAttentionFollowThroughStatus,
        progress: DreamAttentionProgress,
        world_response: DreamAttentionWorldResponse | None,
    ) -> DreamAttentionFollowThrough:
        if (
            application.viewer_account_ref != record.viewer_account_ref
            or application.attention_ref != record.attention_ref
            or application.attention_hash != record.attention_hash
            or application.tree_ref != record.tree_ref
        ):
            raise ValueError(
                "dream_attention_follow_through_application_mismatch"
            )
        response_visible = world_response is not None
        return cls(
            application_ref=application.application_ref,
            application_hash=application.application_hash,
            attention_ref=record.attention_ref,
            attention_hash=record.attention_hash,
            source_encounter_ref=record.source_encounter_ref,
            source_encounter_version=record.source_encounter_version,
            source_echo_ref=record.source_echo_ref,
            source_echo_hash=record.source_echo_hash,
            source_candidate_ref=record.source_candidate_ref,
            source_candidate_hash=record.source_candidate_hash,
            source_tree_ref=record.tree_ref,
            target_tree_ref=application.tree_ref,
            target_encounter_ref=application.encounter_ref,
            observation_ref=record.observation.observation_ref,
            label=record.observation.label,
            summary=record.observation.summary,
            status=status,
            progress=progress,
            world_response=world_response,
            semantic_match_status=(
                "SEMANTIC_MATCH_NOT_EVALUATED"
                if response_visible
                else "NOT_AVAILABLE_BEFORE_REVEAL"
            ),
            answer_status="NOT_EVALUATED",
            semantics="DREAM_ATTENTION_FOLLOW_THROUGH_ONLY",
            evidence_role="NOT_EVIDENCE",
            tree_candidate_set_or_order_changed=False,
            question_changed=False,
            answer_changed=False,
            npc_choice_changed=False,
            outcome_changed=False,
            mingli_write_allowed=False,
            decision_write_allowed=False,
            knowledge_write_allowed=False,
            read_only=True,
        )
