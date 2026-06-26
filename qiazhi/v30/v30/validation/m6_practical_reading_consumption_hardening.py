from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.validation.m5_calibration_replay_closeout import run_m5_calibration_replay_closeout
from v30.validation.real_business_answer_refresh_regression import run_real_business_answer_refresh_regression
from v30.validation.real_business_bazi_reading_acceptance import run_real_business_bazi_reading_acceptance
from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.training_signals import extract_training_signals


M6_PRACTICAL_READING_CONSUMPTION_HARDENING_VERSION = "v30.m6_practical_reading_consumption_hardening.v1"

M6_REQUIRED_DOMAINS = ("career", "wealth", "relationship", "health", "timing")


def run_m6_practical_reading_consumption_hardening(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    m5_closeout = run_m5_calibration_replay_closeout(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    m6_contract = run_synthetic_tier("m6_practical_reading_contract")
    real_case_pack = run_synthetic_tier("real_case_calibration_pack")
    business_acceptance = run_real_business_bazi_reading_acceptance(case_limit=12)
    answer_refresh = run_real_business_answer_refresh_regression(case_limit=5)
    training_signals = []
    for result in (m6_contract, real_case_pack):
        training_signals.extend(
            signal.model_dump(mode="json")
            for signal in extract_training_signals(result)
        )
    return build_m6_practical_reading_consumption_hardening(
        m5_closeout=m5_closeout,
        m6_contract_synthetic=m6_contract.model_dump(mode="json"),
        real_case_synthetic=real_case_pack.model_dump(mode="json"),
        business_acceptance=business_acceptance,
        answer_refresh_regression=answer_refresh,
        training_signals=training_signals,
        artifact_dir=artifact_dir,
    )


def build_m6_practical_reading_consumption_hardening(
    *,
    m5_closeout: Mapping[str, Any],
    m6_contract_synthetic: Mapping[str, Any],
    real_case_synthetic: Mapping[str, Any],
    business_acceptance: Mapping[str, Any],
    answer_refresh_regression: Mapping[str, Any],
    training_signals: list[Mapping[str, Any]],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    review_id = f"v30.m6.h1.{reviewed_at.strftime('%Y%m%d%H%M%S%f')}"
    m5_summary = _m5_closeout_summary(m5_closeout)
    synthetic_summary = _synthetic_summary(m6_contract_synthetic, real_case_synthetic)
    consumption_summary = _consumption_summary(m6_contract_synthetic)
    business_summary = _business_summary(business_acceptance, answer_refresh_regression)
    training_summary = _training_summary(training_signals)
    checks = _checks(
        m5_summary=m5_summary,
        synthetic_summary=synthetic_summary,
        consumption_summary=consumption_summary,
        business_summary=business_summary,
        training_summary=training_summary,
    )
    decision = _decision(checks=checks, consumption_summary=consumption_summary)
    payload: dict[str, Any] = {
        "version": M6_PRACTICAL_READING_CONSUMPTION_HARDENING_VERSION,
        "review_id": review_id,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["m6_consumption_hardening_ready"] else "blocked",
        "decision": decision,
        "m5_closeout_summary": m5_summary,
        "synthetic_summary": synthetic_summary,
        "practical_reading_consumption_summary": consumption_summary,
        "business_reading_summary": business_summary,
        "training_signal_summary": training_summary,
        "hardening_checks": checks,
        "policy_boundary": {
            "reading_composition_only": True,
            "llm_expression_only": True,
            "runtime_decision_write_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_strength_verdict_allowed": False,
            "fixed_structure_verdict_allowed": False,
            "fixed_useful_god_verdict_allowed": False,
            "fixed_event_prediction_allowed": False,
            "raw_model_score_visible": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "boundary": "m6_h1_hardens_practical_reading_consumption_without_generating_chart_facts_or_fixed_verdicts",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "m6_practical_reading_consumption_hardening_validates_customer_reading_uses_core_modules_read_only",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _m5_closeout_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "m5_calibration_replay_closed": bool(decision.get("m5_calibration_replay_closed")),
        "m5_ranked_decision_steady_support_ready": bool(decision.get("m5_ranked_decision_steady_support_ready")),
        "m5_ready_for_m6_consumption": bool(decision.get("m5_ready_for_m6_consumption")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "fixed_bazi_verdict_allowed": bool(decision.get("fixed_bazi_verdict_allowed")),
    }


def _synthetic_summary(m6_contract: Mapping[str, Any], real_case: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "m6_practical_reading_contract": _suite_summary(m6_contract),
        "real_case_calibration_pack": _suite_summary(real_case),
        "case_count_total": int(m6_contract.get("case_count", 0) or 0) + int(real_case.get("case_count", 0) or 0),
        "boundary": "m6_synthetic_summary_reviews_contract_and_real_case_replay_only",
    }


def _suite_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "suite_id": str(payload.get("suite_id") or ""),
        "passed": bool(payload.get("passed")),
        "case_count": int(payload.get("case_count", 0) or 0),
        "passed_count": int(payload.get("passed_count", 0) or 0),
        "failed_count": int(payload.get("failed_count", 0) or 0),
    }


def _consumption_summary(m6_contract: Mapping[str, Any]) -> dict[str, Any]:
    domain_payloads = _domain_payloads(m6_contract)
    trace_rows = [
        _mapping(payload.get("module_trace"))
        for payload in domain_payloads
        if isinstance(payload.get("module_trace"), Mapping)
    ]
    quality_rows = [
        _mapping(payload.get("quality_contract"))
        for payload in domain_payloads
        if isinstance(payload.get("quality_contract"), Mapping)
    ]
    domain_counts = Counter(
        str(domain)
        for row in _result_rows(m6_contract)
        for domain in _domains_for_result(row)
    )
    blocked_claims = [
        str(claim)
        for payload in domain_payloads
        for claim in _list(payload.get("blocked_claims"))
    ]
    raw_leak_count = sum(1 for payload in domain_payloads if _has_raw_score_leak(payload))
    return {
        "domain_payload_count": len(domain_payloads),
        "domain_counts": dict(domain_counts),
        "required_domains": list(M6_REQUIRED_DOMAINS),
        "domain_coverage_complete": set(M6_REQUIRED_DOMAINS) <= set(domain_counts),
        "module_trace_count": len(trace_rows),
        "uses_m1_m2_facts_count": sum(1 for trace in trace_rows if trace.get("uses_m1_m2_facts") is True),
        "uses_m3_structure_evidence_count": sum(1 for trace in trace_rows if trace.get("uses_m3_structure_evidence") is True),
        "uses_m4_model_signal_count": sum(1 for trace in trace_rows if trace.get("uses_m4_model_signal") is True),
        "uses_m5_ranked_decisions_count": sum(1 for trace in trace_rows if trace.get("uses_m5_ranked_decisions") is True),
        "raw_model_score_visible_count": sum(1 for trace in trace_rows if trace.get("raw_model_score_visible") is True),
        "chart_fact_mutation_allowed_count": sum(1 for trace in trace_rows if trace.get("chart_fact_mutation_allowed") is True),
        "quality_contract_count": len(quality_rows),
        "quality_boundary_count": sum(
            1
            for row in quality_rows
            if row.get("boundary") == "practical_reading_quality_trains_expression_not_chart_facts"
        ),
        "blocked_claim_count": len(blocked_claims),
        "blocked_claim_examples": sorted(set(blocked_claims))[:12],
        "calculation_basis_count": sum(1 for payload in domain_payloads if isinstance(payload.get("calculation_basis"), Mapping)),
        "ranked_decision_link_count": sum(1 for payload in domain_payloads if isinstance(payload.get("ranked_decision_links"), Mapping)),
        "model_signal_context_count": sum(1 for payload in domain_payloads if isinstance(payload.get("model_signal_context"), Mapping)),
        "evidence_bound_count": sum(1 for payload in domain_payloads if _list(payload.get("evidence_ids"))),
        "explanation_unit_count": sum(len(_list(payload.get("explanation_units"))) for payload in domain_payloads),
        "action_step_count": sum(len(_list(payload.get("action_steps"))) for payload in domain_payloads),
        "calibration_prompt_count": sum(len(_list(payload.get("calibration_prompts"))) for payload in domain_payloads),
        "raw_score_leak_count": raw_leak_count,
        "boundary": "m6_consumption_summary_proves_practical_reading_uses_m1_to_m5_without_raw_score_or_fact_mutation",
    }


def _business_summary(
    acceptance: Mapping[str, Any],
    answer_refresh: Mapping[str, Any],
) -> dict[str, Any]:
    acceptance_decision = _mapping(acceptance.get("decision"))
    acceptance_summary = _mapping(acceptance.get("acceptance_summary"))
    refresh_decision = _mapping(answer_refresh.get("decision"))
    refresh_summary = _mapping(answer_refresh.get("refresh_summary"))
    return {
        "business_acceptance_version": str(acceptance.get("version") or ""),
        "business_bazi_reading_ready": bool(acceptance_decision.get("business_bazi_reading_ready")),
        "business_ready_case_count": int(acceptance_summary.get("ready_case_count", 0) or 0),
        "business_m6_practical_ready_count": int(acceptance_summary.get("m6_practical_ready_count", 0) or 0),
        "customer_projection_leak_free_count": int(acceptance_summary.get("customer_projection_leak_free_count", 0) or 0),
        "answer_refresh_version": str(answer_refresh.get("version") or ""),
        "answer_refresh_regression_ready": bool(refresh_decision.get("answer_refresh_regression_ready")),
        "answer_case_count": int(refresh_summary.get("answer_case_count", 0) or 0),
        "passed_answer_case_count": int(refresh_summary.get("passed_answer_case_count", 0) or 0),
        "stable_core_fingerprint_count": int(refresh_summary.get("stable_core_fingerprint_count", 0) or 0),
        "policy_pointer_promotion_allowed": bool(acceptance_decision.get("policy_pointer_promotion_allowed")) or bool(refresh_decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(acceptance_decision.get("chart_fact_mutation_allowed")) or bool(refresh_decision.get("chart_fact_mutation_allowed")),
        "boundary": "business_summary_confirms_practical_reading_and_answer_refresh_preserve_customer_surface",
    }


def _training_summary(signals: list[Mapping[str, Any]]) -> dict[str, Any]:
    signal_by_id = {
        str(signal.get("signal_id") or ""): signal
        for signal in signals
        if signal.get("signal_id")
    }
    reading_signal = _mapping(signal_by_id.get("v30.training_signal.practical_reading_quality"))
    payload = _mapping(reading_signal.get("payload"))
    return {
        "signal_count": len(signals),
        "signal_ids": sorted(signal_by_id),
        "practical_reading_quality_present": bool(reading_signal),
        "practical_reading_quality_domain": str(reading_signal.get("domain") or ""),
        "practical_reading_quality_strength": float(reading_signal.get("strength", 0.0) or 0.0),
        "reading_domain_count": int(payload.get("reading_domain_count", 0) or 0),
        "module_trace_count": int(payload.get("module_trace_count", 0) or 0),
        "quality_boundary": str(payload.get("boundary") or ""),
        "boundary": "m6_training_signals_tune_expression_and_domain_priority_not_chart_facts",
    }


def _checks(
    *,
    m5_summary: Mapping[str, Any],
    synthetic_summary: Mapping[str, Any],
    consumption_summary: Mapping[str, Any],
    business_summary: Mapping[str, Any],
    training_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    m6_contract = _mapping(synthetic_summary.get("m6_practical_reading_contract"))
    real_case = _mapping(synthetic_summary.get("real_case_calibration_pack"))
    domain_payload_count = int(consumption_summary.get("domain_payload_count", 0) or 0)
    return [
        {
            "check_id": "m5_closeout_ready_for_m6",
            "passed": (
                m5_summary["version"] == "v30.m5_calibration_replay_closeout.v1"
                and m5_summary["m5_calibration_replay_closed"]
                and m5_summary["m5_ready_for_m6_consumption"]
            ),
            "expected": "M5-H3 closeout is ready for M6 consumption",
        },
        {
            "check_id": "m6_synthetic_contracts_passed",
            "passed": (
                m6_contract["suite_id"] == "v30.synthetic.m6_practical_reading_contract"
                and m6_contract["passed"]
                and int(m6_contract["case_count"]) >= 30
                and real_case["suite_id"] == "v30.synthetic.real_case_calibration_pack"
                and real_case["passed"]
                and int(real_case["case_count"]) >= 30
            ),
            "expected": "M6 contract and real-case calibration synthetic tiers pass",
        },
        {
            "check_id": "m6_consumes_m1_to_m5_modules",
            "passed": (
                domain_payload_count >= 100
                and consumption_summary["domain_coverage_complete"]
                and consumption_summary["module_trace_count"] == domain_payload_count
                and consumption_summary["uses_m1_m2_facts_count"] == domain_payload_count
                and consumption_summary["uses_m3_structure_evidence_count"] == domain_payload_count
                and consumption_summary["uses_m4_model_signal_count"] == domain_payload_count
                and consumption_summary["uses_m5_ranked_decisions_count"] == domain_payload_count
            ),
            "expected": "Every practical domain reading traces consumption of M1/M2, M3, M4, and M5",
        },
        {
            "check_id": "m6_customer_reading_quality_surface_complete",
            "passed": (
                consumption_summary["quality_contract_count"] == domain_payload_count
                and consumption_summary["quality_boundary_count"] == domain_payload_count
                and consumption_summary["calculation_basis_count"] == domain_payload_count
                and consumption_summary["ranked_decision_link_count"] == domain_payload_count
                and consumption_summary["model_signal_context_count"] == domain_payload_count
                and consumption_summary["evidence_bound_count"] == domain_payload_count
                and consumption_summary["explanation_unit_count"] >= domain_payload_count * 3
                and consumption_summary["action_step_count"] >= domain_payload_count * 3
                and consumption_summary["calibration_prompt_count"] >= domain_payload_count * 2
            ),
            "expected": "M6 domain readings expose quality contracts, evidence links, explanations, action steps, and calibration prompts",
        },
        {
            "check_id": "m6_no_raw_score_or_fixed_claim_leak",
            "passed": (
                consumption_summary["raw_score_leak_count"] == 0
                and consumption_summary["raw_model_score_visible_count"] == 0
                and consumption_summary["chart_fact_mutation_allowed_count"] == 0
                and consumption_summary["blocked_claim_count"] >= domain_payload_count
            ),
            "expected": "M6 hides raw scores, blocks fixed claims, and cannot mutate chart facts",
        },
        {
            "check_id": "m6_business_reading_and_answer_refresh_ready",
            "passed": (
                business_summary["business_acceptance_version"] == "v30.real_business_bazi_reading_acceptance.v1"
                and business_summary["business_bazi_reading_ready"]
                and business_summary["business_m6_practical_ready_count"] >= 10
                and business_summary["answer_refresh_version"] == "v30.real_business_answer_refresh_regression.v1"
                and business_summary["answer_refresh_regression_ready"]
                and business_summary["passed_answer_case_count"] >= 5
                and business_summary["stable_core_fingerprint_count"] >= 5
            ),
            "expected": "Business reading acceptance and answer refresh preserve the M6 customer surface",
        },
        {
            "check_id": "m6_training_signal_boundary_locked",
            "passed": (
                training_summary["practical_reading_quality_present"]
                and training_summary["practical_reading_quality_domain"] == "practical_reading"
                and training_summary["quality_boundary"] == "v30.training_signal.practical_reading_quality_validates_runtime_context_not_chart_fact"
                and training_summary["reading_domain_count"] >= 5
                and training_summary["module_trace_count"] >= 100
            ),
            "expected": "M6 training signal tunes expression/domain priority only, never chart facts",
        },
        {
            "check_id": "m6_no_pointer_or_chart_fact_mutation",
            "passed": (
                not m5_summary["policy_pointer_promotion_allowed"]
                and not m5_summary["chart_fact_mutation_allowed"]
                and not m5_summary["fixed_bazi_verdict_allowed"]
                and not business_summary["policy_pointer_promotion_allowed"]
                and not business_summary["chart_fact_mutation_allowed"]
            ),
            "expected": "M6 hardening remains read-only across M5, business acceptance, and answer refresh",
        },
    ]


def _decision(*, checks: list[dict[str, Any]], consumption_summary: Mapping[str, Any]) -> dict[str, Any]:
    failed = [row["check_id"] for row in checks if not row["passed"]]
    ready = not failed
    return {
        "decision_status": "m6_practical_reading_consumption_hardening_ready" if ready else "m6_practical_reading_consumption_hardening_blocked",
        "m6_consumption_hardening_ready": ready,
        "m6_practical_reading_support_ready": ready,
        "ready_for_m6_closeout": ready,
        "domain_payload_count": int(consumption_summary.get("domain_payload_count", 0) or 0),
        "hardening_check_count": len(checks),
        "passed_hardening_check_count": sum(1 for row in checks if row["passed"]),
        "failed_hardening_check_ids": failed,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "blockers": ["m6_consumption_hardening_checks_failed"] if failed else [],
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["m6_consumption_hardening_ready"]:
        return {
            "next_task": "M6 Practical Reading Closeout",
            "reason": "M6 consumes M1-M5 evidence cleanly; next close M6 as customer-facing reading support before returning to IQ or M7.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "M6 Practical Reading Consumption Remediation",
        "reason": "M6 consumption hardening checks are blocked; repair practical reading evidence links, surface quality, or training boundaries.",
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _domain_payloads(suite: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    payloads: list[Mapping[str, Any]] = []
    for row in _result_rows(suite):
        observed = _mapping(row.get("observed"))
        practical = _mapping(observed.get("practical_reading_context"))
        readings = _mapping(practical.get("domain_readings"))
        payloads.extend(_mapping(payload) for payload in readings.values() if isinstance(payload, Mapping))
    return payloads


def _domains_for_result(row: Mapping[str, Any]) -> list[str]:
    observed = _mapping(row.get("observed"))
    practical = _mapping(observed.get("practical_reading_context"))
    readings = _mapping(practical.get("domain_readings"))
    return [str(domain) for domain in readings if domain]


def _result_rows(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = payload.get("results", [])
    return [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, list) else []


def _has_raw_score_leak(payload: Mapping[str, Any]) -> bool:
    return _has_forbidden_key(payload, {"raw_score", "raw_weight", "energy", "stability", "volatility"})


def _has_forbidden_key(value: Any, forbidden: set[str]) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in forbidden:
                return True
            if _has_forbidden_key(child, forbidden):
                return True
        return False
    if isinstance(value, list):
        return any(_has_forbidden_key(child, forbidden) for child in value)
    return False


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['review_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
