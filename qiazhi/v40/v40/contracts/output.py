from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from v40.contracts.base import AssertionLevel, RoleKey, SurfaceKey, Topic, V40Model


class AcceptanceStatus(str, Enum):
    ACCEPTED = "accepted"
    REPAIR = "repair"
    SALVAGE = "salvage"
    REASK = "reask"
    FALLBACK = "fallback"
    HARD_REJECT = "hard_reject"


class ProductVerdictCard(V40Model):
    version: str = "v40.product_verdict_card.v1"
    card_id: str
    source_verdict_id: str
    topic: Topic = Topic.UNKNOWN
    title: str
    primary_text: str
    advice_points: list[str] = Field(default_factory=list)
    confidence_label: str = ""
    assertion_level: AssertionLevel = AssertionLevel.WEAK_CANDIDATE
    evidence_count: int = Field(default=0, ge=0)
    role_visibility: list[RoleKey] = Field(default_factory=lambda: ["guest", "user", "practitioner"])
    boundary: str = "product_verdict_card_projects_decision_verdict_without_mutation"


class BranchCard(V40Model):
    version: str = "v40.branch_card.v1"
    card_id: str
    source_branch_id: str = ""
    topic: Topic = Topic.UNKNOWN
    title: str
    user_summary: str
    practitioner_summary: str = ""
    key_question: str = ""
    confidence_label: str = ""
    role_visibility: list[RoleKey] = Field(default_factory=lambda: ["guest", "user", "practitioner"])
    boundary: str = "branch_card_keeps_uncertainty_human_readable_without_policy_keys"


class ProductAdviceCard(V40Model):
    version: str = "v40.product_advice_card.v1"
    card_id: str
    source_advice_id: str
    topic: Topic = Topic.UNKNOWN
    title: str
    action_points: list[str] = Field(default_factory=list)
    avoid_points: list[str] = Field(default_factory=list)
    condition_points: list[str] = Field(default_factory=list)
    role_visibility: list[RoleKey] = Field(default_factory=lambda: ["guest", "user", "practitioner"])
    boundary: str = "product_advice_card_uses_advice_plan_without_exceeding_verdict"


class LLMExpressionTask(V40Model):
    version: str = "v40.llm_expression_task.v1"
    task_id: str
    reading_id: str
    role_key: RoleKey = "user"
    topic: Topic = Topic.UNKNOWN
    input_card_ids: list[str] = Field(default_factory=list)
    instruction: str
    allowed_assertions: list[str] = Field(default_factory=list)
    forbidden_assertions: list[str] = Field(default_factory=list)
    can_change_verdict: bool = False
    can_create_chart_facts: bool = False
    boundary: str = "llm_expression_task_rewrites_language_not_decision_or_chart_facts"

    @model_validator(mode="after")
    def _task_boundary(self) -> "LLMExpressionTask":
        if self.can_change_verdict:
            raise ValueError("LLMExpressionTask cannot change verdict")
        if self.can_create_chart_facts:
            raise ValueError("LLMExpressionTask cannot create chart facts")
        if not self.instruction.strip():
            raise ValueError("LLMExpressionTask requires instruction")
        return self


class LLMExpressionResult(V40Model):
    version: str = "v40.llm_expression_result.v1"
    result_id: str
    task_id: str
    reading_id: str
    text: str
    raw_thinking: str = ""
    provider: str = ""
    model: str = ""
    changed_verdict: bool = False
    created_chart_facts: bool = False
    boundary: str = "llm_expression_result_must_pass_acceptance_before_user_surface"

    @model_validator(mode="after")
    def _result_boundary(self) -> "LLMExpressionResult":
        if self.changed_verdict:
            raise ValueError("LLMExpressionResult cannot change verdict")
        if self.created_chart_facts:
            raise ValueError("LLMExpressionResult cannot create chart facts")
        if not self.text.strip():
            raise ValueError("LLMExpressionResult requires text")
        return self


class AcceptanceResult(V40Model):
    version: str = "v40.acceptance_result.v1"
    result_id: str
    reading_id: str
    status: AcceptanceStatus
    accepted_text: str = ""
    repair_reasons: list[str] = Field(default_factory=list)
    leakage_hits: list[str] = Field(default_factory=list)
    overclaim_hits: list[str] = Field(default_factory=list)
    verdict_mutation_detected: bool = False
    chart_fact_mutation_detected: bool = False
    boundary: str = "acceptance_result_blocks_llm_or_surface_drift_before_final_projection"

    @model_validator(mode="after")
    def _acceptance_boundary(self) -> "AcceptanceResult":
        if self.status == AcceptanceStatus.ACCEPTED and not self.accepted_text.strip():
            raise ValueError("Accepted output requires accepted_text")
        if self.status == AcceptanceStatus.ACCEPTED and (self.leakage_hits or self.overclaim_hits):
            raise ValueError("Accepted output cannot contain leakage or overclaim hits")
        if self.status == AcceptanceStatus.ACCEPTED and self.verdict_mutation_detected:
            raise ValueError("Accepted output cannot contain verdict mutation")
        if self.status == AcceptanceStatus.ACCEPTED and self.chart_fact_mutation_detected:
            raise ValueError("Accepted output cannot contain chart fact mutation")
        return self


class ExpressionTelemetry(V40Model):
    version: str = "v40.expression_telemetry.v1"
    telemetry_id: str
    reading_id: str
    task_id: str
    result_id: str
    execution_mode: str = "local"
    provider: str = ""
    model: str = ""
    accepted: bool = False
    acceptance_status: AcceptanceStatus = AcceptanceStatus.REPAIR
    thinking_trace_available: bool = False
    thinking_trace_chars: int = Field(default=0, ge=0)
    repair_reasons: list[str] = Field(default_factory=list)
    leakage_hits: list[str] = Field(default_factory=list)
    overclaim_hits: list[str] = Field(default_factory=list)
    verdict_mutation_detected: bool = False
    chart_fact_mutation_detected: bool = False
    llm_decision_authority: bool = False
    writes_v30_state: bool = False
    writes_v40_production: bool = False
    boundary: str = "expression_telemetry_observes_llm_expression_without_decision_authority"

    @model_validator(mode="after")
    def _telemetry_boundary(self) -> "ExpressionTelemetry":
        if self.llm_decision_authority:
            raise ValueError("ExpressionTelemetry cannot grant LLM decision authority")
        if self.writes_v30_state:
            raise ValueError("ExpressionTelemetry cannot write V30 state")
        if self.writes_v40_production:
            raise ValueError("ExpressionTelemetry cannot write V40 production")
        return self


class ConversationSeed(V40Model):
    version: str = "v40.conversation_seed.v1"
    seed_id: str
    reading_id: str
    topic: Topic = Topic.UNKNOWN
    question: str
    intent: str = ""
    answer_mode: str = "choice_or_short_text"
    options: list[str] = Field(default_factory=list)
    source_probe_ids: list[str] = Field(default_factory=list)
    source_verdict_ids: list[str] = Field(default_factory=list)
    source_advice_ids: list[str] = Field(default_factory=list)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    generated_after_report: bool = True
    auto_start: bool = False
    role_visibility: list[RoleKey] = Field(default_factory=lambda: ["user", "practitioner"])
    boundary: str = "conversation_seed_invites_user_dialogue_without_auto_start_or_verdict_authority"

    @model_validator(mode="after")
    def _seed_boundary(self) -> "ConversationSeed":
        if not self.seed_id.strip():
            raise ValueError("ConversationSeed requires seed_id")
        if not self.question.strip():
            raise ValueError("ConversationSeed requires question")
        if self.auto_start:
            raise ValueError("ConversationSeed cannot auto-start dialogue")
        return self


class ConversationTurn(V40Model):
    version: str = "v40.conversation_turn.v1"
    turn_id: str
    reading_id: str
    role_key: RoleKey = "user"
    topic: Topic = Topic.UNKNOWN
    question: str
    selected_option: str = ""
    source_seed_id: str = ""
    source_probe_ids: list[str] = Field(default_factory=list)
    source_verdict_ids: list[str] = Field(default_factory=list)
    source_advice_ids: list[str] = Field(default_factory=list)
    answer_text: str = ""
    raw_thinking: str = ""
    provider: str = ""
    model: str = ""
    accepted: bool = False
    acceptance_status: AcceptanceStatus = AcceptanceStatus.REPAIR
    next_seeds: list[ConversationSeed] = Field(default_factory=list)
    can_change_verdict: bool = False
    can_create_chart_facts: bool = False
    writes_v30_state: bool = False
    writes_v40_production: bool = False
    boundary: str = "conversation_turn_answers_user_question_without_verdict_or_chart_fact_authority"

    @model_validator(mode="after")
    def _turn_boundary(self) -> "ConversationTurn":
        if not self.turn_id.strip():
            raise ValueError("ConversationTurn requires turn_id")
        if not self.question.strip():
            raise ValueError("ConversationTurn requires question")
        if self.accepted and not self.answer_text.strip():
            raise ValueError("Accepted ConversationTurn requires answer_text")
        if self.can_change_verdict:
            raise ValueError("ConversationTurn cannot change verdict")
        if self.can_create_chart_facts:
            raise ValueError("ConversationTurn cannot create chart facts")
        if self.writes_v30_state:
            raise ValueError("ConversationTurn cannot write V30 state")
        if self.writes_v40_production:
            raise ValueError("ConversationTurn cannot write V40 production")
        return self


class ProductProjectionBundle(V40Model):
    version: str = "v40.product_projection_bundle.v1"
    reading_id: str
    role_key: RoleKey = "user"
    verdict_cards: list[ProductVerdictCard] = Field(default_factory=list)
    branch_cards: list[BranchCard] = Field(default_factory=list)
    advice_cards: list[ProductAdviceCard] = Field(default_factory=list)
    leakage_scan_passed: bool = False
    boundary: str = "product_projection_bundle_is_surface_ready_projection_not_decision_authority"


class SurfaceBundle(V40Model):
    version: str = "v40.surface_bundle.v1"
    reading_id: str
    role_key: RoleKey = "user"
    surfaces: dict[SurfaceKey, dict[str, object]] = Field(default_factory=dict)
    report_first: bool = True
    probe_invited_only: bool = True
    conversation_invited_only: bool = True
    thinking_requested_only: bool = True
    boundary: str = "surface_bundle_keeps_reading_probe_conversation_and_thinking_separate"
