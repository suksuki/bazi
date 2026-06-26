from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from v30.config import V30Settings
from v30.validation.corpus_518k_readiness_matrix import run_518k_readiness_matrix
from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.synthetic_coverage_manifest import run_synthetic_coverage_manifest


BRAIN_TRAINING_SYNTHETIC_CLOSEOUT_VERSION = "v30.brain_training_synthetic_closeout.v1"


def run_brain_training_synthetic_closeout(
    *,
    sample_limit: int = 8,
    shard_id: int = 7,
    shard_limit: int = 16,
    artifact_dir: str | Path | None = None,
    settings: V30Settings | None = None,
) -> dict[str, Any]:
    central_brain = run_synthetic_tier("central_brain")
    training_pipeline = run_synthetic_tier("training_pipeline")
    manifest = run_synthetic_coverage_manifest()
    readiness = run_518k_readiness_matrix(
        sample_limit=sample_limit,
        shard_id=shard_id,
        shard_limit=shard_limit,
        artifact_dir=artifact_dir,
        settings=settings,
    )
    return build_brain_training_synthetic_closeout(
        central_brain_synthetic=central_brain.model_dump(mode="json"),
        training_pipeline_synthetic=training_pipeline.model_dump(mode="json"),
        synthetic_coverage_manifest=manifest,
        readiness_518k_matrix=readiness,
    )


def build_brain_training_synthetic_closeout(
    *,
    central_brain_synthetic: Mapping[str, Any],
    training_pipeline_synthetic: Mapping[str, Any],
    synthetic_coverage_manifest: Mapping[str, Any],
    readiness_518k_matrix: Mapping[str, Any],
) -> dict[str, Any]:
    central = dict(central_brain_synthetic)
    training = dict(training_pipeline_synthetic)
    manifest = dict(synthetic_coverage_manifest)
    readiness = dict(readiness_518k_matrix)
    evidence = _evidence_summary(
        central=central,
        training=training,
        manifest=manifest,
        readiness=readiness,
    )
    completion = _completion_summary(evidence)
    checks = _closeout_checks(evidence=evidence, completion=completion)
    decision = _decision(checks)
    return {
        "version": BRAIN_TRAINING_SYNTHETIC_CLOSEOUT_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["closeout_ready"] else "blocked",
        "decision": decision,
        "completion_summary": completion,
        "bt_evidence_summary": evidence,
        "closeout_checks": checks,
        "steady_state": {
            "state_id": "BT-S1",
            "status": "support_systems_steady_state" if decision["closeout_ready"] else "support_systems_closeout_blocked",
            "default_validation_cadence": "targeted_tier_or_new_evidence_only",
            "next_reopen_conditions": [
                "central_brain_contract_regression",
                "training_signal_or_candidate_boundary_regression",
                "synthetic_manifest_undocumented_tier",
                "518k_sample_or_shard_distribution_drift",
                "explicit_release_or_full_freeze_request",
            ],
        },
        "policy_boundary": {
            "closeout_is_read_only": True,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "synthetic_all_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "boundary": "bt10_closeout_records_support_system_steady_state_without_reopening_core_or_running_heavy_gates",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "bt10_unified_brain_training_synthetic_closeout",
    }


def _evidence_summary(
    *,
    central: Mapping[str, Any],
    training: Mapping[str, Any],
    manifest: Mapping[str, Any],
    readiness: Mapping[str, Any],
) -> dict[str, Any]:
    manifest_decision = manifest.get("decision", {})
    manifest_decision = manifest_decision if isinstance(manifest_decision, Mapping) else {}
    readiness_decision = readiness.get("decision", {})
    readiness_decision = readiness_decision if isinstance(readiness_decision, Mapping) else {}
    return {
        "bt1_bt3_central_brain": {
            "source": str(central.get("suite_id") or ""),
            "ready": bool(central.get("passed")),
            "case_count": int(central.get("case_count", 0) or 0),
            "passed_count": int(central.get("passed_count", 0) or 0),
            "expected_case_count": 5,
            "covers_acceptance_session_failure_routes": bool(central.get("passed")) and int(central.get("case_count", 0) or 0) >= 5,
        },
        "bt4_bt5_training": {
            "source": str(training.get("suite_id") or ""),
            "ready": bool(training.get("passed")),
            "case_count": int(training.get("case_count", 0) or 0),
            "passed_count": int(training.get("passed_count", 0) or 0),
            "expected_min_case_count": 80,
            "covers_signal_candidate_validation_quarantine_boundaries": bool(training.get("passed"))
            and int(training.get("case_count", 0) or 0) >= 80,
        },
        "bt6_synthetic_manifest": {
            "version": str(manifest.get("version") or ""),
            "ready": bool(manifest_decision.get("synthetic_coverage_manifest_ready")),
            "decision_status": str(manifest_decision.get("decision_status") or ""),
            "synthetic_completion": int(manifest_decision.get("synthetic_completion", 0) or 0),
            "next_task": str((manifest.get("next_mainline_selection", {}) if isinstance(manifest.get("next_mainline_selection", {}), Mapping) else {}).get("task_id") or ""),
        },
        "bt7_central_brain_synthetic": {
            "ready": bool(central.get("passed")),
            "suite_id": str(central.get("suite_id") or ""),
            "case_count": int(central.get("case_count", 0) or 0),
        },
        "bt8_training_pipeline_synthetic": {
            "ready": bool(training.get("passed")),
            "suite_id": str(training.get("suite_id") or ""),
            "case_count": int(training.get("case_count", 0) or 0),
        },
        "bt9_518k_readiness": {
            "version": str(readiness.get("version") or ""),
            "ready": bool(readiness_decision.get("readiness_matrix_ready")),
            "decision_status": str(readiness_decision.get("decision_status") or ""),
            "validation_518k_completion": int(readiness_decision.get("validation_518k_completion", 0) or 0),
            "full_518k_required": bool(readiness_decision.get("full_518k_required")),
            "next_task": str((readiness.get("next_mainline_selection", {}) if isinstance(readiness.get("next_mainline_selection", {}), Mapping) else {}).get("task_id") or ""),
        },
    }


def _completion_summary(evidence: Mapping[str, Any]) -> dict[str, Any]:
    central_ready = _ready(evidence, "bt1_bt3_central_brain") and _ready(evidence, "bt7_central_brain_synthetic")
    training_ready = _ready(evidence, "bt4_bt5_training") and _ready(evidence, "bt8_training_pipeline_synthetic")
    manifest_ready = _ready(evidence, "bt6_synthetic_manifest")
    readiness_ready = _ready(evidence, "bt9_518k_readiness")
    return {
        "central_brain_completion": 100 if central_ready else 97,
        "training_completion": 100 if training_ready else 99,
        "synthetic_completion": 100 if manifest_ready and central_ready and training_ready else 99,
        "validation_518k_completion": 95 if readiness_ready else 85,
        "support_systems_current_scope_complete": central_ready and training_ready and manifest_ready and readiness_ready,
    }


def _closeout_checks(*, evidence: Mapping[str, Any], completion: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "central_brain_current_scope_ready",
            "passed": _ready(evidence, "bt1_bt3_central_brain") and _ready(evidence, "bt7_central_brain_synthetic"),
            "expected": "central brain acceptance/session/routing contracts are represented by the passing central_brain tier",
        },
        {
            "check_id": "training_current_scope_ready",
            "passed": _ready(evidence, "bt4_bt5_training") and _ready(evidence, "bt8_training_pipeline_synthetic"),
            "expected": "training signal/candidate/validation/quarantine boundaries are represented by the passing training_pipeline tier",
        },
        {
            "check_id": "synthetic_manifest_ready",
            "passed": _ready(evidence, "bt6_synthetic_manifest")
            and _nested(evidence, "bt6_synthetic_manifest", "synthetic_completion") >= 99,
            "expected": "synthetic coverage manifest is ready with central_brain and training_pipeline implemented",
        },
        {
            "check_id": "518k_readiness_matrix_ready",
            "passed": _ready(evidence, "bt9_518k_readiness")
            and _nested(evidence, "bt9_518k_readiness", "validation_518k_completion") >= 95
            and not bool(_nested(evidence, "bt9_518k_readiness", "full_518k_required")),
            "expected": "518K readiness matrix is ready and full 518K remains explicit-only",
        },
        {
            "check_id": "completion_targets_reached",
            "passed": (
                completion["central_brain_completion"] == 100
                and completion["training_completion"] == 100
                and completion["synthetic_completion"] == 100
                and completion["validation_518k_completion"] == 95
            ),
            "expected": "current-scope completion targets are reached",
        },
        {
            "check_id": "heavy_gates_remain_explicit",
            "passed": True,
            "expected": "BT10 closeout does not run or authorize full pytest, synthetic all, or full 518K by default",
        },
    ]


def _decision(checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if not row.get("passed")]
    ready = not failed
    return {
        "closeout_ready": ready,
        "decision_status": "bt10_support_systems_steady_state_ready" if ready else "bt10_closeout_blocked",
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("passed")),
        "failed_check_ids": failed,
        "support_systems_steady_state": ready,
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": ["brain_training_synthetic_closeout_checks_failed"] if failed else [],
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["closeout_ready"]:
        return {
            "task_id": "BT-S1",
            "title": "Support Systems Steady State",
            "selected_track": "steady_state",
            "scope": [
                "wait for new calibration or business evidence",
                "run targeted tier checks only when evidence changes",
                "keep heavy gates explicit",
            ],
        }
    return {
        "task_id": "BT10-FR",
        "title": "Support Systems Closeout Failure Review",
        "selected_track": "brain_training_synthetic_completion",
        "scope": [
            "inspect failed closeout checks",
            "repair affected BT evidence",
            "avoid unrelated module work",
        ],
    }


def _ready(evidence: Mapping[str, Any], key: str) -> bool:
    row = evidence.get(key, {})
    return bool(row.get("ready")) if isinstance(row, Mapping) else False


def _nested(evidence: Mapping[str, Any], section: str, key: str) -> int:
    row = evidence.get(section, {})
    if not isinstance(row, Mapping):
        return 0
    return int(row.get(key, 0) or 0)
