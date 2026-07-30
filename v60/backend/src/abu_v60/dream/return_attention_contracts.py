from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

DREAM_RETURN_ATTENTION_VERSION = "v60.dream-return-attention.001"
DREAM_OPENING_ATTENTION_VERSION = "v60.dream-opening-attention.001"
DREAM_ATTENTION_APPLICATION_VERSION = (
    "v60.dream-opening-attention-application.001"
)


class DreamReturnAttentionOption(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    observation_ref: str = Field(min_length=1)
    kind: Literal["WORLD_RESPONSE", "OUTCOME_EVIDENCE", "OPEN_OBSERVATION"]
    label: str = Field(min_length=1)
    summary: str = Field(min_length=1)


class DreamReturnAttentionSelection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    attention_ref: str = Field(min_length=1)
    attention_hash: str = Field(min_length=64, max_length=64)
    observation_ref: str = Field(min_length=1)
    label: str = Field(min_length=1)
    summary: str = Field(min_length=1)


class DreamReturnAttentionPrompt(BaseModel):
    """Server-owned choices attached to one immutable Grove return echo."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal[
        "v60.dream-return-attention.001"
    ] = DREAM_RETURN_ATTENTION_VERSION
    source_encounter_ref: str = Field(min_length=1)
    source_encounter_version: int = Field(ge=1)
    source_echo_ref: str = Field(min_length=1)
    source_echo_hash: str = Field(min_length=64, max_length=64)
    source_candidate_ref: str = Field(min_length=1)
    source_candidate_hash: str = Field(min_length=64, max_length=64)
    tree_ref: str = Field(min_length=1)
    status: Literal["AWAITING_SELECTION", "SELECTED"]
    options: tuple[DreamReturnAttentionOption, ...] = Field(
        min_length=2,
        max_length=3,
    )
    selection: DreamReturnAttentionSelection | None
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

    @model_validator(mode="after")
    def options_and_selection_are_bound(self) -> DreamReturnAttentionPrompt:
        refs = tuple(option.observation_ref for option in self.options)
        if refs != tuple(dict.fromkeys(refs)):
            raise ValueError("dream_return_attention_options_not_unique")
        for option in self.options:
            identity = {
                "source_echo_ref": self.source_echo_ref,
                "kind": option.kind,
                "label": option.label,
                "summary": option.summary,
            }
            if option.observation_ref != stable_ref(
                "v60-dream-return-observation",
                identity,
            ):
                raise ValueError("dream_return_attention_option_ref_mismatch")
        if self.status == "AWAITING_SELECTION" and self.selection is not None:
            raise ValueError("dream_return_attention_unexpected_selection")
        if self.status == "SELECTED" and self.selection is None:
            raise ValueError("dream_return_attention_selection_missing")
        if self.selection is not None:
            selected = next(
                (
                    option
                    for option in self.options
                    if option.observation_ref == self.selection.observation_ref
                ),
                None,
            )
            if (
                selected is None
                or selected.label != self.selection.label
                or selected.summary != self.selection.summary
            ):
                raise ValueError("dream_return_attention_selection_option_mismatch")
        return self


class DreamReturnAttentionRecord(BaseModel):
    """Append-only account-private selection made through DreamCommandEnvelope."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal[
        "v60.dream-return-attention.001"
    ] = DREAM_RETURN_ATTENTION_VERSION
    attention_ref: str = Field(min_length=1)
    attention_hash: str = Field(min_length=64, max_length=64)
    viewer_account_ref: str = Field(min_length=1)
    source_encounter_ref: str = Field(min_length=1)
    source_encounter_version: int = Field(ge=1)
    source_echo_ref: str = Field(min_length=1)
    source_echo_hash: str = Field(min_length=64, max_length=64)
    source_candidate_ref: str = Field(min_length=1)
    source_candidate_hash: str = Field(min_length=64, max_length=64)
    tree_ref: str = Field(min_length=1)
    observation: DreamReturnAttentionOption
    idempotency_key: str = Field(min_length=1, max_length=180)
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

    @model_validator(mode="after")
    def identity_is_valid(self) -> DreamReturnAttentionRecord:
        observation_identity = {
            "source_echo_ref": self.source_echo_ref,
            "kind": self.observation.kind,
            "label": self.observation.label,
            "summary": self.observation.summary,
        }
        if self.observation.observation_ref != stable_ref(
            "v60-dream-return-observation",
            observation_identity,
        ):
            raise ValueError("dream_return_attention_option_ref_mismatch")
        identity = self.model_dump(
            mode="json",
            exclude={"attention_ref", "attention_hash"},
        )
        if self.attention_hash != content_hash(identity):
            raise ValueError("dream_return_attention_hash_mismatch")
        if self.attention_ref != stable_ref(
            "v60-dream-return-attention",
            identity,
        ):
            raise ValueError("dream_return_attention_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> DreamReturnAttentionRecord:
        identity = {
            "contract_version": DREAM_RETURN_ATTENTION_VERSION,
            **values,
            "semantics": "DREAM_RETURN_ATTENTION_ONLY",
            "evidence_role": "NOT_EVIDENCE",
            "tree_candidate_set_or_order_changed": False,
            "question_changed": False,
            "answer_changed": False,
            "npc_choice_changed": False,
            "outcome_changed": False,
            "mingli_write_allowed": False,
            "decision_write_allowed": False,
            "knowledge_write_allowed": False,
        }
        normalized = {
            key: (
                value.model_dump(mode="json")
                if isinstance(value, BaseModel)
                else value
            )
            for key, value in identity.items()
        }
        return cls(
            attention_ref=stable_ref(
                "v60-dream-return-attention",
                normalized,
            ),
            attention_hash=content_hash(normalized),
            **normalized,
        )

    def public_selection(self) -> DreamReturnAttentionSelection:
        return DreamReturnAttentionSelection(
            attention_ref=self.attention_ref,
            attention_hash=self.attention_hash,
            observation_ref=self.observation.observation_ref,
            label=self.observation.label,
            summary=self.observation.summary,
        )


class DreamReturnAttentionApplication(BaseModel):
    """Immutable proof that a pending attention opened one same-tree Encounter."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal[
        "v60.dream-opening-attention-application.001"
    ] = DREAM_ATTENTION_APPLICATION_VERSION
    application_ref: str = Field(min_length=1)
    application_hash: str = Field(min_length=64, max_length=64)
    viewer_account_ref: str = Field(min_length=1)
    attention_ref: str = Field(min_length=1)
    attention_hash: str = Field(min_length=64, max_length=64)
    encounter_ref: str = Field(min_length=1)
    tree_ref: str = Field(min_length=1)

    @model_validator(mode="after")
    def identity_is_valid(self) -> DreamReturnAttentionApplication:
        identity = self.model_dump(
            mode="json",
            exclude={"application_ref", "application_hash"},
        )
        if self.application_hash != content_hash(identity):
            raise ValueError("dream_opening_attention_application_hash_mismatch")
        if self.application_ref != stable_ref(
            "v60-dream-opening-attention-application",
            identity,
        ):
            raise ValueError("dream_opening_attention_application_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> DreamReturnAttentionApplication:
        identity = {
            "contract_version": DREAM_ATTENTION_APPLICATION_VERSION,
            **values,
        }
        return cls(
            application_ref=stable_ref(
                "v60-dream-opening-attention-application",
                identity,
            ),
            application_hash=content_hash(identity),
            **identity,
        )


class DreamOpeningAttention(BaseModel):
    """Read-only restoration of one selected attention in its next same-tree visit."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal[
        "v60.dream-opening-attention.001"
    ] = DREAM_OPENING_ATTENTION_VERSION
    application_ref: str = Field(min_length=1)
    application_hash: str = Field(min_length=64, max_length=64)
    attention_ref: str = Field(min_length=1)
    attention_hash: str = Field(min_length=64, max_length=64)
    source_echo_ref: str = Field(min_length=1)
    source_tree_ref: str = Field(min_length=1)
    target_tree_ref: str = Field(min_length=1)
    target_encounter_ref: str = Field(min_length=1)
    observation_ref: str = Field(min_length=1)
    label: str = Field(min_length=1)
    summary: str = Field(min_length=1)
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
        application: DreamReturnAttentionApplication,
    ) -> DreamOpeningAttention:
        if (
            application.attention_ref != record.attention_ref
            or application.attention_hash != record.attention_hash
            or application.viewer_account_ref != record.viewer_account_ref
            or application.tree_ref != record.tree_ref
        ):
            raise ValueError("dream_opening_attention_lineage_mismatch")
        return cls(
            application_ref=application.application_ref,
            application_hash=application.application_hash,
            attention_ref=record.attention_ref,
            attention_hash=record.attention_hash,
            source_echo_ref=record.source_echo_ref,
            source_tree_ref=record.tree_ref,
            target_tree_ref=application.tree_ref,
            target_encounter_ref=application.encounter_ref,
            observation_ref=record.observation.observation_ref,
            label=record.observation.label,
            summary=record.observation.summary,
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
