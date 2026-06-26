from __future__ import annotations

import os

from v30.llm import (
    V30LLMProviderConfig,
    build_answer_draft_contract,
    build_failure_cluster_summary_contract,
    build_llm_role_prompt_context,
    build_question_explanation_contract,
    build_synthetic_case_draft_contract,
    check_llm_answer_drift,
    compose_llm_answer_draft,
    llm_provider_readiness_report,
    load_v30_llm_provider_config_from_env,
)
from v30.runtime import create_smoke_runtime
from v30.validation import run_llm_live_smoke


def test_llm_prompt_context_preserves_answer_boundaries_by_role() -> None:
    runtime = create_smoke_runtime("v30-llm-context-test")
    assert runtime.answer_context is not None
    prompt_context = build_llm_role_prompt_context(runtime.answer_context, role_key="analyst")
    assert prompt_context.role_key == "analyst"
    assert "rule_bound_answer_no_llm_fact_mutation" in prompt_context.answer_boundaries
    assert "evidence_summary" in prompt_context.allowed_context_blocks
    assert "Do not create new chart facts." in prompt_context.system_constraints
    assert prompt_context.user_context["selected_question_id"] == runtime.answer_result.question_id


def test_llm_drift_checker_blocks_unbound_timing_claims() -> None:
    runtime = create_smoke_runtime("v30-llm-drift-test")
    assert runtime.answer_context is not None
    prompt_context = build_llm_role_prompt_context(runtime.answer_context, role_key="user")
    result = check_llm_answer_drift("In 2027 this will definitely happen.", prompt_context)
    assert result.passed is False
    assert "unsupported_deterministic_timing_claim" in result.failures


def test_llm_drift_checker_accepts_bound_answer_text() -> None:
    runtime = create_smoke_runtime("v30-llm-drift-pass-test")
    assert runtime.answer_context is not None
    assert runtime.answer_result is not None
    prompt_context = build_llm_role_prompt_context(runtime.answer_context, role_key="user")
    result = check_llm_answer_drift(runtime.answer_result.text, prompt_context)
    assert result.passed is True


def test_llm_output_contracts_validate_answer_and_question_explanation() -> None:
    runtime = create_smoke_runtime("v30-llm-output-contract-test")
    assert runtime.answer_context is not None
    assert runtime.answer_result is not None
    answer_contract = build_answer_draft_contract(runtime.answer_context, runtime.answer_result, role_key="user")
    question_contract = build_question_explanation_contract(runtime.answer_context, role_key="user")
    synthetic_contract = build_synthetic_case_draft_contract(runtime.answer_context, role_key="lab")
    failure_contract = build_failure_cluster_summary_contract(
        runtime.answer_context,
        failures=["missing_macro_signal_domains:wealth"],
        role_key="lab",
    )
    summary = runtime.question_plan.policy_effect["llm_output_contract_summary"]
    assert answer_contract.task_type == "answer_draft"
    assert answer_contract.validation_status == "passed"
    assert question_contract.task_type == "question_explanation"
    assert question_contract.validation_status == "passed"
    assert synthetic_contract.task_type == "synthetic_case_draft"
    assert synthetic_contract.output_schema == "SyntheticCaseDraft"
    assert synthetic_contract.validation_status == "passed"
    assert failure_contract.task_type == "failure_cluster_summary"
    assert failure_contract.output_schema == "FailureClusterSummary"
    assert failure_contract.validation_status == "passed"
    assert "answer_draft" in summary["task_types"]
    assert "question_explanation" in summary["task_types"]
    assert "synthetic_case_draft" in summary["task_types"]
    assert "failure_cluster_summary" in summary["task_types"]
    assert summary["contract_count"] == 4
    assert summary["validation_status"] == "passed"


def test_v30_llm_config_can_reuse_v20_env_shape_without_v20_import(monkeypatch) -> None:
    for name in list(os.environ):
        if name.startswith("V30_LLM_"):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("V20_LLM_ENABLED", "1")
    monkeypatch.setenv("V20_LLM_EXECUTE", "0")
    monkeypatch.setenv("V20_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("V20_LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    monkeypatch.setenv("V20_LLM_MODEL", "qwen-test")

    config = load_v30_llm_provider_config_from_env()
    readiness = llm_provider_readiness_report(config)

    assert config.config_source == "legacy_compat"
    assert config.model == "qwen-test"
    assert readiness["ready_for_connection"] is True
    assert readiness["boundary"] == "llm_readiness_reuses_legacy_env_shape_not_legacy_runtime_or_chart_fact"


def test_llm_answer_draft_falls_back_when_execute_flag_disabled() -> None:
    runtime = create_smoke_runtime("v30-llm-fallback-test")
    assert runtime.answer_context is not None
    assert runtime.answer_result is not None
    config = V30LLMProviderConfig(
        enabled=True,
        execute_llm=False,
        provider="ollama",
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

    answer = compose_llm_answer_draft(runtime.answer_context, runtime.answer_result, config=config)

    assert answer.text == runtime.answer_result.text
    assert answer.source == "rule_bound_fallback"
    assert answer.llm_metadata["fallback_reason"] == "execute_flag_disabled"
    assert answer.llm_metadata["boundary"] == "llm_fallback_keeps_rule_answer_and_does_not_mutate_chart_facts"


def test_llm_live_smoke_reports_unconfigured_without_failure(monkeypatch) -> None:
    for name in (
        "V30_LLM_ENABLED",
        "V30_LLM_EXECUTE",
        "V30_LLM_BASE_URL",
        "V30_LLM_HOST",
        "V30_LLM_MODEL",
        "V20_LLM_ENABLED",
        "V20_LLM_EXECUTE",
        "V20_LLM_BASE_URL",
        "V20_LLM_HOST",
        "V20_LLM_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    result = run_llm_live_smoke(reading_id="v30-llm-live-unconfigured-test", write_artifact=False)

    assert result.passed is True
    assert result.summary["smoke_status"] == "unconfigured"
    assert result.summary["call_status"] == "fallback"
    assert result.summary["fallback_reason"] == "provider_not_ready"
    assert result.summary["no_chart_fact_mutation_proof"]["chart_facts_unchanged"] is True
    assert result.summary["no_chart_fact_mutation_proof"]["ranked_decisions_unchanged"] is True
    assert result.summary["no_chart_fact_mutation_proof"]["model_signal_unchanged"] is True
    assert result.summary["no_chart_fact_mutation_proof"]["interaction_state_unchanged"] is True


def test_llm_live_smoke_reports_configured_not_executed() -> None:
    config = V30LLMProviderConfig(
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

    result = run_llm_live_smoke(reading_id="v30-llm-live-disabled-test", config=config, write_artifact=False)

    assert result.passed is True
    assert result.summary["configured"] is True
    assert result.summary["smoke_status"] == "configured_not_executed"
    assert result.summary["fallback_reason"] == "execute_flag_disabled"
    assert result.summary["executed"] is False


def test_llm_live_smoke_reports_drift_rejected_without_runtime_mutation() -> None:
    config = V30LLMProviderConfig(
        enabled=True,
        execute_llm=True,
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

    def fake_call(answer_context, rule_answer, reading_surface, config):
        return {
            "version": "v30.llm_answer_draft_call.v1",
            "status": "fallback",
            "fallback_reason": "drift_check_failed",
            "text": "In 2027 this will definitely happen.",
            "executed": True,
            "readiness": {
                "version": "v30.llm_provider_readiness.v1",
                "enabled": True,
                "execute_llm": True,
                "provider": "ollama_native",
                "model": "qwen-test",
                "ready_for_connection": True,
                "config_source": "test",
            },
            "drift_check": {
                "passed": False,
                "failures": ["unsupported_deterministic_timing_claim"],
            },
            "boundary": "llm_fallback_keeps_rule_answer_and_does_not_mutate_chart_facts",
        }

    result = run_llm_live_smoke(
        reading_id="v30-llm-live-drift-test",
        config=config,
        write_artifact=False,
        llm_call=fake_call,
    )

    assert result.passed is True
    assert result.summary["smoke_status"] == "drift_rejected"
    assert result.summary["executed"] is True
    assert result.summary["drift_passed"] is False
    assert result.summary["drift_failures"] == ["unsupported_deterministic_timing_claim"]
    assert result.summary["no_chart_fact_mutation_proof"]["chart_facts_unchanged"] is True
