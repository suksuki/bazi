from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class LLMTaskContract:
    task_name: str
    allowed_inputs: tuple[str, ...]
    required_outputs: tuple[str, ...]
    forbidden_outputs: tuple[str, ...]
    fallback: str
    runtime_scope: str = "assistive"
    guardrails: tuple[str, ...] = (
        "LLM_TASK_BOUNDED",
        "NO_FACT_GENERATION",
        "NO_RULE_MUTATION",
        "VALIDATOR_REQUIRED",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


INTENT_PARSE = LLMTaskContract(
    task_name="intent_parse",
    allowed_inputs=("user_text", "locale", "interaction_state"),
    required_outputs=("intent_key", "normalized_question", "candidate_question_keys", "feature_domains", "confidence"),
    forbidden_outputs=("chart_fact", "rule_activation", "final_answer", "fortune_verdict"),
    fallback="deterministic_intent_router",
    guardrails=(
        "LLM_TASK_BOUNDED",
        "INTENT_IS_ROUTING_HINT_ONLY",
        "NO_FACT_GENERATION",
        "VALIDATOR_REQUIRED",
    ),
)

QUESTION_SUGGESTION = LLMTaskContract(
    task_name="question_suggestion",
    allowed_inputs=("user_text", "feature_layer", "question_candidates", "locale"),
    required_outputs=("question_key", "reason", "source_feature_ids"),
    forbidden_outputs=("new_chart_fact", "rule_activation", "unsupported_question"),
    fallback="feature_spine_question_ranker",
)

FEATURE_CANDIDATE_PROPOSAL = LLMTaskContract(
    task_name="feature_candidate_proposal",
    allowed_inputs=("user_text", "feature_layer", "knowledge_refs", "locale"),
    required_outputs=("domain", "rationale", "required_evidence", "status"),
    forbidden_outputs=("runtime_feature_write", "new_chart_fact", "rule_mutation", "final_conclusion"),
    fallback="no_feature_candidate",
    guardrails=(
        "LLM_TASK_BOUNDED",
        "CANDIDATE_ONLY",
        "FEATURE_COMPILER_OWNS_RUNTIME_FEATURES",
        "VALIDATOR_REQUIRED",
    ),
)

ANSWER_PLAN_ASSIST = LLMTaskContract(
    task_name="answer_plan_assist",
    allowed_inputs=("answer_plan", "feature_layer", "knowledge_refs", "locale"),
    required_outputs=("section_order", "missing_boundary_notes", "clarity_notes"),
    forbidden_outputs=("new_chart_fact", "rule_activation", "unsupported_claim"),
    fallback="deterministic_answer_plan",
)

ANSWER_PLAN_REWRITE = LLMTaskContract(
    task_name="answer_plan_rewrite",
    allowed_inputs=("answer_plan", "locale", "tone"),
    required_outputs=("text",),
    forbidden_outputs=("new_chart_fact", "rule_activation", "unsupported_claim"),
    fallback="deterministic_answer",
)

MULTILINGUAL_RENDER = LLMTaskContract(
    task_name="multilingual_render",
    allowed_inputs=("verified_answer_text", "locale", "terminology_map"),
    required_outputs=("text", "locale", "terminology_notes"),
    forbidden_outputs=("new_claim", "dropped_boundary", "internal_id"),
    fallback="deterministic_locale_template",
)

FEEDBACK_SUMMARY = LLMTaskContract(
    task_name="feedback_summary",
    allowed_inputs=("feedback_text", "feature_layer", "locale"),
    required_outputs=("summary", "candidate_domains", "calibration_notes"),
    forbidden_outputs=("rule_mutation", "automatic_promotion", "private_data_exposure"),
    fallback="store_raw_feedback_only",
)

SAFETY_REVIEW = LLMTaskContract(
    task_name="safety_review",
    allowed_inputs=("candidate_text", "locale", "contract"),
    required_outputs=("ok", "failures", "risk_notes"),
    forbidden_outputs=("override_validator", "publish_without_guardrail"),
    fallback="deterministic_safety_validator",
    guardrails=(
        "LLM_TASK_BOUNDED",
        "SAFETY_REVIEW_IS_ADVISORY",
        "DETERMINISTIC_VALIDATOR_HAS_FINAL_SAY",
        "VALIDATOR_REQUIRED",
    ),
)

LLM_CONTRACTS = (
    INTENT_PARSE,
    QUESTION_SUGGESTION,
    FEATURE_CANDIDATE_PROPOSAL,
    ANSWER_PLAN_ASSIST,
    ANSWER_PLAN_REWRITE,
    MULTILINGUAL_RENDER,
    FEEDBACK_SUMMARY,
    SAFETY_REVIEW,
)
