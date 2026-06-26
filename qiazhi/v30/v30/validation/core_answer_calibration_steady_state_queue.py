from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from v30.validation.synthetic_typical_answer_calibration_closeout import (
    SYNTHETIC_TYPICAL_ANSWER_CALIBRATION_CLOSEOUT_VERSION,
    run_synthetic_typical_answer_calibration_closeout,
)


CORE_ANSWER_CALIBRATION_STEADY_STATE_QUEUE_VERSION = "v30.core_answer_calibration_steady_state_queue.v1"


def run_core_answer_calibration_steady_state_queue(
    *,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    return build_core_answer_calibration_steady_state_queue(
        typical_answer_closeout=run_synthetic_typical_answer_calibration_closeout(),
        answer_quality_evidence=[],
        artifact_dir=artifact_dir,
    )


def build_core_answer_calibration_steady_state_queue(
    *,
    typical_answer_closeout: Mapping[str, Any],
    answer_quality_evidence: list[Mapping[str, Any]] | None = None,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    recorded_at = datetime.now(timezone.utc)
    queue_id = f"v30.core_answer_calibration.s4.{recorded_at.strftime('%Y%m%d%H%M%S%f')}"
    closeout_summary = _closeout_summary(typical_answer_closeout)
    evidence_rows = _evidence_rows(answer_quality_evidence or [])
    queue_items = _queue_items(evidence_rows)
    cadence = _steady_state_cadence()
    checks = _checks(closeout_summary=closeout_summary, evidence_rows=evidence_rows, queue_items=queue_items, cadence=cadence)
    decision = _decision(checks=checks, queue_items=queue_items)
    payload: dict[str, Any] = {
        "version": CORE_ANSWER_CALIBRATION_STEADY_STATE_QUEUE_VERSION,
        "queue_id": queue_id,
        "recorded_at": recorded_at.isoformat(),
        "status": "completed" if decision["core_answer_calibration_steady_state_queue_ready"] else "blocked",
        "task": {
            "task_id": "CORE-CAL-S4",
            "title": "Core Answer Calibration Steady-State Queue",
            "scope": "keep_typical_answer_calibration_steady_and_reopen_only_from_answer_quality_evidence",
        },
        "typical_answer_closeout_summary": closeout_summary,
        "answer_quality_evidence": evidence_rows,
        "calibration_queue_items": queue_items,
        "steady_state_cadence": cadence,
        "checks": checks,
        "decision": decision,
        "queue_policy": {
            "current_mode": "answer_calibration_steady_state_wait",
            "accepted_evidence_source_ids": cadence["evidence_entrypoints"],
            "allowed_target_modules": ["M3", "M6", "LLM", "interaction"],
            "core_module_reopen_by_default": False,
            "runtime_decision_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "boundary": "core_cal_s4_accepts_answer_quality_evidence_without_default_core_logic_changes",
        },
        "policy_boundary": {
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
            "external_release_allowed": False,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "fixed_bazi_verdict_allowed": False,
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "core_cal_s4_is_a_steady_answer_calibration_queue_not_a_runtime_patch",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _closeout_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    cadence = _mapping(payload.get("routine_cadence"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "closed": bool(decision.get("synthetic_typical_answer_calibration_closed")),
        "closeout_check_count": int(decision.get("closeout_check_count", 0) or 0),
        "passed_closeout_check_count": int(decision.get("passed_closeout_check_count", 0) or 0),
        "training_signal_count": int(decision.get("training_signal_count", 0) or 0),
        "queued_item_count": int(decision.get("queued_item_count", 0) or 0),
        "routine_targeted_commands": _str_list(cadence.get("routine_targeted_commands")),
        "external_release_allowed": bool(decision.get("external_release_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "auto_apply_training_allowed": bool(decision.get("auto_apply_training_allowed")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "synthetic_all_required": bool(decision.get("synthetic_all_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "live_llm_required": bool(decision.get("live_llm_required")),
    }


def _evidence_rows(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        source_id = str(row.get("source_id") or "")
        severity = str(row.get("severity") or "info")
        targets = _normalize_targets(row.get("target_modules"))
        normalized.append(
            {
                "evidence_id": str(row.get("evidence_id") or f"answer_quality_evidence_{index}"),
                "source_id": source_id,
                "severity": severity,
                "target_modules": targets,
                "issue_type": str(row.get("issue_type") or "answer_quality_observation"),
                "summary": str(row.get("summary") or ""),
                "accepted": source_id in _accepted_sources() and severity in {"review", "warning", "critical"},
                "review_only": True,
                "chart_fact_mutation_allowed": False,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "external_release_allowed": False,
            }
        )
    return normalized


def _queue_items(evidence_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for row in evidence_rows:
        if row.get("accepted") is not True:
            continue
        items.append(
            {
                "queue_item_id": f"core_cal_s4.{row.get('evidence_id')}",
                "evidence_id": row.get("evidence_id"),
                "source_id": row.get("source_id"),
                "target_modules": row.get("target_modules"),
                "issue_type": row.get("issue_type"),
                "summary": row.get("summary"),
                "review_only": True,
                "chart_fact_mutation_allowed": False,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "external_release_allowed": False,
            }
        )
    return sorted(items, key=lambda item: str(item["queue_item_id"]))


def _steady_state_cadence() -> dict[str, Any]:
    return {
        "version": "v30.core_answer_calibration_steady_state_cadence.v1",
        "routine_targeted_commands": [
            "python3 scripts/run_synthetic_typical_bazi_answer_calibration.py",
            "python3 scripts/run_synthetic_validation.py --tier synthetic_typical_bazi_answer",
            "python3 scripts/run_synthetic_typical_answer_training_signal_review.py",
            "python3 scripts/run_synthetic_typical_answer_calibration_closeout.py",
            "python3 scripts/run_core_answer_calibration_steady_state_queue.py",
        ],
        "evidence_entrypoints": sorted(_accepted_sources()),
        "major_node_commands_explicit_only": [
            "pytest -q",
            "python3 scripts/run_synthetic_validation.py --tier all",
            "python3 scripts/run_518k_validation.py --mode full --confirm-full",
            "python3 scripts/run_llm_live_smoke.py --json",
        ],
        "module_reopen_policy": "answer_quality_evidence_only",
        "boundary": "s4_runs_targeted_answer_calibration_and_defers_heavy_gates_to_explicit_major_nodes",
    }


def _checks(
    *,
    closeout_summary: Mapping[str, Any],
    evidence_rows: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
    cadence: Mapping[str, Any],
) -> list[dict[str, Any]]:
    accepted_source_ids = set(_accepted_sources())
    accepted_rows = [row for row in evidence_rows if row.get("accepted") is True]
    queue_readonly = all(_readonly(row) for row in queue_items)
    evidence_readonly = all(_readonly(row) for row in evidence_rows)
    targets_allowed = all(set(_str_list(row.get("target_modules"))) <= {"M3", "M6", "LLM", "interaction"} for row in evidence_rows + queue_items)
    return [
        {
            "check_id": "core_cal_s3_typical_answer_closeout_ready",
            "passed": closeout_summary.get("version") == SYNTHETIC_TYPICAL_ANSWER_CALIBRATION_CLOSEOUT_VERSION
            and closeout_summary.get("closed") is True
            and int(closeout_summary.get("training_signal_count", 0) or 0) >= 5
            and int(closeout_summary.get("queued_item_count", 0) or 0) == 0,
            "observed": closeout_summary,
        },
        {
            "check_id": "answer_quality_evidence_sources_registered",
            "passed": accepted_source_ids <= set(_str_list(cadence.get("evidence_entrypoints"))),
            "observed": {"required_sources": sorted(accepted_source_ids), "registered_sources": cadence.get("evidence_entrypoints")},
        },
        {
            "check_id": "answer_quality_queue_matches_accepted_evidence",
            "passed": len(queue_items) == len(accepted_rows),
            "observed": {"accepted_evidence_count": len(accepted_rows), "queue_item_count": len(queue_items)},
        },
        {
            "check_id": "routine_targeted_cadence_defined",
            "passed": cadence.get("version") == "v30.core_answer_calibration_steady_state_cadence.v1"
            and len(_str_list(cadence.get("routine_targeted_commands"))) >= 5
            and len(_str_list(cadence.get("major_node_commands_explicit_only"))) >= 4
            and cadence.get("module_reopen_policy") == "answer_quality_evidence_only",
            "observed": cadence,
        },
        {
            "check_id": "targets_limited_to_answer_calibration_modules",
            "passed": targets_allowed,
            "observed": {"allowed_targets": ["M3", "M6", "LLM", "interaction"]},
        },
        {
            "check_id": "evidence_and_queue_are_review_only",
            "passed": evidence_readonly and queue_readonly,
            "observed": {"evidence_readonly": evidence_readonly, "queue_readonly": queue_readonly},
        },
        {
            "check_id": "no_default_reopen_or_heavy_gate",
            "passed": closeout_summary.get("full_pytest_required") is False
            and closeout_summary.get("synthetic_all_required") is False
            and closeout_summary.get("full_518k_required") is False
            and closeout_summary.get("live_llm_required") is False,
            "observed": {
                "full_pytest_required": closeout_summary.get("full_pytest_required"),
                "synthetic_all_required": closeout_summary.get("synthetic_all_required"),
                "full_518k_required": closeout_summary.get("full_518k_required"),
                "live_llm_required": closeout_summary.get("live_llm_required"),
            },
        },
        {
            "check_id": "no_mutation_or_promotion_boundary",
            "passed": closeout_summary.get("chart_fact_mutation_allowed") is False
            and closeout_summary.get("auto_apply_training_allowed") is False
            and closeout_summary.get("policy_pointer_promotion_allowed") is False
            and closeout_summary.get("external_release_allowed") is False,
            "observed": {
                "chart_fact_mutation_allowed": False,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "external_release_allowed": False,
            },
        },
    ]


def _decision(*, checks: list[Mapping[str, Any]], queue_items: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    candidate_count = len(queue_items)
    return {
        "core_answer_calibration_steady_state_queue_ready": ready,
        "decision_status": "core_cal_s4_answer_calibration_steady_state_queue_ready"
        if ready
        else "core_cal_s4_answer_calibration_steady_state_queue_blocked",
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("passed") is True),
        "failed_check_ids": failed,
        "waiting_for_new_answer_quality_evidence": ready and candidate_count == 0,
        "focused_answer_fix_candidate_count": candidate_count,
        "focused_answer_fix_required": ready and candidate_count > 0,
        "core_module_reopen_by_default": False,
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "live_llm_required": False,
        "external_release_allowed": False,
        "chart_fact_mutation_allowed": False,
        "auto_apply_training_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "blockers": ["core_cal_s4_checks_failed"] if failed else [],
        "rationale": (
            "Answer calibration is in steady-state wait mode; reopen only from focused answer-quality evidence."
            if ready
            else "CORE-CAL-S4 is blocked until failed closeout or queue checks are repaired."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("core_answer_calibration_steady_state_queue_ready") is True:
        if int(decision.get("focused_answer_fix_candidate_count", 0) or 0) > 0:
            return {
                "task_id": "CORE-CAL-S4-FIX",
                "title": "Focused Answer Calibration Fix Plan",
                "selected_track": "core_answer_calibration",
                "scope": [
                    "review queued answer-quality evidence",
                    "change only targeted M3/M6/LLM/interaction logic",
                    "rerun S1-S4 targeted gates after the focused fix",
                ],
            }
        return {
            "task_id": "CORE-CAL-WAIT",
            "title": "Await Focused Answer Quality Evidence Or Explicit Major Validation",
            "selected_track": "core_answer_calibration",
            "scope": [
                "serve current Bazi answer system",
                "collect concrete answer-quality evidence through registered intake sources",
                "run targeted routine gates only",
                "run full pytest/synthetic-all/full-518K only at explicit major nodes",
            ],
        }
    return {
        "task_id": "CORE-CAL-S4-FR",
        "title": "Core Answer Calibration Steady-State Queue Failure Review",
        "selected_track": "core_answer_calibration",
        "scope": [
            "repair failed S4 checks",
            "do not reopen answer modules while blocked",
        ],
    }


def _accepted_sources() -> set[str]:
    return {
        "answer_quality_delta_review",
        "synthetic_typical_bazi_answer",
        "runtime_answer_integration",
        "business_answer_refresh",
        "llm_output_acceptance",
        "user_feedback_answer_quality",
    }


def _normalize_targets(value: object) -> list[str]:
    targets = set(_str_list(value))
    normalized: set[str] = set()
    for target in targets:
        if target in {"M3", "M6", "LLM", "interaction"}:
            normalized.add(target)
        elif target.startswith("M3"):
            normalized.add("M3")
        elif target.startswith("M6"):
            normalized.add("M6")
        elif "llm" in target.lower():
            normalized.add("LLM")
        elif "question" in target.lower() or "interaction" in target.lower():
            normalized.add("interaction")
    return sorted(normalized or {"M6"})


def _readonly(row: Mapping[str, Any]) -> bool:
    return (
        row.get("review_only") is True
        and row.get("chart_fact_mutation_allowed") is False
        and row.get("auto_apply_training_allowed") is False
        and row.get("policy_pointer_promotion_allowed") is False
        and row.get("external_release_allowed") is False
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _str_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(row) for row in value if str(row)]
    return []


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['queue_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
