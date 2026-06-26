from __future__ import annotations

from v30.contracts import CoreRuntimeResult
from v30.llm import compose_bazi_llm_answer_draft
from v30.llm.provider import V30LLMProviderConfig
from v30.runtime import attach_question_outcome, create_smoke_runtime


BAZI_LLM_ANSWER_GENERATOR_READINESS_VERSION = "v30.bazi_llm_answer_generator_readiness.v1"


def run_bazi_llm_answer_generator_readiness(
    reading_id: str = "bl4-bazi-llm-answer-generator",
) -> dict[str, object]:
    runtime = create_smoke_runtime(reading_id=reading_id)
    followup_runtime = attach_question_outcome(
        runtime,
        runtime.question_anchors[0].question_id,
        {
            "answer": "career focus",
            "selected_option": "career",
            "confidence": 0.8,
            "feedback_tags": ["domain_followup"],
        },
    )
    return build_bazi_llm_answer_generator_readiness(
        initial_runtime=runtime,
        followup_runtime=followup_runtime,
    )


def build_bazi_llm_answer_generator_readiness(
    *,
    initial_runtime: CoreRuntimeResult,
    followup_runtime: CoreRuntimeResult,
) -> dict[str, object]:
    initial_answer = _compose_with_disabled_provider(initial_runtime, task_type="customer_initial_reading", role_key="user")
    guest_answer = _compose_with_disabled_provider(initial_runtime, task_type="customer_initial_reading", role_key="guest")
    practitioner_answer = _compose_with_disabled_provider(
        initial_runtime,
        task_type="practitioner_analysis",
        role_key="practitioner",
    )
    followup_answer = _compose_with_disabled_provider(followup_runtime, task_type="domain_followup", role_key="user")
    answer_results = {
        "customer_initial_reading_user": _answer_observation(initial_runtime, initial_answer),
        "customer_initial_reading_guest": _answer_observation(initial_runtime, guest_answer),
        "practitioner_analysis_practitioner": _answer_observation(initial_runtime, practitioner_answer),
        "domain_followup_user": _answer_observation(followup_runtime, followup_answer),
    }
    checks = [
        {
            "check_id": "bazi_answer_uses_task_specific_prompt_request",
            "passed": all(row["prompt_request_version_ok"] and row["context_pack_present"] for row in answer_results.values()),
            "observed": answer_results,
        },
        {
            "check_id": "role_contracts_are_preserved_in_answer_metadata",
            "passed": all(row["role_contract_present"] for row in answer_results.values()),
            "observed": {key: row["role_contract_id"] for key, row in answer_results.items()},
        },
        {
            "check_id": "rule_bound_fallback_is_preserved_when_provider_not_executed",
            "passed": all(row["source"] == "rule_bound_fallback" and row["executed"] is False for row in answer_results.values()),
            "observed": {key: {"source": row["source"], "executed": row["executed"]} for key, row in answer_results.items()},
        },
        {
            "check_id": "customer_and_followup_tasks_are_covered",
            "passed": {
                answer_results["customer_initial_reading_user"]["task_type"],
                answer_results["domain_followup_user"]["task_type"],
            } == {"customer_initial_reading", "domain_followup"},
            "observed": {key: row["task_type"] for key, row in answer_results.items()},
        },
        {
            "check_id": "no_raw_runtime_or_chart_mutation_in_prompt_request",
            "passed": all(
                row["raw_runtime_payload_included"] is False and row["chart_fact_mutation_allowed"] is False
                for row in answer_results.values()
            ),
            "observed": {
                key: {
                    "raw_runtime_payload_included": row["raw_runtime_payload_included"],
                    "chart_fact_mutation_allowed": row["chart_fact_mutation_allowed"],
                }
                for key, row in answer_results.items()
            },
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": BAZI_LLM_ANSWER_GENERATOR_READINESS_VERSION,
        "task": {
            "task_id": "BL4",
            "title": "Customer Bazi Reading LLM Answer Generator",
            "scope": "runtime_answer_generation_uses_bazi_task_role_context_prompt_contracts",
        },
        "answer_results": answer_results,
        "completion_summary": {
            "bazi_llm_context_compiler_completion": 78 if ready else 72,
            "prompt_contract_registry_completion": 74 if ready else 68,
            "context_budget_verifier_completion": 72 if ready else 68,
            "bazi_llm_answer_generator_completion": 70 if ready else 55,
            "bazi_llm_mainline_completion": 65 if ready else 58,
            "current_scope_ready": ready,
        },
        "checks": checks,
        "decision": {
            "readiness_ready": ready,
            "decision_status": "bl4_bazi_llm_answer_generator_ready"
            if ready
            else "bl4_bazi_llm_answer_generator_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "llm_execution_required": False,
            "chart_fact_mutation_allowed": False,
            "core_bazi_modules_reopened": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": {
            "task_id": "BL5" if ready else "BL4-FIX",
            "title": "Bazi LLM Output Schema And Drift Acceptance Gate"
            if ready
            else "Fix Bazi LLM Answer Generator",
            "reason": "answer_generation_uses_task_role_context_prompt_contracts"
            if ready
            else "answer_generator_readiness_checks_failed",
        },
        "boundary": "bl4_readiness_uses_disabled_provider_and_does_not_execute_live_llm_or_mutate_bazi_facts",
    }


def _compose_with_disabled_provider(
    runtime: CoreRuntimeResult,
    *,
    task_type: str,
    role_key: str,
):
    assert runtime.answer_context is not None
    assert runtime.answer_result is not None
    return compose_bazi_llm_answer_draft(
        runtime,
        runtime.answer_context,
        runtime.answer_result,
        task_type=task_type,
        role_key=role_key,
        config=_disabled_config(),
    )


def _answer_observation(runtime: CoreRuntimeResult, answer) -> dict[str, object]:
    metadata = answer.llm_metadata
    prompt_request = metadata.get("prompt_request", {}) if isinstance(metadata, dict) else {}
    return {
        "reading_id": runtime.reading_id,
        "answer_id": answer.answer_id,
        "source": answer.source,
        "metadata_version": metadata.get("version", ""),
        "status": metadata.get("status", ""),
        "fallback_reason": metadata.get("fallback_reason", ""),
        "executed": metadata.get("executed", None),
        "task_type": metadata.get("task_type", ""),
        "role_key": metadata.get("role_key", ""),
        "prompt_request_version_ok": prompt_request.get("version") == "v30.bazi_llm_prompt_request.v1",
        "context_pack_present": bool(prompt_request.get("context_pack")),
        "role_contract_present": bool(prompt_request.get("role_contract_id")),
        "role_contract_id": prompt_request.get("role_contract_id", ""),
        "raw_runtime_payload_included": prompt_request.get("raw_runtime_payload_included", True),
        "chart_fact_mutation_allowed": prompt_request.get("chart_fact_mutation_allowed", True),
    }


def _disabled_config() -> V30LLMProviderConfig:
    return V30LLMProviderConfig(
        enabled=True,
        execute_llm=False,
        provider="ollama_native",
        host="127.0.0.1",
        port=11434,
        base_url="http://127.0.0.1:11434/v1",
        model="qwen-test",
        api_key_env="V30_LLM_API_KEY",
        http_timeout_sec=0.1,
        temperature=0.2,
        max_tokens=120,
        config_source="test",
    )
