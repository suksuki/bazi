from __future__ import annotations

from v20.features.schema import FeatureLayer
from v20.interaction.questions import HOOK_DOMAIN_PREFERENCE, QuestionCandidate
from v20.llm.tasks import (
    DOMAIN_ROUTE_PRIORITY,
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
                "DYNAMIC_DECISION_QUESTIONS_REMAIN_AUTHORITATIVE",
                "NO_CORE_FACT_MUTATION",
            ],
        }
    intent = interpret_user_intent(text, feature_layer, locale=locale)
    suggestions = suggest_question_candidates(text, feature_layer, questions, locale=locale)
    proposals = propose_feature_candidates(text, feature_layer, locale=locale)
    routed_question_key = (
        _single_intent_question_key(intent)
        or _first_supported_question_key(suggestions, questions)
        or _first_supported_intent_question_key(intent, questions)
    )
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
            "DYNAMIC_DECISION_QUESTION_RANKER_HAS_FINAL_SAY",
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
    candidates = tuple(
        str(row["question_key"])
        for row in suggestions.get("suggestions", ())
        if isinstance(row, dict) and row.get("question_key") in supported
    )
    return _first_supported_by_route(candidates, questions, feature_domains=())


def _first_supported_intent_question_key(intent: dict[str, object], questions: tuple[QuestionCandidate, ...]) -> str:
    supported = {question.question_key for question in questions}
    result = intent.get("result", {})
    if not isinstance(result, dict):
        return ""
    feature_domains = tuple(str(domain) for domain in result.get("feature_domains", ()) if str(domain))
    candidates = tuple(
        str(key)
        for key in result.get("candidate_question_keys", ())
        if str(key) in supported
    )
    return _first_supported_by_route(candidates, questions, feature_domains=feature_domains)


def _single_intent_question_key(intent: dict[str, object]) -> str:
    result = intent.get("result", {})
    if not isinstance(result, dict):
        return ""
    feature_domains = tuple(str(domain) for domain in result.get("feature_domains", ()) if str(domain))
    keys = tuple(str(key) for key in result.get("candidate_question_keys", ()) if str(key))
    return _first_supported_by_route(keys, (), feature_domains=feature_domains)


def _first_supported_by_route(
    candidates: tuple[str, ...],
    questions: tuple[QuestionCandidate, ...],
    *,
    feature_domains: tuple[str, ...],
) -> str:
    question_domain: dict[str, str] = {question.question_key: question.domain for question in questions}
    preference = {domain: index + 1 for index, domain in enumerate(dict.fromkeys(feature_domains))}
    scored: list[tuple[int, int, int, str]] = []
    for index, key in enumerate(dict.fromkeys(candidates), start=1):
        domain = question_domain.get(key) or HOOK_DOMAIN_PREFERENCE.get(key, "")
        scored.append((
            DOMAIN_ROUTE_PRIORITY.get(domain, 99),
            preference.get(domain, 99),
            index,
            key,
        ))
    if not scored:
        return ""
    return sorted(scored, key=lambda item: item[:3])[0][3]
