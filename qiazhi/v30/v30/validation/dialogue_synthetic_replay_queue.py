from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from v30.config import V30Settings
from v30.training.dialogue_synthetic_replay_queue import (
    DIALOGUE_SYNTHETIC_REPLAY_QUEUE_VERSION,
    build_dialogue_synthetic_replay_queue,
    run_dialogue_synthetic_replay_queue,
)


DIALOGUE_SYNTHETIC_REPLAY_QUEUE_VALIDATION_VERSION = "v30.dialogue_synthetic_replay_queue_validation.v1"


def run_dialogue_synthetic_replay_queue_validation(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dtc4-dialogue-synthetic-replay-queue",
    persist_review: bool = True,
    settings: V30Settings | None = None,
) -> dict[str, object]:
    queue = run_dialogue_synthetic_replay_queue(
        runtime_payloads=runtime_payloads,
        sample_limit=sample_limit,
        run_id=run_id,
        persist_review=persist_review,
        settings=settings,
    )
    return build_dialogue_synthetic_replay_queue_validation(queue_result=queue)


def build_dialogue_synthetic_replay_queue_validation(
    *,
    queue_result: Mapping[str, Any],
) -> dict[str, object]:
    queue = dict(queue_result)
    decision = _mapping(queue.get("decision"))
    boundary = _mapping(queue.get("policy_boundary"))
    aggregate = _mapping(queue.get("aggregate"))
    checks = [
        _check(
            "queue_completed",
            queue.get("version") == DIALOGUE_SYNTHETIC_REPLAY_QUEUE_VERSION
            and queue.get("status") == "completed",
            {"queue_version": queue.get("version"), "queue_status": queue.get("status")},
        ),
        _check(
            "batch_replay_stable",
            aggregate.get("stable_enough_for_operator_review") is True
            and float(aggregate.get("pass_ratio") or 0.0) >= 1.0,
            {
                "stable_enough_for_operator_review": aggregate.get("stable_enough_for_operator_review"),
                "pass_ratio": aggregate.get("pass_ratio"),
                "case_count": aggregate.get("case_count"),
            },
        ),
        _check(
            "operator_review_only",
            decision.get("candidate_ready_for_operator_review") is True
            and decision.get("promotion_allowed") is False
            and decision.get("policy_pointer_write_allowed") is False,
            {
                "candidate_ready_for_operator_review": decision.get("candidate_ready_for_operator_review"),
                "promotion_allowed": decision.get("promotion_allowed"),
                "policy_pointer_write_allowed": decision.get("policy_pointer_write_allowed"),
            },
        ),
        _check(
            "chart_fact_boundary_safe",
            decision.get("chart_fact_mutation_allowed") is False
            and boundary.get("chart_fact_mutation_allowed") is False,
            {
                "decision_chart_fact_mutation_allowed": decision.get("chart_fact_mutation_allowed"),
                "boundary_chart_fact_mutation_allowed": boundary.get("chart_fact_mutation_allowed"),
            },
        ),
    ]
    failed = [row for row in checks if row["passed"] is not True]
    ready = not failed
    return {
        "version": DIALOGUE_SYNTHETIC_REPLAY_QUEUE_VALIDATION_VERSION,
        "status": "completed" if ready else "blocked",
        "queue_result": queue,
        "checks": checks,
        "decision": {
            "dialogue_synthetic_replay_queue_ready": ready,
            "decision_status": "dtc4_dialogue_synthetic_replay_queue_ready"
            if ready else "dtc4_dialogue_synthetic_replay_queue_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "candidate_ready_for_operator_review": bool(decision.get("candidate_ready_for_operator_review")),
            "promotion_allowed": False,
            "policy_pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": queue.get("next_mainline_selection", {}),
        "policy_boundary": boundary,
        "boundary": "dialogue_synthetic_replay_queue_validation_is_read_only_and_blocks_policy_release",
    }


def _check(check_id: str, passed: bool, observed: Mapping[str, object]) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "observed": dict(observed)}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
