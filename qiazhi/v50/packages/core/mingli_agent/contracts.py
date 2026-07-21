from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from core.contracts.base import V50Model
from core.life_domains import LifeDomain


EpistemicKind = Literal[
    "fact",
    "derived_observation",
    "hypothesis",
    "assertion",
    "user_evidence",
    "unknown",
]


class WorldFact(V50Model):
    fact_id: str
    kind: Literal["fact", "derived_observation"]
    category: str
    statement: str
    payload: dict[str, Any] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list)
    authority: Literal[
        "deterministic_fact",
        "neutral_relation",
        "experimental_tool_observation",
        "research_prior",
    ] = "deterministic_fact"


class KnowledgeExcerpt(V50Model):
    knowledge_id: str
    title: str
    summary: str
    conditions: list[str] = Field(default_factory=list)
    counter_conditions: list[str] = Field(default_factory=list)
    controversy: str = ""
    source_refs: list[str] = Field(default_factory=list)


class ChartWorldInstance(V50Model):
    world_id: str
    reading_id: str
    pillars: list[str]
    birth_profile: dict[str, Any]
    facts: list[WorldFact]
    knowledge: list[KnowledgeExcerpt]
    ziwei_profile: dict[str, Any] = Field(default_factory=dict)
    timing_context: dict[str, Any] = Field(default_factory=dict)
    allowed_evidence_refs: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)


class SalientPhenomenon(V50Model):
    phenomenon_id: str
    observation: str
    why_it_matters: str
    evidence_refs: list[str]


class CognitiveHypothesis(V50Model):
    hypothesis_id: str
    name: str
    thesis: str
    rank: int = Field(ge=1)
    status: Literal["primary", "alternative", "unresolved"]
    supporting_evidence_refs: list[str]
    counter_evidence_refs: list[str] = Field(default_factory=list)
    success_conditions: list[str] = Field(default_factory=list)
    failure_conditions: list[str] = Field(default_factory=list)
    rejection_reason: str = ""
    confidence: Literal["low", "medium", "high"]


class WorkPathReasoning(V50Model):
    path_statement: str
    source: list[str]
    transformations: list[str]
    target: list[str]
    body_function_relation: str
    closure: Literal["closed", "conditional", "broken", "uncertain"]
    success_conditions: list[str]
    failure_conditions: list[str]
    evidence_refs: list[str]
    origin: Literal["system_enumerated", "retrieval_suggested", "llm_composed", "mixed"] = "llm_composed"
    candidate_path_refs: list[str] = Field(default_factory=list)
    competing_path_refs: list[str] = Field(default_factory=list)
    comparison_reasons: list[str] = Field(default_factory=list)


class UsefulGodReasoning(V50Model):
    candidate: str
    role: str
    why_useful: str
    when_harmful: str
    applicable_conditions: list[str]
    invalidating_conditions: list[str]
    evidence_refs: list[str]
    lens: Literal[
        "climate",
        "support_balance",
        "structure",
        "transformation",
        "work_path",
        "timing",
        "domain",
        # Legacy model values remain parseable, but the Reliability Gate
        # normalizes seasonal/repair and blocks mixed before commit.
        "seasonal",
        "repair",
        "mixed",
    ] = "work_path"
    question_answered: str = ""
    scope: Literal["natal", "current_timing", "domain_condition"] = "natal"
    node_refs: list[str] = Field(default_factory=list)
    counter_evidence_refs: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"


class CaseAssertion(V50Model):
    assertion_id: str
    domain: LifeDomain | Literal["timing", "portrait"]
    claim: str
    rationale: str
    epistemic_status: Literal["supported", "partially_supported", "unresolved"]
    conditions: list[str] = Field(default_factory=list)
    falsifiers: list[str] = Field(default_factory=list)
    evidence_refs: list[str]
    counter_evidence_refs: list[str] = Field(default_factory=list)


class DiscriminatingProbe(V50Model):
    probe_id: str
    question: str
    purpose: str
    distinguishes_hypothesis_refs: list[str]
    options: list[str]
    expected_updates: dict[str, str]


class DomainCausalReading(V50Model):
    domain: LifeDomain
    core_question: str
    causal_chain: list[str]
    stable_tendencies: list[str]
    favorable_environments: list[str]
    adverse_environments: list[str]
    opportunity_conditions: list[str]
    risk_conditions: list[str]
    timing_note: str
    prior_directions: list[str]
    assertions: list[CaseAssertion]
    unknowns: list[str]
    next_probe: DiscriminatingProbe | None = None


class PriorPrediction(V50Model):
    prediction_id: str
    claim: str
    why_predicted: str
    target_hypothesis_ref: str
    evidence_refs: list[str]
    disconfirming_answer: str


class ZiweiLensObservation(V50Model):
    observation_id: str
    domain: Literal["identity", "career", "wealth", "timing"]
    claim: str
    why_it_matters: str
    evidence_refs: list[str]
    counter_conditions: list[str] = Field(default_factory=list)


class DualLensCognitionDraft(V50Model):
    ziwei_first_look: str
    identity_axis: str
    palace_observations: list[ZiweiLensObservation]
    agreements: list[str]
    tensions: list[str]
    integrated_thesis: str
    current_stage_note: str
    cross_lens_probe: DiscriminatingProbe
    uncertainties: list[str]
    evidence_refs: list[str]


class WholeChartCognitionDraft(V50Model):
    first_look: str
    whole_chart_thesis: str
    salient_phenomena: list[SalientPhenomenon]
    hypotheses: list[CognitiveHypothesis]
    selected_hypothesis_id: str
    work_path: WorkPathReasoning
    useful_god_reasoning: list[UsefulGodReasoning]
    portrait: list[CaseAssertion]
    prior_predictions: list[PriorPrediction]
    next_probe: DiscriminatingProbe
    dual_lens: DualLensCognitionDraft | None = None
    unresolved_questions: list[str]
    evidence_refs: list[str]


class WholeChartStructuralDraft(V50Model):
    first_look: str
    whole_chart_thesis: str
    salient_phenomena: list[SalientPhenomenon]
    hypotheses: list[CognitiveHypothesis]
    selected_hypothesis_id: str
    work_path: WorkPathReasoning
    useful_god_reasoning: list[UsefulGodReasoning]
    portrait: list[CaseAssertion]
    unresolved_questions: list[str]
    evidence_refs: list[str]


class PatternHypothesisDraft(V50Model):
    first_look: str
    whole_chart_thesis: str
    salient_phenomena: list[SalientPhenomenon]
    hypotheses: list[CognitiveHypothesis]
    selected_hypothesis_id: str
    evidence_refs: list[str]


class PatternPreviewDraft(V50Model):
    preview_line: str
    focus_refs: list[str]


class WorkPathPortraitDraft(V50Model):
    work_path: WorkPathReasoning
    useful_god_reasoning: list[UsefulGodReasoning]
    portrait: list[CaseAssertion]
    unresolved_questions: list[str]
    evidence_refs: list[str]


class PredictionProbeDraft(V50Model):
    prior_predictions: list[PriorPrediction]
    next_probe: DiscriminatingProbe


class DomainCognitionDraft(V50Model):
    career: DomainCausalReading
    wealth: DomainCausalReading
    evidence_refs: list[str]


class MingliCognitiveDraft(WholeChartCognitionDraft):
    career: DomainCausalReading | None = None
    wealth: DomainCausalReading | None = None


class ReviewIssue(V50Model):
    code: str
    severity: Literal["error", "warning"]
    message: str
    category: Literal[
        "chart_fact",
        "evidence",
        "semantic_consistency",
        "completeness",
        "hypothesis_competition",
        "safety",
        "quality",
    ] = "quality"
    blocks_commit: bool = False
    repairable: bool = False


class ProfessionalFactIssue(V50Model):
    issue_id: str
    claim_ref: str
    issue_type: str
    original_text: str
    canonical_fact_ref: str
    modality: Literal[
        "asserted_natal_fact",
        "derived_natal_claim",
        "hypothesis",
        "counterfactual",
        "timing_condition",
        "question",
        "quoted_claim",
    ]
    severity: Literal["hard", "major", "warning"]
    disposition: Literal["annotate", "suppress_from_projection"]


class EpistemicReviewReceipt(V50Model):
    passed: bool
    issues: list[ReviewIssue] = Field(default_factory=list)
    fact_traceability_rate: float = Field(ge=0.0, le=1.0)
    model: str
    repaired: bool = False
    disposition: Literal["reliable", "competing", "blocked"] = "reliable"
    commit_eligible: bool = True
    hard_failure_codes: list[str] = Field(default_factory=list)
    repairable_issue_codes: list[str] = Field(default_factory=list)
    gate_version: str = "legacy"


class AssertionGateDecision(V50Model):
    assertion_ref: str
    assertion_kind: str
    field_path: str
    disposition: Literal["accepted", "repaired", "candidate", "suppressed"]
    reason_codes: list[str] = Field(default_factory=list)
    accepted_evidence_refs: list[str] = Field(default_factory=list)
    rejected_evidence_refs: list[str] = Field(default_factory=list)
    original_text: str = ""
    projected_text: str = ""


class AssertionGateReceipt(V50Model):
    version: Literal["mingli_assertion_gate.v1"] = "mingli_assertion_gate.v1"
    decisions: list[AssertionGateDecision] = Field(default_factory=list)
    accepted_count: int = Field(default=0, ge=0)
    repaired_count: int = Field(default=0, ge=0)
    candidate_count: int = Field(default=0, ge=0)
    suppressed_count: int = Field(default=0, ge=0)
    whole_chart_claim_available: bool = False
    automatic_full_rerun_allowed: Literal[False] = False


class HypothesisComparisonReceipt(V50Model):
    passed: bool
    selected_hypothesis_id: str
    primary_hypothesis_ids: list[str] = Field(default_factory=list)
    alternative_hypothesis_ids: list[str] = Field(default_factory=list)
    distinct_signature_count: int = 0
    salient_evidence_coverage_rate: float = Field(ge=0.0, le=1.0)
    uncovered_salient_refs: list[str] = Field(default_factory=list)
    attention_evidence_used: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class DomainExploration(V50Model):
    domain: LifeDomain
    reading: DomainCausalReading
    review: EpistemicReviewReceipt
    assertion_gate: AssertionGateReceipt = Field(default_factory=AssertionGateReceipt)
    reasoning_protocol: dict[str, Any]
    context_manifest: dict[str, Any] = Field(default_factory=dict)
    generated_at: str
    reliability_disposition: Literal["reliable", "competing", "blocked"] = "reliable"
    baseline_record_id: str = ""
    baseline_insight_id: str = ""
    baseline_case_version: str = ""
    baseline_semantic_signature: str = ""
    request_fingerprint: str = ""
    implementation_versions: dict[str, str] = Field(default_factory=dict)
    input_context_hash: str = ""
    temporal_scope: str = "current"
    case_revision_candidate: dict[str, Any] | None = None


class MingliCognitiveRecord(V50Model):
    version: str = "deepbazi.mingli_cognitive_record.v3"
    record_id: str
    case_id: str
    world_id: str
    created_at: str
    model: str
    cognition: MingliCognitiveDraft
    review: EpistemicReviewReceipt
    assertion_gate: AssertionGateReceipt = Field(default_factory=AssertionGateReceipt)
    hypothesis_comparison: HypothesisComparisonReceipt | None = None
    stage_receipts: list[dict[str, Any]] = Field(default_factory=list)
    context_manifest: list[dict[str, Any]] = Field(default_factory=list)
    model_routes: list[dict[str, Any]] = Field(default_factory=list)
    user_evidence: list[dict[str, Any]] = Field(default_factory=list)
    revisions: list[dict[str, Any]] = Field(default_factory=list)
    domain_explorations: dict[LifeDomain, DomainExploration] = Field(default_factory=dict)
    reliability_disposition: Literal["reliable", "competing", "blocked", "legacy_unreviewed"] = "legacy_unreviewed"
    reliability_signature: str = ""


class BirthIntakeDraft(V50Model):
    name: str = ""
    gender: Literal["male", "female", "unknown"] = "unknown"
    calendar_type: Literal["solar", "lunar", "unknown"] = "solar"
    birth_date: str = ""
    birth_time: str = ""
    birth_location: str = ""
    timezone: str = "Asia/Shanghai"
    time_precision: Literal["exact", "approximate", "unknown"] = "unknown"
    missing_fields: list[str] = Field(default_factory=list)
    clarification_question: str = ""
    ready_for_confirmation: bool = False


class CaseTurnDraft(V50Model):
    interaction_type: Literal["explain", "domain_deepen", "feedback_revision", "clarification"]
    abu_message: str
    canvas_focus: Literal["overview", "hypotheses", "career", "wealth", "evidence", "profile"]
    interpretation: str
    hypothesis_updates: dict[str, Literal["strengthen", "weaken", "unchanged"]] = Field(default_factory=dict)
    changed_assertions: list[CaseAssertion] = Field(default_factory=list)
    retained_assertion_ids: list[str] = Field(default_factory=list)
    next_probe: DiscriminatingProbe | None = None
    suggested_actions: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
