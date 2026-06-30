from __future__ import annotations

from pydantic import Field, model_validator

from v40.contracts.base import AssertionLevel, Polarity, Topic, V40Model
from v40.contracts.signal import RuntimeSignal


class DecisionInputBundle(V40Model):
    version: str = "v40.decision_input_bundle.v1"
    bundle_id: str
    reading_id: str
    signal_ids: list[str] = Field(default_factory=list)
    signals: list[RuntimeSignal] = Field(default_factory=list)
    local_overlay_ids: list[str] = Field(default_factory=list)
    policy_version: str = "v40.policy.initial"
    llm_input_used: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "decision_input_bundle_feeds_decision_engine_without_llm_or_chart_fact_mutation"

    @model_validator(mode="after")
    def _bundle_boundary(self) -> "DecisionInputBundle":
        if not self.bundle_id.strip():
            raise ValueError("DecisionInputBundle requires bundle_id")
        if self.llm_input_used:
            raise ValueError("DecisionInputBundle cannot use LLM output as decision input in V40 alpha")
        if self.chart_fact_mutation_allowed:
            raise ValueError("DecisionInputBundle cannot mutate chart facts")
        return self


class BranchCandidate(V40Model):
    version: str = "v40.branch_candidate.v1"
    branch_id: str
    reading_id: str
    topic: Topic = Topic.UNKNOWN
    claim: str
    polarity: Polarity = Polarity.NEUTRAL
    probability: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    counter_evidence_refs: list[str] = Field(default_factory=list)
    needs_probe: bool = False
    probe_question: str = ""
    boundary: str = "branch_candidate_keeps_uncertainty_until_decision_or_calibration"


class DecisionVerdict(V40Model):
    version: str = "v40.decision_verdict.v1"
    verdict_id: str
    reading_id: str
    topic: Topic = Topic.UNKNOWN
    headline: str
    assertion_level: AssertionLevel = AssertionLevel.WEAK_CANDIDATE
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    allowed_assertions: list[str] = Field(default_factory=list)
    forbidden_assertions: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    counter_evidence_refs: list[str] = Field(default_factory=list)
    primary_branch_id: str = ""
    alternative_branch_ids: list[str] = Field(default_factory=list)
    next_probe_ids: list[str] = Field(default_factory=list)
    llm_decision_authority: bool = False
    central_brain_decision_authority: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "decision_verdict_is_only_generated_by_decision_engine"

    @model_validator(mode="after")
    def _verdict_boundary(self) -> "DecisionVerdict":
        if not self.verdict_id.strip():
            raise ValueError("DecisionVerdict requires verdict_id")
        if not self.headline.strip():
            raise ValueError("DecisionVerdict requires headline")
        if self.llm_decision_authority:
            raise ValueError("LLM cannot be verdict authority")
        if self.central_brain_decision_authority:
            raise ValueError("CentralBrain cannot be verdict authority")
        if self.chart_fact_mutation_allowed:
            raise ValueError("DecisionVerdict cannot mutate chart facts")
        if self.assertion_level in {AssertionLevel.CONFIRMED, AssertionLevel.SUPPORTED} and not self.evidence_refs:
            raise ValueError("Strong DecisionVerdict requires evidence_refs")
        return self


class AdvicePlan(V40Model):
    version: str = "v40.advice_plan.v1"
    advice_id: str
    reading_id: str
    topic: Topic = Topic.UNKNOWN
    source_verdict_ids: list[str] = Field(default_factory=list)
    action_points: list[str] = Field(default_factory=list)
    avoid_points: list[str] = Field(default_factory=list)
    condition_points: list[str] = Field(default_factory=list)
    priority: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    exceeds_verdict_boundary: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "advice_plan_must_bind_verdict_and_evidence"

    @model_validator(mode="after")
    def _advice_boundary(self) -> "AdvicePlan":
        if not self.advice_id.strip():
            raise ValueError("AdvicePlan requires advice_id")
        if not self.source_verdict_ids:
            raise ValueError("AdvicePlan requires source_verdict_ids")
        if not (self.action_points or self.avoid_points or self.condition_points):
            raise ValueError("AdvicePlan requires action, avoid, or condition points")
        if self.exceeds_verdict_boundary:
            raise ValueError("AdvicePlan cannot exceed verdict boundary")
        if self.chart_fact_mutation_allowed:
            raise ValueError("AdvicePlan cannot mutate chart facts")
        return self


class ProbeCandidate(V40Model):
    version: str = "v40.probe_candidate.v1"
    probe_id: str
    reading_id: str
    topic: Topic = Topic.UNKNOWN
    question: str
    target_branch_ids: list[str] = Field(default_factory=list)
    target_verdict_ids: list[str] = Field(default_factory=list)
    expected_information_gain: float = Field(default=0.0, ge=0.0, le=1.0)
    user_cost: float = Field(default=0.0, ge=0.0, le=1.0)
    ask_now: bool = False
    boundary: str = "probe_candidate_may_request_information_but_not_auto_dialogue"

    @model_validator(mode="after")
    def _probe_boundary(self) -> "ProbeCandidate":
        if not self.probe_id.strip():
            raise ValueError("ProbeCandidate requires probe_id")
        if not self.question.strip():
            raise ValueError("ProbeCandidate requires question")
        if not (self.target_branch_ids or self.target_verdict_ids):
            raise ValueError("ProbeCandidate requires target branch or verdict")
        if self.ask_now and self.expected_information_gain <= self.user_cost:
            raise ValueError("ProbeCandidate can ask now only when information gain exceeds user cost")
        return self


class DecisionEngineOutput(V40Model):
    version: str = "v40.decision_engine_output.v1"
    output_id: str
    reading_id: str
    input_bundle: DecisionInputBundle
    branch_candidates: list[BranchCandidate] = Field(default_factory=list)
    verdicts: list[DecisionVerdict] = Field(default_factory=list)
    advice_plans: list[AdvicePlan] = Field(default_factory=list)
    probes: list[ProbeCandidate] = Field(default_factory=list)
    policy_version: str = "v40.decision.native_product.v1"
    llm_decision_authority: bool = False
    central_brain_decision_authority: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "decision_engine_output_is_product_decision_layer_not_engine_or_llm"

    @model_validator(mode="after")
    def _decision_output_boundary(self) -> "DecisionEngineOutput":
        if not self.output_id.strip():
            raise ValueError("DecisionEngineOutput requires output_id")
        if not self.verdicts:
            raise ValueError("DecisionEngineOutput requires verdicts")
        if not self.advice_plans:
            raise ValueError("DecisionEngineOutput requires advice_plans")
        if self.llm_decision_authority:
            raise ValueError("DecisionEngineOutput cannot grant LLM decision authority")
        if self.central_brain_decision_authority:
            raise ValueError("DecisionEngineOutput cannot grant CentralBrain decision authority")
        if self.chart_fact_mutation_allowed:
            raise ValueError("DecisionEngineOutput cannot mutate chart facts")
        return self
