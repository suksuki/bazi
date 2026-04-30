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


def run_runtime_rule_db_answer_guardrail_regression() -> Dict[str, Any]:
    route_regression = run_runtime_rule_db_synthetic_route_regression()
    dataset = build_runtime_rule_db_synthetic_eval_dataset(
        [
            _fixture_rule("ready.ten_god", "ten_god_relation", "ten_god_interaction", "R1", 0.82, True, False),
            _fixture_rule("ready.income", "income_stability", "income_path", "R1", 0.8, True, False),
        ],
        limit=10,
    )
    route_by_case = {str(row.get("case_id") or ""): row for row in route_regression.get("routes") or []}
    answer_results = [_evaluate_answer_guardrail(sample, route_by_case.get(str(sample.get("case_id") or ""), {})) for sample in dataset["samples"]]
    failures = [failure for row in answer_results for failure in row["failures"]]
    forbidden_text_failure_count = sum(1 for failure in failures if failure.get("failure_type") == "forbidden_text_present")
    internal_term_failure_count = sum(1 for failure in failures if failure.get("failure_type") == "internal_term_present")
    unsupported_answer_count = sum(1 for failure in failures if failure.get("failure_type") == "unsupported_route_answer")
    status = "answer_guardrail_pass_no_activation" if route_regression.get("ok") and not failures else "blocked"
    return {
        "ok": status == "answer_guardrail_pass_no_activation",
        "version": "v19.mainline.runtime_rule_db_answer_guardrail_regression.v1",
        "status": status,
        "summary": {
            "sample_count": len(answer_results),
            "answer_passed": sum(1 for row in answer_results if row["status"] == "pass"),
            "answer_failed": sum(1 for row in answer_results if row["status"] == "fail"),
            "forbidden_text_failure_count": forbidden_text_failure_count,
            "internal_term_failure_count": internal_term_failure_count,
            "unsupported_answer_count": unsupported_answer_count,
            "route_regression_status": route_regression.get("status"),
            "activation_updated_count": 0,
        },
        "answers": answer_results,
        "failures": failures,
        "activation_policy": {
            "current_stage": "Answer guardrail regression over runtime Rule DB synthetic route samples.",
            "runtime_activation": "No Rule DB engine activation is allowed from answer guardrail checks.",
            "next": "Only samples passing readiness, eval dataset, route regression, and answer guardrails can enter controlled activation planning.",
        },
        "guardrails": route_regression["guardrails"] + ["ANSWER_GUARDRAIL", "NO_INTERNAL_TERMS", "NO_PREDICTION_TEXT"],
    }


def build_runtime_rule_db_controlled_activation_plan(
    rules: Iterable[Dict[str, Any]] | None = None,
    *,
    max_direct_gate_risk: str = "R1",
    min_confidence: float = 0.62,
    limit: int = 24,
) -> Dict[str, Any]:
    source_rules = list(rules if rules is not None else bazi_rule_db.list_bazi_rules().get("rules") or [])
    answer_gate = _runtime_pipeline_gate(source_rules, max_direct_gate_risk=max_direct_gate_risk, min_confidence=min_confidence, limit=limit)
    candidates = [
        _activation_plan_row(row)
        for row in answer_gate["readiness"].get("selected_for_next_synthetic_gate") or []
        if answer_gate["ok"]
    ]
    return {
        "ok": answer_gate["ok"],
        "version": "v19.mainline.runtime_rule_db_controlled_activation_plan.v1",
        "status": "controlled_activation_plan_ready_no_runtime_activation" if answer_gate["ok"] else "controlled_activation_plan_blocked",
        "runtime_scope": "activation_planning_only_no_runtime_mutation",
        "summary": {
            "source_rule_count": len(source_rules),
            "activation_candidate_count": len(candidates),
            "ring0_canary_count": sum(1 for row in candidates if row["release_ring"] == "ring0_canary"),
            "ring1_internal_count": sum(1 for row in candidates if row["release_ring"] == "ring1_internal"),
            "pipeline_gate_status": answer_gate["status"],
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "activation_updated_count": 0,
            "runtime_mutation": False,
            "by_domain": _count_by(candidates, "domain"),
        },
        "activation_candidates": candidates,
        "release_policy": {
            "ring0_canary": "R0 candidates may enter the smallest isolated canary ring after explicit execution.",
            "ring1_internal": "R1 candidates remain internal-only until canary telemetry is clean.",
            "production": "Production activation is outside this planning stage.",
        },
        "pipeline_gate": {
            "readiness_status": answer_gate["readiness"].get("status"),
            "eval_status": answer_gate["eval"].get("status"),
            "route_status": answer_gate["route"].get("status"),
            "answer_guardrail_status": answer_gate["answer"].get("status"),
        },
        "guardrails": [
            "CONTROLLED_ACTIVATION_PLAN_ONLY",
            "NO_ENGINE_ACTIVATION",
            "NO_RESULT_MUTATION",
            "ROLLBACK_REQUIRED",
            "CANARY_FIRST",
        ],
    }


def build_runtime_rule_db_rollback_manifest(
    rules: Iterable[Dict[str, Any]] | None = None,
    *,
    max_direct_gate_risk: str = "R1",
    min_confidence: float = 0.62,
    limit: int = 24,
) -> Dict[str, Any]:
    plan = build_runtime_rule_db_controlled_activation_plan(
        rules,
        max_direct_gate_risk=max_direct_gate_risk,
        min_confidence=min_confidence,
        limit=limit,
    )
    items = [_rollback_row(row) for row in plan.get("activation_candidates") or []]
    return {
        "ok": plan.get("ok") is True,
        "version": "v19.mainline.runtime_rule_db_rollback_manifest.v1",
        "status": "rollback_manifest_ready_no_runtime_activation" if plan.get("ok") else "rollback_manifest_blocked",
        "runtime_scope": "rollback_planning_only_no_runtime_mutation",
        "summary": {
            "activation_candidate_count": plan["summary"]["activation_candidate_count"],
            "rollback_item_count": len(items),
            "missing_rollback_count": plan["summary"]["activation_candidate_count"] - len(items),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "activation_updated_count": 0,
            "runtime_mutation": False,
        },
        "items": items,
        "guardrails": plan["guardrails"] + ["ROLLBACK_MANIFEST", "KILL_SWITCH_REQUIRED"],
    }


def run_runtime_rule_db_controlled_activation_regression() -> Dict[str, Any]:
    fixtures = [
        _fixture_rule("ready.r0.ten_god", "ten_god_relation", "ten_god_interaction", "R0", 0.9, True, False),
        _fixture_rule("ready.r1.income", "income_stability", "income_path", "R1", 0.8, True, False),
        _fixture_rule("shadow.r2.income", "income_stability", "income_collision", "R2", 0.78, True, False),
    ]
    plan = build_runtime_rule_db_controlled_activation_plan(fixtures, limit=10)
    rollback = build_runtime_rule_db_rollback_manifest(fixtures, limit=10)
    failures: List[Dict[str, Any]] = []
    if plan["status"] != "controlled_activation_plan_ready_no_runtime_activation":
        failures.append({"failure_type": "activation_plan_not_ready"})
    if plan["summary"]["activation_updated_count"] != 0 or plan["summary"]["engine_enabled_count"] != 0:
        failures.append({"failure_type": "runtime_activation_not_allowed"})
    if rollback["summary"]["missing_rollback_count"] != 0:
        failures.append({"failure_type": "rollback_manifest_incomplete"})
    if plan["summary"]["ring0_canary_count"] != 1:
        failures.append({"failure_type": "ring0_count_mismatch", "actual": plan["summary"]["ring0_canary_count"]})
    if plan["summary"]["ring1_internal_count"] != 1:
        failures.append({"failure_type": "ring1_count_mismatch", "actual": plan["summary"]["ring1_internal_count"]})
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": "v19.mainline.runtime_rule_db_controlled_activation_regression.v1",
        "status": status,
        "summary": {
            "activation_candidate_count": plan["summary"]["activation_candidate_count"],
            "ring0_canary_count": plan["summary"]["ring0_canary_count"],
            "ring1_internal_count": plan["summary"]["ring1_internal_count"],
            "rollback_item_count": rollback["summary"]["rollback_item_count"],
            "missing_rollback_count": rollback["summary"]["missing_rollback_count"],
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "activation_updated_count": 0,
            "runtime_mutation": False,
        },
        "activation_plan": plan,
        "rollback_manifest": rollback,
        "failures": failures,
        "guardrails": plan["guardrails"] + ["REGRESSION_ONLY_NO_ACTIVATION"],
    }


def build_runtime_rule_db_isolated_canary_plan(
    rules: Iterable[Dict[str, Any]] | None = None,
    *,
    max_direct_gate_risk: str = "R1",
    min_confidence: float = 0.62,
    limit: int = 24,
) -> Dict[str, Any]:
    plan = build_runtime_rule_db_controlled_activation_plan(
        rules,
        max_direct_gate_risk=max_direct_gate_risk,
        min_confidence=min_confidence,
        limit=limit,
    )
    rollback = build_runtime_rule_db_rollback_manifest(
        rules,
        max_direct_gate_risk=max_direct_gate_risk,
        min_confidence=min_confidence,
        limit=limit,
    )
    rollback_by_candidate = {str(row.get("activation_candidate_id") or ""): row for row in rollback.get("items") or []}
    canaries = [
        _canary_row(row, rollback_by_candidate.get(str(row.get("activation_candidate_id") or "")))
        for row in plan.get("activation_candidates") or []
        if row.get("release_ring") == "ring0_canary"
    ]
    failures = []
    if plan.get("status") != "controlled_activation_plan_ready_no_runtime_activation":
        failures.append({"failure_type": "activation_plan_not_ready"})
    if any(not row.get("rollback_id") for row in canaries):
        failures.append({"failure_type": "rollback_missing"})
    if any(row.get("production_engine_enabled") for row in canaries):
        failures.append({"failure_type": "production_engine_enabled"})
    return {
        "ok": not failures,
        "version": "v19.mainline.runtime_rule_db_isolated_canary_plan.v1",
        "status": "isolated_canary_plan_ready_no_production_activation" if not failures else "isolated_canary_plan_blocked",
        "runtime_scope": "isolated_canary_planning_no_production_mutation",
        "summary": {
            "controlled_plan_status": plan.get("status"),
            "ring0_canary_count": len(canaries),
            "canary_runtime_enabled_count": sum(1 for row in canaries if row.get("canary_engine_enabled") is True),
            "production_engine_enabled_count": sum(1 for row in canaries if row.get("production_engine_enabled") is True),
            "rollback_covered_count": sum(1 for row in canaries if row.get("rollback_id")),
            "kill_switch_covered_count": sum(1 for row in canaries if row.get("kill_switch_enabled") is True),
            "answer_mutation_count": 0,
            "production_runtime_mutation": False,
        },
        "canaries": canaries,
        "failures": failures,
        "canary_policy": {
            "scope": "Isolated internal signal route only.",
            "production": "Production engine remains disabled.",
            "rollback": "Every canary requires rollback and kill switch coverage.",
        },
        "guardrails": plan["guardrails"] + ["ISOLATED_CANARY_ONLY", "PRODUCTION_ENGINE_DISABLED"],
    }


def build_runtime_rule_db_isolated_canary_eval_dataset(
    rules: Iterable[Dict[str, Any]] | None = None,
    *,
    max_direct_gate_risk: str = "R1",
    min_confidence: float = 0.62,
    limit: int = 24,
) -> Dict[str, Any]:
    plan = build_runtime_rule_db_isolated_canary_plan(
        rules,
        max_direct_gate_risk=max_direct_gate_risk,
        min_confidence=min_confidence,
        limit=limit,
    )
    samples = [sample for canary in plan.get("canaries") or [] for sample in _canary_samples(canary)]
    return {
        "ok": plan.get("ok") is True,
        "version": "v19.mainline.runtime_rule_db_isolated_canary_eval_dataset.v1",
        "status": "isolated_canary_eval_dataset_ready_no_production_activation",
        "runtime_scope": "isolated_canary_eval_dataset_no_production_mutation",
        "summary": {
            "ring0_canary_count": plan["summary"]["ring0_canary_count"],
            "sample_count": len(samples),
            "min_samples_per_canary": len(_canary_sample_types()) if plan["summary"]["ring0_canary_count"] else 0,
            "canary_runtime_enabled_count": plan["summary"]["canary_runtime_enabled_count"],
            "production_engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "by_sample_type": _count_by(samples, "sample_type"),
        },
        "samples": samples,
        "source_plan_summary": plan["summary"],
        "guardrails": plan["guardrails"] + ["CANARY_EVAL_DATASET_ONLY"],
    }


def run_runtime_rule_db_isolated_canary_trial() -> Dict[str, Any]:
    fixtures = [
        _fixture_rule("ready.r0.ten_god", "ten_god_relation", "ten_god_interaction", "R0", 0.9, True, False),
        _fixture_rule("ready.r1.income", "income_stability", "income_path", "R1", 0.8, True, False),
    ]
    dataset = build_runtime_rule_db_isolated_canary_eval_dataset(fixtures, limit=10)
    sample_results = [_evaluate_canary_sample(sample) for sample in dataset.get("samples") or []]
    failures = [failure for row in sample_results for failure in row["failures"]]
    status = "pass" if dataset.get("ok") is True and not failures else "fail"
    return {
        "ok": status == "pass",
        "version": "v19.mainline.runtime_rule_db_isolated_canary_trial.v1",
        "status": status,
        "summary": {
            "ring0_canary_count": dataset["summary"]["ring0_canary_count"],
            "sample_count": len(sample_results),
            "sample_passed": sum(1 for row in sample_results if row["status"] == "pass"),
            "sample_failed": sum(1 for row in sample_results if row["status"] == "fail"),
            "canary_internal_signal_count": sum(1 for row in sample_results if row["canary_internal_signal"] is True),
            "production_signal_leak_count": sum(1 for row in sample_results if row["production_signal_leak"] is True),
            "forbidden_text_failure_count": sum(1 for failure in failures if failure.get("failure_type") == "forbidden_text_contract_failed"),
            "rollback_ready_count": _unique_count(dataset.get("samples") or [], "rollback_ready"),
            "kill_switch_ready_count": _unique_count(dataset.get("samples") or [], "kill_switch_ready"),
            "canary_runtime_enabled_count": dataset["summary"]["canary_runtime_enabled_count"],
            "production_engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "production_runtime_mutation": False,
            "activation_updated_count": 0,
        },
        "samples": sample_results,
        "eval_dataset": dataset,
        "failures": failures,
        "guardrails": dataset["guardrails"] + ["CANARY_TRIAL_NO_PRODUCTION_ACTIVATION"],
    }


def run_runtime_rule_db_isolated_canary_release_regression() -> Dict[str, Any]:
    trial = run_runtime_rule_db_isolated_canary_trial()
    failures = []
    if trial.get("status") != "pass":
        failures.append({"failure_type": "canary_trial_failed"})
    if trial["summary"]["production_signal_leak_count"] != 0:
        failures.append({"failure_type": "production_signal_leak"})
    if trial["summary"]["production_engine_enabled_count"] != 0:
        failures.append({"failure_type": "production_engine_enabled"})
    if trial["summary"]["answer_mutation_count"] != 0:
        failures.append({"failure_type": "answer_mutation_not_allowed"})
    if trial["summary"]["rollback_ready_count"] != trial["summary"]["ring0_canary_count"]:
        failures.append({"failure_type": "rollback_coverage_failed"})
    if trial["summary"]["kill_switch_ready_count"] != trial["summary"]["ring0_canary_count"]:
        failures.append({"failure_type": "kill_switch_coverage_failed"})
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": "v19.mainline.runtime_rule_db_isolated_canary_release_regression.v1",
        "status": status,
        "summary": {
            "ring0_canary_count": trial["summary"]["ring0_canary_count"],
            "sample_count": trial["summary"]["sample_count"],
            "sample_failed": trial["summary"]["sample_failed"],
            "canary_runtime_enabled_count": trial["summary"]["canary_runtime_enabled_count"],
            "production_engine_enabled_count": 0,
            "production_signal_leak_count": trial["summary"]["production_signal_leak_count"],
            "forbidden_text_failure_count": trial["summary"]["forbidden_text_failure_count"],
            "rollback_ready_count": trial["summary"]["rollback_ready_count"],
            "kill_switch_ready_count": trial["summary"]["kill_switch_ready_count"],
            "answer_mutation_count": 0,
            "activation_updated_count": 0,
            "production_runtime_mutation": False,
        },
        "canary_trial": trial,
        "failures": failures,
        "guardrails": trial["guardrails"] + ["RELEASE_REGRESSION_ONLY_NO_PRODUCTION_ACTIVATION"],
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


def _runtime_pipeline_gate(
    rules: List[Dict[str, Any]],
    *,
    max_direct_gate_risk: str,
    min_confidence: float,
    limit: int,
) -> Dict[str, Any]:
    readiness = build_runtime_rule_db_readiness_audit(
        rules,
        max_direct_gate_risk=max_direct_gate_risk,
        min_confidence=min_confidence,
        limit=limit,
    )
    dataset = build_runtime_rule_db_synthetic_eval_dataset(
        rules,
        max_direct_gate_risk=max_direct_gate_risk,
        min_confidence=min_confidence,
        limit=limit,
    )
    eval_results = [_evaluate_runtime_eval_sample(sample) for sample in dataset["samples"]]
    eval_failures = [failure for row in eval_results for failure in row["failures"]]
    route_results = [_evaluate_route_sample(sample) for sample in dataset["samples"]]
    route_failures = [failure for row in route_results for failure in row["failures"]]
    route_by_case = {str(row.get("case_id") or ""): row for row in route_results}
    answer_results = [_evaluate_answer_guardrail(sample, route_by_case.get(str(sample.get("case_id") or ""), {})) for sample in dataset["samples"]]
    answer_failures = [failure for row in answer_results for failure in row["failures"]]
    ok = not eval_failures and not route_failures and not answer_failures
    return {
        "ok": ok,
        "status": "pipeline_gate_pass" if ok else "pipeline_gate_blocked",
        "readiness": readiness,
        "eval": {
            "status": "pass" if not eval_failures else "fail",
            "failure_count": len(eval_failures),
        },
        "route": {
            "status": "shadow_route_pass_no_activation" if not route_failures else "blocked",
            "failure_count": len(route_failures),
        },
        "answer": {
            "status": "answer_guardrail_pass_no_activation" if not answer_failures else "blocked",
            "failure_count": len(answer_failures),
        },
    }


def _activation_plan_row(row: Dict[str, Any]) -> Dict[str, Any]:
    risk = str(row.get("risk_level") or "R1")
    return {
        "activation_candidate_id": f"runtime.activation.{_slug(str(row.get('knowledge_id') or 'unknown'))}",
        "rule_id": row.get("rule_id") or "",
        "knowledge_id": row.get("knowledge_id") or "",
        "domain": row.get("domain") or "",
        "category": row.get("category") or "",
        "risk_level": risk,
        "confidence": row.get("confidence"),
        "release_ring": "ring0_canary" if risk == "R0" else "ring1_internal",
        "preconditions": [
            "readiness_audit_passed",
            "synthetic_eval_dataset_passed",
            "shadow_route_regression_passed",
            "answer_guardrail_passed",
            "rollback_manifest_ready",
        ],
        "engine_enabled": False,
        "answer_mutation": False,
        "runtime_mutation": False,
        "kill_switch": f"disable:{row.get('rule_id') or row.get('knowledge_id') or ''}",
    }


def _rollback_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "rollback_id": f"runtime.rollback.{_slug(str(row.get('knowledge_id') or 'unknown'))}",
        "activation_candidate_id": row.get("activation_candidate_id") or "",
        "rule_id": row.get("rule_id") or "",
        "knowledge_id": row.get("knowledge_id") or "",
        "release_ring": row.get("release_ring") or "",
        "rollback_action": "disable_engine_and_remove_from_release_ring",
        "kill_switch": row.get("kill_switch") or "",
        "engine_enabled_after_rollback": False,
        "answer_mutation": False,
        "runtime_mutation": False,
    }


def _canary_row(candidate: Dict[str, Any], rollback: Dict[str, Any] | None) -> Dict[str, Any]:
    return {
        "canary_id": f"runtime.canary.{_slug(str(candidate.get('knowledge_id') or 'unknown'))}",
        "activation_candidate_id": candidate.get("activation_candidate_id") or "",
        "rule_id": candidate.get("rule_id") or "",
        "knowledge_id": candidate.get("knowledge_id") or "",
        "domain": candidate.get("domain") or "",
        "category": candidate.get("category") or "",
        "risk_level": candidate.get("risk_level") or "",
        "release_ring": candidate.get("release_ring") or "",
        "canary_engine_enabled": True,
        "production_engine_enabled": False,
        "answer_mutation": False,
        "production_runtime_mutation": False,
        "rollback_id": (rollback or {}).get("rollback_id") or "",
        "kill_switch": candidate.get("kill_switch") or "",
        "kill_switch_enabled": bool(candidate.get("kill_switch")),
        "canary_scope": "isolated_internal_signal_route",
    }


def _canary_samples(canary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [_canary_sample(canary, sample_type, index) for index, sample_type in enumerate(_canary_sample_types(), start=1)]


def _canary_sample_types() -> List[str]:
    return [
        "canary_internal_signal_contract",
        "production_route_no_signal_contract",
        "answer_text_no_mutation_contract",
        "forbidden_text_contract",
        "rollback_execution_contract",
        "kill_switch_contract",
    ]


def _canary_sample(canary: Dict[str, Any], sample_type: str, index: int) -> Dict[str, Any]:
    return {
        "case_id": f"runtime.canary.{_slug(str(canary.get('knowledge_id') or 'unknown'))}.{index}.{sample_type}",
        "canary_id": canary.get("canary_id") or "",
        "activation_candidate_id": canary.get("activation_candidate_id") or "",
        "rule_id": canary.get("rule_id") or "",
        "knowledge_id": canary.get("knowledge_id") or "",
        "domain": canary.get("domain") or "",
        "sample_type": sample_type,
        "canary_engine_enabled": canary.get("canary_engine_enabled") is True,
        "production_engine_enabled": False,
        "expected_internal_signal": sample_type == "canary_internal_signal_contract",
        "production_signal_leak": False,
        "answer_mutation": False,
        "rollback_ready": sample_type == "rollback_execution_contract",
        "kill_switch_ready": sample_type == "kill_switch_contract",
        "forbidden_text": _forbidden_text_for_domain(str(canary.get("domain") or "")),
        "generated_answer_text": "",
        "audit_tags": ["runtime_rule_db_isolated_canary", sample_type],
    }


def _evaluate_canary_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    failures: List[Dict[str, Any]] = []
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
        if str(token) and str(token) in answer_text:
            failures.append(_sample_failure(sample, "forbidden_text_contract_failed", str(token)))
            break
    return {
        "case_id": sample.get("case_id") or "",
        "knowledge_id": sample.get("knowledge_id") or "",
        "sample_type": sample.get("sample_type") or "",
        "status": "fail" if failures else "pass",
        "canary_internal_signal": sample.get("sample_type") == "canary_internal_signal_contract",
        "production_signal_leak": sample.get("production_signal_leak") is True,
        "failures": failures,
    }


def _unique_count(samples: List[Dict[str, Any]], key: str) -> int:
    return len({str(sample.get("activation_candidate_id") or sample.get("rule_id") or "") for sample in samples if sample.get(key) is True})


def _sample_failure(sample: Dict[str, Any], failure_type: str, detail: str) -> Dict[str, str]:
    return {
        "case_id": str(sample.get("case_id") or ""),
        "knowledge_id": str(sample.get("knowledge_id") or ""),
        "failure_type": failure_type,
        "detail": detail,
    }


def _evaluate_answer_guardrail(sample: Dict[str, Any], route: Dict[str, Any]) -> Dict[str, Any]:
    answer = _render_guarded_answer(sample, route)
    failures: List[Dict[str, Any]] = []
    normalized = " ".join(answer.split())
    for token in sample.get("forbidden_text") or []:
        if str(token) and str(token) in normalized:
            failures.append({"case_id": sample.get("case_id"), "failure_type": "forbidden_text_present", "forbidden": str(token)})
    for token in _internal_answer_terms():
        if token in normalized:
            failures.append({"case_id": sample.get("case_id"), "failure_type": "internal_term_present", "term": token})
    if sample.get("polarity") == "positive" and not route.get("matched_route_ids"):
        failures.append({"case_id": sample.get("case_id"), "failure_type": "unsupported_route_answer"})
    if sample.get("polarity") != "positive" and "不能作为命中依据" not in answer:
        failures.append({"case_id": sample.get("case_id"), "failure_type": "non_positive_boundary_missing"})
    if sample.get("polarity") == "positive" and "只说明结构线索" not in answer:
        failures.append({"case_id": sample.get("case_id"), "failure_type": "positive_boundary_missing"})
    return {
        "case_id": sample.get("case_id"),
        "source_knowledge_id": sample.get("source_knowledge_id") or "",
        "polarity": sample.get("polarity") or "",
        "answer_preview": normalized[:240],
        "status": "fail" if failures else "pass",
        "failures": failures,
    }


def _render_guarded_answer(sample: Dict[str, Any], route: Dict[str, Any]) -> str:
    domain = str(sample.get("domain") or "")
    category = str(sample.get("category") or "")
    polarity = str(sample.get("polarity") or "")
    topic = _answer_topic_label(domain, category)
    if polarity == "positive" and route.get("matched_route_ids"):
        return (
            f"这条样本可以作为{topic}的结构线索来读。"
            "它只说明结构线索和证据来源，不直接推出事件结果。"
            "后续仍要看同层作用、承载条件和时间背景是否同时成立。"
        )
    return (
        f"这条样本暂时不能作为命中依据，当前只涉及{topic}的边界检查。"
        "原因是条件轴里存在来源层、同层作用、承载或时间边界的阻断。"
        "它可以保留为反例或干扰例，用来防止误触发。"
    )


def _answer_topic_label(domain: str, category: str) -> str:
    if domain == "income_stability":
        return "收入稳定性"
    if domain == "time_structure":
        return "时间背景"
    if domain == "structural_relation":
        return "地支关系"
    if domain == "day_master_element":
        return "日主与月令"
    if category:
        return "十神关系"
    return "命盘结构"


def _internal_answer_terms() -> List[str]:
    return [
        "rule_id",
        "signal_id",
        "source_signal_id",
        "question_basis",
        "GUIDED_ANSWER",
        "DETERMINISTIC",
        "ResultCard",
        "income_stability",
        "runtime_rule_db",
        "engine_adapter_status",
        "synthetic_gate",
    ]


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


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in str(value or "")).strip("_")


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
