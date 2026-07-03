from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import Field

from v30.contracts import V30Model


BAZI_DIALOGUE_CHAIN_VERSION = "v30.bazi_dialogue_chain.v1"

DialogueSource = Literal["system", "user", "practitioner", "training"]
MacroDomain = Literal[
    "wealth",
    "career",
    "relationship",
    "health",
    "family",
    "timing",
    "decision",
    "useful_god",
    "structure",
    "overview",
]
TimeScope = Literal["natal", "current_year", "current_luck", "month", "custom"]
UserIntent = Literal["ask_conclusion", "ask_advice", "compare_options", "verify_event", "open_chat"]
AnswerPriority = Literal["answer_first", "clarify_first", "calibrate_first"]
DialogueStatus = Literal["active", "paused", "completed"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaziDialogueSeed(V30Model):
    version: str = "v30.bazi_dialogue_seed.v1"
    seed_id: str
    reading_id: str
    source: DialogueSource = "user"
    raw_text: str
    normalized_question: str
    macro_domain: MacroDomain = "overview"
    bazi_topics: list[str] = Field(default_factory=list)
    time_scope: TimeScope = "natal"
    user_intent: UserIntent = "ask_conclusion"
    answer_priority: AnswerPriority = "answer_first"
    confidence: float = Field(default=0.72, ge=0.0, le=1.0)
    evidence_binding: list[str] = Field(default_factory=list)
    stage_id: str = ""
    boundary: str = "dialogue_seed_is_intent_not_chart_fact"


class DialogueQuestionCandidate(V30Model):
    version: str = "v30.dialogue_question_candidate.v1"
    question_id: str
    label: str
    macro_domain: MacroDomain = "overview"
    user_intent: UserIntent = "ask_conclusion"
    prompt_text: str
    options: list[dict[str, Any]] = Field(default_factory=list)
    expected_information_gain: float = Field(default=0.55, ge=0.0, le=1.0)
    priority: int = Field(default=50, ge=0, le=100)
    reason: str = ""
    source: str = "dialogue_orchestrator"
    boundary: str = "dialogue_question_candidate_guides_next_turn_not_chart_fact"


class BaziDialogueAnswer(V30Model):
    version: str = "v30.bazi_dialogue_answer.v1"
    answer_id: str
    status: str = "ready"
    verdict_refs: list[str] = Field(default_factory=list)
    conclusion_items: list[str] = Field(default_factory=list)
    advice_items: list[str] = Field(default_factory=list)
    uncertainty_items: list[str] = Field(default_factory=list)
    evidence_items: list[str] = Field(default_factory=list)
    display_text: str = ""
    visual_hint: dict[str, Any] = Field(default_factory=dict)
    llm_metadata: dict[str, Any] = Field(default_factory=dict)
    boundary: str = "dialogue_answer_projects_runtime_verdicts_not_new_chart_facts"


class DialogueMemory(V30Model):
    version: str = "v30.dialogue_memory.v1"
    answered_seed_ids: list[str] = Field(default_factory=list)
    asked_question_ids: list[str] = Field(default_factory=list)
    selected_options: list[str] = Field(default_factory=list)
    domain_counts: dict[str, int] = Field(default_factory=dict)
    last_user_inputs: list[str] = Field(default_factory=list)
    summary: str = ""
    boundary: str = "dialogue_memory_records_feedback_not_chart_facts"


class BaziDialogueTurn(V30Model):
    version: str = "v30.bazi_dialogue_turn.v1"
    turn_id: str
    dialogue_id: str
    reading_id: str
    turn_index: int = Field(ge=1)
    user_input: dict[str, Any] = Field(default_factory=dict)
    interpreted_seed: BaziDialogueSeed
    answer_contract: dict[str, Any] = Field(default_factory=dict)
    answer: BaziDialogueAnswer
    next_question_candidates: list[DialogueQuestionCandidate] = Field(default_factory=list)
    selected_next_question: DialogueQuestionCandidate | None = None
    training_signal: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    boundary: str = "dialogue_turn_is_feedback_and_expression_not_chart_fact"


class BaziDialogueSession(V30Model):
    version: str = BAZI_DIALOGUE_CHAIN_VERSION
    dialogue_id: str
    reading_id: str
    seed: BaziDialogueSeed
    status: DialogueStatus = "active"
    turn_count: int = 0
    active_domain: MacroDomain = "overview"
    active_question_id: str = ""
    unresolved_slots: list[str] = Field(default_factory=list)
    memory_summary: DialogueMemory = Field(default_factory=DialogueMemory)
    policy_state: dict[str, Any] = Field(default_factory=dict)
    turns: list[BaziDialogueTurn] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    boundary: str = "dialogue_session_updates_memory_not_chart_facts"
