from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


RoleKey = Literal["guest", "user", "practitioner", "analyst", "admin", "lab"]
LocaleKey = Literal["zh", "en", "ko"]
ClientKey = Literal["web", "mobile", "admin", "lab"]
AnchorStatus = Literal["bound", "weak", "missing_time", "missing_structure", "unsupported"]
CalendarType = Literal["solar", "lunar"]
GenderKey = Literal["male", "female", "unknown"]
ChartBuildSourceType = Literal["explicit_pillars", "birth_input"]
ChartBuildStatus = Literal["ready", "pending", "unsupported", "blocked"]


class V30Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class BirthInput(V30Model):
    input_id: str = ""
    calendar_type: CalendarType = "solar"
    birth_date: str
    birth_time: str | None = None
    timezone: str = "Asia/Shanghai"
    birth_place: str = ""
    gender: GenderKey = "unknown"
    lunar_is_leap_month: bool = False
    use_true_solar_time: bool = False
    unknown_hour: bool = False
    calendar_assumption: str = "birth_input_requires_calendar_conversion"
    source: str = "user"

    @model_validator(mode="after")
    def _require_time_or_unknown_hour(self) -> "BirthInput":
        if not self.unknown_hour and not str(self.birth_time or "").strip():
            raise ValueError("birth_time is required unless unknown_hour=True")
        return self


class ChartBuildSource(V30Model):
    source_type: ChartBuildSourceType
    input_id: str = ""
    calendar_assumption: str
    status: ChartBuildStatus
    source: str = ""
    guardrails: list[str] = Field(default_factory=list)


class CalendarConversionTrace(V30Model):
    trace_id: str
    status: ChartBuildStatus
    calendar_type: CalendarType
    timezone: str
    use_true_solar_time: bool = False
    unknown_hour: bool = False
    boundary_flags: list[str] = Field(default_factory=list)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)


class FourPillarResult(V30Model):
    status: ChartBuildStatus
    pillars: dict[str, Any] = Field(default_factory=dict)
    missing_pillars: list[str] = Field(default_factory=list)
    chart_build_source: ChartBuildSource
    conversion_trace: CalendarConversionTrace | None = None
    guardrails: list[str] = Field(default_factory=list)


class ChartContext(V30Model):
    context_id: str
    reading_id: str
    input_pillars: dict[str, Any]
    natal_pillars: dict[str, Any]
    day_master: str
    day_master_element: str
    time_layers: dict[str, Any]
    locale: LocaleKey = "zh"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BirthChartBuildResult(V30Model):
    reading_id: str
    birth_input: BirthInput
    four_pillar_result: FourPillarResult
    chart_context: ChartContext | None = None
    status: ChartBuildStatus
    failures: list[str] = Field(default_factory=list)


class LuckCycleContext(V30Model):
    version: str = "v30.luck_cycle_context.v1"
    status: ChartBuildStatus
    direction: str = ""
    start_age: int | None = None
    start_year: int | None = None
    start_solar: str = ""
    current_luck_pillar: str = ""
    current_luck: dict[str, Any] = Field(default_factory=dict)
    luck_cycles: list[dict[str, Any]] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    trace: dict[str, Any] = Field(default_factory=dict)
    guardrails: list[str] = Field(default_factory=list)


class FlowContext(V30Model):
    version: str = "v30.flow_context.v1"
    status: ChartBuildStatus
    target_date: str = ""
    flow_year_pillar: str = ""
    flow_month_pillar: str = ""
    trace: dict[str, Any] = Field(default_factory=dict)
    guardrails: list[str] = Field(default_factory=list)


class SixPillarContext(V30Model):
    version: str = "v30.six_pillar_context.v1"
    status: ChartBuildStatus
    natal_pillars: dict[str, Any] = Field(default_factory=dict)
    luck_pillar: str = ""
    flow_year_pillar: str = ""
    flow_month_pillar: str = ""
    pillars: list[dict[str, Any]] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)


class RankedDecision(V30Model):
    decision_id: str
    domain: str
    status: str
    primary_candidate: str
    alternatives: list[str] = Field(default_factory=list)
    candidate_scores: dict[str, float] = Field(default_factory=dict)
    scoring_basis: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: list[str] = Field(default_factory=list)
    weakening_evidence: list[str] = Field(default_factory=list)
    unresolved_requirements: list[str] = Field(default_factory=list)
    model_signal_summary: dict[str, Any] = Field(default_factory=dict)
    boundary: str


class PracticalReadingContext(V30Model):
    version: str = "v30.practical_reading_context.v1"
    status: str
    role_modes: list[str] = Field(default_factory=list)
    domain_readings: dict[str, dict[str, Any]] = Field(default_factory=dict)
    timing_summary: dict[str, Any] = Field(default_factory=dict)
    question_gaps: list[dict[str, Any]] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)


class TenGodEnergyScore(V30Model):
    label: str
    family: str
    energy: float = Field(ge=0.0, le=1.0)
    stability: float = Field(ge=0.0, le=1.0)
    volatility: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    raw_weight: float = 0.0
    sources: list[str] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    boundary: str = "ten_god_energy_model_signal_not_chart_fact"


class TenGodEnergyModel(V30Model):
    version: str = "v30.ten_god_energy_model.v1"
    status: str
    context_id: str
    target_year: int | None = None
    day_master: str
    day_master_element: str
    scores: dict[str, TenGodEnergyScore] = Field(default_factory=dict)
    dominant_ten_gods: list[str] = Field(default_factory=list)
    high_volatility_ten_gods: list[str] = Field(default_factory=list)
    low_stability_ten_gods: list[str] = Field(default_factory=list)
    interaction_matrix: dict[str, dict[str, float]] = Field(default_factory=dict)
    trace: dict[str, Any] = Field(default_factory=dict)
    boundary: str = "ten_god_energy_model_signal_not_chart_fact"


class ClientProfile(V30Model):
    client: ClientKey
    density: str
    max_questions: int
    show_reasons: bool
    show_diagnostics: bool
    actions: list[str] = Field(default_factory=list)
    boundary: str = "client_profile_changes_projection_not_chart_fact"


class FeatureEvidence(V30Model):
    evidence_id: str
    domain: str
    kind: str
    label: str
    source: str
    confidence: float = Field(ge=0.0, le=1.0)
    supports: list[str] = Field(default_factory=list)
    weakens: list[str] = Field(default_factory=list)
    boundary: str | None = None


class StructureState(V30Model):
    structure_id: str
    primary_chain: list[str]
    candidate_chains: list[list[str]] = Field(default_factory=list)
    graph_nodes: list[dict[str, Any]] = Field(default_factory=list)
    graph_edges: list[dict[str, Any]] = Field(default_factory=list)
    path_scores: dict[str, float] = Field(default_factory=dict)
    semantic_label: str
    state: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str]
    boundary: str | None = None


class MainlineState(V30Model):
    mainline_id: str
    domain: str
    title: str
    state: str
    score: float
    primary_structure_id: str
    evidence_ids: list[str]
    supporting_mainlines: list[str] = Field(default_factory=list)
    rejected_mainlines: list[str] = Field(default_factory=list)
    why_selected: str
    quality_gate: str


class QuestionIntentPlan(V30Model):
    plan_id: str
    role_key: RoleKey
    session_state: dict[str, Any] = Field(default_factory=dict)
    candidate_intents: list[str] = Field(default_factory=list)
    suppressed_intents: list[str] = Field(default_factory=list)
    recommended_questions: list[dict[str, Any]] = Field(default_factory=list)
    hidden_factor_probes: list[dict[str, Any]] = Field(default_factory=list)
    knowledge_rule_portrait_signals: list[dict[str, Any]] = Field(default_factory=list)
    policy_effect: dict[str, Any] = Field(default_factory=dict)


class BaziQuestionAnchor(V30Model):
    anchor_id: str
    question_id: str
    intent_id: str
    context_id: str
    role_key: RoleKey
    anchor_status: AnchorStatus
    day_master: str
    time_binding: dict[str, Any]
    primary_structure_id: str | None
    mainline_id: str | None
    evidence_ids: list[str] = Field(default_factory=list)
    why_this_question: str
    missing_requirements: list[str] = Field(default_factory=list)


class AnswerContext(V30Model):
    answer_context_id: str
    selected_question_anchor: BaziQuestionAnchor
    chart_summary: dict[str, Any]
    structure_summary: dict[str, Any]
    mainline_summary: dict[str, Any]
    evidence_summary: list[dict[str, Any]]
    knowledge_boundaries: list[str] = Field(default_factory=list)
    role_answer_contract: dict[str, Any]
    forbidden_drift: list[str] = Field(default_factory=list)


class AnswerResult(V30Model):
    answer_id: str
    question_id: str
    text: str
    evidence_ids: list[str]
    boundary: str | None = None
    source: str = "rule_bound"
    llm_metadata: dict[str, Any] = Field(default_factory=dict)


class CoreRuntimeResult(V30Model):
    reading_id: str
    chart_context: ChartContext
    feature_evidence: list[FeatureEvidence]
    structure_state: StructureState
    mainline_state: MainlineState
    question_plan: QuestionIntentPlan
    question_anchors: list[BaziQuestionAnchor]
    answer_context: AnswerContext | None = None
    answer_result: AnswerResult | None = None
    trace_id: str


class ClientPresentationModel(V30Model):
    reading_id: str
    role_key: RoleKey
    locale: LocaleKey
    client: ClientKey
    layout: dict[str, Any]
    header: dict[str, Any]
    reading_surface: dict[str, Any] = Field(default_factory=dict)
    chart_summary: dict[str, Any]
    mainline_card: dict[str, Any]
    structure_card: dict[str, Any]
    questions: list[dict[str, Any]]
    answer_panel: dict[str, Any] | None = None
    actions: list[dict[str, Any]] = Field(default_factory=list)
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    projection_contract: dict[str, Any] = Field(default_factory=dict)


class ValidationCase(V30Model):
    case_id: str
    source: str
    chart_context: dict[str, Any]
    expected_structure: dict[str, Any]
    expected_mainline: dict[str, Any]
    expected_questions: list[dict[str, Any]]
    expected_answer_boundaries: list[str] = Field(default_factory=list)
    negative_expectations: list[str] = Field(default_factory=list)
    role_expectations: dict[str, Any] = Field(default_factory=dict)
    locale_expectations: dict[str, Any] = Field(default_factory=dict)
    client_expectations: dict[str, Any] = Field(default_factory=dict)
