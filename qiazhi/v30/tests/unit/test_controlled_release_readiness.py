from __future__ import annotations

from v30.validation import run_controlled_release_readiness
from v30.validation.controlled_release_readiness import (
    CONTROLLED_RELEASE_READINESS_VERSION,
    build_controlled_release_readiness,
)


def _scal_wait(*, ready: bool = True) -> dict[str, object]:
    return {
        "version": "v30.synthetic_canonical_await_trigger.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "synthetic_canonical_await_trigger_ready": ready,
            "decision_status": "scal_s3_await_trigger_ready" if ready else "blocked",
            "waiting_for_synthetic_canonical_trigger": ready,
            "synthetic_canonical_gate_run_required": False,
            "case_count": 16,
            "covered_family_count": 10,
        },
    }


def _scal_steady() -> dict[str, object]:
    return {
        "version": "v30.synthetic_canonical_steady_state.v1",
        "status": "completed",
        "decision": {
            "synthetic_canonical_steady_state_ready": True,
            "decision_status": "scal_s3_synthetic_canonical_steady_state_ready",
            "routine_gate_ready": True,
            "case_count": 16,
            "covered_family_count": 10,
        },
    }


def _rbd() -> dict[str, object]:
    return {
        "version": "v30.real_bazi_diagnosis_steady_state.v1",
        "status": "completed",
        "decision": {
            "rbd_steady_state_ready": True,
            "decision_status": "rbd_s113_steady_state_ready",
            "rbd_mainline_closed_for_current_scope": True,
            "training_signal_count": 4,
            "queued_item_count": 2,
            "full_pytest_required": False,
            "full_518k_required": False,
        },
    }


def _api() -> dict[str, object]:
    return {
        "version": "v30.bazi_backend_api_journey_acceptance.v1",
        "status": "completed",
        "decision": {
            "api_journey_ready": True,
            "decision_status": "ir2_bazi_backend_api_journey_accepted",
            "check_count": 6,
            "passed_check_count": 6,
            "live_llm_required": False,
            "chart_fact_mutation_allowed": False,
        },
        "journey_summary": {
            "created_status": "ready",
            "projection_contract_version": "v30.api_projection_contract.v1",
            "answer_accepted": True,
            "interaction_state_version": "v30.interaction_state.v1",
            "history_count": 1,
        },
    }


def _runtime() -> dict[str, object]:
    return {
        "repository": "memory",
        "database_url_configured": False,
        "redis_url_configured": False,
        "redis_prefix": "v30",
        "llm_enabled": False,
        "llm_execute": False,
        "real_env_smoke_run": False,
        "live_llm_smoke_run": False,
        "full_pytest_run": False,
    }


def test_rel_s1_controlled_release_readiness_ready() -> None:
    result = build_controlled_release_readiness(
        synthetic_canonical_await_trigger=_scal_wait(),
        synthetic_canonical_steady_state=_scal_steady(),
        real_bazi_diagnosis_steady_state=_rbd(),
        backend_api_journey_acceptance=_api(),
        runtime_config=_runtime(),
    )

    assert result["version"] == CONTROLLED_RELEASE_READINESS_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "rel_s1_controlled_release_readiness_ready"
    assert result["decision"]["controlled_trial_ready"] is True
    assert result["decision"]["external_release_ready"] is False
    assert result["decision"]["full_pytest_required"] is False
    assert result["release_boundary_policy"]["full_pytest_required_before_external_release"] is True
    assert result["next_mainline_selection"]["task_id"] == "REL-S2"


def test_rel_s1_blocks_missing_scal_wait_or_api_journey() -> None:
    scal_blocked = build_controlled_release_readiness(
        synthetic_canonical_await_trigger=_scal_wait(ready=False),
        synthetic_canonical_steady_state=_scal_steady(),
        real_bazi_diagnosis_steady_state=_rbd(),
        backend_api_journey_acceptance=_api(),
        runtime_config=_runtime(),
    )
    api_blocked = build_controlled_release_readiness(
        synthetic_canonical_await_trigger=_scal_wait(),
        synthetic_canonical_steady_state=_scal_steady(),
        real_bazi_diagnosis_steady_state=_rbd(),
        backend_api_journey_acceptance={**_api(), "journey_summary": {"created_status": "blocked"}},
        runtime_config=_runtime(),
    )

    assert "synthetic_canonical_gate_waiting_without_trigger" in scal_blocked["decision"]["failed_check_ids"]
    assert "backend_api_customer_journey_ready" in api_blocked["decision"]["failed_check_ids"]


def test_rel_s1_runner_passes_targeted_readiness() -> None:
    result = run_controlled_release_readiness(reading_id="pytest-rel-s1")

    assert result["decision"]["decision_status"] == "rel_s1_controlled_release_readiness_ready"
    assert result["decision"]["external_release_ready"] is False
    assert result["policy_boundary"]["full_pytest_required"] is False
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
