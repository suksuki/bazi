from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from core.contracts.base import V50Model, require_non_empty, require_refs


class MechanismComponentRole(str, Enum):
    SOURCE = "source"
    PATH = "path"
    CONVERTER = "converter"
    BRIDGE = "bridge"
    ANCHOR = "anchor"
    TARGET = "target"
    COUNTER_FORCE = "counter_force"
    STATE_DELTA = "state_delta"


class MechanismCompleteness(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    REFERENCE_ONLY = "reference_only"
    INVALID = "invalid"


class StateDeltaStatus(str, Enum):
    REAL = "real"
    INFERRED = "inferred"
    MISSING = "missing"


class MechanismDomainFit(str, Enum):
    DIRECT = "direct"
    SUPPORTING = "supporting"
    STRUCTURAL_BASELINE = "structural_baseline"
    OUT_OF_SCOPE = "out_of_scope"


class MechanismCandidateRole(str, Enum):
    PRIMARY = "primary"
    SUPPORTING = "supporting"
    ALTERNATIVE = "alternative"
    FALLBACK = "fallback"


class MechanismComponent(V50Model):
    version: str = "v50.mechanism_component.v1"
    component_id: str
    reading_id: str
    role: MechanismComponentRole
    ref: str
    label: str = ""
    position: str = ""
    reason_codes: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _boundary(self) -> "MechanismComponent":
        require_non_empty(self.component_id, "component_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.ref, "ref")
        require_refs(self.evidence_refs, "evidence_refs")
        return self


class MechanismRepresentation(V50Model):
    version: str = "v50.mechanism_representation.v1"
    representation_id: str
    reading_id: str
    mechanism_code: str
    mechanism_label_code: str = ""
    components: list[MechanismComponent] = Field(default_factory=list)
    path_refs: list[str] = Field(default_factory=list)
    state_delta_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    completeness: MechanismCompleteness = MechanismCompleteness.REFERENCE_ONLY
    missing_fields: list[str] = Field(default_factory=list)
    uncertainty: dict[str, Any] = Field(default_factory=dict)
    ast_shape: str = ""
    state_delta_status: StateDeltaStatus = StateDeltaStatus.MISSING
    synthetic_filled_fields: list[str] = Field(default_factory=list)
    hard_filled_fields: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    label_is_presentation_only: bool = True
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "mechanism_representation_is_ast_not_label_or_verdict"

    @model_validator(mode="after")
    def _boundary(self) -> "MechanismRepresentation":
        require_non_empty(self.representation_id, "representation_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.mechanism_code, "mechanism_code")
        require_refs(self.components, "components")
        require_refs(self.path_refs, "path_refs")
        require_refs(self.evidence_refs, "evidence_refs")
        roles = {component.role for component in self.components}
        for required in (
            MechanismComponentRole.SOURCE,
            MechanismComponentRole.PATH,
            MechanismComponentRole.TARGET,
        ):
            if required not in roles:
                raise ValueError(f"MechanismRepresentation requires {required.value} component")
        if not self.label_is_presentation_only:
            raise ValueError("Mechanism label must remain presentation-only")
        if self.completeness == MechanismCompleteness.INVALID:
            raise ValueError("MechanismRepresentation cannot be invalid")
        if self.hard_filled_fields:
            raise ValueError("MechanismRepresentation cannot contain hard_filled_fields")
        if self.synthetic_filled_fields:
            raise ValueError("MechanismRepresentation cannot contain synthetic_filled_fields")
        for component in self.components:
            require_refs(component.evidence_refs, f"{component.role.value} evidence_refs")
        if not self.ast_shape.strip():
            raise ValueError("MechanismRepresentation requires ast_shape")
        if self.state_delta_status == StateDeltaStatus.REAL and not self.state_delta_refs:
            raise ValueError("real state_delta_status requires state_delta_refs")
        if self.state_delta_status == StateDeltaStatus.MISSING and self.completeness == MechanismCompleteness.COMPLETE:
            raise ValueError("complete MechanismRepresentation requires state_delta")
        if self.creates_judgment:
            raise ValueError("MechanismRepresentation cannot create judgment")
        if self.calls_brain:
            raise ValueError("MechanismRepresentation cannot call Brain")
        if self.calls_llm:
            raise ValueError("MechanismRepresentation cannot call LLM")
        return self


class MechanismRecognitionCandidate(V50Model):
    version: str = "v50.mechanism_recognition_candidate.v1"
    candidate_id: str
    reading_id: str
    domain: str
    flow_state_id: str
    mechanism_code: str
    domain_fit: MechanismDomainFit
    candidate_role: MechanismCandidateRole
    structural_evidence_score: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=1)
    representation: MechanismRepresentation
    supporting_evidence_refs: list[str] = Field(default_factory=list)
    counter_evidence_codes: list[str] = Field(default_factory=list)
    selected_by_label: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    creates_judgment: bool = False

    @model_validator(mode="after")
    def _boundary(self) -> "MechanismRecognitionCandidate":
        require_non_empty(self.candidate_id, "mechanism recognition candidate_id")
        require_non_empty(self.reading_id, "mechanism recognition reading_id")
        require_non_empty(self.domain, "mechanism recognition domain")
        require_non_empty(self.flow_state_id, "mechanism recognition flow_state_id")
        require_non_empty(self.mechanism_code, "mechanism recognition mechanism_code")
        require_refs(self.supporting_evidence_refs, "mechanism recognition supporting_evidence_refs")
        if self.representation.reading_id != self.reading_id:
            raise ValueError("MechanismRecognitionCandidate cannot mix readings")
        if self.selected_by_label:
            raise ValueError("Mechanism recognition cannot select by presentation label")
        if self.calls_brain or self.calls_llm or self.creates_judgment:
            raise ValueError("Mechanism recognition is structural evidence, not judgment")
        return self


class MechanismRecognitionResult(V50Model):
    version: str = "v50.mechanism_recognition_result.v1"
    result_id: str
    reading_id: str
    domain: str
    candidates: list[MechanismRecognitionCandidate] = Field(default_factory=list)
    primary_candidate_id: str
    evidence_refs: list[str] = Field(default_factory=list)
    ranking_policy: str = "domain_gate_then_structural_evidence_v1"
    label_authority: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    creates_judgment: bool = False

    @model_validator(mode="after")
    def _boundary(self) -> "MechanismRecognitionResult":
        require_non_empty(self.result_id, "mechanism recognition result_id")
        require_non_empty(self.reading_id, "mechanism recognition reading_id")
        require_non_empty(self.domain, "mechanism recognition domain")
        require_refs(self.candidates, "mechanism recognition candidates")
        require_refs(self.evidence_refs, "mechanism recognition evidence_refs")
        ids = {candidate.candidate_id for candidate in self.candidates}
        if self.primary_candidate_id not in ids:
            raise ValueError("primary mechanism candidate must exist")
        if sum(candidate.candidate_role == MechanismCandidateRole.PRIMARY for candidate in self.candidates) != 1:
            raise ValueError("MechanismRecognitionResult requires exactly one primary")
        if self.label_authority:
            raise ValueError("Mechanism label cannot be ranking authority")
        if self.calls_brain or self.calls_llm or self.creates_judgment:
            raise ValueError("MechanismRecognitionResult cannot create judgment")
        return self
