from __future__ import annotations

from v30.validation import run_bazi_llm_closeout


def test_bazi_llm_closeout_accepts_bl1_bl7_evidence() -> None:
    result = run_bazi_llm_closeout(reading_id="pytest-bl8-closeout")

    assert result["version"] == "v30.bazi_llm_closeout.v1"
    assert result["decision"]["decision_status"] == "bl8_bazi_llm_steady_state_ready"
    assert result["decision"]["closeout_ready"] is True
    assert result["decision"]["bazi_llm_steady_state"] is True
    assert result["next_mainline_selection"]["task_id"] == "BL-S1"
    assert set(result["accepted_evidence"]) == {"bl1_bl3", "bl4", "bl5", "bl6", "bl7"}
    assert all(row["ready"] for row in result["accepted_evidence"].values())


def test_bazi_llm_closeout_keeps_live_smoke_explicit_only() -> None:
    result = run_bazi_llm_closeout(reading_id="pytest-bl8-live-boundary")
    decision = result["decision"]
    live_check = next(row for row in result["checks"] if row["check_id"] == "optional_live_smoke_boundary_is_explicit")

    assert decision["optional_live_smoke_allowed"] is True
    assert decision["live_llm_required"] is False
    assert decision["full_pytest_required"] is False
    assert decision["synthetic_all_required"] is False
    assert decision["full_518k_required"] is False
    assert live_check["observed"]["default_live_smoke"] is False
    assert live_check["observed"]["requires_explicit_operator_or_release_boundary"] is True


def test_bazi_llm_closeout_preserves_core_and_training_boundaries() -> None:
    result = run_bazi_llm_closeout(reading_id="pytest-bl8-boundaries")
    decision = result["decision"]
    training_check = next(row for row in result["checks"] if row["check_id"] == "training_targets_remain_expression_and_question_strategy")

    assert decision["chart_fact_mutation_allowed"] is False
    assert decision["policy_pointer_write_allowed"] is False
    assert decision["core_bazi_modules_reopened"] is False
    assert training_check["observed"]["can_tune_expression"] is True
    assert training_check["observed"]["can_tune_question_strategy"] is True
    assert training_check["observed"]["can_tune_chart_facts"] is False
