from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

LIFE_DOMAIN_VECTOR_VERSION = "v60.mingli-life-domain-evidence-vector.001"

LifeDomain = Literal["career", "wealth", "relationship"]
DomainSignalStatus = Literal[
    "TIMING_MECHANISM_OVERLAP",
    "TIMING_AND_MECHANISM_PRESENT",
    "TIMING_ONLY",
    "MECHANISM_ONLY",
    "NO_BOUNDED_EVIDENCE",
]


class LifeDomainObservation(BaseModel):
    """One bounded attention window, never an event or auspiciousness verdict."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    observation_ref: str = Field(min_length=1)
    domain: LifeDomain
    label: str = Field(min_length=1)
    signal_status: DomainSignalStatus
    statement: str = Field(min_length=1)
    observation_prompt: str = Field(min_length=1)
    timing_coordinate_refs: tuple[str, ...]
    mechanism_candidate_refs: tuple[str, ...]
    overlap_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    unresolved_dimensions: tuple[str, ...] = Field(min_length=1)
    outcome_status: Literal["UNRESOLVED"]
    probability_status: Literal["NOT_COMPUTED"]
    professional_verdict_allowed: Literal[False]

    @model_validator(mode="after")
    def identity_and_refs_are_valid(self) -> LifeDomainObservation:
        for values in (
            self.timing_coordinate_refs,
            self.mechanism_candidate_refs,
            self.overlap_refs,
            self.evidence_refs,
            self.unresolved_dimensions,
        ):
            if values != tuple(sorted(set(values))):
                raise ValueError("life_domain_observation_refs_must_be_sorted_unique")
        identity = self.model_dump(mode="json", exclude={"observation_ref"})
        if self.observation_ref != stable_ref(
            "v60-life-domain-observation",
            identity,
        ):
            raise ValueError("life_domain_observation_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> LifeDomainObservation:
        identity = {
            **values,
            "outcome_status": "UNRESOLVED",
            "probability_status": "NOT_COMPUTED",
            "professional_verdict_allowed": False,
        }
        return cls(
            observation_ref=stable_ref("v60-life-domain-observation", identity),
            **identity,
        )


class MingliLifeDomainEvidenceVector(BaseModel):
    """Reproducible domain routing over existing mechanism and timing evidence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    vector_ref: str = Field(min_length=1)
    vector_hash: str = Field(min_length=64, max_length=64)
    vector_version: str = LIFE_DOMAIN_VECTOR_VERSION
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    life_case_revision_ref: str = Field(min_length=1)
    mechanism_vector_ref: str = Field(min_length=1)
    mechanism_vector_hash: str = Field(min_length=64, max_length=64)
    timing_vector_ref: str = Field(min_length=1)
    timing_vector_hash: str = Field(min_length=64, max_length=64)
    policy_ref: str = Field(min_length=1)
    policy_hash: str = Field(min_length=64, max_length=64)
    observations: tuple[LifeDomainObservation, ...] = Field(
        min_length=3,
        max_length=3,
    )
    evidence_semantics: Literal["ATTENTION_WINDOW_ONLY"]
    outcome_status: Literal["UNRESOLVED"]
    probability_status: Literal["NOT_COMPUTED"]
    professional_verdict_allowed: Literal[False]
    canonical_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_and_shape_are_valid(self) -> MingliLifeDomainEvidenceVector:
        if tuple(item.domain for item in self.observations) != (
            "career",
            "wealth",
            "relationship",
        ):
            raise ValueError("life_domain_observation_order_invalid")
        if len({item.observation_ref for item in self.observations}) != 3:
            raise ValueError("life_domain_observation_not_unique")
        identity = self.model_dump(
            mode="json",
            exclude={"vector_ref", "vector_hash"},
        )
        if self.vector_hash != content_hash(identity):
            raise ValueError("life_domain_vector_hash_mismatch")
        if self.vector_ref != stable_ref("v60-mingli-life-domain-vector", identity):
            raise ValueError("life_domain_vector_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliLifeDomainEvidenceVector:
        observations = tuple(
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in values["observations"]
        )
        identity = {
            "vector_version": LIFE_DOMAIN_VECTOR_VERSION,
            **values,
            "observations": observations,
            "evidence_semantics": "ATTENTION_WINDOW_ONLY",
            "outcome_status": "UNRESOLVED",
            "probability_status": "NOT_COMPUTED",
            "professional_verdict_allowed": False,
            "canonical_write_allowed": False,
            "read_only": True,
        }
        return cls(
            vector_ref=stable_ref("v60-mingli-life-domain-vector", identity),
            vector_hash=content_hash(identity),
            **identity,
        )
