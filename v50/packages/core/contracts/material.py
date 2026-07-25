from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from core.contracts.base import SourceEngine, Topic, V50Model, require_non_empty, require_refs


class MaterialType(str, Enum):
    BAZI_CHART_FACT = "bazi.chart_fact"
    BAZI_TEN_GOD = "bazi.ten_god"
    BAZI_HIDDEN_STEM = "bazi.hidden_stem"
    BAZI_ROOT_STRENGTH = "bazi.root_strength"
    BAZI_STRENGTH = "bazi.strength"
    BAZI_COMBINATION = "bazi.combination"
    BAZI_LUCK = "bazi.luck"
    ZIWEI_PALACE = "ziwei.palace"
    ZIWEI_STAR = "ziwei.star"
    ZIWEI_FOUR_TRANSFORMATION = "ziwei.four_transformation"
    ZIWEI_TIME_WINDOW = "ziwei.time_window"
    ZIWEI_PALACE_RELATION = "ziwei.palace_relation"
    FUTURE_ENGINE = "future_engine.material"


class MingliMaterial(V50Model):
    version: str = "v50.mingli_material.v1"
    material_id: str
    reading_id: str
    source_engine: SourceEngine
    material_type: MaterialType
    topic: Topic = Topic.UNKNOWN
    raw_value: dict[str, object] = Field(default_factory=dict)
    normalized_value: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    knowledge_refs: list[str] = Field(default_factory=list)
    rule_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    verdict_authority: bool = False
    llm_decision_authority: bool = False
    mutates_birth_input: bool = False
    boundary: str = "material_is_engine_output_not_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "MingliMaterial":
        require_non_empty(self.material_id, "material_id")
        require_non_empty(self.reading_id, "reading_id")
        require_refs(self.evidence_refs, "evidence_refs")
        if self.verdict_authority:
            raise ValueError("MingliMaterial cannot have verdict authority")
        if self.llm_decision_authority:
            raise ValueError("MingliMaterial cannot grant LLM decision authority")
        if self.mutates_birth_input:
            raise ValueError("MingliMaterial cannot mutate birth input")
        return self


class UnifiedMingliMaterialStore(V50Model):
    version: str = "v50.unified_mingli_material_store.v1"
    store_id: str
    reading_id: str
    materials: list[MingliMaterial] = Field(default_factory=list)
    material_count: int = Field(default=0, ge=0)
    material_ids_by_engine: dict[str, list[str]] = Field(default_factory=dict)
    material_ids_by_type: dict[str, list[str]] = Field(default_factory=dict)
    boundary: str = "material_store_unifies_engine_materials_without_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "UnifiedMingliMaterialStore":
        require_non_empty(self.store_id, "store_id")
        require_non_empty(self.reading_id, "reading_id")
        if self.material_count != len(self.materials):
            raise ValueError("material_count must match materials")
        return self
