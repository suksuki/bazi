from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    topic_id: str = "topic-00-seen-and-continuing"
    topic_version: str = "1.0.0"
    mode: Literal["live", "time_shift", "solo"] = "solo"


class SessionJoinRequest(BaseModel):
    case_id: str | None = None
    disclosure_level: Literal["observer", "chart_facts", "approved_insights"] = "approved_insights"


class PrivateCompleteRequest(BaseModel):
    participant_run_id: str
    access_token: str = Field(min_length=16, max_length=200)
    response: str = Field(default="", max_length=800)


class ParticipantActionRequest(BaseModel):
    participant_run_id: str
    access_token: str = Field(min_length=16, max_length=200)
    event: str = Field(default="next", min_length=1, max_length=80)


class PerformancePrepareRequest(BaseModel):
    participant_run_id: str
    access_token: str = Field(min_length=16, max_length=200)


class ExperimentNodeRequest(BaseModel):
    participant_run_id: str
    access_token: str = Field(min_length=16, max_length=200)
    node_id: str = Field(min_length=1, max_length=260)


class ExperimentActionRequest(BaseModel):
    participant_run_id: str
    access_token: str = Field(min_length=16, max_length=200)


class ExperimentSaveRequest(ExperimentActionRequest):
    observation: str = Field(default="", max_length=1200)
    open_question: str = Field(default="", max_length=1200)


class DirectorActionRequest(BaseModel):
    event: str = Field(default="next", min_length=1, max_length=80)
