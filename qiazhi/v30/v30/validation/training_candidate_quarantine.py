from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from v30.config import V30Settings
from v30.policy import (
    PromotionResult,
    RuntimePointerStore,
    make_baseline_candidate,
    quarantine_failed_candidate,
)
from v30.policy.quarantine import TrainingCandidateQuarantineRecord
from v30.runtime import create_smoke_runtime
from v30.validation.training_system_closeout import run_training_system_closeout


TRAINING_CANDIDATE_QUARANTINE_VERSION = "v30.training_candidate_quarantine.v1"


def run_training_candidate_quarantine(*, training_run_id: str = "bt5-quarantine") -> dict[str, Any]:
    bt4 = run_training_system_closeout(training_run_id=f"{training_run_id}.bt4")
    with tempfile.TemporaryDirectory(prefix="v30-bt5-quarantine-") as temp_root:
        settings = V30Settings(
            database_url=None,
            redis_url=None,
            redis_prefix="v30",
            runtime_dir=Path(temp_root) / ".runtime",
            host="127.0.0.1",
            port=9030,
            env="bt5-quarantine",
            repository="memory",
        )
        store = RuntimePointerStore(settings)
        before = store.load_pointer("question_policy")
        candidate = make_baseline_candidate(
            candidate_id=f"{training_run_id}.question_policy.failed",
            family="question_policy",
            payload={
                "mode": "auto_apply_training",
                "family": "question_policy",
                "training_run_id": training_run_id,
                "weights": {"topic_weights": {"hidden_factor": 99.0}},
                "training_signals": [
                    {"signal_id": "v30.training_signal.question_dialogue_outcome"},
                    {"signal_id": "v30.training_signal.interaction_loop_quality"},
                ],
            },
            change_summary="BT5 intentionally failed question-policy candidate",
        )
        promotion = PromotionResult(
            candidate_id=candidate.candidate_id,
            family=candidate.family,
            promoted=False,
            validation_run_id=(
                "v30.synthetic.promotion.question_policy.all+"
                "v30.518k.sample.bt5_failed_candidate"
            ),
            failures=[
                "synthetic_validation_failed:visible_next_question_regression",
                "518k_sample_failed:question_policy_distribution_drift",
            ],
        )
        record = quarantine_failed_candidate(
            candidate=candidate,
            promotion=promotion,
            store=store,
            source_signals=candidate.payload["training_signals"],
            persist=True,
        )
        after = store.load_pointer("question_policy")
        runtime = create_smoke_runtime(
            reading_id=f"{training_run_id}.runtime-last-good",
            active_policy_version_overrides=store.active_versions(
                ("structure_policy", "mainline_policy", "question_policy", "rule_policy")
            ),
        )
        chart_status = "ready" if runtime.chart_context.natal_pillars else "pending"
        return build_training_candidate_quarantine(
            bt4_training_closeout=bt4,
            quarantine_record=record.model_dump(mode="json"),
            pointer_before=before.model_dump(mode="json"),
            pointer_after=after.model_dump(mode="json"),
            runtime_summary={
                "reading_id": runtime.reading_id,
                "question_policy_version": runtime.question_plan.policy_effect["active_policy_versions"]["question_policy"],
                "recommended_question_count": len(runtime.question_plan.recommended_questions),
                "chart_status": chart_status,
            },
        )


def build_training_candidate_quarantine(
    *,
    bt4_training_closeout: Mapping[str, Any],
    quarantine_record: Mapping[str, Any],
    pointer_before: Mapping[str, Any],
    pointer_after: Mapping[str, Any],
    runtime_summary: Mapping[str, Any],
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    bt4_summary = _bt4_summary(bt4_training_closeout)
    record = dict(quarantine_record)
    before = dict(pointer_before)
    after = dict(pointer_after)
    runtime = dict(runtime_summary)
    quarantine_summary = _quarantine_summary(record)
    pointer_summary = _pointer_summary(before, after)
    runtime_last_good = _runtime_last_good_summary(runtime, after)
    checks = _quarantine_checks(
        bt4_summary=bt4_summary,
        quarantine_summary=quarantine_summary,
        pointer_summary=pointer_summary,
        runtime_last_good=runtime_last_good,
    )
    decision = _decision(checks)
    return {
        "version": TRAINING_CANDIDATE_QUARANTINE_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["training_candidate_quarantine_ready"] else "blocked",
        "decision": decision,
        "bt4_summary": bt4_summary,
        "quarantine_summary": quarantine_summary,
        "runtime_pointer_summary": pointer_summary,
        "runtime_last_good_summary": runtime_last_good,
        "quarantine_record": record,
        "quarantine_checks": checks,
        "policy_boundary": {
            "closeout_admin_endpoint_read_only": True,
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "failed_candidate_pointer_write_allowed": False,
            "training_signal_may_change_chart_facts": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "boundary": "bt5_quarantine_records_failed_candidates_without_promoting_or_mutating_chart_facts",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "bt5_failed_training_candidates_are_quarantined_and_runtime_keeps_last_good_pointer",
    }


def _bt4_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, Mapping) else {}
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "training_system_closeout_ready": bool(decision.get("training_system_closeout_ready")),
        "training_completion": int(decision.get("training_completion", 0) or 0),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
    }


def _quarantine_summary(record: Mapping[str, Any]) -> dict[str, Any]:
    remediation = record.get("remediation_route", {})
    remediation = remediation if isinstance(remediation, Mapping) else {}
    return {
        "record_version": str(record.get("version") or ""),
        "record_id": str(record.get("record_id") or ""),
        "candidate_id": str(record.get("candidate_id") or ""),
        "family": str(record.get("family") or ""),
        "status": str(record.get("status") or ""),
        "source_signal_ids": list(record.get("source_signal_ids", []))
        if isinstance(record.get("source_signal_ids", []), list)
        else [],
        "source_signal_count": int(record.get("source_signal_count", 0) or 0),
        "failed_validation_ids": list(record.get("failed_validation_ids", []))
        if isinstance(record.get("failed_validation_ids", []), list)
        else [],
        "failure_count": len(record.get("failures", [])) if isinstance(record.get("failures", []), list) else 0,
        "rollback_target_artifact_id": str(
            (record.get("rollback_target_pointer", {}) if isinstance(record.get("rollback_target_pointer", {}), Mapping) else {}).get("active_artifact_id")
            or ""
        ),
        "pointer_unchanged": bool(record.get("pointer_unchanged")),
        "artifact_uri": str(record.get("artifact_uri") or ""),
        "remediation_route_id": str(remediation.get("route_id") or ""),
        "remediation_pointer_write_allowed": bool(remediation.get("runtime_pointer_write_allowed")),
        "remediation_chart_fact_mutation_allowed": bool(remediation.get("chart_fact_mutation_allowed")),
    }


def _pointer_summary(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "family": str(before.get("family") or after.get("family") or ""),
        "active_artifact_before": str(before.get("active_artifact_id") or ""),
        "active_artifact_after": str(after.get("active_artifact_id") or ""),
        "previous_artifact_before": str(before.get("previous_artifact_id") or ""),
        "previous_artifact_after": str(after.get("previous_artifact_id") or ""),
        "status_before": str(before.get("status") or ""),
        "status_after": str(after.get("status") or ""),
        "pointer_unchanged": before.get("active_artifact_id") == after.get("active_artifact_id"),
    }


def _runtime_last_good_summary(runtime: Mapping[str, Any], pointer_after: Mapping[str, Any]) -> dict[str, Any]:
    question_policy_version = str(runtime.get("question_policy_version") or "")
    pointer_artifact = str(pointer_after.get("active_artifact_id") or "")
    return {
        "reading_id": str(runtime.get("reading_id") or ""),
        "question_policy_version": question_policy_version,
        "pointer_active_artifact_id": pointer_artifact,
        "runtime_uses_last_good_pointer": question_policy_version == pointer_artifact,
        "recommended_question_count": int(runtime.get("recommended_question_count", 0) or 0),
        "chart_status": str(runtime.get("chart_status") or ""),
    }


def _quarantine_checks(
    *,
    bt4_summary: Mapping[str, Any],
    quarantine_summary: Mapping[str, Any],
    pointer_summary: Mapping[str, Any],
    runtime_last_good: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "bt4_training_closeout_ready",
            "passed": (
                bt4_summary["version"] == "v30.training_system_closeout.v1"
                and bt4_summary["training_system_closeout_ready"]
                and bt4_summary["decision_status"] == "bt4_training_system_closeout_ready"
            ),
            "expected": "BT4 training system closeout is ready before failed-candidate quarantine",
        },
        {
            "check_id": "failed_candidate_recorded_as_quarantined",
            "passed": (
                quarantine_summary["record_version"] == "v30.training_candidate_quarantine_record.v1"
                and quarantine_summary["status"] == "quarantined"
                and quarantine_summary["candidate_id"]
                and quarantine_summary["family"] == "question_policy"
            ),
            "expected": "failed candidate has a machine-readable quarantine record",
        },
        {
            "check_id": "source_signals_and_failed_validations_recorded",
            "passed": (
                quarantine_summary["source_signal_count"] >= 2
                and len(quarantine_summary["source_signal_ids"]) >= 2
                and len(quarantine_summary["failed_validation_ids"]) >= 2
                and quarantine_summary["failure_count"] >= 2
            ),
            "expected": "quarantine record includes source signals, failed validation ids, and failure reasons",
        },
        {
            "check_id": "rollback_target_and_artifact_recorded",
            "passed": (
                bool(quarantine_summary["rollback_target_artifact_id"])
                and quarantine_summary["pointer_unchanged"]
                and bool(quarantine_summary["artifact_uri"])
            ),
            "expected": "rollback target pointer and persisted quarantine artifact are recorded",
        },
        {
            "check_id": "pointer_stays_on_last_good_artifact",
            "passed": (
                pointer_summary["pointer_unchanged"]
                and pointer_summary["status_before"] == "active"
                and pointer_summary["status_after"] == "active"
            ),
            "expected": "failed candidate does not change the active runtime pointer",
        },
        {
            "check_id": "runtime_uses_last_good_pointer",
            "passed": (
                runtime_last_good["runtime_uses_last_good_pointer"]
                and runtime_last_good["recommended_question_count"] > 0
                and runtime_last_good["chart_status"] == "ready"
            ),
            "expected": "runtime remains usable and reads the last good active pointer",
        },
        {
            "check_id": "remediation_route_is_diagnostic_only",
            "passed": (
                quarantine_summary["remediation_route_id"] == "route.training_candidate_quarantine"
                and not quarantine_summary["remediation_pointer_write_allowed"]
                and not quarantine_summary["remediation_chart_fact_mutation_allowed"]
            ),
            "expected": "remediation route is diagnostic and cannot write pointers or chart facts",
        },
        {
            "check_id": "heavy_validation_and_chart_fact_boundaries_preserved",
            "passed": (
                not bt4_summary["chart_fact_mutation_allowed"]
                and not bt4_summary["full_pytest_required"]
                and not bt4_summary["full_518k_required"]
            ),
            "expected": "BT5 does not authorize chart fact mutation or default heavy gates",
        },
    ]


def _decision(checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if not row.get("passed")]
    ready = not failed
    return {
        "training_candidate_quarantine_ready": ready,
        "decision_status": "bt5_training_candidate_quarantine_ready" if ready else "bt5_training_candidate_quarantine_blocked",
        "quarantine_check_count": len(checks),
        "passed_quarantine_check_count": sum(1 for row in checks if row.get("passed")),
        "failed_check_ids": failed,
        "training_completion": 99 if ready else 97,
        "blockers": ["training_candidate_quarantine_checks_failed"] if failed else [],
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "rationale": (
            "Failed training candidates are quarantined with source signals, validation failures, rollback target, and last-good runtime pointer proof."
            if ready
            else "BT5 cannot complete until failed-candidate quarantine blockers are repaired."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["training_candidate_quarantine_ready"]:
        return {
            "task_id": "BT6",
            "title": "Synthetic Coverage Manifest",
            "selected_track": "brain_training_synthetic_completion",
            "scope": [
                "enumerate synthetic tiers and protected contracts",
                "separate validation coverage from truth claims",
                "prepare BT7/BT8 dedicated brain/training tiers",
            ],
        }
    return {
        "task_id": "BT5-FR",
        "title": "Training Candidate Quarantine Failure Review",
        "selected_track": "brain_training_synthetic_completion",
        "scope": [
            "inspect failed BT5 quarantine checks",
            "repair quarantine record, rollback target, or last-good pointer proof",
            "keep failed candidates out of active runtime pointers",
        ],
    }
