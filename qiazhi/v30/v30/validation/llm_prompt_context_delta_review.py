from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.llm.prompt_registry import build_bazi_llm_prompt_request
from v30.runtime import create_smoke_runtime


LLM_PROMPT_CONTEXT_DELTA_REVIEW_VERSION = "v30.llm_prompt_context_delta_review.v1"

TASK_SPECS: tuple[tuple[str, str, str], ...] = (
    ("customer_initial_reading", "", "user"),
    ("domain_followup", "career", "user"),
    ("domain_followup", "wealth", "user"),
    ("domain_followup", "relationship", "user"),
    ("domain_followup", "timing", "user"),
    ("hidden_factor_dialogue", "", "user"),
    ("useful_god_candidate_explanation", "", "user"),
    ("practitioner_analysis", "", "practitioner"),
)

REQUIRED_DOMAIN_MODULES = {"M3", "M4", "M5", "M6", "interaction_state", "known_user_signals"}
REQUIRED_DOMAIN_SECTIONS = {
    "structure_dynamics",
    "model_signals",
    "ranked_decisions",
    "practical_reading",
    "interaction_state",
    "known_user_signals",
}
FORBIDDEN_CONTEXT_TOKENS = (
    "policy_pointer_write_allowed\": true",
    "training_signal_mutation_allowed\": true",
    "chart_fact_mutation_allowed\": true",
)


def run_llm_prompt_context_delta_review(
    *,
    reading_id: str = "core-evidence-3-llm-prompt-context",
) -> dict[str, Any]:
    runtime = create_smoke_runtime(
        reading_id,
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    requests = [
        build_bazi_llm_prompt_request(
            runtime,
            task_type=task_type,
            domain=domain,
            role_key=role_key,
            locale="zh",
            client="web",
        )
        for task_type, domain, role_key in TASK_SPECS
    ]
    return build_llm_prompt_context_delta_review(prompt_requests=requests, reading_id=reading_id)


def build_llm_prompt_context_delta_review(
    *,
    prompt_requests: Sequence[Mapping[str, Any]],
    reading_id: str = "core-evidence-3-llm-prompt-context",
) -> dict[str, Any]:
    rows = [_request_row(request) for request in prompt_requests]
    summary = _summary(rows)
    decision = _decision(summary, rows)
    return {
        "version": LLM_PROMPT_CONTEXT_DELTA_REVIEW_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["llm_prompt_context_delta_ready"] else "blocked",
        "reading_id": reading_id,
        "decision": decision,
        "quality_summary": summary,
        "prompt_context_rows": rows,
        "core_scope": {
            "task_id": "CORE-EVIDENCE-3",
            "title": "LLM Prompt Context Delta Review",
            "acceptance_target": (
                "LLM prompt requests must select task-specific Bazi module context, "
                "especially domain follow-up packs with M3/M4/M5/M6 evidence, "
                "without raw runtime payload or chart-fact mutation"
            ),
            "covered_tasks": sorted({task for task, _, _ in TASK_SPECS}),
            "covered_roles": sorted({role for _, _, role in TASK_SPECS}),
        },
        "policy_boundary": {
            "llm_execution_performed": False,
            "live_provider_smoke_required": False,
            "full_pytest_run_by_default": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
            "boundary": "core_evidence_3_validates_prompt_context_shape_without_executing_provider",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "llm_prompt_context_delta_review_keeps_llm_as_bazi_expression_layer",
    }


def _request_row(request: Mapping[str, Any]) -> dict[str, Any]:
    contract = _dict(request.get("prompt_contract"))
    context = _dict(request.get("context_pack"))
    sections = [_dict(section) for section in _list(context.get("sections"))]
    section_ids = [str(section.get("section_id") or "") for section in sections]
    module_ids = [str(section.get("module_id") or "") for section in sections]
    included_modules = {str(row) for row in _list(context.get("included_modules"))}
    excluded_modules = {str(row) for row in _list(context.get("excluded_modules"))}
    task_type = str(request.get("task_type") or "")
    is_domain_followup = task_type == "domain_followup"
    budget = _dict(context.get("budget"))
    text_blob = str(
        {
            "sections": sections,
            "fact_boundary": context.get("fact_boundary"),
            "chart_fact_mutation_allowed": request.get("chart_fact_mutation_allowed"),
            "raw_runtime_payload_included": request.get("raw_runtime_payload_included"),
        }
    )
    checks = {
        "task_specific_context_pack": context.get("context_pack") == contract.get("required_context_pack"),
        "prompt_not_raw_runtime_dump": request.get("raw_runtime_payload_included") is False
        and "raw_runtime_payload" in excluded_modules,
        "read_only_fact_boundary": request.get("chart_fact_mutation_allowed") is False
        and _dict(context.get("fact_boundary")).get("chart_fact_mutation_allowed") is False
        and _dict(context.get("fact_boundary")).get("policy_pointer_write_allowed") is False,
        "budget_not_prompt_pileup": (
            int(budget.get("observed_context_sections") or 0) <= int(budget.get("max_context_sections") or 0)
            and int(budget.get("observed_evidence_items") or 0) <= int(budget.get("max_evidence_items") or 0)
            and int(budget.get("max_prompt_tokens_estimate") or 0) <= 1800
        ),
        "contract_has_verifier_and_fallback": bool(_dict(contract.get("verifier")).get("checks"))
        and bool(_dict(contract.get("fallback")).get("on_verifier_failure")),
        "domain_followup_uses_core_bazi_modules": True
        if not is_domain_followup
        else REQUIRED_DOMAIN_MODULES.issubset(included_modules),
        "domain_followup_uses_module_sections": True
        if not is_domain_followup
        else REQUIRED_DOMAIN_SECTIONS.issubset(set(section_ids)),
        "forbidden_context_tokens_absent": not any(token in text_blob for token in FORBIDDEN_CONTEXT_TOKENS),
    }
    failed = [check_id for check_id, passed in checks.items() if not passed]
    return {
        "task_type": task_type,
        "domain": str(context.get("domain") or ""),
        "role_key": str(context.get("role_key") or contract.get("role_key") or ""),
        "context_pack": str(context.get("context_pack") or ""),
        "quality_ready": not failed,
        "checks": checks,
        "failed_check_ids": failed,
        "included_modules": sorted(included_modules),
        "excluded_modules": sorted(excluded_modules),
        "section_ids": section_ids,
        "module_ids": module_ids,
        "budget": budget,
        "allowed_answer_scope": str(context.get("allowed_answer_scope") or ""),
        "boundary": str(request.get("boundary") or ""),
    }


def _summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ready_rows = [row for row in rows if row.get("quality_ready") is True]
    domain_rows = [row for row in rows if row.get("task_type") == "domain_followup"]
    return {
        "row_count": len(rows),
        "ready_row_count": len(ready_rows),
        "failed_row_count": len(rows) - len(ready_rows),
        "ready_ratio": round(len(ready_rows) / max(1, len(rows)), 3),
        "task_types": sorted({str(row.get("task_type") or "") for row in rows}),
        "domain_followup_domains": sorted({str(row.get("domain") or "") for row in domain_rows}),
        "domain_followup_count": len(domain_rows),
        "max_observed_context_sections": max(
            (int(_dict(row.get("budget")).get("observed_context_sections") or 0) for row in rows),
            default=0,
        ),
        "max_prompt_tokens_estimate": max(
            (int(_dict(row.get("budget")).get("max_prompt_tokens_estimate") or 0) for row in rows),
            default=0,
        ),
    }


def _decision(summary: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    failed_rows = [row for row in rows if row.get("failed_check_ids")]
    if failed_rows:
        blockers.append("llm_prompt_context_delta_rows_failed")
    if int(summary.get("domain_followup_count", 0) or 0) < 4:
        blockers.append("domain_followup_coverage_below_minimum")
    if not {"career", "wealth", "relationship", "timing"}.issubset(set(summary.get("domain_followup_domains", []))):
        blockers.append("domain_followup_domain_coverage_incomplete")
    if int(summary.get("max_prompt_tokens_estimate", 0) or 0) > 1800:
        blockers.append("prompt_budget_exceeds_core_evidence_limit")
    ready = not blockers
    return {
        "llm_prompt_context_delta_ready": ready,
        "decision_status": "core_evidence_3_llm_prompt_context_ready"
        if ready
        else "core_evidence_3_llm_prompt_context_blocked",
        "check_count": len(rows) * 8,
        "passed_check_count": sum(1 for row in rows for passed in _dict(row.get("checks")).values() if passed),
        "failed_check_ids": sorted(
            {
                str(check_id)
                for row in rows
                for check_id in _list(row.get("failed_check_ids"))
                if check_id
            }
        ),
        "blockers": blockers,
        "llm_execution_performed": False,
        "full_pytest_required": False,
        "next_action": "continue_to_llm_answer_output_delta_review"
        if ready
        else "harden_llm_context_packs_before_answer_generation_review",
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("llm_prompt_context_delta_ready") is True:
        return {
            "task_id": "CORE-EVIDENCE-4",
            "title": "LLM Answer Output Delta Review",
            "rationale": "Prompt context packs are module-bound; next verify generated/fallback answer output uses them without generic filler.",
            "full_pytest_required_before_start": False,
        }
    return {
        "task_id": "CORE-EVIDENCE-3A",
        "title": "LLM Context Pack Hardening",
        "rationale": "One or more prompt requests lacks bounded module context or read-only boundaries.",
        "full_pytest_required_before_start": False,
    }


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
