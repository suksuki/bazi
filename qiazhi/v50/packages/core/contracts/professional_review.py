from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from core.contracts.base import V50Model


PersistenceStatus = Literal["draft", "persisted", "failed"]
ProfessionalReleaseStatus = Literal[
    "unreviewed",
    "passed",
    "blocked",
    "partially_blocked",
]
MingliAssertionType = Literal[
    "chart_fact",
    "derived_relation",
    "structural_hypothesis",
    "mechanism_claim",
    "work_path_claim",
    "functional_role_claim",
    "portrait_claim",
    "domain_claim",
    "timing_claim",
    "prediction",
    "question",
    "counterfactual",
]
MingliAssertionModality = Literal[
    "asserted",
    "candidate",
    "conditional",
    "counterfactual",
    "quoted",
    "interrogative",
    "negated",
]
MingliAssertionScope = Literal[
    "natal",
    "luck_cycle",
    "annual",
    "monthly",
    "domain",
    "case_context",
]
MingliAssertionEpistemicStatus = Literal[
    "fact",
    "derived",
    "hypothesis",
    "interpretation",
    "unresolved",
]
ProfessionalIssueSeverity = Literal["hard", "major", "minor", "warning"]
ProfessionalIssueDisposition = Literal[
    "hard_block",
    "domain_block",
    "suppress",
    "manual_review",
]
ProfessionalBlockScope = Literal["core", "domain", "assertion"]
ProfessionalRawSourceKind = Literal[
    "model_payload",
    "assertion_gate_original_chunks",
    "fixture_raw_payload",
    "deterministic_system_payload",
]


class AssertionSourceSpan(V50Model):
    field_path: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_span(self) -> "AssertionSourceSpan":
        if self.end < self.start:
            raise ValueError("assertion_source_span_reversed")
        return self


class MingliAssertion(V50Model):
    """One immutable proposition extracted from a cognitive source payload."""

    version: str = "deepbazi.mingli_assertion.v1"
    assertion_id: str
    cognitive_record_ref: str
    source_text: str
    source_span: AssertionSourceSpan
    source_hash: str
    assertion_type: MingliAssertionType
    modality: MingliAssertionModality
    scope: MingliAssertionScope
    subject_refs: list[str] = Field(default_factory=list)
    predicate: str = ""
    object_refs: list[str] = Field(default_factory=list)
    hypothesis_ref: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    counter_evidence_refs: list[str] = Field(default_factory=list)
    epistemic_status: MingliAssertionEpistemicStatus
    impact_scope: ProfessionalBlockScope = "assertion"
    domain: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)


class ProfessionalIntegrityIssue(V50Model):
    version: str = "deepbazi.professional_integrity_issue.v1"
    issue_id: str
    assertion_ref: str
    tier: Literal[0, 1, 2, 3, 4]
    issue_class: str
    severity: ProfessionalIssueSeverity
    disposition: ProfessionalIssueDisposition
    block_scope: ProfessionalBlockScope
    domain: str = ""
    message: str
    canonical_refs: list[str] = Field(default_factory=list)


class ProfessionalScopeBlock(V50Model):
    scope: ProfessionalBlockScope
    scope_ref: str
    reason_issue_refs: list[str] = Field(default_factory=list)
    downstream_domains_blocked: bool = False


class ProfessionalReviewOverlay(V50Model):
    """Immutable review verdict layered over an untouched cognitive record."""

    version: str = "deepbazi.professional_review_overlay.v1"
    overlay_id: str
    cognitive_record_ref: str
    review_version: str = "assertion_integrity_gate.v1"
    assertions_hash: str
    raw_output_hash: str
    raw_source_kind: ProfessionalRawSourceKind = "model_payload"
    persistence_status: PersistenceStatus
    professional_release_status: ProfessionalReleaseStatus
    reviewed_assertion_refs: list[str] = Field(default_factory=list)
    blocked_assertion_refs: list[str] = Field(default_factory=list)
    suppressed_assertion_refs: list[str] = Field(default_factory=list)
    issues: list[ProfessionalIntegrityIssue] = Field(default_factory=list)
    hard_error_count: int = Field(default=0, ge=0)
    major_error_count: int = Field(default=0, ge=0)
    minor_error_count: int = Field(default=0, ge=0)
    scope_blocks: list[ProfessionalScopeBlock] = Field(default_factory=list)
    downstream_domains_blocked: bool = False
    reviewer: str
    created_at: str
    raw_output_modified: Literal[False] = False

    @model_validator(mode="after")
    def validate_release_boundary(self) -> "ProfessionalReviewOverlay":
        issue_refs = {item.assertion_ref for item in self.issues}
        if not set(self.blocked_assertion_refs).issubset(issue_refs):
            raise ValueError("blocked_assertion_without_review_issue")
        if not set(self.suppressed_assertion_refs).issubset(issue_refs):
            raise ValueError("suppressed_assertion_without_review_issue")
        if self.professional_release_status == "passed" and (
            self.blocked_assertion_refs or self.suppressed_assertion_refs
        ):
            raise ValueError("passed_overlay_cannot_contain_blocked_assertions")
        return self


class ProfessionalReviewBundle(V50Model):
    version: str = "deepbazi.professional_review_bundle.v1"
    assertions: list[MingliAssertion]
    overlay: ProfessionalReviewOverlay


__all__ = [
    "AssertionSourceSpan",
    "MingliAssertion",
    "MingliAssertionEpistemicStatus",
    "MingliAssertionModality",
    "MingliAssertionScope",
    "MingliAssertionType",
    "PersistenceStatus",
    "ProfessionalBlockScope",
    "ProfessionalIntegrityIssue",
    "ProfessionalIssueDisposition",
    "ProfessionalIssueSeverity",
    "ProfessionalRawSourceKind",
    "ProfessionalReleaseStatus",
    "ProfessionalReviewBundle",
    "ProfessionalReviewOverlay",
    "ProfessionalScopeBlock",
]
