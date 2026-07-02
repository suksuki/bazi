from __future__ import annotations

from collections import Counter

from v40.contracts.base import ReleaseRecommendation, Topic
from v40.contracts.evaluation import AcceptanceWindowResult, RealCaseRecord


REQUIRED_REAL_CASE_TOPICS = [
    Topic.CAREER,
    Topic.WEALTH,
    Topic.RELATIONSHIP,
    Topic.HEALTH,
    Topic.TIMING,
    Topic.USEFUL_GOD,
    Topic.HIDDEN_ATTRIBUTE,
]


def build_real_case_expansion_evidence_pack(
    *,
    cases: list[RealCaseRecord],
    acceptance_windows: list[AcceptanceWindowResult] | None = None,
    target_case_count: int = 100,
    min_cases_per_topic: int = 8,
    min_trainable_case_count: int = 20,
) -> dict[str, object]:
    windows = acceptance_windows or []
    topic_counts = _topic_counts(cases)
    coverage_gaps = _coverage_gaps(topic_counts=topic_counts, min_cases_per_topic=min_cases_per_topic)
    trainable_case_count = sum(1 for case in cases if case.allow_training_use)
    latest_window = windows[-1] if windows else None
    window_ready = _window_ready(latest_window)
    case_count_ready = len(cases) >= target_case_count
    trainable_ready = trainable_case_count >= min_trainable_case_count
    coverage_ready = not coverage_gaps
    automatic_ready = case_count_ready and trainable_ready and coverage_ready and window_ready
    return {
        "version": "v40.real_case_expansion_evidence_pack.v1",
        "case_count": len(cases),
        "target_case_count": target_case_count,
        "case_count_ready": case_count_ready,
        "trainable_case_count": trainable_case_count,
        "min_trainable_case_count": min_trainable_case_count,
        "trainable_case_ready": trainable_ready,
        "topic_counts": {topic.value: topic_counts.get(topic, 0) for topic in REQUIRED_REAL_CASE_TOPICS},
        "min_cases_per_topic": min_cases_per_topic,
        "coverage_gaps": coverage_gaps,
        "coverage_ready": coverage_ready,
        "acceptance_window_count": len(windows),
        "latest_acceptance_window": _window_summary(latest_window),
        "acceptance_window_ready": window_ready,
        "automatic_status": "ready" if automatic_ready else "blocked",
        "cutover_status": "ready_for_human_signoff" if automatic_ready else "blocked_by_real_case_evidence",
        "manual_signoff_required": ["真实命例质量判断", "线上切换窗口"],
        "next_collection_tasks": _next_collection_tasks(
            case_count=len(cases),
            target_case_count=target_case_count,
            trainable_case_count=trainable_case_count,
            min_trainable_case_count=min_trainable_case_count,
            coverage_gaps=coverage_gaps,
            latest_window=latest_window,
        ),
        "writes_v30_state": False,
        "writes_v40_production": False,
        "boundary": "real_case_expansion_evidence_reads_cases_and_windows_without_cutover_or_policy_write",
    }


def _topic_counts(cases: list[RealCaseRecord]) -> Counter[Topic]:
    counts: Counter[Topic] = Counter()
    for case in cases:
        topics = {case.topic} if case.topic not in {Topic.OVERVIEW, Topic.UNKNOWN} else set()
        topics.update(outcome.topic for outcome in case.expected_outcomes if outcome.topic != Topic.UNKNOWN)
        for topic in topics:
            counts[topic] += 1
    return counts


def _coverage_gaps(*, topic_counts: Counter[Topic], min_cases_per_topic: int) -> list[dict[str, object]]:
    gaps: list[dict[str, object]] = []
    for topic in REQUIRED_REAL_CASE_TOPICS:
        count = topic_counts.get(topic, 0)
        if count >= min_cases_per_topic:
            continue
        gaps.append(
            {
                "topic": topic.value,
                "current": count,
                "required": min_cases_per_topic,
                "missing": min_cases_per_topic - count,
            }
        )
    return gaps


def _window_ready(window: AcceptanceWindowResult | None) -> bool:
    if window is None:
        return False
    if window.recommendation != ReleaseRecommendation.APPROVE:
        return False
    if window.blocked_count:
        return False
    if window.average_overclaim_rate > 0:
        return False
    return window.average_overall_score >= 0.78


def _window_summary(window: AcceptanceWindowResult | None) -> dict[str, object]:
    if window is None:
        return {
            "available": False,
            "recommendation": "missing",
            "ready": False,
        }
    return {
        "available": True,
        "window_id": window.window_id,
        "candidate_version": window.candidate_version,
        "case_count": window.case_count,
        "passed_count": window.passed_count,
        "review_count": window.review_count,
        "blocked_count": window.blocked_count,
        "average_overall_score": window.average_overall_score,
        "average_overclaim_rate": window.average_overclaim_rate,
        "recommendation": window.recommendation.value,
        "ready": _window_ready(window),
        "failed_reason_counts": window.failed_reason_counts,
    }


def _next_collection_tasks(
    *,
    case_count: int,
    target_case_count: int,
    trainable_case_count: int,
    min_trainable_case_count: int,
    coverage_gaps: list[dict[str, object]],
    latest_window: AcceptanceWindowResult | None,
) -> list[str]:
    tasks: list[str] = []
    if case_count < target_case_count:
        tasks.append(f"补充 {target_case_count - case_count} 个真实命例。")
    if trainable_case_count < min_trainable_case_count:
        tasks.append(f"至少再补 {min_trainable_case_count - trainable_case_count} 个允许训练使用的命例。")
    for gap in coverage_gaps[:5]:
        tasks.append(f"补齐 {gap['topic']} 主题真实命例，还缺 {gap['missing']} 个。")
    if latest_window is None:
        tasks.append("用最新候选版本运行一次 Acceptance Window。")
    elif not _window_ready(latest_window):
        tasks.append("处理最新 Acceptance Window 的 review/block 原因，再重新跑验收窗口。")
    return tasks or ["真实案例证据已满足自动门槛，等待人工确认上线窗口。"]
