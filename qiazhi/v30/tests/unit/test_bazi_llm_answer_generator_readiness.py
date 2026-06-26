from __future__ import annotations

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


def test_default_runtime_defers_live_llm_to_keep_answer_fast(monkeypatch) -> None:
    monkeypatch.delenv("V30_LLM_SYNC_MODE", raising=False)
    runtime = create_smoke_runtime("pytest-bl4-fast-default")

    assert runtime.answer_result is not None
    assert runtime.answer_result.source == "rule_bound_llm_deferred"
    assert runtime.answer_result.llm_metadata["status"] == "deferred"
    assert runtime.answer_result.llm_metadata["fallback_reason"] == "sync_mode_fast_llm_deferred"
    assert runtime.answer_result.llm_metadata["executed"] is False
    assert runtime.answer_result.llm_metadata["llm_execution_required"] is False


def test_blocking_sync_mode_can_still_use_provider_path(monkeypatch) -> None:
    monkeypatch.setenv("V30_LLM_SYNC_MODE", "blocking")
    runtime = create_smoke_runtime("pytest-bl4-blocking-mode")

    assert runtime.answer_result is not None
    assert runtime.answer_result.llm_metadata["status"] in {"fallback", "accepted"}
    assert runtime.answer_result.llm_metadata["status"] != "deferred"


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
