from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from v30.config import V30Settings
from v30.training.dialogue_operator_review_pack import (
    DIALOGUE_OPERATOR_REVIEW_PACK_VERSION,
    build_dialogue_operator_review_pack,
    run_dialogue_operator_review_pack,
)


DIALOGUE_OPERATOR_REVIEW_PACK_VALIDATION_VERSION = "v30.dialogue_operator_review_pack_validation.v1"


def run_dialogue_operator_review_pack_validation(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dtc5-dialogue-operator-review-pack",
    persist_review: bool = True,
    settings: V30Settings | None = None,
) -> dict[str, object]:
    pack = run_dialogue_operator_review_pack(
        runtime_payloads=runtime_payloads,
        sample_limit=sample_limit,
        run_id=run_id,
        persist_review=persist_review,
        settings=settings,
    )
    return build_dialogue_operator_review_pack_validation(pack_result=pack)


def build_dialogue_operator_review_pack_validation(
    *,
    pack_result: Mapping[str, Any],
) -> dict[str, object]:
    pack = dict(pack_result)
    decision = _mapping(pack.get("decision"))
    boundary = _mapping(pack.get("policy_boundary"))
    evidence = _mapping(pack.get("evidence_summary"))
    checks = [
        _check(
            "pack_completed",
            pack.get("version") == DIALOGUE_OPERATOR_REVIEW_PACK_VERSION
            and pack.get("status") == "completed",
            {"pack_version": pack.get("version"), "pack_status": pack.get("status")},
        ),
        _check(
            "operator_review_required",
            decision.get("operator_review_required") is True
            and decision.get("candidate_ready_for_heavy_validation_review") is True,
            {
                "operator_review_required": decision.get("operator_review_required"),
                "candidate_ready_for_heavy_validation_review": decision.get("candidate_ready_for_heavy_validation_review"),
            },
        ),
        _check(
            "evidence_summary_complete",
            bool(evidence.get("candidate_id"))
            and int(evidence.get("dtc4_case_count") or 0) >= 4
            and float(evidence.get("dtc4_pass_ratio") or 0.0) >= 1.0,
            {
                "candidate_id": evidence.get("candidate_id"),
                "dtc4_case_count": evidence.get("dtc4_case_count"),
                "dtc4_pass_ratio": evidence.get("dtc4_pass_ratio"),
            },
        ),
        _check(
            "release_still_blocked",
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
        "version": DIALOGUE_OPERATOR_REVIEW_PACK_VALIDATION_VERSION,
        "status": "completed" if ready else "blocked",
        "pack_result": pack,
        "checks": checks,
        "decision": {
            "dialogue_operator_review_pack_ready": ready,
            "decision_status": "dtc5_dialogue_operator_review_pack_ready"
            if ready else "dtc5_dialogue_operator_review_pack_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "operator_review_required": True,
            "candidate_ready_for_heavy_validation_review": bool(decision.get("candidate_ready_for_heavy_validation_review")),
            "promotion_allowed": False,
            "policy_pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": pack.get("next_mainline_selection", {}),
        "policy_boundary": boundary,
        "boundary": "dialogue_operator_review_pack_validation_is_read_only_and_blocks_policy_release",
    }


def _check(check_id: str, passed: bool, observed: Mapping[str, object]) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "observed": dict(observed)}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
