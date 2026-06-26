from __future__ import annotations

from pydantic import Field

from v30.contracts import AnswerContext, V30Model


class LLMRolePromptContext(V30Model):
    prompt_context_id: str
    role_key: str
    role_directive: str
    allowed_context_blocks: list[str] = Field(default_factory=list)
    answer_boundaries: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    system_constraints: list[str] = Field(default_factory=list)
    user_context: dict[str, object] = Field(default_factory=dict)


ROLE_DIRECTIVES = {
    "guest": "Explain only the high-level evidence-bound context and avoid specialist terminology.",
    "user": "Explain the selected Bazi context with clear next questions and no unsupported timing claims.",
    "practitioner": "Expose evidence, boundaries, and candidate paths while keeping verdicts defeasible.",
    "analyst": "Focus on traceability, policy effects, validation hooks, and uncertainty boundaries.",
    "admin": "Focus on runtime diagnostics, active policies, validation signals, and blocked drift.",
    "lab": "Focus on experiment design, synthetic validation, and parameter tuning signals.",
}


def build_llm_role_prompt_context(answer_context: AnswerContext, *, role_key: str | None = None) -> LLMRolePromptContext:
    role = role_key or str(answer_context.role_answer_contract.get("role") or "user")
    evidence_ids = [
        str(row.get("evidence_id"))
        for row in answer_context.evidence_summary
        if row.get("evidence_id")
    ]
    return LLMRolePromptContext(
        prompt_context_id=f"{answer_context.answer_context_id}:llm:{role}",
        role_key=role,
        role_directive=ROLE_DIRECTIVES.get(role, ROLE_DIRECTIVES["user"]),
        allowed_context_blocks=[
            "chart_summary",
            "structure_summary",
            "mainline_summary",
            "evidence_summary",
            "knowledge_boundaries",
        ],
        answer_boundaries=[
            *answer_context.knowledge_boundaries,
            "rule_bound_answer_no_llm_fact_mutation",
        ],
        evidence_ids=evidence_ids,
        system_constraints=[
            "Do not create new chart facts.",
            "Do not invent timing, event years, or user history.",
            "Do not turn hidden-factor hypotheses into deterministic claims.",
            "Use role style only after preserving evidence and boundaries.",
        ],
        user_context={
            "selected_question_id": answer_context.selected_question_anchor.question_id,
            "anchor_status": answer_context.selected_question_anchor.anchor_status,
            "quality_gate": answer_context.mainline_summary.get("quality_gate"),
        },
    )
