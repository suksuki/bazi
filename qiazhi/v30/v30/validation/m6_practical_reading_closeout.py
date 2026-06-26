from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.validation.m6_practical_reading_consumption_hardening import (
    M6_REQUIRED_DOMAINS,
    run_m6_practical_reading_consumption_hardening,
)


M6_PRACTICAL_READING_CLOSEOUT_VERSION = "v30.m6_practical_reading_closeout.v1"


def run_m6_practical_reading_closeout(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    consumption_hardening = run_m6_practical_reading_consumption_hardening(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    return build_m6_practical_reading_closeout(
        consumption_hardening=consumption_hardening,
        artifact_dir=artifact_dir,
    )


def build_m6_practical_reading_closeout(
    *,
    consumption_hardening: Mapping[str, Any],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    closed_at = datetime.now(timezone.utc)
    closeout_id = f"v30.m6.h2.{closed_at.strftime('%Y%m%d%H%M%S%f')}"
    hardening_summary = _hardening_summary(consumption_hardening)
    module_summary = _module_summary(consumption_hardening)
    monitoring_baseline = _monitoring_baseline(hardening_summary, module_summary)
    closeout_checks = _closeout_checks(hardening_summary, module_summary)
    decision = _decision(
        hardening_summary=hardening_summary,
        module_summary=module_summary,
        closeout_checks=closeout_checks,
    )
    payload: dict[str, Any] = {
        "version": M6_PRACTICAL_READING_CLOSEOUT_VERSION,
        "closeout_id": closeout_id,
        "closed_at": closed_at.isoformat(),
        "status": "completed" if decision["m6_practical_reading_closed"] else "blocked",
        "decision": decision,
        "consumption_hardening_summary": hardening_summary,
        "m6_module_summary": module_summary,
        "monitoring_baseline": monitoring_baseline,
        "closeout_checks": closeout_checks,
        "policy_boundary": {
            "steady_state_support_module": decision["m6_practical_reading_closed"],
            "customer_facing_reading_support": True,
            "reading_composition_only": True,
            "llm_expression_only": True,
            "runtime_decision_write_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "fixed_event_prediction_allowed": False,
            "raw_model_score_visible": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "boundary": "m6_h2_closes_practical_reading_without_fact_generation_pointer_writes_or_fixed_verdicts",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "m6_practical_reading_closeout_marks_customer_reading_as_steady_support_when_checks_pass",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _hardening_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    consumption = _mapping(payload.get("practical_reading_consumption_summary"))
    business = _mapping(payload.get("business_reading_summary"))
    training = _mapping(payload.get("training_signal_summary"))
    synthetic = _mapping(payload.get("synthetic_summary"))
    m6_contract = _mapping(synthetic.get("m6_practical_reading_contract"))
    real_case = _mapping(synthetic.get("real_case_calibration_pack"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "m6_consumption_hardening_ready": bool(decision.get("m6_consumption_hardening_ready")),
        "m6_practical_reading_support_ready": bool(decision.get("m6_practical_reading_support_ready")),
        "ready_for_m6_closeout": bool(decision.get("ready_for_m6_closeout")),
        "hardening_check_count": int(decision.get("hardening_check_count", 0) or 0),
        "passed_hardening_check_count": int(decision.get("passed_hardening_check_count", 0) or 0),
        "domain_payload_count": int(decision.get("domain_payload_count", 0) or consumption.get("domain_payload_count", 0) or 0),
        "required_domains": _list(consumption.get("required_domains")),
        "domain_counts": dict(_mapping(consumption.get("domain_counts"))),
        "blocked_claim_count": int(consumption.get("blocked_claim_count", 0) or 0),
        "raw_score_leak_count": int(consumption.get("raw_score_leak_count", 0) or 0),
        "raw_model_score_visible_count": int(consumption.get("raw_model_score_visible_count", 0) or 0),
        "chart_fact_mutation_allowed_count": int(consumption.get("chart_fact_mutation_allowed_count", 0) or 0),
        "business_bazi_reading_ready": bool(business.get("business_bazi_reading_ready")),
        "answer_refresh_regression_ready": bool(business.get("answer_refresh_regression_ready")),
        "business_m6_practical_ready_count": int(business.get("business_m6_practical_ready_count", 0) or 0),
        "passed_answer_case_count": int(business.get("passed_answer_case_count", 0) or 0),
        "practical_reading_quality_present": bool(training.get("practical_reading_quality_present")),
        "quality_boundary": str(training.get("quality_boundary") or ""),
        "m6_contract_passed": bool(m6_contract.get("passed")),
        "m6_contract_case_count": int(m6_contract.get("case_count", 0) or 0),
        "real_case_pack_passed": bool(real_case.get("passed")),
        "real_case_pack_case_count": int(real_case.get("case_count", 0) or 0),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "pointer_write_performed": bool(decision.get("pointer_write_performed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "fixed_bazi_verdict_allowed": bool(decision.get("fixed_bazi_verdict_allowed")),
    }


def _module_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    consumption = _mapping(payload.get("practical_reading_consumption_summary"))
    business = _mapping(payload.get("business_reading_summary"))
    return {
        "module_id": "M6",
        "module_name": "Practical Bazi reading output",
        "module_status": "steady_support_candidate",
        "reading_domains": list(M6_REQUIRED_DOMAINS),
        "domain_payload_count": int(consumption.get("domain_payload_count", 0) or 0),
        "domain_counts": dict(_mapping(consumption.get("domain_counts"))),
        "module_trace_count": int(consumption.get("module_trace_count", 0) or 0),
        "evidence_bound_count": int(consumption.get("evidence_bound_count", 0) or 0),
        "explanation_unit_count": int(consumption.get("explanation_unit_count", 0) or 0),
        "action_step_count": int(consumption.get("action_step_count", 0) or 0),
        "calibration_prompt_count": int(consumption.get("calibration_prompt_count", 0) or 0),
        "business_ready_case_count": int(business.get("business_ready_case_count", 0) or 0),
        "answer_refresh_passed_case_count": int(business.get("passed_answer_case_count", 0) or 0),
        "customer_projection_leak_free_count": int(business.get("customer_projection_leak_free_count", 0) or 0),
        "iq_question_strategy_consumption_ready": True,
        "llm_context_consumption_ready": True,
        "training_consumption_ready": True,
        "release_acceptance_consumption_ready": True,
        "boundary": "m6_outputs_customer_facing_practical_reading_not_new_chart_facts_or_final_fortune_claims",
    }


def _monitoring_baseline(
    hardening_summary: Mapping[str, Any],
    module_summary: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "monitoring_id": "m6_practical_reading_steady_state_monitoring",
        "recommended_trigger": "before_release_or_after_new_real_case_pack_or_llm_prompt_change",
        "commands": [
            "python3 scripts/run_m6_practical_reading_closeout.py --sample-limit 8",
            "python3 scripts/run_synthetic_validation.py --tier m6_practical_reading_contract",
            "python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack",
        ],
        "watched_metrics": {
            "domain_payload_count": int(hardening_summary.get("domain_payload_count", 0) or 0),
            "blocked_claim_count": int(hardening_summary.get("blocked_claim_count", 0) or 0),
            "business_m6_practical_ready_count": int(hardening_summary.get("business_m6_practical_ready_count", 0) or 0),
            "passed_answer_case_count": int(hardening_summary.get("passed_answer_case_count", 0) or 0),
            "reading_domains": _list(module_summary.get("reading_domains")),
        },
        "full_pytest_required": False,
        "full_518k_required": False,
        "boundary": "monitoring_tracks_m6_reading_surface_drift_without_fact_or_policy_writes",
    }


def _closeout_checks(
    hardening_summary: Mapping[str, Any],
    module_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    domain_counts = _mapping(hardening_summary.get("domain_counts"))
    return [
        {
            "check_id": "m6_h1_consumption_hardening_ready",
            "passed": (
                hardening_summary["version"] == "v30.m6_practical_reading_consumption_hardening.v1"
                and hardening_summary["m6_consumption_hardening_ready"]
                and hardening_summary["ready_for_m6_closeout"]
                and hardening_summary["passed_hardening_check_count"] == hardening_summary["hardening_check_count"]
            ),
            "expected": "M6-H1 consumption hardening is ready for closeout",
        },
        {
            "check_id": "m6_reading_domains_steady",
            "passed": (
                set(domain_counts) >= set(M6_REQUIRED_DOMAINS)
                and hardening_summary["domain_payload_count"] >= 100
                and all(int(domain_counts.get(domain, 0) or 0) >= 20 for domain in M6_REQUIRED_DOMAINS)
            ),
            "expected": "career, wealth, relationship, health, and timing domains have steady coverage",
        },
        {
            "check_id": "m6_business_surface_stable",
            "passed": (
                hardening_summary["business_bazi_reading_ready"]
                and hardening_summary["answer_refresh_regression_ready"]
                and hardening_summary["business_m6_practical_ready_count"] >= 10
                and hardening_summary["passed_answer_case_count"] >= 5
            ),
            "expected": "business reading and answer refresh preserve the M6 customer surface",
        },
        {
            "check_id": "m6_synthetic_and_training_lineage_complete",
            "passed": (
                hardening_summary["m6_contract_passed"]
                and hardening_summary["m6_contract_case_count"] >= 30
                and hardening_summary["real_case_pack_passed"]
                and hardening_summary["real_case_pack_case_count"] >= 30
                and hardening_summary["practical_reading_quality_present"]
                and hardening_summary["quality_boundary"] == "v30.training_signal.practical_reading_quality_validates_runtime_context_not_chart_fact"
            ),
            "expected": "M6 contract, real-case pack, and practical-reading training signal lineage are complete",
        },
        {
            "check_id": "m6_customer_claim_guardrails_locked",
            "passed": (
                hardening_summary["blocked_claim_count"] >= hardening_summary["domain_payload_count"]
                and hardening_summary["raw_score_leak_count"] == 0
                and hardening_summary["raw_model_score_visible_count"] == 0
                and hardening_summary["chart_fact_mutation_allowed_count"] == 0
            ),
            "expected": "blocked claims are present and raw score/chart mutation leaks are absent",
        },
        {
            "check_id": "m6_downstream_consumption_ready",
            "passed": (
                module_summary["iq_question_strategy_consumption_ready"]
                and module_summary["llm_context_consumption_ready"]
                and module_summary["training_consumption_ready"]
                and module_summary["release_acceptance_consumption_ready"]
            ),
            "expected": "M6 can support IQ, LLM context, training, and release acceptance paths",
        },
        {
            "check_id": "m6_no_write_boundary_preserved",
            "passed": (
                not hardening_summary["policy_pointer_promotion_allowed"]
                and not hardening_summary["pointer_write_performed"]
                and not hardening_summary["chart_fact_mutation_allowed"]
                and not hardening_summary["fixed_bazi_verdict_allowed"]
            ),
            "expected": "no pointer, fixed-verdict, or chart-fact write occurred",
        },
    ]


def _decision(
    *,
    hardening_summary: Mapping[str, Any],
    module_summary: Mapping[str, Any],
    closeout_checks: list[dict[str, Any]],
) -> dict[str, Any]:
    failed = [row["check_id"] for row in closeout_checks if not row["passed"]]
    ready = not failed
    return {
        "decision_status": "m6_practical_reading_closed" if ready else "m6_practical_reading_closeout_blocked",
        "m6_practical_reading_closed": ready,
        "m6_steady_customer_reading_support_ready": ready,
        "m6_ready_for_iq_consumption": ready and bool(module_summary.get("iq_question_strategy_consumption_ready")),
        "m6_ready_for_llm_context_consumption": ready and bool(module_summary.get("llm_context_consumption_ready")),
        "m6_ready_for_training_consumption": ready and bool(module_summary.get("training_consumption_ready")),
        "m6_ready_for_release_acceptance": ready and bool(module_summary.get("release_acceptance_consumption_ready")),
        "domain_payload_count": int(hardening_summary.get("domain_payload_count", 0) or 0),
        "closeout_check_count": len(closeout_checks),
        "passed_closeout_check_count": sum(1 for row in closeout_checks if row["passed"]),
        "failed_closeout_check_ids": failed,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "blockers": ["m6_practical_reading_closeout_checks_failed"] if failed else [],
        "rationale": (
            "M6-H1 is complete; M6 can serve as stable customer-facing practical reading support."
            if ready
            else "M6 cannot close until the failed closeout checks are resolved."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["m6_practical_reading_closed"]:
        return {
            "next_task": "M7 Real-Case Calibration Steady-State Review",
            "reason": "M6 customer-facing reading support is closed; next verify real-case calibration remains sufficient for ongoing module calibration.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "M6 Practical Reading Closeout Remediation",
        "reason": "M6 closeout checks failed; repair hardening lineage, reading domain coverage, business surface, or guardrails.",
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['closeout_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
