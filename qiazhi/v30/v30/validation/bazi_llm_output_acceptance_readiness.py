from __future__ import annotations

from v30.llm import build_bazi_llm_prompt_request, validate_bazi_llm_output_payload
from v30.runtime import attach_question_outcome, create_smoke_runtime


BAZI_LLM_OUTPUT_ACCEPTANCE_READINESS_VERSION = "v30.bazi_llm_output_acceptance_readiness.v1"


def run_bazi_llm_output_acceptance_readiness(
    reading_id: str = "bl5-bazi-llm-output-acceptance",
) -> dict[str, object]:
    runtime = create_smoke_runtime(reading_id=reading_id)
    followup = attach_question_outcome(
        runtime,
        runtime.question_anchors[0].question_id,
        {"answer": "career", "selected_option": "career", "confidence": 0.8},
    )
    customer_request = build_bazi_llm_prompt_request(runtime, task_type="customer_initial_reading", role_key="user")
    followup_request = build_bazi_llm_prompt_request(
        followup,
        task_type="domain_followup",
        role_key="user",
        domain="career",
    )
    accepted_customer = validate_bazi_llm_output_payload(
        {
            "answer_text": "庚日主的命盘先看官杀压力能否被印星承接，事业和时运判断落在官印相生路径上。当前只沿已验证结构、画像和候选路径说明，不新增年份或固定结论。",
            "evidence_ids": ["evidence-1"],
            "boundaries": ["rule_bound_answer_no_llm_fact_mutation"],
            "next_question_hint": "继续确认一个近期反复出现的状态。",
        },
        prompt_request=customer_request,
        text="庚日主的命盘先看官杀压力能否被印星承接，事业和时运判断落在官印相生路径上。当前只沿已验证结构、画像和候选路径说明，不新增年份或固定结论。",
        drift_check={"passed": True, "failures": []},
    )
    accepted_followup = validate_bazi_llm_output_payload(
        {
            "domain": "career",
            "answer_text": "事业追问以庚日主的官杀压力和印星承接为核心，重点看职责、资质和平台能否形成官印相生路径。这里使用已知反馈和结构特征说明，不新增年份或固定结论。",
            "used_user_signals": ["career"],
            "boundaries": ["rule_bound_answer_no_llm_fact_mutation"],
        },
        prompt_request=followup_request,
        text="事业追问以庚日主的官杀压力和印星承接为核心，重点看职责、资质和平台能否形成官印相生路径。这里使用已知反馈和结构特征说明，不新增年份或固定结论。",
        drift_check={"passed": True, "failures": []},
    )
    rejected_missing_schema = validate_bazi_llm_output_payload(
        {"answer_text": "缺少证据和边界。"},
        prompt_request=customer_request,
        text="缺少证据和边界。",
        drift_check={"passed": True, "failures": []},
    )
    rejected_role_leak = validate_bazi_llm_output_payload(
        {
            "answer_text": "diagnostics policy v30.prompt_contract_id should be hidden",
            "evidence_ids": ["evidence-1"],
            "boundaries": ["rule_bound_answer_no_llm_fact_mutation"],
            "next_question_hint": "hidden",
        },
        prompt_request=customer_request,
        text="diagnostics policy v30.prompt_contract_id should be hidden",
        drift_check={"passed": True, "failures": []},
    )
    rejected_drift = validate_bazi_llm_output_payload(
        {
            "answer_text": "In 2027 this will definitely happen.",
            "evidence_ids": ["evidence-1"],
            "boundaries": ["rule_bound_answer_no_llm_fact_mutation"],
            "next_question_hint": "hidden",
        },
        prompt_request=customer_request,
        text="In 2027 this will definitely happen.",
        drift_check={"passed": False, "failures": ["unsupported_deterministic_timing_claim"]},
    )
    return build_bazi_llm_output_acceptance_readiness(
        acceptance_results={
            "customer_initial_reading_accepted": accepted_customer,
            "domain_followup_accepted": accepted_followup,
            "missing_schema_rejected": rejected_missing_schema,
            "role_leak_rejected": rejected_role_leak,
            "drift_rejected": rejected_drift,
        }
    )


def build_bazi_llm_output_acceptance_readiness(
    *,
    acceptance_results: dict[str, dict[str, object]],
) -> dict[str, object]:
    checks = [
        {
            "check_id": "accepted_outputs_pass_schema_role_and_drift",
            "passed": all(
                acceptance_results[key]["accepted"] is True
                for key in ("customer_initial_reading_accepted", "domain_followup_accepted")
            ),
            "observed": {
                key: acceptance_results[key]
                for key in ("customer_initial_reading_accepted", "domain_followup_accepted")
            },
        },
        {
            "check_id": "missing_schema_fields_are_rejected",
            "passed": acceptance_results["missing_schema_rejected"]["accepted"] is False
            and bool(acceptance_results["missing_schema_rejected"]["missing_fields"]),
            "observed": acceptance_results["missing_schema_rejected"],
        },
        {
            "check_id": "customer_role_visibility_leaks_are_rejected",
            "passed": acceptance_results["role_leak_rejected"]["accepted"] is False
            and bool(acceptance_results["role_leak_rejected"]["role_failures"]),
            "observed": acceptance_results["role_leak_rejected"],
        },
        {
            "check_id": "drift_failures_are_rejected_before_text_replacement",
            "passed": acceptance_results["drift_rejected"]["accepted"] is False
            and bool(acceptance_results["drift_rejected"]["drift_failures"]),
            "observed": acceptance_results["drift_rejected"],
        },
        {
            "check_id": "accepted_outputs_remain_non_mutating",
            "passed": all(
                row["chart_fact_mutation_allowed"] is False
                and row["raw_runtime_payload_included"] is False
                for row in acceptance_results.values()
            ),
            "observed": {
                key: {
                    "chart_fact_mutation_allowed": row["chart_fact_mutation_allowed"],
                    "raw_runtime_payload_included": row["raw_runtime_payload_included"],
                }
                for key, row in acceptance_results.items()
            },
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": BAZI_LLM_OUTPUT_ACCEPTANCE_READINESS_VERSION,
        "task": {
            "task_id": "BL5",
            "title": "Bazi LLM Output Schema And Drift Acceptance Gate",
            "scope": "schema_role_and_drift_gate_before_llm_text_replaces_rule_bound_answer",
        },
        "acceptance_results": acceptance_results,
        "completion_summary": {
            "bazi_llm_answer_generator_completion": 78 if ready else 70,
            "bazi_llm_output_acceptance_completion": 72 if ready else 50,
            "bazi_llm_mainline_completion": 70 if ready else 65,
            "current_scope_ready": ready,
        },
        "checks": checks,
        "decision": {
            "readiness_ready": ready,
            "decision_status": "bl5_bazi_llm_output_acceptance_ready"
            if ready
            else "bl5_bazi_llm_output_acceptance_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "live_llm_required": False,
            "chart_fact_mutation_allowed": False,
            "core_bazi_modules_reopened": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": {
            "task_id": "BL6" if ready else "BL5-FIX",
            "title": "Bazi LLM Training Signals And Synthetic Tier"
            if ready
            else "Fix Bazi LLM Output Acceptance",
            "reason": "output_acceptance_gate_is_ready"
            if ready
            else "output_acceptance_checks_failed",
        },
        "boundary": "bl5_readiness_uses_deterministic_payloads_and_does_not_execute_live_llm_or_mutate_bazi_facts",
    }
