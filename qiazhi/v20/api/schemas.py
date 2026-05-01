from __future__ import annotations

from pydantic import BaseModel, Field


class MeasureRequest(BaseModel):
    year: str = Field(..., min_length=2, max_length=2)
    month: str = Field(..., min_length=2, max_length=2)
    day: str = Field(..., min_length=2, max_length=2)
    hour: str = Field(..., min_length=2, max_length=2)
    flow_year_pillar: str = Field("", min_length=0, max_length=2)
    luck_pillar: str = Field("", min_length=0, max_length=2)
    flow_month_pillar: str = Field("", min_length=0, max_length=2)
    input_id: str = ""
    question_key: str = ""
    user_text: str = ""
    locale: str = "zh"


class MeasureResponse(BaseModel):
    version: str
    input_id: str
    locale: str
    runtime_mutation: bool
    answer_text: str
    guardrails: list[str]


class FeedbackRequest(BaseModel):
    input_id: str = ""
    source_role: str = "user"
    feedback_text: str = Field(..., min_length=1, max_length=2000)
    feature_ids: list[str] = Field(default_factory=list)
    locale: str = "zh"


class PortraitCalibrationRequest(BaseModel):
    input_id: str = ""
    feature_id: str = Field(..., min_length=1, max_length=160)
    source_role: str = "user"
    signal: str = Field(..., pattern="^(confirm|reject|needs_review|evidence_gap)$")
    note: str = Field("", max_length=1000)
    locale: str = "zh"


class PolicyReviewRequest(BaseModel):
    policy_type: str = Field(..., pattern="^(question_ranking|knowledge_retrieval|confidence_calibration)$")
    policy_payload: dict[str, object] = Field(default_factory=dict)
    source: str = "manual_review"
    eval_report_id: str = ""
