from __future__ import annotations

from v30.validation import run_explicit_release_gate_authorization
from v30.validation.explicit_release_gate_authorization import (
    EXPLICIT_RELEASE_GATE_AUTHORIZATION_VERSION,
    build_explicit_release_gate_authorization,
)


def _readiness(*, ready: bool = True) -> dict[str, object]:
    return {
        "version": "v30.controlled_release_readiness.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "rel_s1_controlled_release_readiness_ready" if ready else "blocked",
            "controlled_release_readiness_ready": ready,
            "controlled_trial_ready": ready,
            "external_release_ready": False,
            "real_env_configured": False,
        },
        "policy_boundary": {
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
    }


def test_rel_s2_authorizes_stage_a_without_running_gates() -> None:
    result = build_explicit_release_gate_authorization(controlled_release_readiness=_readiness())

    assert result["version"] == EXPLICIT_RELEASE_GATE_AUTHORIZATION_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "rel_s2_stage_a_gates_authorized_pending_execution"
    assert result["decision"]["authorized_gate_ids"] == [
        "controlled_release_readiness",
        "synthetic_all",
        "518k_sample",
        "518k_shard",
    ]
    assert result["decision"]["runs_triggered"] is False
    assert result["decision"]["external_release_allowed"] is False
    assert result["decision"]["full_pytest_authorized"] is False
    assert result["decision"]["live_llm_smoke_authorized"] is False
    assert result["decision"]["real_env_smoke_authorized"] is False
    assert result["decision"]["full_518k_authorized"] is False
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "REL-S3"


def test_rel_s2_can_defer_all_gates() -> None:
    result = build_explicit_release_gate_authorization(
        controlled_release_readiness=_readiness(),
        authorization_decision="defer_all",
    )

    assert result["decision"]["decision_status"] == "rel_s2_all_gates_deferred"
    assert result["decision"]["authorized_gate_ids"] == []
    assert result["decision"]["runs_triggered"] is False
    assert result["next_mainline_selection"]["task_id"] == "MCR3"


def test_rel_s2_blocks_when_rel_s1_is_not_ready() -> None:
    result = build_explicit_release_gate_authorization(controlled_release_readiness=_readiness(ready=False))

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "rel_s2_authorization_blocked"
    assert "controlled_release_readiness_not_ready" in result["decision"]["blockers"]
    assert result["decision"]["authorized_gate_ids"] == []
    assert result["next_mainline_selection"]["task_id"] == "REL-S2-FR"


def test_rel_s2_runner_records_authorization() -> None:
    result = run_explicit_release_gate_authorization(reading_id="pytest-rel-s2")

    assert result["decision"]["decision_status"] == "rel_s2_stage_a_gates_authorized_pending_execution"
    assert result["decision"]["runs_triggered"] is False
    assert "synthetic_all" in result["decision"]["authorized_gate_ids"]
    assert "full_pytest" in result["decision"]["deferred_gate_ids"]
