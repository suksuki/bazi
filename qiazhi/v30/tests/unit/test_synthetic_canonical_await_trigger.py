from __future__ import annotations

from v30.validation import run_synthetic_canonical_await_trigger
from v30.validation.synthetic_canonical_await_trigger import (
    SYNTHETIC_CANONICAL_AWAIT_TRIGGER_VERSION,
    build_synthetic_canonical_await_trigger,
)


def _steady(*, ready: bool = True) -> dict[str, object]:
    return {
        "version": "v30.synthetic_canonical_steady_state.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "synthetic_canonical_steady_state_ready": ready,
            "decision_status": "scal_s3_synthetic_canonical_steady_state_ready" if ready else "blocked",
            "routine_gate_ready": ready,
            "case_count": 16,
            "covered_family_count": 10,
        },
        "routine_gate": {
            "gate_status": "frozen_targeted_gate" if ready else "blocked",
            "case_count": 16,
            "family_count": 10,
        },
        "policy_boundary": {
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
        },
    }


def test_scal_s3_wait_ready_without_trigger() -> None:
    result = build_synthetic_canonical_await_trigger(
        synthetic_canonical_steady_state=_steady(),
    )

    assert result["version"] == SYNTHETIC_CANONICAL_AWAIT_TRIGGER_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "scal_s3_await_trigger_ready"
    assert result["decision"]["waiting_for_synthetic_canonical_trigger"] is True
    assert result["decision"]["synthetic_canonical_gate_run_required"] is False
    assert result["next_mainline_selection"]["next_task"] == "Await Synthetic Canonical Trigger"


def test_scal_s3_wait_routes_known_trigger_to_gate_run() -> None:
    result = build_synthetic_canonical_await_trigger(
        synthetic_canonical_steady_state=_steady(),
        active_triggers=["rbd_change"],
    )

    assert result["decision"]["waiting_for_synthetic_canonical_trigger"] is False
    assert result["decision"]["synthetic_canonical_gate_run_required"] is True
    assert result["decision"]["active_trigger_ids"] == ["rbd_change"]
    assert result["next_mainline_selection"]["next_task"] == "Run Synthetic Canonical Gate"


def test_scal_s3_wait_blocks_unknown_trigger_or_missing_steady_state() -> None:
    unknown = build_synthetic_canonical_await_trigger(
        synthetic_canonical_steady_state=_steady(),
        active_triggers=["unknown"],
    )
    blocked = build_synthetic_canonical_await_trigger(
        synthetic_canonical_steady_state=_steady(ready=False),
    )

    assert "trigger_ids_are_known" in unknown["decision"]["failed_check_ids"]
    assert unknown["status"] == "blocked"
    assert "scal_s3_steady_state_ready" in blocked["decision"]["failed_check_ids"]


def test_scal_s3_wait_runner_passes_current_gate() -> None:
    result = run_synthetic_canonical_await_trigger()

    assert result["decision"]["decision_status"] == "scal_s3_await_trigger_ready"
    assert result["decision"]["waiting_for_synthetic_canonical_trigger"] is True
    assert result["decision"]["case_count"] >= 16
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
