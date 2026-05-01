from __future__ import annotations

from dataclasses import replace

from v20.answer.composer import compose_answer
from v20.answer.plan import AnswerPlan
from v20.features.schema import FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.knowledge.schema import KnowledgeUnit
from v20.llm.client import call_structured_llm
from v20.llm.contracts import ANSWER_PLAN_REWRITE, RULE_EXTRACTION_DRAFT, SAFETY_REVIEW
from v20.llm.prompts import answer_rewrite_prompt, rule_extraction_prompt
from v20.llm.provider import load_llm_provider_config_from_env
from v20.llm.structured_outputs import (
    LLMFeatureCandidate,
    LLMFeedbackSummary,
    LLMIntentParse,
    LLMQuestionSuggestion,
    LLMRuleExtractionDraft,
    LLMSafetyReview,
)
from v20.llm.validators import validate_llm_output, validate_llm_structured_output
from v20.measurement.domain_alignment import ALLOWED_QUESTION_KEYS_BY_DOMAIN, is_allowed_bazi_domain

DOMAIN_ROUTE_PRIORITY = {
    "useful_god": 0,
    "strength": 1,
    "element": 2,
    "time": 3,
    "branch": 4,
    "ten_god": 5,
    "wealth": 6,
}


def accept_or_fallback_rewrite(plan: AnswerPlan, candidate_text: str, *, locale: str = "en") -> dict[str, object]:
    validation = validate_llm_output(ANSWER_PLAN_REWRITE, candidate_text)
    if validation["ok"]:
        return {"ok": True, "text": candidate_text, "validation": validation, "source": "llm_rewrite"}
    return {"ok": False, "text": compose_answer(plan, locale=locale), "validation": validation, "source": "deterministic_fallback"}


def rewrite_answer_plan_with_llm(
    plan: AnswerPlan,
    deterministic_text: str,
    *,
    locale: str = "zh",
    tone: str = "clear",
) -> dict[str, object]:
    prompt = answer_rewrite_prompt(
        plan,
        locale=locale,
        tone=tone,
        verified_answer_text=deterministic_text,
    )
    cfg = load_llm_provider_config_from_env()
    call = call_structured_llm(
        ANSWER_PLAN_REWRITE,
        prompt,
        config=replace(cfg, max_tokens=min(cfg.max_tokens, 320)),
    )
    if call["status"] == "accepted":
        text = str(call.get("output", {}).get("text") or "")
        accepted = accept_or_fallback_rewrite(plan, text, locale=locale)
        if accepted["ok"]:
            return {
                "version": "v20.llm_answer_rewrite.v1",
                "status": "accepted",
                "text": accepted["text"],
                "source": accepted["source"],
                "llm_call": call,
                "validation": accepted["validation"],
                "runtime_mutation": False,
                "guardrails": [
                    "LLM_REWRITE_FROM_VERIFIED_PLAN_ONLY",
                    "DETERMINISTIC_VALIDATOR_FINAL",
                    "FALLBACK_ON_CONTRACT_FAILURE",
                ],
            }
    return {
        "version": "v20.llm_answer_rewrite.v1",
        "status": "fallback",
        "text": deterministic_text,
        "source": "deterministic_fallback",
        "llm_call": call,
        "validation": call.get("validation", {}),
        "runtime_mutation": False,
        "guardrails": [
            "LLM_REWRITE_NOT_PUBLISHED",
            "DETERMINISTIC_ANSWER_USED",
            "NO_FACT_OR_RULE_MUTATION",
        ],
    }


def interpret_user_intent(user_text: str, feature_layer: FeatureLayer | None = None, *, locale: str = "zh") -> dict[str, object]:
    domains = tuple(domain for domain in _domains_from_text(user_text) if is_allowed_bazi_domain(domain))
    if not domains and feature_layer is not None:
        domains = tuple(feature.domain for feature in feature_layer.features[:2] if is_allowed_bazi_domain(feature.domain))
    intent = LLMIntentParse(
        intent_key="domain_focus" if domains else "open_structure_review",
        normalized_question=user_text.strip(),
        candidate_question_keys=_question_keys_for_domains(domains[:3]),
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
    domains = set(domain for domain in _domains_from_text(user_text) if is_allowed_bazi_domain(domain))
    if not domains:
        domains = {feature.domain for feature in feature_layer.features[:2] if is_allowed_bazi_domain(feature.domain)}
    ranked: list[tuple[int, int, str, LLMQuestionSuggestion]] = []
    for question in questions:
        source_domains = {
            feature.domain
            for feature in feature_layer.features
            if feature.feature_id in question.source_feature_ids
        }
        if source_domains & domains:
            priority = 0 if question.domain in domains else 1
            ranked.append(
                (
                    priority,
                    DOMAIN_ROUTE_PRIORITY.get(question.domain, 20),
                    question.question_key,
                    LLMQuestionSuggestion(
                        question_key=question.question_key,
                        reason="Matched the user's requested domain to existing feature-backed questions.",
                        source_feature_ids=question.source_feature_ids,
                    ),
                )
            )
    suggestions = [row for _priority, _domain_priority, _question_key, row in sorted(ranked, key=lambda item: item[:3])]
    return {
        "version": "v20.llm_question_suggestion.v1",
        "contract": "question_suggestion",
        "locale": locale,
        "suggestions": [row.to_dict() for row in suggestions[:3]],
        "runtime_mutation": False,
        "guardrails": ["LLM_SUGGESTS_ONLY", "DYNAMIC_DECISION_QUESTION_RANKER_REMAINS_AUTHORITATIVE"],
    }


def propose_feature_candidates(user_text: str, feature_layer: FeatureLayer, *, locale: str = "zh") -> dict[str, object]:
    existing_domains = {feature.domain for feature in feature_layer.features}
    requested_domains = tuple(domain for domain in _domains_from_text(user_text) if is_allowed_bazi_domain(domain))
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


def draft_rule_extraction_from_knowledge(unit: KnowledgeUnit, *, locale: str = "zh") -> dict[str, object]:
    draft = LLMRuleExtractionDraft(
        condition_atoms=tuple(
            {
                "atom_type": "feature_hook_prefix",
                "operator": "prefix_match",
                "value": hook,
                "source_knowledge_id": unit.knowledge_id,
            }
            for hook in unit.feature_hooks
        ),
        emits_feature_hooks=unit.feature_hooks,
        supports_question_hooks=unit.question_hooks,
        boundary=unit.boundary,
        risk_notes=("draft_requires_deterministic_validator",),
    )
    payload = draft.to_dict()
    return {
        "version": "v20.llm_rule_extraction_draft.v1",
        "contract": "rule_extraction_draft",
        "locale": locale,
        "draft": payload,
        "validation": validate_llm_structured_output(RULE_EXTRACTION_DRAFT, payload),
        "runtime_mutation": False,
        "guardrails": [
            "DRAFT_ONLY",
            "KNOWLEDGE_UNIT_IS_SOURCE",
            "NO_RUNTIME_RULE_ACTIVATION",
        ],
    }


def draft_rule_extraction_with_llm(
    unit: KnowledgeUnit,
    *,
    corpus_validation_signal: dict[str, object] | None = None,
    locale: str = "zh",
) -> dict[str, object]:
    prompt = rule_extraction_prompt(unit, corpus_validation_signal=corpus_validation_signal, locale=locale)
    call = call_structured_llm(RULE_EXTRACTION_DRAFT, prompt)
    fallback = draft_rule_extraction_from_knowledge(unit, locale=locale)
    if call["status"] == "accepted":
        return {
            "version": "v20.llm_rule_extraction_execution.v1",
            "status": "accepted",
            "source": "llm_structured_output",
            "contract": "rule_extraction_draft",
            "locale": locale,
            "draft": call["output"],
            "llm_call": call,
            "fallback": fallback["draft"],
            "runtime_mutation": False,
            "guardrails": [
                "LLM_OUTPUT_VALIDATED",
                "DRAFT_ONLY",
                "NO_RUNTIME_RULE_ACTIVATION",
            ],
        }
    return {
        "version": "v20.llm_rule_extraction_execution.v1",
        "status": "fallback",
        "source": "deterministic_fallback",
        "contract": "rule_extraction_draft",
        "locale": locale,
        "draft": fallback["draft"],
        "llm_call": call,
        "fallback": fallback["draft"],
        "runtime_mutation": False,
        "guardrails": [
            "LLM_NOT_ACCEPTED_OR_NOT_EXECUTED",
            "DETERMINISTIC_FALLBACK_USED",
            "NO_RUNTIME_RULE_ACTIVATION",
        ],
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
        ("element", ("五行", "木", "火", "土", "金", "水", "element", "balance", "오행")),
        ("time", ("流年", "大运", "时间", "应期", "year", "luck", "timing", "세운", "대운")),
        ("ten_god", ("十神", "正官", "七杀", "食神", "ten god", "십성")),
        ("pattern", ("格局", "pattern", "structure", "격국")),
    )
    found = [domain for domain, keywords in domain_keywords if any(keyword in lower for keyword in keywords)]
    return tuple(dict.fromkeys(found))


def _question_keys_for_domains(domains: tuple[str, ...]) -> tuple[str, ...]:
    keys: list[str] = []
    for domain in domains:
        keys.extend(ALLOWED_QUESTION_KEYS_BY_DOMAIN.get(domain, ())[:1])
    return tuple(dict.fromkeys(keys))
