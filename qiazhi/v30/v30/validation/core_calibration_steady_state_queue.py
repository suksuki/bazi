from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from v30.validation.await_new_calibration_evidence_status import run_await_new_calibration_evidence_status
from v30.validation.synthetic_archetype_calibration_closeout import (
    SYNTHETIC_ARCHETYPE_CALIBRATION_CLOSEOUT_VERSION,
    run_synthetic_archetype_calibration_closeout,
)


CORE_CALIBRATION_STEADY_STATE_QUEUE_VERSION = "v30.core_calibration_steady_state_queue.v1"


def run_core_calibration_steady_state_queue(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    synthetic_archetype_closeout = run_synthetic_archetype_calibration_closeout()
    await_status = run_await_new_calibration_evidence_status(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    return build_core_calibration_steady_state_queue(
        synthetic_archetype_closeout=synthetic_archetype_closeout,
        await_new_evidence_status=await_status,
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )


def build_core_calibration_steady_state_queue(
    *,
    synthetic_archetype_closeout: Mapping[str, Any],
    await_new_evidence_status: Mapping[str, Any],
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    recorded_at = datetime.now(timezone.utc)
    queue_id = f"v30.core_calibration.s0.{recorded_at.strftime('%Y%m%d%H%M%S%f')}"
    archetype_summary = _archetype_closeout_summary(synthetic_archetype_closeout)
    await_summary = _await_status_summary(await_new_evidence_status)
    cadence = _steady_state_cadence(sample_limit=sample_limit)
    checks = _checks(
        archetype_summary=archetype_summary,
        await_summary=await_summary,
        cadence=cadence,
    )
    decision = _decision(checks=checks, await_summary=await_summary)
    payload: dict[str, Any] = {
        "version": CORE_CALIBRATION_STEADY_STATE_QUEUE_VERSION,
        "queue_id": queue_id,
        "recorded_at": recorded_at.isoformat(),
        "status": "completed" if decision["core_calibration_steady_state_queue_ready"] else "blocked",
        "task": {
            "task_id": "CORE-CAL-S0",
            "title": "Core Calibration Steady-State Queue",
            "scope": "keep_core_bazi_modules_steady_and_reopen_only_from_focused_evidence",
        },
        "synthetic_archetype_closeout_summary": archetype_summary,
        "await_new_evidence_summary": await_summary,
        "steady_state_cadence": cadence,
        "checks": checks,
        "decision": decision,
        "queue_policy": {
            "current_mode": "steady_state_wait",
            "accepted_next_inputs": await_summary["accepted_evidence_source_ids"],
            "focused_fix_candidate_entrypoint": "Focused Calibration Fix Plan",
            "core_module_reopen_by_default": False,
            "reopen_all_core_modules_allowed": False,
            "runtime_decision_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "boundary": "core_calibration_s0_accepts_concrete_evidence_without_default_module_reopen",
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
        "boundary": "core_calibration_s0_is_a_steady_queue_not_a_new_core_module_buildout",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _archetype_closeout_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    cadence = _mapping(payload.get("routine_cadence"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "closed": bool(decision.get("synthetic_archetype_calibration_closed")),
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


def _await_status_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    wait_policy = _mapping(payload.get("wait_policy"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "await_new_evidence_ready": bool(decision.get("await_new_evidence_ready")),
        "waiting_for_new_calibration_evidence": bool(decision.get("waiting_for_new_calibration_evidence")),
        "focused_fix_candidate_count": int(decision.get("focused_fix_candidate_count", 0) or 0),
        "focused_module_fix_required": bool(decision.get("focused_module_fix_required")),
        "accepted_evidence_source_ids": _str_list(wait_policy.get("accepted_evidence_sources")),
        "core_module_reopen_by_default": bool(decision.get("core_module_reopen_by_default")),
        "external_release_allowed": False,
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "auto_apply_training_allowed": False,
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "synthetic_all_required": bool(decision.get("synthetic_all_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "live_llm_required": bool(decision.get("live_llm_required")),
    }


def _steady_state_cadence(*, sample_limit: int) -> dict[str, Any]:
    return {
        "version": "v30.core_calibration_steady_state_cadence.v1",
        "routine_targeted_commands": [
            "python3 scripts/run_synthetic_validation.py --tier synthetic_archetype_rule_claim",
            "python3 scripts/run_synthetic_archetype_training_signal_review.py",
            "python3 scripts/run_synthetic_archetype_calibration_closeout.py",
            f"python3 scripts/run_await_new_calibration_evidence_status.py --sample-limit {sample_limit}",
            f"python3 scripts/run_core_calibration_steady_state_queue.py --sample-limit {sample_limit}",
        ],
        "evidence_entrypoints": [
            "real_case_calibration",
            "business_acceptance",
            "518k_distribution",
            "training_signal_distribution",
            "llm_expression_acceptance",
            "question_chain_acceptance",
        ],
        "major_node_commands_explicit_only": [
            "pytest -q",
            "python3 scripts/run_synthetic_validation.py --tier all",
            "python3 scripts/run_518k_validation.py --mode full --confirm-full",
            "python3 scripts/run_llm_live_smoke.py --json",
        ],
        "core_module_reopen_policy": "focused_evidence_only",
        "boundary": "s0_runs_targeted_cadence_and_defers_heavy_gates_to_explicit_major_nodes",
    }


def _checks(
    *,
    archetype_summary: Mapping[str, Any],
    await_summary: Mapping[str, Any],
    cadence: Mapping[str, Any],
) -> list[dict[str, Any]]:
    required_sources = {
        "real_case_calibration",
        "business_acceptance",
        "518k_distribution",
        "training_signal_distribution",
        "llm_expression_acceptance",
        "question_chain_acceptance",
    }
    return [
        {
            "check_id": "syn_cal4_archetype_closeout_ready",
            "passed": archetype_summary.get("version") == SYNTHETIC_ARCHETYPE_CALIBRATION_CLOSEOUT_VERSION
            and archetype_summary.get("closed") is True
            and int(archetype_summary.get("training_signal_count", 0) or 0) >= 4
            and int(archetype_summary.get("queued_item_count", 0) or 0) == 0,
            "observed": archetype_summary,
        },
        {
            "check_id": "await_new_evidence_state_ready",
            "passed": await_summary.get("version") == "v30.await_new_calibration_evidence_status.v1"
            and await_summary.get("await_new_evidence_ready") is True
            and await_summary.get("waiting_for_new_calibration_evidence") is True
            and int(await_summary.get("focused_fix_candidate_count", 0) or 0) == 0,
            "observed": await_summary,
        },
        {
            "check_id": "accepted_evidence_sources_registered",
            "passed": required_sources <= set(_str_list(await_summary.get("accepted_evidence_source_ids"))),
            "observed": {
                "required_sources": sorted(required_sources),
                "accepted_sources": _str_list(await_summary.get("accepted_evidence_source_ids")),
            },
        },
        {
            "check_id": "routine_targeted_cadence_defined",
            "passed": cadence.get("version") == "v30.core_calibration_steady_state_cadence.v1"
            and len(_str_list(cadence.get("routine_targeted_commands"))) >= 5
            and len(_str_list(cadence.get("major_node_commands_explicit_only"))) >= 4
            and cadence.get("core_module_reopen_policy") == "focused_evidence_only",
            "observed": cadence,
        },
        {
            "check_id": "no_default_reopen_or_heavy_gate",
            "passed": await_summary.get("core_module_reopen_by_default") is False
            and await_summary.get("full_pytest_required") is False
            and await_summary.get("synthetic_all_required") is False
            and await_summary.get("full_518k_required") is False
            and await_summary.get("live_llm_required") is False
            and archetype_summary.get("full_pytest_required") is False
            and archetype_summary.get("synthetic_all_required") is False
            and archetype_summary.get("full_518k_required") is False
            and archetype_summary.get("live_llm_required") is False,
            "observed": {
                "core_module_reopen_by_default": await_summary.get("core_module_reopen_by_default"),
                "full_pytest_required": await_summary.get("full_pytest_required"),
                "synthetic_all_required": await_summary.get("synthetic_all_required"),
                "full_518k_required": await_summary.get("full_518k_required"),
                "live_llm_required": await_summary.get("live_llm_required"),
            },
        },
        {
            "check_id": "no_mutation_or_promotion_boundary",
            "passed": await_summary.get("chart_fact_mutation_allowed") is False
            and await_summary.get("auto_apply_training_allowed") is False
            and await_summary.get("policy_pointer_promotion_allowed") is False
            and archetype_summary.get("chart_fact_mutation_allowed") is False
            and archetype_summary.get("auto_apply_training_allowed") is False
            and archetype_summary.get("policy_pointer_promotion_allowed") is False
            and archetype_summary.get("external_release_allowed") is False,
            "observed": {
                "chart_fact_mutation_allowed": False,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "external_release_allowed": False,
            },
        },
    ]


def _decision(*, checks: list[Mapping[str, Any]], await_summary: Mapping[str, Any]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    candidate_count = int(await_summary.get("focused_fix_candidate_count", 0) or 0)
    return {
        "core_calibration_steady_state_queue_ready": ready,
        "decision_status": "core_calibration_s0_steady_state_queue_ready" if ready else "core_calibration_s0_steady_state_queue_blocked",
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("passed") is True),
        "failed_check_ids": failed,
        "waiting_for_new_calibration_evidence": ready and candidate_count == 0,
        "focused_fix_candidate_count": candidate_count,
        "focused_module_fix_required": ready and candidate_count > 0,
        "core_module_reopen_by_default": False,
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "live_llm_required": False,
        "external_release_allowed": False,
        "chart_fact_mutation_allowed": False,
        "auto_apply_training_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "blockers": ["core_calibration_s0_checks_failed"] if failed else [],
        "rationale": (
            "Core calibration is in steady-state wait mode; reopen only from focused concrete evidence."
            if ready
            else "CORE-CAL-S0 is blocked until the failed upstream closeout or await-state checks are repaired."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("core_calibration_steady_state_queue_ready") is True:
        return {
            "task_id": "CORE-CAL-WAIT",
            "title": "Await Focused Calibration Evidence Or Explicit Major Validation",
            "selected_track": "core_bazi_calibration",
            "scope": [
                "serve current Bazi system",
                "collect concrete evidence through registered intake sources",
                "run targeted routine gates only",
                "run full pytest/synthetic-all/full-518K only at explicit major nodes",
            ],
        }
    return {
        "task_id": "CORE-CAL-S0-FR",
        "title": "Core Calibration Steady-State Queue Failure Review",
        "selected_track": "core_bazi_calibration",
        "scope": [
            "repair failed S0 checks",
            "do not reopen all core modules while blocked",
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
    path = artifact_dir / f"{payload['queue_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
