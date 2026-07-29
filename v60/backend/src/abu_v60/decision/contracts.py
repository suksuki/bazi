from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DecisionKind(StrEnum):
    FACT = "FACT"
    POLICY = "POLICY"
    DOMAIN_INFERENCE = "DOMAIN_INFERENCE"
    INTERPRETATION = "INTERPRETATION"
    WORLD_TRANSITION = "WORLD_TRANSITION"
    WORLD_OUTCOME = "WORLD_OUTCOME"
    NPC_INTENT = "NPC_INTENT"
    STORY_PRESENTATION = "STORY_PRESENTATION"
    HUMAN_CONSENT = "HUMAN_CONSENT"
    KNOWLEDGE_PROMOTION = "KNOWLEDGE_PROMOTION"


class DecisionAuthority(StrEnum):
    SYSTEM = "SYSTEM"
    RULE_ENGINE = "RULE_ENGINE"
    LLM_REASONER = "LLM_REASONER"
    HUMAN = "HUMAN"
    OWNER_PROFESSIONAL_REVIEW = "OWNER_PROFESSIONAL_REVIEW"
    NONE = "NONE"


class DecisionRouteStatus(StrEnum):
    RESOLVED = "RESOLVED"
    PENDING = "PENDING"
    UNRESOLVED = "UNRESOLVED"
    DENIED = "DENIED"


class DecisionCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    candidate_ref: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = ()
    qualified: bool = True


class DecisionRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: str = Field(min_length=1)
    decision_kind: DecisionKind
    subject_ref: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = ()
    candidates: tuple[DecisionCandidate, ...] = ()
    deterministic_result: dict[str, Any] | None = None
    llm_allowed: bool = False
    human_required: bool = False
    correlation_id: str = Field(min_length=1)
    causation_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_identity_and_evidence(self) -> DecisionRequest:
        candidate_refs = [candidate.candidate_ref for candidate in self.candidates]
        if len(candidate_refs) != len(set(candidate_refs)):
            raise ValueError("decision_candidate_refs_must_be_unique")
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ValueError("decision_evidence_refs_must_be_unique")
        allowed_evidence = set(self.evidence_refs)
        for candidate in self.candidates:
            if not set(candidate.evidence_refs).issubset(allowed_evidence):
                raise ValueError("candidate_evidence_must_belong_to_request")
        return self


class DecisionRoute(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: str
    status: DecisionRouteStatus
    authority: DecisionAuthority
    selected_candidate_ref: str | None = None
    result: dict[str, Any] | None = None
    reason: str


class DecisionLedgerResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision_id: str = Field(min_length=1)
    route: DecisionRoute
    record_hash: str = Field(min_length=64, max_length=64)
    already_recorded: bool


class GateDisposition(StrEnum):
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"


class DecisionProposal(BaseModel):
    model_config = ConfigDict(frozen=True)

    proposal_ref: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    reasoner_runtime_ref: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    model_ref: str = Field(min_length=1)
    model_profile_ref: str = Field(min_length=1)
    model_profile_hash: str = Field(min_length=64, max_length=64)
    prompt_ref: str = Field(min_length=1)
    provider_response_ref: str = Field(min_length=1)
    context_hash: str = Field(min_length=64, max_length=64)
    selected_candidate_ref: str = Field(min_length=1)
    reviewed_candidate_refs: tuple[str, ...] = Field(min_length=1)
    evidence_refs_used: tuple[str, ...] = Field(min_length=1)
    counter_evidence_refs: tuple[str, ...] = ()
    confidence: float = Field(ge=0.0, le=1.0)
    rationale_summary: str = Field(min_length=1, max_length=1200)

    @model_validator(mode="after")
    def validate_unique_refs(self) -> DecisionProposal:
        ref_groups = (
            self.reviewed_candidate_refs,
            self.evidence_refs_used,
            self.counter_evidence_refs,
        )
        if any(len(refs) != len(set(refs)) for refs in ref_groups):
            raise ValueError("decision_proposal_refs_must_be_unique")
        return self


class EpistemicGateReceipt(BaseModel):
    model_config = ConfigDict(frozen=True)

    receipt_ref: str = Field(min_length=1)
    gate_version: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    proposal_ref: str = Field(min_length=1)
    proposal_hash: str = Field(min_length=64, max_length=64)
    disposition: GateDisposition
    reason: str = Field(min_length=1)
    selected_candidate_ref: str | None = None
    decision_record_allowed: bool = False
    canonical_domain_write_allowed: bool = False
