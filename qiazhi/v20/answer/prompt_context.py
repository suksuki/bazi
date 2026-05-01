from __future__ import annotations

from v20.answer.plan import AnswerPlan


def answer_plan_prompt_context(plan: AnswerPlan) -> dict[str, object]:
    return {
        "version": "v20.answer_prompt_context.v1",
        "question_key": plan.question_key,
        "measurement_focus": plan.measurement_focus,
        "sections": [
            {
                "title": section.title,
                "body": section.body,
                "section_type": section.section_type,
                "measurement_topic": section.measurement_topic,
            }
            for section in plan.sections
        ],
        "domain_boundary": {
            "measurement_topic": (plan.domain_projection or {}).get("measurement_topic", ""),
            "allowed_claim_types": (plan.domain_projection or {}).get("allowed_claim_types", ()),
            "blocked_claim_types": (plan.domain_projection or {}).get("blocked_claim_types", ()),
            "boundary": (plan.domain_projection or {}).get("boundary", ""),
        },
        "evidence_summary": {
            "feature_count": len(plan.evidence_pack.feature_ids),
            "evidence_ref_count": len(plan.evidence_pack.evidence_refs),
            "boundary_count": len(plan.evidence_pack.boundaries),
        },
        "llm_role": "rewrite_verified_answer_plan_only",
        "guardrails": [
            "NO_NEW_FACTS",
            "NO_UNSUPPORTED_CLAIMS",
            "NO_INTERNAL_IDS_IN_USER_TEXT",
        ],
    }
