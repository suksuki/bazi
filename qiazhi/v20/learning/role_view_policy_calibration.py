from __future__ import annotations

from v20.learning.role_question_click_training import build_role_question_click_training_report
from v20.learning.role_view_policy_replay import build_role_view_policy_replay_report
from v20.storage.local_jsonl import LocalJsonlStore


CALIBRATION_VERSION = "v20.role_view_policy_calibration_report.v1"


def build_role_view_policy_calibration_report(
    *,
    click_training_report: dict[str, object] | None = None,
    replay_report: dict[str, object] | None = None,
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    clicks = click_training_report or build_role_question_click_training_report(store=store)
    replay = replay_report or build_role_view_policy_replay_report(store=store)
    reward = _reward_observation(clicks)
    ab = replay.get("ab_test_summary", {}) if isinstance(replay.get("ab_test_summary"), dict) else {}
    comparison_count = int(replay.get("comparison_count", 0) or 0)
    thresholds = _suggested_thresholds(
        click_count=int(clicks.get("click_count", 0) or 0),
        comparison_count=comparison_count,
        reward_average=float(reward.get("reward_average", 0.0) or 0.0),
        ab_risk_count=int(ab.get("risk_count", 0) or 0),
    )
    return {
        "version": CALIBRATION_VERSION,
        "status": "ready" if clicks.get("status") == "ready" and replay.get("status") == "ready_for_review" else "not_enough_data",
        "source_click_count": clicks.get("click_count", 0),
        "source_comparison_count": comparison_count,
        "reward_observation": reward,
        "ab_observation": {
            "candidate_win": bool(ab.get("candidate_win", False)),
            "net_lift": float(ab.get("net_lift", 0.0) or 0.0),
            "average_lift": float(ab.get("average_lift", 0.0) or 0.0),
            "risk_count": int(ab.get("risk_count", 0) or 0),
        },
        "suggested_thresholds": thresholds,
        "calibration_note": _calibration_note(thresholds),
        "runtime_mutation": False,
        "guardrails": [
            "ROLE_VIEW_POLICY_CALIBRATION_IS_OFFLINE_ONLY",
            "CALIBRATION_SUGGESTS_THRESHOLDS_ONLY",
            "NO_RUNTIME_POINTER_WRITE",
            "NO_CHART_FACT_MUTATION",
            "NO_RULE_TRUTH_MUTATION",
        ],
    }


def _reward_observation(report: dict[str, object]) -> dict[str, object]:
    summaries = report.get("reward_summaries", ())
    total_samples = 0
    reward_total = 0.0
    positive = 0
    negative = 0
    if isinstance(summaries, list):
        for row in summaries:
            if not isinstance(row, dict):
                continue
            sample_count = int(row.get("sample_count", 0) or 0)
            total_samples += sample_count
            reward_total += float(row.get("reward_total", 0.0) or 0.0)
            positive += int(row.get("positive_count", 0) or 0)
            negative += int(row.get("negative_count", 0) or 0)
    return {
        "sample_count": total_samples,
        "reward_total": round(reward_total, 3),
        "reward_average": round(reward_total / max(1, total_samples), 3),
        "positive_count": positive,
        "negative_count": negative,
    }


def _suggested_thresholds(
    *,
    click_count: int,
    comparison_count: int,
    reward_average: float,
    ab_risk_count: int,
) -> dict[str, object]:
    min_comparisons = 3
    if click_count >= 30 and comparison_count >= 5:
        min_comparisons = 5
    elif click_count >= 12 and comparison_count >= 4:
        min_comparisons = 4
    min_score_average = 0.2
    if ab_risk_count > 0:
        min_score_average = 0.3
    elif reward_average < 0.4:
        min_score_average = 0.25
    min_ab_net_lift = 0.1 if comparison_count >= min_comparisons else 0.0
    return {
        "min_promotion_comparisons": min_comparisons,
        "min_offline_score_average": min_score_average,
        "min_ab_net_lift": min_ab_net_lift,
        "max_ab_risk_count": 0,
        "runtime_allowed": False,
    }


def _calibration_note(thresholds: dict[str, object]) -> str:
    return (
        f"min comparisons {thresholds.get('min_promotion_comparisons')}; "
        f"min score avg {thresholds.get('min_offline_score_average')}; "
        f"min A/B lift {thresholds.get('min_ab_net_lift')}; "
        f"max risk {thresholds.get('max_ab_risk_count')}"
    )
