from __future__ import annotations

from v20.answer.prompt_context import answer_plan_prompt_context
from v20.answer.plan import AnswerPlan
from v20.features.schema import FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.knowledge.schema import KnowledgeUnit


def answer_rewrite_prompt(
    plan: AnswerPlan,
    *,
    locale: str = "en",
    tone: str = "clear",
    verified_answer_text: str = "",
) -> dict[str, object]:
    context = answer_plan_prompt_context(plan)
    if verified_answer_text:
        context = {
            "version": "v20.answer_rewrite_compact_context.v1",
            "verified_answer_text": verified_answer_text,
            "domain_boundary": context["domain_boundary"],
            "evidence_summary": context["evidence_summary"],
            "guardrails": context["guardrails"],
        }
    return {
        "task": "answer_plan_rewrite",
        "locale": locale,
        "tone": tone,
        "context": context,
        "output_schema": {"text": "string"},
        "instruction": (
            "Return only {\"text\":\"...\"}. Rewrite the verified answer into one concise, user-facing paragraph under 260 Chinese characters or locale equivalent. "
            "Do not echo the context, do not include answer_plan, and do not add facts or conclusions."
        ),
    }


def intent_parse_prompt(user_text: str, *, locale: str = "zh") -> dict[str, object]:
    return {
        "task": "intent_parse",
        "locale": locale,
        "user_text": user_text,
        "instruction": "Extract routing intent only. Do not create chart facts, rule activations, or conclusions.",
    }


def question_suggestion_prompt(
    user_text: str,
    feature_layer: FeatureLayer,
    questions: tuple[QuestionCandidate, ...],
    *,
    locale: str = "zh",
) -> dict[str, object]:
    return {
        "task": "question_suggestion",
        "locale": locale,
        "user_text": user_text,
        "feature_domains": sorted({feature.domain for feature in feature_layer.features}),
        "question_keys": [question.question_key for question in questions],
        "instruction": "Suggest only from existing feature-backed question keys.",
    }


def feature_candidate_prompt(user_text: str, feature_layer: FeatureLayer, *, locale: str = "zh") -> dict[str, object]:
    return {
        "task": "feature_candidate_proposal",
        "locale": locale,
        "user_text": user_text,
        "feature_domains": sorted({feature.domain for feature in feature_layer.features}),
        "instruction": "Propose candidate domains only. The feature compiler owns runtime features.",
    }


def rule_extraction_prompt(
    unit: KnowledgeUnit,
    *,
    corpus_validation_signal: dict[str, object] | None = None,
    locale: str = "zh",
) -> dict[str, object]:
    return {
        "task": "rule_extraction_draft",
        "locale": locale,
        "reviewed_knowledge_unit": unit.to_dict(),
        "feature_hook_contracts": list(unit.feature_hooks),
        "question_hook_contracts": list(unit.question_hooks),
        "corpus_validation_signal": corpus_validation_signal or {"status": "not_available"},
        "instruction": (
            "Extract draft condition atoms from the reviewed knowledge unit only. "
            "Corpus data may suggest validation gaps but must not author new rules. "
            "Do not activate runtime rules or add fortune conclusions."
        ),
    }


def safety_review_prompt(candidate_text: str, *, locale: str = "zh") -> dict[str, object]:
    return {
        "task": "safety_review",
        "locale": locale,
        "candidate_text": candidate_text,
        "instruction": "Review for forbidden claims, internal identifiers, privacy leaks, and missing boundaries.",
    }
