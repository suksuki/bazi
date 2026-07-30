from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

DREAM_RETURN_ECHO_VERSION = "v60.dream-return-echo.001"


class DreamReturnEchoJudgment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    choice_label: str = Field(min_length=1)
    summary: str = Field(min_length=1)


class DreamReturnEchoWorldResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    summary: str = Field(min_length=1)
    evidence_summaries: tuple[str, ...] = Field(min_length=1)


class DreamReturnEchoOpenObservation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    summary: str = Field(min_length=1)


class DreamReturnEchoAbuRecap(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    meaning: str = Field(min_length=1)
    boundary: str = Field(min_length=1)
    next_attention: str = Field(min_length=1)


class DreamReturnEchoLineage(BaseModel):
    """Existing Dream records that are allowed to support one return echo."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    question_ref: str = Field(min_length=1)
    episode_ref: str = Field(min_length=1)
    episode_version: int = Field(ge=1)
    answer_seal_ref: str = Field(min_length=1)
    answer_seal_hash: str = Field(min_length=64, max_length=64)
    reveal_ref: str = Field(min_length=1)
    reveal_hash: str = Field(min_length=64, max_length=64)
    world_event_ref: str = Field(min_length=1)
    reconciliation_result: Literal["SUPPORTED", "PARTIAL", "NOT_SUPPORTED"]
    committed_evidence_refs: tuple[str, ...] = Field(min_length=1)
    committed_evidence_hashes: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def evidence_identity_is_ordered_and_complete(
        self,
    ) -> DreamReturnEchoLineage:
        if self.committed_evidence_refs != tuple(
            sorted(set(self.committed_evidence_refs))
        ):
            raise ValueError("dream_return_echo_evidence_refs_not_ordered_unique")
        if len(self.committed_evidence_refs) != len(
            self.committed_evidence_hashes
        ):
            raise ValueError("dream_return_echo_evidence_hash_count_mismatch")
        return self


class DreamReturnEcho(BaseModel):
    """Read-only account-private recap of one departed Dream encounter."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal[
        "v60.dream-return-echo.001"
    ] = DREAM_RETURN_ECHO_VERSION
    echo_ref: str = Field(min_length=1)
    echo_hash: str = Field(min_length=64, max_length=64)
    encounter_ref: str = Field(min_length=1)
    public_alias: str = Field(min_length=1)
    episode_title: str = Field(min_length=1)
    judgment: DreamReturnEchoJudgment
    world_response: DreamReturnEchoWorldResponse
    still_to_observe: DreamReturnEchoOpenObservation
    abu_recap: DreamReturnEchoAbuRecap
    lineage: DreamReturnEchoLineage
    semantics: Literal["DREAM_LIFE_RETURN_ECHO_ONLY"]
    owner_mingli_evidence_allowed: Literal[False]
    dream_outcome_admitted_as_owner_evidence: Literal[False]
    tree_candidate_set_or_order_changed: Literal[False]
    mingli_write_allowed: Literal[False]
    decision_write_allowed: Literal[False]
    knowledge_write_allowed: Literal[False]
    canonical_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_and_sources_are_valid(self) -> DreamReturnEcho:
        if len(self.world_response.evidence_summaries) != len(
            self.lineage.committed_evidence_refs
        ):
            raise ValueError("dream_return_echo_evidence_summary_count_mismatch")
        identity = self.model_dump(
            mode="json",
            exclude={"echo_ref", "echo_hash"},
        )
        if self.echo_hash != content_hash(identity):
            raise ValueError("dream_return_echo_hash_mismatch")
        if self.echo_ref != stable_ref("v60-dream-return-echo", identity):
            raise ValueError("dream_return_echo_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> DreamReturnEcho:
        identity = {
            "contract_version": DREAM_RETURN_ECHO_VERSION,
            **values,
            "semantics": "DREAM_LIFE_RETURN_ECHO_ONLY",
            "owner_mingli_evidence_allowed": False,
            "dream_outcome_admitted_as_owner_evidence": False,
            "tree_candidate_set_or_order_changed": False,
            "mingli_write_allowed": False,
            "decision_write_allowed": False,
            "knowledge_write_allowed": False,
            "canonical_write_allowed": False,
            "read_only": True,
        }
        normalized = cls._normalize(identity)
        return cls(
            echo_ref=stable_ref("v60-dream-return-echo", normalized),
            echo_hash=content_hash(normalized),
            **normalized,
        )

    @staticmethod
    def _normalize(values: dict[str, Any]) -> dict[str, Any]:
        return {
            key: (
                value.model_dump(mode="json")
                if isinstance(value, BaseModel)
                else value
            )
            for key, value in values.items()
        }
