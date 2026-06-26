from __future__ import annotations

from pathlib import Path

from v30.validation import (
    build_core_chain_steady_state_summary,
    run_core_chain_steady_state_summary,
)


def _training(*, blocked: bool = False, full_gate: bool = False) -> dict[str, object]:
    ready = not blocked
    return {
        "version": "v30.training_synthetic_support_review.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "training_synthetic_support_ready" if ready else "training_synthetic_support_blocked",
            "training_synthetic_support_ready": ready,
            "training_pipeline_case_count": 91,
            "training_signal_count": 33,
            "sample_518k_case_count": 8,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "synthetic_all_required": full_gate,
            "full_pytest_required": full_gate,
            "full_518k_required": full_gate,
        },
    }


def _mcr2(
    *,
    blocked: bool = False,
    m3_completion: int = 100,
    policy_write: bool = False,
) -> dict[str, object]:
    ready = not blocked
    rows = [
        ("M1/M2", 100, "steady"),
        ("M3", m3_completion, "steady" if m3_completion == 100 else "active"),
        ("M4", 100, "steady"),
        ("M5", 100, "steady"),
        ("M6", 100, "steady"),
        ("M7", 100, "steady"),
        ("M8", 100, "steady"),
        ("SURFACE", 100, "steady"),
        ("CTX", 100, "steady"),
        ("IQ", 98, "steady"),
        ("LLM", 88, "bounded_steady"),
        ("BT", 100, "steady"),
        ("U", 100, "steady"),
    ]
    return {
        "version": "v30.customer_surface_bazi_context_reconciliation.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": (
                "mcr2_customer_surface_bazi_context_reconciled"
                if ready
                else "mcr2_customer_surface_bazi_context_blocked"
            ),
            "customer_surface_bazi_context_reconciled": ready,
            "passed_count": 6 if ready else 5,
            "check_count": 6,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": policy_write,
            "live_llm_required": False,
            "synthetic_all_required": False,
            "full_pytest_required": False,
            "full_518k_required": False,
        },
        "module_completion_matrix": [
            {"module_id": module_id, "completion": completion, "status": status}
            for module_id, completion, status in rows
        ],
    }


def test_core_chain_summary_ready(tmp_path: Path) -> None:
    result = build_core_chain_steady_state_summary(
        training_support=_training(),
        mcr2_reconciliation=_mcr2(),
        artifact_dir=tmp_path,
    )
    decision = result["decision"]

    assert result["version"] == "v30.core_chain_steady_state_summary.v1"
    assert result["status"] == "completed"
    assert decision["decision_status"] == "core_chain_steady_state_ready"
    assert decision["module_count"] == 13
    assert result["next_mainline_selection"]["next_task"] == "Evidence-Driven Calibration Queue"
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert Path(str(result["artifact_uri"])).exists()


def test_core_chain_summary_blocks_missing_training_or_mcr2() -> None:
    training_result = build_core_chain_steady_state_summary(
        training_support=_training(blocked=True),
        mcr2_reconciliation=_mcr2(),
    )
    mcr2_result = build_core_chain_steady_state_summary(
        training_support=_training(),
        mcr2_reconciliation=_mcr2(blocked=True),
    )

    assert training_result["status"] == "blocked"
    assert "bt_s1_training_support_ready" in training_result["decision"]["failed_check_ids"]
    assert mcr2_result["status"] == "blocked"
    assert "mcr2_surface_context_reconciled" in mcr2_result["decision"]["failed_check_ids"]


def test_core_chain_summary_blocks_module_or_write_boundary_gap() -> None:
    matrix_result = build_core_chain_steady_state_summary(
        training_support=_training(),
        mcr2_reconciliation=_mcr2(m3_completion=99),
    )
    write_result = build_core_chain_steady_state_summary(
        training_support=_training(),
        mcr2_reconciliation=_mcr2(policy_write=True),
    )

    assert "core_module_matrix_steady" in matrix_result["decision"]["failed_check_ids"]
    assert "no_write_or_fact_mutation_boundary" in write_result["decision"]["failed_check_ids"]


def test_core_chain_summary_runner_passes_targeted_gates(tmp_path: Path) -> None:
    result = run_core_chain_steady_state_summary(sample_limit=8, artifact_dir=tmp_path)

    assert result["decision"]["decision_status"] == "core_chain_steady_state_ready"
    assert result["decision"]["module_count"] >= 13
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["validation_cadence"]["full_pytest_required_by_default"] is False
    assert result["validation_cadence"]["full_518k_required_by_default"] is False
