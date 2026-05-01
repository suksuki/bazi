from __future__ import annotations

from v20.answer.composer import compose_answer
from v20.answer.plan import AnswerPlan
from v20.features.schema import FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.llm.contracts import ANSWER_PLAN_REWRITE, SAFETY_REVIEW
from v20.llm.structured_outputs import (
    LLMFeatureCandidate,
    LLMFeedbackSummary,
    LLMIntentParse,
    LLMQuestionSuggestion,
    LLMSafetyReview,
)
from v20.llm.validators import validate_llm_output


def accept_or_fallback_rewrite(plan: AnswerPlan, candidate_text: str, *, locale: str = "en") -> dict[str, object]:
    validation = validate_llm_output(ANSWER_PLAN_REWRITE, candidate_text)
    if validation["ok"]:
        return {"ok": True, "text": candidate_text, "validation": validation, "source": "llm_rewrite"}
    return {"ok": False, "text": compose_answer(plan, locale=locale), "validation": validation, "source": "deterministic_fallback"}


def interpret_user_intent(user_text: str, feature_layer: FeatureLayer | None = None, *, locale: str = "zh") -> dict[str, object]:
    domains = _domains_from_text(user_text)
    if not domains and feature_layer is not None:
        domains = tuple(feature.domain for feature in feature_layer.features[:2])
    intent = LLMIntentParse(
        intent_key="domain_focus" if domains else "open_structure_review",
        normalized_question=user_text.strip(),
        candidate_question_keys=tuple(f"q_{domain}_review" for domain in domains[:3]),
        feature_domains=domains,
        confidence=0.56 if domains else 0.32,
        locale=locale,
    )
    return {
        "version": "v20.llm_intent_parse.v1",
        "contract": "intent_parse",
        "result": intent.to_dict(),
        "runtime_mutation": False,
        "guardrails": ["LLM_INTENT_ROUTING_HINT_ONLY", "CORE_FACTS_UNCHANGED"],
    }


def suggest_question_candidates(
    user_text: str,
    feature_layer: FeatureLayer,
    questions: tuple[QuestionCandidate, ...],
    *,
    locale: str = "zh",
) -> dict[str, object]:
    domains = set(_domains_from_text(user_text))
    if not domains:
        domains = {feature.domain for feature in feature_layer.features[:2]}
    suggestions: list[LLMQuestionSuggestion] = []
    for question in questions:
        source_domains = {
            feature.domain
            for feature in feature_layer.features
            if feature.feature_id in question.source_feature_ids
        }
        if source_domains & domains:
            suggestions.append(
                LLMQuestionSuggestion(
                    question_key=question.question_key,
                    reason="Matched the user's requested domain to existing feature-backed questions.",
                    source_feature_ids=question.source_feature_ids,
                )
            )
    return {
        "version": "v20.llm_question_suggestion.v1",
        "contract": "question_suggestion",
        "locale": locale,
        "suggestions": [row.to_dict() for row in suggestions[:3]],
        "runtime_mutation": False,
        "guardrails": ["LLM_SUGGESTS_ONLY", "FEATURE_RANKER_REMAINS_AUTHORITATIVE"],
    }


def propose_feature_candidates(user_text: str, feature_layer: FeatureLayer, *, locale: str = "zh") -> dict[str, object]:
    existing_domains = {feature.domain for feature in feature_layer.features}
    requested_domains = _domains_from_text(user_text)
    candidates = [
        LLMFeatureCandidate(
            domain=domain,
            rationale="The user's wording asks for this domain, but runtime features must still come from the compiler.",
            required_evidence=("chart_facts", "rule_path", "reviewed_knowledge"),
        )
        for domain in requested_domains
        if domain in existing_domains
    ]
    return {
        "version": "v20.llm_feature_candidate_proposal.v1",
        "contract": "feature_candidate_proposal",
        "locale": locale,
        "candidates": [row.to_dict() for row in candidates],
        "runtime_mutation": False,
        "guardrails": ["CANDIDATE_ONLY", "FEATURE_COMPILER_HAS_FINAL_SAY"],
    }


def review_output_safety(candidate_text: str) -> dict[str, object]:
    validation = validate_llm_output(SAFETY_REVIEW, candidate_text)
    review = LLMSafetyReview(
        ok=bool(validation["ok"]),
        failures=tuple(validation["failures"]),
        risk_notes=tuple(validation["failures"]) or ("none",),
    )
    return {
        "version": "v20.llm_safety_review.v1",
        "contract": "safety_review",
        "result": review.to_dict(),
        "deterministic_validation": validation,
        "runtime_mutation": False,
        "guardrails": ["DETERMINISTIC_VALIDATOR_FINAL", "LLM_REVIEW_ADVISORY_ONLY"],
    }


def summarize_feedback(feedback_text: str, *, locale: str = "zh") -> dict[str, object]:
    domains = _domains_from_text(feedback_text)
    summary = LLMFeedbackSummary(
        summary=feedback_text.strip()[:160],
        candidate_domains=domains,
        calibration_notes=("feedback_requires_validation_before_promotion",),
    )
    return {
        "version": "v20.llm_feedback_summary.v1",
        "contract": "feedback_summary",
        "locale": locale,
        "result": summary.to_dict(),
        "runtime_mutation": False,
        "guardrails": ["FEEDBACK_ANALYSIS_ONLY", "NO_AUTOMATIC_PROMOTION"],
    }


def _domains_from_text(text: str) -> tuple[str, ...]:
    lower = text.lower()
    domain_keywords = (
        ("wealth", ("财", "收入", "money", "wealth", "income", "재물", "수입")),
        ("strength", ("身强", "身弱", "强弱", "strength", "capacity", "강약")),
        ("useful_god", ("用神", "喜忌", "useful", "favorable", "용신")),
        ("branch", ("冲", "合", "刑", "害", "地支", "branch", "clash", "합", "충")),
        ("ten_god", ("十神", "正官", "七杀", "食神", "ten god", "십성")),
        ("pattern", ("格局", "pattern", "structure", "격국")),
    )
    found = [domain for domain, keywords in domain_keywords if any(keyword in lower for keyword in keywords)]
    return tuple(dict.fromkeys(found))
