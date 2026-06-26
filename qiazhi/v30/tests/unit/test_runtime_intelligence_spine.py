from __future__ import annotations

from v30.runtime import create_smoke_runtime


def test_runtime_exposes_krp_library_hidden_calibration_and_answer_context() -> None:
    runtime = create_smoke_runtime("runtime-intelligence")
    effect = runtime.question_plan.policy_effect
    assert effect["krp_library_units"]
    assert effect["hidden_factor_calibration"]["status"] in {"needs_dialogue", "feedback_calibrated"}
    assert runtime.answer_context is not None
    assert runtime.answer_result is not None
    assert runtime.answer_result.boundary == "rule_bound_answer_no_llm_fact_mutation"
    assert effect["llm_output_contract_summary"]["validation_status"] == "passed"
    assert set(effect["llm_output_contract_summary"]["task_types"]) >= {
        "answer_draft",
        "question_explanation",
        "synthetic_case_draft",
        "failure_cluster_summary",
    }
    diagnostics = effect["adaptive_question_diagnostics"]
    assert diagnostics["version"] == "v30.adaptive_question_diagnostics.v1"
    assert diagnostics["decision_count"] == len(runtime.question_plan.recommended_questions)
    assert diagnostics["decision_rows"][0]["question_id"] == runtime.question_plan.recommended_questions[0]["question_id"]
    assert diagnostics["alignment_status"] in {
        "brain_graph_and_rank_aligned",
        "graph_and_rank_aligned",
        "brain_strategy_recorded",
    }
    assert diagnostics["replay_controls"]["can_replay_from_runtime_trace"] is True
    assert "adaptive_question_diagnostics_are_trace_replay_not_chart_fact" in diagnostics["boundaries"]


def test_runtime_hidden_factor_feedback_calibrates_amplifier_candidate() -> None:
    runtime = create_smoke_runtime("runtime-hidden-calibrated", hidden_factor_user_calibrated=True)
    calibration = runtime.question_plan.policy_effect["hidden_factor_calibration"]
    assert calibration["status"] == "feedback_calibrated"
    assert calibration["amplifier_candidate"] is True
    assert calibration["hypothesis_strength"] > 0.7


def test_dynamic_graph_v2_reaches_mainline_and_question_reasons() -> None:
    runtime = create_smoke_runtime("runtime-dynamic-v2")
    assert "Dynamic graph v2 paths are extracted" in runtime.mainline_state.why_selected
    assert any(
        "dynamic_graph_paths_scored" in row.get("reasons", [])
        for row in runtime.question_plan.recommended_questions
    )


def test_macro_dimension_signals_reach_question_and_answer_context() -> None:
    runtime = create_smoke_runtime("runtime-macro-question-answer")
    assert any(
        any(str(reason).startswith("macro_dimension_context:") for reason in row.get("reasons", []))
        for row in runtime.question_plan.recommended_questions
    )
    assert runtime.answer_context is not None
    contract = runtime.answer_context.role_answer_contract
    assert "macro_dimension_signals" in contract["can_use"]
    assert "macro_portrait_projections" in contract["can_use"]
    assert "macro_portrait_projection_views" in contract["can_use"]
    assert contract["macro_dimension_signals"]
    assert contract["macro_portrait_projections"]
    assert contract["macro_portrait_projection_views"]
    assert any("Do not" in boundary for boundary in runtime.answer_context.knowledge_boundaries)


def test_macro_portrait_projections_are_traceable_and_bounded() -> None:
    runtime = create_smoke_runtime("runtime-macro-portrait")
    projections = runtime.question_plan.policy_effect["macro_portrait_projections"]
    summary = runtime.question_plan.policy_effect["macro_portrait_summary"]
    domains = {row["domain"] for row in projections}
    assert domains >= {"wealth", "career", "relationship", "romance", "health", "hidden_factor"}
    assert all(row["source_policy"] == "portrait_is_projection_not_fact_source" for row in projections)
    assert all(row["evidence_ids"] for row in projections)
    assert summary["projection_count"] == len(projections)
    assert summary["source_policy"] == "portrait_is_projection_not_fact_source"
    view_summary = runtime.question_plan.policy_effect["macro_portrait_view_summary"]
    assert view_summary["view_count"] == len(runtime.question_plan.policy_effect["macro_portrait_projection_views"])
    assert view_summary["roles"] == ["user"]
    assert "boundary_visible" in view_summary["visibility"]
