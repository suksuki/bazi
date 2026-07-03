from __future__ import annotations

import v30.llm.client as llm_client
from v30.llm import compose_bazi_llm_answer_draft
from v30.llm.provider import V30LLMProviderConfig
from v30.runtime import attach_question_outcome, create_smoke_runtime
from v30.validation import run_bazi_llm_answer_generator_readiness


def test_runtime_answer_result_uses_bazi_llm_prompt_request_metadata() -> None:
    runtime = create_smoke_runtime("pytest-bl4-runtime")

    assert runtime.answer_result is not None
    metadata = runtime.answer_result.llm_metadata
    prompt_request = metadata["prompt_request"]

    assert metadata["version"] == "v30.bazi_llm_answer_draft_call.v1"
    assert metadata["task_type"] == "customer_initial_reading"
    assert metadata["role_key"] == "user"
    assert prompt_request["version"] == "v30.bazi_llm_prompt_request.v1"
    assert prompt_request["context_pack"] == "BaziCoreContext"
    assert prompt_request["role_contract_id"] == "v30.bazi_llm_role.user.v1"
    assert prompt_request["raw_runtime_payload_included"] is False
    assert prompt_request["chart_fact_mutation_allowed"] is False


def test_product_default_executes_blocking_llm_when_no_fast_override(monkeypatch) -> None:
    monkeypatch.delenv("V30_LLM_SYNC_MODE", raising=False)
    monkeypatch.setattr(llm_client, "call_bazi_llm_answer_draft", _accepted_call)

    runtime = create_smoke_runtime("pytest-bl4-blocking-default")

    assert runtime.answer_result is not None
    assert runtime.answer_result.source == "llm_bazi_answer_draft"
    assert runtime.answer_result.llm_metadata["status"] == "accepted"
    assert runtime.answer_result.llm_metadata["executed"] is True
    assert runtime.answer_result.llm_metadata["sync_mode"] == "blocking"


def test_blocking_sync_mode_can_still_use_provider_path(monkeypatch) -> None:
    monkeypatch.setenv("V30_LLM_SYNC_MODE", "blocking")
    monkeypatch.setattr(llm_client, "call_bazi_llm_answer_draft", _accepted_call)
    runtime = create_smoke_runtime("pytest-bl4-blocking-mode")

    assert runtime.answer_result is not None
    assert runtime.answer_result.source == "llm_bazi_answer_draft"
    assert runtime.answer_result.llm_metadata["status"] == "accepted"
    assert runtime.answer_result.llm_metadata["executed"] is True


def test_fast_sync_mode_is_explicit_test_and_performance_path(monkeypatch) -> None:
    monkeypatch.setenv("V30_LLM_SYNC_MODE", "fast")
    runtime = create_smoke_runtime("pytest-bl4-fast-explicit")

    assert runtime.answer_result is not None
    assert runtime.answer_result.source == "rule_bound_llm_deferred"
    assert runtime.answer_result.llm_metadata["status"] == "deferred"
    assert runtime.answer_result.llm_metadata["fallback_reason"] == "sync_mode_fast_llm_deferred"
    assert runtime.answer_result.llm_metadata["executed"] is False
    assert runtime.answer_result.llm_metadata["llm_execution_required"] is False


def test_bazi_llm_answer_generator_fallback_preserves_rule_answer_by_role() -> None:
    runtime = create_smoke_runtime("pytest-bl4-guest")
    assert runtime.answer_context is not None
    assert runtime.answer_result is not None
    rule_text = runtime.answer_result.text

    answer = compose_bazi_llm_answer_draft(
        runtime,
        runtime.answer_context,
        runtime.answer_result,
        task_type="customer_initial_reading",
        role_key="guest",
        config=_disabled_config(),
    )

    assert answer.text == rule_text
    assert answer.source == "rule_bound_fallback"
    assert answer.llm_metadata["task_type"] == "customer_initial_reading"
    assert answer.llm_metadata["role_key"] == "guest"
    assert answer.llm_metadata["prompt_request"]["role_contract_id"] == "v30.bazi_llm_role.guest.v1"
    assert answer.llm_metadata["fallback_reason"] == "execute_flag_disabled"


def test_bazi_llm_answer_generator_selects_domain_followup_after_question_answer() -> None:
    runtime = create_smoke_runtime("pytest-bl4-followup")
    followup = attach_question_outcome(
        runtime,
        runtime.question_anchors[0].question_id,
        {"answer": "career", "selected_option": "career", "confidence": 0.8},
    )

    assert followup.answer_result is not None
    metadata = followup.answer_result.llm_metadata
    assert metadata["task_type"] == "domain_followup"
    assert metadata["prompt_request"]["context_pack"] == "BaziDomainContext"
    assert metadata["prompt_request"]["raw_runtime_payload_included"] is False


def test_bazi_llm_answer_generator_readiness_accepts_bl4() -> None:
    result = run_bazi_llm_answer_generator_readiness(reading_id="pytest-bl4-readiness")

    assert result["version"] == "v30.bazi_llm_answer_generator_readiness.v1"
    assert result["decision"]["decision_status"] == "bl4_bazi_llm_answer_generator_ready"
    assert result["decision"]["readiness_ready"] is True
    assert result["decision"]["llm_execution_required"] is False
    assert result["next_mainline_selection"]["task_id"] == "BL5"


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


def _accepted_call(*args, **kwargs) -> dict[str, object]:
    return {
        "version": "v30.bazi_llm_answer_draft_call.v1",
        "status": "accepted",
        "text": "结论：LLM 已按中枢裁决组织表达。\n建议：继续围绕已验证证据给出行动建议。",
        "executed": True,
        "sync_mode": "blocking",
        "task_type": str(kwargs.get("task_type") or "customer_initial_reading"),
        "role_key": str(kwargs.get("role_key") or "user"),
        "prompt_request": {
            "version": "v30.bazi_llm_prompt_request.v1",
            "context_pack": "BaziCoreContext",
            "role_contract_id": "v30.bazi_llm_role.user.v1",
            "raw_runtime_payload_included": False,
            "chart_fact_mutation_allowed": False,
        },
        "boundary": "bazi_llm_answer_draft_expression_only_no_chart_fact_mutation",
    }
