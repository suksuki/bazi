from __future__ import annotations

from typing import Any, Dict, List, Sequence

from v19.synthetic_validation.rule_audit_application import (
    build_p40_framework_rule_registry,
    run_p40_rule_audit_application_regression,
)


P41_CONDITION_TOPIC_BATCH_VERSION = "v19.p41.condition_topic_batches.v1"
P41_CONDITION_DEEP_EVAL_VERSION = "v19.p41.condition_deep_eval_dataset.v1"
P41_CONDITION_DEEP_REGRESSION_VERSION = "v19.p41.condition_deep_regression.v1"
P41_SMART_GATE_BATCH_VERSION = "v19.p41.smart_gate_candidate_batches.v1"
P41_TOPIC_BATCH_APPLICATION_REGRESSION_VERSION = "v19.p41.topic_batch_application_regression.v1"

P41_GUARDRAILS = [
    "P40_FRAMEWORK_REGISTRY_REQUIRED",
    "TOPIC_BATCH_DEEP_VALIDATION",
    "TEN_SAMPLE_MINIMUM_PER_CONDITION_CANDIDATE",
    "SMART_GATE_CANDIDATE_BATCH_ONLY",
    "ENGINE_DISABLED_BY_DEFAULT",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_DOMAIN_RESULT_PREDICTION",
]

P41_DEEP_SAMPLE_TYPES = [
    "positive_all_axes_present",
    "positive_rescue_path_present",
    "positive_same_layer_action_present",
    "negative_missing_source_layer",
    "negative_missing_action_path",
    "negative_capacity_insufficient",
    "negative_cross_layer_no_action",
    "negative_relation_name_no_transformation",
    "distractor_time_trigger_only",
    "distractor_hidden_stem_only",
]


def build_p41_condition_topic_batches() -> Dict[str, Any]:
    p40 = run_p40_rule_audit_application_regression()
    registry = build_p40_framework_rule_registry()
    candidates = [
        dict(row)
        for row in registry.get("items") or []
        if row.get("application_status") == "condition_model_queue_validated"
    ]
    batches = []
    for topic_lane in _topic_lane_order():
        items = [row for row in candidates if _topic_lane(row) == topic_lane]
        if not items:
            continue
        batches.append(_topic_batch(topic_lane, items, p40.get("status")))
    failures = []
    if p40.get("status") != "pass":
        failures.append({"failure_type": "p40_regression_not_passed", "detail": "P40 must pass before P41 topic batching."})
    if sum(row["candidate_count"] for row in batches) != len(candidates):
        failures.append({"failure_type": "topic_batch_candidate_mismatch", "detail": "Not every condition candidate was assigned to a topic batch."})
    return {
        "ok": not failures,
        "version": P41_CONDITION_TOPIC_BATCH_VERSION,
        "status": "condition_topic_batches_ready" if not failures else "condition_topic_batches_failed",
        "summary": {
            "p40_regression_status": p40.get("status"),
            "topic_batch_count": len(batches),
            "condition_candidate_count": len(candidates),
            "assigned_candidate_count": sum(row["candidate_count"] for row in batches),
            "activation_updated_count": 0,
            "engine_enabled_count": 0,
            "by_topic_lane": {row["topic_lane"]: row["candidate_count"] for row in batches},
        },
        "batches": batches,
        "failures": failures,
        "batch_policy": {
            "purpose": "Convert the validated P40 condition-model queue into topic-sized work units.",
            "next": "Each topic batch must pass P41 deep positive/negative synthetic samples before smart-gate candidacy.",
        },
        "guardrails": P41_GUARDRAILS,
    }


def build_p41_condition_deep_eval_dataset() -> Dict[str, Any]:
    batches = build_p41_condition_topic_batches()
    samples = [
        sample
        for batch in batches.get("batches") or []
        for item in batch.get("items") or []
        for sample in _deep_samples_for_item(item, str(batch.get("topic_lane") or "unknown"))
    ]
    return {
        "ok": batches.get("ok") is True,
        "version": P41_CONDITION_DEEP_EVAL_VERSION,
        "status": "condition_deep_eval_dataset_ready_no_activation",
        "summary": {
            "topic_batch_count": batches["summary"]["topic_batch_count"],
            "condition_candidate_count": batches["summary"]["condition_candidate_count"],
            "sample_count": len(samples),
            "min_samples_per_candidate": len(P41_DEEP_SAMPLE_TYPES) if batches["summary"]["condition_candidate_count"] else 0,
            "activation_updated_count": 0,
            "engine_enabled_count": 0,
            "by_topic_lane": _count_by(samples, "topic_lane"),
            "by_sample_type": _count_by(samples, "sample_type"),
            "by_polarity": _count_by(samples, "polarity"),
        },
        "samples": samples,
        "source_batch_summary": batches["summary"],
        "guardrails": P41_GUARDRAILS,
    }


def run_p41_condition_deep_regression() -> Dict[str, Any]:
    dataset = build_p41_condition_deep_eval_dataset()
    sample_results = [_evaluate_deep_sample(sample) for sample in dataset.get("samples") or []]
    failures = [failure for row in sample_results for failure in row.get("failures") or []]
    false_positive_count = sum(1 for row in sample_results if row.get("false_positive"))
    status = "pass" if dataset.get("ok") is True and not failures and false_positive_count == 0 else "fail"
    return {
        "ok": status == "pass",
        "version": P41_CONDITION_DEEP_REGRESSION_VERSION,
        "status": status,
        "summary": {
            "topic_batch_count": dataset["summary"]["topic_batch_count"],
            "condition_candidate_count": dataset["summary"]["condition_candidate_count"],
            "sample_count": len(sample_results),
            "sample_passed": sum(1 for row in sample_results if row.get("status") == "pass"),
            "sample_failed": sum(1 for row in sample_results if row.get("status") == "fail"),
            "false_positive_count": false_positive_count,
            "forbidden_text_failure_count": sum(
                1
                for failure in failures
                if failure.get("failure_type") == "forbidden_text_contract_failed"
            ),
            "activation_updated_count": 0,
            "engine_enabled_count": 0,
            "by_topic_lane": dataset["summary"]["by_topic_lane"],
            "by_sample_type": dataset["summary"]["by_sample_type"],
        },
        "samples": sample_results,
        "failures": failures,
        "guardrails": P41_GUARDRAILS,
    }


def build_p41_smart_gate_candidate_batches() -> Dict[str, Any]:
    batches = build_p41_condition_topic_batches()
    regression = run_p41_condition_deep_regression()
    sample_counts = regression["summary"]["by_topic_lane"]
    gate_batches = []
    for batch in batches.get("batches") or []:
        topic_lane = str(batch.get("topic_lane") or "unknown")
        gate_batches.append(
            {
                "gate_batch_id": f"p41.smart_gate.{topic_lane}",
                "topic_lane": topic_lane,
                "candidate_count": batch.get("candidate_count"),
                "sample_count": int(sample_counts.get(topic_lane, 0) or 0),
                "regression_status": regression.get("status"),
                "readiness_status": "smart_gate_candidate_ready" if regression.get("status") == "pass" else "blocked_by_deep_regression",
                "engine_enabled": False,
                "activation_allowed": False,
                "runtime_mutation": False,
                "candidate_rule_ids": batch.get("candidate_rule_ids") or [],
            }
        )
    return {
        "ok": batches.get("ok") is True and regression.get("ok") is True,
        "version": P41_SMART_GATE_BATCH_VERSION,
        "status": "smart_gate_candidate_batches_ready_no_activation",
        "summary": {
            "topic_batch_count": len(gate_batches),
            "gate_candidate_count": sum(int(row.get("candidate_count") or 0) for row in gate_batches),
            "deep_sample_count": regression["summary"]["sample_count"],
            "ready_batch_count": sum(1 for row in gate_batches if row.get("readiness_status") == "smart_gate_candidate_ready"),
            "blocked_batch_count": sum(1 for row in gate_batches if row.get("readiness_status") != "smart_gate_candidate_ready"),
            "activation_updated_count": 0,
            "engine_enabled_count": 0,
            "runtime_mutation": False,
            "by_topic_lane": {row["topic_lane"]: row["candidate_count"] for row in gate_batches},
        },
        "batches": gate_batches,
        "source_regression_summary": regression["summary"],
        "guardrails": P41_GUARDRAILS,
    }


def run_p41_topic_batch_application_regression() -> Dict[str, Any]:
    batches = build_p41_smart_gate_candidate_batches()
    failures = []
    if batches.get("ok") is not True:
        failures.append({"failure_type": "smart_gate_batch_not_ready", "detail": "P41 smart gate batches are not ready."})
    if batches["summary"]["engine_enabled_count"] != 0:
        failures.append({"failure_type": "engine_activation_not_allowed", "detail": "P41 cannot enable rule engines."})
    if batches["summary"]["runtime_mutation"] is not False:
        failures.append({"failure_type": "runtime_mutation_not_allowed", "detail": "P41 cannot mutate runtime inference."})
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P41_TOPIC_BATCH_APPLICATION_REGRESSION_VERSION,
        "status": status,
        "summary": {
            "topic_batch_count": batches["summary"]["topic_batch_count"],
            "gate_candidate_count": batches["summary"]["gate_candidate_count"],
            "deep_sample_count": batches["summary"]["deep_sample_count"],
            "ready_batch_count": batches["summary"]["ready_batch_count"],
            "blocked_batch_count": batches["summary"]["blocked_batch_count"],
            "activation_updated_count": 0,
            "engine_enabled_count": 0,
            "runtime_mutation": False,
        },
        "smart_gate_batches": batches,
        "failures": failures,
        "guardrails": P41_GUARDRAILS,
    }


def _topic_batch(topic_lane: str, items: List[Dict[str, Any]], p40_status: str) -> Dict[str, Any]:
    return {
        "topic_batch_id": f"p41.topic.{topic_lane}",
        "topic_lane": topic_lane,
        "p40_regression_status": p40_status,
        "candidate_count": len(items),
        "expected_deep_sample_count": len(items) * len(P41_DEEP_SAMPLE_TYPES),
        "minimum_samples_per_candidate": len(P41_DEEP_SAMPLE_TYPES),
        "engine_enabled": False,
        "activation_allowed": False,
        "candidate_rule_ids": [str(row.get("candidate_rule_id") or "") for row in items],
        "knowledge_ids": [str(row.get("knowledge_id") or "") for row in items],
        "items": items,
    }


def _deep_samples_for_item(item: Dict[str, Any], topic_lane: str) -> List[Dict[str, Any]]:
    return [_deep_sample_for_type(item, topic_lane, sample_type, index) for index, sample_type in enumerate(P41_DEEP_SAMPLE_TYPES, start=1)]


def _deep_sample_for_type(item: Dict[str, Any], topic_lane: str, sample_type: str, index: int) -> Dict[str, Any]:
    positive = sample_type.startswith("positive_")
    signal = str(item.get("expected_signal") or "")
    return {
        "case_id": f"p41.deep.{topic_lane}.{_slug(str(item.get('knowledge_id') or 'unknown'))}.{index}.{sample_type}",
        "topic_lane": topic_lane,
        "source_candidate_rule_id": str(item.get("candidate_rule_id") or ""),
        "knowledge_id": str(item.get("knowledge_id") or ""),
        "domain": str(item.get("domain") or "unknown"),
        "polarity": _polarity_for_sample_type(sample_type),
        "sample_type": sample_type,
        "expected_signal": signal if positive else "",
        "forbidden_signals": [] if positive else [signal],
        "condition_axes_expected": _sample_axes(sample_type, list(item.get("condition_axes_required") or [])),
        "expected_question_keys": list(item.get("expected_question_keys") or []),
        "forbidden_text": [] if positive else list(item.get("forbidden_outputs") or []),
        "audit_tags": ["p41_condition_topic_deep_validation", topic_lane, sample_type],
        "generated_answer_text": "",
    }


def _evaluate_deep_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    failures = []
    positive = str(sample.get("sample_type") or "").startswith("positive_")
    required = {
        "case_id",
        "topic_lane",
        "source_candidate_rule_id",
        "knowledge_id",
        "polarity",
        "sample_type",
        "expected_signal",
        "forbidden_signals",
        "condition_axes_expected",
        "expected_question_keys",
        "forbidden_text",
        "audit_tags",
    }
    missing = sorted(key for key in required if key not in sample)
    if missing:
        failures.append(_sample_failure(sample, "sample_schema_missing_fields", ",".join(missing)))
    if positive and not sample.get("expected_signal"):
        failures.append(_sample_failure(sample, "positive_signal_missing", "Positive deep sample requires expected signal."))
    if not positive and sample.get("expected_signal"):
        failures.append(_sample_failure(sample, "false_positive_signal", "Non-positive deep sample cannot expect positive signal."))
    if not positive and not sample.get("forbidden_signals"):
        failures.append(_sample_failure(sample, "forbidden_signal_missing", "Non-positive deep sample requires forbidden signal."))
    if not sample.get("condition_axes_expected"):
        failures.append(_sample_failure(sample, "condition_axes_missing", "Deep sample requires condition axes."))
    answer_text = str(sample.get("generated_answer_text") or "")
    for token in sample.get("forbidden_text") or []:
        if token and str(token) in answer_text:
            failures.append(_sample_failure(sample, "forbidden_text_contract_failed", str(token)))
            break
    return {
        "case_id": sample.get("case_id"),
        "topic_lane": sample.get("topic_lane"),
        "knowledge_id": sample.get("knowledge_id"),
        "sample_type": sample.get("sample_type"),
        "status": "fail" if failures else "pass",
        "false_positive": (not positive and bool(sample.get("expected_signal"))),
        "failures": failures,
    }


def _sample_axes(sample_type: str, axes: Sequence[str]) -> List[Dict[str, str]]:
    if sample_type == "positive_all_axes_present":
        return [{"axis": axis, "expected": "present"} for axis in axes]
    if sample_type == "positive_rescue_path_present":
        return [{"axis": "rescue_path", "expected": "present_or_explicitly_not_required"}]
    if sample_type == "positive_same_layer_action_present":
        return [{"axis": "same_layer_action", "expected": "present"}]
    if sample_type == "negative_missing_source_layer":
        return [{"axis": "source_layer", "expected": "missing_blocks_signal"}]
    if sample_type == "negative_missing_action_path":
        return [{"axis": "same_layer_action", "expected": "missing_blocks_signal"}]
    if sample_type == "negative_capacity_insufficient":
        return [{"axis": "capacity_strength", "expected": "insufficient_blocks_signal"}]
    if sample_type == "negative_cross_layer_no_action":
        return [{"axis": "source_layer", "expected": "cross_layer_without_action_path_blocks_signal"}]
    if sample_type == "negative_relation_name_no_transformation":
        return [{"axis": "same_layer_action", "expected": "relation_name_only_without_transform_or_control_blocks_signal"}]
    if sample_type == "distractor_time_trigger_only":
        return [{"axis": "time_layer", "expected": "trigger_context_only_no_natal_rewrite"}]
    return [{"axis": "hidden_stem_layer", "expected": "background_only_no_visible_signal"}]


def _polarity_for_sample_type(sample_type: str) -> str:
    if sample_type.startswith("positive_"):
        return "positive"
    if sample_type == "distractor_time_trigger_only":
        return "distractor_time"
    if sample_type == "distractor_hidden_stem_only":
        return "distractor_hidden"
    return "negative"


def _topic_lane(item: Dict[str, Any]) -> str:
    domain = str(item.get("domain") or "")
    knowledge_id = str(item.get("knowledge_id") or "")
    if domain in {"interaction", "ten_god"}:
        return "ten_god_mechanism"
    if domain == "pattern":
        return "pattern_structure"
    if domain in {"wealth", "career"}:
        return "wealth_career_bridge"
    if domain in {"blind", "palace"}:
        return "blind_lifa_palace"
    if domain == "luck_flow" or any(
        token in knowledge_id
        for token in ["branch", "time", "luck", "stem_combination", "vault", "month_command", "hidden_stem"]
    ):
        return "branch_time_activation"
    return "core_strength_foundation"


def _topic_lane_order() -> List[str]:
    return [
        "ten_god_mechanism",
        "branch_time_activation",
        "wealth_career_bridge",
        "pattern_structure",
        "core_strength_foundation",
        "blind_lifa_palace",
    ]


def _sample_failure(sample: Dict[str, Any], failure_type: str, detail: str) -> Dict[str, str]:
    return {
        "case_id": str(sample.get("case_id") or ""),
        "topic_lane": str(sample.get("topic_lane") or ""),
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
