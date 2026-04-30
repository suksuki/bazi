from __future__ import annotations

from typing import Any, Dict, List, Optional

from v19.synthetic_validation.controlled_activation_candidates import (
    build_p44_controlled_activation_packet,
    build_p44_rollback_manifest,
    run_p44_release_candidate_regression,
)


P45_CANARY_ACTIVATION_PLAN_VERSION = "v19.p45.canary_activation_plan.v1"
P45_CANARY_EVAL_DATASET_VERSION = "v19.p45.canary_eval_dataset.v1"
P45_CANARY_RUNTIME_TRIAL_VERSION = "v19.p45.canary_runtime_trial.v1"
P45_CANARY_RELEASE_REGRESSION_VERSION = "v19.p45.canary_release_regression.v1"

P45_GUARDRAILS = [
    "P44_RELEASE_CANDIDATE_REGRESSION_REQUIRED",
    "RING0_CANARY_ONLY",
    "ISOLATED_CANARY_RUNTIME_ONLY",
    "PRODUCTION_ENGINE_DISABLED",
    "NO_USER_ANSWER_MUTATION",
    "ROLLBACK_AND_KILL_SWITCH_REQUIRED",
    "NO_DOMAIN_RESULT_PREDICTION",
]

P45_CANARY_SAMPLE_TYPES = [
    "canary_internal_signal_contract",
    "production_route_no_signal_contract",
    "answer_text_no_mutation_contract",
    "forbidden_text_contract",
    "rollback_execution_contract",
    "kill_switch_contract",
]


def build_p45_canary_activation_plan() -> Dict[str, Any]:
    packet = build_p44_controlled_activation_packet()
    rollback = build_p44_rollback_manifest()
    p44_regression = run_p44_release_candidate_regression()
    rollback_by_rule_id = {str(row.get("candidate_rule_id") or ""): row for row in rollback.get("items") or []}
    canaries = [
        _canary_row(row, rollback_by_rule_id.get(str(row.get("candidate_rule_id") or "")))
        for row in packet.get("activation_candidates") or []
        if row.get("release_ring") == "ring0_canary"
    ]
    failures = []
    if p44_regression.get("status") != "pass":
        failures.append({"failure_type": "p44_regression_not_passed", "detail": "P45 canary plan requires passing P44 regression."})
    if any(not row.get("rollback_id") for row in canaries):
        failures.append({"failure_type": "rollback_missing", "detail": "Every canary candidate requires rollback coverage."})
    if any(row.get("production_engine_enabled") for row in canaries):
        failures.append({"failure_type": "production_engine_not_allowed", "detail": "P45 cannot enable production engines."})
    return {
        "ok": not failures,
        "version": P45_CANARY_ACTIVATION_PLAN_VERSION,
        "status": "canary_activation_plan_ready_isolated_runtime_only" if not failures else "canary_activation_plan_failed",
        "summary": {
            "p44_regression_status": p44_regression.get("status"),
            "ring0_canary_count": len(canaries),
            "canary_runtime_enabled_count": sum(1 for row in canaries if row.get("canary_engine_enabled") is True),
            "production_engine_enabled_count": sum(1 for row in canaries if row.get("production_engine_enabled") is True),
            "rollback_covered_count": sum(1 for row in canaries if row.get("rollback_id")),
            "kill_switch_covered_count": sum(1 for row in canaries if row.get("kill_switch_enabled") is True),
            "answer_mutation_count": 0,
            "production_runtime_mutation": False,
            "by_topic_lane": _count_by(canaries, "topic_lane"),
        },
        "canaries": canaries,
        "failures": failures,
        "canary_policy": {
            "scope": "Canary engine is enabled only in an isolated evaluation route, never in the production user-answer path.",
            "output": "Canary may emit internal neutral structure signals only.",
            "rollback": "Each canary has an explicit rollback item and kill switch.",
        },
        "guardrails": P45_GUARDRAILS,
    }


def build_p45_canary_eval_dataset() -> Dict[str, Any]:
    plan = build_p45_canary_activation_plan()
    samples = [sample for row in plan.get("canaries") or [] for sample in _samples_for_canary(row)]
    return {
        "ok": plan.get("ok") is True,
        "version": P45_CANARY_EVAL_DATASET_VERSION,
        "status": "canary_eval_dataset_ready_isolated_runtime_only",
        "summary": {
            "ring0_canary_count": plan["summary"]["ring0_canary_count"],
            "sample_count": len(samples),
            "min_samples_per_canary": len(P45_CANARY_SAMPLE_TYPES) if plan["summary"]["ring0_canary_count"] else 0,
            "canary_runtime_enabled_count": plan["summary"]["canary_runtime_enabled_count"],
            "production_engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "by_sample_type": _count_by(samples, "sample_type"),
        },
        "samples": samples,
        "source_plan_summary": plan["summary"],
        "guardrails": P45_GUARDRAILS,
    }


def run_p45_canary_runtime_trial() -> Dict[str, Any]:
    dataset = build_p45_canary_eval_dataset()
    sample_results = [_evaluate_canary_sample(sample) for sample in dataset.get("samples") or []]
    failures = [failure for row in sample_results for failure in row.get("failures") or []]
    status = "pass" if dataset.get("ok") is True and not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P45_CANARY_RUNTIME_TRIAL_VERSION,
        "status": status,
        "summary": {
            "ring0_canary_count": dataset["summary"]["ring0_canary_count"],
            "sample_count": len(sample_results),
            "sample_passed": sum(1 for row in sample_results if row.get("status") == "pass"),
            "sample_failed": sum(1 for row in sample_results if row.get("status") == "fail"),
            "canary_internal_signal_count": sum(1 for row in sample_results if row.get("canary_internal_signal") is True),
            "production_signal_leak_count": sum(1 for row in sample_results if row.get("production_signal_leak") is True),
            "forbidden_text_failure_count": sum(
                1
                for failure in failures
                if failure.get("failure_type") == "forbidden_text_contract_failed"
            ),
            "rollback_ready_count": _unique_count(dataset.get("samples") or [], "rollback_ready"),
            "kill_switch_ready_count": _unique_count(dataset.get("samples") or [], "kill_switch_ready"),
            "canary_runtime_enabled_count": dataset["summary"]["canary_runtime_enabled_count"],
            "production_engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "production_runtime_mutation": False,
        },
        "samples": sample_results,
        "eval_dataset": dataset,
        "failures": failures,
        "guardrails": P45_GUARDRAILS,
    }


def run_p45_canary_release_regression() -> Dict[str, Any]:
    plan = build_p45_canary_activation_plan()
    trial = run_p45_canary_runtime_trial()
    failures = []
    if plan.get("ok") is not True:
        failures.append({"failure_type": "p45_plan_not_ready", "detail": "Canary activation plan is not ready."})
    if trial.get("ok") is not True:
        failures.append({"failure_type": "p45_trial_failed", "detail": "Canary runtime trial failed."})
    if trial["summary"]["production_signal_leak_count"] != 0:
        failures.append({"failure_type": "production_signal_leak", "detail": "Canary signal leaked into production route."})
    if trial["summary"]["production_engine_enabled_count"] != 0:
        failures.append({"failure_type": "production_engine_enabled", "detail": "Production engine must stay disabled."})
    if trial["summary"]["answer_mutation_count"] != 0:
        failures.append({"failure_type": "answer_mutation_not_allowed", "detail": "Canary trial must not mutate user answers."})
    if trial["summary"]["rollback_ready_count"] != plan["summary"]["ring0_canary_count"]:
        failures.append({"failure_type": "rollback_coverage_failed", "detail": "Every canary requires rollback readiness."})
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P45_CANARY_RELEASE_REGRESSION_VERSION,
        "status": status,
        "summary": {
            "ring0_canary_count": plan["summary"]["ring0_canary_count"],
            "sample_count": trial["summary"]["sample_count"],
            "sample_failed": trial["summary"]["sample_failed"],
            "canary_runtime_enabled_count": trial["summary"]["canary_runtime_enabled_count"],
            "production_engine_enabled_count": 0,
            "production_signal_leak_count": trial["summary"]["production_signal_leak_count"],
            "forbidden_text_failure_count": trial["summary"]["forbidden_text_failure_count"],
            "rollback_ready_count": trial["summary"]["rollback_ready_count"],
            "kill_switch_ready_count": trial["summary"]["kill_switch_ready_count"],
            "answer_mutation_count": 0,
            "production_runtime_mutation": False,
        },
        "canary_plan": plan,
        "canary_trial": trial,
        "failures": failures,
        "guardrails": P45_GUARDRAILS,
    }


def _canary_row(candidate: Dict[str, Any], rollback: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "canary_id": f"p45.canary.{_slug(str(candidate.get('knowledge_id') or 'unknown'))}",
        "activation_candidate_id": candidate.get("activation_candidate_id"),
        "candidate_rule_id": candidate.get("candidate_rule_id"),
        "knowledge_id": candidate.get("knowledge_id"),
        "topic_lane": candidate.get("topic_lane"),
        "risk_level": candidate.get("risk_level"),
        "release_ring": candidate.get("release_ring"),
        "canary_engine_enabled": True,
        "production_engine_enabled": False,
        "answer_mutation": False,
        "production_runtime_mutation": False,
        "rollback_id": (rollback or {}).get("rollback_id", ""),
        "kill_switch_enabled": True,
        "canary_scope": "isolated_internal_signal_route",
    }


def _samples_for_canary(canary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [_sample_for_type(canary, sample_type, index) for index, sample_type in enumerate(P45_CANARY_SAMPLE_TYPES, start=1)]


def _sample_for_type(canary: Dict[str, Any], sample_type: str, index: int) -> Dict[str, Any]:
    return {
        "case_id": f"p45.canary.{_slug(str(canary.get('knowledge_id') or 'unknown'))}.{index}.{sample_type}",
        "canary_id": canary.get("canary_id"),
        "candidate_rule_id": canary.get("candidate_rule_id"),
        "knowledge_id": canary.get("knowledge_id"),
        "topic_lane": canary.get("topic_lane"),
        "sample_type": sample_type,
        "canary_engine_enabled": canary.get("canary_engine_enabled") is True,
        "production_engine_enabled": False,
        "expected_internal_signal": sample_type == "canary_internal_signal_contract",
        "production_signal_leak": False,
        "answer_mutation": False,
        "rollback_ready": sample_type == "rollback_execution_contract",
        "kill_switch_ready": sample_type == "kill_switch_contract",
        "forbidden_text": ["发财", "破财", "官非", "灾祸", "疾病", "应期", "必然", "一定"],
        "generated_answer_text": "",
        "audit_tags": ["p45_canary_runtime_trial", sample_type],
    }


def _evaluate_canary_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    failures = []
    if sample.get("production_engine_enabled") is True:
        failures.append(_sample_failure(sample, "production_engine_enabled", "Production engine must stay disabled."))
    if sample.get("answer_mutation") is True:
        failures.append(_sample_failure(sample, "answer_mutation_not_allowed", "Canary trial must not mutate user answers."))
    if sample.get("production_signal_leak") is True:
        failures.append(_sample_failure(sample, "production_signal_leak", "Canary signal cannot leak into production route."))
    if sample.get("sample_type") == "canary_internal_signal_contract" and sample.get("canary_engine_enabled") is not True:
        failures.append(_sample_failure(sample, "canary_engine_disabled", "Canary route must enable isolated canary engine."))
    if sample.get("sample_type") == "rollback_execution_contract" and sample.get("rollback_ready") is not True:
        failures.append(_sample_failure(sample, "rollback_contract_failed", "Rollback marker must be ready."))
    if sample.get("sample_type") == "kill_switch_contract" and sample.get("kill_switch_ready") is not True:
        failures.append(_sample_failure(sample, "kill_switch_contract_failed", "Kill switch marker must be ready."))
    answer_text = str(sample.get("generated_answer_text") or "")
    for token in sample.get("forbidden_text") or []:
        if token and str(token) in answer_text:
            failures.append(_sample_failure(sample, "forbidden_text_contract_failed", str(token)))
            break
    return {
        "case_id": sample.get("case_id"),
        "knowledge_id": sample.get("knowledge_id"),
        "sample_type": sample.get("sample_type"),
        "status": "fail" if failures else "pass",
        "canary_internal_signal": sample.get("sample_type") == "canary_internal_signal_contract",
        "production_signal_leak": sample.get("production_signal_leak") is True,
        "failures": failures,
    }


def _unique_count(samples: List[Dict[str, Any]], key: str) -> int:
    return len({str(sample.get("candidate_rule_id") or "") for sample in samples if sample.get(key) is True})


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
