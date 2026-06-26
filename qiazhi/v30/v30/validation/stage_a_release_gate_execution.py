from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.controlled_release_readiness import run_controlled_release_readiness
from v30.validation.corpus_518k import run_518k_validation
from v30.validation.explicit_release_gate_authorization import (
    EXPLICIT_RELEASE_GATE_AUTHORIZATION_VERSION,
    run_explicit_release_gate_authorization,
)
from v30.validation.synthetic_case import run_synthetic_tier


STAGE_A_RELEASE_GATE_EXECUTION_VERSION = "v30.stage_a_release_gate_execution.v1"
STAGE_A_GATE_IDS = ("controlled_release_readiness", "synthetic_all", "518k_sample", "518k_shard")


def run_stage_a_release_gate_execution(
    *,
    sample_limit: int = 8,
    shard_id: int = 7,
    shard_limit: int = 16,
    reading_id: str = "rel-s3-stage-a-release-gates",
) -> dict[str, Any]:
    authorization = run_explicit_release_gate_authorization(
        authorization_decision="authorize_stage_a",
        reading_id=reading_id,
    )
    authorization_summary = _authorization_summary(authorization)
    if not _stage_a_authorized(authorization_summary):
        return build_stage_a_release_gate_execution(
            authorization=authorization,
            gate_results={},
            sample_limit=sample_limit,
            shard_id=shard_id,
            shard_limit=shard_limit,
        )

    controlled = run_controlled_release_readiness(reading_id=reading_id)
    synthetic_all = run_synthetic_tier("all")
    sample = run_518k_validation(mode="sample", limit=sample_limit)
    shard = run_518k_validation(mode="shard", shard_id=shard_id, limit=shard_limit)
    return build_stage_a_release_gate_execution(
        authorization=authorization,
        gate_results={
            "controlled_release_readiness": controlled,
            "synthetic_all": synthetic_all,
            "518k_sample": sample,
            "518k_shard": shard,
        },
        sample_limit=sample_limit,
        shard_id=shard_id,
        shard_limit=shard_limit,
    )


def build_stage_a_release_gate_execution(
    *,
    authorization: Mapping[str, Any],
    gate_results: Mapping[str, Any],
    sample_limit: int = 8,
    shard_id: int = 7,
    shard_limit: int = 16,
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    authorization_summary = _authorization_summary(authorization)
    gate_summaries = [
        _gate_summary("controlled_release_readiness", gate_results.get("controlled_release_readiness")),
        _gate_summary("synthetic_all", gate_results.get("synthetic_all")),
        _gate_summary("518k_sample", gate_results.get("518k_sample")),
        _gate_summary("518k_shard", gate_results.get("518k_shard")),
    ]
    decision = _decision(authorization_summary=authorization_summary, gate_summaries=gate_summaries)
    return {
        "version": STAGE_A_RELEASE_GATE_EXECUTION_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["stage_a_release_gates_passed"] else "blocked",
        "task": {
            "task_id": "REL-S3",
            "title": "Execute Stage-A Authorized Release Gates",
            "scope": "execute_only_rel_s2_authorized_non_live_stage_a_gates_and_record_evidence",
        },
        "input": {
            "sample_limit": sample_limit,
            "shard_id": shard_id,
            "shard_limit": shard_limit,
            "authorized_gate_ids": authorization_summary["authorized_gate_ids"],
        },
        "authorization_summary": authorization_summary,
        "gate_summaries": gate_summaries,
        "decision": decision,
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
        "boundary": "rel_s3_executes_stage_a_only_without_live_full_or_release_actions",
    }


def _authorization_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "authorization_recorded": bool(decision.get("authorization_recorded")),
        "authorized_gate_ids": list(decision.get("authorized_gate_ids") or []),
        "deferred_gate_ids": list(decision.get("deferred_gate_ids") or []),
        "runs_triggered_by_authorization": bool(decision.get("runs_triggered")),
        "external_release_allowed": bool(decision.get("external_release_allowed")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _stage_a_authorized(summary: Mapping[str, Any]) -> bool:
    return (
        summary["version"] == EXPLICIT_RELEASE_GATE_AUTHORIZATION_VERSION
        and summary["authorization_recorded"]
        and set(summary["authorized_gate_ids"]) == set(STAGE_A_GATE_IDS)
        and not summary["runs_triggered_by_authorization"]
        and not summary["external_release_allowed"]
        and not summary["policy_pointer_promotion_allowed"]
        and not summary["chart_fact_mutation_allowed"]
    )


def _gate_summary(gate_id: str, result: object) -> dict[str, Any]:
    if result is None:
        return {
            "gate_id": gate_id,
            "executed": False,
            "passed": False,
            "status": "missing",
            "summary": {},
        }
    if gate_id == "controlled_release_readiness" and isinstance(result, Mapping):
        decision = _mapping(result.get("decision"))
        return {
            "gate_id": gate_id,
            "executed": True,
            "passed": bool(decision.get("controlled_release_readiness_ready")),
            "status": str(result.get("status") or ""),
            "summary": {
                "decision_status": str(decision.get("decision_status") or ""),
                "check_count": int(decision.get("check_count", 0) or 0),
                "passed_check_count": int(decision.get("passed_check_count", 0) or 0),
                "controlled_trial_ready": bool(decision.get("controlled_trial_ready")),
                "external_release_ready": bool(decision.get("external_release_ready")),
            },
        }
    if gate_id == "synthetic_all":
        return {
            "gate_id": gate_id,
            "executed": True,
            "passed": bool(getattr(result, "passed", False)),
            "status": "passed" if getattr(result, "passed", False) else "failed",
            "summary": {
                "suite_id": str(getattr(result, "suite_id", "")),
                "case_count": int(getattr(result, "case_count", 0) or 0),
                "passed_count": int(getattr(result, "passed_count", 0) or 0),
            },
        }
    if gate_id in {"518k_sample", "518k_shard"}:
        return {
            "gate_id": gate_id,
            "executed": True,
            "passed": getattr(result, "promotion_signal", "") == "eligible",
            "status": str(getattr(result, "promotion_signal", "")),
            "summary": {
                "run_id": str(getattr(result, "run_id", "")),
                "mode": str(getattr(result, "mode", "")),
                "case_count": int(getattr(result, "case_count", 0) or 0),
                "shard_ids": list(getattr(result, "shard_ids", []) or []),
                "artifact_uri": str(getattr(result, "artifact_uri", "") or ""),
                "index_uri": str(getattr(result, "index_uri", "") or ""),
                "artifact_record_id": str(getattr(result, "artifact_record_id", "") or ""),
                "artifact_search_backend": str(getattr(result, "artifact_search_backend", "") or ""),
            },
        }
    return {
        "gate_id": gate_id,
        "executed": True,
        "passed": False,
        "status": "unknown_result_type",
        "summary": {},
    }


def _decision(
    *,
    authorization_summary: Mapping[str, Any],
    gate_summaries: list[Mapping[str, Any]],
) -> dict[str, Any]:
    failed = [str(row["gate_id"]) for row in gate_summaries if not row.get("passed")]
    missing = [str(row["gate_id"]) for row in gate_summaries if not row.get("executed")]
    blockers: list[str] = []
    if not _stage_a_authorized(authorization_summary):
        blockers.append("rel_s2_stage_a_authorization_missing")
    if missing:
        blockers.append("stage_a_gate_execution_missing")
    if failed:
        blockers.append("stage_a_gate_failed")
    passed = not blockers
    return {
        "stage_a_release_gates_passed": passed,
        "decision_status": "rel_s3_stage_a_gates_passed" if passed else "rel_s3_stage_a_gates_blocked",
        "gate_count": len(gate_summaries),
        "executed_gate_count": sum(1 for row in gate_summaries if row.get("executed")),
        "passed_gate_count": sum(1 for row in gate_summaries if row.get("passed")),
        "failed_gate_ids": failed,
        "missing_gate_ids": missing,
        "blockers": blockers,
        "external_release_ready": False,
        "external_release_allowed": False,
        "full_pytest_run": False,
        "live_llm_smoke_run": False,
        "real_env_smoke_run": False,
        "full_518k_run": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["stage_a_release_gates_passed"]:
        return {
            "task_id": "REL-S4",
            "title": "Stage-A Evidence Review And External-Release Hold",
            "selected_track": "controlled_release_boundary",
            "scope": [
                "review Stage-A pass evidence",
                "keep external release on hold",
                "decide whether to return to core module work or authorize additional heavy/live gates",
            ],
        }
    return {
        "task_id": "REL-S3-FR",
        "title": "Stage-A Gate Failure Review",
        "selected_track": "controlled_release_boundary",
        "scope": [
            "inspect failed Stage-A gate summaries",
            "repair only the failed gate surface",
            "do not run full pytest, live LLM, real-env smoke, full 518K, or pointer promotion while blocked",
        ],
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
