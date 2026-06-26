from __future__ import annotations

from v30.llm import (
    BAZI_LLM_CONTEXT_PACK_VERSION,
    BAZI_LLM_PROMPT_REGISTRY_VERSION,
    build_bazi_llm_prompt_request,
    supported_bazi_llm_roles,
    supported_bazi_llm_tasks,
)
from v30.runtime import create_smoke_runtime


BAZI_LLM_CONTEXT_PROMPT_READINESS_VERSION = "v30.bazi_llm_context_prompt_readiness.v1"


def run_bazi_llm_context_prompt_readiness(
    reading_id: str = "bl1-bl3-bazi-llm-context-prompt",
) -> dict[str, object]:
    runtime = create_smoke_runtime(reading_id=reading_id)
    request_specs = [
        ("customer_initial_reading", "", "guest"),
        ("customer_initial_reading", "", "user"),
        ("domain_followup", "career", "user"),
        ("useful_god_candidate_explanation", "", "user"),
        ("hidden_factor_dialogue", "", "user"),
        ("practitioner_analysis", "", "practitioner"),
        ("practitioner_analysis", "", "analyst"),
        ("practitioner_analysis", "", "admin"),
        ("practitioner_analysis", "", "lab"),
        ("locale_rewrite", "", "guest"),
        ("locale_rewrite", "", "user"),
    ]
    requests = [
        build_bazi_llm_prompt_request(
            runtime,
            task_type=task_type,
            domain=domain,
            role_key=role_key,
            locale="zh",
            client="web",
        )
        for task_type, domain, role_key in request_specs
    ]
    return build_bazi_llm_context_prompt_readiness(prompt_requests=requests)


def build_bazi_llm_context_prompt_readiness(
    *,
    prompt_requests: list[dict[str, object]],
) -> dict[str, object]:
    task_results = [_task_result(request) for request in prompt_requests]
    checks = [
        {
            "check_id": "all_required_tasks_have_prompt_contracts",
            "passed": sorted({str(row["task_type"]) for row in task_results}) == sorted(supported_bazi_llm_tasks()),
            "observed": {"task_types": sorted({str(row["task_type"]) for row in task_results})},
        },
        {
            "check_id": "all_required_roles_have_prompt_contracts",
            "passed": sorted({str(row["role_key"]) for row in task_results}) == sorted(supported_bazi_llm_roles()),
            "observed": {"role_keys": sorted({str(row["role_key"]) for row in task_results})},
        },
        {
            "check_id": "context_pack_versions_are_current",
            "passed": all(row["context_pack_version_ok"] for row in task_results),
            "observed": _task_observed(task_results, "context_pack_version_ok"),
        },
        {
            "check_id": "prompt_registry_versions_are_current",
            "passed": all(row["prompt_registry_version_ok"] for row in task_results),
            "observed": _task_observed(task_results, "prompt_registry_version_ok"),
        },
        {
            "check_id": "task_context_pack_matches_prompt_contract",
            "passed": all(row["context_pack_match"] for row in task_results),
            "observed": _task_observed(task_results, "context_pack_match"),
        },
        {
            "check_id": "module_gate_excludes_forbidden_context",
            "passed": all(row["forbidden_module_absent"] for row in task_results),
            "observed": _task_observed(task_results, "forbidden_module_absent"),
        },
        {
            "check_id": "role_visibility_gate_is_enforced",
            "passed": all(row["role_visibility_gate_ok"] for row in task_results),
            "observed": _task_observed(task_results, "role_visibility_gate_ok"),
        },
        {
            "check_id": "context_budget_is_bounded",
            "passed": all(row["context_budget_ok"] for row in task_results),
            "observed": _task_observed(task_results, "budget"),
        },
        {
            "check_id": "bazi_llm_remains_read_only",
            "passed": all(row["read_only_boundary_ok"] for row in task_results),
            "observed": _task_observed(task_results, "read_only_boundary_ok"),
        },
        {
            "check_id": "verifier_and_fallback_are_present",
            "passed": all(row["verifier_fallback_ok"] for row in task_results),
            "observed": _task_observed(task_results, "verifier_fallback_ok"),
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": BAZI_LLM_CONTEXT_PROMPT_READINESS_VERSION,
        "task": {
            "task_id": "BL1-BL3",
            "title": "Bazi LLM Context Pack And Prompt Contract Readiness",
            "scope": "task_specific_llm_context_prompt_contracts_for_bazi_reading",
        },
        "task_results": task_results,
        "completion_summary": {
            "bazi_llm_context_compiler_completion": 70 if ready else 55,
            "prompt_contract_registry_completion": 65 if ready else 50,
            "context_budget_verifier_completion": 65 if ready else 45,
            "bazi_llm_mainline_completion": 55 if ready else 45,
            "current_scope_ready": ready,
        },
        "checks": checks,
        "decision": {
            "readiness_ready": ready,
            "decision_status": "bl1_bl3_bazi_llm_context_prompt_ready"
            if ready
            else "bl1_bl3_bazi_llm_context_prompt_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "llm_execution_performed": False,
            "chart_fact_mutation_allowed": False,
            "core_bazi_modules_reopened": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": {
            "task_id": "BL4" if ready else "BL1-BL3-FIX",
            "title": "Customer Bazi Reading LLM Answer Generator"
            if ready
            else "Fix Bazi LLM Context Prompt Contracts",
            "reason": "task_specific_context_and_prompt_contracts_are_ready"
            if ready
            else "context_prompt_readiness_checks_failed",
        },
        "boundary": "bazi_llm_context_prompt_readiness_does_not_execute_llm_or_mutate_bazi_facts",
    }


def _task_result(request: dict[str, object]) -> dict[str, object]:
    contract = _dict(request.get("prompt_contract"))
    context = _dict(request.get("context_pack"))
    contract_role = _dict(contract.get("role_contract"))
    context_role = _dict(context.get("role_contract"))
    budget = _dict(context.get("budget"))
    included = {str(row) for row in _list(context.get("included_modules"))}
    excluded = {str(row) for row in _list(context.get("excluded_modules"))}
    sections = _list(context.get("sections"))
    section_modules = {str(_dict(section).get("module_id")) for section in sections}
    forbidden_overlap = (included | section_modules) & excluded
    fact_boundary = _dict(context.get("fact_boundary"))
    task_type = str(request.get("task_type") or "")
    role_key = str(context.get("role_key") or contract.get("role_key") or "")
    forbidden_sections = {str(row) for row in _list(context_role.get("forbidden_sections"))}
    section_ids = [str(_dict(section).get("section_id")) for section in sections]
    return {
        "task_type": task_type,
        "role_key": role_key,
        "context_pack": context.get("context_pack", ""),
        "required_context_pack": contract.get("required_context_pack", ""),
        "context_pack_version_ok": context.get("version") == BAZI_LLM_CONTEXT_PACK_VERSION,
        "prompt_registry_version_ok": contract.get("version") == BAZI_LLM_PROMPT_REGISTRY_VERSION,
        "context_pack_match": context.get("context_pack") == contract.get("required_context_pack"),
        "role_visibility_gate_ok": (
            context_role.get("role_contract_id") == contract_role.get("role_contract_id")
            and task_type in {str(row) for row in _list(context_role.get("allowed_tasks"))}
            and not (set(section_ids) & forbidden_sections)
            and (
                bool(context_role.get("diagnostics_visible"))
                or "diagnostics_summary" not in section_ids
            )
        ),
        "forbidden_module_absent": not forbidden_overlap and request.get("raw_runtime_payload_included") is False,
        "context_budget_ok": (
            int(budget.get("observed_context_sections") or 0) <= int(budget.get("max_context_sections") or 0)
            and int(budget.get("observed_evidence_items") or 0) <= int(budget.get("max_evidence_items") or 0)
        ),
        "read_only_boundary_ok": (
            request.get("chart_fact_mutation_allowed") is False
            and fact_boundary.get("chart_fact_mutation_allowed") is False
            and fact_boundary.get("policy_pointer_write_allowed") is False
        ),
        "verifier_fallback_ok": bool(_dict(contract.get("verifier")).get("checks"))
        and bool(_dict(contract.get("fallback")).get("on_verifier_failure"))
        and bool(_dict(contract.get("output_schema")).get("required_fields")),
        "budget": budget,
        "included_modules": sorted(included),
        "excluded_modules": sorted(excluded),
        "section_ids": section_ids,
        "role_contract_id": context_role.get("role_contract_id", ""),
        "diagnostics_visible": context_role.get("diagnostics_visible", False),
        "forbidden_overlap": sorted(forbidden_overlap),
    }


def _task_observed(task_results: list[dict[str, object]], key: str) -> dict[str, object]:
    return {str(row["task_type"]): row.get(key) for row in task_results}


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []
