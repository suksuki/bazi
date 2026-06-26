from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.real_bazi_distribution_replay import (
    REAL_BAZI_DISTRIBUTION_REPLAY_VERSION,
    run_real_bazi_distribution_replay,
)


REAL_BAZI_TRAINING_CALIBRATION_QUEUE_VERSION = "v30.real_bazi_training_calibration_queue.v1"


def run_real_bazi_training_calibration_queue(
    *,
    real_case_limit: int = 8,
    sample_518k_limit: int = 8,
) -> dict[str, Any]:
    replay = run_real_bazi_distribution_replay(
        real_case_limit=real_case_limit,
        sample_518k_limit=sample_518k_limit,
    )
    return build_real_bazi_training_calibration_queue(distribution_replay=replay)


def build_real_bazi_training_calibration_queue(
    *,
    distribution_replay: Mapping[str, Any],
) -> dict[str, Any]:
    replay = _mapping(distribution_replay)
    training_signals = _training_signals(replay)
    queue_items = _calibration_queue_items(replay)
    checks = _checks(replay, training_signals, queue_items)
    decision = _decision(checks, training_signals, queue_items)
    return {
        "version": REAL_BAZI_TRAINING_CALIBRATION_QUEUE_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["training_calibration_queue_ready"] else "blocked",
        "task": {
            "task_id": "RBD-S1.12",
            "title": "RBD Training Signal And Calibration Queue",
            "scope": "convert_accepted_rbd_replay_metrics_into_readonly_training_and_calibration_candidates",
        },
        "upstream_summary": _upstream_summary(replay),
        "training_signals": training_signals,
        "calibration_queue_items": queue_items,
        "checks": checks,
        "decision": decision,
        "policy_boundary": {
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "boundary": "rbd_s112_builds_candidate_queue_only_no_runtime_mutation_no_pointer_promotion",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "rbd_training_signals_are_evidence_candidates_not_direct_bazi_truth_or_weight_changes",
    }


def _training_signals(replay: Mapping[str, Any]) -> list[dict[str, Any]]:
    decision = _mapping(replay.get("decision"))
    real_case = _mapping(replay.get("real_case_summary"))
    sample = _mapping(replay.get("sample_518k_summary"))
    replay_ready = bool(decision.get("distribution_replay_ready"))
    real_ready_ratio = _float(real_case.get("ready_ratio"))
    sample_ready_ratio = _float(sample.get("ready_ratio"))
    min_ready_ratio = min(real_ready_ratio, sample_ready_ratio)
    average_domain_count = (
        _float(real_case.get("average_ready_domain_count")) + _float(sample.get("average_ready_domain_count"))
    ) / 2
    average_quality_domain_count = (
        _float(real_case.get("average_quality_ready_domain_count"))
        + _float(sample.get("average_quality_ready_domain_count"))
    ) / 2
    min_quality_domain_count = min(
        int(real_case.get("min_quality_ready_domain_count", 0) or 0),
        int(sample.get("min_quality_ready_domain_count", 0) or 0),
    )
    generic_hits = int(real_case.get("generic_language_hit_count", 0) or 0) + int(
        sample.get("generic_language_hit_count", 0) or 0
    )
    leaks = int(real_case.get("customer_internal_leak_count", 0) or 0) + int(
        sample.get("customer_internal_leak_count", 0) or 0
    )
    failed_by_source = _failed_domain_counts(replay)
    return [
        {
            "signal_id": "v30.training_signal.rbd_product_reading_acceptance",
            "signal_type": "product_reading_acceptance",
            "domain": "real_bazi_diagnosis",
            "strength": 1.0 if replay_ready else 0.0,
            "source_version": REAL_BAZI_DISTRIBUTION_REPLAY_VERSION,
            "payload": {
                "distribution_replay_ready": replay_ready,
                "answer_rbd_ready_real_case_count": real_case.get("answer_rbd_ready_count"),
                "answer_rbd_ready_sample_518k_count": sample.get("answer_rbd_ready_count"),
                "generic_language_hit_count": generic_hits,
                "customer_internal_leak_count": leaks,
            },
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
        },
        {
            "signal_id": "v30.training_signal.rbd_distribution_replay_quality",
            "signal_type": "distribution_replay_quality",
            "domain": "real_bazi_diagnosis",
            "strength": round(min_ready_ratio, 3),
            "source_version": REAL_BAZI_DISTRIBUTION_REPLAY_VERSION,
            "payload": {
                "real_case_ready": f"{real_case.get('ready_case_count')}/{real_case.get('replay_case_count')}",
                "sample_518k_ready": f"{sample.get('ready_case_count')}/{sample.get('replay_case_count')}",
                "real_case_ready_ratio": real_ready_ratio,
                "sample_518k_ready_ratio": sample_ready_ratio,
                "min_admin_claim_count": sample.get("min_admin_claim_count"),
                "min_admin_path_count": sample.get("min_admin_path_count"),
                "min_admin_portrait_count": sample.get("min_admin_portrait_count"),
            },
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
        },
        {
            "signal_id": "v30.training_signal.rbd_domain_coverage",
            "signal_type": "domain_coverage",
            "domain": "real_bazi_diagnosis",
            "strength": round(min(1.0, average_domain_count / 5.0), 3),
            "source_version": REAL_BAZI_DISTRIBUTION_REPLAY_VERSION,
            "payload": {
                "real_case_average_ready_domain_count": real_case.get("average_ready_domain_count"),
                "sample_518k_average_ready_domain_count": sample.get("average_ready_domain_count"),
                "failed_domain_counts_by_source": failed_by_source,
            },
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
        },
        {
            "signal_id": "v30.training_signal.rbd_projection_safety",
            "signal_type": "projection_safety",
            "domain": "real_bazi_diagnosis",
            "strength": 1.0 if generic_hits == 0 and leaks == 0 else 0.0,
            "source_version": REAL_BAZI_DISTRIBUTION_REPLAY_VERSION,
            "payload": {
                "generic_language_hit_count": generic_hits,
                "customer_internal_leak_count": leaks,
                "customer_projection_safety_clean": generic_hits == 0 and leaks == 0,
            },
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
        },
        {
            "signal_id": "v30.training_signal.rbd_core_claim_quality",
            "signal_type": "core_claim_quality",
            "domain": "real_bazi_diagnosis",
            "strength": round(min(1.0, average_quality_domain_count / 5.0), 3),
            "source_version": REAL_BAZI_DISTRIBUTION_REPLAY_VERSION,
            "payload": {
                "real_case_min_quality_ready_domain_count": real_case.get("min_quality_ready_domain_count"),
                "sample_518k_min_quality_ready_domain_count": sample.get("min_quality_ready_domain_count"),
                "real_case_average_quality_ready_domain_count": real_case.get("average_quality_ready_domain_count"),
                "sample_518k_average_quality_ready_domain_count": sample.get("average_quality_ready_domain_count"),
                "min_quality_ready_domain_count": min_quality_domain_count,
                "required_quality_ready_domain_count": 5,
                "failed_quality_domain_counts_by_source": _failed_quality_domain_counts(replay),
            },
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
        },
    ]


def _calibration_queue_items(replay: Mapping[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    source_alias = {
        "real_case_calibration_pack": "real_case_distribution_replay",
        "generated_518k_sample": "generated_518k_sample",
    }
    for row in _rows(replay):
        source = str(row.get("source") or "unknown_source")
        source_key = source_alias.get(source, source)
        case_id = str(row.get("case_id") or "")
        for domain in _list(row.get("failed_domains")):
            domain_key = str(domain or "")
            if not domain_key:
                continue
            key = (source_key, domain_key, "domain_path_or_claim_density_gap")
            if key not in grouped:
                grouped[key] = {
                    "queue_item_id": f"rbd.calibration.{source_key}.{domain_key}",
                    "target_module": "RBD",
                    "target_domain": domain_key,
                    "issue_type": "domain_path_or_claim_density_gap",
                    "source": source_key,
                    "evidence_case_ids": [],
                    "observed_failure_count": 0,
                    "recommended_action": "review_rbd_domain_path_claim_portrait_density",
                    "status": "queued_for_review",
                    "runtime_mutation_allowed": False,
                    "chart_fact_mutation_allowed": False,
                    "policy_pointer_promotion_allowed": False,
                    "boundary": "rbd_calibration_queue_item_is_evidence_backed_candidate_not_auto_apply",
                }
            grouped[key]["observed_failure_count"] += 1
            if case_id and case_id not in grouped[key]["evidence_case_ids"]:
                grouped[key]["evidence_case_ids"].append(case_id)
        for domain in _list(row.get("failed_quality_domains")):
            domain_key = str(domain or "")
            if not domain_key:
                continue
            key = (source_key, domain_key, "core_claim_quality_gap")
            if key not in grouped:
                grouped[key] = {
                    "queue_item_id": f"rbd.calibration.{source_key}.{domain_key}.claim_quality",
                    "target_module": "RBD",
                    "target_domain": domain_key,
                    "issue_type": "core_claim_quality_gap",
                    "source": source_key,
                    "evidence_case_ids": [],
                    "observed_failure_count": 0,
                    "recommended_action": "review_rbd_core_claim_quality_projection_and_domain_claim_trace",
                    "status": "queued_for_review",
                    "runtime_mutation_allowed": False,
                    "chart_fact_mutation_allowed": False,
                    "policy_pointer_promotion_allowed": False,
                    "boundary": "rbd_claim_quality_queue_item_is_review_only_not_auto_apply",
                }
            grouped[key]["observed_failure_count"] += 1
            if case_id and case_id not in grouped[key]["evidence_case_ids"]:
                grouped[key]["evidence_case_ids"].append(case_id)
    return sorted(grouped.values(), key=lambda item: (str(item["source"]), str(item["target_domain"])))


def _checks(
    replay: Mapping[str, Any],
    training_signals: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    decision = _mapping(replay.get("decision"))
    required_signals = {
        "v30.training_signal.rbd_product_reading_acceptance",
        "v30.training_signal.rbd_distribution_replay_quality",
        "v30.training_signal.rbd_domain_coverage",
        "v30.training_signal.rbd_projection_safety",
        "v30.training_signal.rbd_core_claim_quality",
    }
    signal_ids = {str(row.get("signal_id") or "") for row in training_signals}
    queue_is_readonly = all(
        item.get("runtime_mutation_allowed") is False
        and item.get("chart_fact_mutation_allowed") is False
        and item.get("policy_pointer_promotion_allowed") is False
        for item in queue_items
    )
    signals_are_readonly = all(
        item.get("runtime_mutation_allowed") is False
        and item.get("chart_fact_mutation_allowed") is False
        and item.get("policy_pointer_promotion_allowed") is False
        for item in training_signals
    )
    return [
        {
            "check_id": "s111_distribution_replay_ready",
            "passed": replay.get("version") == REAL_BAZI_DISTRIBUTION_REPLAY_VERSION
            and decision.get("distribution_replay_ready") is True
            and decision.get("decision_status") == "rbd_s111_distribution_replay_ready",
            "observed": {
                "version": replay.get("version"),
                "status": replay.get("status"),
                "decision_status": decision.get("decision_status"),
            },
        },
        {
            "check_id": "required_training_signals_present",
            "passed": required_signals.issubset(signal_ids) and len(training_signals) >= 4,
            "observed": {"signal_ids": sorted(signal_ids), "signal_count": len(training_signals)},
        },
        {
            "check_id": "calibration_queue_evidence_backed",
            "passed": all(
                int(item.get("observed_failure_count", 0) or 0) >= 1 and bool(item.get("evidence_case_ids"))
                for item in queue_items
            ),
            "observed": {
                "queued_item_count": len(queue_items),
                "queue_item_ids": [str(item.get("queue_item_id") or "") for item in queue_items],
            },
        },
        {
            "check_id": "queue_and_signals_are_readonly_candidates",
            "passed": signals_are_readonly and queue_is_readonly,
            "observed": {
                "signals_are_readonly": signals_are_readonly,
                "queue_is_readonly": queue_is_readonly,
                "auto_apply_training_allowed": False,
            },
        },
        {
            "check_id": "heavy_gates_remain_explicit",
            "passed": True,
            "observed": {
                "full_pytest_required": False,
                "synthetic_all_required": False,
                "full_518k_required": False,
            },
        },
    ]


def _decision(
    checks: list[Mapping[str, Any]],
    training_signals: list[Mapping[str, Any]],
    queue_items: list[Mapping[str, Any]],
) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "training_calibration_queue_ready": ready,
        "decision_status": (
            "rbd_s112_training_calibration_queue_ready"
            if ready
            else "rbd_s112_training_calibration_queue_blocked"
        ),
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "blockers": ["rbd_training_calibration_queue_checks_failed"] if failed else [],
        "training_signal_count": len(training_signals),
        "queued_item_count": len(queue_items),
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "chart_fact_mutation_allowed": False,
        "auto_apply_training_allowed": False,
        "policy_pointer_promotion_allowed": False,
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("training_calibration_queue_ready"):
        return {
            "task_id": "RBD-S1.13",
            "title": "RBD Mainline Closeout And Steady State",
            "selected_track": "real_bazi_diagnosis",
            "scope": [
                "freeze RBD acceptance evidence into mainline docs",
                "define steady-state cadence for replay and calibration review",
                "keep queue items read-only until evidence review approves tuning",
            ],
        }
    return {
        "task_id": "RBD-S1.12-FR",
        "title": "RBD Training Signal Queue Failure Review",
        "selected_track": "real_bazi_diagnosis",
        "scope": ["repair upstream replay or queue evidence before closeout"],
    }


def _upstream_summary(replay: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "version": str(replay.get("version") or ""),
        "status": str(replay.get("status") or ""),
        "decision": dict(_mapping(replay.get("decision"))),
        "real_case_summary": dict(_mapping(replay.get("real_case_summary"))),
        "sample_518k_summary": dict(_mapping(replay.get("sample_518k_summary"))),
    }


def _failed_domain_counts(replay: Mapping[str, Any]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in _rows(replay):
        source = str(row.get("source") or "unknown_source")
        for domain in _list(row.get("failed_domains")):
            counts[source][str(domain)] += 1
    return {source: dict(domain_counts) for source, domain_counts in sorted(counts.items())}


def _failed_quality_domain_counts(replay: Mapping[str, Any]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in _rows(replay):
        source = str(row.get("source") or "unknown_source")
        for domain in _list(row.get("failed_quality_domains")):
            counts[source][str(domain)] += 1
    return {source: dict(domain_counts) for source, domain_counts in sorted(counts.items())}


def _rows(replay: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []
    for key in ("real_case_rows", "sample_518k_rows"):
        value = replay.get(key)
        if isinstance(value, list):
            rows.extend(row for row in value if isinstance(row, Mapping))
    return rows


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _float(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
