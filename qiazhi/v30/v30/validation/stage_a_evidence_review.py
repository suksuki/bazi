from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.stage_a_release_gate_execution import (
    STAGE_A_RELEASE_GATE_EXECUTION_VERSION,
    run_stage_a_release_gate_execution,
)


STAGE_A_EVIDENCE_REVIEW_VERSION = "v30.stage_a_evidence_review.v1"
REQUIRED_STAGE_A_GATES = ("controlled_release_readiness", "synthetic_all", "518k_sample", "518k_shard")


def run_stage_a_evidence_review(
    *,
    sample_limit: int = 8,
    shard_id: int = 7,
    shard_limit: int = 16,
    reading_id: str = "rel-s4-stage-a-evidence-review",
) -> dict[str, Any]:
    stage_a = run_stage_a_release_gate_execution(
        sample_limit=sample_limit,
        shard_id=shard_id,
        shard_limit=shard_limit,
        reading_id=reading_id,
    )
    return build_stage_a_evidence_review(stage_a_execution=stage_a)


def build_stage_a_evidence_review(*, stage_a_execution: Mapping[str, Any]) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    stage_a = _stage_a_summary(stage_a_execution)
    gate_rows = [_gate_row(row) for row in _list(stage_a_execution.get("gate_summaries"))]
    decision = _decision(stage_a=stage_a, gate_rows=gate_rows)
    return {
        "version": STAGE_A_EVIDENCE_REVIEW_VERSION,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["stage_a_evidence_review_complete"] else "blocked",
        "task": {
            "task_id": "REL-S4",
            "title": "Stage-A Evidence Review And External-Release Hold",
            "scope": "review_stage_a_evidence_keep_external_release_on_hold_and_return_to_core_mainline",
        },
        "stage_a_execution_summary": stage_a,
        "gate_evidence": gate_rows,
        "decision": decision,
        "external_release_hold": {
            "external_release_ready": False,
            "external_release_allowed": False,
            "reason": "stage_a_passes_controlled_trial_readiness_only_not_external_release",
            "additional_authorization_required_for_external_release": True,
            "required_before_external_release": [
                "explicit_operator_approval",
                "full_pytest_if_operator_authorizes",
                "real_env_smoke_if_deployment_changes_or_operator_authorizes",
                "live_llm_smoke_if_live_llm_is_enabled_for_release",
                "separate_policy_pointer_promotion_decision",
            ],
        },
        "policy_boundary": {
            "full_pytest_run": False,
            "live_llm_smoke_run": False,
            "real_env_smoke_run": False,
            "full_518k_run": False,
            "external_release_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "rel_s4_reviews_stage_a_evidence_and_holds_external_release",
    }


def _stage_a_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    policy = _mapping(payload.get("policy_boundary"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "stage_a_release_gates_passed": bool(decision.get("stage_a_release_gates_passed")),
        "gate_count": int(decision.get("gate_count", 0) or 0),
        "executed_gate_count": int(decision.get("executed_gate_count", 0) or 0),
        "passed_gate_count": int(decision.get("passed_gate_count", 0) or 0),
        "failed_gate_ids": list(decision.get("failed_gate_ids") or []),
        "missing_gate_ids": list(decision.get("missing_gate_ids") or []),
        "external_release_allowed": bool(decision.get("external_release_allowed")),
        "full_pytest_run": bool(policy.get("full_pytest_run")),
        "live_llm_smoke_run": bool(policy.get("live_llm_smoke_run")),
        "real_env_smoke_run": bool(policy.get("real_env_smoke_run")),
        "full_518k_run": bool(policy.get("full_518k_run")),
        "policy_pointer_promotion_allowed": bool(policy.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(policy.get("chart_fact_mutation_allowed")),
    }


def _gate_row(row: object) -> dict[str, Any]:
    gate = _mapping(row)
    summary = _mapping(gate.get("summary"))
    return {
        "gate_id": str(gate.get("gate_id") or ""),
        "executed": bool(gate.get("executed")),
        "passed": bool(gate.get("passed")),
        "status": str(gate.get("status") or ""),
        "case_count": int(summary.get("case_count", 0) or 0),
        "passed_count": int(summary.get("passed_count", 0) or 0),
        "run_id": str(summary.get("run_id") or ""),
        "artifact_uri": str(summary.get("artifact_uri") or ""),
        "index_uri": str(summary.get("index_uri") or ""),
        "artifact_record_id": str(summary.get("artifact_record_id") or ""),
        "artifact_search_backend": str(summary.get("artifact_search_backend") or ""),
    }


def _decision(*, stage_a: Mapping[str, Any], gate_rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    gate_ids = [str(row.get("gate_id") or "") for row in gate_rows]
    missing_required = [gate_id for gate_id in REQUIRED_STAGE_A_GATES if gate_id not in gate_ids]
    failed = [str(row.get("gate_id") or "") for row in gate_rows if row.get("passed") is not True]
    blockers: list[str] = []
    if stage_a["version"] != STAGE_A_RELEASE_GATE_EXECUTION_VERSION:
        blockers.append("stage_a_execution_missing")
    if not stage_a["stage_a_release_gates_passed"]:
        blockers.append("stage_a_execution_not_passed")
    if stage_a["gate_count"] != len(REQUIRED_STAGE_A_GATES) or stage_a["passed_gate_count"] != len(REQUIRED_STAGE_A_GATES):
        blockers.append("stage_a_gate_count_mismatch")
    if missing_required:
        blockers.append("required_stage_a_gate_missing")
    if failed:
        blockers.append("stage_a_gate_failed")
    if stage_a["external_release_allowed"]:
        blockers.append("unexpected_external_release_permission")
    if stage_a["full_pytest_run"] or stage_a["live_llm_smoke_run"] or stage_a["real_env_smoke_run"] or stage_a["full_518k_run"]:
        blockers.append("unexpected_heavy_or_live_gate_execution")
    if stage_a["policy_pointer_promotion_allowed"] or stage_a["chart_fact_mutation_allowed"]:
        blockers.append("unexpected_policy_or_chart_mutation_permission")

    complete = not blockers
    return {
        "stage_a_evidence_review_complete": complete,
        "decision_status": "rel_s4_stage_a_evidence_review_complete_external_release_held"
        if complete
        else "rel_s4_stage_a_evidence_review_blocked",
        "reviewed_gate_ids": gate_ids,
        "missing_required_gate_ids": missing_required,
        "failed_gate_ids": failed,
        "blockers": blockers,
        "controlled_trial_readiness_confirmed": complete,
        "external_release_ready": False,
        "external_release_allowed": False,
        "return_to_core_module_mainline": complete,
        "additional_heavy_live_gate_authorization_recommended": False,
        "full_pytest_authorized": False,
        "live_llm_smoke_authorized": False,
        "real_env_smoke_authorized": False,
        "full_518k_authorized": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["stage_a_evidence_review_complete"]:
        return {
            "task_id": "MCR3",
            "title": "Return To Core Module Mainline Selection",
            "selected_track": "core_module_mainline",
            "scope": [
                "resume targeted core-module work instead of release expansion",
                "keep external release on hold",
                "authorize full/live gates only through a later explicit release task",
            ],
        }
    return {
        "task_id": "REL-S4-FR",
        "title": "Stage-A Evidence Review Failure Repair",
        "selected_track": "controlled_release_boundary",
        "scope": [
            "inspect missing or failed Stage-A evidence",
            "rerun only blocked Stage-A gates",
            "keep external release and pointer promotion disabled",
        ],
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
