from __future__ import annotations

from v30.llm.acceptance import validate_bazi_llm_output_payload
from v30.llm.prompt_registry import build_bazi_llm_prompt_request
from v30.runtime import create_smoke_runtime
from v30.validation.llm_answer_output_delta_review import (
    LLM_ANSWER_OUTPUT_DELTA_REVIEW_VERSION,
    run_llm_answer_output_delta_review,
)


def test_llm_answer_output_delta_review_accepts_quality_gate() -> None:
    result = run_llm_answer_output_delta_review(reading_id="pytest-core-evidence-4")

    assert result["version"] == LLM_ANSWER_OUTPUT_DELTA_REVIEW_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["llm_answer_output_delta_ready"] is True
    assert result["decision"]["failed_check_ids"] == []
    assert result["quality_summary"]["accepted_quality_rows"] >= 4
    assert result["quality_summary"]["rejection_quality_rows"] >= 1
    assert result["next_mainline_selection"]["task_id"] == "CORE-EVIDENCE-5"


def test_llm_output_acceptance_rejects_generic_bazi_free_customer_text() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-core-evidence-4-generic")
    request = build_bazi_llm_prompt_request(runtime, task_type="customer_initial_reading", role_key="user")
    result = validate_bazi_llm_output_payload(
        {
            "answer_text": "当前回答只按已验证的趋势边界说明，后续需要结合问题继续观察。",
            "evidence_ids": ["evidence-1"],
            "boundaries": ["rule_bound_answer_no_llm_fact_mutation"],
            "next_question_hint": "继续确认问题。",
        },
        prompt_request=request,
        text="当前回答只按已验证的趋势边界说明，后续需要结合问题继续观察。",
        drift_check={"passed": True, "failures": []},
    )

    assert result["accepted"] is False
    assert result["content_quality_passed"] is False
    assert "missing_bazi_mechanism_language" in result["content_failures"]


def test_llm_output_acceptance_accepts_concrete_bazi_customer_text() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-core-evidence-4-concrete")
    request = build_bazi_llm_prompt_request(runtime, task_type="customer_initial_reading", role_key="user")
    result = validate_bazi_llm_output_payload(
        {
            "answer_text": (
                "庚日主的命盘先看官杀压力能否被印星承接，事业和时运判断落在官印相生路径上。"
                "当前只沿已验证结构、画像和候选路径说明，不新增年份或固定结论。"
            ),
            "evidence_ids": ["evidence-1"],
            "boundaries": ["rule_bound_answer_no_llm_fact_mutation"],
            "next_question_hint": "继续确认一个近期反复出现的状态。",
        },
        prompt_request=request,
        text=(
            "庚日主的命盘先看官杀压力能否被印星承接，事业和时运判断落在官印相生路径上。"
            "当前只沿已验证结构、画像和候选路径说明，不新增年份或固定结论。"
        ),
        drift_check={"passed": True, "failures": []},
    )

    assert result["accepted"] is True
    assert result["content_quality_passed"] is True
    assert result["content_failures"] == []
