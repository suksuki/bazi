from __future__ import annotations

from pathlib import Path

from v30.validation import (
    build_m6_practical_reading_closeout,
    run_m6_practical_reading_closeout,
)


def _hardening(
    *,
    blocked: bool = False,
    bad_training_boundary: bool = False,
    raw_leak: bool = False,
    business_blocked: bool = False,
) -> dict[str, object]:
    ready = not blocked
    return {
        "version": "v30.m6_practical_reading_consumption_hardening.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "m6_practical_reading_consumption_hardening_ready" if ready else "m6_practical_reading_consumption_hardening_blocked",
            "m6_consumption_hardening_ready": ready,
            "m6_practical_reading_support_ready": ready,
            "ready_for_m6_closeout": ready,
            "hardening_check_count": 8,
            "passed_hardening_check_count": 8 if ready else 7,
            "domain_payload_count": 125,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
        },
        "practical_reading_consumption_summary": {
            "domain_payload_count": 125,
            "required_domains": ["career", "wealth", "relationship", "health", "timing"],
            "domain_counts": {
                "career": 25,
                "wealth": 25,
                "relationship": 25,
                "health": 25,
                "timing": 25,
            },
            "blocked_claim_count": 250,
            "raw_score_leak_count": 1 if raw_leak else 0,
            "raw_model_score_visible_count": 0,
            "chart_fact_mutation_allowed_count": 0,
            "module_trace_count": 125,
            "evidence_bound_count": 125,
            "explanation_unit_count": 375,
            "action_step_count": 375,
            "calibration_prompt_count": 250,
        },
        "business_reading_summary": {
            "business_bazi_reading_ready": not business_blocked,
            "answer_refresh_regression_ready": not business_blocked,
            "business_ready_case_count": 12,
            "business_m6_practical_ready_count": 9 if business_blocked else 12,
            "customer_projection_leak_free_count": 12,
            "passed_answer_case_count": 4 if business_blocked else 5,
        },
        "training_signal_summary": {
            "practical_reading_quality_present": True,
            "quality_boundary": (
                "bad_boundary"
                if bad_training_boundary
                else "v30.training_signal.practical_reading_quality_validates_runtime_context_not_chart_fact"
            ),
        },
        "synthetic_summary": {
            "m6_practical_reading_contract": {"passed": True, "case_count": 30},
            "real_case_calibration_pack": {"passed": True, "case_count": 30},
        },
    }


def test_m6_practical_reading_closeout_ready(tmp_path: Path) -> None:
    result = build_m6_practical_reading_closeout(
        consumption_hardening=_hardening(),
        artifact_dir=tmp_path,
    )
    decision = result["decision"]

    assert result["version"] == "v30.m6_practical_reading_closeout.v1"
    assert result["status"] == "completed"
    assert decision["decision_status"] == "m6_practical_reading_closed"
    assert decision["m6_steady_customer_reading_support_ready"] is True
    assert decision["m6_ready_for_iq_consumption"] is True
    assert decision["m6_ready_for_llm_context_consumption"] is True
    assert decision["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["next_task"] == "M7 Real-Case Calibration Steady-State Review"
    assert Path(str(result["artifact_uri"])).exists()


def test_m6_practical_reading_closeout_blocks_missing_h1() -> None:
    result = build_m6_practical_reading_closeout(consumption_hardening=_hardening(blocked=True))

    assert result["status"] == "blocked"
    assert "m6_h1_consumption_hardening_ready" in result["decision"]["failed_closeout_check_ids"]


def test_m6_practical_reading_closeout_blocks_business_surface_gap() -> None:
    result = build_m6_practical_reading_closeout(consumption_hardening=_hardening(business_blocked=True))

    assert result["status"] == "blocked"
    assert "m6_business_surface_stable" in result["decision"]["failed_closeout_check_ids"]


def test_m6_practical_reading_closeout_blocks_guardrail_gap() -> None:
    result = build_m6_practical_reading_closeout(consumption_hardening=_hardening(raw_leak=True))

    assert result["status"] == "blocked"
    assert "m6_customer_claim_guardrails_locked" in result["decision"]["failed_closeout_check_ids"]


def test_m6_practical_reading_closeout_blocks_training_boundary_gap() -> None:
    result = build_m6_practical_reading_closeout(consumption_hardening=_hardening(bad_training_boundary=True))

    assert result["status"] == "blocked"
    assert "m6_synthetic_and_training_lineage_complete" in result["decision"]["failed_closeout_check_ids"]


def test_m6_practical_reading_closeout_runner_passes_targeted_gates(tmp_path: Path) -> None:
    result = run_m6_practical_reading_closeout(sample_limit=8, artifact_dir=tmp_path)

    assert result["decision"]["decision_status"] == "m6_practical_reading_closed"
    assert result["decision"]["domain_payload_count"] >= 100
    assert result["decision"]["m6_ready_for_iq_consumption"] is True
