from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from core.contracts.base import V50Model
from core.contracts.professional_review import (
    PersistenceStatus,
    ProfessionalReleaseStatus,
    ProfessionalReviewOverlay,
)
from core.graph.provenance import (
    AssertionLifecycle,
    PathAssertion,
    RelationAssertion,
    canonical_scene_scope_ref,
    validate_assertion_history,
)


InsightType = Literal[
    "baseline",
    "temporal_prior",
    "domain_analysis",
    "decision_support",
    "case_revision",
]
InsightStatus = Literal[
    "draft",
    "partial",
    "reviewed",
    "committed",
    "failed",
    "superseded",
    "rejected",
    "validated",  # Legacy read compatibility; new runs use reviewed.
]
class InsightBasis(V50Model):
    chart_fact_refs: list[str] = Field(default_factory=list)
    holistic_belief_refs: list[str] = Field(default_factory=list)
    temporal_activation_refs: list[str] = Field(default_factory=list)
    reality_context_refs: list[str] = Field(default_factory=list)


class ReasoningPathStep(V50Model):
    premise: str
    conclusion: str
    source_refs: list[str] = Field(default_factory=list)


class InsightUncertainty(V50Model):
    level: Literal["low", "medium", "high"]
    reasons: list[str] = Field(default_factory=list)
    competing_hypotheses: list[str] = Field(default_factory=list)


class InsightNextAction(V50Model):
    text: str
    category: Literal["observe", "reflect", "prepare", "seek_professional_help"]
    risk_level: Literal["low", "medium", "high"] = "low"


class InsightProvenance(V50Model):
    reasoner_id: str
    reasoner_version: str
    theory_version: str
    model_version: str
    context_hash: str
    generated_at: str
    source_record_id: str


class FormalInsight(V50Model):
    version: str = "deepbazi.formal_insight.v1"
    insight_id: str
    case_id: str
    case_version: str
    type: InsightType
    claim: str
    scope: dict[str, Any] = Field(default_factory=dict)
    basis: InsightBasis
    reasoning_path: list[ReasoningPathStep]
    conditions: list[str] = Field(default_factory=list)
    expected_manifestations: list[str] = Field(default_factory=list)
    counter_signals: list[str] = Field(default_factory=list)
    uncertainty: InsightUncertainty
    next_action: InsightNextAction | None = None
    provenance: InsightProvenance
    status: InsightStatus = "draft"
    persistence_status: PersistenceStatus = "draft"
    professional_release_status: ProfessionalReleaseStatus = "unreviewed"
    professional_review_overlay: ProfessionalReviewOverlay | None = None
    epistemic_state: Literal["reliable", "competing", "blocked", "legacy_unreviewed"] = "legacy_unreviewed"
    source_review_gate: str = "legacy"
    source_review_issue_codes: list[str] = Field(default_factory=list)
    strategy_dimensions: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    baseline_insight_id: str = ""
    baseline_record_id: str = ""
    baseline_semantic_signature: str = ""
    projection_payload: dict[str, Any] = Field(default_factory=dict)


class InsightValidationReceipt(V50Model):
    passed: bool
    insight_id: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checked_at: str
    fact_traceability_rate: float = Field(ge=0.0, le=1.0)
    chart_version_matches: bool = True
    epistemic_state: Literal["reliable", "competing", "blocked", "legacy_unreviewed"] = "legacy_unreviewed"
    baseline_reference_matches: bool = True


class ChartVersionRef(V50Model):
    version_id: str
    world_id: str
    chart_hash: str
    created_at: str
    active: bool = True


class LifeCaseRevision(V50Model):
    revision_id: str
    kind: Literal[
        "baseline_committed",
        "chart_version_changed",
        "temporal_prior_committed",
        "domain_insight_committed",
        "reality_evidence_added",
        "reality_evidence_updated",
        "temporal_snapshot_selected",
        "monthly_review_completed",
        "case_revision_candidate_created",
        "case_revision_committed",
    ]
    created_at: str
    insight_id: str = ""
    summary: str
    chart_facts_modified: bool = False
    global_theory_modified: bool = False


class RealityEvidenceRevision(V50Model):
    revision_id: str
    revision_number: int = Field(ge=1)
    changed_at: str
    changed_by: str = "user"
    summary: str


class RealityEvidence(V50Model):
    version: str = "deepbazi.reality_evidence.v1"
    evidence_id: str
    idempotency_key: str
    case_id: str
    case_version_at_recording: str
    source: Literal[
        "page",
        "abu",
        "probe",
        "monthly_review",
        "practitioner",
        "research",
        "import",
    ]
    source_ref: str = ""
    kind: str = "life_event"
    summary: str
    domain: str = "whole_chart"
    period_key: str
    occurred_at: str = ""
    recorded_at: str
    updated_at: str
    confirmation_status: Literal["reported", "confirmed", "corrected", "withdrawn"] = "reported"
    severity: Literal["low", "medium", "high", "unknown"] = "unknown"
    subjective_impact: str = ""
    structured_payload: dict[str, Any] = Field(default_factory=dict)
    revision_number: int = Field(default=1, ge=1)
    revisions: list[RealityEvidenceRevision] = Field(default_factory=list)
    case_local_only: bool = True
    chart_facts_modified: bool = False
    global_theory_modified: bool = False


class TemporalSnapshot(V50Model):
    version: str = "deepbazi.temporal_snapshot.v1"
    snapshot_id: str
    case_id: str
    case_version: str
    chart_version_id: str
    period_key: str
    system_period_key: str
    perspective: Literal["past", "current", "future"]
    baseline_insight_id: str
    temporal_insight_id: str = ""
    reality_evidence_refs: list[str] = Field(default_factory=list)
    observation_theme: str
    summary: str
    conditions: list[str] = Field(default_factory=list)
    counter_signals: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    implementation_fingerprint: str
    generated_at: str
    status: Literal["active", "superseded"] = "active"


MonthlyReviewVerdict = Literal[
    "supported",
    "partially_supported",
    "not_observed",
    "contradicted",
    "insufficient_evidence",
]


class MonthlyReview(V50Model):
    version: str = "deepbazi.monthly_review.v1"
    review_id: str
    case_id: str
    case_version: str
    period_key: str
    temporal_snapshot_id: str
    evidence_refs: list[str] = Field(default_factory=list)
    verdict: MonthlyReviewVerdict
    user_note: str = ""
    system_summary: str
    status: Literal["completed", "withdrawn"] = "completed"
    created_at: str
    updated_at: str


class CaseRevisionCandidate(V50Model):
    version: str = "deepbazi.case_revision_candidate.v1"
    candidate_id: str
    case_id: str
    from_case_version: str
    to_case_version: str
    monthly_review_id: str
    period_key: str
    prior_insight_refs: list[str] = Field(default_factory=list)
    reality_evidence_refs: list[str] = Field(default_factory=list)
    proposed_claim: str
    preserved_claims: list[str] = Field(default_factory=list)
    uncertainty_change: str
    reliability_state: Literal["eligible", "blocked"] = "eligible"
    status: Literal["pending", "committed", "withdrawn"] = "pending"
    created_at: str


class LifeCaseVersionSnapshot(V50Model):
    snapshot_id: str
    case_version: str
    baseline_insight_id: str
    domain_insight_ids: list[str] = Field(default_factory=list)
    temporal_snapshot_ids: list[str] = Field(default_factory=list)
    reality_evidence_refs: list[str] = Field(default_factory=list)
    case_revision_ids: list[str] = Field(default_factory=list)
    status: Literal["superseded", "archived"] = "superseded"
    created_at: str
    superseded_at: str


class LifeCase(V50Model):
    version: str = "deepbazi.life_case.v1"
    life_case_id: str
    case_id: str
    case_version: str = "v1"
    profile_id: str | None = None
    chart_version: ChartVersionRef
    baseline_insight: FormalInsight
    relation_assertions: list[RelationAssertion] = Field(default_factory=list)
    path_assertions: list[PathAssertion] = Field(default_factory=list)
    temporal_priors: list[FormalInsight] = Field(default_factory=list)
    domain_insights: dict[str, list[FormalInsight]] = Field(default_factory=dict)
    reality_evidence: list[RealityEvidence] = Field(default_factory=list)
    temporal_snapshots: list[TemporalSnapshot] = Field(default_factory=list)
    monthly_reviews: list[MonthlyReview] = Field(default_factory=list)
    case_revision_candidates: list[CaseRevisionCandidate] = Field(default_factory=list)
    case_revisions: list[FormalInsight] = Field(default_factory=list)
    version_history: list[LifeCaseVersionSnapshot] = Field(default_factory=list)
    revisions: list[LifeCaseRevision] = Field(default_factory=list)
    status: Literal["active", "superseded", "archived"] = "active"
    created_at: str
    updated_at: str

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_reality_evidence(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        rows = value.get("reality_evidence")
        if not isinstance(rows, list) or not rows:
            return value
        case_id = str(value.get("case_id") or "")
        case_version = str(value.get("case_version") or "v1")
        fallback_time = str(value.get("updated_at") or value.get("created_at") or "")
        migrated: list[Any] = []
        changed = False
        for item in rows:
            if not isinstance(item, dict) or item.get("version") == "deepbazi.reality_evidence.v1":
                migrated.append(item)
                continue
            evidence_id = str(item.get("evidence_id") or "legacy-evidence")
            recorded_at = str(item.get("recorded_at") or fallback_time)
            year_value = item.get("year_value")
            period_key = (
                f"{int(year_value):04d}-01"
                if isinstance(year_value, int)
                else recorded_at[:7]
                if len(recorded_at) >= 7
                else "unknown"
            )
            migrated.append({
                "evidence_id": evidence_id,
                "idempotency_key": f"legacy:{evidence_id}",
                "case_id": case_id,
                "case_version_at_recording": case_version,
                "source": "probe" if item.get("plan_id") else "import",
                "source_ref": str(item.get("source_probe_id") or item.get("plan_id") or ""),
                "kind": str(item.get("evidence_kind") or item.get("kind") or "life_event"),
                "summary": str(item.get("event_note") or item.get("option_label") or "历史现实记录"),
                "domain": str(item.get("domain") or "whole_chart"),
                "period_key": period_key,
                "occurred_at": "",
                "recorded_at": recorded_at,
                "updated_at": recorded_at,
                "confirmation_status": "reported",
                "severity": "unknown",
                "structured_payload": item,
            })
            changed = True
        return {**value, "reality_evidence": migrated} if changed else value

    @model_validator(mode="after")
    def validate_relation_path_authority(self) -> "LifeCase":
        relation_ids = [item.assertion_id for item in self.relation_assertions]
        path_ids = [item.assertion_id for item in self.path_assertions]
        if len(relation_ids) != len(set(relation_ids)):
            raise ValueError("life_case_duplicate_relation_assertion")
        if len(path_ids) != len(set(path_ids)):
            raise ValueError("life_case_duplicate_path_assertion")
        if any(item.status == AssertionLifecycle.CANDIDATE for item in self.relation_assertions):
            raise ValueError("life_case_cannot_own_candidate_relation")
        if any(item.status == AssertionLifecycle.CANDIDATE for item in self.path_assertions):
            raise ValueError("life_case_cannot_own_candidate_path")
        validate_assertion_history(self.relation_assertions)
        validate_assertion_history(self.path_assertions)
        scene_ref = canonical_scene_scope_ref(
            life_case_id=self.life_case_id,
            chart_version_id=self.chart_version.version_id,
        )
        if any(item.relation_key.scene_ref != scene_ref for item in self.relation_assertions):
            raise ValueError("life_case_relation_scene_scope_mismatch")
        if any(
            item.path_key is not None and item.path_key.scene_ref != scene_ref
            for item in self.path_assertions
        ):
            raise ValueError("life_case_path_scene_scope_mismatch")
        return self
