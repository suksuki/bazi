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
