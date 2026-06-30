from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from v40.contracts.base import AssertionLevel, ReleaseRecommendation, Topic, V40Model
from v40.contracts.output import ExpressionTelemetry


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
