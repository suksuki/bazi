from __future__ import annotations

from copy import deepcopy

from v30.validation.central_brain_failure_routing import (
    CENTRAL_BRAIN_FAILURE_ROUTING_VERSION,
    build_central_brain_failure_routing,
    run_central_brain_failure_routing,
)


def _bt2_ready() -> dict[str, object]:
    return {
        "version": "v30.central_brain_session_replay.v1",
        "status": "completed",
        "decision": {
            "central_brain_session_replay_ready": True,
            "decision_status": "bt2_central_brain_session_replay_ready",
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
    }


def test_bt3_brain_failure_routing_ready() -> None:
    result = run_central_brain_failure_routing()

    assert result["version"] == CENTRAL_BRAIN_FAILURE_ROUTING_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "bt3_brain_failure_routing_ready"
    assert result["decision"]["central_brain_completion"] == 97
    assert result["decision"]["passed_routing_check_count"] == 6
    assert result["decision"]["queued_route_count"] >= 5
    assert {row["module_target"] for row in result["task_queue"]} >= {
        "M8 projection leak",
        "question strategy",
        "hidden-factor feedback",
        "training candidate",
        "release/full validation",
    }
    assert result["policy_boundary"]["operator_plan_only"] is True
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["policy_boundary"]["policy_pointer_write_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "BT4"


def test_bt3_blocks_pointer_write_pressure() -> None:
    result = build_central_brain_failure_routing(
        bt2_session_replay=_bt2_ready(),
        failure_events=[
            {
                "event_id": "bad-pointer",
                "failure_type": "training_candidate",
                "pointer_write_requested": True,
            }
        ],
    )

    assert result["status"] == "blocked"
    assert "no_chart_pointer_or_heavy_validation_by_default" in result["decision"]["failed_check_ids"]
    assert result["decision"]["policy_pointer_promotion_allowed"] is False


def test_bt3_blocks_missing_bt2_dependency() -> None:
    bt2 = deepcopy(_bt2_ready())
    bt2["decision"]["central_brain_session_replay_ready"] = False  # type: ignore[index]

    result = build_central_brain_failure_routing(
        bt2_session_replay=bt2,
        failure_events=[{"event_id": "projection", "failure_type": "projection_leak"}],
    )

    assert result["status"] == "blocked"
    assert "bt2_session_replay_ready" in result["decision"]["failed_check_ids"]


def test_bt3_routes_all_required_failure_families() -> None:
    events = [
        {"event_id": "birth", "failure_type": "birth_input_boundary"},
        {"event_id": "facts", "failure_type": "chart_fact_mutation"},
        {"event_id": "m3", "failure_type": "m3_knowledge_gap"},
        {"event_id": "m4", "failure_type": "model_signal_drift"},
        {"event_id": "m5", "failure_type": "ranked_decision_drift"},
        {"event_id": "m6", "failure_type": "practical_reading_contract"},
        {"event_id": "m8", "failure_type": "projection_leak"},
        {"event_id": "question", "failure_type": "question_strategy"},
        {"event_id": "hidden", "failure_type": "hidden_factor_feedback"},
        {"event_id": "training", "failure_type": "training_candidate"},
        {"event_id": "release", "failure_type": "release_full_validation"},
    ]
    result = build_central_brain_failure_routing(
        bt2_session_replay=_bt2_ready(),
        failure_events=events,
    )

    assert result["status"] == "completed"
    assert {row["module_target"] for row in result["route_items"]} >= {
        "M1/M2 fact boundary",
        "M3 evidence/rule/path gap",
        "M4/M5 calibration",
        "M6 practical reading contract",
        "M8 projection leak",
        "question strategy",
        "hidden-factor feedback",
        "training candidate",
        "release/full validation",
    }
    assert all(row["operator_plan_only"] for row in result["route_items"])
