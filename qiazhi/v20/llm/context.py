from __future__ import annotations

from v20.answer.plan import AnswerPlan
from v20.features.schema import FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.knowledge.schema import KnowledgeRetrievalReport
from v20.llm.contracts import (
    ANSWER_PLAN_REWRITE,
    FEATURE_CANDIDATE_PROPOSAL,
    INTENT_PARSE,
    QUESTION_SUGGESTION,
    SAFETY_REVIEW,
)
from v20.llm.prompts import (
    answer_rewrite_prompt,
    feature_candidate_prompt,
    intent_parse_prompt,
    question_suggestion_prompt,
    safety_review_prompt,
)


def build_llm_context_pack(
    user_text: str,
    feature_layer: FeatureLayer,
    questions: tuple[QuestionCandidate, ...],
    knowledge_report: KnowledgeRetrievalReport,
    answer_plan: AnswerPlan,
    answer_text: str,
    *,
    locale: str = "zh",
) -> dict[str, object]:
    return {
        "version": "v20.llm_context_pack.v1",
        "locale": locale,
        "user_text_present": bool(user_text.strip()),
        "feature_domains": sorted({feature.domain for feature in feature_layer.features}),
        "macro_feature_count": len(feature_layer.macro_features),
        "question_count": len(questions),
        "knowledge_ref_count": len(knowledge_report.refs),
        "task_contexts": {
            "intent_parse": {
                "contract": INTENT_PARSE.to_dict(),
                "prompt": intent_parse_prompt(user_text, locale=locale),
            },
            "question_suggestion": {
                "contract": QUESTION_SUGGESTION.to_dict(),
                "prompt": question_suggestion_prompt(user_text, feature_layer, questions, locale=locale),
            },
            "feature_candidate_proposal": {
                "contract": FEATURE_CANDIDATE_PROPOSAL.to_dict(),
                "prompt": feature_candidate_prompt(user_text, feature_layer, locale=locale),
            },
            "answer_plan_rewrite": {
                "contract": ANSWER_PLAN_REWRITE.to_dict(),
                "prompt": answer_rewrite_prompt(answer_plan, locale=locale),
            },
            "safety_review": {
                "contract": SAFETY_REVIEW.to_dict(),
                "prompt": safety_review_prompt(answer_text, locale=locale),
            },
        },
        "publishable": False,
        "runtime_mutation": False,
        "guardrails": [
            "LLM_CONTEXT_PACK_IS_INTERNAL_ASSISTIVE_INPUT",
            "FEATURE_LAYER_AND_ANSWER_PLAN_ARE_SOURCE_OF_TRUTH",
            "LLM_OUTPUT_MUST_PASS_VALIDATORS_BEFORE_PUBLICATION",
            "NO_CORE_FACT_OR_RULE_MUTATION",
        ],
    }
