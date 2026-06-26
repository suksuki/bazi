from __future__ import annotations

from pathlib import Path

from v30.validation import (
    build_m8_projection_api_contract_closeout,
    run_m8_projection_api_contract_closeout,
)


def _m7(*, blocked: bool = False) -> dict[str, object]:
    ready = not blocked
    return {
        "version": "v30.m7_real_case_calibration_closeout.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "m7_real_case_calibration_closed" if ready else "m7_real_case_calibration_closeout_blocked",
            "m7_real_case_calibration_closed": ready,
            "m7_ready_for_m8_projection_api_closeout": ready,
            "real_case_fixture_count": 30,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
    }


def _contract(*, leak: bool = False, admin_missing: bool = False, additive_gap: bool = False) -> dict[str, object]:
    must_preserve = [
        "reading_surface",
        "core_bazi_reading",
        "domain_cards",
        "questions",
        "answer_panel",
        "next_question_id",
        "visible_next_question_id",
        "internal_next_question_id",
        "actor_context",
        "llm_runtime_status",
        "diagnostics",
        "projection_contract",
    ]
    if additive_gap:
        must_preserve = ["reading_surface"]
    return {
        "api_projection_contract": {
            "version": "v30.api_projection_contract.v1",
            "customer_surface_order": ["core_bazi_reading", "domain_cards", "questions"],
            "core_first_projection": {
                "calculation_before_questions": True,
                "required_surface_prefix": ["core_bazi_reading", "domain_cards"],
            },
            "customer_surface_contract": {"surface_prefix_ready": True},
            "additive_api_policy": {"must_preserve": must_preserve},
            "customer_forbidden_fields": {
                "fields": ["raw_score", "raw_weight", "training_signal", "policy_effect", "internal_next_question_id"],
            },
            "leak_scan": {
                "passed": not leak,
                "diagnostics_hidden": not leak,
                "forbidden_token_hits": ["raw_score"] if leak else [],
            },
        },
        "admin_api_projection_contract": {
            "diagnostics_visible": not admin_missing,
        },
    }


def _projection(
    *,
    count: int = 30,
    leak: bool = False,
    admin_missing: bool = False,
    additive_gap: bool = False,
    bad_boundary: bool = False,
) -> dict[str, object]:
    return {
        "suite_id": "v30.synthetic.m8_api_projection_contract",
        "passed": not leak and not admin_missing and not additive_gap,
        "case_count": count,
        "results": [
            {
                "case_id": f"case_{idx}",
                "passed": not leak and not admin_missing and not additive_gap,
                "observed": _contract(
                    leak=leak,
                    admin_missing=admin_missing,
                    additive_gap=additive_gap,
                ),
            }
            for idx in range(count)
        ],
        "training_signals": [
            {
                "signal_id": "v30.training_signal.api_projection_contract",
                "domain": "presentation",
                "signal_type": "api_projection_contract_coverage",
                "strength": 1.0,
                "source_case_ids": [f"case_{idx}" for idx in range(count)],
                "payload": {
                    "contract_observation_count": count,
                    "user_contract_ready_count": count,
                    "user_leak_pass_count": 29 if leak else count,
                    "admin_diagnostic_ready_count": 29 if admin_missing else count,
                    "core_first_count": count,
                    "core_first_policy_count": count,
                    "customer_surface_contract_ready_count": count,
                    "additive_policy_count": 29 if additive_gap else count,
                    "forbidden_field_policy_count": count,
                    "required_additive_fields": [],
                    "boundary": (
                        "bad_boundary"
                        if bad_boundary
                        else "api_projection_contract_trains_visibility_policy_not_chart_facts"
                    ),
                },
            }
        ],
    }


def _api_freeze(*, blocked: bool = False) -> dict[str, object]:
    ready = not blocked
    return {
        "version": "v30.real_business_api_contract_freeze.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "b5_business_api_contract_frozen" if ready else "b5_business_api_contract_freeze_blocked",
            "api_contract_freeze_ready": ready,
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
        "freeze_summary": {
            "gate_count": 4,
            "passed_gate_count": 4 if ready else 3,
            "business_endpoint_count": 6,
            "customer_surface_key_count": 8,
        },
        "api_contract": {
            "version": "v30.business_reading_api_contract.v1",
            "additive_api_policy": {
                "field_removal_allowed": False,
                "new_fields_allowed": True,
                "must_preserve": ["reading_surface", "core_bazi_reading"],
            },
        },
    }


def test_m8_projection_api_contract_closeout_ready(tmp_path: Path) -> None:
    result = build_m8_projection_api_contract_closeout(
        m7_closeout=_m7(),
        projection_synthetic=_projection(),
        api_freeze=_api_freeze(),
        artifact_dir=tmp_path,
    )
    decision = result["decision"]

    assert result["version"] == "v30.m8_projection_api_contract_closeout.v1"
    assert result["status"] == "completed"
    assert decision["decision_status"] == "m8_projection_api_contract_closed"
    assert decision["projection_contract_count"] == 30
    assert result["next_mainline_selection"]["next_task"] == "IQ Intelligent Question Support Review"
    assert Path(str(result["artifact_uri"])).exists()


def test_m8_closeout_blocks_missing_m7_backbone() -> None:
    result = build_m8_projection_api_contract_closeout(
        m7_closeout=_m7(blocked=True),
        projection_synthetic=_projection(),
        api_freeze=_api_freeze(),
    )

    assert result["status"] == "blocked"
    assert "m7_backbone_ready_for_m8" in result["decision"]["failed_closeout_check_ids"]


def test_m8_closeout_blocks_projection_leak_or_additive_gap() -> None:
    leak_result = build_m8_projection_api_contract_closeout(
        m7_closeout=_m7(),
        projection_synthetic=_projection(leak=True),
        api_freeze=_api_freeze(),
    )
    additive_result = build_m8_projection_api_contract_closeout(
        m7_closeout=_m7(),
        projection_synthetic=_projection(additive_gap=True),
        api_freeze=_api_freeze(),
    )

    assert leak_result["status"] == "blocked"
    assert additive_result["status"] == "blocked"
    assert "m8_projection_contract_synthetic_ready" in leak_result["decision"]["failed_closeout_check_ids"]
    assert "m8_core_first_additive_forbidden_contract_ready" in additive_result["decision"]["failed_closeout_check_ids"]


def test_m8_closeout_blocks_api_freeze_gap() -> None:
    result = build_m8_projection_api_contract_closeout(
        m7_closeout=_m7(),
        projection_synthetic=_projection(),
        api_freeze=_api_freeze(blocked=True),
    )

    assert result["status"] == "blocked"
    assert "business_api_freeze_ready" in result["decision"]["failed_closeout_check_ids"]


def test_m8_closeout_blocks_training_boundary_gap() -> None:
    result = build_m8_projection_api_contract_closeout(
        m7_closeout=_m7(),
        projection_synthetic=_projection(bad_boundary=True),
        api_freeze=_api_freeze(),
    )

    assert result["status"] == "blocked"
    assert "m8_training_boundary_locked" in result["decision"]["failed_closeout_check_ids"]


def test_m8_projection_api_contract_closeout_runner_passes_targeted_gates(tmp_path: Path) -> None:
    result = run_m8_projection_api_contract_closeout(sample_limit=8, artifact_dir=tmp_path)

    assert result["decision"]["decision_status"] == "m8_projection_api_contract_closed"
    assert result["decision"]["projection_case_count"] >= 30
    assert result["decision"]["projection_contract_count"] >= 20
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
