from __future__ import annotations

from v30.llm import compose_bazi_llm_answer_draft
from v30.llm.provider import V30LLMProviderConfig
from v30.runtime import attach_question_outcome, create_smoke_runtime
from v30.validation import run_bazi_llm_output_acceptance_readiness


def test_bazi_llm_accepts_schema_valid_fake_provider_output(monkeypatch) -> None:
    from v30.llm import client as client_module

    def fake_provider(prompt, config):
        return {
            "answer_text": "庚日主的命盘先看官杀压力是否被印星承接，事业判断落在官印相生和结构路径上。当前只按已验证特征说明，不新增年份或固定结论。",
            "evidence_ids": ["evidence-1"],
            "boundaries": ["rule_bound_answer_no_llm_fact_mutation"],
            "next_question_hint": "继续确认一个近期反复出现的状态。",
        }

    monkeypatch.setattr(client_module, "_post_ollama_native_completion", fake_provider)
    runtime = create_smoke_runtime("pytest-bl5-accepted")
    assert runtime.answer_context is not None
    assert runtime.answer_result is not None

    answer = compose_bazi_llm_answer_draft(
        runtime,
        runtime.answer_context,
        runtime.answer_result,
        task_type="customer_initial_reading",
        role_key="user",
        config=_execute_config(),
    )

    assert answer.source == "llm_bazi_answer_draft"
    assert answer.llm_metadata["status"] == "accepted"
    assert answer.llm_metadata["output_acceptance"]["accepted"] is True
    assert answer.llm_metadata["output_acceptance"]["schema_id"] == "BaziCustomerAnswerDraft"


def test_bazi_llm_wraps_plain_text_provider_output(monkeypatch) -> None:
    from v30.llm import client as client_module

    def fake_provider(prompt, config):
        return {"text": "庚日主的命盘事业侧重点看官杀压力与印星承接，按官印相生路径说明结构特征，不新增年份或固定结论。"}

    monkeypatch.setattr(client_module, "_post_ollama_native_completion", fake_provider)
    runtime = create_smoke_runtime("pytest-bl5-plain-text-wrap")
    assert runtime.answer_context is not None
    assert runtime.answer_result is not None

    answer = compose_bazi_llm_answer_draft(
        runtime,
        runtime.answer_context,
        runtime.answer_result,
        task_type="customer_initial_reading",
        role_key="user",
        config=_execute_config(),
    )

    assert answer.source == "llm_bazi_answer_draft"
    assert answer.llm_metadata["status"] == "accepted"
    assert answer.llm_metadata["output_acceptance"]["accepted"] is True


def test_bazi_llm_rejects_schema_invalid_fake_provider_output(monkeypatch) -> None:
    from v30.llm import client as client_module

    def fake_provider(prompt, config):
        return {"answer_text": "缺少边界和证据。"}

    monkeypatch.setattr(client_module, "_post_ollama_native_completion", fake_provider)
    runtime = create_smoke_runtime("pytest-bl5-schema-reject")
    assert runtime.answer_context is not None
    assert runtime.answer_result is not None

    answer = compose_bazi_llm_answer_draft(
        runtime,
        runtime.answer_context,
        runtime.answer_result,
        task_type="customer_initial_reading",
        role_key="user",
        config=_execute_config(),
    )

    assert answer.source == "rule_bound_fallback"
    assert answer.llm_metadata["fallback_reason"] == "output_acceptance_failed"
    assert "evidence_ids" in answer.llm_metadata["output_acceptance"]["missing_fields"]
    assert answer.llm_metadata["output_acceptance"]["accepted"] is False


def test_bazi_llm_rejects_customer_role_diagnostic_leak(monkeypatch) -> None:
    from v30.llm import client as client_module

    def fake_provider(prompt, config):
        return {
            "answer_text": "diagnostics policy v30.prompt_contract_id should be hidden",
            "evidence_ids": ["evidence-1"],
            "boundaries": ["rule_bound_answer_no_llm_fact_mutation"],
            "next_question_hint": "hidden",
        }

    monkeypatch.setattr(client_module, "_post_ollama_native_completion", fake_provider)
    runtime = create_smoke_runtime("pytest-bl5-role-reject")
    assert runtime.answer_context is not None
    assert runtime.answer_result is not None

    answer = compose_bazi_llm_answer_draft(
        runtime,
        runtime.answer_context,
        runtime.answer_result,
        task_type="customer_initial_reading",
        role_key="user",
        config=_execute_config(),
    )

    assert answer.source == "rule_bound_fallback"
    assert answer.llm_metadata["fallback_reason"] == "output_acceptance_failed"
    assert answer.llm_metadata["output_acceptance"]["role_visibility_passed"] is False


def test_bazi_llm_rejects_customer_answer_internal_chinese_sections(monkeypatch) -> None:
    from v30.llm import client as client_module

    def fake_provider(prompt, config):
        return {
            "answer_text": "基础判断：强弱取相对平衡。路径复核：官杀到印星。llm_bazi_answer_draft · LLM accepted",
            "evidence_ids": ["evidence-1"],
            "boundaries": ["rule_bound_answer_no_llm_fact_mutation"],
            "next_question_hint": "继续确认当前最关心的问题。",
        }

    monkeypatch.setattr(client_module, "_post_ollama_native_completion", fake_provider)
    runtime = create_smoke_runtime("pytest-bl5-chinese-internal-reject")
    assert runtime.answer_context is not None
    assert runtime.answer_result is not None

    answer = compose_bazi_llm_answer_draft(
        runtime,
        runtime.answer_context,
        runtime.answer_result,
        task_type="customer_initial_reading",
        role_key="user",
        config=_execute_config(),
    )

    assert answer.source == "rule_bound_fallback"
    assert answer.llm_metadata["fallback_reason"] == "output_acceptance_failed"
    assert answer.llm_metadata["output_acceptance"]["role_visibility_passed"] is False
    assert any("基础判断：" in failure for failure in answer.llm_metadata["output_acceptance"]["role_failures"])


def test_bazi_llm_accepts_domain_followup_schema_valid_output(monkeypatch) -> None:
    from v30.llm import client as client_module

    def fake_provider(prompt, config):
        return {
            "domain": "career",
            "answer_text": "事业追问以庚日主的官杀压力和印星承接为核心，看职责、资质和平台能否形成官印相生路径。这里只沿结构特征和已知反馈说明，不新增年份或固定结论。",
            "used_user_signals": ["career"],
            "boundaries": ["rule_bound_answer_no_llm_fact_mutation"],
        }

    monkeypatch.setattr(client_module, "_post_ollama_native_completion", fake_provider)
    runtime = create_smoke_runtime("pytest-bl5-followup-accepted")
    followup = attach_question_outcome(
        runtime,
        runtime.question_anchors[0].question_id,
        {"answer": "career", "selected_option": "career", "confidence": 0.8},
    )
    assert followup.answer_context is not None
    assert followup.answer_result is not None

    answer = compose_bazi_llm_answer_draft(
        followup,
        followup.answer_context,
        followup.answer_result,
        task_type="domain_followup",
        role_key="user",
        domain="career",
        config=_execute_config(),
    )

    assert answer.source == "llm_bazi_answer_draft"
    assert answer.llm_metadata["output_acceptance"]["schema_id"] == "BaziDomainFollowupAnswer"
    assert answer.llm_metadata["output_acceptance"]["accepted"] is True


def test_bazi_llm_output_acceptance_readiness_accepts_bl5() -> None:
    result = run_bazi_llm_output_acceptance_readiness(reading_id="pytest-bl5-readiness")

    assert result["version"] == "v30.bazi_llm_output_acceptance_readiness.v1"
    assert result["decision"]["decision_status"] == "bl5_bazi_llm_output_acceptance_ready"
    assert result["decision"]["readiness_ready"] is True
    assert result["decision"]["live_llm_required"] is False
    assert result["next_mainline_selection"]["task_id"] == "BL6"


def _execute_config() -> V30LLMProviderConfig:
    return V30LLMProviderConfig(
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
