from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from v40.contracts.base import RoleKey, Topic, V40Model
from v40.contracts.training import TrainingLabelEvent


class ConsentScope(str, Enum):
    PRACTITIONER_REVIEW = "practitioner_review"
    TRAINING_FEEDBACK = "training_feedback"
    ANONYMIZED_CASE_SHARE = "anonymized_case_share"


class ReviewRequestStatus(str, Enum):
    QUEUED = "queued"
    ASSIGNED = "assigned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PractitionerReviewDecision(str, Enum):
    SUPPORTS = "supports"
    REVISE = "revise"
    NEEDS_PROBE = "needs_probe"
    UNSURE = "unsure"


class ConsentGrant(V40Model):
    version: str = "v40.consent_grant.v1"
    grant_id: str
    reading_id: str
    granted_by_role: RoleKey = "user"
    scopes: list[ConsentScope] = Field(default_factory=list)
    allow_practitioner_review: bool = False
    allow_training_use: bool = False
    anonymized_case_only: bool = True
    revoked: bool = False
    expires_at: str = ""
    note: str = ""
    raw_chart_share_allowed: bool = False
    admin_control_allowed: bool = False
    boundary: str = "consent_grant_controls_case_sharing_without_admin_or_chart_fact_mutation"

    @model_validator(mode="after")
    def _consent_boundary(self) -> "ConsentGrant":
        if not self.grant_id.strip():
            raise ValueError("ConsentGrant requires grant_id")
        if not self.reading_id.strip():
            raise ValueError("ConsentGrant requires reading_id")
        if self.granted_by_role not in {"guest", "user", "practitioner"}:
            raise ValueError("ConsentGrant must be granted from user app role")
        if self.allow_practitioner_review and ConsentScope.PRACTITIONER_REVIEW not in self.scopes:
            raise ValueError("Practitioner review consent requires practitioner_review scope")
        if self.allow_training_use and ConsentScope.TRAINING_FEEDBACK not in self.scopes:
            raise ValueError("Training use consent requires training_feedback scope")
        if not self.anonymized_case_only or self.raw_chart_share_allowed:
            raise ValueError("Phase 51 supports anonymized case sharing only")
        if self.admin_control_allowed:
            raise ValueError("ConsentGrant cannot grant admin control")
        return self


class AnonymizedCaseView(V40Model):
    version: str = "v40.anonymized_case_view.v1"
    case_view_id: str
    consent_grant_id: str
    reading_id: str
    topic: Topic = Topic.UNKNOWN
    summary: str = ""
    verdict_summaries: list[str] = Field(default_factory=list)
    advice_summaries: list[str] = Field(default_factory=list)
    probe_questions: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    source_signal_ids: list[str] = Field(default_factory=list)
    hidden_user_fields: list[str] = Field(default_factory=lambda: ["name", "birth_datetime", "contact", "account_id"])
    chart_facts_included: bool = False
    raw_runtime_included: bool = False
    boundary: str = "anonymized_case_view_is_review_material_not_raw_runtime_or_chart_facts"

    @model_validator(mode="after")
    def _case_view_boundary(self) -> "AnonymizedCaseView":
        if not self.case_view_id.strip():
            raise ValueError("AnonymizedCaseView requires case_view_id")
        if self.chart_facts_included or self.raw_runtime_included:
            raise ValueError("AnonymizedCaseView cannot include chart facts or raw runtime")
        if not (self.verdict_summaries or self.advice_summaries or self.probe_questions):
            raise ValueError("AnonymizedCaseView requires review material")
        return self


class PractitionerReviewRequest(V40Model):
    version: str = "v40.practitioner_review_request.v1"
    review_request_id: str
    consent_grant_id: str
    reading_id: str
    requested_topic: Topic = Topic.UNKNOWN
    case_view: AnonymizedCaseView
    status: ReviewRequestStatus = ReviewRequestStatus.QUEUED
    requested_by_role: RoleKey = "user"
    assigned_to_practitioner_ref: str = ""
    note: str = ""
    runtime_ref: str = ""
    boundary: str = "practitioner_review_request_queues_anonymized_case_without_verdict_mutation"

    @model_validator(mode="after")
    def _request_boundary(self) -> "PractitionerReviewRequest":
        if not self.review_request_id.strip():
            raise ValueError("PractitionerReviewRequest requires review_request_id")
        if self.case_view.consent_grant_id != self.consent_grant_id:
            raise ValueError("Review request consent_grant_id must match case view")
        if self.case_view.reading_id != self.reading_id:
            raise ValueError("Review request reading_id must match case view")
        if self.requested_by_role not in {"guest", "user", "practitioner"}:
            raise ValueError("Review request must originate from user app role")
        return self


class PractitionerReviewQueueItem(V40Model):
    version: str = "v40.practitioner_review_queue_item.v1"
    queue_item_id: str
    review_request_id: str
    reading_id: str
    topic: Topic = Topic.UNKNOWN
    status: ReviewRequestStatus = ReviewRequestStatus.QUEUED
    summary: str = ""
    consent_scopes: list[ConsentScope] = Field(default_factory=list)
    assigned_to_practitioner_ref: str = ""
    boundary: str = "practitioner_review_queue_item_is_assignment_metadata_not_raw_case_data"


class PractitionerReviewResult(V40Model):
    version: str = "v40.practitioner_review_result.v1"
    result_id: str
    review_request_id: str
    reading_id: str
    reviewer_role: RoleKey = "practitioner"
    decision: PractitionerReviewDecision = PractitionerReviewDecision.UNSURE
    selected_signal_ids: list[str] = Field(default_factory=list)
    selected_verdict_ids: list[str] = Field(default_factory=list)
    advice_notes: list[str] = Field(default_factory=list)
    probe_suggestions: list[str] = Field(default_factory=list)
    training_label_events: list[TrainingLabelEvent] = Field(default_factory=list)
    changes_verdict: bool = False
    changes_chart_facts: bool = False
    writes_global_weight: bool = False
    boundary: str = "practitioner_review_result_creates_training_material_without_direct_decision_mutation"

    @model_validator(mode="after")
    def _result_boundary(self) -> "PractitionerReviewResult":
        if not self.result_id.strip():
            raise ValueError("PractitionerReviewResult requires result_id")
        if self.reviewer_role not in {"practitioner", "admin"}:
            raise ValueError("PractitionerReviewResult requires practitioner or admin reviewer")
        if self.changes_verdict or self.changes_chart_facts or self.writes_global_weight:
            raise ValueError("PractitionerReviewResult cannot directly mutate verdict, chart facts, or global weights")
        for event in self.training_label_events:
            if not event.local_only:
                raise ValueError("Practitioner review training labels must remain local until batch review")
        return self
