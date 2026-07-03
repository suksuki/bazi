from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from v30.config import V30Settings
from v30.training.dialogue_strategy_validation_gate import (
    DIALOGUE_STRATEGY_VALIDATION_GATE_VERSION,
    build_dialogue_strategy_validation_gate,
    run_dialogue_strategy_validation_gate,
)


DIALOGUE_STRATEGY_VALIDATION_GATE_VALIDATION_VERSION = "v30.dialogue_strategy_validation_gate_validation.v1"


def run_dialogue_strategy_validation_gate_validation(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dtc3-dialogue-strategy-validation-gate",
    persist_review: bool = True,
    settings: V30Settings | None = None,
) -> dict[str, object]:
    gate = run_dialogue_strategy_validation_gate(
        runtime_payloads=runtime_payloads,
        sample_limit=sample_limit,
        run_id=run_id,
        persist_review=persist_review,
        settings=settings,
    )
    return build_dialogue_strategy_validation_gate_validation(gate_result=gate)


def build_dialogue_strategy_validation_gate_validation(
    *,
    gate_result: Mapping[str, Any],
) -> dict[str, object]:
    gate = dict(gate_result)
    decision = _mapping(gate.get("decision"))
    boundary = _mapping(gate.get("policy_boundary"))
    replay = _mapping(gate.get("replay_evaluation"))
    checks = [
        _check(
            "gate_completed",
            gate.get("version") == DIALOGUE_STRATEGY_VALIDATION_GATE_VERSION
            and gate.get("status") == "completed",
            {"gate_version": gate.get("version"), "gate_status": gate.get("status")},
        ),
        _check(
            "candidate_routes_to_synthetic_replay",
            decision.get("candidate_deserves_synthetic_replay") is True
            and replay.get("synthetic_replay_recommended") is True,
            {
                "candidate_deserves_synthetic_replay": decision.get("candidate_deserves_synthetic_replay"),
                "synthetic_replay_recommended": replay.get("synthetic_replay_recommended"),
                "evaluation_label": replay.get("evaluation_label"),
            },
        ),
        _check(
            "promotion_still_blocked",
            decision.get("promotion_allowed") is False
            and decision.get("policy_pointer_write_allowed") is False
            and boundary.get("policy_pointer_promotion_allowed") is False,
            {
                "promotion_allowed": decision.get("promotion_allowed"),
                "policy_pointer_write_allowed": decision.get("policy_pointer_write_allowed"),
                "policy_pointer_promotion_allowed": boundary.get("policy_pointer_promotion_allowed"),
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
        "version": DIALOGUE_STRATEGY_VALIDATION_GATE_VALIDATION_VERSION,
        "status": "completed" if ready else "blocked",
        "gate_result": gate,
        "checks": checks,
        "decision": {
            "dialogue_strategy_validation_gate_ready": ready,
            "decision_status": "dtc3_dialogue_strategy_validation_gate_ready"
            if ready else "dtc3_dialogue_strategy_validation_gate_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "candidate_deserves_synthetic_replay": bool(decision.get("candidate_deserves_synthetic_replay")),
            "promotion_allowed": False,
            "policy_pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": gate.get("next_mainline_selection", {}),
        "policy_boundary": boundary,
        "boundary": "dialogue_strategy_validation_gate_validation_is_read_only_and_blocks_policy_release",
    }


def _check(check_id: str, passed: bool, observed: Mapping[str, object]) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "observed": dict(observed)}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
