from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

MINGLI_EXPLANATION_VERSION = "v60.mingli-explanation.001"


class MingliEvidenceCitation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_ref: str = Field(min_length=1)
    evidence_kind: Literal[
        "DETERMINISTIC_FACT",
        "SOURCE_MANIFESTATION",
        "TIMING_COORDINATE",
        "TIMING_RELATION",
        "TIMING_CANDIDATE_OVERLAP",
        "MECHANISM_CANDIDATE",
        "VERSIONED_VECTOR",
    ]
    summary: str = Field(min_length=1)
    epistemic_status: Literal[
        "CONFIRMED",
        "MEMBERSHIP_ONLY",
        "CANDIDATE_ONLY",
        "COORDINATE_ONLY",
    ]
    source_refs: tuple[str, ...] = Field(min_length=1)


class MingliExplanationClaim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    claim_ref: str = Field(min_length=1)
    claim_kind: Literal[
        "CONFIRMED_FOUNDATION",
        "MECHANISM_CANDIDATE",
        "LIFE_DOMAIN_WINDOW",
    ]
    title: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    epistemic_status: Literal["CONFIRMED", "CANDIDATE", "OBSERVE"]
    decision_basis: Literal[
        "SYSTEM_DETERMINISTIC",
        "VERSIONED_RULE_CANDIDATE",
        "BOUNDED_ATTENTION_COMPARISON",
        "ATTENTION_WINDOW_POLICY",
    ]
    support_evidence: tuple[MingliEvidenceCitation, ...] = Field(min_length=1)
    counter_evidence: tuple[MingliEvidenceCitation, ...] = ()
    counter_evidence_status: Literal["AVAILABLE", "NOT_ADMITTED"]
    unresolved_questions: tuple[str, ...]
    competing_claim_refs: tuple[str, ...] = ()
    source_profile_refs: tuple[str, ...] = Field(min_length=1)
    boundary: str = Field(min_length=1)

    @model_validator(mode="after")
    def refs_are_unique(self) -> MingliExplanationClaim:
        groups = (
            tuple(item.evidence_ref for item in self.support_evidence),
            tuple(item.evidence_ref for item in self.counter_evidence),
            self.unresolved_questions,
            self.competing_claim_refs,
            self.source_profile_refs,
        )
        if any(values != tuple(dict.fromkeys(values)) for values in groups):
            raise ValueError("mingli_explanation_claim_refs_must_be_unique")
        return self


class MingliExplanationEnvelope(BaseModel):
    """One read-only explanation graph derived from a pinned Mingli Reading."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    explanation_ref: str = Field(min_length=1)
    explanation_hash: str = Field(min_length=64, max_length=64)
    explanation_version: str = MINGLI_EXPLANATION_VERSION
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    claims: tuple[MingliExplanationClaim, ...] = Field(min_length=1)
    confirmed_count: int = Field(ge=1)
    candidate_count: int = Field(ge=0)
    observation_count: int = Field(ge=0)
    decision_authority: Literal[
        "SYSTEM_FACTS_ONLY",
        "RULE_ENGINE",
        "LLM_REASONER",
    ]
    decision_meaning: str = Field(min_length=1)
    professional_verdict: Literal[False]
    probability_claim: Literal[False]
    canonical_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_and_counts_are_valid(self) -> MingliExplanationEnvelope:
        claim_refs = tuple(item.claim_ref for item in self.claims)
        if len(claim_refs) != len(set(claim_refs)):
            raise ValueError("mingli_explanation_claim_refs_not_unique")
        expected_counts = {
            "confirmed_count": sum(item.epistemic_status == "CONFIRMED" for item in self.claims),
            "candidate_count": sum(item.epistemic_status == "CANDIDATE" for item in self.claims),
            "observation_count": sum(item.epistemic_status == "OBSERVE" for item in self.claims),
        }
        if any(getattr(self, key) != value for key, value in expected_counts.items()):
            raise ValueError("mingli_explanation_claim_count_mismatch")
        identity = self.model_dump(
            mode="json",
            exclude={"explanation_ref", "explanation_hash"},
        )
        if self.explanation_hash != content_hash(identity):
            raise ValueError("mingli_explanation_hash_mismatch")
        if self.explanation_ref != stable_ref("v60-mingli-explanation", identity):
            raise ValueError("mingli_explanation_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliExplanationEnvelope:
        claims = tuple(
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in values["claims"]
        )
        identity = {
            "explanation_version": MINGLI_EXPLANATION_VERSION,
            **values,
            "claims": claims,
            "professional_verdict": False,
            "probability_claim": False,
            "canonical_write_allowed": False,
            "read_only": True,
        }
        return cls(
            explanation_ref=stable_ref("v60-mingli-explanation", identity),
            explanation_hash=content_hash(identity),
            **identity,
        )
