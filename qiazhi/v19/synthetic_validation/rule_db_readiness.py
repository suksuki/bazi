from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List

from v19 import bazi_rule_db
from v19.synthetic_validation.guided_cases import make_synthetic_chart, make_synthetic_time_context


RISK_RANK = {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4}


DOMAIN_EVAL_REQUIREMENTS = {
    "ten_god_relation": [
        "3 positive cases with all required condition axes present",
        "3 negative cases covering co-presence without action path, cross-layer mismatch, or rescue-path absence",
        "1 hidden-stem interference case where藏干不能替代透出",
        "1 time-layer interference case where大运流年只作触发背景",
    ],
    "income_stability": [
        "3 positive cases for visible wealth/access/path signals",
        "3 negative cases for wealth visible but blocked, bound, or unsupported",
        "1 time-layer volatility case without rewriting natal structure",
        "1 hidden-stem wealth background case without direct verdict",
    ],
    "structural_relation": [
        "3 positive branch-relation cases with relation type and layer explicit",
        "3 negative cases for named relation without valid composition/action",
        "1 composite relation interference case",
        "1 time-layer relation case that remains context-only",
    ],
    "time_structure": [
        "3 positive cases where luck/year relation activates an existing structural topic",
        "3 negative cases where time background is present but does not change natal facts",
        "1 natal-vs-time layer disambiguation case",
        "1 relation-name-only boundary case",
    ],
    "day_master_element": [
        "3 positive cases with day master, month command, and support/pressure evidence",
        "3 negative cases where single-axis evidence is insufficient",
        "1 hidden-stem capacity candidate case",
        "1 time-background non-overwrite case",
    ],
}


def build_runtime_rule_db_readiness_audit(
    rules: Iterable[Dict[str, Any]] | None = None,
    *,
    max_direct_gate_risk: str = "R1",
    min_confidence: float = 0.62,
    limit: int = 80,
) -> Dict[str, Any]:
    """Classify runtime Rule DB records for the next mainline validation step.

    This audit is intentionally read-only. It does not promote, activate, or
    mutate Rule DB records; it only tells the mainline which rules can move into
    synthetic gate validation and which still need shadow work.
    """

    source_rules = list(rules if rules is not None else bazi_rule_db.list_bazi_rules().get("rules") or [])
    max_rank = RISK_RANK.get(str(max_direct_gate_risk or "R1"), 1)
    min_conf = _bounded_float(min_confidence, 0.62)
    rows = [_readiness_row(rule, max_rank=max_rank, min_confidence=min_conf) for rule in source_rules]
    candidates = [row for row in rows if row["engine_enabled"] is not True]
    selected = sorted(
        [row for row in candidates if row["decision"] == "synthetic_gate_candidate"],
        key=lambda row: (row["score"], row["confidence"], row["knowledge_id"]),
        reverse=True,
    )[: max(0, int(limit or 0))]

    summary = {
        "rule_count": len(rows),
        "engine_enabled_count": sum(1 for row in rows if row["engine_enabled"] is True),
        "engine_disabled_count": sum(1 for row in rows if row["engine_enabled"] is not True),
        "synthetic_gate_candidate_count": sum(1 for row in rows if row["decision"] == "synthetic_gate_candidate"),
        "shadow_eval_candidate_count": sum(1 for row in rows if row["decision"] == "shadow_eval_candidate"),
        "adapter_fact_gap_count": sum(1 for row in rows if row["decision"] == "adapter_fact_gap"),
        "blocked_count": sum(1 for row in rows if row["decision"] == "blocked"),
        "selected_count": len(selected),
        "by_domain": _count_by(rows, "domain"),
        "by_decision": _count_by(rows, "decision"),
        "by_risk_level": _count_by(rows, "risk_level"),
    }

    return {
        "ok": True,
        "version": "v19.mainline.runtime_rule_db_readiness.v1",
        "status": "readiness_audit_only_no_activation",
        "runtime_scope": "rule_db_validation_planning_no_runtime_mutation",
        "summary": summary,
        "selected_for_next_synthetic_gate": selected,
        "items": rows[: max(0, int(limit or 0))] if limit else rows,
        "eval_requirements": _eval_requirements(rows),
        "guardrails": [
            "READ_ONLY_AUDIT",
            "NO_ENGINE_ACTIVATION",
            "NO_RESULT_MUTATION",
            "SYNTHETIC_GATE_REQUIRED_BEFORE_PROMOTION",
            "R4_ARCHIVE_ONLY",
        ],
    }


def build_runtime_rule_db_synthetic_gate_queue(
    rules: Iterable[Dict[str, Any]] | None = None,
    *,
    max_direct_gate_risk: str = "R1",
    min_confidence: float = 0.62,
    limit: int = 24,
) -> Dict[str, Any]:
    audit = build_runtime_rule_db_readiness_audit(
        rules,
        max_direct_gate_risk=max_direct_gate_risk,
        min_confidence=min_confidence,
        limit=limit,
    )
    gate_cases: List[Dict[str, Any]] = []
    for rule in audit["selected_for_next_synthetic_gate"]:
        gate_cases.extend(_gate_case_slots(rule))
    return {
        "ok": True,
        "version": "v19.mainline.runtime_rule_db_synthetic_gate_queue.v1",
        "status": "synthetic_gate_queue_ready_no_activation",
        "runtime_scope": "eval_dataset_planning_no_runtime_mutation",
        "readiness_summary": audit["summary"],
        "candidate_count": len(audit["selected_for_next_synthetic_gate"]),
        "case_count": len(gate_cases),
        "cases": gate_cases,
        "guardrails": audit["guardrails"] + ["EVAL_DATASET_ONLY", "NO_SYNTHETIC_CASE_AUTO_PASS"],
    }


def build_runtime_rule_db_synthetic_eval_dataset(
    rules: Iterable[Dict[str, Any]] | None = None,
    *,
    max_direct_gate_risk: str = "R1",
    min_confidence: float = 0.62,
    limit: int = 24,
) -> Dict[str, Any]:
    queue = build_runtime_rule_db_synthetic_gate_queue(
        rules,
        max_direct_gate_risk=max_direct_gate_risk,
        min_confidence=min_confidence,
        limit=limit,
    )
    samples = [_sample_from_gate_case(case) for case in queue["cases"]]
    return {
        "ok": True,
        "version": "v19.mainline.runtime_rule_db_synthetic_eval_dataset.v1",
        "status": "runtime_rule_db_eval_dataset_ready_no_activation",
        "runtime_scope": "synthetic_eval_dataset_no_runtime_mutation",
        "schema": {
            "required_fields": [
                "case_id",
                "source_rule_id",
                "source_knowledge_id",
                "polarity",
                "chart",
                "time_context",
                "expected_signal",
                "forbidden_signals",
                "expected_question_keys",
                "forbidden_text",
                "condition_axes_expected",
                "audit_tags",
            ],
            "polarity_values": ["positive", "negative", "time_interference", "hidden_source_interference"],
        },
        "summary": {
            "candidate_count": queue["candidate_count"],
            "sample_count": len(samples),
            "by_domain": _count_by(samples, "domain"),
            "by_polarity": _count_by(samples, "polarity"),
            "min_samples_per_rule": min(_count_by(samples, "source_knowledge_id").values() or [0]),
        },
        "samples": samples,
        "quality_thresholds": {
            "positive_minimum": 3,
            "negative_minimum": 3,
            "time_interference_minimum": 1,
            "hidden_source_interference_minimum": 1,
            "precision_required": 1.0,
            "false_positive_allowed": 0,
            "forbidden_text_allowed": 0,
            "activation_allowed": False,
        },
        "guardrails": queue["guardrails"] + ["DATASET_READY", "ACTIVATION_REQUIRES_PASSING_REGRESSION"],
    }


def run_runtime_rule_db_readiness_regression() -> Dict[str, Any]:
    fixtures = [
        _fixture_rule("ready.ten_god", "ten_god_relation", "ten_god_interaction", "R1", 0.82, True, False),
        _fixture_rule("shadow.income", "income_stability", "income_collision", "R2", 0.78, True, False),
        _fixture_rule("gap.branch", "structural_relation", "branch_relation", "R1", 0.8, False, False),
        _fixture_rule("blocked.geo", "structural_relation", "geo_context", "R3", 0.9, True, False),
        _fixture_rule("active.time", "time_structure", "timing_context", "R1", 0.9, True, True),
    ]
    audit = build_runtime_rule_db_readiness_audit(fixtures, limit=20)
    summary = audit["summary"]
    checks = [
        summary["rule_count"] == 5,
        summary["engine_enabled_count"] == 1,
        summary["synthetic_gate_candidate_count"] == 1,
        summary["shadow_eval_candidate_count"] == 1,
        summary["adapter_fact_gap_count"] == 1,
        summary["blocked_count"] == 1,
        audit["selected_for_next_synthetic_gate"][0]["knowledge_id"] == "ready.ten_god",
        "ten_god_relation" in audit["eval_requirements"],
    ]
    return {
        "ok": all(checks),
        "status": "pass" if all(checks) else "fail",
        "audit": audit,
        "checks": checks,
    }


def run_runtime_rule_db_synthetic_eval_regression() -> Dict[str, Any]:
    fixtures = [
        _fixture_rule("ready.ten_god", "ten_god_relation", "ten_god_interaction", "R1", 0.82, True, False),
        _fixture_rule("ready.income", "income_stability", "income_path", "R1", 0.8, True, False),
    ]
    dataset = build_runtime_rule_db_synthetic_eval_dataset(fixtures, limit=10)
    sample_results = [_evaluate_runtime_eval_sample(sample) for sample in dataset["samples"]]
    failures = [failure for row in sample_results for failure in row["failures"]]
    false_positive_count = sum(1 for row in sample_results if row["false_positive"])
    status = "pass" if not failures and false_positive_count == 0 else "fail"
    return {
        "ok": status == "pass",
        "version": "v19.mainline.runtime_rule_db_synthetic_eval_regression.v1",
        "status": status,
        "summary": {
            "sample_count": len(sample_results),
            "sample_passed": sum(1 for row in sample_results if row["status"] == "pass"),
            "sample_failed": sum(1 for row in sample_results if row["status"] == "fail"),
            "false_positive_count": false_positive_count,
            "by_polarity": dataset["summary"]["by_polarity"],
            "activation_updated_count": 0,
        },
        "dataset": {
            "version": dataset["version"],
            "status": dataset["status"],
            "sample_count": dataset["summary"]["sample_count"],
            "quality_thresholds": dataset["quality_thresholds"],
        },
        "samples": sample_results,
        "failures": failures,
        "activation_policy": {
            "current_stage": "Synthetic eval dataset validation only.",
            "runtime_activation": "No Rule DB engine activation is allowed from this regression.",
            "next": "A later gate may run these samples against the Rule Graph and answer guardrails before activation.",
        },
        "guardrails": dataset["guardrails"],
    }


def run_runtime_rule_db_synthetic_route_regression() -> Dict[str, Any]:
    fixtures = [
        _fixture_rule("ready.ten_god", "ten_god_relation", "ten_god_interaction", "R1", 0.82, True, False),
        _fixture_rule("ready.income", "income_stability", "income_path", "R1", 0.8, True, False),
    ]
    dataset = build_runtime_rule_db_synthetic_eval_dataset(fixtures, limit=10)
    route_results = [_evaluate_route_sample(sample) for sample in dataset["samples"]]
    failures = [failure for row in route_results for failure in row["failures"]]
    false_positive_count = sum(1 for row in route_results if row["false_positive"])
    missed_positive_count = sum(1 for row in route_results if row["missed_positive"])
    status = "shadow_route_pass_no_activation" if not failures and false_positive_count == 0 and missed_positive_count == 0 else "blocked"
    return {
        "ok": status == "shadow_route_pass_no_activation",
        "version": "v19.mainline.runtime_rule_db_synthetic_route_regression.v1",
        "status": status,
        "summary": {
            "sample_count": len(route_results),
            "route_passed": sum(1 for row in route_results if row["status"] == "pass"),
            "route_failed": sum(1 for row in route_results if row["status"] == "fail"),
            "false_positive_count": false_positive_count,
            "missed_positive_count": missed_positive_count,
            "activation_updated_count": 0,
            "by_polarity": dataset["summary"]["by_polarity"],
        },
        "routes": route_results,
        "failures": failures,
        "activation_policy": {
            "current_stage": "Shadow route regression over synthetic eval samples.",
            "runtime_activation": "No Rule DB engine activation is allowed from this route regression.",
            "next": "Connect passing route samples to answer guardrail checks before controlled activation.",
        },
        "guardrails": dataset["guardrails"] + ["SHADOW_ROUTE_ONLY", "NO_FALSE_POSITIVE_ROUTE"],
    }


def run_runtime_rule_db_synthetic_gate_queue_regression() -> Dict[str, Any]:
    fixtures = [
        _fixture_rule("ready.ten_god", "ten_god_relation", "ten_god_interaction", "R1", 0.82, True, False),
        _fixture_rule("ready.income", "income_stability", "income_path", "R1", 0.8, True, False),
        _fixture_rule("shadow.income", "income_stability", "income_collision", "R2", 0.78, True, False),
    ]
    queue = build_runtime_rule_db_synthetic_gate_queue(fixtures, limit=10)
    by_rule = _count_by(queue["cases"], "source_knowledge_id")
    polarities = _count_by(queue["cases"], "polarity")
    checks = [
        queue["status"] == "synthetic_gate_queue_ready_no_activation",
        queue["candidate_count"] == 2,
        queue["case_count"] == 16,
        by_rule.get("ready.ten_god") == 8,
        by_rule.get("ready.income") == 8,
        polarities.get("positive") == 6,
        polarities.get("negative") == 6,
        polarities.get("time_interference") == 2,
        polarities.get("hidden_source_interference") == 2,
        all(case["expected_result"] == "manual_or_synthetic_runner_required" for case in queue["cases"]),
    ]
    return {
        "ok": all(checks),
        "status": "pass" if all(checks) else "fail",
        "queue": queue,
        "checks": checks,
    }


def _evaluate_route_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    polarity = str(sample.get("polarity") or "")
    source_id = str(sample.get("source_knowledge_id") or "")
    blocked_axes = [
        str(row.get("key") or "")
        for row in sample.get("condition_axes_expected") or []
        if isinstance(row, dict) and str(row.get("expected") or "") == "blocked"
    ]
    matched_route = bool(source_id and polarity == "positive" and not blocked_axes)
    failures: List[Dict[str, Any]] = []
    if polarity == "positive" and not matched_route:
        failures.append({"case_id": sample.get("case_id"), "failure_type": "expected_route_missing", "expected": source_id, "blocked_axes": blocked_axes})
    if polarity != "positive" and matched_route:
        failures.append({"case_id": sample.get("case_id"), "failure_type": "unexpected_route_match", "unexpected": source_id})
    if polarity != "positive" and not blocked_axes:
        failures.append({"case_id": sample.get("case_id"), "failure_type": "non_positive_route_has_no_blocked_axis"})
    return {
        "case_id": sample.get("case_id"),
        "source_knowledge_id": source_id,
        "polarity": polarity,
        "matched_route_ids": [source_id] if matched_route else [],
        "blocked_axes": blocked_axes,
        "false_positive": polarity != "positive" and matched_route,
        "missed_positive": polarity == "positive" and not matched_route,
        "status": "fail" if failures else "pass",
        "failures": failures,
    }


def _sample_from_gate_case(case: Dict[str, Any]) -> Dict[str, Any]:
    polarity = str(case.get("polarity") or "")
    source_id = str(case.get("source_knowledge_id") or "")
    domain = str(case.get("domain") or "")
    chart = _synthetic_chart_for_sample(case)
    return {
        "case_id": case.get("case_id") or "",
        "source_rule_id": case.get("source_rule_id") or "",
        "source_knowledge_id": source_id,
        "domain": domain,
        "category": case.get("category") or "",
        "polarity": polarity,
        "sample_type": case.get("slot_name") or "",
        "chart": chart,
        "time_context": _time_context_for_sample(case, chart),
        "expected_signal": source_id if polarity == "positive" else "",
        "forbidden_signals": [] if polarity == "positive" else [source_id] + list(case.get("forbidden_signals") or []),
        "expected_question_keys": _expected_question_keys(domain),
        "forbidden_text": _forbidden_text_for_domain(domain),
        "condition_axes_expected": _axis_expectations_for_gate_case(case),
        "audit_tags": list(case.get("audit_tags") or []) + ["runtime_rule_db_eval_dataset"],
    }


def _evaluate_runtime_eval_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    failures: List[Dict[str, Any]] = []
    required = [
        "case_id",
        "source_rule_id",
        "source_knowledge_id",
        "polarity",
        "chart",
        "time_context",
        "expected_signal",
        "forbidden_signals",
        "expected_question_keys",
        "forbidden_text",
        "condition_axes_expected",
        "audit_tags",
    ]
    for key in required:
        if key not in sample:
            failures.append({"case_id": sample.get("case_id"), "failure_type": "schema_field_missing", "field": key})
    source_id = str(sample.get("source_knowledge_id") or "")
    polarity = str(sample.get("polarity") or "")
    expected_signal = str(sample.get("expected_signal") or "")
    axis_statuses = [str(row.get("expected") or "") for row in sample.get("condition_axes_expected") or [] if isinstance(row, dict)]
    if polarity == "positive":
        if expected_signal != source_id:
            failures.append({"case_id": sample.get("case_id"), "failure_type": "positive_expected_signal_mismatch", "expected": source_id, "actual": expected_signal})
        if "blocked" in axis_statuses:
            failures.append({"case_id": sample.get("case_id"), "failure_type": "positive_axis_blocked"})
    else:
        if expected_signal:
            failures.append({"case_id": sample.get("case_id"), "failure_type": "non_positive_expected_signal_should_be_empty", "actual": expected_signal})
        if source_id not in set(str(item) for item in sample.get("forbidden_signals") or []):
            failures.append({"case_id": sample.get("case_id"), "failure_type": "forbidden_signal_missing", "expected": source_id})
        if "blocked" not in axis_statuses:
            failures.append({"case_id": sample.get("case_id"), "failure_type": "non_positive_has_no_blocked_axis"})
    chart = sample.get("chart") or {}
    if not isinstance(chart, dict) or chart.get("status") != "ok" or not chart.get("pillars"):
        failures.append({"case_id": sample.get("case_id"), "failure_type": "synthetic_chart_missing"})
    forbidden_text = set(str(item) for item in sample.get("forbidden_text") or [])
    if not {"发财", "破财", "必然", "应期"} <= forbidden_text:
        failures.append({"case_id": sample.get("case_id"), "failure_type": "forbidden_text_contract_failed"})
    return {
        "case_id": sample.get("case_id"),
        "source_knowledge_id": source_id,
        "polarity": polarity,
        "sample_type": sample.get("sample_type") or "",
        "false_positive": polarity != "positive" and bool(expected_signal),
        "status": "fail" if failures else "pass",
        "failures": failures,
    }


def _readiness_row(rule: Dict[str, Any], *, max_rank: int, min_confidence: float) -> Dict[str, Any]:
    risk = str(rule.get("risk_level") or "R2")
    risk_rank = RISK_RANK.get(risk, 9)
    confidence = _bounded_float(rule.get("confidence"), 0.0)
    structured_facts = ((rule.get("condition") or {}).get("structured_facts") or {})
    input_required = ((rule.get("input_contract") or {}).get("required") or [])
    forbidden = [str(item) for item in (rule.get("forbidden_usage") or [])]
    allowed = [str(item) for item in (rule.get("allowed_usage") or [])]
    engine_enabled = rule.get("engine_enabled") is True
    blockers: List[str] = []

    if risk_rank >= 4:
        blockers.append("archive_only_risk")
    elif risk_rank > 2:
        blockers.append("risk_above_shadow_threshold")
    if not structured_facts:
        blockers.append("missing_structured_facts")
    if not input_required:
        blockers.append("missing_input_contract")
    if confidence < min_confidence:
        blockers.append("confidence_below_threshold")
    if any(token in forbidden for token in ["direct_fortune_output", "wealth_verdict", "prediction_verdict"]):
        blockers.append("answer_guardrail_required")

    if engine_enabled:
        decision = "already_engine_enabled"
    elif "archive_only_risk" in blockers or "risk_above_shadow_threshold" in blockers:
        decision = "blocked"
    elif "missing_structured_facts" in blockers or "missing_input_contract" in blockers:
        decision = "adapter_fact_gap"
    elif risk_rank <= max_rank and confidence >= min_confidence:
        decision = "synthetic_gate_candidate"
    else:
        decision = "shadow_eval_candidate"

    if decision == "synthetic_gate_candidate" and "answer_guardrail_required" in blockers:
        synthetic_gate = "required_with_answer_guardrail"
    elif decision in {"synthetic_gate_candidate", "shadow_eval_candidate"}:
        synthetic_gate = "required"
    elif decision == "already_engine_enabled":
        synthetic_gate = "already_active_route_only"
    else:
        synthetic_gate = "not_ready"

    score = max(0, 100 - risk_rank * 12 + int(confidence * 20) + (10 if structured_facts else 0) + (4 if input_required else 0))
    return {
        "rule_id": rule.get("rule_id") or "",
        "knowledge_id": rule.get("knowledge_id") or "",
        "title": rule.get("title") or "",
        "domain": rule.get("domain") or "",
        "category": rule.get("category") or "",
        "risk_level": risk,
        "confidence": confidence,
        "engine_enabled": engine_enabled,
        "engine_adapter_status": rule.get("engine_adapter_status") or "",
        "allowed_usage": allowed,
        "forbidden_usage": forbidden,
        "has_structured_facts": bool(structured_facts),
        "has_input_contract": bool(input_required),
        "decision": decision,
        "synthetic_gate": synthetic_gate,
        "blockers": blockers,
        "score": score,
        "eval_requirement_key": rule.get("domain") or "default",
    }


def _synthetic_chart_for_sample(case: Dict[str, Any]) -> Dict[str, Any]:
    domain = str(case.get("domain") or "")
    polarity = str(case.get("polarity") or "")
    case_id = str(case.get("case_id") or "runtime_gate.synthetic")
    if domain == "income_stability":
        pillars = {"year": "戊辰", "month": "丁巳", "day": "壬午", "hour": "丙午"} if polarity == "positive" else {"year": "庚申", "month": "壬子", "day": "壬午", "hour": "辛亥"}
    elif domain == "structural_relation":
        pillars = {"year": "甲子", "month": "乙丑", "day": "庚午", "hour": "丁未"} if polarity == "positive" else {"year": "甲寅", "month": "乙卯", "day": "庚申", "hour": "丁酉"}
    elif domain == "time_structure":
        pillars = {"year": "甲子", "month": "丁亥", "day": "壬午", "hour": "庚戌"}
    elif domain == "day_master_element":
        pillars = {"year": "庚申", "month": "辛酉", "day": "甲寅", "hour": "癸亥"} if polarity == "positive" else {"year": "丙午", "month": "丁巳", "day": "甲申", "hour": "戊辰"}
    else:
        pillars = {"year": "甲寅", "month": "辛酉", "day": "戊辰", "hour": "癸亥"} if polarity == "positive" else {"year": "甲子", "month": "乙丑", "day": "戊辰", "hour": "己未"}
    return make_synthetic_chart(case_id, pillars)


def _time_context_for_sample(case: Dict[str, Any], chart: Dict[str, Any]) -> Dict[str, Any]:
    if str(case.get("polarity") or "") == "time_interference":
        return make_synthetic_time_context(
            chart,
            luck_pillar="庚寅",
            flow_pillar="丙午",
            luck_relations={"combination": ["亥寅"]},
            flow_relations={"same_branch": ["午"]},
        )
    return make_synthetic_time_context(chart)


def _expected_question_keys(domain: str) -> List[str]:
    if domain == "income_stability":
        return ["q_income_stability", "kbq_income_path_route"]
    if domain == "time_structure":
        return ["q_time_context", "q_time_context_boundary"]
    if domain == "structural_relation":
        return ["q_branch_relation_detail", "q_time_vs_natal_relation"]
    if domain == "day_master_element":
        return ["q_day_master_month_anchor", "q_month_command_anchor"]
    return ["q_ten_god_metadata"]


def _forbidden_text_for_domain(domain: str) -> List[str]:
    base = ["发财", "破财", "升职", "离婚", "疾病", "官非", "必然", "应期", "吉凶", "预测"]
    if domain == "income_stability":
        base.extend(["财运一定", "必定赚钱"])
    return base


def _axis_expectations_for_gate_case(case: Dict[str, Any]) -> List[Dict[str, str]]:
    polarity = str(case.get("polarity") or "")
    slot_name = str(case.get("slot_name") or "")
    rows = []
    for axis in case.get("condition_axes_expected") or []:
        key = str(axis or "")
        expected = "satisfied"
        if polarity != "positive":
            expected = "blocked" if _axis_blocked_by_slot(key, slot_name, polarity) else "satisfied"
        rows.append({"key": key, "expected": expected})
    return rows


def _axis_blocked_by_slot(axis: str, slot_name: str, polarity: str) -> bool:
    if polarity == "time_interference":
        return axis in {"source_layer", "same_layer_action", "answer_boundary"}
    if polarity == "hidden_source_interference":
        return axis in {"source_layer", "same_layer_action"}
    if slot_name == "negative_no_action_path":
        return axis in {"same_layer_action", "answer_boundary"}
    if slot_name == "negative_cross_layer_mismatch":
        return axis in {"source_layer", "same_layer_action"}
    if slot_name == "negative_capacity_or_rescue_absent":
        return axis in {"capacity_strength", "rescue_path"}
    return axis == "answer_boundary"


def _gate_case_slots(rule: Dict[str, Any]) -> List[Dict[str, Any]]:
    slots = [
        ("positive", "positive_full_axes_1"),
        ("positive", "positive_full_axes_2"),
        ("positive", "positive_full_axes_3"),
        ("negative", "negative_no_action_path"),
        ("negative", "negative_cross_layer_mismatch"),
        ("negative", "negative_capacity_or_rescue_absent"),
        ("time_interference", "time_layer_context_only"),
        ("hidden_source_interference", "hidden_stem_or_source_layer_boundary"),
    ]
    return [
        {
            "case_id": f"runtime_gate.{rule['knowledge_id']}.{slot_name}",
            "source_rule_id": rule.get("rule_id") or "",
            "source_knowledge_id": rule.get("knowledge_id") or "",
            "domain": rule.get("domain") or "",
            "category": rule.get("category") or "",
            "polarity": polarity,
            "slot_name": slot_name,
            "expected_signal": rule.get("category") or rule.get("domain") or "runtime_rule_db_signal",
            "forbidden_signals": _forbidden_signals_for_rule(rule),
            "condition_axes_expected": [
                "source_layer",
                "capacity_strength",
                "same_layer_action",
                "rescue_path",
                "answer_boundary",
            ],
            "expected_result": "manual_or_synthetic_runner_required",
            "audit_tags": [
                "runtime_rule_db_synthetic_gate",
                "no_runtime_mutation",
                "no_prediction_verdict",
                polarity,
            ],
        }
        for polarity, slot_name in slots
    ]


def _forbidden_signals_for_rule(rule: Dict[str, Any]) -> List[str]:
    forbidden = ["direct_fortune_output", "prediction_verdict"]
    if str(rule.get("domain") or "") == "time_structure":
        forbidden.append("time_layer_rewrites_natal_structure")
    if str(rule.get("domain") or "") == "income_stability":
        forbidden.append("wealth_verdict_without_time_and_fact_gate")
    return forbidden


def _eval_requirements(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    domains = sorted({str(row.get("domain") or "") for row in rows if row.get("decision") in {"synthetic_gate_candidate", "shadow_eval_candidate"}})
    return {
        domain: {
            "sample_floor": "8 cases minimum per mechanism; expand to 10-12 for complex mechanisms",
            "requirements": DOMAIN_EVAL_REQUIREMENTS.get(
                domain,
                [
                    "3 positive cases with full condition axes present",
                    "3 negative boundary cases",
                    "1 time-layer interference case",
                    "1 hidden/source-layer interference case",
                ],
            ),
        }
        for domain in domains
    }


def _count_by(rows: Iterable[Dict[str, Any]], key: str) -> Dict[str, int]:
    return dict(Counter(str(row.get(key) or "unknown") for row in rows))


def _bounded_float(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(0.0, min(parsed, 1.0))


def _fixture_rule(
    knowledge_id: str,
    domain: str,
    category: str,
    risk_level: str,
    confidence: float,
    has_facts: bool,
    engine_enabled: bool,
) -> Dict[str, Any]:
    return {
        "rule_id": f"v19.rule.{knowledge_id}",
        "knowledge_id": knowledge_id,
        "title": knowledge_id,
        "domain": domain,
        "category": category,
        "risk_level": risk_level,
        "confidence": confidence,
        "status": "active_in_rule_db",
        "engine_enabled": engine_enabled,
        "engine_adapter_status": "synthetic_gate_active" if engine_enabled else "candidate_waiting_synthetic_acceptance",
        "input_contract": {"required": ["chart"]},
        "condition": {"structured_facts": {"candidate_signal": knowledge_id}} if has_facts else {"conditions": {"keywords": [knowledge_id]}},
        "allowed_usage": ["rule_db", "shadow_signal_candidate"],
        "forbidden_usage": ["direct_fortune_output"] if domain == "income_stability" else [],
    }
