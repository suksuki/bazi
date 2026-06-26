from __future__ import annotations

import re

from pydantic import Field

from v30.contracts import V30Model
from v30.llm.context import LLMRolePromptContext


class LLMDriftCheckResult(V30Model):
    passed: bool
    failures: list[str] = Field(default_factory=list)
    checked_boundaries: list[str] = Field(default_factory=list)


UNSUPPORTED_TIMING_PATTERNS = (
    re.compile(r"\b(19|20)\d{2}\b.*\b(will|must|definitely|certainly)\b", re.IGNORECASE),
    re.compile(r"\b(will|must|definitely|certainly)\b.*\b(19|20)\d{2}\b", re.IGNORECASE),
)


def check_llm_answer_drift(text: str, prompt_context: LLMRolePromptContext) -> LLMDriftCheckResult:
    failures: list[str] = []
    normalized = text.lower()
    if "rule_bound_answer_no_llm_fact_mutation" not in prompt_context.answer_boundaries:
        failures.append("missing_answer_fact_mutation_boundary")
    if any(pattern.search(text) for pattern in UNSUPPORTED_TIMING_PATTERNS):
        failures.append("unsupported_deterministic_timing_claim")
    if "confirmed hidden factor" in normalized and "hidden_factor_feedback_can_condition_followups" not in prompt_context.answer_boundaries:
        failures.append("unsupported_hidden_factor_confirmation")
    if not prompt_context.evidence_ids and "evidence" in normalized:
        failures.append("mentions_evidence_without_bound_evidence_ids")
    return LLMDriftCheckResult(
        passed=not failures,
        failures=failures,
        checked_boundaries=prompt_context.answer_boundaries,
    )
