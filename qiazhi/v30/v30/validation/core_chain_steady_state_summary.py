from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.validation.customer_surface_bazi_context_reconciliation import (
    run_customer_surface_bazi_context_reconciliation,
)
from v30.validation.training_synthetic_support_review import run_training_synthetic_support_review


CORE_CHAIN_STEADY_STATE_SUMMARY_VERSION = "v30.core_chain_steady_state_summary.v1"


def run_core_chain_steady_state_summary(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    training_support = run_training_synthetic_support_review(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    mcr2 = run_customer_surface_bazi_context_reconciliation(
        reading_id="core-chain-steady-state-summary-mcr2",
    )
    return build_core_chain_steady_state_summary(
        training_support=training_support,
        mcr2_reconciliation=mcr2,
        artifact_dir=artifact_dir,
    )


def build_core_chain_steady_state_summary(
    *,
    training_support: Mapping[str, Any],
    mcr2_reconciliation: Mapping[str, Any],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    summarized_at = datetime.now(timezone.utc)
    summary_id = f"v30.core_chain.s1.{summarized_at.strftime('%Y%m%d%H%M%S%f')}"
    training_summary = _training_support_summary(training_support)
    mcr2_summary = _mcr2_summary(mcr2_reconciliation)
    module_matrix = _module_matrix(training_summary, mcr2_summary)
    cadence = _validation_cadence(training_summary)
    checks = _checks(
        training_summary=training_summary,
        mcr2_summary=mcr2_summary,
        module_matrix=module_matrix,
        cadence=cadence,
    )
    decision = _decision(checks, module_matrix)
    payload: dict[str, Any] = {
        "version": CORE_CHAIN_STEADY_STATE_SUMMARY_VERSION,
        "summary_id": summary_id,
        "summarized_at": summarized_at.isoformat(),
        "status": "completed" if decision["core_chain_steady_state_ready"] else "blocked",
        "decision": decision,
        "training_support_summary": training_summary,
        "mcr2_reconciliation_summary": mcr2_summary,
        "module_completion_matrix": module_matrix,
        "validation_cadence": cadence,
        "checks": checks,
        "policy_boundary": {
            "core_modules_reopened": False,
            "runtime_decision_write_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "live_llm_required": False,
            "synthetic_all_required": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "boundary": "core_chain_summary_records_steady_state_without_reopening_or_mutating_core_modules",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "core_chain_steady_state_summary_selects_evidence_driven_next_work",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _training_support_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "training_synthetic_support_ready": bool(decision.get("training_synthetic_support_ready")),
        "training_pipeline_case_count": int(decision.get("training_pipeline_case_count", 0) or 0),
        "training_signal_count": int(decision.get("training_signal_count", 0) or 0),
        "sample_518k_case_count": int(decision.get("sample_518k_case_count", 0) or 0),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "synthetic_all_required": bool(decision.get("synthetic_all_required")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
    }


def _mcr2_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    rows = [_mapping(row) for row in _list(payload.get("module_completion_matrix"))]
    completion_by_id = {
        str(row.get("module_id")): int(row.get("completion", 0) or 0)
        for row in rows
        if row.get("module_id")
    }
    status_by_id = {
        str(row.get("module_id")): str(row.get("status") or "")
        for row in rows
        if row.get("module_id")
    }
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "customer_surface_bazi_context_reconciled": bool(decision.get("customer_surface_bazi_context_reconciled")),
        "passed_count": int(decision.get("passed_count", 0) or 0),
        "check_count": int(decision.get("check_count", 0) or 0),
        "completion_by_id": completion_by_id,
        "status_by_id": status_by_id,
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "policy_pointer_write_allowed": bool(decision.get("policy_pointer_write_allowed")),
        "live_llm_required": bool(decision.get("live_llm_required")),
        "synthetic_all_required": bool(decision.get("synthetic_all_required")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
    }


def _module_matrix(
    training_summary: Mapping[str, Any],
    mcr2_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    completion = _mapping(mcr2_summary.get("completion_by_id"))
    status = _mapping(mcr2_summary.get("status_by_id"))
    base = [
        ("M1/M2", "BirthInput and deterministic chart facts"),
        ("M3", "Knowledge, rule, portrait, feature, and structure spine"),
        ("M4", "Ten-god energy model and model-signal summary"),
        ("M5", "Strength, structure, and useful-god ranked decisions"),
        ("M6", "Practical Bazi reading output"),
        ("M7", "Real-case calibration pack and drift routing"),
        ("M8", "Customer reading projection and API contract"),
        ("SURFACE", "Customer reading surface accounting"),
        ("CTX", "BaziContext internalization accounting"),
        ("IQ", "Intelligent question interaction"),
        ("LLM", "Bazi LLM expression layer"),
        ("BT", "Central brain, training, synthetic, and 518K support"),
        ("U", "Multi-user, terminal, session, and locale projection"),
    ]
    rows = [
        {
            "module_id": module_id,
            "name": name,
            "completion": int(completion.get(module_id, 0) or 0),
            "status": str(status.get(module_id) or ""),
            "steady": str(status.get(module_id) or "") in {"steady", "bounded_steady"},
            "reopen_by_default": False,
        }
        for module_id, name in base
    ]
    for row in rows:
        if row["module_id"] == "BT":
            row["training_pipeline_case_count"] = int(training_summary.get("training_pipeline_case_count", 0) or 0)
            row["training_signal_count"] = int(training_summary.get("training_signal_count", 0) or 0)
            row["sample_518k_case_count"] = int(training_summary.get("sample_518k_case_count", 0) or 0)
    return rows


def _validation_cadence(training_summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "routine_commands": [
            "python3 scripts/run_core_chain_steady_state_summary.py --sample-limit 8",
            "python3 scripts/run_training_synthetic_support_review.py --sample-limit 8",
            "python3 scripts/run_synthetic_validation.py --tier training_pipeline",
            "python3 scripts/run_518k_validation.py --mode sample --limit 8",
        ],
        "targeted_route_smoke": "pytest -q tests/test_v30_scaffold.py::test_api_routes_are_v30_only",
        "major_node_commands": [
            "python3 scripts/run_synthetic_validation.py --tier all",
            "pytest -q",
            "python3 scripts/run_llm_live_smoke.py --json",
            "python3 scripts/run_518k_validation.py --mode full --confirm-full",
        ],
        "routine_training_pipeline_case_count": int(training_summary.get("training_pipeline_case_count", 0) or 0),
        "routine_518k_sample_case_count": int(training_summary.get("sample_518k_case_count", 0) or 0),
        "synthetic_all_required_by_default": False,
        "full_pytest_required_by_default": False,
        "live_llm_required_by_default": False,
        "full_518k_required_by_default": False,
        "policy_pointer_promotion_allowed_by_default": False,
        "boundary": "routine_cadence_uses_targeted_gates_major_node_commands_are_explicit_only",
    }


def _checks(
    *,
    training_summary: Mapping[str, Any],
    mcr2_summary: Mapping[str, Any],
    module_matrix: list[Mapping[str, Any]],
    cadence: Mapping[str, Any],
) -> list[dict[str, Any]]:
    completion = {
        str(row.get("module_id")): int(row.get("completion", 0) or 0)
        for row in module_matrix
    }
    required_100 = {"M1/M2", "M3", "M4", "M5", "M6", "M7", "M8", "SURFACE", "CTX", "BT", "U"}
    return [
        {
            "check_id": "bt_s1_training_support_ready",
            "passed": (
                training_summary["version"] == "v30.training_synthetic_support_review.v1"
                and training_summary["training_synthetic_support_ready"]
                and training_summary["training_pipeline_case_count"] >= 90
                and training_summary["training_signal_count"] >= 30
                and training_summary["sample_518k_case_count"] >= 8
            ),
            "expected": "BT-S1 training/synthetic support is ready",
        },
        {
            "check_id": "mcr2_surface_context_reconciled",
            "passed": (
                mcr2_summary["version"] == "v30.customer_surface_bazi_context_reconciliation.v1"
                and mcr2_summary["customer_surface_bazi_context_reconciled"]
                and mcr2_summary["passed_count"] == mcr2_summary["check_count"]
            ),
            "expected": "customer surface and BaziContext accounting are reconciled",
        },
        {
            "check_id": "core_module_matrix_steady",
            "passed": (
                all(completion.get(module_id) == 100 for module_id in required_100)
                and completion.get("IQ", 0) >= 98
                and completion.get("LLM", 0) >= 88
                and all(row.get("reopen_by_default") is False for row in module_matrix)
            ),
            "expected": "M1-M8, surface/context, BT, and U are 100%; IQ/LLM are bounded steady",
        },
        {
            "check_id": "no_write_or_fact_mutation_boundary",
            "passed": (
                not training_summary["policy_pointer_promotion_allowed"]
                and not training_summary["chart_fact_mutation_allowed"]
                and not mcr2_summary["policy_pointer_write_allowed"]
                and not mcr2_summary["chart_fact_mutation_allowed"]
            ),
            "expected": "summary is read-only and cannot mutate deterministic Bazi facts",
        },
        {
            "check_id": "routine_and_major_node_cadence_separated",
            "passed": (
                cadence["routine_training_pipeline_case_count"] >= 90
                and cadence["routine_518k_sample_case_count"] >= 8
                and not cadence["synthetic_all_required_by_default"]
                and not cadence["full_pytest_required_by_default"]
                and not cadence["live_llm_required_by_default"]
                and not cadence["full_518k_required_by_default"]
                and not cadence["policy_pointer_promotion_allowed_by_default"]
            ),
            "expected": "routine validation is targeted and major gates remain explicit",
        },
    ]


def _decision(checks: list[Mapping[str, Any]], module_matrix: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "decision_status": "core_chain_steady_state_ready" if ready else "core_chain_steady_state_blocked",
        "core_chain_steady_state_ready": ready,
        "module_count": len(module_matrix),
        "steady_module_count": sum(1 for row in module_matrix if row.get("steady") is True),
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("passed") is True),
        "failed_check_ids": failed,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "synthetic_all_required": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "live_llm_required": False,
        "blockers": ["core_chain_summary_checks_failed"] if failed else [],
        "rationale": (
            "Core chain is steady; future work should be selected only from new evidence, calibration gaps, or explicit major gates."
            if ready
            else "Core chain summary is blocked until failed steady-state checks pass."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["core_chain_steady_state_ready"]:
        return {
            "next_task": "Evidence-Driven Calibration Queue",
            "reason": "The core chain is steady; next work should wait for or review concrete calibration/business evidence instead of reopening modules broadly.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "Core Chain Steady-State Remediation",
        "reason": "Repair failed steady-state summary checks before selecting new work.",
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['summary_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
