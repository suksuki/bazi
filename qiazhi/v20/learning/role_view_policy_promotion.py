from __future__ import annotations

from typing import Any

from v20.learning.role_view_policy_replay import build_role_view_policy_replay_report
from v20.storage.local_jsonl import LocalJsonlStore


MIN_PROMOTION_COMPARISONS = 3
MIN_OFFLINE_SCORE_AVERAGE = 0.2


def build_role_view_policy_promotion_gate(
    *,
    replay_report: dict[str, object] | None = None,
    calibration_report: dict[str, object] | None = None,
    store: LocalJsonlStore | None = None,
    runtime_rollout_switch: bool = False,
) -> dict[str, Any]:
    replay = replay_report or build_role_view_policy_replay_report(store=store)
    replay_result = replay.get("replay_result", {}) if isinstance(replay.get("replay_result"), dict) else {}
    impact = replay.get("impact_summary", {}) if isinstance(replay.get("impact_summary"), dict) else {}
    ab_summary = replay.get("ab_test_summary", {}) if isinstance(replay.get("ab_test_summary"), dict) else {}
    comparison_count = int(replay.get("comparison_count", 0) or 0)
    positive_count = int(replay_result.get("positive_score_count", 0) or 0)
    negative_count = int(replay_result.get("negative_score_count", 0) or 0)
    score_average = float(impact.get("offline_score_average", 0.0) or 0.0)
    ab_net_lift = float(ab_summary.get("net_lift", 0.0) or 0.0)
    ab_risk_count = int(ab_summary.get("risk_count", 0) or 0)
    thresholds = _thresholds(calibration_report)
    checks = (
        _check("candidate_replay_ready", replay.get("status") == "ready_for_review"),
        _check("minimum_comparisons", comparison_count >= thresholds["min_promotion_comparisons"]),
        _check("positive_reward_margin", positive_count >= negative_count),
        _check("offline_score_average", score_average >= thresholds["min_offline_score_average"]),
        _check("ab_candidate_lift", ab_net_lift > thresholds["min_ab_net_lift"]),
        _check("ab_no_negative_risk", ab_risk_count <= thresholds["max_ab_risk_count"]),
        _check("runtime_rollout_switch", runtime_rollout_switch, "" if runtime_rollout_switch else "runtime_rollout_switch_disabled_until_pointer_write_path"),
    )
    failures = tuple(row["check_key"] for row in checks if not row["ok"])
    return {
        "version": "v20.role_view_policy_promotion_gate.v1",
        "status": "blocked" if failures else "eligible",
        "eligible_for_runtime": not failures,
        "candidate_policy_version": replay.get("candidate_policy_version", ""),
        "baseline_policy_version": replay.get("baseline_policy_version", ""),
        "comparison_count": comparison_count,
        "positive_score_count": positive_count,
        "negative_score_count": negative_count,
        "offline_score_average": score_average,
        "ab_net_lift": ab_net_lift,
        "ab_risk_count": ab_risk_count,
        "calibration_version": str((calibration_report or {}).get("version", "")) if isinstance(calibration_report, dict) else "",
        "applied_thresholds": thresholds,
        "checks": checks,
        "failure_count": len(failures),
        "failures": failures,
        "blocking_gate": failures[0] if failures else "",
        "runtime_mutation": False,
        "guardrails": [
            "ROLE_VIEW_POLICY_PROMOTION_GATE_IS_READ_ONLY",
            "ROLE_VIEW_POLICY_PROMOTION_USES_CALIBRATED_THRESHOLDS",
            "NO_RUNTIME_POINTER_WRITE_FROM_GATE",
            "NO_CHART_FACT_MUTATION",
            "NO_RULE_TRUTH_MUTATION",
        ],
    }


def _check(check_key: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {
        "check_key": check_key,
        "ok": bool(ok),
        "detail": detail,
    }


def _thresholds(calibration_report: dict[str, object] | None) -> dict[str, float]:
    source = calibration_report.get("suggested_thresholds", {}) if isinstance(calibration_report, dict) else {}
    if not isinstance(source, dict):
        source = {}
    return {
        "min_promotion_comparisons": float(source.get("min_promotion_comparisons", MIN_PROMOTION_COMPARISONS) or MIN_PROMOTION_COMPARISONS),
        "min_offline_score_average": float(source.get("min_offline_score_average", MIN_OFFLINE_SCORE_AVERAGE) or MIN_OFFLINE_SCORE_AVERAGE),
        "min_ab_net_lift": float(source.get("min_ab_net_lift", 0.0) or 0.0),
        "max_ab_risk_count": float(source.get("max_ab_risk_count", 0.0) or 0.0),
    }
