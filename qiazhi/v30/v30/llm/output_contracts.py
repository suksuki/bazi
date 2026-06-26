from __future__ import annotations

from typing import Literal

from pydantic import Field

from v30.contracts import AnswerContext, AnswerResult, V30Model
from v30.llm.context import LLMRolePromptContext, build_llm_role_prompt_context
from v30.llm.drift import LLMDriftCheckResult, check_llm_answer_drift


LLM_OUTPUT_CONTRACT_VERSION = "v30.llm.output_contracts.v1"
LLMTaskType = Literal[
    "answer_draft",
    "question_explanation",
    "synthetic_case_draft",
    "failure_cluster_summary",
]


class LLMOutputContract(V30Model):
    contract_id: str
    task_type: LLMTaskType
    role_key: str
    prompt_context_id: str
    output_schema: str
    required_fields: list[str] = Field(default_factory=list)
    text: str
    evidence_ids: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)
    drift_check: LLMDriftCheckResult
    validation_status: str


def build_answer_draft_contract(
    answer_context: AnswerContext,
    answer_result: AnswerResult,
    *,
    role_key: str | None = None,
) -> LLMOutputContract:
    prompt_context = build_llm_role_prompt_context(answer_context, role_key=role_key)
    drift = check_llm_answer_drift(answer_result.text, prompt_context)
    required = ["answer_id", "question_id", "text", "evidence_ids", "boundary"]
    return LLMOutputContract(
        contract_id=f"{answer_result.answer_id}:llm-contract:answer-draft:{prompt_context.role_key}",
        task_type="answer_draft",
        role_key=prompt_context.role_key,
        prompt_context_id=prompt_context.prompt_context_id,
        output_schema="AnswerDraft",
        required_fields=required,
        text=answer_result.text,
        evidence_ids=answer_result.evidence_ids,
        boundaries=[answer_result.boundary or "", *prompt_context.answer_boundaries],
        drift_check=drift,
        validation_status="passed" if drift.passed and _has_required_text(answer_result.text) else "failed",
    )


def build_question_explanation_contract(
    answer_context: AnswerContext,
    *,
    role_key: str | None = None,
) -> LLMOutputContract:
    prompt_context = build_llm_role_prompt_context(answer_context, role_key=role_key)
    anchor = answer_context.selected_question_anchor
    text = (
        f"Question {anchor.question_id} is selected for intent {anchor.intent_id}. "
        "It must stay bound to the selected evidence and cannot create chart facts."
    )
    drift = check_llm_answer_drift(text, prompt_context)
    return LLMOutputContract(
        contract_id=f"{answer_context.answer_context_id}:llm-contract:question-explanation:{prompt_context.role_key}",
        task_type="question_explanation",
        role_key=prompt_context.role_key,
        prompt_context_id=prompt_context.prompt_context_id,
        output_schema="QuestionExplanation",
        required_fields=["question_id", "intent_id", "why_this_question", "evidence_ids", "boundary"],
        text=text,
        evidence_ids=prompt_context.evidence_ids,
        boundaries=[*prompt_context.answer_boundaries, "question_explanation_cannot_mutate_runtime"],
        drift_check=drift,
        validation_status="passed" if drift.passed and anchor.question_id in text else "failed",
    )


def build_synthetic_case_draft_contract(
    answer_context: AnswerContext,
    *,
    role_key: str | None = None,
) -> LLMOutputContract:
    prompt_context = build_llm_role_prompt_context(answer_context, role_key=role_key or "lab")
    anchor = answer_context.selected_question_anchor
    text = (
        f"SyntheticCaseDraft for {anchor.question_id} must reuse selected evidence IDs, "
        "expected topics, and boundary checks only. It cannot invent chart facts, fixed timing, "
        "or confirmed hidden-factor facts."
    )
    drift = check_llm_answer_drift(text, prompt_context)
    return LLMOutputContract(
        contract_id=f"{answer_context.answer_context_id}:llm-contract:synthetic-case-draft:{prompt_context.role_key}",
        task_type="synthetic_case_draft",
        role_key=prompt_context.role_key,
        prompt_context_id=prompt_context.prompt_context_id,
        output_schema="SyntheticCaseDraft",
        required_fields=[
            "case_id",
            "case_type",
            "domain",
            "chart_input",
            "expected_observations",
            "negative_expectations",
            "boundaries",
        ],
        text=text,
        evidence_ids=prompt_context.evidence_ids,
        boundaries=[*prompt_context.answer_boundaries, "synthetic_case_draft_cannot_mutate_chart_facts"],
        drift_check=drift,
        validation_status="passed" if drift.passed and anchor.question_id in text else "failed",
    )


def build_failure_cluster_summary_contract(
    answer_context: AnswerContext,
    *,
    failures: list[str] | None = None,
    role_key: str | None = None,
) -> LLMOutputContract:
    prompt_context = build_llm_role_prompt_context(answer_context, role_key=role_key or "lab")
    failures = [str(row) for row in failures or [] if str(row)]
    failure_text = ", ".join(failures[:4]) if failures else "no active synthetic failures"
    text = (
        f"FailureClusterSummary reports {failure_text}. "
        "It groups validation failures for training triage and cannot change runtime facts, "
        "chart facts, policy pointers, or hidden-factor status."
    )
    drift = check_llm_answer_drift(text, prompt_context)
    return LLMOutputContract(
        contract_id=f"{answer_context.answer_context_id}:llm-contract:failure-cluster-summary:{prompt_context.role_key}",
        task_type="failure_cluster_summary",
        role_key=prompt_context.role_key,
        prompt_context_id=prompt_context.prompt_context_id,
        output_schema="FailureClusterSummary",
        required_fields=[
            "cluster_key",
            "failure_count",
            "source_case_ids",
            "failure_types",
            "recommended_owner",
            "boundaries",
        ],
        text=text,
        evidence_ids=prompt_context.evidence_ids,
        boundaries=[*prompt_context.answer_boundaries, "failure_cluster_summary_is_training_triage_not_runtime_fact"],
        drift_check=drift,
        validation_status="passed" if drift.passed and "FailureClusterSummary" in text else "failed",
    )


def summarize_llm_output_contracts(contracts: list[LLMOutputContract]) -> dict[str, object]:
    failed = [contract.contract_id for contract in contracts if contract.validation_status != "passed"]
    drift_failures = sorted({
        failure
        for contract in contracts
        for failure in contract.drift_check.failures
    })
    return {
        "version": LLM_OUTPUT_CONTRACT_VERSION,
        "contract_count": len(contracts),
        "task_types": sorted({contract.task_type for contract in contracts}),
        "validation_status": "passed" if not failed else "failed",
        "failed_contract_ids": failed,
        "drift_failures": drift_failures,
    }


def _has_required_text(text: str) -> bool:
    return bool(text and text.strip())
