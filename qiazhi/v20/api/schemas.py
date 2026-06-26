from __future__ import annotations

from pydantic import BaseModel, Field


class PractitionerControlSelectionRequest(BaseModel):
    control_key: str = Field(..., min_length=1, max_length=160)
    option: str = Field(..., min_length=1, max_length=40)
    source_decision_keys: list[str] = Field(default_factory=list)


class LatentEventCalibrationAnswerRequest(BaseModel):
    scenario_id: str = Field(..., min_length=1, max_length=120)
    year_option: str = Field(..., min_length=1, max_length=40)
    result_option: str = Field(..., min_length=1, max_length=80)
    intensity: str = Field(..., pattern="^(none|mild|clear|strong)$")
    confidence: str = Field(..., pattern="^(low|medium|high)$")


class MeasureRequest(BaseModel):
    year: str = Field(..., min_length=2, max_length=4)
    month: str = Field(..., min_length=1, max_length=2)
    day: str = Field(..., min_length=1, max_length=2)
    hour: str = Field(..., min_length=1, max_length=2)
    calendar: str = "solar"
    gender: str = "male"
    lunar_is_leap: bool = False
    flow_year_pillar: str = Field("", min_length=0, max_length=2)
    luck_pillar: str = Field("", min_length=0, max_length=2)
    flow_month_pillar: str = Field("", min_length=0, max_length=2)
    input_id: str = ""
    question_key: str = ""
    user_text: str = ""
    locale: str = "zh"
    source_role: str = Field("user", pattern="^(guest|user|analyst|admin|lab|practitioner)$")
    llm_mode: str = Field("deterministic", pattern="^(deterministic|rewrite|practitioner)$")
    practitioner_selections: list[PractitionerControlSelectionRequest] = Field(default_factory=list)
    latent_event_answers: list[LatentEventCalibrationAnswerRequest] = Field(default_factory=list)
    question_id: str = ""
    answered_question_ids: list[str] = Field(default_factory=list)
    answered_question_keys: list[str] = Field(default_factory=list)


class MeasureResponse(BaseModel):
    version: str
    input_id: str
    locale: str
    runtime_mutation: bool
    answer_text: str
    guardrails: list[str]


class ProfileMutationRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=120)
    owner_id: str = Field("", max_length=160)
    status: str = Field("active", max_length=40)
    birth_input: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class FeedbackRequest(BaseModel):
    input_id: str = ""
    source_role: str = "user"
    feedback_text: str = Field(..., min_length=1, max_length=2000)
    feature_ids: list[str] = Field(default_factory=list)
    locale: str = "zh"


class QuestionSourceRankingRecordRequest(BaseModel):
    input_id: str = ""
    source_role: str = Field("user", pattern="^(guest|user|analyst|admin|lab|practitioner)$")
    question_source_ranking_report: dict[str, object] = Field(default_factory=dict)
    locale: str = "zh"


class RoleQuestionClickRequest(BaseModel):
    input_id: str = ""
    source_role: str = Field("user", pattern="^(guest|user|analyst|admin|lab|practitioner)$")
    question: dict[str, object] = Field(default_factory=dict)
    locale: str = "zh"


class QuestionReviewRequest(BaseModel):
    input_id: str = ""
    source_role: str = Field("analyst", pattern="^(analyst|admin|lab|practitioner)$")
    question: dict[str, object] = Field(default_factory=dict)
    action: str = Field(..., pattern="^(approve|rewrite|downrank|merge|delete)$")
    reason: str = Field("", pattern="^(|role_mismatch|mainline_mismatch|too_technical|duplicate|unfocused)$")
    locale: str = "zh"


class PortraitCalibrationRequest(BaseModel):
    input_id: str = ""
    feature_id: str = Field(..., min_length=1, max_length=160)
    source_role: str = "user"
    signal: str = Field(..., pattern="^(confirm|reject|needs_review|evidence_gap)$")
    note: str = Field("", max_length=1000)
    locale: str = "zh"


class PractitionerCalibrationRequest(BaseModel):
    input_id: str = ""
    source_role: str = Field("analyst", pattern="^(analyst|admin|practitioner)$")
    selections: list[PractitionerControlSelectionRequest] = Field(default_factory=list, min_length=1)
    locale: str = "zh"


class LatentEventCalibrationRequest(BaseModel):
    input_id: str = ""
    source_role: str = Field("user", pattern="^(user|analyst|admin|practitioner)$")
    answers: list[LatentEventCalibrationAnswerRequest] = Field(default_factory=list, min_length=1)
    locale: str = "zh"


class OrchestratorMemoryRecordRequest(BaseModel):
    input_id: str = ""
    source_role: str = Field("analyst", pattern="^(analyst|admin|lab|practitioner)$")
    brain_memory_signal: dict[str, object] = Field(default_factory=dict)
    locale: str = "zh"
