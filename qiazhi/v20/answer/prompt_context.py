from __future__ import annotations

from v20.answer.plan import AnswerPlan


def answer_plan_prompt_context(plan: AnswerPlan) -> dict[str, object]:
    return {
        "version": "v20.answer_prompt_context.v1",
        "answer_plan": plan.to_dict(),
        "llm_role": "rewrite_verified_answer_plan_only",
        "guardrails": [
            "NO_NEW_FACTS",
            "NO_UNSUPPORTED_CLAIMS",
            "NO_INTERNAL_IDS_IN_USER_TEXT",
        ],
    }
