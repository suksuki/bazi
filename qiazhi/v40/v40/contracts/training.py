from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from v40.contracts.base import ReleaseRecommendation, RoleKey, Topic, V40Model


class LabelSource(str, Enum):
    USER_ANSWER = "user_answer"
    USER_FEEDBACK = "user_feedback"
    PRACTITIONER_SELECTION = "practitioner_selection"
    ADMIN_LABEL = "admin_label"
    GOLDEN_CASE = "golden_case"
    REAL_OUTCOME = "real_outcome"
    PROBE_ANSWER = "probe_answer"


class LabelTargetType(str, Enum):
    SIGNAL = "signal"
    CLAIM = "claim"
    BRANCH = "branch"
    VERDICT = "verdict"
    ADVICE = "advice"
    PROBE = "probe"
    LLM_OUTPUT = "llm_output"
    SURFACE = "surface"


class LabelValue(str, Enum):
    SUPPORTS = "supports"
    WEAKENS = "weakens"
    MATCHES_REALITY = "matches_reality"
    MISMATCH = "mismatch"
    OVERCLAIMED = "overclaimed"
    UNDERCLAIMED = "underclaimed"
    GOOD_ADVICE = "good_advice"
    BAD_ADVICE = "bad_advice"
    NEEDS_PROBE = "needs_probe"
    PROBE_HELPFUL = "probe_helpful"
    PROBE_USELESS = "probe_useless"
    EXPRESSION_GOOD = "expression_good"
    EXPRESSION_BAD = "expression_bad"


class TrainingLabelEvent(V40Model):
    version: str = "v40.training_label_event.v1"
    event_id: str
    reading_id: str
    source: LabelSource
    target_type: LabelTargetType
    target_ids: list[str]
    label: LabelValue
    strength: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    created_by_role: RoleKey = "user"
    local_only: bool = True
    chart_fact_mutation_allowed: bool = False
    boundary: str = "training_label_event_is_feedback_signal_not_chart_fact_or_direct_weight_write"

    @model_validator(mode="after")
    def _label_event_boundary(self) -> "TrainingLabelEvent":
        if not self.event_id.strip():
            raise ValueError("TrainingLabelEvent requires event_id")
        if not self.target_ids:
            raise ValueError("TrainingLabelEvent requires target_ids")
        if self.chart_fact_mutation_allowed:
            raise ValueError("TrainingLabelEvent cannot mutate chart facts")
        return self


class TrainingExampleV2(V40Model):
    version: str = "v40.training_example_v2.v1"
    example_id: str
    reading_id: str
    topic: Topic = Topic.UNKNOWN
    input_snapshot_ref: str = ""
    runtime_output_ref: str = ""
    label_events: list[TrainingLabelEvent] = Field(default_factory=list)
    attribution_targets: list[str] = Field(default_factory=list)
    expected_update: dict[str, object] = Field(default_factory=dict)
    global_update_allowed: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "training_example_collects_attribution_material_without_auto_global_update"

    @model_validator(mode="after")
    def _training_example_boundary(self) -> "TrainingExampleV2":
        if not self.example_id.strip():
            raise ValueError("TrainingExampleV2 requires example_id")
        if not self.label_events:
            raise ValueError("TrainingExampleV2 requires label_events")
        if self.global_update_allowed:
            raise ValueError("TrainingExampleV2 cannot directly allow global updates")
        if self.chart_fact_mutation_allowed:
            raise ValueError("TrainingExampleV2 cannot mutate chart facts")
        return self


class WeightChange(V40Model):
    target_id: str
    before: float
    after: float
    reason: str = ""


class ThresholdChange(V40Model):
    target_id: str
    before: float
    after: float
    reason: str = ""


class TrainingImpactDiff(V40Model):
    version: str = "v40.training_impact_diff.v1"
    training_run_id: str
    base_version: str
    candidate_version: str
    changed_weights: list[WeightChange] = Field(default_factory=list)
    changed_thresholds: list[ThresholdChange] = Field(default_factory=list)
    changed_probe_policies: list[str] = Field(default_factory=list)
    changed_advice_priorities: list[str] = Field(default_factory=list)
    affected_signals: list[str] = Field(default_factory=list)
    affected_branches: list[str] = Field(default_factory=list)
    affected_verdicts: list[str] = Field(default_factory=list)
    affected_advice: list[str] = Field(default_factory=list)
    affected_probes: list[str] = Field(default_factory=list)
    golden_case_diff: dict[str, object] = Field(default_factory=dict)
    regression_failures: list[str] = Field(default_factory=list)
    improvement_summary: list[str] = Field(default_factory=list)
    risk_summary: list[str] = Field(default_factory=list)
    release_recommendation: ReleaseRecommendation = ReleaseRecommendation.NEEDS_REVIEW
    production_write_allowed: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "training_impact_diff_explains_candidate_update_without_writing_production"

    @model_validator(mode="after")
    def _impact_boundary(self) -> "TrainingImpactDiff":
        if self.production_write_allowed:
            raise ValueError("TrainingImpactDiff cannot write production directly")
        if self.chart_fact_mutation_allowed:
            raise ValueError("TrainingImpactDiff cannot mutate chart facts")
        if self.release_recommendation == ReleaseRecommendation.APPROVE and self.regression_failures:
            raise ValueError("TrainingImpactDiff cannot approve with regression failures")
        return self


class LocalOverlay(V40Model):
    version: str = "v40.local_overlay.v1"
    overlay_id: str
    reading_id: str
    label_event_ids: list[str] = Field(default_factory=list)
    affected_target_ids: list[str] = Field(default_factory=list)
    expires_after_reading: bool = True
    global_update_allowed: bool = False
    boundary: str = "local_overlay_updates_current_reading_only"

    @model_validator(mode="after")
    def _local_overlay_boundary(self) -> "LocalOverlay":
        if self.global_update_allowed:
            raise ValueError("LocalOverlay cannot allow global update")
        return self


class GlobalWeightVersion(V40Model):
    version: str = "v40.global_weight_version.v1"
    weight_version_id: str
    source_training_run_id: str
    release_gate_id: str
    active: bool = False
    rollback_version_id: str = ""
    boundary: str = "global_weight_version_requires_release_gate_before_activation"


class WeightActivationReview(V40Model):
    version: str = "v40.weight_activation_review.v1"
    review_id: str
    weight_version_id: str
    release_readiness_id: str
    reviewed_by_role: RoleKey = "admin"
    decision: ReleaseRecommendation = ReleaseRecommendation.NEEDS_REVIEW
    reasons: list[str] = Field(default_factory=list)
    activation_applied: bool = False
    production_write_allowed: bool = False
    boundary: str = "weight_activation_review_records_decision_without_applying_activation"

    @model_validator(mode="after")
    def _activation_review_boundary(self) -> "WeightActivationReview":
        if not self.review_id.strip():
            raise ValueError("WeightActivationReview requires review_id")
        if not self.weight_version_id.strip():
            raise ValueError("WeightActivationReview requires weight_version_id")
        if not self.release_readiness_id.strip():
            raise ValueError("WeightActivationReview requires release_readiness_id")
        if self.activation_applied:
            raise ValueError("WeightActivationReview cannot apply activation directly")
        if self.production_write_allowed:
            raise ValueError("WeightActivationReview cannot write production policy")
        return self
