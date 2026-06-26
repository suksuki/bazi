from __future__ import annotations

from pydantic import Field

from v30.contracts import RoleKey, V30Model


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
