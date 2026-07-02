from __future__ import annotations

from v40.contracts.training import BatchTrainerV1Result, ThresholdChange, WeightChange


def build_direct_training_activation_evidence(*, result: BatchTrainerV1Result) -> dict[str, object]:
    rollback_ready = bool(result.rollback_registry_id and result.candidate_registry.rollback_available)
    regression_clean = not result.impact_diff.regression_failures
    direct_activation_ready = result.active_policy_applied and rollback_ready and regression_clean
    return {
        "version": "v40.direct_training_activation_evidence.v1",
        "training_run_id": result.training_run_id,
        "base_policy_version": result.base_policy_version,
        "candidate_policy_version": result.candidate_policy_version,
        "active_policy_applied": result.active_policy_applied,
        "active_policy_version": result.candidate_registry.active_policy_version,
        "previous_policy_version": result.previous_policy_version,
        "rollback_registry_id": result.rollback_registry_id,
        "rollback_ready": rollback_ready,
        "changed_unit_count": result.changed_unit_count,
        "weight_changes": [_change_row(change) for change in result.impact_diff.changed_weights],
        "threshold_changes": [_threshold_row(change) for change in result.impact_diff.changed_thresholds],
        "changed_probe_policy_count": len(result.impact_diff.changed_probe_policies),
        "changed_advice_priority_count": len(result.impact_diff.changed_advice_priorities),
        "affected_counts": {
            "signals": len(result.impact_diff.affected_signals),
            "branches": len(result.impact_diff.affected_branches),
            "verdicts": len(result.impact_diff.affected_verdicts),
            "advice": len(result.impact_diff.affected_advice),
            "probes": len(result.impact_diff.affected_probes),
        },
        "improvement_summary": result.impact_diff.improvement_summary,
        "risk_summary": result.impact_diff.risk_summary,
        "regression_failures": result.impact_diff.regression_failures,
        "release_recommendation": result.impact_diff.release_recommendation.value,
        "automatic_status": "ready" if direct_activation_ready else "needs_replay_or_rollback",
        "next_actions": _next_actions(result=result, rollback_ready=rollback_ready, regression_clean=regression_clean),
        "writes_v30_state": False,
        "writes_v40_production": False,
        "boundary": "direct_training_activation_evidence_explains_active_policy_without_applying_or_rolling_back",
    }


def _change_row(change: WeightChange) -> dict[str, object]:
    return {
        "target_id": change.target_id,
        "before": change.before,
        "after": change.after,
        "delta": round(change.after - change.before, 4),
        "direction": _direction(change.before, change.after),
        "reason": change.reason,
    }


def _threshold_row(change: ThresholdChange) -> dict[str, object]:
    return {
        "target_id": change.target_id,
        "before": change.before,
        "after": change.after,
        "delta": round(change.after - change.before, 4),
        "direction": _direction(change.before, change.after),
        "reason": change.reason,
    }


def _direction(before: float, after: float) -> str:
    if after > before:
        return "up"
    if after < before:
        return "down"
    return "same"


def _next_actions(*, result: BatchTrainerV1Result, rollback_ready: bool, regression_clean: bool) -> list[str]:
    actions: list[str] = []
    if not result.active_policy_applied:
        actions.append("训练结果尚未成为 active policy，需要重新运行 BatchTrainerV1。")
    if not rollback_ready:
        actions.append("补齐 rollback_registry_id，确保可回滚。")
    if not regression_clean:
        actions.append("先处理 regression failures，再继续观察 active policy。")
    if result.impact_diff.risk_summary:
        actions.append("用 replay / acceptance window 观察本次 active policy 的风险摘要。")
    if not actions:
        actions.append("训练已直接生效且具备回滚指针，下一步进入 replay 与真实案例验收。")
    return actions
