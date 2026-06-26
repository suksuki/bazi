from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.policy.runtime_pointer import PolicyFamily
from v30.validation.corpus_518k import Corpus518KValidationResult, run_518k_validation
from v30.validation.synthetic_case import SyntheticValidationSuiteResult, run_synthetic_tier
from v30.validation.targeted_calibration_candidate_review import (
    DEFAULT_TARGETED_CALIBRATION_FAMILIES,
    build_targeted_calibration_candidate_review,
    run_targeted_calibration_candidate_review,
)


TARGETED_CALIBRATION_VALIDATION_GATE_VERSION = "v30.targeted_calibration_validation_gate.v1"


def run_targeted_calibration_validation_gate(
    *,
    families: Sequence[PolicyFamily] = DEFAULT_TARGETED_CALIBRATION_FAMILIES,
    sample_limit: int = 8,
    gate_id: str | None = None,
) -> dict[str, Any]:
    candidate_review = run_targeted_calibration_candidate_review(families=families, review_id=gate_id)
    policy_payload_overrides = _policy_payload_overrides(candidate_review)
    active_policy_version_overrides = {
        family: f"{family}.{gate_id or candidate_review.get('review_id', 'targeted_calibration_gate')}.{family}"
        for family in policy_payload_overrides
    }
    synthetic_all = run_synthetic_tier(
        "all",
        suite_id=f"{gate_id or candidate_review.get('review_id', 'targeted_calibration_gate')}.synthetic_all",
        policy_payload_overrides=policy_payload_overrides,
        active_policy_version_overrides=active_policy_version_overrides,
    )
    sample = run_518k_validation(
        mode="sample",
        limit=sample_limit,
        policy_payload_overrides=policy_payload_overrides,
        active_policy_version_overrides=active_policy_version_overrides,
    )
    return build_targeted_calibration_validation_gate(
        candidate_review=candidate_review,
        synthetic_all=synthetic_all,
        corpus_sample=sample,
        gate_id=gate_id,
    )


def build_targeted_calibration_validation_gate(
    *,
    candidate_review: Mapping[str, Any],
    synthetic_all: SyntheticValidationSuiteResult | Mapping[str, Any],
    corpus_sample: Corpus518KValidationResult | Mapping[str, Any],
    gate_id: str | None = None,
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    synthetic_summary = _synthetic_summary(synthetic_all)
    sample_summary = _sample_summary(corpus_sample)
    decision = _decision(
        candidate_review=candidate_review,
        synthetic_summary=synthetic_summary,
        sample_summary=sample_summary,
    )
    return {
        "version": TARGETED_CALIBRATION_VALIDATION_GATE_VERSION,
        "gate_id": gate_id or f"v30.targeted_calibration.validation_gate.{reviewed_at.strftime('%Y%m%d%H%M%S')}",
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed",
        "decision": decision,
        "candidate_review_summary": _candidate_review_summary(candidate_review),
        "synthetic_all_summary": synthetic_summary,
        "corpus_518k_sample_summary": sample_summary,
        "policy_boundary": {
            "policy_pointer_review_allowed": decision["validation_gate_ready"],
            "policy_pointer_promotion_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "f3_validation_gate_is_evidence_only_not_pointer_promotion",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "targeted_calibration_validation_gate_validates_candidates_without_mutating_policy_or_chart_facts",
    }


def _policy_payload_overrides(candidate_review: Mapping[str, Any]) -> dict[str, dict[str, object]]:
    candidates = candidate_review.get("candidates", [])
    if not isinstance(candidates, list):
        return {}
    supported = {"structure_policy", "rule_policy", "question_policy"}
    overrides: dict[str, dict[str, object]] = {}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        family = str(candidate.get("family") or "")
        payload = candidate.get("policy_payload", {})
        if family in supported and isinstance(payload, dict):
            overrides[family] = payload
    return overrides


def _synthetic_summary(result: SyntheticValidationSuiteResult | Mapping[str, Any]) -> dict[str, Any]:
    payload = result.model_dump(mode="json") if isinstance(result, SyntheticValidationSuiteResult) else dict(result)
    return {
        "suite_id": str(payload.get("suite_id") or ""),
        "passed": bool(payload.get("passed")),
        "case_count": int(payload.get("case_count", 0) or 0),
        "passed_count": int(payload.get("passed_count", 0) or 0),
        "failed_count": int(payload.get("failed_count", 0) or 0),
    }


def _sample_summary(result: Corpus518KValidationResult | Mapping[str, Any]) -> dict[str, Any]:
    payload = result.model_dump(mode="json") if isinstance(result, Corpus518KValidationResult) else dict(result)
    return {
        "run_id": str(payload.get("run_id") or ""),
        "mode": str(payload.get("mode") or ""),
        "case_count": int(payload.get("case_count", 0) or 0),
        "promotion_signal": str(payload.get("promotion_signal") or ""),
        "failure_cluster_count": len(payload.get("failure_clusters", []) or []),
        "artifact_record_id": str(payload.get("artifact_record_id") or ""),
        "artifact_search_backend": str(payload.get("artifact_search_backend") or ""),
    }


def _candidate_review_summary(review: Mapping[str, Any]) -> dict[str, Any]:
    decision = review.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    candidate_summary = review.get("candidate_summary", {})
    candidate_summary = candidate_summary if isinstance(candidate_summary, dict) else {}
    return {
        "version": str(review.get("version") or ""),
        "review_id": str(review.get("review_id") or ""),
        "targeted_calibration_review_ready": bool(decision.get("targeted_calibration_review_ready")),
        "candidate_count": int(candidate_summary.get("candidate_count", 0) or 0),
        "families": candidate_summary.get("families", []) if isinstance(candidate_summary.get("families", []), list) else [],
    }


def _decision(
    *,
    candidate_review: Mapping[str, Any],
    synthetic_summary: Mapping[str, Any],
    sample_summary: Mapping[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    candidate_decision = candidate_review.get("decision", {})
    candidate_decision = candidate_decision if isinstance(candidate_decision, dict) else {}
    if not candidate_decision.get("targeted_calibration_review_ready"):
        blockers.append("f2_candidate_review_not_ready")
    if not synthetic_summary.get("passed"):
        blockers.append("synthetic_all_failed")
    if int(synthetic_summary.get("case_count", 0) or 0) < 90:
        blockers.append("synthetic_all_case_count_low")
    if sample_summary.get("promotion_signal") != "eligible":
        blockers.append("518k_sample_not_eligible")
    if int(sample_summary.get("case_count", 0) or 0) < 8:
        blockers.append("518k_sample_case_count_low")
    ready = not blockers
    return {
        "validation_gate_ready": ready,
        "policy_pointer_review_allowed": ready,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "decision_status": "ready_for_policy_pointer_review" if ready else "targeted_validation_gate_blocked",
        "blockers": blockers,
        "rationale": (
            "F2 candidates passed synthetic all and 518K sample evidence; a separate pointer review may inspect them, but this gate still does not promote policy."
            if ready
            else "Targeted calibration validation gate needs the listed blockers closed before any pointer review."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["validation_gate_ready"]:
        return {
            "task_id": "F4",
            "title": "Targeted Calibration Pointer Review",
            "selected_track": "targeted_calibration",
            "scope": [
                "inspect F2/F3 evidence before any pointer decision",
                "keep automatic promotion disabled unless explicitly requested",
                "keep deterministic chart facts and frozen M1-M8 completion sealed",
            ],
        }
    return {
        "task_id": "F3",
        "title": "Targeted Calibration Validation Gap Closure",
        "selected_track": "targeted_calibration",
        "scope": [
            "close synthetic all or 518K sample blockers",
            "rerun F2 candidate review if candidates are stale",
            "do not promote policy pointers while blocked",
        ],
    }
