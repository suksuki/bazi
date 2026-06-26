from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.validation.core_calibration_queue_review import run_core_calibration_queue_review
from v30.validation.core_chain_steady_state_summary import run_core_chain_steady_state_summary


EVIDENCE_DRIVEN_CALIBRATION_QUEUE_VERSION = "v30.evidence_driven_calibration_queue.v1"


def run_evidence_driven_calibration_queue(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    core_chain = run_core_chain_steady_state_summary(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    queue_review = run_core_calibration_queue_review(sample_limit=sample_limit)
    return build_evidence_driven_calibration_queue(
        core_chain_steady_state=core_chain,
        core_calibration_queue_review=queue_review,
        artifact_dir=artifact_dir,
    )


def build_evidence_driven_calibration_queue(
    *,
    core_chain_steady_state: Mapping[str, Any],
    core_calibration_queue_review: Mapping[str, Any],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    evaluated_at = datetime.now(timezone.utc)
    queue_id = f"v30.evidence_queue.e1.{evaluated_at.strftime('%Y%m%d%H%M%S%f')}"
    core_summary = _core_chain_summary(core_chain_steady_state)
    queue_summary = _queue_review_summary(core_calibration_queue_review)
    intake_sources = _intake_sources()
    checks = _checks(core_summary=core_summary, queue_summary=queue_summary)
    decision = _decision(checks=checks, queue_summary=queue_summary)
    payload: dict[str, Any] = {
        "version": EVIDENCE_DRIVEN_CALIBRATION_QUEUE_VERSION,
        "queue_id": queue_id,
        "evaluated_at": evaluated_at.isoformat(),
        "status": "completed" if decision["evidence_driven_queue_ready"] else "blocked",
        "decision": decision,
        "core_chain_summary": core_summary,
        "queue_review_summary": queue_summary,
        "evidence_intake_sources": intake_sources,
        "checks": checks,
        "queue_policy": {
            "scope": "post_steady_state_concrete_evidence_only",
            "accepted_evidence_required": True,
            "default_core_module_reopen_allowed": False,
            "focused_fix_execution_allowed": False,
            "default_heavy_validation": False,
            "full_pytest_trigger": "explicit_major_node_only",
            "synthetic_all_trigger": "explicit_major_node_only",
            "full_518k_trigger": "explicit_major_node_or_distribution_drift_only",
            "live_llm_trigger": "explicit_provider_smoke_only",
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "boundary": "e1_accepts_only_evidence_backed_calibration_without_reopening_core_modules",
        },
        "policy_boundary": {
            "m1_m8_reopen_by_default": False,
            "iq_llm_bt_u_reopen_by_default": False,
            "runtime_decision_write_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "e1_operates_post_steady_state_evidence_queue_without_heavy_default_gates",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _core_chain_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "core_chain_steady_state_ready": bool(decision.get("core_chain_steady_state_ready")),
        "module_count": int(decision.get("module_count", 0) or 0),
        "passed_check_count": int(decision.get("passed_check_count", 0) or 0),
        "check_count": int(decision.get("check_count", 0) or 0),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "pointer_write_performed": bool(decision.get("pointer_write_performed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "synthetic_all_required": bool(decision.get("synthetic_all_required")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "live_llm_required": bool(decision.get("live_llm_required")),
    }


def _queue_review_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "queue_review_ready": bool(decision.get("queue_review_ready")),
        "reviewed_module_count": int(decision.get("reviewed_module_count", 0) or 0),
        "focused_fix_candidate_count": int(decision.get("focused_fix_candidate_count", 0) or 0),
        "focused_module_fix_required": bool(decision.get("focused_module_fix_required")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "pointer_write_performed": bool(decision.get("pointer_write_performed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "module_reviews": _list(payload.get("module_reviews")),
    }


def _intake_sources() -> list[dict[str, Any]]:
    return [
        {
            "source_id": "real_case_calibration",
            "accepted_inputs": ["fixture regression", "boundary case mismatch", "calibration drift tag"],
            "allowed_targets": ["M3", "M4", "M5", "M6", "M7", "IQ"],
            "can_mutate_chart_facts": False,
        },
        {
            "source_id": "business_acceptance",
            "accepted_inputs": ["customer reading regression", "answer refresh failure", "blocked-input behavior"],
            "allowed_targets": ["M6", "M8", "IQ", "LLM", "U"],
            "can_mutate_chart_facts": False,
        },
        {
            "source_id": "518k_distribution",
            "accepted_inputs": ["sample failure cluster", "shard drift", "coverage gap"],
            "allowed_targets": ["M3", "M4", "M5", "M7", "BT"],
            "can_mutate_chart_facts": False,
        },
        {
            "source_id": "training_signal_distribution",
            "accepted_inputs": ["signal gap", "policy candidate gap", "synthetic tier failure"],
            "allowed_targets": ["M3", "M4", "M5", "M6", "IQ", "LLM", "BT"],
            "can_mutate_chart_facts": False,
        },
        {
            "source_id": "llm_expression_acceptance",
            "accepted_inputs": ["fallback overuse", "role leak", "unsupported claim", "streaming expression failure"],
            "allowed_targets": ["LLM", "M6", "IQ"],
            "can_mutate_chart_facts": False,
        },
        {
            "source_id": "question_chain_acceptance",
            "accepted_inputs": ["visible/internal split failure", "question order drift", "hidden probe leak"],
            "allowed_targets": ["IQ", "M5", "M7", "BT"],
            "can_mutate_chart_facts": False,
        },
    ]


def _checks(
    *,
    core_summary: Mapping[str, Any],
    queue_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "core_chain_steady_before_evidence_queue",
            "passed": (
                core_summary["version"] == "v30.core_chain_steady_state_summary.v1"
                and core_summary["core_chain_steady_state_ready"]
                and core_summary["module_count"] >= 13
                and core_summary["passed_check_count"] == core_summary["check_count"]
            ),
            "expected": "S-S1 core chain is steady before accepting new calibration queue work",
        },
        {
            "check_id": "queue_review_ready",
            "passed": (
                queue_summary["version"] == "v30.core_calibration_queue_review.v1"
                and queue_summary["queue_review_ready"]
            ),
            "expected": "focused evidence queue review is ready",
        },
        {
            "check_id": "no_default_heavy_or_live_gate",
            "passed": (
                not core_summary["synthetic_all_required"]
                and not core_summary["full_pytest_required"]
                and not core_summary["full_518k_required"]
                and not core_summary["live_llm_required"]
                and not queue_summary["full_pytest_required"]
                and not queue_summary["full_518k_required"]
            ),
            "expected": "heavy validation and live LLM remain explicit-only",
        },
        {
            "check_id": "no_pointer_or_chart_fact_mutation",
            "passed": (
                not core_summary["policy_pointer_promotion_allowed"]
                and not core_summary["pointer_write_performed"]
                and not core_summary["chart_fact_mutation_allowed"]
                and not queue_summary["policy_pointer_promotion_allowed"]
                and not queue_summary["pointer_write_performed"]
                and not queue_summary["chart_fact_mutation_allowed"]
            ),
            "expected": "queue is read-only and cannot mutate deterministic facts or pointers",
        },
    ]


def _decision(*, checks: list[Mapping[str, Any]], queue_summary: Mapping[str, Any]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    candidate_count = int(queue_summary.get("focused_fix_candidate_count", 0) or 0)
    return {
        "decision_status": (
            "evidence_driven_calibration_queue_ready"
            if ready and candidate_count == 0
            else "evidence_driven_calibration_queue_has_candidates"
            if ready
            else "evidence_driven_calibration_queue_blocked"
        ),
        "evidence_driven_queue_ready": ready,
        "post_steady_state_mode": True,
        "concrete_evidence_required": True,
        "focused_fix_candidate_count": candidate_count,
        "focused_module_fix_required": ready and candidate_count > 0,
        "reviewed_module_count": int(queue_summary.get("reviewed_module_count", 0) or 0),
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
        "blockers": ["evidence_queue_checks_failed"] if failed else [],
        "rationale": (
            "Core chain is steady and no focused candidates are queued; wait for concrete calibration evidence."
            if ready and candidate_count == 0
            else "Concrete evidence has focused candidates; prepare a narrow fix plan without global module reopen."
            if ready
            else "Evidence-driven queue is blocked until core steady-state and queue review checks pass."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if not decision["evidence_driven_queue_ready"]:
        return {
            "next_task": "Evidence Queue Remediation",
            "reason": "Repair failed E-S1 checks before accepting post-steady-state calibration evidence.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    if decision["focused_module_fix_required"]:
        return {
            "next_task": "Focused Calibration Fix Plan",
            "reason": "Queued evidence exists; open only the affected module targets and keep deterministic facts read-only.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "Await New Calibration Evidence",
        "reason": "No concrete evidence is queued; keep routine targeted monitoring active.",
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['queue_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
