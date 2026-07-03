from __future__ import annotations

from typing import Any, Literal

from pydantic import Field
from pydantic import model_validator

from v30.contracts import RoleKey, V30Model

BrainDecisionAction = Literal[
    "conclude_stage",
    "ask_stage_question",
    "ask_hidden_attribute_probe",
    "request_timing_context",
    "continue_next_stage",
    "final_synthesis",
    "blocked",
]
BrainClaimStatus = Literal["candidate", "selected", "weak", "blocked", "rejected"]
BrainQuestionAnswerShape = Literal["choice", "number", "short_text", "year", "none"]
BrainTrainingOutcomeStatus = Literal["pending", "answered", "skipped", "confirmed", "contradicted", "blocked"]
BrainTrainingExampleSource = Literal["runtime_feedback", "synthetic_replay", "518k_validation", "admin_label", "runtime_trace"]
DecisionCandidateType = Literal[
    "claim",
    "rule",
    "path",
    "portrait",
    "feature",
    "useful_god",
    "timing",
    "domain",
]
DecisionAssertionLevel = Literal["confirmed", "supported", "mixed", "weak_candidate", "blocked"]


class DecisionCandidate(V30Model):
    version: str = "v30.decision_candidate.v1"
    candidate_id: str
    candidate_type: DecisionCandidateType = "claim"
    claim_id: str = ""
    domain: str = "overview"
    claim_text: str
    source_module: str = "diagnosis_claim"
    evidence_refs: list[str] = Field(default_factory=list)
    counter_evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    score_components: dict[str, float] = Field(default_factory=dict)
    requires_calibration: bool = False
    role_visibility: list[RoleKey] = Field(default_factory=lambda: ["user", "practitioner", "admin"])
    source_signal_ids: list[str] = Field(default_factory=list)
    signal_source_summary: dict[str, Any] = Field(default_factory=dict)
    candidate_builder: dict[str, Any] = Field(default_factory=dict)
    chart_fact_mutation_allowed: bool = False
    boundary: str = "decision_candidate_is_structured_material_not_final_verdict"

    @model_validator(mode="after")
    def _candidate_is_traceable_material(self) -> "DecisionCandidate":
        if not self.candidate_id.strip():
            raise ValueError("DecisionCandidate requires candidate_id")
        if not self.claim_text.strip():
            raise ValueError("DecisionCandidate requires claim_text")
        if not self.evidence_refs and self.confidence >= 0.62:
            raise ValueError("High-confidence DecisionCandidate requires evidence_refs")
        if self.chart_fact_mutation_allowed:
            raise ValueError("DecisionCandidate cannot mutate chart facts")
        return self


class DecisionConflict(V30Model):
    version: str = "v30.decision_conflict.v1"
    conflict_id: str
    domain: str = "overview"
    conflict_type: str
    branch_a_id: str
    branch_b_id: str = ""
    evidence_for_a: list[str] = Field(default_factory=list)
    evidence_for_b: list[str] = Field(default_factory=list)
    resolution_policy: str
    needed_question: str = ""
    boundary: str = "decision_conflict_preserves_branch_uncertainty_without_forcing_single_verdict"

    @model_validator(mode="after")
    def _conflict_has_resolution_path(self) -> "DecisionConflict":
        if not self.conflict_id.strip():
            raise ValueError("DecisionConflict requires conflict_id")
        if not self.branch_a_id.strip():
            raise ValueError("DecisionConflict requires branch_a_id")
        if not (self.branch_b_id or self.needed_question):
            raise ValueError("DecisionConflict requires branch_b_id or needed_question")
        return self


class DecisionVerdict(V30Model):
    version: str = "v30.decision_verdict.v1"
    verdict_id: str
    domain: str = "overview"
    headline: str
    assertion_level: DecisionAssertionLevel
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    primary_branch_id: str
    alternative_branch_ids: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    counter_evidence_refs: list[str] = Field(default_factory=list)
    allowed_assertions: list[str] = Field(default_factory=list)
    forbidden_assertions: list[str] = Field(default_factory=list)
    advice_points: list[str] = Field(default_factory=list)
    next_question_slots: list[dict[str, Any]] = Field(default_factory=list)
    trace: dict[str, Any] = Field(default_factory=dict)
    chart_fact_mutation_allowed: bool = False
    llm_expression_only: bool = True
    boundary: str = "decision_verdict_is_the_only_customer_verdict_source_before_llm_expression"

    @model_validator(mode="after")
    def _verdict_is_bounded_and_traceable(self) -> "DecisionVerdict":
        if not self.verdict_id.strip():
            raise ValueError("DecisionVerdict requires verdict_id")
        if not self.headline.strip():
            raise ValueError("DecisionVerdict requires headline")
        if not self.primary_branch_id.strip():
            raise ValueError("DecisionVerdict requires primary_branch_id")
        if self.assertion_level in {"confirmed", "supported", "mixed"} and not self.evidence_refs:
            raise ValueError("DecisionVerdict requires evidence_refs for asserted verdicts")
        if not self.allowed_assertions:
            raise ValueError("DecisionVerdict requires allowed_assertions")
        if not self.forbidden_assertions:
            raise ValueError("DecisionVerdict requires forbidden_assertions")
        if self.chart_fact_mutation_allowed:
            raise ValueError("DecisionVerdict cannot mutate chart facts")
        if not self.llm_expression_only:
            raise ValueError("DecisionVerdict must keep LLM expression-only boundary")
        return self


class DecisionInputBundle(V30Model):
    version: str = "v30.decision_input_bundle.v1"
    bundle_id: str
    reading_id: str
    active_stage_id: str = ""
    candidates: list[DecisionCandidate] = Field(default_factory=list)
    conflicts: list[DecisionConflict] = Field(default_factory=list)
    feedback_overlay: dict[str, Any] = Field(default_factory=dict)
    practitioner_selection_count: int = Field(default=0, ge=0)
    llm_text_as_fact_allowed: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "decision_input_bundle_contains_clean_material_not_llm_longform_text"

    @model_validator(mode="after")
    def _bundle_blocks_dirty_fact_sources(self) -> "DecisionInputBundle":
        if not self.bundle_id.strip():
            raise ValueError("DecisionInputBundle requires bundle_id")
        if not self.reading_id.strip():
            raise ValueError("DecisionInputBundle requires reading_id")
        if self.llm_text_as_fact_allowed:
            raise ValueError("DecisionInputBundle cannot accept LLM longform as fact")
        if self.chart_fact_mutation_allowed:
            raise ValueError("DecisionInputBundle cannot mutate chart facts")
        return self


class DecisionEngineResult(V30Model):
    version: str = "v30.decision_engine_result.v1"
    engine_version: str
    reading_id: str
    active_stage_id: str = ""
    decision_input_bundle: DecisionInputBundle
    verdicts: list[DecisionVerdict] = Field(default_factory=list)
    candidate_builder_summary: dict[str, Any] = Field(default_factory=dict)
    conflict_resolver_summary: dict[str, Any] = Field(default_factory=dict)
    conflict_resolver_audit: list[dict[str, Any]] = Field(default_factory=list)
    feedback_recalculation_summary: dict[str, Any] = Field(default_factory=dict)
    blocked_verdict_count: int = Field(default=0, ge=0)
    llm_expression_contract: dict[str, Any] = Field(default_factory=dict)
    training_signal: dict[str, Any] = Field(default_factory=dict)
    chart_fact_mutation_allowed: bool = False
    boundary: str = "decision_engine_result_emits_verdicts_from_clean_material_before_llm_expression"

    @model_validator(mode="after")
    def _result_is_decision_centered(self) -> "DecisionEngineResult":
        if self.decision_input_bundle.reading_id != self.reading_id:
            raise ValueError("DecisionEngineResult reading id must match input bundle")
        if self.chart_fact_mutation_allowed:
            raise ValueError("DecisionEngineResult cannot mutate chart facts")
        if self.verdicts and not self.llm_expression_contract.get("llm_can_rewrite_expression_only"):
            raise ValueError("DecisionEngineResult requires LLM expression-only contract")
        return self


class BrainState(V30Model):
    state_id: str
    reading_id: str
    role_key: RoleKey
    session_phase: str
    active_mainline_id: str
    selected_question_id: str | None = None
    known_context: list[str] = Field(default_factory=list)
    unknown_context: list[str] = Field(default_factory=list)
    hidden_factor_focus: str


class SessionMemory(V30Model):
    memory_id: str
    known_context: list[str] = Field(default_factory=list)
    unknown_context: list[str] = Field(default_factory=list)
    last_selected_question_id: str | None = None
    feedback_slots: list[str] = Field(default_factory=list)
    memory_policy: str


class RoleState(V30Model):
    role_state_id: str
    role_key: RoleKey
    visibility: str
    answer_density: str
    diagnostics_visible: bool = False
    expression_voice: str


class RuntimePlannerDecision(V30Model):
    decision_id: str
    focus: str
    next_actions: list[str] = Field(default_factory=list)
    safeguards: list[str] = Field(default_factory=list)


class QuestionDialogueStrategy(V30Model):
    strategy_id: str
    selected_question_id: str | None
    selected_intent_id: str | None
    strategy: str
    reasons: list[str] = Field(default_factory=list)
    hidden_factor_mode: str


class ExpressionOrchestration(V30Model):
    orchestration_id: str
    expression_plan_id: str | None
    rendered_narrative_id: str | None
    style_profile_id: str | None
    surface_status: str
    safeguards: list[str] = Field(default_factory=list)


class FeedbackStrategy(V30Model):
    strategy_id: str
    capture_targets: list[str] = Field(default_factory=list)
    immediate_effect: list[str] = Field(default_factory=list)
    training_routes: list[str] = Field(default_factory=list)
    no_review_gate: bool = True


class TrainingSignalRoute(V30Model):
    route_id: str
    source: str
    target_signal_domain: str
    reason: str


class CentralBrainTrace(V30Model):
    trace_id: str
    version: str
    brain_state: BrainState
    session_memory: SessionMemory
    role_state: RoleState
    runtime_plan: RuntimePlannerDecision
    question_strategy: QuestionDialogueStrategy
    expression_orchestration: ExpressionOrchestration
    feedback_strategy: FeedbackStrategy
    training_signal_routes: list[TrainingSignalRoute] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)


class BrainEvidenceGraphSnapshot(V30Model):
    version: str = "v30.central_brain.evidence_graph_snapshot.v1"
    graph_id: str = ""
    reading_id: str
    node_count: int = Field(default=0, ge=0)
    edge_count: int = Field(default=0, ge=0)
    node_kinds: list[str] = Field(default_factory=list)
    edge_kinds: list[str] = Field(default_factory=list)
    top_claim_ids: list[str] = Field(default_factory=list)
    top_path_ids: list[str] = Field(default_factory=list)
    graph_missing: bool = False
    boundary: str = "central_brain_reads_evidence_graph_without_mutating_chart_facts"


class BrainClaimBelief(V30Model):
    version: str = "v30.central_brain.claim_belief.v1"
    claim_id: str
    domain: str = "overview"
    status: BrainClaimStatus = "candidate"
    confidence: float = Field(ge=0.0, le=1.0)
    actionability: float = Field(default=0.0, ge=0.0, le=1.0)
    uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    supporting_node_ids: list[str] = Field(default_factory=list)
    weakening_node_ids: list[str] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)
    overclaim_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    requires_question: bool = False
    posterior_delta: float = Field(default=0.0, ge=-1.0, le=1.0)
    boundary: str = "claim_belief_scores_existing_claim_without_generating_new_fact"

    @model_validator(mode="after")
    def _belief_has_trace_or_gap(self) -> "BrainClaimBelief":
        if not self.claim_id.strip():
            raise ValueError("BrainClaimBelief requires claim_id")
        if self.status in {"selected", "candidate"} and not (
            self.supporting_node_ids or self.missing_context or self.weakening_node_ids
        ):
            raise ValueError("BrainClaimBelief requires evidence trace or explicit missing context")
        return self


class BrainUncertaintySlot(V30Model):
    version: str = "v30.central_brain.uncertainty_slot.v1"
    uncertainty_id: str
    domain: str = "overview"
    target_claim_ids: list[str] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)
    information_gain: float = Field(ge=0.0, le=1.0)
    user_cost: float = Field(default=0.0, ge=0.0, le=1.0)
    hidden_attribute_gain: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _slot_targets_something(self) -> "BrainUncertaintySlot":
        if not self.target_claim_ids and not self.missing_context:
            raise ValueError("BrainUncertaintySlot requires target claims or missing context")
        return self


class BrainBeliefState(V30Model):
    version: str = "v30.central_brain.belief_state.v1"
    reading_id: str
    active_stage_id: str = ""
    user_goal: str = "overview"
    evidence_graph: BrainEvidenceGraphSnapshot
    top_claims: list[BrainClaimBelief] = Field(default_factory=list)
    weak_claims: list[BrainClaimBelief] = Field(default_factory=list)
    blocked_claims: list[BrainClaimBelief] = Field(default_factory=list)
    uncertainty_map: list[BrainUncertaintySlot] = Field(default_factory=list)
    known_context: list[str] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)
    final_decision_readiness: float = Field(default=0.0, ge=0.0, le=1.0)
    chart_fact_mutation_allowed: bool = False
    boundary: str = "belief_state_updates_claim_confidence_not_chart_facts"

    @model_validator(mode="after")
    def _belief_state_is_read_only(self) -> "BrainBeliefState":
        if self.chart_fact_mutation_allowed:
            raise ValueError("BrainBeliefState cannot allow chart fact mutation")
        if self.evidence_graph.reading_id != self.reading_id:
            raise ValueError("BrainBeliefState reading id must match evidence graph")
        return self


class BrainQuestionCandidate(V30Model):
    version: str = "v30.central_brain.question_candidate.v1"
    question_id: str
    prompt: str
    domain: str = "overview"
    answer_shape: BrainQuestionAnswerShape = "choice"
    target_claim_ids: list[str] = Field(default_factory=list)
    target_uncertainty_ids: list[str] = Field(default_factory=list)
    option_labels: list[str] = Field(default_factory=list)
    information_gain: float = Field(default=0.0, ge=0.0, le=1.0)
    user_cost: float = Field(default=0.0, ge=0.0, le=1.0)
    overask_penalty: float = Field(default=0.0, ge=0.0, le=1.0)
    hidden_attribute_probe: bool = False
    boundary: str = "question_candidate_must_reduce_uncertainty_or_calibrate_claim"

    @model_validator(mode="after")
    def _question_is_useful(self) -> "BrainQuestionCandidate":
        if not self.question_id.strip():
            raise ValueError("BrainQuestionCandidate requires question_id")
        if not self.prompt.strip() and self.answer_shape != "none":
            raise ValueError("BrainQuestionCandidate requires prompt")
        if not (self.target_claim_ids or self.target_uncertainty_ids):
            raise ValueError("BrainQuestionCandidate requires target claim or uncertainty")
        return self


class BrainLLMCandidateDerivation(V30Model):
    version: str = "v30.central_brain.llm_candidate_derivation.v1"
    provider: str = ""
    model: str = ""
    stage_id: str = ""
    accepted: bool = False
    public_thinking_lines: list[str] = Field(default_factory=list)
    derived_conclusion: str = ""
    derived_advice: str = ""
    used_evidence_ids: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    rejection_reasons: list[str] = Field(default_factory=list)
    llm_generated_facts: bool = False
    chart_fact_mutation_requested: bool = False
    boundary: str = "llm_derivation_is_candidate_only_and_cannot_create_chart_facts"

    @model_validator(mode="after")
    def _llm_cannot_generate_facts(self) -> "BrainLLMCandidateDerivation":
        if self.llm_generated_facts:
            raise ValueError("BrainLLMCandidateDerivation cannot generate facts")
        if self.chart_fact_mutation_requested:
            raise ValueError("BrainLLMCandidateDerivation cannot request chart fact mutation")
        if self.accepted and not self.used_evidence_ids:
            raise ValueError("Accepted BrainLLMCandidateDerivation requires used evidence")
        return self


class BrainDecisionTrace(V30Model):
    version: str = "v30.central_brain.decision_trace.v1"
    decision_id: str
    reading_id: str
    stage_id: str = ""
    selected_action: BrainDecisionAction
    selected_claim_ids: list[str] = Field(default_factory=list)
    rejected_claim_ids: list[str] = Field(default_factory=list)
    selected_question_id: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    feature_vector: dict[str, float] = Field(default_factory=dict)
    belief_state: BrainBeliefState
    question_candidates: list[BrainQuestionCandidate] = Field(default_factory=list)
    llm_candidate: BrainLLMCandidateDerivation | None = None
    training_targets: list[str] = Field(default_factory=list)
    chart_fact_mutation_allowed: bool = False
    production_policy_write_allowed: bool = False
    boundary: str = "brain_decision_trace_explains_action_without_mutating_facts_or_policies"

    @model_validator(mode="after")
    def _decision_is_explainable_and_read_only(self) -> "BrainDecisionTrace":
        if self.chart_fact_mutation_allowed:
            raise ValueError("BrainDecisionTrace cannot allow chart fact mutation")
        if self.production_policy_write_allowed:
            raise ValueError("BrainDecisionTrace cannot write production policy")
        if self.belief_state.reading_id != self.reading_id:
            raise ValueError("BrainDecisionTrace reading id must match belief state")
        if not self.reason_codes:
            raise ValueError("BrainDecisionTrace requires reason codes")
        if self.selected_action in {"ask_stage_question", "ask_hidden_attribute_probe"} and not self.selected_question_id:
            raise ValueError("Question actions require selected_question_id")
        if self.selected_question_id:
            question_ids = {question.question_id for question in self.question_candidates}
            if self.selected_question_id not in question_ids:
                raise ValueError("selected_question_id must exist in question_candidates")
        if self.selected_action in {"conclude_stage", "final_synthesis"} and not self.selected_claim_ids:
            raise ValueError("Conclusion actions require selected claims")
        if self.llm_candidate and self.llm_candidate.accepted:
            missing = set(self.llm_candidate.used_evidence_ids) - {
                node_id
                for claim in [*self.belief_state.top_claims, *self.belief_state.weak_claims, *self.belief_state.blocked_claims]
                for node_id in [*claim.supporting_node_ids, *claim.weakening_node_ids]
            }
            if missing:
                raise ValueError("Accepted LLM evidence must be present in belief state claim evidence")
        return self


class BrainDecisionOutcome(V30Model):
    version: str = "v30.central_brain.decision_outcome.v1"
    status: BrainTrainingOutcomeStatus = "pending"
    user_answered: bool = False
    answer_type: BrainQuestionAnswerShape = "none"
    selected_option: str = ""
    structured_payload: dict[str, Any] = Field(default_factory=dict)
    claim_delta: dict[str, float] = Field(default_factory=dict)
    followup_useful: bool | None = None
    contradiction_found: bool = False


class BrainTrainingInputSnapshot(V30Model):
    version: str = "v30.brain_training.input_snapshot.v1"
    stage_id: str = ""
    evidence_graph_snapshot: BrainEvidenceGraphSnapshot
    belief_state: BrainBeliefState
    candidate_claim_ids: list[str] = Field(default_factory=list)
    candidate_question_ids: list[str] = Field(default_factory=list)
    user_goal: str = "overview"
    chart_fact_mutation_allowed: bool = False

    @model_validator(mode="after")
    def _input_snapshot_is_read_only(self) -> "BrainTrainingInputSnapshot":
        if self.chart_fact_mutation_allowed:
            raise ValueError("BrainTrainingInputSnapshot cannot allow chart fact mutation")
        if self.evidence_graph_snapshot.reading_id != self.belief_state.reading_id:
            raise ValueError("BrainTrainingInputSnapshot reading id must match belief state")
        return self


class BrainTrainingLabels(V30Model):
    version: str = "v30.brain_training.labels.v1"
    claim_correctness: float = Field(default=0.0, ge=0.0, le=1.0)
    question_information_gain: float = Field(default=0.0, ge=0.0, le=1.0)
    advice_actionability: float = Field(default=0.0, ge=0.0, le=1.0)
    template_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    overclaim_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    user_cost: float = Field(default=0.0, ge=0.0, le=1.0)
    overask: bool = False
    contradiction_found: bool = False


class BrainTrainingSafety(V30Model):
    version: str = "v30.brain_training.safety.v1"
    chart_fact_mutation_allowed: bool = False
    llm_fact_injection_detected: bool = False
    production_policy_write_allowed: bool = False
    contains_sensitive_plaintext: bool = False

    @model_validator(mode="after")
    def _safety_blocks_fact_mutation(self) -> "BrainTrainingSafety":
        if self.chart_fact_mutation_allowed:
            raise ValueError("BrainTrainingSafety cannot allow chart fact mutation")
        if self.llm_fact_injection_detected:
            raise ValueError("BrainTrainingSafety cannot accept LLM fact injection")
        if self.production_policy_write_allowed:
            raise ValueError("BrainTrainingSafety cannot write production policy")
        if self.contains_sensitive_plaintext:
            raise ValueError("BrainTrainingSafety cannot contain sensitive plaintext")
        return self


class BrainTrainingExample(V30Model):
    version: str = "v30.brain_training_example.v1"
    example_id: str
    reading_id: str
    source: BrainTrainingExampleSource = "runtime_trace"
    source_decision_id: str
    input_stage_id: str = ""
    evidence_graph_snapshot: BrainEvidenceGraphSnapshot
    input: BrainTrainingInputSnapshot | None = None
    candidate_claim_ids: list[str] = Field(default_factory=list)
    candidate_question_ids: list[str] = Field(default_factory=list)
    decision: BrainDecisionTrace
    outcome: BrainDecisionOutcome = Field(default_factory=BrainDecisionOutcome)
    structured_labels: BrainTrainingLabels = Field(default_factory=BrainTrainingLabels)
    labels: dict[str, Any] = Field(default_factory=dict)
    safety: BrainTrainingSafety = Field(default_factory=BrainTrainingSafety)
    trainable_targets: list[str] = Field(default_factory=list)
    blocked_targets: list[str] = Field(
        default_factory=lambda: [
            "chart_facts",
            "calendar_conversion",
            "pillar_calculation",
            "unconfirmed_hidden_factor_facts",
        ]
    )
    contains_sensitive_plaintext: bool = False
    production_policy_write_allowed: bool = False
    boundary: str = "brain_training_example_trains_policy_candidates_not_chart_facts_or_production_pointer"

    @model_validator(mode="after")
    def _training_example_is_safe_candidate_data(self) -> "BrainTrainingExample":
        if self.decision.reading_id != self.reading_id:
            raise ValueError("BrainTrainingExample reading id must match decision")
        if self.evidence_graph_snapshot.reading_id != self.reading_id:
            raise ValueError("BrainTrainingExample reading id must match evidence graph snapshot")
        if self.input and self.input.belief_state.reading_id != self.reading_id:
            raise ValueError("BrainTrainingExample input reading id must match example")
        if self.decision.decision_id != self.source_decision_id:
            raise ValueError("BrainTrainingExample source decision id must match decision")
        if self.contains_sensitive_plaintext:
            raise ValueError("BrainTrainingExample cannot contain sensitive plaintext")
        if self.production_policy_write_allowed:
            raise ValueError("BrainTrainingExample cannot write production policy")
        forbidden = {"chart_facts", "calendar_conversion", "pillar_calculation", "unconfirmed_hidden_factor_facts"}
        if forbidden.intersection(self.trainable_targets):
            raise ValueError("BrainTrainingExample cannot train deterministic fact targets")
        return self
