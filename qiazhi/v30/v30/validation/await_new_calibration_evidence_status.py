from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.validation.evidence_driven_calibration_queue import run_evidence_driven_calibration_queue


AWAIT_NEW_CALIBRATION_EVIDENCE_STATUS_VERSION = "v30.await_new_calibration_evidence_status.v1"


def run_await_new_calibration_evidence_status(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    evidence_queue = run_evidence_driven_calibration_queue(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    return build_await_new_calibration_evidence_status(
        evidence_driven_calibration_queue=evidence_queue,
        artifact_dir=artifact_dir,
    )


def build_await_new_calibration_evidence_status(
    *,
    evidence_driven_calibration_queue: Mapping[str, Any],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    recorded_at = datetime.now(timezone.utc)
    status_id = f"v30.await_evidence.w1.{recorded_at.strftime('%Y%m%d%H%M%S%f')}"
    queue_summary = _queue_summary(evidence_driven_calibration_queue)
    checks = _checks(queue_summary)
    decision = _decision(checks=checks, queue_summary=queue_summary)
    payload: dict[str, Any] = {
        "version": AWAIT_NEW_CALIBRATION_EVIDENCE_STATUS_VERSION,
        "status_id": status_id,
        "recorded_at": recorded_at.isoformat(),
        "status": "completed" if decision["await_new_evidence_ready"] else "blocked",
        "decision": decision,
        "evidence_queue_summary": queue_summary,
        "wait_policy": {
            "current_state": "W-S1 Await New Calibration Evidence",
            "default_action": "serve_current_core_bazi_system_and_collect_concrete_evidence",
            "accepted_evidence_sources": queue_summary["accepted_evidence_source_ids"],
            "new_evidence_entrypoint": "E-S1 Evidence-Driven Calibration Queue",
            "candidate_entrypoint": "Focused Calibration Fix Plan",
            "core_module_reopen_by_default": False,
            "runtime_decision_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "boundary": "w_s1_waits_for_evidence_without_runtime_mutation",
        },
        "routine_cadence": {
            "routine_command": "python3 scripts/run_await_new_calibration_evidence_status.py --sample-limit 8",
            "evidence_queue_command": "python3 scripts/run_evidence_driven_calibration_queue.py --sample-limit 8",
            "major_node_commands": [
                "python3 scripts/run_synthetic_validation.py --tier all",
                "pytest -q",
                "python3 scripts/run_llm_live_smoke.py --json",
                "python3 scripts/run_518k_validation.py --mode full --confirm-full",
            ],
            "major_node_commands_explicit_only": True,
        },
        "policy_boundary": {
            "full_pytest_run_allowed_by_default": False,
            "synthetic_all_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "live_llm_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "w_s1_records_await_new_calibration_evidence_without_heavy_default_gates",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _queue_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    sources = _list(payload.get("evidence_intake_sources"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "evidence_driven_queue_ready": bool(decision.get("evidence_driven_queue_ready")),
        "focused_fix_candidate_count": int(decision.get("focused_fix_candidate_count", 0) or 0),
        "focused_module_fix_required": bool(decision.get("focused_module_fix_required")),
        "concrete_evidence_required": bool(decision.get("concrete_evidence_required")),
        "core_module_reopen_by_default": bool(decision.get("core_module_reopen_by_default")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "synthetic_all_required": bool(decision.get("synthetic_all_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "live_llm_required": bool(decision.get("live_llm_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "pointer_write_performed": bool(decision.get("pointer_write_performed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "accepted_evidence_source_ids": [str(row.get("source_id") or "") for row in sources if isinstance(row, Mapping)],
    }


def _checks(queue_summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "e_s1_evidence_queue_ready",
            "passed": (
                queue_summary["version"] == "v30.evidence_driven_calibration_queue.v1"
                and queue_summary["evidence_driven_queue_ready"]
            ),
            "expected": "E-S1 evidence-driven calibration queue is ready",
        },
        {
            "check_id": "no_current_focused_candidates",
            "passed": queue_summary["focused_fix_candidate_count"] == 0
            and not queue_summary["focused_module_fix_required"],
            "expected": "no focused calibration candidates are currently queued",
        },
        {
            "check_id": "accepted_evidence_sources_registered",
            "passed": set(queue_summary["accepted_evidence_source_ids"]) >= {
                "real_case_calibration",
                "business_acceptance",
                "518k_distribution",
                "training_signal_distribution",
                "llm_expression_acceptance",
                "question_chain_acceptance",
            },
            "expected": "all post-steady-state evidence intake sources are registered",
        },
        {
            "check_id": "no_heavy_pointer_or_fact_mutation",
            "passed": (
                not queue_summary["core_module_reopen_by_default"]
                and not queue_summary["full_pytest_required"]
                and not queue_summary["synthetic_all_required"]
                and not queue_summary["full_518k_required"]
                and not queue_summary["live_llm_required"]
                and not queue_summary["policy_pointer_promotion_allowed"]
                and not queue_summary["pointer_write_performed"]
                and not queue_summary["chart_fact_mutation_allowed"]
            ),
            "expected": "wait state does not run heavy gates, promote pointers, or mutate chart facts",
        },
    ]


def _decision(*, checks: list[Mapping[str, Any]], queue_summary: Mapping[str, Any]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    candidate_count = int(queue_summary.get("focused_fix_candidate_count", 0) or 0)
    ready = not failed
    return {
        "decision_status": "await_new_calibration_evidence_ready" if ready else "await_new_calibration_evidence_blocked",
        "await_new_evidence_ready": ready,
        "waiting_for_new_calibration_evidence": ready,
        "focused_fix_candidate_count": candidate_count,
        "focused_module_fix_required": candidate_count > 0,
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("passed") is True),
        "failed_check_ids": failed,
        "core_module_reopen_by_default": False,
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "live_llm_required": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": ["await_new_evidence_checks_failed"] if failed else [],
        "rationale": (
            "No concrete calibration evidence is queued; keep serving the current core Bazi system and wait for evidence."
            if ready
            else "Cannot enter wait state until E-S1 is ready and current focused candidates are handled."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["await_new_evidence_ready"]:
        return {
            "next_task": "Await Evidence Or Explicit Major Validation",
            "reason": "The core chain remains steady and no focused candidates are queued.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    if decision["focused_module_fix_required"]:
        return {
            "next_task": "Focused Calibration Fix Plan",
            "reason": "Handle queued focused candidates before returning to wait state.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "Await State Remediation",
        "reason": "Repair failed wait-state checks before resuming steady-state wait.",
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['status_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
