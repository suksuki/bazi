from __future__ import annotations

from typing import Any, Dict, List, Sequence

from v19.synthetic_validation.rule_conversion_validation import (
    P39_ELIGIBLE_RISKS,
    build_p39_rule_conversion_candidates,
    run_p39_rule_conversion_regression,
)


P40_RULE_AUDIT_APPLICATION_VERSION = "v19.p40.rule_audit_application.v1"
P40_CONDITION_SYNTHETIC_DATASET_VERSION = "v19.p40.condition_model_synthetic_dataset.v1"
P40_CONDITION_SYNTHETIC_REGRESSION_VERSION = "v19.p40.condition_model_synthetic_regression.v1"
P40_FRAMEWORK_REGISTRY_VERSION = "v19.p40.framework_rule_registry.v1"
P40_RULE_AUDIT_APPLICATION_REGRESSION_VERSION = "v19.p40.rule_audit_application_regression.v1"

P40_GUARDRAILS = [
    "RULE_AUDIT_BEFORE_FRAMEWORK_APPLICATION",
    "P39_REGRESSION_REQUIRED",
    "NON_PREDICTIVE_CONTRACTS_ONLY",
    "CONDITION_MODELS_REQUIRE_SYNTHETIC_VALIDATION",
    "ENGINE_DISABLED_BY_DEFAULT",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_DOMAIN_RESULT_PREDICTION",
]

P40_CONDITION_SAMPLE_TYPES = [
    "positive_all_axes_present",
    "negative_missing_action_path",
    "distractor_time_only",
    "distractor_hidden_only",
]


def build_p40_rule_audit_report() -> Dict[str, Any]:
    registry = build_p39_rule_conversion_candidates()
    p39_regression = run_p39_rule_conversion_regression()
    candidates = list(registry.get("candidates") or [])
    audit_items = [_audit_candidate(candidate, p39_regression) for candidate in candidates]
    failures = [failure for row in audit_items for failure in row.get("failures") or []]
    return {
        "ok": not failures and p39_regression.get("status") == "pass",
        "version": P40_RULE_AUDIT_APPLICATION_VERSION,
        "status": "rule_audit_ready" if not failures and p39_regression.get("status") == "pass" else "rule_audit_failed",
        "summary": {
            "p39_regression_status": p39_regression.get("status"),
            "candidate_count": len(candidates),
            "blocked_high_risk_count": registry["summary"]["blocked_count"],
            "audit_failed_count": len(failures),
            "framework_contract_ready_count": sum(1 for row in audit_items if row["audit_status"] == "framework_contract_ready"),
            "condition_synthetic_required_count": sum(1 for row in audit_items if row["audit_status"] == "condition_synthetic_required"),
            "engine_enabled_count": sum(1 for row in audit_items if row.get("engine_enabled") is True),
            "activation_updated_count": 0,
            "by_audit_status": _count_by(audit_items, "audit_status"),
            "by_application_lane": _count_by(audit_items, "framework_application_lane"),
            "by_conversion_mode": _count_by(audit_items, "conversion_mode"),
        },
        "items": audit_items,
        "failures": failures,
        "application_policy": {
            "framework_contract_ready": "Non-predictive answer/governance/metadata contracts can be registered into the framework with engine disabled.",
            "condition_synthetic_required": "Structure mechanism candidates must pass synthetic validation before entering the condition-model framework queue.",
            "blocked_high_risk": "R3/R4 knowledge stays outside P40 and remains archive or specialist review work.",
        },
        "guardrails": P40_GUARDRAILS,
    }


def build_p40_condition_model_synthetic_dataset() -> Dict[str, Any]:
    audit = build_p40_rule_audit_report()
    condition_items = [row for row in audit.get("items") or [] if row.get("audit_status") == "condition_synthetic_required"]
    samples = [sample for item in condition_items for sample in _condition_samples_for_item(item)]
    return {
        "ok": audit.get("ok") is True,
        "version": P40_CONDITION_SYNTHETIC_DATASET_VERSION,
        "status": "condition_synthetic_dataset_ready_no_activation",
        "summary": {
            "source_candidate_count": len(condition_items),
            "sample_count": len(samples),
            "min_samples_per_candidate": len(P40_CONDITION_SAMPLE_TYPES) if condition_items else 0,
            "activation_updated_count": 0,
            "by_sample_type": _count_by(samples, "sample_type"),
            "by_polarity": _count_by(samples, "polarity"),
            "by_domain": _count_by(samples, "domain"),
        },
        "samples": samples,
        "source_audit_summary": audit["summary"],
        "guardrails": P40_GUARDRAILS,
    }


def run_p40_condition_model_synthetic_regression() -> Dict[str, Any]:
    dataset = build_p40_condition_model_synthetic_dataset()
    sample_results = [_evaluate_condition_sample(sample) for sample in dataset.get("samples") or []]
    failures = [failure for row in sample_results for failure in row.get("failures") or []]
    false_positive_count = sum(1 for row in sample_results if row.get("false_positive"))
    status = "pass" if not failures and false_positive_count == 0 and dataset.get("ok") is True else "fail"
    return {
        "ok": status == "pass",
        "version": P40_CONDITION_SYNTHETIC_REGRESSION_VERSION,
        "status": status,
        "summary": {
            "source_candidate_count": dataset["summary"]["source_candidate_count"],
            "sample_count": len(sample_results),
            "sample_passed": sum(1 for row in sample_results if row.get("status") == "pass"),
            "sample_failed": sum(1 for row in sample_results if row.get("status") == "fail"),
            "false_positive_count": false_positive_count,
            "activation_updated_count": 0,
            "by_sample_type": dataset["summary"]["by_sample_type"],
        },
        "samples": sample_results,
        "failures": failures,
        "guardrails": P40_GUARDRAILS,
    }


def build_p40_framework_rule_registry() -> Dict[str, Any]:
    audit = build_p40_rule_audit_report()
    synthetic = run_p40_condition_model_synthetic_regression()
    return _framework_registry(audit, synthetic)


def run_p40_rule_audit_application_regression() -> Dict[str, Any]:
    audit = build_p40_rule_audit_report()
    synthetic = run_p40_condition_model_synthetic_regression()
    registry = _framework_registry(audit, synthetic)
    failures = []
    failures.extend(audit.get("failures") or [])
    failures.extend(synthetic.get("failures") or [])
    if registry["summary"]["engine_enabled_count"] != 0:
        failures.append({"failure_type": "engine_activation_not_allowed", "detail": "P40 framework application must keep all engines disabled."})
    if registry["summary"]["runtime_mutation"] is not False:
        failures.append({"failure_type": "runtime_mutation_not_allowed", "detail": "P40 must not mutate runtime inference."})
    status = "pass" if audit.get("ok") and synthetic.get("ok") and not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P40_RULE_AUDIT_APPLICATION_REGRESSION_VERSION,
        "status": status,
        "summary": {
            "candidate_count": audit["summary"]["candidate_count"],
            "blocked_high_risk_count": audit["summary"]["blocked_high_risk_count"],
            "framework_registered_count": registry["summary"]["framework_registered_count"],
            "framework_contract_applied_count": registry["summary"]["framework_contract_applied_count"],
            "condition_model_queue_count": registry["summary"]["condition_model_queue_count"],
            "condition_synthetic_sample_count": synthetic["summary"]["sample_count"],
            "audit_failed_count": audit["summary"]["audit_failed_count"],
            "condition_synthetic_failed_count": synthetic["summary"]["sample_failed"],
            "false_positive_count": synthetic["summary"]["false_positive_count"],
            "engine_enabled_count": registry["summary"]["engine_enabled_count"],
            "activation_updated_count": 0,
            "runtime_mutation": False,
        },
        "audit": audit,
        "condition_synthetic": synthetic,
        "framework_registry": registry,
        "failures": failures,
        "guardrails": P40_GUARDRAILS,
    }


def _audit_candidate(candidate: Dict[str, Any], p39_regression: Dict[str, Any]) -> Dict[str, Any]:
    conversion_mode = str(candidate.get("conversion_mode") or "")
    lane = _application_lane(conversion_mode)
    failures = []
    if p39_regression.get("status") != "pass":
        failures.append(_failure(candidate, "p39_regression_not_passed", "P39 regression must pass before P40 audit."))
    if candidate.get("risk_level") not in P39_ELIGIBLE_RISKS:
        failures.append(_failure(candidate, "risk_gate_failed", "Only R0/R1/R2 candidates may enter P40 audit."))
    if candidate.get("engine_enabled") is True or candidate.get("activation_allowed") is True:
        failures.append(_failure(candidate, "activation_contract_failed", "P40 audit cannot receive active rules."))
    for key in ["condition_axes_required", "expected_question_keys", "forbidden_outputs", "answer_boundary"]:
        if not candidate.get(key):
            failures.append(_failure(candidate, f"{key}_missing", f"Candidate is missing {key}."))
    requires_synthetic = conversion_mode == "condition_model_candidate"
    if failures:
        status = "audit_failed"
    elif requires_synthetic:
        status = "condition_synthetic_required"
    else:
        status = "framework_contract_ready"
    return {
        "audit_id": f"p40.audit.{_slug(str(candidate.get('knowledge_id') or 'unknown'))}",
        "candidate_rule_id": str(candidate.get("candidate_rule_id") or ""),
        "knowledge_id": str(candidate.get("knowledge_id") or ""),
        "title": str(candidate.get("title") or ""),
        "domain": str(candidate.get("domain") or "unknown"),
        "risk_level": str(candidate.get("risk_level") or "unknown"),
        "conversion_mode": conversion_mode,
        "framework_application_lane": lane,
        "framework_model": str(candidate.get("framework_model") or ""),
        "condition_axes_required": list(candidate.get("condition_axes_required") or []),
        "expected_signal": str(candidate.get("expected_signal") or ""),
        "expected_question_keys": list(candidate.get("expected_question_keys") or []),
        "forbidden_outputs": list(candidate.get("forbidden_outputs") or []),
        "answer_boundary": str(candidate.get("answer_boundary") or ""),
        "requires_synthetic_validation": requires_synthetic,
        "audit_status": status,
        "engine_enabled": False,
        "activation_allowed": False,
        "failures": failures,
    }


def _framework_registry(audit: Dict[str, Any], synthetic: Dict[str, Any]) -> Dict[str, Any]:
    items = []
    synthetic_passed = synthetic.get("status") == "pass"
    for row in audit.get("items") or []:
        if row.get("audit_status") == "audit_failed":
            continue
        if row.get("audit_status") == "condition_synthetic_required":
            status = "condition_model_queue_validated" if synthetic_passed else "condition_model_queue_waiting_synthetic"
        else:
            status = "framework_contract_applied"
        items.append(
            {
                "framework_application_id": f"p40.framework.{_slug(str(row.get('knowledge_id') or 'unknown'))}",
                "audit_id": row.get("audit_id"),
                "candidate_rule_id": row.get("candidate_rule_id"),
                "knowledge_id": row.get("knowledge_id"),
                "domain": row.get("domain"),
                "risk_level": row.get("risk_level"),
                "framework_application_lane": row.get("framework_application_lane"),
                "framework_model": row.get("framework_model"),
                "application_status": status,
                "condition_axes_required": row.get("condition_axes_required") or [],
                "expected_signal": row.get("expected_signal"),
                "expected_question_keys": row.get("expected_question_keys") or [],
                "forbidden_outputs": row.get("forbidden_outputs") or [],
                "engine_enabled": False,
                "activation_allowed": False,
                "runtime_mutation": False,
            }
        )
    return {
        "ok": audit.get("ok") is True and synthetic.get("ok") is True,
        "version": P40_FRAMEWORK_REGISTRY_VERSION,
        "status": "framework_registry_ready_no_runtime_activation",
        "summary": {
            "framework_registered_count": len(items),
            "framework_contract_applied_count": sum(1 for row in items if row["application_status"] == "framework_contract_applied"),
            "condition_model_queue_count": sum(1 for row in items if row["application_status"].startswith("condition_model_queue")),
            "condition_model_queue_validated_count": sum(1 for row in items if row["application_status"] == "condition_model_queue_validated"),
            "engine_enabled_count": sum(1 for row in items if row.get("engine_enabled") is True),
            "activation_updated_count": 0,
            "runtime_mutation": False,
            "by_application_status": _count_by(items, "application_status"),
            "by_application_lane": _count_by(items, "framework_application_lane"),
        },
        "items": items,
        "source_audit_summary": audit["summary"],
        "source_synthetic_summary": synthetic["summary"],
        "guardrails": P40_GUARDRAILS,
    }


def _condition_samples_for_item(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [_condition_sample_for_type(item, sample_type, index) for index, sample_type in enumerate(P40_CONDITION_SAMPLE_TYPES, start=1)]


def _condition_sample_for_type(item: Dict[str, Any], sample_type: str, index: int) -> Dict[str, Any]:
    positive = sample_type == "positive_all_axes_present"
    signal = str(item.get("expected_signal") or "")
    axes = list(item.get("condition_axes_required") or [])
    sample = {
        "case_id": f"p40.condition.{_slug(str(item.get('knowledge_id') or 'unknown'))}.{index}.{sample_type}",
        "audit_id": str(item.get("audit_id") or ""),
        "source_candidate_rule_id": str(item.get("candidate_rule_id") or ""),
        "knowledge_id": str(item.get("knowledge_id") or ""),
        "domain": str(item.get("domain") or "unknown"),
        "polarity": "positive" if positive else _polarity_for_sample_type(sample_type),
        "sample_type": sample_type,
        "expected_signal": signal if positive else "",
        "forbidden_signals": [] if positive else [signal],
        "condition_axes_expected": _sample_axes(sample_type, axes),
        "forbidden_text": [] if positive else list(item.get("forbidden_outputs") or []),
        "expected_question_keys": list(item.get("expected_question_keys") or []),
        "audit_tags": ["p40_condition_model_synthetic", f"mode:{item.get('conversion_mode')}", sample_type],
        "generated_answer_text": "",
    }
    return sample


def _evaluate_condition_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    failures = []
    positive = sample.get("sample_type") == "positive_all_axes_present"
    if positive and not sample.get("expected_signal"):
        failures.append(_sample_failure(sample, "positive_signal_missing", "Positive sample requires expected signal."))
    if not positive and sample.get("expected_signal"):
        failures.append(_sample_failure(sample, "false_positive_signal", "Non-positive sample cannot expect positive signal."))
    if not positive and not sample.get("forbidden_signals"):
        failures.append(_sample_failure(sample, "forbidden_signal_missing", "Non-positive sample requires forbidden signal."))
    if not sample.get("condition_axes_expected"):
        failures.append(_sample_failure(sample, "condition_axes_missing", "Synthetic sample requires condition axes."))
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
        "false_positive": (not positive and bool(sample.get("expected_signal"))),
        "failures": failures,
    }


def _application_lane(conversion_mode: str) -> str:
    return {
        "answer_expression_contract": "answer_governance_framework",
        "governance_gate_contract": "review_gate_framework",
        "metadata_boundary_rule": "metadata_boundary_framework",
        "archive_metadata_candidate": "archive_neutral_tag_framework",
        "metadata_seed_rule_candidate": "metadata_seed_framework",
        "condition_model_candidate": "condition_model_framework_queue",
    }.get(conversion_mode, "metadata_seed_framework")


def _sample_axes(sample_type: str, axes: Sequence[str]) -> List[Dict[str, str]]:
    if sample_type == "positive_all_axes_present":
        return [{"axis": axis, "expected": "present"} for axis in axes]
    if sample_type == "negative_missing_action_path":
        return [{"axis": "same_layer_action", "expected": "missing_blocks_signal"}]
    if sample_type == "distractor_time_only":
        return [{"axis": "time_layer", "expected": "does_not_rewrite_natal_or_trigger_without_base_axes"}]
    return [{"axis": "hidden_stem_layer", "expected": "does_not_trigger_visible_signal_without_action_path"}]


def _polarity_for_sample_type(sample_type: str) -> str:
    if sample_type == "distractor_time_only":
        return "distractor_time"
    if sample_type == "distractor_hidden_only":
        return "distractor_hidden"
    return "negative"


def _failure(candidate: Dict[str, Any], failure_type: str, detail: str) -> Dict[str, str]:
    return {
        "candidate_rule_id": str(candidate.get("candidate_rule_id") or ""),
        "knowledge_id": str(candidate.get("knowledge_id") or ""),
        "failure_type": failure_type,
        "detail": detail,
    }


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
