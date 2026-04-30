from __future__ import annotations

from typing import Any, Dict, List, Optional

from v19.synthetic_validation.condition_topic_deep_validation import (
    build_p41_smart_gate_candidate_batches,
    run_p41_topic_batch_application_regression,
)
from v19.synthetic_validation.rule_audit_application import build_p40_framework_rule_registry


P42_SMART_GATE_AUDIT_VERSION = "v19.p42.smart_gate_audit.v1"
P42_SMART_GATE_EVAL_VERSION = "v19.p42.smart_gate_eval_dataset.v1"
P42_SMART_GATE_REGRESSION_VERSION = "v19.p42.smart_gate_regression.v1"
P42_FRAMEWORK_GATE_PLAN_VERSION = "v19.p42.framework_gate_plan.v1"
P42_SMART_GATE_APPLICATION_REGRESSION_VERSION = "v19.p42.smart_gate_application_regression.v1"

P42_GUARDRAILS = [
    "P41_DEEP_VALIDATION_REQUIRED",
    "SMART_GATE_ACCELERATION_DRY_RUN_ONLY",
    "R0_R1_DRY_RUN_CANDIDATE",
    "R2_SHADOW_SCORING_CANDIDATE",
    "ENGINE_DISABLED_BY_DEFAULT",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_DOMAIN_RESULT_PREDICTION",
]

P42_GATE_SAMPLE_TYPES = [
    "gate_decision_contract",
    "risk_boundary_contract",
    "forbidden_runtime_activation_contract",
    "rollback_contract",
]


def build_p42_smart_gate_audit() -> Dict[str, Any]:
    p41 = run_p41_topic_batch_application_regression()
    p41_batches = build_p41_smart_gate_candidate_batches()
    registry = build_p40_framework_rule_registry()
    batch_by_rule_id = _batch_by_rule_id(p41_batches.get("batches") or [])
    candidates = [
        _gate_row(row, batch_by_rule_id.get(str(row.get("candidate_rule_id") or "")), p41.get("status"))
        for row in registry.get("items") or []
        if row.get("application_status") == "condition_model_queue_validated"
    ]
    failures = []
    if p41.get("status") != "pass":
        failures.append({"failure_type": "p41_regression_not_passed", "detail": "P42 requires passing P41 deep validation."})
    if any(row.get("engine_enabled") is True for row in candidates):
        failures.append({"failure_type": "engine_activation_not_allowed", "detail": "P42 candidates must remain engine-disabled."})
    return {
        "ok": not failures,
        "version": P42_SMART_GATE_AUDIT_VERSION,
        "status": "smart_gate_audit_ready" if not failures else "smart_gate_audit_failed",
        "summary": {
            "p41_regression_status": p41.get("status"),
            "candidate_count": len(candidates),
            "dry_run_candidate_count": sum(1 for row in candidates if row["gate_decision"] == "dry_run_candidate"),
            "shadow_scoring_candidate_count": sum(1 for row in candidates if row["gate_decision"] == "shadow_scoring_candidate"),
            "blocked_count": sum(1 for row in candidates if row["gate_decision"].startswith("blocked")),
            "engine_enabled_count": sum(1 for row in candidates if row.get("engine_enabled") is True),
            "activation_updated_count": 0,
            "by_gate_decision": _count_by(candidates, "gate_decision"),
            "by_risk_level": _count_by(candidates, "risk_level"),
            "by_topic_lane": _count_by(candidates, "topic_lane"),
        },
        "items": candidates,
        "failures": failures,
        "gate_policy": {
            "dry_run_candidate": "R0/R1 candidates that passed P41 deep validation may enter dry-run gate planning.",
            "shadow_scoring_candidate": "R2 candidates are accelerated into shadow scoring, not runtime activation.",
            "blocked": "Any missing P41 batch, failed validation, or higher risk stays blocked.",
        },
        "guardrails": P42_GUARDRAILS,
    }


def build_p42_smart_gate_eval_dataset() -> Dict[str, Any]:
    audit = build_p42_smart_gate_audit()
    samples = [sample for row in audit.get("items") or [] for sample in _gate_samples_for_row(row)]
    return {
        "ok": audit.get("ok") is True,
        "version": P42_SMART_GATE_EVAL_VERSION,
        "status": "smart_gate_eval_dataset_ready_no_activation",
        "summary": {
            "candidate_count": audit["summary"]["candidate_count"],
            "sample_count": len(samples),
            "min_samples_per_candidate": len(P42_GATE_SAMPLE_TYPES) if audit["summary"]["candidate_count"] else 0,
            "activation_updated_count": 0,
            "engine_enabled_count": 0,
            "by_sample_type": _count_by(samples, "sample_type"),
            "by_gate_decision": _count_by(samples, "gate_decision"),
        },
        "samples": samples,
        "source_audit_summary": audit["summary"],
        "guardrails": P42_GUARDRAILS,
    }


def run_p42_smart_gate_regression() -> Dict[str, Any]:
    dataset = build_p42_smart_gate_eval_dataset()
    sample_results = [_evaluate_gate_sample(sample) for sample in dataset.get("samples") or []]
    failures = [failure for row in sample_results for failure in row.get("failures") or []]
    status = "pass" if dataset.get("ok") is True and not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P42_SMART_GATE_REGRESSION_VERSION,
        "status": status,
        "summary": {
            "candidate_count": dataset["summary"]["candidate_count"],
            "sample_count": len(sample_results),
            "sample_passed": sum(1 for row in sample_results if row.get("status") == "pass"),
            "sample_failed": sum(1 for row in sample_results if row.get("status") == "fail"),
            "engine_enabled_count": 0,
            "activation_updated_count": 0,
            "by_sample_type": dataset["summary"]["by_sample_type"],
        },
        "samples": sample_results,
        "failures": failures,
        "guardrails": P42_GUARDRAILS,
    }


def build_p42_framework_gate_plan() -> Dict[str, Any]:
    audit = build_p42_smart_gate_audit()
    regression = run_p42_smart_gate_regression()
    items = [
        {
            "gate_plan_id": f"p42.plan.{_slug(str(row.get('knowledge_id') or 'unknown'))}",
            "candidate_rule_id": row.get("candidate_rule_id"),
            "knowledge_id": row.get("knowledge_id"),
            "topic_lane": row.get("topic_lane"),
            "risk_level": row.get("risk_level"),
            "gate_decision": row.get("gate_decision"),
            "gate_score": row.get("gate_score"),
            "application_status": _planned_status(row, regression.get("status")),
            "engine_enabled": False,
            "runtime_mutation": False,
        }
        for row in audit.get("items") or []
    ]
    return {
        "ok": audit.get("ok") is True and regression.get("ok") is True,
        "version": P42_FRAMEWORK_GATE_PLAN_VERSION,
        "status": "framework_gate_plan_ready_no_activation",
        "summary": {
            "candidate_count": len(items),
            "dry_run_candidate_count": sum(1 for row in items if row["application_status"] == "dry_run_planned"),
            "shadow_scoring_candidate_count": sum(1 for row in items if row["application_status"] == "shadow_scoring_planned"),
            "blocked_count": sum(1 for row in items if row["application_status"].startswith("blocked")),
            "engine_enabled_count": 0,
            "activation_updated_count": 0,
            "runtime_mutation": False,
            "by_application_status": _count_by(items, "application_status"),
            "by_topic_lane": _count_by(items, "topic_lane"),
        },
        "items": items,
        "source_audit_summary": audit["summary"],
        "source_regression_summary": regression["summary"],
        "guardrails": P42_GUARDRAILS,
    }


def run_p42_smart_gate_application_regression() -> Dict[str, Any]:
    plan = build_p42_framework_gate_plan()
    failures = []
    if plan.get("ok") is not True:
        failures.append({"failure_type": "p42_plan_not_ready", "detail": "P42 gate plan is not ready."})
    if plan["summary"]["engine_enabled_count"] != 0:
        failures.append({"failure_type": "engine_activation_not_allowed", "detail": "P42 cannot enable engines."})
    if plan["summary"]["runtime_mutation"] is not False:
        failures.append({"failure_type": "runtime_mutation_not_allowed", "detail": "P42 cannot mutate runtime inference."})
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P42_SMART_GATE_APPLICATION_REGRESSION_VERSION,
        "status": status,
        "summary": {
            "candidate_count": plan["summary"]["candidate_count"],
            "dry_run_candidate_count": plan["summary"]["dry_run_candidate_count"],
            "shadow_scoring_candidate_count": plan["summary"]["shadow_scoring_candidate_count"],
            "blocked_count": plan["summary"]["blocked_count"],
            "engine_enabled_count": 0,
            "activation_updated_count": 0,
            "runtime_mutation": False,
        },
        "framework_gate_plan": plan,
        "failures": failures,
        "guardrails": P42_GUARDRAILS,
    }


def _gate_row(item: Dict[str, Any], batch: Optional[Dict[str, Any]], p41_status: str) -> Dict[str, Any]:
    risk = str(item.get("risk_level") or "R4")
    topic_lane = str((batch or {}).get("topic_lane") or "unknown")
    if p41_status != "pass":
        decision = "blocked_by_p41_regression"
    elif not batch:
        decision = "blocked_missing_topic_batch"
    elif risk in {"R0", "R1"}:
        decision = "dry_run_candidate"
    elif risk == "R2":
        decision = "shadow_scoring_candidate"
    else:
        decision = "blocked_by_risk_level"
    return {
        "gate_audit_id": f"p42.gate.{_slug(str(item.get('knowledge_id') or 'unknown'))}",
        "candidate_rule_id": str(item.get("candidate_rule_id") or ""),
        "knowledge_id": str(item.get("knowledge_id") or ""),
        "topic_lane": topic_lane,
        "domain": str(item.get("domain") or "unknown"),
        "risk_level": risk,
        "gate_decision": decision,
        "gate_score": _gate_score(risk, topic_lane, decision),
        "p41_batch_id": str((batch or {}).get("gate_batch_id") or ""),
        "engine_enabled": False,
        "activation_allowed": False,
        "runtime_mutation": False,
    }


def _gate_samples_for_row(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [_gate_sample_for_type(row, sample_type, index) for index, sample_type in enumerate(P42_GATE_SAMPLE_TYPES, start=1)]


def _gate_sample_for_type(row: Dict[str, Any], sample_type: str, index: int) -> Dict[str, Any]:
    return {
        "case_id": f"p42.gate.{_slug(str(row.get('knowledge_id') or 'unknown'))}.{index}.{sample_type}",
        "gate_audit_id": row.get("gate_audit_id"),
        "candidate_rule_id": row.get("candidate_rule_id"),
        "knowledge_id": row.get("knowledge_id"),
        "topic_lane": row.get("topic_lane"),
        "risk_level": row.get("risk_level"),
        "gate_decision": row.get("gate_decision"),
        "sample_type": sample_type,
        "expected_gate_state": _expected_gate_state(row, sample_type),
        "engine_enabled": False,
        "forbidden_state": "runtime_activation",
        "audit_tags": ["p42_smart_gate_acceleration", sample_type],
    }


def _evaluate_gate_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    failures = []
    if sample.get("engine_enabled") is True:
        failures.append(_sample_failure(sample, "engine_activation_not_allowed", "P42 gate sample must keep engine disabled."))
    if sample.get("sample_type") == "risk_boundary_contract" and sample.get("risk_level") == "R2":
        if sample.get("expected_gate_state") != "shadow_scoring_only":
            failures.append(_sample_failure(sample, "r2_boundary_failed", "R2 candidates must stay shadow scoring only."))
    if sample.get("sample_type") == "forbidden_runtime_activation_contract":
        if sample.get("forbidden_state") != "runtime_activation":
            failures.append(_sample_failure(sample, "forbidden_runtime_contract_missing", "Runtime activation must be explicitly forbidden."))
    if sample.get("sample_type") == "rollback_contract" and sample.get("expected_gate_state") != "rollback_ready":
        failures.append(_sample_failure(sample, "rollback_contract_failed", "Rollback contract must be present."))
    return {
        "case_id": sample.get("case_id"),
        "knowledge_id": sample.get("knowledge_id"),
        "sample_type": sample.get("sample_type"),
        "status": "fail" if failures else "pass",
        "failures": failures,
    }


def _expected_gate_state(row: Dict[str, Any], sample_type: str) -> str:
    decision = str(row.get("gate_decision") or "")
    risk = str(row.get("risk_level") or "")
    if sample_type == "gate_decision_contract":
        return decision
    if sample_type == "risk_boundary_contract":
        return "shadow_scoring_only" if risk == "R2" else "dry_run_allowed"
    if sample_type == "forbidden_runtime_activation_contract":
        return "runtime_activation_forbidden"
    return "rollback_ready"


def _planned_status(row: Dict[str, Any], regression_status: str) -> str:
    if regression_status != "pass":
        return "blocked_by_p42_regression"
    decision = str(row.get("gate_decision") or "")
    if decision == "dry_run_candidate":
        return "dry_run_planned"
    if decision == "shadow_scoring_candidate":
        return "shadow_scoring_planned"
    return decision


def _batch_by_rule_id(batches: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out = {}
    for batch in batches:
        for rule_id in batch.get("candidate_rule_ids") or []:
            out[str(rule_id)] = batch
    return out


def _gate_score(risk: str, topic_lane: str, decision: str) -> float:
    if decision.startswith("blocked"):
        return 0.0
    base = {"R0": 0.96, "R1": 0.88, "R2": 0.74}.get(risk, 0.0)
    complexity_penalty = {
        "ten_god_mechanism": 0.02,
        "branch_time_activation": 0.03,
        "wealth_career_bridge": 0.05,
        "pattern_structure": 0.05,
        "core_strength_foundation": 0.01,
        "blind_lifa_palace": 0.06,
    }.get(topic_lane, 0.04)
    return round(max(0.0, base - complexity_penalty), 2)


def _sample_failure(sample: Dict[str, Any], failure_type: str, detail: str) -> Dict[str, str]:
    return {
        "case_id": str(sample.get("case_id") or ""),
        "knowledge_id": str(sample.get("knowledge_id") or ""),
        "failure_type": failure_type,
        "detail": detail,
    }


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_")


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts
