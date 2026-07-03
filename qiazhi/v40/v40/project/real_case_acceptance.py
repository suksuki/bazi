from __future__ import annotations

from collections import Counter
from typing import Any

from v40.contracts.base import ReleaseRecommendation, Topic
from v40.contracts.evaluation import AcceptanceWindowResult, RealCaseRecord


def build_real_case_acceptance_pack(
    *,
    cases: list[RealCaseRecord],
    acceptance_window: AcceptanceWindowResult | None,
    real_case_evidence: dict[str, Any],
    online_cutover_decision: dict[str, Any],
    min_owner_review_case_count: int = 1,
) -> dict[str, object]:
    evidence = _unwrap_payload(real_case_evidence, "evidence")
    cutover = _unwrap_payload(online_cutover_decision, "decision")
    topic_counts = _topic_counts(cases)
    window_summary = _window_summary(acceptance_window)
    failed_reason_counts = dict(sorted((acceptance_window.failed_reason_counts if acceptance_window else {}).items()))
    hints = _trainable_hints(acceptance_window)
    status = _acceptance_status(
        cases=cases,
        acceptance_window=acceptance_window,
        real_case_evidence=evidence,
        online_cutover_decision=cutover,
        min_owner_review_case_count=min_owner_review_case_count,
    )
    blockers = _blockers(
        cases=cases,
        acceptance_window=acceptance_window,
        real_case_evidence=evidence,
        online_cutover_decision=cutover,
        min_owner_review_case_count=min_owner_review_case_count,
    )
    return {
        "version": "v40.real_case_acceptance_pack.v1",
        "acceptance_status": status,
        "case_count": len(cases),
        "min_owner_review_case_count": min_owner_review_case_count,
        "trainable_case_count": sum(1 for case in cases if case.allow_training_use),
        "topic_counts": {topic.value: count for topic, count in sorted(topic_counts.items(), key=lambda item: item[0].value)},
        "window": window_summary,
        "real_case_evidence_status": str(evidence.get("automatic_status", "unknown")),
        "real_case_cutover_status": str(evidence.get("cutover_status", "unknown")),
        "online_cutover_decision_status": str(cutover.get("decision_status", "unknown")),
        "failed_reason_counts": failed_reason_counts,
        "trainable_attribution_hints": hints,
        "owner_review_required": status == "ready_for_owner_review",
        "manual_signoff_required": [
            "真实命例质量判断",
            "LLM 表达质量抽检",
            "beta 切换窗口",
        ],
        "blockers": blockers,
        "next_actions": _next_actions(status=status, blockers=blockers, hints=hints),
        "writes_v30_state": False,
        "writes_v40_production": False,
        "traffic_switch_allowed_by_system": False,
        "boundary": "real_case_acceptance_pack_reads_acceptance_evidence_without_cutover",
    }


def _unwrap_payload(payload: dict[str, Any], preferred_key: str) -> dict[str, Any]:
    nested = payload.get(preferred_key)
    if isinstance(nested, dict):
        return nested
    return payload


def _acceptance_status(
    *,
    cases: list[RealCaseRecord],
    acceptance_window: AcceptanceWindowResult | None,
    real_case_evidence: dict[str, Any],
    online_cutover_decision: dict[str, Any],
    min_owner_review_case_count: int,
) -> str:
    if len(cases) < min_owner_review_case_count:
        return "needs_more_cases"
    if acceptance_window is None:
        return "needs_replay"
    if acceptance_window.blocked_count or acceptance_window.average_overclaim_rate > 0:
        return "blocked_by_quality"
    if acceptance_window.recommendation == ReleaseRecommendation.REJECT:
        return "blocked_by_quality"
    if acceptance_window.review_count or acceptance_window.recommendation != ReleaseRecommendation.APPROVE:
        return "needs_replay"
    if real_case_evidence.get("automatic_status") != "ready":
        return "needs_more_cases"
    if online_cutover_decision.get("decision_status") != "ready_for_human_signoff":
        return "needs_replay"
    return "ready_for_owner_review"


def _blockers(
    *,
    cases: list[RealCaseRecord],
    acceptance_window: AcceptanceWindowResult | None,
    real_case_evidence: dict[str, Any],
    online_cutover_decision: dict[str, Any],
    min_owner_review_case_count: int,
) -> list[dict[str, object]]:
    blockers: list[dict[str, object]] = []
    if len(cases) < min_owner_review_case_count:
        blockers.append(
            {
                "key": "owner_review_case_count",
                "label": "Owner review case count",
                "current": len(cases),
                "required": min_owner_review_case_count,
                "action": "补齐用于 owner review 的真实命例。",
            }
        )
    if acceptance_window is None:
        blockers.append(
            {
                "key": "acceptance_window_missing",
                "label": "Acceptance window missing",
                "action": "用当前 runtime 跑一次 Acceptance Window。",
            }
        )
    else:
        if acceptance_window.blocked_count:
            blockers.append(
                {
                    "key": "acceptance_window_blocked",
                    "label": "Acceptance window blocked",
                    "current": acceptance_window.blocked_count,
                    "action": "先处理 blocked case，再重新跑验收窗口。",
                }
            )
        if acceptance_window.review_count:
            blockers.append(
                {
                    "key": "acceptance_window_review",
                    "label": "Acceptance window needs review",
                    "current": acceptance_window.review_count,
                    "action": "处理 review case 的失败原因，再重新跑验收窗口。",
                }
            )
        if acceptance_window.average_overclaim_rate > 0:
            blockers.append(
                {
                    "key": "acceptance_window_overclaim",
                    "label": "Acceptance window overclaim",
                    "current": acceptance_window.average_overclaim_rate,
                    "action": "消除过度断言，再重新跑验收窗口。",
                }
            )
    if real_case_evidence.get("automatic_status") != "ready":
        blockers.append(
            {
                "key": "real_case_evidence_not_ready",
                "label": "Real case evidence not ready",
                "current": str(real_case_evidence.get("automatic_status", "unknown")),
                "action": "补齐真实命例数量、主题覆盖、可训练案例和最新验收窗口。",
            }
        )
    if online_cutover_decision.get("decision_status") != "ready_for_human_signoff":
        blockers.append(
            {
                "key": "online_cutover_decision_not_ready",
                "label": "Online cutover decision not ready",
                "current": str(online_cutover_decision.get("decision_status", "unknown")),
                "action": "补齐上线决策包里的阻塞项。",
            }
        )
    return blockers


def _topic_counts(cases: list[RealCaseRecord]) -> Counter[Topic]:
    counts: Counter[Topic] = Counter()
    for case in cases:
        topics: set[Topic] = set()
        if case.topic not in {Topic.OVERVIEW, Topic.UNKNOWN}:
            topics.add(case.topic)
        for outcome in case.expected_outcomes:
            if outcome.topic != Topic.UNKNOWN:
                topics.add(outcome.topic)
        for topic in topics:
            counts[topic] += 1
    return counts


def _window_summary(window: AcceptanceWindowResult | None) -> dict[str, object]:
    if window is None:
        return {"available": False, "ready": False}
    return {
        "available": True,
        "ready": _window_ready(window),
        "window_id": window.window_id,
        "candidate_version": window.candidate_version,
        "case_count": window.case_count,
        "passed_count": window.passed_count,
        "review_count": window.review_count,
        "blocked_count": window.blocked_count,
        "average_overall_score": window.average_overall_score,
        "average_overclaim_rate": window.average_overclaim_rate,
        "average_llm_expression_clarity_score": window.average_llm_expression_clarity_score,
        "recommendation": window.recommendation.value,
    }


def _window_ready(window: AcceptanceWindowResult) -> bool:
    return (
        window.recommendation == ReleaseRecommendation.APPROVE
        and window.blocked_count == 0
        and window.review_count == 0
        and window.average_overclaim_rate == 0
    )


def _trainable_hints(window: AcceptanceWindowResult | None) -> list[str]:
    if window is None:
        return []
    hints: set[str] = set()
    for result in window.case_results:
        hints.update(result.trainable_attribution_hints)
    return sorted(hints)


def _next_actions(*, status: str, blockers: list[dict[str, object]], hints: list[str]) -> list[str]:
    if status == "ready_for_owner_review":
        return [
            "安排 owner 逐案抽检真实命例质量。",
            "抽检 LLM 报告和一问一答表达。",
            "确认 beta 切换窗口与 rollback 指针。",
        ]
    actions = [str(blocker["action"]) for blocker in blockers]
    if hints:
        actions.append("把 trainable_attribution_hints 送入训练影响 review。")
    return list(dict.fromkeys(actions))
