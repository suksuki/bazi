from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from v30.validation.core_answer_calibration_steady_state_queue import (
    CORE_ANSWER_CALIBRATION_STEADY_STATE_QUEUE_VERSION,
    run_core_answer_calibration_steady_state_queue,
)


CORE_ANSWER_CALIBRATION_WAIT_STATUS_VERSION = "v30.core_answer_calibration_wait_status.v1"


def run_core_answer_calibration_wait_status(
    *,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    queue = run_core_answer_calibration_steady_state_queue(artifact_dir=artifact_dir)
    return build_core_answer_calibration_wait_status(
        core_answer_calibration_queue=queue,
        artifact_dir=artifact_dir,
    )


def build_core_answer_calibration_wait_status(
    *,
    core_answer_calibration_queue: Mapping[str, Any],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    recorded_at = datetime.now(timezone.utc)
    status_id = f"v30.core_answer_calibration.wait.{recorded_at.strftime('%Y%m%d%H%M%S%f')}"
    queue_summary = _queue_summary(core_answer_calibration_queue)
    checks = _checks(queue_summary)
    decision = _decision(checks=checks, queue_summary=queue_summary)
    payload: dict[str, Any] = {
        "version": CORE_ANSWER_CALIBRATION_WAIT_STATUS_VERSION,
        "status_id": status_id,
        "recorded_at": recorded_at.isoformat(),
        "status": "completed" if decision["core_answer_calibration_wait_ready"] else "blocked",
        "task": {
            "task_id": "CORE-CAL-WAIT",
            "title": "Await Focused Answer Quality Evidence Or Explicit Major Validation",
            "scope": "serve_current_answer_system_and_wait_for_focused_answer_quality_evidence",
        },
        "queue_summary": queue_summary,
        "checks": checks,
        "decision": decision,
        "wait_policy": {
            "current_state": "answer_calibration_wait",
            "default_action": "serve_current_bazi_answer_system",
            "accepted_evidence_sources": queue_summary["accepted_evidence_source_ids"],
            "candidate_entrypoint": "CORE-CAL-S4-FIX Focused Answer Calibration Fix Plan",
            "routine_targeted_command": "python3 scripts/run_core_answer_calibration_wait_status.py",
            "core_module_reopen_by_default": False,
            "runtime_decision_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "boundary": "core_cal_wait_records_answer_calibration_wait_without_runtime_mutation",
        },
        "routine_cadence": {
            "routine_commands": [
                "python3 scripts/run_synthetic_typical_bazi_answer_calibration.py",
                "python3 scripts/run_synthetic_validation.py --tier synthetic_typical_bazi_answer",
                "python3 scripts/run_synthetic_typical_answer_training_signal_review.py",
                "python3 scripts/run_synthetic_typical_answer_calibration_closeout.py",
                "python3 scripts/run_core_answer_calibration_steady_state_queue.py",
                "python3 scripts/run_core_answer_calibration_wait_status.py",
            ],
            "major_node_commands_explicit_only": [
                "pytest -q",
                "python3 scripts/run_synthetic_validation.py --tier all",
                "python3 scripts/run_518k_validation.py --mode full --confirm-full",
                "python3 scripts/run_llm_live_smoke.py --json",
            ],
        },
        "policy_boundary": {
            "full_pytest_run_allowed_by_default": False,
            "synthetic_all_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "live_llm_run_allowed_by_default": False,
            "external_release_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "core_cal_wait_is_read_only_status_not_a_new_module_task",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _queue_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    queue_policy = _mapping(payload.get("queue_policy"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "queue_ready": bool(decision.get("core_answer_calibration_steady_state_queue_ready")),
        "waiting_for_new_answer_quality_evidence": bool(decision.get("waiting_for_new_answer_quality_evidence")),
        "focused_answer_fix_candidate_count": int(decision.get("focused_answer_fix_candidate_count", 0) or 0),
        "focused_answer_fix_required": bool(decision.get("focused_answer_fix_required")),
        "core_module_reopen_by_default": bool(decision.get("core_module_reopen_by_default")),
        "accepted_evidence_source_ids": _str_list(queue_policy.get("accepted_evidence_source_ids")),
        "allowed_target_modules": _str_list(queue_policy.get("allowed_target_modules")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "synthetic_all_required": bool(decision.get("synthetic_all_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "live_llm_required": bool(decision.get("live_llm_required")),
        "external_release_allowed": bool(decision.get("external_release_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "auto_apply_training_allowed": bool(decision.get("auto_apply_training_allowed")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
    }


def _checks(queue_summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "core_cal_s4_answer_queue_ready",
            "passed": queue_summary["version"] == CORE_ANSWER_CALIBRATION_STEADY_STATE_QUEUE_VERSION
            and queue_summary["queue_ready"] is True,
            "observed": queue_summary,
        },
        {
            "check_id": "waiting_without_current_candidates",
            "passed": queue_summary["waiting_for_new_answer_quality_evidence"] is True
            and int(queue_summary["focused_answer_fix_candidate_count"]) == 0
            and queue_summary["focused_answer_fix_required"] is False,
            "observed": {
                "waiting": queue_summary["waiting_for_new_answer_quality_evidence"],
                "candidate_count": queue_summary["focused_answer_fix_candidate_count"],
                "focused_answer_fix_required": queue_summary["focused_answer_fix_required"],
            },
        },
        {
            "check_id": "answer_evidence_sources_registered",
            "passed": set(queue_summary["accepted_evidence_source_ids"]) >= {
                "answer_quality_delta_review",
                "synthetic_typical_bazi_answer",
                "runtime_answer_integration",
                "business_answer_refresh",
                "llm_output_acceptance",
                "user_feedback_answer_quality",
            },
            "observed": queue_summary["accepted_evidence_source_ids"],
        },
        {
            "check_id": "answer_targets_limited",
            "passed": set(queue_summary["allowed_target_modules"]) <= {"M3", "M6", "LLM", "interaction"}
            and set(queue_summary["allowed_target_modules"]) >= {"M3", "M6", "LLM", "interaction"},
            "observed": queue_summary["allowed_target_modules"],
        },
        {
            "check_id": "no_heavy_release_or_mutation_defaults",
            "passed": queue_summary["core_module_reopen_by_default"] is False
            and queue_summary["full_pytest_required"] is False
            and queue_summary["synthetic_all_required"] is False
            and queue_summary["full_518k_required"] is False
            and queue_summary["live_llm_required"] is False
            and queue_summary["external_release_allowed"] is False
            and queue_summary["chart_fact_mutation_allowed"] is False
            and queue_summary["auto_apply_training_allowed"] is False
            and queue_summary["policy_pointer_promotion_allowed"] is False,
            "observed": {
                "core_module_reopen_by_default": queue_summary["core_module_reopen_by_default"],
                "full_pytest_required": queue_summary["full_pytest_required"],
                "synthetic_all_required": queue_summary["synthetic_all_required"],
                "full_518k_required": queue_summary["full_518k_required"],
                "live_llm_required": queue_summary["live_llm_required"],
            },
        },
    ]


def _decision(*, checks: list[Mapping[str, Any]], queue_summary: Mapping[str, Any]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "core_answer_calibration_wait_ready": ready,
        "decision_status": "core_cal_wait_answer_quality_evidence_wait_ready"
        if ready
        else "core_cal_wait_answer_quality_evidence_wait_blocked",
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("passed") is True),
        "failed_check_ids": failed,
        "waiting_for_new_answer_quality_evidence": ready,
        "focused_answer_fix_candidate_count": int(queue_summary.get("focused_answer_fix_candidate_count", 0) or 0),
        "focused_answer_fix_required": False,
        "core_module_reopen_by_default": False,
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "live_llm_required": False,
        "external_release_allowed": False,
        "chart_fact_mutation_allowed": False,
        "auto_apply_training_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "blockers": ["core_cal_wait_checks_failed"] if failed else [],
        "rationale": (
            "Answer calibration is steady; wait for focused evidence or explicit major validation."
            if ready
            else "CORE-CAL-WAIT is blocked until the S4 answer queue is ready and empty."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("core_answer_calibration_wait_ready") is True:
        return {
            "task_id": "CORE-CAL-WAIT",
            "title": "Await Focused Answer Quality Evidence Or Explicit Major Validation",
            "selected_track": "core_answer_calibration",
            "scope": [
                "serve current Bazi answer system",
                "collect concrete answer-quality evidence",
                "run targeted S1-S4 chain when answer logic changes",
                "run full pytest/synthetic-all/full-518K only at explicit major nodes",
            ],
        }
    return {
        "task_id": "CORE-CAL-WAIT-FR",
        "title": "Answer Calibration Wait State Failure Review",
        "selected_track": "core_answer_calibration",
        "scope": [
            "repair failed wait-state checks",
            "do not reopen M3/M6/LLM/interaction globally while blocked",
        ],
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _str_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(row) for row in value if str(row)]
    return []


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['status_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
