from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from v30.contracts import V30Model


EVALUATION_SPINE_VERSION = "v30.evaluation_training_spine.v1"

EvaluationCaseType = Literal["synthetic", "golden", "real_feedback", "regression"]
EvaluationStatus = Literal["passed", "blocked", "review"]


class ExpectedSignal(V30Model):
    version: str = "v30.expected_signal.v1"
    source_type: str = ""
    source_module: str = ""
    domain: str = ""
    claim_key: str = ""
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    required: bool = True


class ExpectedVerdict(V30Model):
    version: str = "v30.expected_verdict.v1"
    domain: str
    allowed_assertion_levels: list[str] = Field(default_factory=lambda: ["confirmed", "supported", "mixed", "weak_candidate"])
    min_evidence_count: int = Field(default=1, ge=0)
    expected_keywords: list[str] = Field(default_factory=list)
    allowed_assertions: list[str] = Field(default_factory=list)
    forbidden_assertions: list[str] = Field(default_factory=list)
    requires_conflict_handling: bool = False


class ExpectedAdvice(V30Model):
    version: str = "v30.expected_advice.v1"
    domain: str
    source_verdict_domain: str = ""
    must_include_any: list[str] = Field(default_factory=list)
    requires_action: bool = True
    requires_avoid: bool = False
    requires_condition: bool = False


class ExpectedProbe(V30Model):
    version: str = "v30.expected_probe.v1"
    domain: str
    target: str = ""
    hidden_attribute_key: str = ""
    expected_keywords: list[str] = Field(default_factory=list)
    required: bool = False


class ForbiddenAssertion(V30Model):
    version: str = "v30.forbidden_assertion.v1"
    text: str
    severity: Literal["low", "medium", "high", "critical"] = "high"
    reason: str = ""


class EvaluationCaseSpec(V30Model):
    version: str = "v30.evaluation_case_spec.v1"
    case_id: str
    case_type: EvaluationCaseType = "golden"
    linked_case_id: str = ""
    user_question: str = ""
    topic: str = "overview"
    time_scope: str = "natal"
    known_reality: dict[str, Any] = Field(default_factory=dict)
    expert_notes: list[str] = Field(default_factory=list)
    expected_signals: list[ExpectedSignal] = Field(default_factory=list)
    expected_verdicts: list[ExpectedVerdict] = Field(default_factory=list)
    expected_advice: list[ExpectedAdvice] = Field(default_factory=list)
    expected_probes: list[ExpectedProbe] = Field(default_factory=list)
    allowed_assertions: list[str] = Field(default_factory=list)
    forbidden_assertions: list[ForbiddenAssertion] = Field(default_factory=list)
    evaluation_tags: list[str] = Field(default_factory=list)
    chart_fact_mutation_allowed: bool = False
    boundary: str = "evaluation_case_spec_defines_measurement_contract_not_runtime_policy"

    @model_validator(mode="after")
    def _case_spec_is_evaluable(self) -> "EvaluationCaseSpec":
        if not self.case_id.strip():
            raise ValueError("EvaluationCaseSpec requires case_id")
        if not self.expected_verdicts:
            raise ValueError("EvaluationCaseSpec requires expected_verdicts")
        if not self.forbidden_assertions:
            raise ValueError("EvaluationCaseSpec requires forbidden_assertions")
        if self.chart_fact_mutation_allowed:
            raise ValueError("EvaluationCaseSpec cannot allow chart fact mutation")
        return self


class VerdictEvalResult(V30Model):
    version: str = "v30.verdict_eval_result.v1"
    case_id: str
    reading_id: str
    verdict_count: int = Field(default=0, ge=0)
    expected_verdict_count: int = Field(default=0, ge=0)
    evidence_coverage_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    expected_domain_coverage_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    overclaim_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    assertion_calibration_score: float = Field(default=0.0, ge=0.0, le=1.0)
    conflict_resolution_score: float = Field(default=0.0, ge=0.0, le=1.0)
    forbidden_assertion_hits: list[str] = Field(default_factory=list)
    failed_reasons: list[str] = Field(default_factory=list)
    passed: bool = False
    boundary: str = "verdict_eval_measures_decision_verdict_without_changing_it"


class AdviceEvalResult(V30Model):
    version: str = "v30.advice_eval_result.v1"
    case_id: str
    reading_id: str
    advice_count: int = Field(default=0, ge=0)
    grounded_advice_count: int = Field(default=0, ge=0)
    advice_grounding_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    actionability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    assertion_boundary_score: float = Field(default=0.0, ge=0.0, le=1.0)
    ungrounded_advice: list[str] = Field(default_factory=list)
    failed_reasons: list[str] = Field(default_factory=list)
    passed: bool = False
    boundary: str = "advice_eval_requires_advice_to_bind_verdicts_and_evidence"


class ProbeEvalResult(V30Model):
    version: str = "v30.probe_eval_result.v1"
    case_id: str
    reading_id: str
    probe_candidate_count: int = Field(default=0, ge=0)
    expected_probe_count: int = Field(default=0, ge=0)
    answer_signal_count: int = Field(default=0, ge=0)
    probe_binding_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    probe_yield_score: float = Field(default=0.0, ge=0.0, le=1.0)
    requires_followup: bool = False
    failed_reasons: list[str] = Field(default_factory=list)
    passed: bool = False
    boundary: str = "probe_eval_measures_information_gain_without_mutating_hidden_attributes"


class TrainingImpactDiff(V30Model):
    version: str = "v30.training_impact_diff.v1"
    run_id: str
    before_example_count: int = Field(default=0, ge=0)
    after_example_count: int = Field(default=0, ge=0)
    before_metrics: dict[str, float] = Field(default_factory=dict)
    after_metrics: dict[str, float] = Field(default_factory=dict)
    metric_deltas: dict[str, float] = Field(default_factory=dict)
    changed_trainable_targets: list[str] = Field(default_factory=list)
    regression_detected: bool = False
    production_policy_write_allowed: bool = False
    boundary: str = "training_impact_diff_observes_training_effect_without_writing_policy_pointer"

    @model_validator(mode="after")
    def _impact_diff_does_not_write_policy(self) -> "TrainingImpactDiff":
        if self.production_policy_write_allowed:
            raise ValueError("TrainingImpactDiff cannot write production policy")
        return self


class MetricSummary(V30Model):
    version: str = "v30.evaluation_metric_summary.v1"
    case_id: str
    reading_id: str
    evidence_coverage_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    overclaim_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    assertion_calibration_score: float = Field(default=0.0, ge=0.0, le=1.0)
    advice_grounding_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    probe_yield_score: float = Field(default=0.0, ge=0.0, le=1.0)
    llm_drift_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: EvaluationStatus = "review"
    failed_reasons: list[str] = Field(default_factory=list)
    boundary: str = "metric_summary_combines_structured_evaluation_without_llm_as_judge"


class EvaluationRunResult(V30Model):
    version: str = "v30.evaluation_run_result.v1"
    run_id: str
    case_spec: EvaluationCaseSpec
    reading_id: str
    verdict_eval: VerdictEvalResult
    advice_eval: AdviceEvalResult
    probe_eval: ProbeEvalResult
    metric_summary: MetricSummary
    training_impact: TrainingImpactDiff | None = None
    status: EvaluationStatus
    chart_fact_mutation_allowed: bool = False
    production_policy_write_allowed: bool = False
    boundary: str = "evaluation_run_result_is_sidecar_and_never_changes_user_result"

    @model_validator(mode="after")
    def _evaluation_run_is_sidecar(self) -> "EvaluationRunResult":
        if self.chart_fact_mutation_allowed:
            raise ValueError("EvaluationRunResult cannot allow chart fact mutation")
        if self.production_policy_write_allowed:
            raise ValueError("EvaluationRunResult cannot write production policy")
        return self
