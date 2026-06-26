from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

from v30.validation.synthetic_case import SyntheticValidationResult, SyntheticValidationSuiteResult, run_synthetic_tier
from v30.validation.training_signals import SyntheticTrainingSignal, extract_training_signals


FROZEN_CORE_CALIBRATION_REVIEW_VERSION = "v30.frozen_core_calibration_review.v1"

DEFAULT_FROZEN_CORE_CALIBRATION_TIERS = (
    "m1_m2_bazi_calculation",
    "m3_core_spine",
    "ten_god_energy_calibration",
    "m4_ten_god_real_case_replay",
    "real_case_calibration_pack",
    "interaction_loop",
)

DEFAULT_REQUIRED_SIGNAL_IDS = (
    "v30.training_signal.m1_m2_base_fact_contract",
    "v30.training_signal.m3_core_spine_coverage",
    "v30.training_signal.ten_god_energy_fusion",
    "v30.training_signal.ranked_decision_fusion",
    "v30.training_signal.real_case_calibration_pack",
    "v30.training_signal.m5_weight_replay",
    "v30.training_signal.practical_reading_quality",
    "v30.training_signal.api_projection_contract",
    "v30.training_signal.interaction_loop_quality",
)


def run_frozen_core_calibration_review(
    *,
    tiers: Sequence[str] = DEFAULT_FROZEN_CORE_CALIBRATION_TIERS,
    required_signal_ids: Sequence[str] = DEFAULT_REQUIRED_SIGNAL_IDS,
) -> dict[str, Any]:
    suite_results = {tier: run_synthetic_tier(tier) for tier in tiers}
    combined = _combined_suite_result(suite_results.values())
    signals = extract_training_signals(combined)
    return build_frozen_core_calibration_review(
        suite_results=suite_results,
        training_signals=signals,
        required_signal_ids=required_signal_ids,
    )


def build_frozen_core_calibration_review(
    *,
    suite_results: Mapping[str, SyntheticValidationSuiteResult | Mapping[str, Any]],
    training_signals: Sequence[SyntheticTrainingSignal | Mapping[str, Any]] = (),
    required_signal_ids: Sequence[str] = DEFAULT_REQUIRED_SIGNAL_IDS,
) -> dict[str, Any]:
    normalized_suites = {
        str(tier): _suite_summary(result)
        for tier, result in suite_results.items()
    }
    normalized_signals = [_signal_summary(signal) for signal in training_signals]
    decision = _decision(
        suite_summaries=normalized_suites,
        signal_summaries=normalized_signals,
        required_signal_ids=required_signal_ids,
    )
    return {
        "version": FROZEN_CORE_CALIBRATION_REVIEW_VERSION,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "decision": decision,
        "frozen_core_scope": {
            "module_count": 8,
            "completion_state": "M1-M8_100_percent_current_scope_frozen",
            "deterministic_chart_fact_mutation_allowed": False,
            "core_completion_track_open": False,
            "boundary": "frozen_core_scope_reopens_only_on_targeted_validation_regression",
        },
        "synthetic_tier_summary": normalized_suites,
        "training_signal_summary": _training_signal_summary(normalized_signals, required_signal_ids),
        "policy_boundary": {
            "policy_pointer_promotion_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "llm_fact_generation_allowed": False,
            "boundary": "f1_review_is_read_only_and_does_not_mutate_policy_or_chart_facts",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "frozen_core_calibration_review_validates_calibration_readiness_without_reopening_core_completion",
    }


def _combined_suite_result(results: Iterable[SyntheticValidationSuiteResult]) -> SyntheticValidationSuiteResult:
    rows: list[SyntheticValidationResult] = []
    for result in results:
        rows.extend(result.results)
    passed_count = sum(1 for row in rows if row.passed)
    failed_count = len(rows) - passed_count
    return SyntheticValidationSuiteResult(
        suite_id="v30.synthetic.frozen_core_calibration_combined",
        passed=failed_count == 0,
        case_count=len(rows),
        passed_count=passed_count,
        failed_count=failed_count,
        results=rows,
    )


def _suite_summary(result: SyntheticValidationSuiteResult | Mapping[str, Any]) -> dict[str, Any]:
    payload = result.model_dump(mode="json") if isinstance(result, SyntheticValidationSuiteResult) else dict(result)
    return {
        "suite_id": str(payload.get("suite_id") or ""),
        "passed": bool(payload.get("passed")),
        "case_count": int(payload.get("case_count", 0) or 0),
        "passed_count": int(payload.get("passed_count", 0) or 0),
        "failed_count": int(payload.get("failed_count", 0) or 0),
    }


def _signal_summary(signal: SyntheticTrainingSignal | Mapping[str, Any]) -> dict[str, Any]:
    payload = signal.model_dump(mode="json") if isinstance(signal, SyntheticTrainingSignal) else dict(signal)
    return {
        "signal_id": str(payload.get("signal_id") or ""),
        "domain": str(payload.get("domain") or ""),
        "signal_type": str(payload.get("signal_type") or ""),
        "strength": float(payload.get("strength", 0.0) or 0.0),
        "source_case_count": len(payload.get("source_case_ids", []) or []),
        "payload": payload.get("payload", {}) if isinstance(payload.get("payload"), dict) else {},
    }


def _decision(
    *,
    suite_summaries: Mapping[str, dict[str, Any]],
    signal_summaries: Sequence[dict[str, Any]],
    required_signal_ids: Sequence[str],
) -> dict[str, Any]:
    blockers: list[str] = []
    if not suite_summaries:
        blockers.append("frozen_core_calibration_tiers_not_run")
    failed_tiers = [
        tier for tier, summary in suite_summaries.items()
        if not summary.get("passed") or int(summary.get("failed_count", 0) or 0) > 0
    ]
    if failed_tiers:
        blockers.append("synthetic_calibration_tiers_failed")
    signal_ids = {row["signal_id"] for row in signal_summaries if row.get("signal_id")}
    missing_signal_ids = [signal_id for signal_id in required_signal_ids if signal_id not in signal_ids]
    if missing_signal_ids:
        blockers.append("required_training_signals_missing")
    failure_signal_count = sum(
        1 for row in signal_summaries
        if row.get("signal_id") == "v30.training_signal.synthetic_failure_cluster"
    )
    if failure_signal_count:
        blockers.append("synthetic_failure_cluster_signal_present")
    ready = not blockers
    return {
        "calibration_baseline_ready": ready,
        "core_reopen_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "decision_status": "ready_for_targeted_calibration_iteration" if ready else "calibration_baseline_blocked",
        "blockers": blockers,
        "failed_tiers": failed_tiers,
        "missing_required_signal_ids": missing_signal_ids,
        "failure_signal_count": failure_signal_count,
        "rationale": (
            "Frozen M1-M8 core has enough synthetic and training-signal evidence for targeted calibration iteration without reopening deterministic chart facts."
            if ready
            else "Frozen-core calibration needs the listed evidence before starting targeted tuning."
        ),
    }


def _training_signal_summary(
    signal_summaries: Sequence[dict[str, Any]],
    required_signal_ids: Sequence[str],
) -> dict[str, Any]:
    signal_ids = {row["signal_id"] for row in signal_summaries if row.get("signal_id")}
    return {
        "signal_count": len(signal_summaries),
        "required_signal_count": len(required_signal_ids),
        "required_signal_ready_count": sum(1 for signal_id in required_signal_ids if signal_id in signal_ids),
        "required_signal_ids": list(required_signal_ids),
        "missing_required_signal_ids": [signal_id for signal_id in required_signal_ids if signal_id not in signal_ids],
        "signal_ids": sorted(signal_ids),
        "boundary": "training_signals_tune_calibration_candidates_not_deterministic_chart_facts",
    }


def _next_selection(decision: dict[str, Any]) -> dict[str, Any]:
    if decision["calibration_baseline_ready"]:
        return {
            "task_id": "F2",
            "title": "Targeted Calibration Candidate Review",
            "selected_track": "targeted_calibration",
            "scope": [
                "review training-signal candidates for model weights, rule weights, question strategy, and expression only",
                "require synthetic all plus 518K sample before any pointer review",
                "keep deterministic chart facts and frozen M1-M8 completion sealed",
            ],
        }
    return {
        "task_id": "F1",
        "title": "Frozen Core Calibration Evidence Gap Closure",
        "selected_track": "targeted_calibration",
        "scope": [
            "rerun failing or missing calibration tiers",
            "restore required training signals",
            "do not reopen core modules unless a targeted validation regression proves it",
        ],
    }
