from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from v40.contracts.base import AssertionLevel, ReleaseRecommendation, Topic, V40Model
from v40.contracts.chart import BaziChartFacts, BirthInputCanonical, ZiweiChartFacts
from v40.contracts.context import RuntimeContext
from v40.contracts.output import ExpressionTelemetry
from v40.contracts.training import TrainingExampleV2


class EvaluationCaseType(str, Enum):
    SYNTHETIC = "synthetic"
    GOLDEN = "golden"
    REAL_FEEDBACK = "real_feedback"
    REGRESSION = "regression"
    SHADOW_COMPARE = "shadow_compare"


class EvaluationStatus(str, Enum):
    PASSED = "passed"
    REVIEW = "review"
    BLOCKED = "blocked"


class ExpectedSignal(V40Model):
    version: str = "v40.expected_signal.v1"
    source: str = ""
    topic: Topic = Topic.UNKNOWN
    claim_keywords: list[str] = Field(default_factory=list)
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    required: bool = True


class ExpectedVerdict(V40Model):
    version: str = "v40.expected_verdict.v1"
    topic: Topic = Topic.UNKNOWN
    allowed_assertion_levels: list[AssertionLevel] = Field(
        default_factory=lambda: [
            AssertionLevel.CONFIRMED,
            AssertionLevel.SUPPORTED,
            AssertionLevel.MIXED,
            AssertionLevel.WEAK_CANDIDATE,
        ]
    )
    min_evidence_count: int = Field(default=1, ge=0)
    expected_keywords: list[str] = Field(default_factory=list)
    requires_conflict_handling: bool = False


class ExpectedAdvice(V40Model):
    version: str = "v40.expected_advice.v1"
    topic: Topic = Topic.UNKNOWN
    must_include_any: list[str] = Field(default_factory=list)
    requires_action: bool = True
    requires_avoid: bool = False
    requires_condition: bool = False


class ExpectedProbe(V40Model):
    version: str = "v40.expected_probe.v1"
    topic: Topic = Topic.UNKNOWN
    target: str = ""
    expected_keywords: list[str] = Field(default_factory=list)
    required: bool = False


class ForbiddenAssertion(V40Model):
    version: str = "v40.forbidden_assertion.v1"
    text: str
    severity: str = "high"
    reason: str = ""


class EvaluationCaseSpec(V40Model):
    version: str = "v40.evaluation_case_spec.v1"
    case_id: str
    case_type: EvaluationCaseType = EvaluationCaseType.GOLDEN
    user_question: str = ""
    topic: Topic = Topic.OVERVIEW
    known_reality: dict[str, object] = Field(default_factory=dict)
    runtime_context: RuntimeContext | None = None
    context_variants: list[RuntimeContext] = Field(default_factory=list)
    expert_notes: list[str] = Field(default_factory=list)
    expected_signals: list[ExpectedSignal] = Field(default_factory=list)
    expected_verdicts: list[ExpectedVerdict] = Field(default_factory=list)
    expected_advice: list[ExpectedAdvice] = Field(default_factory=list)
    expected_probes: list[ExpectedProbe] = Field(default_factory=list)
    allowed_assertions: list[str] = Field(default_factory=list)
    forbidden_assertions: list[ForbiddenAssertion] = Field(default_factory=list)
    chart_fact_mutation_allowed: bool = False
    boundary: str = "evaluation_case_spec_defines_measurement_contract_not_runtime_policy"

    @model_validator(mode="after")
    def _case_spec_boundary(self) -> "EvaluationCaseSpec":
        if not self.case_id.strip():
            raise ValueError("EvaluationCaseSpec requires case_id")
        if not self.expected_verdicts:
            raise ValueError("EvaluationCaseSpec requires expected_verdicts")
        if not self.forbidden_assertions:
            raise ValueError("EvaluationCaseSpec requires forbidden_assertions")
        if self.chart_fact_mutation_allowed:
            raise ValueError("EvaluationCaseSpec cannot allow chart fact mutation")
        return self


class GoldenCase(EvaluationCaseSpec):
    version: str = "v40.golden_case.v1"
    case_type: EvaluationCaseType = EvaluationCaseType.GOLDEN
    expert_reviewer: str = ""
    quality_tier: str = "draft"


class MetricSummary(V40Model):
    version: str = "v40.metric_summary.v1"
    case_id: str
    reading_id: str
    evidence_coverage_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    overclaim_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    assertion_calibration_score: float = Field(default=0.0, ge=0.0, le=1.0)
    conflict_resolution_score: float = Field(default=0.0, ge=0.0, le=1.0)
    advice_grounding_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    probe_yield_score: float = Field(default=0.0, ge=0.0, le=1.0)
    llm_boundary_violation_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    expression_acceptance_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    expression_thinking_trace_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    ziwei_sidecar_signal_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    cross_engine_topic_agreement_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    surface_leakage_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: EvaluationStatus = EvaluationStatus.REVIEW
    failed_reasons: list[str] = Field(default_factory=list)
    boundary: str = "metric_summary_combines_structured_evaluation_without_llm_as_judge"


class ReleaseGateResult(V40Model):
    version: str = "v40.release_gate_result.v1"
    gate_id: str
    candidate_version: str
    fact_gate_passed: bool = False
    golden_case_gate_passed: bool = False
    overclaim_gate_passed: bool = False
    advice_grounding_gate_passed: bool = False
    probe_yield_gate_passed: bool = False
    llm_boundary_gate_passed: bool = False
    leakage_gate_passed: bool = False
    regression_failures: list[str] = Field(default_factory=list)
    recommendation: ReleaseRecommendation = ReleaseRecommendation.NEEDS_REVIEW
    production_write_allowed: bool = False
    boundary: str = "release_gate_result_must_pass_all_gates_before_production_write"

    @model_validator(mode="after")
    def _release_gate_boundary(self) -> "ReleaseGateResult":
        gates = [
            self.fact_gate_passed,
            self.golden_case_gate_passed,
            self.overclaim_gate_passed,
            self.advice_grounding_gate_passed,
            self.probe_yield_gate_passed,
            self.llm_boundary_gate_passed,
            self.leakage_gate_passed,
        ]
        if self.recommendation == ReleaseRecommendation.APPROVE and (not all(gates) or self.regression_failures):
            raise ValueError("ReleaseGateResult cannot approve unless all gates pass and regressions are empty")
        if self.production_write_allowed and self.recommendation != ReleaseRecommendation.APPROVE:
            raise ValueError("Production write requires approved release gate")
        return self


class EvaluationRunResult(V40Model):
    version: str = "v40.evaluation_run_result.v1"
    run_id: str
    case_spec: EvaluationCaseSpec
    reading_id: str
    metric_summary: MetricSummary
    release_gate: ReleaseGateResult | None = None
    expression_telemetry: ExpressionTelemetry | None = None
    status: EvaluationStatus = EvaluationStatus.REVIEW
    chart_fact_mutation_allowed: bool = False
    production_write_allowed: bool = False
    boundary: str = "evaluation_run_result_is_sidecar_and_never_changes_user_result"

    @model_validator(mode="after")
    def _evaluation_run_boundary(self) -> "EvaluationRunResult":
        if self.chart_fact_mutation_allowed:
            raise ValueError("EvaluationRunResult cannot mutate chart facts")
        if self.production_write_allowed:
            raise ValueError("EvaluationRunResult cannot write production policy")
        return self


class EvaluationBatchSummary(V40Model):
    version: str = "v40.evaluation_batch_summary.v1"
    batch_id: str
    candidate_version: str
    case_count: int = Field(default=0, ge=0)
    run_ids: list[str] = Field(default_factory=list)
    passed_count: int = Field(default=0, ge=0)
    review_count: int = Field(default=0, ge=0)
    blocked_count: int = Field(default=0, ge=0)
    average_overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    failed_reason_counts: dict[str, int] = Field(default_factory=dict)
    recommendation: ReleaseRecommendation = ReleaseRecommendation.NEEDS_REVIEW
    production_write_allowed: bool = False
    boundary: str = "evaluation_batch_summary_aggregates_metrics_without_production_write"

    @model_validator(mode="after")
    def _batch_boundary(self) -> "EvaluationBatchSummary":
        if not self.batch_id.strip():
            raise ValueError("EvaluationBatchSummary requires batch_id")
        if self.case_count != len(self.run_ids):
            raise ValueError("EvaluationBatchSummary case_count must match run_ids")
        if self.passed_count + self.review_count + self.blocked_count != self.case_count:
            raise ValueError("EvaluationBatchSummary status counts must match case_count")
        if self.production_write_allowed:
            raise ValueError("EvaluationBatchSummary cannot write production policy")
        return self


class ObservedLifeEvent(V40Model):
    version: str = "v40.observed_life_event.v1"
    event_id: str
    topic: Topic = Topic.UNKNOWN
    year: str = ""
    description: str
    evidence_tags: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    privacy_level: str = "private"
    boundary: str = "observed_life_event_is_case_evidence_not_chart_fact"

    @model_validator(mode="after")
    def _life_event_boundary(self) -> "ObservedLifeEvent":
        if not self.event_id.strip():
            raise ValueError("ObservedLifeEvent requires event_id")
        if not self.description.strip():
            raise ValueError("ObservedLifeEvent requires description")
        return self


class ExpectedMingliOutcome(V40Model):
    version: str = "v40.expected_mingli_outcome.v1"
    topic: Topic = Topic.UNKNOWN
    verdict_keywords: list[str] = Field(default_factory=list)
    advice_keywords: list[str] = Field(default_factory=list)
    requires_probe: bool = False
    requires_conflict_handling: bool = False
    min_evidence_count: int = Field(default=1, ge=0)
    observed_event_refs: list[str] = Field(default_factory=list)
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    boundary: str = "expected_mingli_outcome_defines_acceptance_target_not_verdict_source"

    @model_validator(mode="after")
    def _outcome_boundary(self) -> "ExpectedMingliOutcome":
        if not self.verdict_keywords and not self.advice_keywords:
            raise ValueError("ExpectedMingliOutcome requires verdict or advice keywords")
        return self


class PractitionerJudgment(V40Model):
    version: str = "v40.practitioner_judgment.v1"
    judgment_id: str
    reviewer_role: str = "practitioner"
    summary: str
    accepted_topics: list[Topic] = Field(default_factory=list)
    rejected_claims: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    boundary: str = "practitioner_judgment_guides_acceptance_not_runtime_fact_mutation"

    @model_validator(mode="after")
    def _judgment_boundary(self) -> "PractitionerJudgment":
        if not self.judgment_id.strip():
            raise ValueError("PractitionerJudgment requires judgment_id")
        if not self.summary.strip():
            raise ValueError("PractitionerJudgment requires summary")
        return self


class AcceptanceRubric(V40Model):
    version: str = "v40.acceptance_rubric.v1"
    min_verdict_match_score: float = Field(default=0.72, ge=0.0, le=1.0)
    min_advice_grounding_score: float = Field(default=0.68, ge=0.0, le=1.0)
    min_domain_coverage_score: float = Field(default=0.65, ge=0.0, le=1.0)
    min_probe_usefulness_score: float = Field(default=0.55, ge=0.0, le=1.0)
    min_llm_expression_clarity_score: float = Field(default=0.70, ge=0.0, le=1.0)
    max_overclaim_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    boundary: str = "acceptance_rubric_sets_measurement_thresholds_without_activating_policy"


class RealCaseRecord(V40Model):
    version: str = "v40.real_case_record.v1"
    case_id: str
    display_name: str = ""
    user_question: str
    topic: Topic = Topic.OVERVIEW
    chart_facts: BaziChartFacts | None = None
    birth_input: BirthInputCanonical | None = None
    ziwei_chart_facts: ZiweiChartFacts | None = None
    observed_events: list[ObservedLifeEvent] = Field(default_factory=list)
    expected_outcomes: list[ExpectedMingliOutcome]
    practitioner_judgments: list[PractitionerJudgment] = Field(default_factory=list)
    forbidden_assertions: list[ForbiddenAssertion]
    rubric: AcceptanceRubric = Field(default_factory=AcceptanceRubric)
    tags: list[str] = Field(default_factory=list)
    privacy_level: str = "private"
    allow_training_use: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "real_case_record_is_acceptance_material_not_runtime_policy_or_public_user_data"

    @model_validator(mode="after")
    def _real_case_boundary(self) -> "RealCaseRecord":
        if not self.case_id.strip():
            raise ValueError("RealCaseRecord requires case_id")
        if not self.user_question.strip():
            raise ValueError("RealCaseRecord requires user_question")
        if not self.expected_outcomes:
            raise ValueError("RealCaseRecord requires expected_outcomes")
        if not self.forbidden_assertions:
            raise ValueError("RealCaseRecord requires forbidden_assertions")
        if self.chart_fact_mutation_allowed:
            raise ValueError("RealCaseRecord cannot allow chart fact mutation")
        return self

    def to_evaluation_case(self) -> EvaluationCaseSpec:
        return EvaluationCaseSpec(
            case_id=self.case_id,
            case_type=EvaluationCaseType.REAL_FEEDBACK,
            user_question=self.user_question,
            topic=self.topic,
            known_reality={
                "observed_events": [event.model_dump(mode="json") for event in self.observed_events],
                "practitioner_judgments": [
                    judgment.model_dump(mode="json") for judgment in self.practitioner_judgments
                ],
                "privacy_level": self.privacy_level,
                "allow_training_use": self.allow_training_use,
            },
            expected_verdicts=[
                ExpectedVerdict(
                    topic=outcome.topic,
                    expected_keywords=outcome.verdict_keywords,
                    min_evidence_count=outcome.min_evidence_count,
                    requires_conflict_handling=outcome.requires_conflict_handling,
                )
                for outcome in self.expected_outcomes
            ],
            expected_advice=[
                ExpectedAdvice(topic=outcome.topic, must_include_any=outcome.advice_keywords)
                for outcome in self.expected_outcomes
                if outcome.advice_keywords
            ],
            expected_probes=[
                ExpectedProbe(
                    topic=outcome.topic,
                    expected_keywords=outcome.verdict_keywords + outcome.advice_keywords,
                    required=outcome.requires_probe,
                )
                for outcome in self.expected_outcomes
                if outcome.requires_probe
            ],
            forbidden_assertions=self.forbidden_assertions,
            expert_notes=[judgment.summary for judgment in self.practitioner_judgments],
        )


class AcceptanceWindowCaseResult(V40Model):
    version: str = "v40.acceptance_window_case_result.v1"
    case_id: str
    run_id: str
    reading_id: str
    verdict_match_score: float = Field(default=0.0, ge=0.0, le=1.0)
    advice_grounding_score: float = Field(default=0.0, ge=0.0, le=1.0)
    overclaim_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    domain_coverage_score: float = Field(default=0.0, ge=0.0, le=1.0)
    probe_usefulness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    llm_expression_clarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: EvaluationStatus = EvaluationStatus.REVIEW
    failed_reasons: list[str] = Field(default_factory=list)
    trainable_attribution_hints: list[str] = Field(default_factory=list)
    boundary: str = "acceptance_window_case_result_scores_real_case_without_runtime_mutation"


class AcceptanceWindowResult(V40Model):
    version: str = "v40.acceptance_window_result.v1"
    window_id: str
    candidate_version: str = "v40-alpha"
    case_count: int = Field(default=0, ge=0)
    case_results: list[AcceptanceWindowCaseResult] = Field(default_factory=list)
    run_ids: list[str] = Field(default_factory=list)
    passed_count: int = Field(default=0, ge=0)
    review_count: int = Field(default=0, ge=0)
    blocked_count: int = Field(default=0, ge=0)
    average_verdict_match_score: float = Field(default=0.0, ge=0.0, le=1.0)
    average_advice_grounding_score: float = Field(default=0.0, ge=0.0, le=1.0)
    average_overclaim_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    average_domain_coverage_score: float = Field(default=0.0, ge=0.0, le=1.0)
    average_probe_usefulness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    average_llm_expression_clarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    average_overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    failed_reason_counts: dict[str, int] = Field(default_factory=dict)
    recommendation: ReleaseRecommendation = ReleaseRecommendation.NEEDS_REVIEW
    production_write_allowed: bool = False
    boundary: str = "acceptance_window_result_aggregates_real_case_acceptance_without_policy_write"

    @model_validator(mode="after")
    def _acceptance_window_boundary(self) -> "AcceptanceWindowResult":
        if not self.window_id.strip():
            raise ValueError("AcceptanceWindowResult requires window_id")
        if self.case_count != len(self.case_results):
            raise ValueError("AcceptanceWindowResult case_count must match case_results")
        if self.case_count != len(self.run_ids):
            raise ValueError("AcceptanceWindowResult case_count must match run_ids")
        if self.passed_count + self.review_count + self.blocked_count != self.case_count:
            raise ValueError("AcceptanceWindowResult status counts must match case_count")
        if self.production_write_allowed:
            raise ValueError("AcceptanceWindowResult cannot write production policy")
        return self


class TrainingExampleReplayResult(V40Model):
    version: str = "v40.training_example_replay_result.v1"
    replay_id: str
    example_id: str
    reading_id: str
    candidate_version: str = "v40-alpha"
    target_count: int = Field(default=0, ge=0)
    matched_target_ids: list[str] = Field(default_factory=list)
    missing_target_ids: list[str] = Field(default_factory=list)
    target_coverage_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    local_overlay_ref_count: int = Field(default=0, ge=0)
    positive_label_count: int = Field(default=0, ge=0)
    negative_label_count: int = Field(default=0, ge=0)
    needs_probe_count: int = Field(default=0, ge=0)
    feedback_alignment_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: EvaluationStatus = EvaluationStatus.REVIEW
    failed_reasons: list[str] = Field(default_factory=list)
    recommendation: ReleaseRecommendation = ReleaseRecommendation.NEEDS_REVIEW
    production_write_allowed: bool = False
    chart_fact_mutation_allowed: bool = False
    source_example: TrainingExampleV2 | None = None
    boundary: str = "training_example_replay_scores_feedback_against_runtime_without_weight_write"

    @model_validator(mode="after")
    def _training_example_replay_boundary(self) -> "TrainingExampleReplayResult":
        if not self.replay_id.strip():
            raise ValueError("TrainingExampleReplayResult requires replay_id")
        if not self.example_id.strip():
            raise ValueError("TrainingExampleReplayResult requires example_id")
        if self.production_write_allowed:
            raise ValueError("TrainingExampleReplayResult cannot write production policy")
        if self.chart_fact_mutation_allowed:
            raise ValueError("TrainingExampleReplayResult cannot mutate chart facts")
        if self.recommendation == ReleaseRecommendation.APPROVE and self.status != EvaluationStatus.PASSED:
            raise ValueError("TrainingExampleReplayResult can approve only when replay passed")
        return self


class TrainingReplayBatchSummary(V40Model):
    version: str = "v40.training_replay_batch_summary.v1"
    batch_id: str
    candidate_version: str
    replay_count: int = Field(default=0, ge=0)
    replay_ids: list[str] = Field(default_factory=list)
    passed_count: int = Field(default=0, ge=0)
    review_count: int = Field(default=0, ge=0)
    blocked_count: int = Field(default=0, ge=0)
    average_feedback_alignment_score: float = Field(default=0.0, ge=0.0, le=1.0)
    average_target_coverage_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    failed_reason_counts: dict[str, int] = Field(default_factory=dict)
    recommendation: ReleaseRecommendation = ReleaseRecommendation.NEEDS_REVIEW
    production_write_allowed: bool = False
    boundary: str = "training_replay_batch_summary_aggregates_feedback_replay_without_weight_write"

    @model_validator(mode="after")
    def _training_replay_batch_boundary(self) -> "TrainingReplayBatchSummary":
        if not self.batch_id.strip():
            raise ValueError("TrainingReplayBatchSummary requires batch_id")
        if self.replay_count != len(self.replay_ids):
            raise ValueError("TrainingReplayBatchSummary replay_count must match replay_ids")
        if self.passed_count + self.review_count + self.blocked_count != self.replay_count:
            raise ValueError("TrainingReplayBatchSummary status counts must match replay_count")
        if self.production_write_allowed:
            raise ValueError("TrainingReplayBatchSummary cannot write production policy")
        if self.recommendation == ReleaseRecommendation.APPROVE and (
            self.blocked_count or self.review_count or not self.replay_count
        ):
            raise ValueError("TrainingReplayBatchSummary can approve only when all replays passed")
        return self


class ReleaseReadinessSummary(V40Model):
    version: str = "v40.release_readiness_summary.v1"
    readiness_id: str
    candidate_version: str
    batch_count: int = Field(default=0, ge=0)
    batch_ids: list[str] = Field(default_factory=list)
    approved_batch_count: int = Field(default=0, ge=0)
    review_batch_count: int = Field(default=0, ge=0)
    rejected_batch_count: int = Field(default=0, ge=0)
    average_batch_score: float = Field(default=0.0, ge=0.0, le=1.0)
    failed_reason_counts: dict[str, int] = Field(default_factory=dict)
    recommendation: ReleaseRecommendation = ReleaseRecommendation.NEEDS_REVIEW
    production_write_allowed: bool = False
    boundary: str = "release_readiness_summary_aggregates_batches_without_activation"

    @model_validator(mode="after")
    def _readiness_boundary(self) -> "ReleaseReadinessSummary":
        if not self.readiness_id.strip():
            raise ValueError("ReleaseReadinessSummary requires readiness_id")
        if self.batch_count != len(self.batch_ids):
            raise ValueError("ReleaseReadinessSummary batch_count must match batch_ids")
        if self.approved_batch_count + self.review_batch_count + self.rejected_batch_count != self.batch_count:
            raise ValueError("ReleaseReadinessSummary status counts must match batch_count")
        if self.production_write_allowed:
            raise ValueError("ReleaseReadinessSummary cannot write production policy")
        return self


class ShadowCompareResult(V40Model):
    version: str = "v40.shadow_compare_result.v1"
    compare_id: str
    v30_export_id: str
    v40_reading_id: str
    v30_signal_count: int = Field(default=0, ge=0)
    v40_signal_count: int = Field(default=0, ge=0)
    v30_verdict_count: int = Field(default=0, ge=0)
    v40_verdict_count: int = Field(default=0, ge=0)
    v30_advice_count: int = Field(default=0, ge=0)
    v40_advice_count: int = Field(default=0, ge=0)
    import_coverage_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    verdict_topic_overlap_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    product_projection_ready: bool = False
    leakage_free: bool = False
    regression_detected: bool = False
    failed_reasons: list[str] = Field(default_factory=list)
    recommendation: ReleaseRecommendation = ReleaseRecommendation.NEEDS_REVIEW
    writes_v30_state: bool = False
    writes_v40_production: bool = False
    boundary: str = "shadow_compare_observes_v30_v40_delta_without_mutating_either_runtime"

    @model_validator(mode="after")
    def _shadow_compare_boundary(self) -> "ShadowCompareResult":
        if self.writes_v30_state:
            raise ValueError("ShadowCompareResult cannot write V30 state")
        if self.writes_v40_production:
            raise ValueError("ShadowCompareResult cannot write V40 production")
        if self.recommendation == ReleaseRecommendation.APPROVE and (
            self.regression_detected or self.failed_reasons
        ):
            raise ValueError("ShadowCompareResult cannot approve with regression or failures")
        return self


class ShadowCompareBatchSummary(V40Model):
    version: str = "v40.shadow_compare_batch_summary.v1"
    batch_id: str
    compare_count: int = Field(default=0, ge=0)
    compare_ids: list[str] = Field(default_factory=list)
    passed_count: int = Field(default=0, ge=0)
    review_count: int = Field(default=0, ge=0)
    regression_count: int = Field(default=0, ge=0)
    average_import_coverage_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    average_verdict_topic_overlap_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    product_projection_ready_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    failed_reason_counts: dict[str, int] = Field(default_factory=dict)
    recommendation: ReleaseRecommendation = ReleaseRecommendation.NEEDS_REVIEW
    writes_v30_state: bool = False
    writes_v40_production: bool = False
    boundary: str = "shadow_compare_batch_observes_migration_risk_without_mutating_v30_or_v40_production"

    @model_validator(mode="after")
    def _shadow_compare_batch_boundary(self) -> "ShadowCompareBatchSummary":
        if not self.batch_id.strip():
            raise ValueError("ShadowCompareBatchSummary requires batch_id")
        if self.compare_count != len(self.compare_ids):
            raise ValueError("ShadowCompareBatchSummary compare_count must match compare_ids")
        if self.passed_count + self.review_count + self.regression_count != self.compare_count:
            raise ValueError("ShadowCompareBatchSummary status counts must match compare_count")
        if self.writes_v30_state:
            raise ValueError("ShadowCompareBatchSummary cannot write V30 state")
        if self.writes_v40_production:
            raise ValueError("ShadowCompareBatchSummary cannot write V40 production")
        return self
