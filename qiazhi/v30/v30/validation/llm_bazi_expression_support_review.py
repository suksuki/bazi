from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.validation.bazi_llm_closeout import run_bazi_llm_closeout
from v30.validation.iq_intelligent_question_support_review import run_iq_intelligent_question_support_review
from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.training_signals import extract_training_signals


LLM_BAZI_EXPRESSION_SUPPORT_REVIEW_VERSION = "v30.llm_bazi_expression_support_review.v1"


def run_llm_bazi_expression_support_review(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    iq_support = run_iq_intelligent_question_support_review(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    llm_closeout = run_bazi_llm_closeout(reading_id="llm-support-review")
    bazi_llm_acceptance = run_synthetic_tier("bazi_llm_acceptance")
    acceptance_payload = bazi_llm_acceptance.model_dump(mode="json")
    acceptance_payload["training_signals"] = [
        signal.model_dump(mode="json") for signal in extract_training_signals(bazi_llm_acceptance)
    ]
    return build_llm_bazi_expression_support_review(
        iq_support=iq_support,
        llm_closeout=llm_closeout,
        bazi_llm_acceptance=acceptance_payload,
        artifact_dir=artifact_dir,
    )


def build_llm_bazi_expression_support_review(
    *,
    iq_support: Mapping[str, Any],
    llm_closeout: Mapping[str, Any],
    bazi_llm_acceptance: Mapping[str, Any],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    review_id = f"v30.llm.s1.{reviewed_at.strftime('%Y%m%d%H%M%S%f')}"
    iq_summary = _iq_summary(iq_support)
    llm_summary = _llm_summary(llm_closeout)
    acceptance_summary = _acceptance_summary(bazi_llm_acceptance)
    training_summary = _training_summary(bazi_llm_acceptance)
    checks = _checks(
        iq_summary=iq_summary,
        llm_summary=llm_summary,
        acceptance_summary=acceptance_summary,
        training_summary=training_summary,
    )
    decision = _decision(checks, llm_summary, acceptance_summary)
    payload: dict[str, Any] = {
        "version": LLM_BAZI_EXPRESSION_SUPPORT_REVIEW_VERSION,
        "review_id": review_id,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["llm_bazi_expression_support_ready"] else "blocked",
        "decision": decision,
        "iq_support_summary": iq_summary,
        "llm_closeout_summary": llm_summary,
        "bazi_llm_acceptance_summary": acceptance_summary,
        "training_signal_summary": training_summary,
        "checks": checks,
        "policy_boundary": {
            "llm_expression_layer": True,
            "bounded_bazi_context_required": True,
            "role_specific_prompt_required": True,
            "fallback_observability_required": True,
            "streaming_ui_observation_scope": "presentation_only",
            "live_provider_smoke_allowed": True,
            "live_provider_smoke_required_by_default": False,
            "runtime_decision_write_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "llm_chart_fact_generation_allowed": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "boundary": "llm_support_review_keeps_llm_as_role_aware_bazi_expression_layer",
        },
        "monitoring_baseline": _monitoring_baseline(acceptance_summary),
        "next_mainline_selection": _next_selection(decision),
        "boundary": "llm_bazi_expression_support_review_validates_bounded_llm_after_iq_support",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _iq_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "iq_support_review_ready": bool(decision.get("iq_support_review_ready")),
        "interaction_loop_case_count": int(decision.get("interaction_loop_case_count", 0) or 0),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "live_llm_required": bool(decision.get("live_llm_required")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
    }


def _llm_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    completion = _mapping(payload.get("completion_summary"))
    accepted = _mapping(payload.get("accepted_evidence"))
    steady = _mapping(payload.get("steady_state"))
    return {
        "version": str(payload.get("version") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "closeout_ready": bool(decision.get("closeout_ready")),
        "bazi_llm_steady_state": bool(decision.get("bazi_llm_steady_state")),
        "bazi_llm_mainline_completion": int(completion.get("bazi_llm_mainline_completion", 0) or 0),
        "context_compiler_completion": int(completion.get("bazi_llm_context_compiler_completion", 0) or 0),
        "prompt_registry_completion": int(completion.get("bazi_llm_prompt_registry_completion", 0) or 0),
        "answer_generator_completion": int(completion.get("bazi_llm_answer_generator_completion", 0) or 0),
        "output_acceptance_completion": int(completion.get("bazi_llm_output_acceptance_completion", 0) or 0),
        "training_synthetic_completion": int(completion.get("bazi_llm_training_synthetic_completion", 0) or 0),
        "role_locale_completion": int(completion.get("bazi_llm_role_locale_completion", 0) or 0),
        "accepted_evidence_keys": sorted(accepted.keys()),
        "accepted_evidence_ready_count": sum(1 for row in accepted.values() if _mapping(row).get("ready") is True),
        "accepted_evidence_count": len(accepted),
        "steady_boundary": str(steady.get("boundary") or ""),
        "optional_live_smoke_allowed": bool(decision.get("optional_live_smoke_allowed")),
        "live_llm_required": bool(decision.get("live_llm_required")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "policy_pointer_write_allowed": bool(decision.get("policy_pointer_write_allowed")),
        "core_bazi_modules_reopened": bool(decision.get("core_bazi_modules_reopened")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "synthetic_all_required": bool(decision.get("synthetic_all_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
    }


def _acceptance_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    quality_rows = [
        _mapping(_mapping(row).get("observed")).get("bazi_llm_output_acceptance_quality")
        for row in _list(payload.get("results"))
    ]
    quality_rows = [row for row in quality_rows if isinstance(row, Mapping)]
    return {
        "suite_id": str(payload.get("suite_id") or ""),
        "passed": bool(payload.get("passed")),
        "case_count": int(payload.get("case_count", 0) or 0),
        "passed_count": int(payload.get("passed_count", 0) or 0),
        "quality_row_count": len(quality_rows),
        "readiness_ready_count": sum(1 for row in quality_rows if row.get("readiness_ready") is True),
        "accepted_count_max": max([int(row.get("accepted_count", 0) or 0) for row in quality_rows] or [0]),
        "rejected_count_max": max([int(row.get("rejected_count", 0) or 0) for row in quality_rows] or [0]),
        "schema_rejected_count_max": max([int(row.get("schema_rejected_count", 0) or 0) for row in quality_rows] or [0]),
        "role_failure_count_max": max([int(row.get("role_failure_count", 0) or 0) for row in quality_rows] or [0]),
        "drift_rejected_count_max": max([int(row.get("drift_rejected_count", 0) or 0) for row in quality_rows] or [0]),
        "chart_fact_mutation_allowed_count": sum(
            1 for row in quality_rows if row.get("chart_fact_mutation_allowed") is True
        ),
        "live_llm_required_count": sum(1 for row in quality_rows if row.get("live_llm_required") is True),
        "boundary": "bazi_llm_acceptance_validates_output_quality_without_live_provider_or_fact_generation",
    }


def _training_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    signal = next(
        (
            _mapping(row) for row in _list(payload.get("training_signals"))
            if _mapping(row).get("signal_id") == "v30.training_signal.bazi_llm_output_acceptance_quality"
        ),
        {},
    )
    signal_payload = _mapping(signal.get("payload"))
    return {
        "bazi_llm_training_signal_present": bool(signal),
        "signal_id": str(signal.get("signal_id") or ""),
        "domain": str(signal.get("domain") or ""),
        "signal_type": str(signal.get("signal_type") or ""),
        "strength": float(signal.get("strength", 0.0) or 0.0),
        "accepted_count": int(signal_payload.get("accepted_count", 0) or 0),
        "rejected_count": int(signal_payload.get("rejected_count", 0) or 0),
        "schema_rejected_count": int(signal_payload.get("schema_rejected_count", 0) or 0),
        "role_failure_count": int(signal_payload.get("role_failure_count", 0) or 0),
        "drift_rejected_count": int(signal_payload.get("drift_rejected_count", 0) or 0),
        "can_tune_expression": bool(signal_payload.get("can_tune_expression")),
        "can_tune_question_strategy": bool(signal_payload.get("can_tune_question_strategy")),
        "can_tune_chart_facts": bool(signal_payload.get("can_tune_chart_facts")),
        "chart_fact_mutation_allowed_count": int(signal_payload.get("chart_fact_mutation_allowed_count", 0) or 0),
        "boundary": "bazi_llm_training_tunes_expression_and_question_strategy_not_chart_facts",
    }


def _checks(
    *,
    iq_summary: Mapping[str, Any],
    llm_summary: Mapping[str, Any],
    acceptance_summary: Mapping[str, Any],
    training_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "iq_support_ready_before_llm_review",
            "passed": (
                iq_summary["version"] == "v30.iq_intelligent_question_support_review.v1"
                and iq_summary["iq_support_review_ready"]
                and iq_summary["interaction_loop_case_count"] >= 5
                and not iq_summary["chart_fact_mutation_allowed"]
                and not iq_summary["policy_pointer_promotion_allowed"]
            ),
            "expected": "IQ-S1 is ready before LLM expression support review",
        },
        {
            "check_id": "bl8_bazi_llm_closeout_ready",
            "passed": (
                llm_summary["version"] == "v30.bazi_llm_closeout.v1"
                and llm_summary["closeout_ready"]
                and llm_summary["bazi_llm_steady_state"]
                and llm_summary["accepted_evidence_ready_count"] == llm_summary["accepted_evidence_count"]
                and llm_summary["accepted_evidence_count"] >= 5
                and llm_summary["bazi_llm_mainline_completion"] >= 88
            ),
            "expected": "BL8 closeout is ready across context, answer, output, training, and role/locale evidence",
        },
        {
            "check_id": "bounded_context_role_prompt_and_fallback_ready",
            "passed": (
                llm_summary["context_compiler_completion"] >= 90
                and llm_summary["prompt_registry_completion"] >= 88
                and llm_summary["answer_generator_completion"] >= 88
                and llm_summary["role_locale_completion"] >= 86
                and set(llm_summary["accepted_evidence_keys"]) >= {"bl1_bl3", "bl4", "bl5", "bl6", "bl7"}
            ),
            "expected": "task-specific context, role prompts, fallback answer path, and role/locale coverage are ready",
        },
        {
            "check_id": "bazi_llm_acceptance_synthetic_ready",
            "passed": (
                acceptance_summary["suite_id"] == "v30.synthetic.bazi_llm_acceptance"
                and acceptance_summary["passed"]
                and acceptance_summary["case_count"] == acceptance_summary["passed_count"]
                and acceptance_summary["case_count"] >= 5
                and acceptance_summary["quality_row_count"] >= 5
                and acceptance_summary["accepted_count_max"] >= 2
                and acceptance_summary["rejected_count_max"] >= 3
                and acceptance_summary["schema_rejected_count_max"] >= 1
                and acceptance_summary["role_failure_count_max"] >= 1
                and acceptance_summary["drift_rejected_count_max"] >= 1
            ),
            "expected": "bazi_llm_acceptance synthetic accepts valid expression and rejects schema, role, and drift failures",
        },
        {
            "check_id": "llm_training_boundary_locked",
            "passed": (
                training_summary["bazi_llm_training_signal_present"]
                and training_summary["domain"] == "llm"
                and training_summary["can_tune_expression"]
                and training_summary["can_tune_question_strategy"]
                and not training_summary["can_tune_chart_facts"]
                and training_summary["chart_fact_mutation_allowed_count"] == 0
            ),
            "expected": "LLM training tunes expression/question strategy only, not deterministic Bazi facts",
        },
        {
            "check_id": "live_heavy_and_fact_generation_boundaries_locked",
            "passed": (
                llm_summary["optional_live_smoke_allowed"]
                and not llm_summary["live_llm_required"]
                and not llm_summary["chart_fact_mutation_allowed"]
                and not llm_summary["policy_pointer_write_allowed"]
                and not llm_summary["core_bazi_modules_reopened"]
                and not llm_summary["full_pytest_required"]
                and not llm_summary["synthetic_all_required"]
                and not llm_summary["full_518k_required"]
                and acceptance_summary["chart_fact_mutation_allowed_count"] == 0
                and acceptance_summary["live_llm_required_count"] == 0
            ),
            "expected": "live smoke and heavy gates remain explicit; LLM cannot generate chart facts",
        },
    ]


def _decision(
    checks: list[Mapping[str, Any]],
    llm_summary: Mapping[str, Any],
    acceptance_summary: Mapping[str, Any],
) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "decision_status": "llm_bazi_expression_support_ready" if ready else "llm_bazi_expression_support_blocked",
        "llm_bazi_expression_support_ready": ready,
        "bazi_llm_mainline_completion": int(llm_summary.get("bazi_llm_mainline_completion", 0) or 0),
        "bazi_llm_acceptance_case_count": int(acceptance_summary.get("case_count", 0) or 0),
        "closeout_check_count": len(checks),
        "passed_closeout_check_count": sum(1 for row in checks if row.get("passed") is True),
        "failed_closeout_check_ids": failed,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "llm_chart_fact_generation_allowed": False,
        "live_llm_required": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "blockers": ["llm_bazi_expression_support_checks_failed"] if failed else [],
        "rationale": (
            "LLM remains ready as bounded, role-aware Bazi expression support after IQ-S1."
            if ready
            else "LLM support review is blocked until IQ, BL8, acceptance synthetic, training, or no-fact boundaries pass."
        ),
    }


def _monitoring_baseline(acceptance_summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "monitoring_id": "llm_bazi_expression_support_steady_state_monitoring",
        "recommended_trigger": "after_prompt_context_change_or_before_release",
        "commands": [
            "python3 scripts/run_llm_bazi_expression_support_review.py --sample-limit 8",
            "python3 scripts/run_synthetic_validation.py --tier bazi_llm_acceptance",
        ],
        "optional_live_command": "python3 scripts/run_llm_live_smoke.py --json",
        "watched_metrics": {
            "bazi_llm_acceptance_case_count": int(acceptance_summary.get("case_count", 0) or 0),
            "accepted_count_max": int(acceptance_summary.get("accepted_count_max", 0) or 0),
            "rejected_count_max": int(acceptance_summary.get("rejected_count_max", 0) or 0),
        },
        "live_llm_required": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "boundary": "monitoring_tracks_llm_expression_drift_without_fact_or_pointer_writes",
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["llm_bazi_expression_support_ready"]:
        return {
            "next_task": "Training/Synthetic Support Review",
            "reason": "LLM expression support is ready; next review training and synthetic support around the stable M1-M8/IQ/LLM chain.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "LLM Bazi Expression Support Remediation",
        "reason": "LLM support checks failed; repair IQ prerequisite, BL8 closeout, acceptance synthetic, training boundary, or no-fact guardrails.",
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['review_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
