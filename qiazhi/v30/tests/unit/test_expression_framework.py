from __future__ import annotations

from v30.expression import build_runtime_narrative_plan, render_narrative
from v30.runtime import create_smoke_runtime


def test_expression_framework_renders_bazi_language_without_engineering_leakage() -> None:
    runtime = create_smoke_runtime("v30-expression-user")
    assert runtime.answer_context is not None
    assert runtime.answer_result is not None
    effect = runtime.question_plan.policy_effect

    assert effect["expression_framework_version"] == "v30.expression.framework.v1"
    assert effect["llm_output_contract_version"] == "v30.llm.output_contracts.v1"
    rendered = effect["rendered_narrative"]
    assert "日主" in rendered["text"]
    assert "原局" in rendered["text"]
    assert rendered["diagnostics"]["forbidden_token_hits"] == []
    assert runtime.answer_result.text == rendered["text"]
    assert "Quality gate" not in runtime.answer_result.text
    assert "policy_effect" not in runtime.answer_result.text
    assert "evidence-bound" not in runtime.answer_result.text
    assert "Current chart" not in runtime.answer_result.text
    assert effect["llm_output_contract_summary"]["validation_status"] == "passed"
    assert effect["llm_output_contract_summary"]["contract_count"] == 4
    assert effect["adaptive_question_diagnostics"]["runtime_focus"]
    assert effect["adaptive_question_diagnostics"]["policy_weight_summary"]["active_question_policy"]


def test_expression_framework_supports_role_specific_projection_density() -> None:
    runtime = create_smoke_runtime("v30-expression-practitioner")
    assert runtime.answer_context is not None

    user_plan = build_runtime_narrative_plan(runtime, answer_context=runtime.answer_context, role_key="user")
    practitioner_plan = build_runtime_narrative_plan(
        runtime,
        answer_context=runtime.answer_context,
        role_key="practitioner",
    )
    user_text = render_narrative(user_plan).text
    practitioner_text = render_narrative(practitioner_plan).text

    assert len(practitioner_plan.frames) >= len(user_plan.frames)
    assert "画像投射" in practitioner_text
    assert "画像投射" not in user_text


def test_expression_framework_consumes_central_brain_role_state() -> None:
    runtime = create_smoke_runtime("v30-expression-role-state")
    assert runtime.answer_context is not None

    plan = build_runtime_narrative_plan(
        runtime,
        answer_context=runtime.answer_context,
        role_state={
            "role_key": "practitioner",
            "answer_density": "diagnostic",
            "expression_voice": "dense_bazi_practitioner",
            "client": "web",
        },
    )

    assert plan.style_profile.role_key == "practitioner"
    assert plan.style_profile.density == "diagnostic"
    assert plan.style_profile.voice == "dense_bazi_practitioner"
