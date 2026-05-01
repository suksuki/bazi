from __future__ import annotations

from v20.features.schema import FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.llm.tasks import (
    interpret_user_intent,
    propose_feature_candidates,
    review_output_safety,
    suggest_question_candidates,
)


def build_llm_routing_assist(
    user_text: str,
    feature_layer: FeatureLayer,
    questions: tuple[QuestionCandidate, ...],
    *,
    locale: str = "zh",
) -> dict[str, object]:
    text = user_text.strip()
    if not text:
        return {
            "version": "v20.llm_assist.v1",
            "status": "idle",
            "user_text_present": False,
            "routed_question_key": "",
            "runtime_mutation": False,
            "guardrails": [
                "LLM_ASSIST_OPTIONAL",
                "FEATURE_RANKER_REMAINS_AUTHORITATIVE",
                "NO_CORE_FACT_MUTATION",
            ],
        }
    intent = interpret_user_intent(text, feature_layer, locale=locale)
    suggestions = suggest_question_candidates(text, feature_layer, questions, locale=locale)
    proposals = propose_feature_candidates(text, feature_layer, locale=locale)
    routed_question_key = _first_supported_question_key(suggestions, questions)
    return {
        "version": "v20.llm_assist.v1",
        "status": "ready",
        "user_text_present": True,
        "intent": intent,
        "question_suggestions": suggestions,
        "feature_candidate_proposals": proposals,
        "routed_question_key": routed_question_key,
        "runtime_mutation": False,
        "guardrails": [
            "LLM_INTENT_IS_ROUTING_HINT_ONLY",
            "LLM_FEATURE_CANDIDATES_ARE_PROPOSAL_ONLY",
            "QUESTION_RANKER_AND_VALIDATOR_HAVE_FINAL_SAY",
            "NO_CORE_FACT_MUTATION",
        ],
    }


def attach_answer_safety_review(llm_assist: dict[str, object], answer_text: str) -> dict[str, object]:
    updated = dict(llm_assist)
    updated["answer_safety_review"] = review_output_safety(answer_text)
    updated["guardrails"] = list(updated.get("guardrails", ())) + ["ANSWER_TEXT_SAFETY_REVIEW_ATTACHED"]
    return updated


def _first_supported_question_key(suggestions: dict[str, object], questions: tuple[QuestionCandidate, ...]) -> str:
    supported = {question.question_key for question in questions}
    for row in suggestions.get("suggestions", ()):
        if isinstance(row, dict) and row.get("question_key") in supported:
            return str(row["question_key"])
    return ""
