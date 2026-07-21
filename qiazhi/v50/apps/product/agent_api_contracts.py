from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from core.contracts import BirthInputCanonical
from core.life_domains import LifeDomain
from core.mingli_agent import BirthIntakeDraft


class IntakeRequest(BaseModel):
    message: str = Field(min_length=1, max_length=800)
    current_draft: BirthIntakeDraft | None = None


class CaseStartRequest(BaseModel):
    birth_input: BirthInputCanonical | None = None
    profile_id: str | None = None
    active_mode: Literal["guest", "member", "practitioner", "research"] | None = None
    progressive: bool = False


class CaseTurnRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1200)
    active_mode: Literal["guest", "member", "practitioner", "research"] | None = None


class ProbePlanRequest(BaseModel):
    active_mode: Literal["guest", "member", "practitioner", "research"] | None = None
    scenario: Literal["recognition", "domain", "timing", "falsification", "decision"] = "recognition"
    domain: LifeDomain = LifeDomain.WHOLE_CHART


class ProbeResponseRequest(ProbePlanRequest):
    plan_id: str
    option_id: str
    year_value: int | None = Field(default=None, ge=1900, le=2100)
    event_note: str = Field(default="", max_length=300)
    recurrence_count: int | None = Field(default=None, ge=0, le=99)


class DomainExploreRequest(BaseModel):
    user_question: str = Field(default="", max_length=600)
    active_mode: Literal["guest", "member", "practitioner", "research"] | None = None
    progressive: bool = False


class DeliberationSelectionRequest(BaseModel):
    active_mode: Literal["practitioner", "research"]
    stage_id: Literal["pattern", "useful_god", "work_path", "ziwei_focus", "domain_assertion"]
    option_id: str = Field(min_length=1, max_length=240)
    action: Literal["select", "support", "challenge", "defer", "research_fork"]
    active_domain: LifeDomain = LifeDomain.WHOLE_CHART
    rationale: str = Field(default="", max_length=600)


class DeliberationUndoRequest(BaseModel):
    active_mode: Literal["practitioner", "research"]
    active_domain: LifeDomain = LifeDomain.WHOLE_CHART


class AbuResolveRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1200)
    has_case: bool = False
    has_profile: bool = False
    active_mode: Literal["guest", "member", "practitioner", "research"] = "guest"
    active_domain: LifeDomain = LifeDomain.WHOLE_CHART


class TemporalSelectRequest(BaseModel):
    period_key: str = Field(min_length=7, max_length=7)
    active_mode: Literal["guest", "member", "practitioner", "research"] | None = None


class RealityEvidenceRequest(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=180)
    source: Literal["page", "abu", "probe", "monthly_review", "practitioner", "research", "import"]
    summary: str = Field(min_length=1, max_length=800)
    period_key: str = Field(min_length=7, max_length=7)
    domain: str = Field(default="whole_chart", max_length=80)
    source_ref: str = Field(default="", max_length=180)
    kind: str = Field(default="life_event", max_length=80)
    occurred_at: str = Field(default="", max_length=64)
    confirmation_status: Literal["reported", "confirmed", "corrected", "withdrawn"] = "reported"
    severity: Literal["low", "medium", "high", "unknown"] = "unknown"
    subjective_impact: str = Field(default="", max_length=600)
    structured_payload: dict[str, Any] = Field(default_factory=dict)
    active_mode: Literal["guest", "member", "practitioner", "research"] | None = None


class MonthlyReviewRequest(BaseModel):
    period_key: str = Field(min_length=7, max_length=7)
    temporal_snapshot_id: str = Field(min_length=1, max_length=180)
    evidence_refs: list[str] = Field(default_factory=list)
    verdict: Literal[
        "supported",
        "partially_supported",
        "not_observed",
        "contradicted",
        "insufficient_evidence",
    ]
    user_note: str = Field(default="", max_length=800)


class CaseRevisionCommitRequest(BaseModel):
    candidate_id: str = Field(min_length=1, max_length=180)
