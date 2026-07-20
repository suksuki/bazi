from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from core.contracts.base import Topic, V50Model, ValidationStatus, require_non_empty, require_refs


class LocalizedClaimRef(V50Model):
    version: str = "v50.localized_claim_ref.v1"
    raw_code: str
    label_key: str
    message_key: str
    display_params: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _boundary(self) -> "LocalizedClaimRef":
        require_non_empty(self.raw_code, "raw_code")
        require_non_empty(self.label_key, "label_key")
        require_non_empty(self.message_key, "message_key")
        return self


class StructureObservation(V50Model):
    version: str = "v50.structure_observation.v1"
    observation_id: str
    reading_id: str
    structure_type: str
    claim: LocalizedClaimRef
    material_refs: list[str] = Field(default_factory=list)
    knowledge_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    validation_status: ValidationStatus = ValidationStatus.UNVALIDATED

    @model_validator(mode="after")
    def _boundary(self) -> "StructureObservation":
        require_non_empty(self.observation_id, "observation_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.structure_type, "structure_type")
        require_refs(self.material_refs, "material_refs")
        return self


class StructureProfileSegment(V50Model):
    version: str = "v50.structure_profile_segment.v1"
    segment_id: str
    reading_id: str
    profile_type: str
    claim: LocalizedClaimRef
    material_refs: list[str] = Field(default_factory=list)
    observation_refs: list[str] = Field(default_factory=list)
    values: dict[str, object] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    final_judgment: bool = False
    user_facing_judgment: bool = False

    @model_validator(mode="after")
    def _boundary(self) -> "StructureProfileSegment":
        require_non_empty(self.segment_id, "segment_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.profile_type, "profile_type")
        require_refs(self.material_refs, "material_refs")
        if self.final_judgment:
            raise ValueError("StructureProfileSegment is not final judgment")
        if self.user_facing_judgment:
            raise ValueError("StructureProfileSegment cannot be user-facing judgment")
        return self


class MingliStructureProfile(V50Model):
    version: str = "v50.mingli_structure_profile.v1"
    profile_id: str
    reading_id: str
    day_master_state: StructureProfileSegment | None = None
    element_balance: StructureProfileSegment | None = None
    ten_god_profile: StructureProfileSegment | None = None
    root_profile: StructureProfileSegment | None = None
    branch_relation_profile: StructureProfileSegment | None = None
    timing_context_profile: StructureProfileSegment | None = None
    ziwei_topic_activation_profile: StructureProfileSegment | None = None
    observation_refs: list[str] = Field(default_factory=list)
    material_refs: list[str] = Field(default_factory=list)
    profile_count: int = Field(default=0, ge=0)
    creates_judgment: bool = False
    calls_brain: bool = False
    llm_used: bool = False
    boundary: str = "structure_profile_organizes_materials_without_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "MingliStructureProfile":
        require_non_empty(self.profile_id, "profile_id")
        require_non_empty(self.reading_id, "reading_id")
        segments = [
            self.day_master_state,
            self.element_balance,
            self.ten_god_profile,
            self.root_profile,
            self.branch_relation_profile,
            self.timing_context_profile,
            self.ziwei_topic_activation_profile,
        ]
        if self.profile_count != len([segment for segment in segments if segment is not None]):
            raise ValueError("profile_count must match populated profile segments")
        if self.creates_judgment:
            raise ValueError("MingliStructureProfile cannot create judgment")
        if self.calls_brain:
            raise ValueError("MingliStructureProfile cannot call Brain")
        if self.llm_used:
            raise ValueError("MingliStructureProfile cannot use LLM")
        return self


class FlowObservation(V50Model):
    version: str = "v50.flow_observation.v1"
    flow_id: str
    reading_id: str
    flow_type: str
    from_node: str
    to_node: str
    claim: LocalizedClaimRef
    structure_refs: list[str] = Field(default_factory=list)
    material_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    validation_status: ValidationStatus = ValidationStatus.UNVALIDATED
    creates_judgment: bool = False
    calls_brain: bool = False
    llm_used: bool = False

    @model_validator(mode="after")
    def _boundary(self) -> "FlowObservation":
        require_non_empty(self.flow_id, "flow_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.flow_type, "flow_type")
        require_non_empty(self.from_node, "from_node")
        require_non_empty(self.to_node, "to_node")
        require_refs(self.structure_refs, "structure_refs")
        require_refs(self.material_refs, "material_refs")
        if self.creates_judgment:
            raise ValueError("FlowObservation cannot create judgment")
        if self.calls_brain:
            raise ValueError("FlowObservation cannot call Brain")
        if self.llm_used:
            raise ValueError("FlowObservation cannot use LLM")
        return self


class JudgmentType(str, Enum):
    TENDENCY = "tendency"
    TIMING = "timing"
    RISK = "risk"
    ADVICE_CANDIDATE = "advice_candidate"


class JudgmentCandidate(V50Model):
    version: str = "v50.judgment_candidate.v1"
    candidate_id: str
    reading_id: str
    topic: Topic = Topic.UNKNOWN
    judgment_type: JudgmentType
    claim: LocalizedClaimRef
    flow_refs: list[str] = Field(default_factory=list)
    structure_refs: list[str] = Field(default_factory=list)
    material_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    must_not_say_checked: bool = False
    validation_status: ValidationStatus = ValidationStatus.UNVALIDATED
    final_verdict: bool = False
    calls_brain: bool = False
    llm_used: bool = False
    user_facing_judgment: bool = False

    @model_validator(mode="after")
    def _boundary(self) -> "JudgmentCandidate":
        require_non_empty(self.candidate_id, "candidate_id")
        require_non_empty(self.reading_id, "reading_id")
        require_refs(self.flow_refs, "flow_refs")
        require_refs(self.structure_refs, "structure_refs")
        require_refs(self.material_refs, "material_refs")
        if self.final_verdict:
            raise ValueError("JudgmentCandidate is not final verdict")
        if self.calls_brain:
            raise ValueError("JudgmentCandidate cannot call Brain")
        if self.llm_used:
            raise ValueError("JudgmentCandidate cannot use LLM")
        if self.user_facing_judgment:
            raise ValueError("JudgmentCandidate is not user-facing judgment")
        return self
