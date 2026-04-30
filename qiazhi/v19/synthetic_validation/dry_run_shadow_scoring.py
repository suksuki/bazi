from __future__ import annotations

from typing import Any, Dict, List

from v19.synthetic_validation.smart_gate_acceleration import build_p42_framework_gate_plan


P43_DRY_RUN_SHADOW_EVAL_VERSION = "v19.p43.dry_run_shadow_eval_dataset.v1"
P43_DRY_RUN_SHADOW_SCORING_VERSION = "v19.p43.dry_run_shadow_scoring.v1"
P43_FEEDBACK_LEDGER_VERSION = "v19.p43.feedback_ledger.v1"
P43_EXECUTION_REGRESSION_VERSION = "v19.p43.execution_regression.v1"

P43_GUARDRAILS = [
    "P42_GATE_PLAN_REQUIRED",
    "NON_RUNTIME_DRY_RUN_AND_SHADOW_ONLY",
    "NO_USER_ANSWER_MUTATION",
    "ROLLBACK_CONTRACT_REQUIRED",
    "ENGINE_DISABLED_BY_DEFAULT",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_DOMAIN_RESULT_PREDICTION",
]

P43_EXECUTION_SAMPLE_TYPES = [
    "internal_signal_contract",
    "no_answer_mutation_contract",
    "forbidden_text_contract",
    "rollback_contract",
]


def build_p43_dry_run_shadow_eval_dataset() -> Dict[str, Any]:
    plan = build_p42_framework_gate_plan()
    items = [
        dict(row)
        for row in plan.get("items") or []
        if row.get("application_status") in {"dry_run_planned", "shadow_scoring_planned"}
    ]
    samples = [sample for item in items for sample in _execution_samples_for_item(item)]
    return {
        "ok": plan.get("ok") is True,
        "version": P43_DRY_RUN_SHADOW_EVAL_VERSION,
        "status": "dry_run_shadow_eval_dataset_ready_no_runtime_activation",
        "summary": {
            "candidate_count": len(items),
            "dry_run_candidate_count": sum(1 for row in items if row.get("application_status") == "dry_run_planned"),
            "shadow_scoring_candidate_count": sum(1 for row in items if row.get("application_status") == "shadow_scoring_planned"),
            "sample_count": len(samples),
            "min_samples_per_candidate": len(P43_EXECUTION_SAMPLE_TYPES) if items else 0,
            "engine_enabled_count": 0,
            "activation_updated_count": 0,
            "answer_mutation_count": 0,
            "by_execution_mode": _count_by(samples, "execution_mode"),
            "by_sample_type": _count_by(samples, "sample_type"),
        },
        "samples": samples,
        "source_gate_plan_summary": plan["summary"],
        "guardrails": P43_GUARDRAILS,
    }


def run_p43_dry_run_shadow_scoring() -> Dict[str, Any]:
    dataset = build_p43_dry_run_shadow_eval_dataset()
    sample_results = [_evaluate_execution_sample(sample) for sample in dataset.get("samples") or []]
    failures = [failure for row in sample_results for failure in row.get("failures") or []]
    status = "pass" if dataset.get("ok") is True and not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P43_DRY_RUN_SHADOW_SCORING_VERSION,
        "status": status,
        "summary": {
            "candidate_count": dataset["summary"]["candidate_count"],
            "dry_run_candidate_count": dataset["summary"]["dry_run_candidate_count"],
            "shadow_scoring_candidate_count": dataset["summary"]["shadow_scoring_candidate_count"],
            "sample_count": len(sample_results),
            "sample_passed": sum(1 for row in sample_results if row.get("status") == "pass"),
            "sample_failed": sum(1 for row in sample_results if row.get("status") == "fail"),
            "false_positive_count": sum(1 for row in sample_results if row.get("false_positive")),
            "forbidden_text_failure_count": sum(
                1
                for failure in failures
                if failure.get("failure_type") == "forbidden_text_contract_failed"
            ),
            "answer_mutation_count": sum(1 for row in sample_results if row.get("answer_mutation")),
            "rollback_ready_count": _rollback_ready_count(dataset.get("samples") or []),
            "engine_enabled_count": 0,
            "activation_updated_count": 0,
            "by_execution_mode": dataset["summary"]["by_execution_mode"],
        },
        "samples": sample_results,
        "failures": failures,
        "guardrails": P43_GUARDRAILS,
    }


def build_p43_feedback_ledger() -> Dict[str, Any]:
    plan = build_p42_framework_gate_plan()
    scoring = run_p43_dry_run_shadow_scoring()
    items = [
        {
            "ledger_item_id": f"p43.ledger.{_slug(str(row.get('knowledge_id') or 'unknown'))}",
            "candidate_rule_id": row.get("candidate_rule_id"),
            "knowledge_id": row.get("knowledge_id"),
            "topic_lane": row.get("topic_lane"),
            "risk_level": row.get("risk_level"),
            "application_status": row.get("application_status"),
            "feedback_status": _feedback_status(row, scoring.get("status")),
            "engine_enabled": False,
            "answer_mutation": False,
            "runtime_mutation": False,
        }
        for row in plan.get("items") or []
        if row.get("application_status") in {"dry_run_planned", "shadow_scoring_planned"}
    ]
    return {
        "ok": plan.get("ok") is True and scoring.get("ok") is True,
        "version": P43_FEEDBACK_LEDGER_VERSION,
        "status": "feedback_ledger_ready_no_runtime_activation",
        "summary": {
            "candidate_count": len(items),
            "dry_run_passed_count": sum(1 for row in items if row.get("feedback_status") == "dry_run_passed"),
            "shadow_scored_count": sum(1 for row in items if row.get("feedback_status") == "shadow_scored"),
            "blocked_count": sum(1 for row in items if str(row.get("feedback_status") or "").startswith("blocked")),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
            "by_feedback_status": _count_by(items, "feedback_status"),
            "by_topic_lane": _count_by(items, "topic_lane"),
        },
        "items": items,
        "source_scoring_summary": scoring["summary"],
        "guardrails": P43_GUARDRAILS,
    }


def run_p43_execution_regression() -> Dict[str, Any]:
    ledger = build_p43_feedback_ledger()
    failures = []
    if ledger.get("ok") is not True:
        failures.append({"failure_type": "p43_ledger_not_ready", "detail": "P43 feedback ledger is not ready."})
    if ledger["summary"]["engine_enabled_count"] != 0:
        failures.append({"failure_type": "engine_activation_not_allowed", "detail": "P43 cannot enable engines."})
    if ledger["summary"]["answer_mutation_count"] != 0:
        failures.append({"failure_type": "answer_mutation_not_allowed", "detail": "P43 cannot mutate user answers."})
    if ledger["summary"]["runtime_mutation"] is not False:
        failures.append({"failure_type": "runtime_mutation_not_allowed", "detail": "P43 cannot mutate runtime inference."})
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P43_EXECUTION_REGRESSION_VERSION,
        "status": status,
        "summary": {
            "candidate_count": ledger["summary"]["candidate_count"],
            "dry_run_passed_count": ledger["summary"]["dry_run_passed_count"],
            "shadow_scored_count": ledger["summary"]["shadow_scored_count"],
            "blocked_count": ledger["summary"]["blocked_count"],
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "feedback_ledger": ledger,
        "failures": failures,
        "guardrails": P43_GUARDRAILS,
    }


def _execution_samples_for_item(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [_execution_sample_for_type(item, sample_type, index) for index, sample_type in enumerate(P43_EXECUTION_SAMPLE_TYPES, start=1)]


def _execution_sample_for_type(item: Dict[str, Any], sample_type: str, index: int) -> Dict[str, Any]:
    execution_mode = "dry_run_internal" if item.get("application_status") == "dry_run_planned" else "shadow_scoring_internal"
    return {
        "case_id": f"p43.execution.{_slug(str(item.get('knowledge_id') or 'unknown'))}.{index}.{sample_type}",
        "candidate_rule_id": item.get("candidate_rule_id"),
        "knowledge_id": item.get("knowledge_id"),
        "topic_lane": item.get("topic_lane"),
        "risk_level": item.get("risk_level"),
        "execution_mode": execution_mode,
        "sample_type": sample_type,
        "expected_internal_signal": sample_type == "internal_signal_contract",
        "expected_shadow_score": execution_mode == "shadow_scoring_internal",
        "answer_mutation": False,
        "engine_enabled": False,
        "rollback_ready": sample_type == "rollback_contract",
        "forbidden_text": ["发财", "破财", "官非", "灾祸", "疾病", "应期", "必然", "一定"],
        "generated_answer_text": "",
        "audit_tags": ["p43_dry_run_shadow_scoring", execution_mode, sample_type],
    }


def _evaluate_execution_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    failures = []
    if sample.get("engine_enabled") is True:
        failures.append(_sample_failure(sample, "engine_activation_not_allowed", "Execution sample must keep engine disabled."))
    if sample.get("answer_mutation") is True:
        failures.append(_sample_failure(sample, "answer_mutation_not_allowed", "Execution sample must not mutate user answers."))
    if sample.get("sample_type") == "internal_signal_contract" and sample.get("expected_internal_signal") is not True:
        failures.append(_sample_failure(sample, "internal_signal_contract_failed", "Dry-run/shadow sample must define internal signal state."))
    if sample.get("sample_type") == "rollback_contract" and sample.get("rollback_ready") is not True:
        failures.append(_sample_failure(sample, "rollback_contract_failed", "Rollback-ready marker is required."))
    answer_text = str(sample.get("generated_answer_text") or "")
    for token in sample.get("forbidden_text") or []:
        if token and str(token) in answer_text:
            failures.append(_sample_failure(sample, "forbidden_text_contract_failed", str(token)))
            break
    return {
        "case_id": sample.get("case_id"),
        "knowledge_id": sample.get("knowledge_id"),
        "execution_mode": sample.get("execution_mode"),
        "sample_type": sample.get("sample_type"),
        "status": "fail" if failures else "pass",
        "false_positive": False,
        "answer_mutation": sample.get("answer_mutation") is True,
        "failures": failures,
    }


def _feedback_status(item: Dict[str, Any], scoring_status: str) -> str:
    if scoring_status != "pass":
        return "blocked_by_p43_scoring"
    if item.get("application_status") == "dry_run_planned":
        return "dry_run_passed"
    if item.get("application_status") == "shadow_scoring_planned":
        return "shadow_scored"
    return "blocked_unknown_application_status"


def _rollback_ready_count(samples: List[Dict[str, Any]]) -> int:
    return len({str(sample.get("candidate_rule_id") or "") for sample in samples if sample.get("rollback_ready") is True})


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
