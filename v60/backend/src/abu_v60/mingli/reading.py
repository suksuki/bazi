from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.knowledge import KnowledgeAuthority
from abu_v60.mingli.contracts import MingliCandidatePath
from abu_v60.mingli.domain_contracts import MingliLifeDomainEvidenceVector
from abu_v60.mingli.mechanism_contracts import MingliMechanismEvidenceVector
from abu_v60.mingli.quant_contracts import MingliQuantFoundationVector
from abu_v60.mingli.timing_contracts import MingliTimingEvidenceVector
from abu_v60.provenance import content_hash, stable_ref

MINGLI_READING_VERSION = "v60.mingli-reading.005"
TIMING_MINGLI_READING_VERSION = "v60.mingli-reading.004"
MECHANISM_MINGLI_READING_VERSION = "v60.mingli-reading.003"
QUANT_MINGLI_READING_VERSION = "v60.mingli-reading.002"
LEGACY_MINGLI_READING_VERSION = "v60.mingli-reading.001"


class MingliReadingStatus(StrEnum):
    BOUNDED_FACTS_AVAILABLE = "BOUNDED_FACTS_AVAILABLE"
    STRUCTURE_CANDIDATES_UNRESOLVED = "STRUCTURE_CANDIDATES_UNRESOLVED"
    MECHANISM_CANDIDATES_UNRESOLVED = "MECHANISM_CANDIDATES_UNRESOLVED"


class KnowledgeProfileBinding(BaseModel):
    """Exact immutable knowledge identity used by one Reading."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    profile_hash: str = Field(min_length=64, max_length=64)
    governance_status: str = Field(min_length=1)
    runtime_scope: str = Field(min_length=1)
    professionally_reviewed: bool
    source_refs: tuple[str, ...] = Field(min_length=1)

    @property
    def profile_ref(self) -> str:
        return f"{self.profile_id}@{self.profile_version}"


class MingliReadingEnvelope(BaseModel):
    """Reproducible read model shared by Mingli, Abu and Lab."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    reading_version: str = MINGLI_READING_VERSION
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    life_case_revision_ref: str = Field(min_length=1)
    foundation_profile: KnowledgeProfileBinding
    candidate_rule_profile: KnowledgeProfileBinding
    quant_foundation_profile: KnowledgeProfileBinding | None = None
    quant_vector_ref: str | None = None
    quant_vector_hash: str | None = Field(default=None, min_length=64, max_length=64)
    mechanism_evidence_profile: KnowledgeProfileBinding | None = None
    mechanism_vector_ref: str | None = None
    mechanism_vector_hash: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    timing_evidence_profile: KnowledgeProfileBinding | None = None
    timing_vector_ref: str | None = None
    timing_vector_hash: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    life_domain_vector_ref: str | None = None
    life_domain_vector_hash: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    fact_refs: tuple[str, ...] = Field(min_length=1)
    candidate_refs: tuple[str, ...] = ()
    decision_refs: tuple[str, ...] = ()
    unresolved_dimensions: tuple[str, ...] = Field(min_length=1)
    status: MingliReadingStatus
    read_only: bool = True

    @model_validator(mode="after")
    def identity_and_order_are_valid(self) -> MingliReadingEnvelope:
        ordered_groups = (
            self.fact_refs,
            self.candidate_refs,
            self.decision_refs,
            self.unresolved_dimensions,
        )
        if any(values != tuple(sorted(set(values))) for values in ordered_groups):
            raise ValueError("mingli_reading_refs_must_be_unique_and_sorted")
        if not self.read_only:
            raise ValueError("mingli_reading_must_be_read_only")
        quant_fields = (
            self.quant_foundation_profile,
            self.quant_vector_ref,
            self.quant_vector_hash,
        )
        mechanism_fields = (
            self.mechanism_evidence_profile,
            self.mechanism_vector_ref,
            self.mechanism_vector_hash,
        )
        timing_fields = (
            self.timing_evidence_profile,
            self.timing_vector_ref,
            self.timing_vector_hash,
        )
        domain_fields = (
            self.life_domain_vector_ref,
            self.life_domain_vector_hash,
        )
        if self.reading_version == MINGLI_READING_VERSION:
            if any(value is None for value in quant_fields):
                raise ValueError("mingli_reading_v5_requires_quant_foundation")
            if any(value is None for value in mechanism_fields):
                raise ValueError("mingli_reading_v5_requires_mechanism_evidence")
            if any(value is None for value in timing_fields):
                raise ValueError("mingli_reading_v5_requires_timing_evidence")
            if any(value is None for value in domain_fields):
                raise ValueError("mingli_reading_v5_requires_life_domain_evidence")
        elif self.reading_version == TIMING_MINGLI_READING_VERSION:
            if any(value is None for value in quant_fields):
                raise ValueError("mingli_reading_v4_requires_quant_foundation")
            if any(value is None for value in mechanism_fields):
                raise ValueError("mingli_reading_v4_requires_mechanism_evidence")
            if any(value is None for value in timing_fields):
                raise ValueError("mingli_reading_v4_requires_timing_evidence")
            if any(value is not None for value in domain_fields):
                raise ValueError("mingli_reading_v4_cannot_bind_life_domain_evidence")
        elif self.reading_version == MECHANISM_MINGLI_READING_VERSION:
            if any(value is None for value in quant_fields):
                raise ValueError("mingli_reading_v3_requires_quant_foundation")
            if any(value is None for value in mechanism_fields):
                raise ValueError("mingli_reading_v3_requires_mechanism_evidence")
            if any(value is not None for value in (*timing_fields, *domain_fields)):
                raise ValueError("mingli_reading_v3_cannot_bind_timing_evidence")
        elif self.reading_version == QUANT_MINGLI_READING_VERSION:
            if any(value is None for value in quant_fields):
                raise ValueError("mingli_reading_v2_requires_quant_foundation")
            if any(
                value is not None
                for value in (*mechanism_fields, *timing_fields, *domain_fields)
            ):
                raise ValueError("mingli_reading_v2_cannot_bind_mechanism_evidence")
        elif self.reading_version == LEGACY_MINGLI_READING_VERSION:
            if any(
                value is not None
                for value in (
                    *quant_fields,
                    *mechanism_fields,
                    *timing_fields,
                    *domain_fields,
                )
            ):
                raise ValueError("mingli_reading_v1_cannot_bind_quant_foundation")
        else:
            raise ValueError("mingli_reading_version_not_supported")
        excluded = {"reading_ref", "reading_hash"}
        if self.reading_version == TIMING_MINGLI_READING_VERSION:
            excluded.update(
                {
                    "life_domain_vector_ref",
                    "life_domain_vector_hash",
                }
            )
        if self.reading_version == MECHANISM_MINGLI_READING_VERSION:
            excluded.update(
                {
                    "timing_evidence_profile",
                    "timing_vector_ref",
                    "timing_vector_hash",
                    "life_domain_vector_ref",
                    "life_domain_vector_hash",
                }
            )
        if self.reading_version == QUANT_MINGLI_READING_VERSION:
            excluded.update(
                {
                    "mechanism_evidence_profile",
                    "mechanism_vector_ref",
                    "mechanism_vector_hash",
                    "timing_evidence_profile",
                    "timing_vector_ref",
                    "timing_vector_hash",
                    "life_domain_vector_ref",
                    "life_domain_vector_hash",
                }
            )
        if self.reading_version == LEGACY_MINGLI_READING_VERSION:
            excluded.update(
                {
                    "quant_foundation_profile",
                    "quant_vector_ref",
                    "quant_vector_hash",
                    "mechanism_evidence_profile",
                    "mechanism_vector_ref",
                    "mechanism_vector_hash",
                    "timing_evidence_profile",
                    "timing_vector_ref",
                    "timing_vector_hash",
                    "life_domain_vector_ref",
                    "life_domain_vector_hash",
                }
            )
        identity = self.model_dump(mode="json", exclude=excluded)
        if self.reading_hash != content_hash(identity):
            raise ValueError("mingli_reading_hash_mismatch")
        if self.reading_ref != stable_ref("v60-mingli-reading", identity):
            raise ValueError("mingli_reading_ref_mismatch")
        return self

    @classmethod
    def issue(
        cls,
        *,
        reading_version: str = MINGLI_READING_VERSION,
        **values: Any,
    ) -> MingliReadingEnvelope:
        identity = {
            "reading_version": reading_version,
            **values,
            "read_only": True,
        }
        for key in (
            "foundation_profile",
            "candidate_rule_profile",
            "quant_foundation_profile",
            "mechanism_evidence_profile",
            "timing_evidence_profile",
        ):
            profile = identity.get(key)
            if isinstance(profile, BaseModel):
                identity[key] = profile.model_dump(mode="json")
        status = identity["status"]
        if isinstance(status, StrEnum):
            identity["status"] = status.value
        hash_identity = dict(identity)
        if reading_version == TIMING_MINGLI_READING_VERSION:
            for key in (
                "life_domain_vector_ref",
                "life_domain_vector_hash",
            ):
                hash_identity.pop(key, None)
        elif reading_version == MECHANISM_MINGLI_READING_VERSION:
            for key in (
                "timing_evidence_profile",
                "timing_vector_ref",
                "timing_vector_hash",
                "life_domain_vector_ref",
                "life_domain_vector_hash",
            ):
                hash_identity.pop(key, None)
        elif reading_version == QUANT_MINGLI_READING_VERSION:
            for key in (
                "mechanism_evidence_profile",
                "mechanism_vector_ref",
                "mechanism_vector_hash",
                "timing_evidence_profile",
                "timing_vector_ref",
                "timing_vector_hash",
                "life_domain_vector_ref",
                "life_domain_vector_hash",
            ):
                hash_identity.pop(key, None)
        elif reading_version == LEGACY_MINGLI_READING_VERSION:
            for key in (
                "quant_foundation_profile",
                "quant_vector_ref",
                "quant_vector_hash",
                "mechanism_evidence_profile",
                "mechanism_vector_ref",
                "mechanism_vector_hash",
                "timing_evidence_profile",
                "timing_vector_ref",
                "timing_vector_hash",
                "life_domain_vector_ref",
                "life_domain_vector_hash",
            ):
                hash_identity.pop(key, None)
        return cls(
            reading_ref=stable_ref("v60-mingli-reading", hash_identity),
            reading_hash=content_hash(hash_identity),
            **identity,
        )


class MingliReadingProjector:
    """Bind one Case revision to exact Knowledge profiles and evidence refs."""

    def __init__(self, authority: KnowledgeAuthority | None = None) -> None:
        self._authority = authority or KnowledgeAuthority()

    def project(
        self,
        *,
        case_ref: str,
        chart_version_ref: str,
        life_case_revision_ref: str,
        facts: Sequence[Mapping[str, Any]],
        candidates: Sequence[MingliCandidatePath],
        quant_vector: MingliQuantFoundationVector,
        mechanism_vector: MingliMechanismEvidenceVector | None = None,
        timing_vector: MingliTimingEvidenceVector | None = None,
        life_domain_vector: MingliLifeDomainEvidenceVector | None = None,
        decision_refs: Sequence[str] = (),
    ) -> MingliReadingEnvelope:
        foundation = self._authority.active_foundation_profile()
        candidate_profile = self._authority.active_candidate_rule_profile()
        quant_profile = self._authority.active_quant_foundation_profile()
        mechanism_profile = self._authority.active_mechanism_evidence_profile()
        timing_profile = self._authority.active_timing_evidence_profile()
        if mechanism_vector is None:
            from abu_v60.mingli.mechanism import (
                MingliMechanismEvidenceCompiler,
            )

            mechanism_vector = MingliMechanismEvidenceCompiler(self._authority).compile(
                quant_vector=quant_vector,
                facts=facts,
            )
        if any(item.chart_version_ref != chart_version_ref for item in candidates):
            raise ValueError("mingli_reading_candidate_chart_mismatch")
        if quant_vector.case_ref != case_ref or quant_vector.chart_version_ref != chart_version_ref:
            raise ValueError("mingli_reading_quant_vector_lineage_mismatch")
        if (
            quant_vector.quant_profile_ref != quant_profile.source_ref
            or quant_vector.quant_profile_hash != quant_profile.profile_hash
        ):
            raise ValueError("mingli_reading_quant_profile_mismatch")
        if (
            mechanism_vector.case_ref != case_ref
            or mechanism_vector.chart_version_ref != chart_version_ref
            or mechanism_vector.quant_vector_ref != quant_vector.vector_ref
        ):
            raise ValueError("mingli_reading_mechanism_vector_lineage_mismatch")
        if (
            mechanism_vector.mechanism_profile_ref != mechanism_profile.source_ref
            or mechanism_vector.mechanism_profile_hash != mechanism_profile.profile_hash
        ):
            raise ValueError("mingli_reading_mechanism_profile_mismatch")
        if timing_vector is not None:
            if (
                timing_vector.case_ref != case_ref
                or timing_vector.chart_version_ref != chart_version_ref
                or timing_vector.life_case_revision_ref != life_case_revision_ref
            ):
                raise ValueError("mingli_reading_timing_vector_lineage_mismatch")
            if (
                timing_vector.timing_profile_ref != timing_profile.source_ref
                or timing_vector.timing_profile_hash != timing_profile.profile_hash
            ):
                raise ValueError("mingli_reading_timing_profile_mismatch")
        if life_domain_vector is not None:
            if timing_vector is None:
                raise ValueError("mingli_reading_life_domain_requires_timing")
            if (
                life_domain_vector.case_ref != case_ref
                or life_domain_vector.chart_version_ref != chart_version_ref
                or life_domain_vector.life_case_revision_ref
                != life_case_revision_ref
                or life_domain_vector.mechanism_vector_ref
                != mechanism_vector.vector_ref
                or life_domain_vector.timing_vector_ref != timing_vector.vector_ref
            ):
                raise ValueError("mingli_reading_life_domain_lineage_mismatch")

        candidate_refs = tuple(
            sorted(
                {
                    *(item.candidate_ref for item in candidates),
                    *(item.candidate_ref for item in mechanism_vector.candidates),
                }
            )
        )
        unresolved = (
            (
                "mechanism_capacity",
                "professional_admission",
                "relation_effect",
                "time_activation",
                "usability",
            )
            if candidate_refs
            else ("professional_interpretation",)
        )
        return MingliReadingEnvelope.issue(
            reading_version=(
                MINGLI_READING_VERSION
                if life_domain_vector is not None
                else TIMING_MINGLI_READING_VERSION
                if timing_vector is not None
                else MECHANISM_MINGLI_READING_VERSION
            ),
            case_ref=case_ref,
            chart_version_ref=chart_version_ref,
            life_case_revision_ref=life_case_revision_ref,
            foundation_profile=self._binding(foundation),
            candidate_rule_profile=self._binding(candidate_profile),
            quant_foundation_profile=self._binding(quant_profile),
            quant_vector_ref=quant_vector.vector_ref,
            quant_vector_hash=quant_vector.vector_hash,
            mechanism_evidence_profile=self._binding(mechanism_profile),
            mechanism_vector_ref=mechanism_vector.vector_ref,
            mechanism_vector_hash=mechanism_vector.vector_hash,
            timing_evidence_profile=(
                self._binding(timing_profile) if timing_vector is not None else None
            ),
            timing_vector_ref=timing_vector.vector_ref if timing_vector is not None else None,
            timing_vector_hash=timing_vector.vector_hash if timing_vector is not None else None,
            life_domain_vector_ref=(
                life_domain_vector.vector_ref
                if life_domain_vector is not None
                else None
            ),
            life_domain_vector_hash=(
                life_domain_vector.vector_hash
                if life_domain_vector is not None
                else None
            ),
            fact_refs=tuple(sorted(str(item["fact_ref"]) for item in facts)),
            candidate_refs=candidate_refs,
            decision_refs=tuple(sorted(set(decision_refs))),
            unresolved_dimensions=tuple(sorted(unresolved)),
            status=(
                MingliReadingStatus.MECHANISM_CANDIDATES_UNRESOLVED
                if mechanism_vector.candidates
                else MingliReadingStatus.STRUCTURE_CANDIDATES_UNRESOLVED
                if candidates
                else MingliReadingStatus.BOUNDED_FACTS_AVAILABLE
            ),
        )

    @staticmethod
    def _binding(profile: Any) -> KnowledgeProfileBinding:
        return KnowledgeProfileBinding(
            profile_id=profile.profile_id,
            profile_version=profile.profile_version,
            profile_hash=profile.profile_hash,
            governance_status=profile.governance_status,
            runtime_scope=profile.runtime_scope,
            professionally_reviewed=profile.professionally_reviewed,
            source_refs=profile.source_refs,
        )
