from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.policy.runtime_pointer import PolicyFamily, RuntimePointerStore
from v30.validation.targeted_calibration_validation_gate import (
    build_targeted_calibration_validation_gate,
    run_targeted_calibration_validation_gate,
)


TARGETED_CALIBRATION_POINTER_REVIEW_VERSION = "v30.targeted_calibration_pointer_review.v1"
POINTER_REVIEW_FAMILIES: tuple[PolicyFamily, ...] = (
    "structure_policy",
    "rule_policy",
    "question_policy",
    "answer_policy",
)


def run_targeted_calibration_pointer_review(
    *,
    sample_limit: int = 8,
    review_id: str | None = None,
    store: RuntimePointerStore | None = None,
) -> dict[str, Any]:
    validation_gate = run_targeted_calibration_validation_gate(
        sample_limit=sample_limit,
        gate_id=review_id,
    )
    return build_targeted_calibration_pointer_review(
        validation_gate=validation_gate,
        store=store,
        review_id=review_id,
    )


def build_targeted_calibration_pointer_review(
    *,
    validation_gate: Mapping[str, Any],
    store: RuntimePointerStore | None = None,
    review_id: str | None = None,
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    store = store or RuntimePointerStore()
    active_versions = _active_versions(store)
    gate_summary = _validation_gate_summary(validation_gate)
    candidate_families = gate_summary["candidate_families"]
    pointer_diff = _pointer_diff(active_versions, candidate_families, review_id or str(validation_gate.get("gate_id") or ""))
    decision = _decision(gate_summary=gate_summary, pointer_diff=pointer_diff)
    return {
        "version": TARGETED_CALIBRATION_POINTER_REVIEW_VERSION,
        "review_id": review_id or f"v30.targeted_calibration.pointer_review.{reviewed_at.strftime('%Y%m%d%H%M%S')}",
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed",
        "decision": decision,
        "validation_gate_summary": gate_summary,
        "active_pointer_summary": {
            "families": sorted(active_versions),
            "active_versions": active_versions,
            "candidate_family_count": len(candidate_families),
            "candidate_families": candidate_families,
        },
        "pointer_diff_summary": pointer_diff,
        "operator_boundary": {
            "manual_pointer_decision_required": decision["manual_pointer_decision_required"],
            "automatic_pointer_write_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "f4_pointer_review_is_operator_decision_prep_not_pointer_write",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "targeted_calibration_pointer_review_inspects_evidence_without_mutating_policy_or_chart_facts",
    }


def _active_versions(store: RuntimePointerStore) -> dict[str, str]:
    versions: dict[str, str] = {}
    for family in POINTER_REVIEW_FAMILIES:
        try:
            versions[family] = store.load_pointer(family).active_artifact_id
        except Exception:
            versions[family] = ""
    return versions


def _validation_gate_summary(gate: Mapping[str, Any]) -> dict[str, Any]:
    decision = gate.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    candidate = gate.get("candidate_review_summary", {})
    candidate = candidate if isinstance(candidate, dict) else {}
    synthetic = gate.get("synthetic_all_summary", {})
    synthetic = synthetic if isinstance(synthetic, dict) else {}
    sample = gate.get("corpus_518k_sample_summary", {})
    sample = sample if isinstance(sample, dict) else {}
    families = candidate.get("families", [])
    families = [str(row) for row in families] if isinstance(families, list) else []
    return {
        "version": str(gate.get("version") or ""),
        "gate_id": str(gate.get("gate_id") or ""),
        "validation_gate_ready": bool(decision.get("validation_gate_ready")),
        "decision_status": str(decision.get("decision_status") or ""),
        "candidate_count": int(candidate.get("candidate_count", 0) or 0),
        "candidate_families": families,
        "synthetic_passed": bool(synthetic.get("passed")),
        "synthetic_case_count": int(synthetic.get("case_count", 0) or 0),
        "synthetic_passed_count": int(synthetic.get("passed_count", 0) or 0),
        "sample_promotion_signal": str(sample.get("promotion_signal") or ""),
        "sample_case_count": int(sample.get("case_count", 0) or 0),
        "sample_artifact_record_id": str(sample.get("artifact_record_id") or ""),
    }


def _pointer_diff(active_versions: Mapping[str, str], candidate_families: list[str], review_id: str) -> dict[str, Any]:
    rows = []
    for family in candidate_families:
        if family not in active_versions:
            continue
        candidate_artifact_id = f"{family}.{review_id}.{family}" if review_id else ""
        rows.append(
            {
                "family": family,
                "active_artifact_id": active_versions.get(family, ""),
                "candidate_artifact_id": candidate_artifact_id,
                "would_change_pointer": bool(candidate_artifact_id and candidate_artifact_id != active_versions.get(family, "")),
                "promotion_allowed": False,
            }
        )
    return {
        "diff_count": len(rows),
        "would_change_count": sum(1 for row in rows if row["would_change_pointer"]),
        "rows": rows,
        "boundary": "pointer_diff_is_review_only_not_pointer_mutation",
    }


def _decision(*, gate_summary: Mapping[str, Any], pointer_diff: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if not gate_summary.get("validation_gate_ready"):
        blockers.append("f3_validation_gate_not_ready")
    if int(gate_summary.get("candidate_count", 0) or 0) < 4:
        blockers.append("candidate_count_low")
    if int(gate_summary.get("synthetic_case_count", 0) or 0) < 90:
        blockers.append("synthetic_all_evidence_low")
    if int(gate_summary.get("sample_case_count", 0) or 0) < 8:
        blockers.append("518k_sample_evidence_low")
    if int(pointer_diff.get("would_change_count", 0) or 0) == 0:
        blockers.append("no_pointer_diff_to_review")
    ready = not blockers
    return {
        "pointer_review_ready": ready,
        "manual_pointer_decision_required": ready,
        "policy_pointer_promotion_allowed": False,
        "automatic_pointer_write_allowed": False,
        "chart_fact_mutation_allowed": False,
        "decision_status": "ready_for_explicit_operator_pointer_decision" if ready else "pointer_review_blocked",
        "blockers": blockers,
        "rationale": (
            "F2/F3 evidence is sufficient for an explicit operator pointer decision; this review still does not promote or write pointers."
            if ready
            else "Pointer review needs the listed blockers closed before an operator pointer decision."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["pointer_review_ready"]:
        return {
            "task_id": "F5",
            "title": "Explicit Operator Pointer Decision",
            "selected_track": "targeted_calibration",
            "scope": [
                "operator chooses whether to promote reviewed targeted-calibration pointers",
                "record rollback pointers if promotion is explicitly approved",
                "keep deterministic chart facts and frozen M1-M8 completion sealed",
            ],
        }
    return {
        "task_id": "F4",
        "title": "Targeted Calibration Pointer Review Gap Closure",
        "selected_track": "targeted_calibration",
        "scope": [
            "restore F3 validation evidence",
            "ensure candidate pointer diffs are available for review",
            "do not write policy pointers while blocked",
        ],
    }
