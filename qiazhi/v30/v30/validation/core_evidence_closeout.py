from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.validation.answer_quality_delta_review import run_answer_quality_delta_review
from v30.validation.llm_answer_output_delta_review import run_llm_answer_output_delta_review
from v30.validation.llm_prompt_context_delta_review import run_llm_prompt_context_delta_review
from v30.validation.runtime_answer_integration_delta_review import run_runtime_answer_integration_delta_review


CORE_EVIDENCE_CLOSEOUT_VERSION = "v30.core_evidence_closeout.v1"


def run_core_evidence_closeout(*, reading_id: str = "core-evidence-6-closeout") -> dict[str, Any]:
    evidence = {
        "CORE-EVIDENCE-2": run_answer_quality_delta_review(reading_id=f"{reading_id}-answer-quality"),
        "CORE-EVIDENCE-3": run_llm_prompt_context_delta_review(reading_id=f"{reading_id}-llm-context"),
        "CORE-EVIDENCE-4": run_llm_answer_output_delta_review(reading_id=f"{reading_id}-llm-output"),
        "CORE-EVIDENCE-5": run_runtime_answer_integration_delta_review(reading_id=f"{reading_id}-runtime-integration"),
    }
    return build_core_evidence_closeout(evidence=evidence, reading_id=reading_id)


def build_core_evidence_closeout(
    *,
    evidence: Mapping[str, Mapping[str, Any]],
    reading_id: str = "core-evidence-6-closeout",
) -> dict[str, Any]:
    rows = [_evidence_row(task_id, payload) for task_id, payload in evidence.items()]
    summary = _summary(rows)
    decision = _decision(summary, rows)
    return {
        "version": CORE_EVIDENCE_CLOSEOUT_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["core_evidence_closeout_ready"] else "blocked",
        "reading_id": reading_id,
        "decision": decision,
        "closeout_summary": summary,
        "evidence_rows": rows,
        "core_scope": {
            "task_id": "CORE-EVIDENCE-6",
            "title": "Core Evidence Closeout And Documentation Sync",
            "covered_chain": [
                "CORE-EVIDENCE-1_module_product_rebaseline",
                "CORE-EVIDENCE-2_answer_quality_delta",
                "CORE-EVIDENCE-3_llm_prompt_context_delta",
                "CORE-EVIDENCE-4_llm_answer_output_delta",
                "CORE-EVIDENCE-5_runtime_answer_integration_delta",
            ],
            "acceptance_target": (
                "Core Bazi answer evidence chain is recorded, targeted gates are green, "
                "and the next task remains core calibration rather than peripheral UI/admin expansion"
            ),
        },
        "policy_boundary": {
            "full_pytest_run_by_default": False,
            "synthetic_all_run_by_default": False,
            "live_llm_execution_performed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "boundary": "core_evidence_closeout_is_documentation_and_targeted_gate_only",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "core_evidence_chain_closed_for_current_runtime_answer_product_scope",
    }


def _evidence_row(task_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    ready_keys = [
        "answer_quality_delta_ready",
        "llm_prompt_context_delta_ready",
        "llm_answer_output_delta_ready",
        "runtime_answer_integration_ready",
    ]
    ready_flags = {key: decision.get(key) for key in ready_keys if key in decision}
    ready = bool(ready_flags) and all(value is True for value in ready_flags.values())
    return {
        "task_id": task_id,
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "ready": ready,
        "decision_status": str(decision.get("decision_status") or ""),
        "ready_flags": ready_flags,
        "passed_check_count": int(decision.get("passed_check_count", 0) or 0),
        "check_count": int(decision.get("check_count", 0) or 0),
        "failed_check_ids": list(decision.get("failed_check_ids", [])) if isinstance(decision.get("failed_check_ids"), list) else [],
        "full_pytest_required": decision.get("full_pytest_required") is True,
        "live_llm_execution_performed": decision.get("live_llm_execution_performed") is True
        or decision.get("llm_execution_performed") is True,
    }


def _summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    required = {"CORE-EVIDENCE-2", "CORE-EVIDENCE-3", "CORE-EVIDENCE-4", "CORE-EVIDENCE-5"}
    observed = {str(row.get("task_id") or "") for row in rows}
    ready_rows = [row for row in rows if row.get("ready") is True]
    return {
        "required_task_ids": sorted(required),
        "observed_task_ids": sorted(observed),
        "missing_task_ids": sorted(required - observed),
        "row_count": len(rows),
        "ready_row_count": len(ready_rows),
        "failed_row_count": len(rows) - len(ready_rows),
        "total_passed_checks": sum(int(row.get("passed_check_count", 0) or 0) for row in rows),
        "total_checks": sum(int(row.get("check_count", 0) or 0) for row in rows),
        "full_pytest_required_count": sum(1 for row in rows if row.get("full_pytest_required") is True),
        "live_llm_execution_count": sum(1 for row in rows if row.get("live_llm_execution_performed") is True),
    }


def _decision(summary: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    failed_rows = [row for row in rows if row.get("ready") is not True]
    if summary.get("missing_task_ids"):
        blockers.append("core_evidence_task_coverage_incomplete")
    if failed_rows:
        blockers.append("core_evidence_rows_failed")
    if int(summary.get("full_pytest_required_count", 0) or 0):
        blockers.append("unexpected_full_pytest_requirement")
    if int(summary.get("live_llm_execution_count", 0) or 0):
        blockers.append("unexpected_live_llm_execution")
    ready = not blockers
    return {
        "core_evidence_closeout_ready": ready,
        "decision_status": "core_evidence_6_closeout_ready" if ready else "core_evidence_6_closeout_blocked",
        "check_count": int(summary.get("total_checks", 0) or 0),
        "passed_check_count": int(summary.get("total_passed_checks", 0) or 0),
        "failed_check_ids": sorted(
            {
                str(check_id)
                for row in rows
                for check_id in row.get("failed_check_ids", [])
                if check_id
            }
        ),
        "failed_task_ids": [str(row.get("task_id") or "") for row in failed_rows],
        "blockers": blockers,
        "full_pytest_required": False,
        "live_llm_required": False,
        "next_action": "start_synthetic_answer_calibration_pack" if ready else "repair_core_evidence_chain",
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("core_evidence_closeout_ready") is True:
        return {
            "task_id": "CORE-CAL-S1",
            "title": "Synthetic Typical Bazi Answer Calibration Pack",
            "rationale": (
                "The runtime answer evidence chain is closed; next core work should calibrate answer quality "
                "against synthetic representative Bazi patterns instead of reopening UI or generic module build-out."
            ),
            "full_pytest_required_before_start": False,
        }
    return {
        "task_id": "CORE-EVIDENCE-6A",
        "title": "Core Evidence Closeout Repair",
        "rationale": "One or more CORE-EVIDENCE gates failed or requested a major-node action.",
        "full_pytest_required_before_start": False,
    }


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
