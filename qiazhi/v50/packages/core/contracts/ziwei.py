from __future__ import annotations

from pydantic import Field, model_validator

from core.contracts.base import Topic, V50Model, require_non_empty, require_refs
from core.contracts.material import UnifiedMingliMaterialStore


class ZiweiPalaceInput(V50Model):
    version: str = "v50.ziwei_palace_input.v1"
    palace_name: str
    branch: str = ""
    major_stars: list[str] = Field(default_factory=list)
    support_stars: list[str] = Field(default_factory=list)
    malefic_stars: list[str] = Field(default_factory=list)
    transformations: dict[str, str] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _identity(self) -> "ZiweiPalaceInput":
        require_non_empty(self.palace_name, "palace_name")
        return self


class ZiweiPlateInput(V50Model):
    version: str = "v50.ziwei_plate_input.v1"
    plate_input_id: str
    birth_input_id: str
    source: str = "explicit_ziwei_plate"
    life_palace: str = ""
    body_palace: str = ""
    palaces: dict[str, ZiweiPalaceInput] = Field(default_factory=dict)
    four_transformations: dict[str, str] = Field(default_factory=dict)
    decade_palace: str = ""
    annual_palace: str = ""
    decade_label: str = ""
    annual_label: str = ""
    input_quality: str = "explicit_plate"
    calculator: str = ""
    soul_star: str = ""
    body_star: str = ""
    five_elements_class: str = ""
    horoscope: dict[str, object] = Field(default_factory=dict)
    reasoning_ready: bool = False
    warnings: list[str] = Field(default_factory=list)
    boundary: str = "ziwei_plate_input_is_explicit_plate_data_not_birth_inference"

    @model_validator(mode="after")
    def _identity(self) -> "ZiweiPlateInput":
        require_non_empty(self.plate_input_id, "plate_input_id")
        require_non_empty(self.birth_input_id, "birth_input_id")
        require_non_empty(self.source, "source")
        return self


class ZiweiMaterialBundle(V50Model):
    version: str = "v50.ziwei_material_bundle.v1"
    bundle_id: str
    reading_id: str
    birth_input_id: str
    plate_input: ZiweiPlateInput
    material_store: UnifiedMingliMaterialStore
    palace_refs: list[str] = Field(default_factory=list)
    star_refs: list[str] = Field(default_factory=list)
    transformation_refs: list[str] = Field(default_factory=list)
    cycle_refs: list[str] = Field(default_factory=list)
    generated_from_birth_input: bool = True
    creates_judgment: bool = False
    llm_used: bool = False
    boundary: str = "ziwei_material_bundle_is_chart_material_not_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "ZiweiMaterialBundle":
        require_non_empty(self.bundle_id, "bundle_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.birth_input_id, "birth_input_id")
        require_refs(self.palace_refs, "palace_refs")
        require_refs(self.star_refs, "star_refs")
        require_refs(self.transformation_refs, "transformation_refs")
        require_refs(self.cycle_refs, "cycle_refs")
        if self.material_store.reading_id != self.reading_id:
            raise ValueError("ZiweiMaterialBundle material_store reading_id mismatch")
        if self.plate_input.birth_input_id != self.birth_input_id:
            raise ValueError("ZiweiMaterialBundle plate_input birth_input_id mismatch")
        if self.creates_judgment:
            raise ValueError("ZiweiMaterialBundle cannot create judgment")
        if self.llm_used:
            raise ValueError("ZiweiMaterialBundle cannot use LLM")
        return self


class ZiweiDynamicEvidence(V50Model):
    version: str = "v50.ziwei_dynamic_evidence.v1"
    evidence_id: str
    reading_id: str
    topic: Topic
    evidence_type: str
    palace_refs: list[str] = Field(default_factory=list)
    star_refs: list[str] = Field(default_factory=list)
    transformation_refs: list[str] = Field(default_factory=list)
    cycle_refs: list[str] = Field(default_factory=list)
    material_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    creates_judgment: bool = False
    llm_used: bool = False
    boundary: str = "ziwei_dynamic_evidence_is_timing_evidence_not_final_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "ZiweiDynamicEvidence":
        require_non_empty(self.evidence_id, "evidence_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.evidence_type, "evidence_type")
        require_refs(self.palace_refs, "palace_refs")
        require_refs(self.star_refs, "star_refs")
        require_refs(self.transformation_refs, "transformation_refs")
        require_refs(self.cycle_refs, "cycle_refs")
        require_refs(self.material_refs, "material_refs")
        if self.creates_judgment:
            raise ValueError("ZiweiDynamicEvidence cannot create judgment")
        if self.llm_used:
            raise ValueError("ZiweiDynamicEvidence cannot use LLM")
        return self


class ZiweiDynamicEvidenceBundle(V50Model):
    version: str = "v50.ziwei_dynamic_evidence_bundle.v1"
    bundle_id: str
    reading_id: str
    evidence_items: list[ZiweiDynamicEvidence] = Field(default_factory=list)
    evidence_count: int = Field(default=0, ge=0)
    creates_judgment: bool = False
    llm_used: bool = False
    boundary: str = "ziwei_dynamic_evidence_bundle_feeds_brain_fusion_without_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "ZiweiDynamicEvidenceBundle":
        require_non_empty(self.bundle_id, "bundle_id")
        require_non_empty(self.reading_id, "reading_id")
        if self.evidence_count != len(self.evidence_items):
            raise ValueError("evidence_count must match evidence_items")
        if any(item.reading_id != self.reading_id for item in self.evidence_items):
            raise ValueError("ZiweiDynamicEvidenceBundle cannot mix readings")
        if self.creates_judgment:
            raise ValueError("ZiweiDynamicEvidenceBundle cannot create judgment")
        if self.llm_used:
            raise ValueError("ZiweiDynamicEvidenceBundle cannot use LLM")
        return self
