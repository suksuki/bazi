from __future__ import annotations

from typing import Any

from v30.brain.contracts import BrainTrainingExample
from v30.validation.central_reading_synthetic_validation import run_central_reading_synthetic_validation

CENTRAL_BRAIN_PHASE2_REPLAY_GATE_VERSION = "v30.central_brain_phase2_replay_gate.v1"


def build_central_brain_phase2_replay_gate(
    *,
    candidate_policy: dict[str, Any],
    replay_examples: list[BrainTrainingExample],
    validation_result: dict[str, Any] | None = None,
    min_replay_examples: int = 1,
) -> dict[str, Any]:
    validation = validation_result or run_central_reading_synthetic_validation("phase2-replay-gate")
    replay_metrics = _replay_metrics(replay_examples)
    checks = [
        _check(
            "candidate_policy_eligible",
            candidate_policy.get("promotion_signal") == "eligible",
            {"promotion_signal": candidate_policy.get("promotion_signal"), "status": candidate_policy.get("status")},
        ),
        _check(
            "central_reading_synthetic_completed",
            validation.get("status") == "completed"
            and _nested(validation, "decision", "central_reading_synthetic_ready") is True,
            {
                "status": validation.get("status"),
                "failed_check_ids": _nested(validation, "decision", "failed_check_ids"),
            },
        ),
        _check(
            "replay_example_count",
            replay_metrics["example_count"] >= min_replay_examples,
            {"example_count": replay_metrics["example_count"], "min_replay_examples": min_replay_examples},
        ),
        _check(
            "replay_claim_quality",
            replay_metrics["example_count"] == 0 or replay_metrics["average_claim_correctness"] >= 0.45,
            {"average_claim_correctness": replay_metrics["average_claim_correctness"]},
        ),
        _check(
            "replay_template_risk",
            replay_metrics["average_template_risk"] <= 0.45,
            {"average_template_risk": replay_metrics["average_template_risk"]},
        ),
        _check(
            "replay_overclaim_risk",
            replay_metrics["average_overclaim_risk"] <= 0.45,
            {"average_overclaim_risk": replay_metrics["average_overclaim_risk"]},
        ),
        _check(
            "chart_fact_immutability",
            candidate_policy.get("chart_fact_mutation_allowed") is False
            and _nested(validation, "decision", "chart_fact_mutation_allowed") is False
            and all(example.safety.chart_fact_mutation_allowed is False for example in replay_examples),
            {
                "candidate_chart_fact_mutation_allowed": candidate_policy.get("chart_fact_mutation_allowed"),
                "validation_chart_fact_mutation_allowed": _nested(validation, "decision", "chart_fact_mutation_allowed"),
            },
        ),
    ]
    failed = [row for row in checks if row["passed"] is False]
    eligible = not failed
    return {
        "version": CENTRAL_BRAIN_PHASE2_REPLAY_GATE_VERSION,
        "status": "passed" if eligible else "blocked",
        "promotion_signal": "eligible" if eligible else "blocked",
        "decision": {
            "phase2_replay_gate_ready": eligible,
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
        },
        "checks": checks,
        "candidate_policy": {
            "version": candidate_policy.get("version"),
            "promotion_signal": candidate_policy.get("promotion_signal"),
            "example_count": candidate_policy.get("example_count"),
            "weight_deltas": candidate_policy.get("weight_deltas", {}),
            "blocked_reasons": candidate_policy.get("blocked_reasons", []),
        },
        "replay_metrics": replay_metrics,
        "synthetic_validation": {
            "version": validation.get("version"),
            "status": validation.get("status"),
            "decision": validation.get("decision", {}),
        },
        "chart_fact_mutation_allowed": False,
        "boundary": "central_brain_phase2_replay_gate_validates_policy_candidate_without_mutating_chart_facts",
    }


def run_central_brain_phase2_replay_gate(
    *,
    candidate_policy: dict[str, Any],
    replay_examples: list[BrainTrainingExample],
    min_replay_examples: int = 1,
) -> dict[str, Any]:
    return build_central_brain_phase2_replay_gate(
        candidate_policy=candidate_policy,
        replay_examples=replay_examples,
        min_replay_examples=min_replay_examples,
    )


def _replay_metrics(examples: list[BrainTrainingExample]) -> dict[str, Any]:
    count = max(1, len(examples))
    return {
        "example_count": len(examples),
        "answered_count": sum(1 for example in examples if example.outcome.user_answered),
        "useful_followup_count": sum(1 for example in examples if example.outcome.followup_useful is True),
        "average_claim_correctness": round(sum(example.structured_labels.claim_correctness for example in examples) / count, 3) if examples else 0.0,
        "average_template_risk": round(sum(example.structured_labels.template_risk for example in examples) / count, 3) if examples else 0.0,
        "average_overclaim_risk": round(sum(example.structured_labels.overclaim_risk for example in examples) / count, 3) if examples else 0.0,
        "average_user_cost": round(sum(example.structured_labels.user_cost for example in examples) / count, 3) if examples else 0.0,
    }


def _check(check_id: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"check_id": check_id, "passed": bool(passed), "details": details}


def _nested(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
