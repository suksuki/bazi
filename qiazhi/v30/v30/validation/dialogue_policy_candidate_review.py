from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from v30.config import V30Settings
from v30.training.dialogue_policy_candidate_review import (
    DIALOGUE_POLICY_CANDIDATE_REVIEW_VERSION,
    build_dialogue_policy_candidate_review,
    run_dialogue_policy_candidate_review,
)


DIALOGUE_POLICY_CANDIDATE_REVIEW_VALIDATION_VERSION = "v30.dialogue_policy_candidate_review_validation.v1"


def run_dialogue_policy_candidate_review_validation(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dtc2-dialogue-policy-candidate-review",
    persist: bool = True,
    settings: V30Settings | None = None,
) -> dict[str, object]:
    review = run_dialogue_policy_candidate_review(
        runtime_payloads=runtime_payloads,
        sample_limit=sample_limit,
        run_id=run_id,
        persist=persist,
        settings=settings,
    )
    return build_dialogue_policy_candidate_review_validation(review_result=review)


def build_dialogue_policy_candidate_review_validation(
    *,
    review_result: Mapping[str, Any],
) -> dict[str, object]:
    review = dict(review_result)
    decision = _mapping(review.get("decision"))
    boundary = _mapping(review.get("policy_boundary"))
    comparison = _mapping(review.get("question_policy_comparison"))
    checks = [
        _check(
            "review_completed",
            review.get("version") == DIALOGUE_POLICY_CANDIDATE_REVIEW_VERSION
            and review.get("status") == "completed",
            {"review_version": review.get("version"), "review_status": review.get("status")},
        ),
        _check(
            "compiled_candidate_ready",
            decision.get("compiled_candidate_ready") is True
            and _mapping(review.get("candidate_payload")).get("requires_operator_review") is True,
            {
                "compiled_candidate_ready": decision.get("compiled_candidate_ready"),
                "requires_operator_review": _mapping(review.get("candidate_payload")).get("requires_operator_review"),
            },
        ),
        _check(
            "comparison_artifact_ready",
            decision.get("comparison_artifact_ready") is True
            and comparison.get("version") == "v30.question_policy_comparison.v1",
            {
                "comparison_artifact_ready": decision.get("comparison_artifact_ready"),
                "comparison_version": comparison.get("version"),
                "artifact_uri": comparison.get("artifact_uri"),
            },
        ),
        _check(
            "safe_policy_boundaries",
            boundary.get("chart_fact_mutation_allowed") is False
            and boundary.get("policy_pointer_promotion_allowed") is False
            and boundary.get("auto_apply_training_allowed") is False,
            {
                "chart_fact_mutation_allowed": boundary.get("chart_fact_mutation_allowed"),
                "policy_pointer_promotion_allowed": boundary.get("policy_pointer_promotion_allowed"),
                "auto_apply_training_allowed": boundary.get("auto_apply_training_allowed"),
            },
        ),
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": DIALOGUE_POLICY_CANDIDATE_REVIEW_VALIDATION_VERSION,
        "status": "completed" if ready else "blocked",
        "review_result": review,
        "checks": checks,
        "decision": {
            "dialogue_policy_candidate_review_ready": ready,
            "decision_status": "dtc2_dialogue_policy_candidate_review_ready"
            if ready else "dtc2_dialogue_policy_candidate_review_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "compiled_candidate_ready": bool(decision.get("compiled_candidate_ready")),
            "comparison_artifact_ready": bool(decision.get("comparison_artifact_ready")),
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": review.get("next_mainline_selection", {}),
        "policy_boundary": boundary,
        "boundary": "dialogue_policy_candidate_review_validation_is_read_only_and_does_not_promote_policy",
    }


def _check(check_id: str, passed: bool, observed: Mapping[str, object]) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "observed": dict(observed)}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
