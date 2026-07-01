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
    HIDDEN_ATTRIBUTE = "hidden_attribute"
    TRAINABLE_UNIT = "trainable_unit"
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
    also_supports: list[str] = Field(default_factory=list)
    weakens: list[str] = Field(default_factory=list)
    affected_trainable_refs: list[str] = Field(default_factory=list)
    strength: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    created_by_role: RoleKey = "user"
    local_only: bool = True
    requires_batch_review: bool = False
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
        if not self.local_only and not self.requires_batch_review:
            raise ValueError("non-local TrainingLabelEvent requires batch review")
        return self


class TrainableUnitType(str, Enum):
    SOURCE_WEIGHT = "source_weight"
    RULE_WEIGHT = "rule_weight"
    PATH_WEIGHT = "path_weight"
    CLAIM_SCORE = "claim_score"
    CONFLICT_POLICY = "conflict_policy"
    ASSERTION_THRESHOLD = "assertion_threshold"
    ADVICE_PRIORITY = "advice_priority"
    PROBE_VOI = "probe_voi"
    LLM_ACCEPTANCE = "llm_acceptance"


class TrainableUpdateScope(str, Enum):
    LOCAL_OVERLAY = "local_overlay"
    CANDIDATE_POLICY = "candidate_policy"
    GLOBAL_POLICY = "global_policy"


class TrainableUnit(V40Model):
    version: str = "v40.trainable_unit.v1"
    unit_id: str
    module: str
    unit_type: TrainableUnitType
    domain: Topic = Topic.UNKNOWN
    claim_key: str = ""
    default_value: float = Field(default=0.0)
    current_value: float = Field(default=0.0)
    min_value: float = Field(default=0.0)
    max_value: float = Field(default=1.0)
    update_scope: TrainableUpdateScope = TrainableUpdateScope.LOCAL_OVERLAY
    policy_version: str = "baseline"
    enabled: bool = True
    chart_fact_mutation_allowed: bool = False
    boundary: str = "trainable_unit_tunes_policy_not_chart_facts"

    @model_validator(mode="after")
    def _trainable_unit_boundary(self) -> "TrainableUnit":
        if not self.unit_id.strip():
            raise ValueError("TrainableUnit requires unit_id")
        if not self.module.strip():
            raise ValueError("TrainableUnit requires module")
        if "fact" in self.module.lower():
            raise ValueError("TrainableUnit cannot target fact modules")
        if self.min_value >= self.max_value:
            raise ValueError("TrainableUnit requires min_value < max_value")
        if not self.min_value <= self.default_value <= self.max_value:
            raise ValueError("TrainableUnit default_value outside bounds")
        if not self.min_value <= self.current_value <= self.max_value:
            raise ValueError("TrainableUnit current_value outside bounds")
        if self.chart_fact_mutation_allowed:
            raise ValueError("TrainableUnit cannot mutate chart facts")
        return self


class TrainablePolicyRegistry(V40Model):
    version: str = "v40.trainable_policy_registry.v1"
    registry_id: str
    active_policy_version: str
    candidate_policy_version: str = ""
    units: list[TrainableUnit] = Field(default_factory=list)
    immutable_fact_modules: list[str] = Field(
        default_factory=lambda: [
            "bazi_fact_engine_pro",
            "ziwei_fact_engine",
            "solar_term_policy",
            "luck_start_policy",
            "true_solar_time_policy",
        ]
    )
    release_gate_required_for_global: bool = True
    chart_fact_mutation_allowed: bool = False
    direct_global_update_allowed: bool = False
    boundary: str = "trainable_policy_registry_versioned_replayable_and_fact_immutable"

    @model_validator(mode="after")
    def _registry_boundary(self) -> "TrainablePolicyRegistry":
        if not self.registry_id.strip():
            raise ValueError("TrainablePolicyRegistry requires registry_id")
        if not self.active_policy_version.strip():
            raise ValueError("TrainablePolicyRegistry requires active_policy_version")
        unit_ids = [unit.unit_id for unit in self.units]
        if len(unit_ids) != len(set(unit_ids)):
            raise ValueError("TrainablePolicyRegistry requires unique unit_id")
        if self.chart_fact_mutation_allowed:
            raise ValueError("TrainablePolicyRegistry cannot mutate chart facts")
        if self.direct_global_update_allowed:
            raise ValueError("TrainablePolicyRegistry cannot allow direct global update")
        if any("fact" in module.lower() for module in self.immutable_fact_modules) is False:
            raise ValueError("TrainablePolicyRegistry must declare immutable fact modules")
        return self


class TrainingAttribution(V40Model):
    version: str = "v40.training_attribution.v1"
    attribution_id: str
    label_event_id: str
    affected_signal_ids: list[str] = Field(default_factory=list)
    affected_trainable_refs: list[str] = Field(default_factory=list)
    affected_branch_ids: list[str] = Field(default_factory=list)
    affected_verdict_ids: list[str] = Field(default_factory=list)
    affected_advice_ids: list[str] = Field(default_factory=list)
    affected_probe_ids: list[str] = Field(default_factory=list)
    attribution_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    update_scope: TrainableUpdateScope = TrainableUpdateScope.LOCAL_OVERLAY
    release_gate_required: bool = True
    chart_fact_mutation_allowed: bool = False
    boundary: str = "training_attribution_maps_feedback_to_policy_units_without_mutating_facts"

    @model_validator(mode="after")
    def _attribution_boundary(self) -> "TrainingAttribution":
        if not self.attribution_id.strip():
            raise ValueError("TrainingAttribution requires attribution_id")
        if not self.label_event_id.strip():
            raise ValueError("TrainingAttribution requires label_event_id")
        affected = (
            self.affected_signal_ids
            + self.affected_trainable_refs
            + self.affected_branch_ids
            + self.affected_verdict_ids
            + self.affected_advice_ids
            + self.affected_probe_ids
        )
        if not affected:
            raise ValueError("TrainingAttribution requires affected targets")
        if self.update_scope == TrainableUpdateScope.GLOBAL_POLICY and not self.release_gate_required:
            raise ValueError("global TrainingAttribution requires release gate")
        if self.chart_fact_mutation_allowed:
            raise ValueError("TrainingAttribution cannot mutate chart facts")
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


class WeightActivationExecution(V40Model):
    version: str = "v40.weight_activation_execution.v1"
    execution_id: str
    review_id: str
    weight_version_id: str
    release_readiness_id: str
    rollback_version_id: str
    executed_by_role: RoleKey = "admin"
    review_decision: ReleaseRecommendation = ReleaseRecommendation.NEEDS_REVIEW
    deactivated_weight_ids: list[str] = Field(default_factory=list)
    activation_applied: bool = True
    v40_weight_write_applied: bool = True
    v30_state_mutated: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "weight_activation_execution_requires_explicit_review_and_rollback_without_v30_mutation"

    @model_validator(mode="after")
    def _activation_execution_boundary(self) -> "WeightActivationExecution":
        if not self.execution_id.strip():
            raise ValueError("WeightActivationExecution requires execution_id")
        if not self.rollback_version_id.strip():
            raise ValueError("WeightActivationExecution requires rollback_version_id")
        if self.executed_by_role != "admin":
            raise ValueError("WeightActivationExecution requires admin role")
        if self.review_decision != ReleaseRecommendation.APPROVE:
            raise ValueError("WeightActivationExecution requires approved review")
        if not self.activation_applied or not self.v40_weight_write_applied:
            raise ValueError("WeightActivationExecution records an applied V40 weight activation")
        if self.v30_state_mutated:
            raise ValueError("WeightActivationExecution cannot mutate V30 state")
        if self.chart_fact_mutation_allowed:
            raise ValueError("WeightActivationExecution cannot mutate chart facts")
        return self
