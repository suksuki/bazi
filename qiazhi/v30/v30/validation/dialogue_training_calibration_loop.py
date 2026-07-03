from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from v30.training import (
    DIALOGUE_TRAINING_CALIBRATION_LOOP_VERSION,
    build_dialogue_training_calibration_loop,
    run_dialogue_training_calibration_loop,
)


DIALOGUE_TRAINING_CALIBRATION_VALIDATION_VERSION = "v30.dialogue_training_calibration_validation.v1"


def run_dialogue_training_calibration_validation(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dtc1-dialogue-training-calibration",
) -> dict[str, object]:
    loop = run_dialogue_training_calibration_loop(
        runtime_payloads=runtime_payloads,
        sample_limit=sample_limit,
        run_id=run_id,
    )
    return build_dialogue_training_calibration_validation(loop_result=loop)


def build_dialogue_training_calibration_validation(
    *,
    loop_result: Mapping[str, Any],
) -> dict[str, object]:
    loop = dict(loop_result)
    decision = _mapping(loop.get("decision"))
    boundary = _mapping(loop.get("policy_boundary"))
    checks = [
        _check(
            "loop_completed",
            loop.get("version") == DIALOGUE_TRAINING_CALIBRATION_LOOP_VERSION
            and loop.get("status") == "completed",
            {"loop_version": loop.get("version"), "loop_status": loop.get("status")},
        ),
        _check(
            "samples_and_candidates_ready",
            int(decision.get("sample_count") or 0) >= 1
            and int(decision.get("policy_candidate_count") or 0) >= 1,
            {
                "sample_count": decision.get("sample_count"),
                "policy_candidate_count": decision.get("policy_candidate_count"),
            },
        ),
        _check(
            "quality_is_measured",
            float(_mapping(loop.get("quality_summary")).get("average_answer_quality") or 0.0) > 0.0,
            {"quality_summary": loop.get("quality_summary")},
        ),
        _check(
            "policy_boundary_is_safe",
            boundary.get("chart_fact_mutation_allowed") is False
            and boundary.get("policy_pointer_promotion_allowed") is False
            and boundary.get("auto_apply_training_allowed") is False,
            {
                "chart_fact_mutation_allowed": boundary.get("chart_fact_mutation_allowed"),
                "policy_pointer_promotion_allowed": boundary.get("policy_pointer_promotion_allowed"),
                "auto_apply_training_allowed": boundary.get("auto_apply_training_allowed"),
            },
        ),
        _check(
            "loop_checks_passed",
            int(decision.get("passed_check_count") or 0) == int(decision.get("check_count") or -1),
            {
                "passed_check_count": decision.get("passed_check_count"),
                "check_count": decision.get("check_count"),
                "failed_check_ids": decision.get("failed_check_ids", []),
            },
        ),
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": DIALOGUE_TRAINING_CALIBRATION_VALIDATION_VERSION,
        "status": "completed" if ready else "blocked",
        "loop_result": loop,
        "checks": checks,
        "decision": {
            "dialogue_training_calibration_ready": ready,
            "decision_status": "dtc1_dialogue_training_calibration_ready"
            if ready else "dtc1_dialogue_training_calibration_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": loop.get("next_mainline_selection", {}),
        "boundary": "dialogue_training_calibration_validation_is_read_only_and_does_not_promote_policy",
    }


def _check(check_id: str, passed: bool, observed: Mapping[str, object]) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "observed": dict(observed)}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
