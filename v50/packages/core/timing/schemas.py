from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from core.contracts.base import V50Model, require_non_empty, require_refs


class TimingLayer(str, Enum):
    LUCK = "luck"
    YEAR = "year"
    MONTH = "month"


class TimingModelFamily(str, Enum):
    SECOND_MONTH_COMMAND = "second_month_command"
    LONG_TERM_FIELD = "long_term_field"
    PERTURBATION_SOURCE = "perturbation_source"
    STAGE_DOMINANT_VARIABLE = "stage_dominant_variable"
    TRIGGER = "trigger"
    SHORT_TERM_FIELD = "short_term_field"
    ACTIVATION_EVENT = "activation_event"
    STRUCTURE_COMPLETION = "structure_completion"
    FINE_GRAINED_TRIGGER = "fine_grained_trigger"
    SHORT_PULSE_FIELD = "short_pulse_field"
    EVENT_WINDOW = "event_window"
    MICRO_STRUCTURE_COMPLETION = "micro_structure_completion"


class TimingChange(str, Enum):
    NODE_ENERGY = "node_energy"
    EDGE_STRENGTH = "edge_strength"
    PATH_ACTIVATION = "path_activation"
    PATH_COST = "path_cost"
    MECHANISM_RANKING = "mechanism_ranking"
    TOPIC_TIMING = "topic_timing"
    TOPIC_PRIORITY = "topic_priority"
    EVENT_WINDOW = "event_window"


class TimingRelation(str, Enum):
    OVERLAY = "overlay"
    ACTIVATE = "activate"
    SUPPRESS = "suppress"
    REROUTE = "reroute"
    COMPLETE = "complete"
    BREAK = "break"
    AMPLIFY = "amplify"
    NEUTRALIZE = "neutralize"
    TRIGGER = "trigger"
    COOPERATE = "cooperate"
    CONFLICT = "conflict"
    FOCUS = "focus"


class TimingSimulatorOutput(str, Enum):
    STATE_DELTA = "state_delta"
    FIELD_DELTA = "field_delta"
    ACTIVATED_PATHS = "activated_paths"
    WEAKENED_NODES = "weakened_nodes"
    STRENGTHENED_NODES = "strengthened_nodes"
    STRENGTHENED_EDGES = "strengthened_edges"
    REROUTED_FLOW = "rerouted_flow"
    COMPLETED_PATHS = "completed_paths"
    BROKEN_PATHS = "broken_paths"
    MECHANISM_SHIFT = "mechanism_shift"
    TOPIC_TIMING_SIGNAL = "topic_timing_signal"
    EVENT_PRESSURE_SCORE = "event_pressure_score"
    EVENT_WINDOW_SCORE = "event_window_score"
    TIMING_PRECISION_SCORE = "timing_precision_score"


class TimingInteractionType(str, Enum):
    EXACT = "exact"
    HARMONY = "harmony"
    CLASH = "clash"
    SAME_ELEMENT = "same_element"
    GENERATES_TARGET = "generates_target"
    CONTROLS_TARGET = "controls_target"
    TARGET_CONTROLS = "target_controls"


class TimingEffect(str, Enum):
    ACTIVATE = "activate"
    SUPPORT = "support"
    AMPLIFY = "amplify"
    SUPPRESS = "suppress"
    CONFLICT = "conflict"
    RESIST = "resist"


class TimingModelCandidate(V50Model):
    version: str = "v50.timing_model_candidate.v1"
    model_id: str
    timing_layer: TimingLayer
    model_family: TimingModelFamily
    current_confidence: float = Field(ge=0.0, le=1.0)
    changes: list[TimingChange] = Field(default_factory=list)
    does_not_change: list[str] = Field(default_factory=list)
    relation_to_natal: list[TimingRelation] = Field(default_factory=list)
    relation_to_other_timing_layers: list[TimingRelation] = Field(default_factory=list)
    simulator_outputs: list[TimingSimulatorOutput] = Field(default_factory=list)
    validation_plan: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    runtime_active: bool = False
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    mutates_natal_structure: bool = False
    boundary: str = "timing_model_candidate_is_research_policy_not_runtime_truth"

    @model_validator(mode="after")
    def _boundary(self) -> "TimingModelCandidate":
        require_non_empty(self.model_id, "model_id")
        if not self.changes:
            raise ValueError("TimingModelCandidate requires changes")
        require_refs(self.does_not_change, "does_not_change")
        require_refs([item.value for item in self.relation_to_natal], "relation_to_natal")
        require_refs([item.value for item in self.simulator_outputs], "simulator_outputs")
        require_refs(self.validation_plan, "validation_plan")
        require_refs(self.source_refs, "source_refs")
        if self.runtime_active:
            raise ValueError("TimingModelCandidate v1 cannot be runtime active")
        if self.creates_judgment:
            raise ValueError("TimingModelCandidate cannot create judgment")
        if self.calls_brain:
            raise ValueError("TimingModelCandidate cannot call Brain")
        if self.calls_llm:
            raise ValueError("TimingModelCandidate cannot call LLM")
        if self.mutates_natal_structure:
            raise ValueError("TimingModelCandidate cannot mutate natal structure")
        return self


class PersonalTimingMaterial(V50Model):
    version: str = "v50.personal_timing_material.v1"
    material_id: str
    reading_id: str
    analysis_year: int = Field(ge=1900, le=2200)
    annual_pillar: str
    luck_pillar: str = ""
    luck_start_year: int | None = None
    luck_end_year: int | None = None
    luck_start_age: int | None = None
    luck_end_age: int | None = None
    calculation_refs: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    creates_judgment: bool = False

    @model_validator(mode="after")
    def _boundary(self) -> "PersonalTimingMaterial":
        require_non_empty(self.material_id, "personal timing material_id")
        require_non_empty(self.reading_id, "personal timing reading_id")
        require_non_empty(self.annual_pillar, "personal timing annual_pillar")
        require_refs(self.calculation_refs, "personal timing calculation_refs")
        if self.luck_pillar and (self.luck_start_year is None or self.luck_end_year is None):
            raise ValueError("luck pillar requires its year range")
        if self.creates_judgment:
            raise ValueError("PersonalTimingMaterial is calendar material, not judgment")
        return self


class TimingInteraction(V50Model):
    version: str = "v50.timing_interaction.v1"
    interaction_id: str
    reading_id: str
    timing_layer: TimingLayer
    timing_symbol: str
    timing_pillar: str
    target_node_ref: str
    target_label: str
    target_path_refs: list[str] = Field(default_factory=list)
    interaction_type: TimingInteractionType
    effect: TimingEffect
    effect_delta: float = Field(ge=-1.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    theory_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    creates_judgment: bool = False

    @model_validator(mode="after")
    def _boundary(self) -> "TimingInteraction":
        require_non_empty(self.interaction_id, "timing interaction_id")
        require_non_empty(self.reading_id, "timing interaction reading_id")
        require_non_empty(self.timing_symbol, "timing interaction symbol")
        require_non_empty(self.timing_pillar, "timing interaction pillar")
        require_non_empty(self.target_node_ref, "timing interaction target")
        require_non_empty(self.target_label, "timing interaction target_label")
        require_refs(self.evidence_refs, "timing interaction evidence_refs")
        require_refs(self.theory_refs, "timing interaction theory_refs")
        if self.creates_judgment:
            raise ValueError("TimingInteraction is evidence, not judgment")
        return self


class PersonalTimingAssessment(V50Model):
    version: str = "v50.personal_timing_assessment.v1"
    assessment_id: str
    reading_id: str
    material: PersonalTimingMaterial
    interactions: list[TimingInteraction] = Field(default_factory=list)
    activated_path_refs: list[str] = Field(default_factory=list)
    weakened_node_refs: list[str] = Field(default_factory=list)
    mechanism_shifts: dict[str, float] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    theory_refs: list[str] = Field(default_factory=lambda: ["T001", "T006"])
    model_candidate_refs: list[str] = Field(
        default_factory=lambda: ["timing.luck.long_term_field.v1", "timing.year.activation_event.v1"]
    )
    validation_status: str = "research_candidate"
    publicly_supported: bool = False
    uncertainty: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    mutates_natal_structure: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    creates_judgment: bool = False

    @model_validator(mode="after")
    def _boundary(self) -> "PersonalTimingAssessment":
        require_non_empty(self.assessment_id, "personal timing assessment_id")
        require_non_empty(self.reading_id, "personal timing assessment reading_id")
        require_refs(self.evidence_refs, "personal timing assessment evidence_refs")
        require_refs(self.theory_refs, "personal timing assessment theory_refs")
        require_refs(self.model_candidate_refs, "personal timing model_candidate_refs")
        if self.material.reading_id != self.reading_id:
            raise ValueError("PersonalTimingAssessment cannot mix readings")
        if self.publicly_supported:
            raise ValueError("Timing v1 remains research candidate and cannot be publicly supported")
        if self.mutates_natal_structure or self.calls_brain or self.calls_llm or self.creates_judgment:
            raise ValueError("Personal timing assessment cannot mutate natal structure or create judgment")
        return self
