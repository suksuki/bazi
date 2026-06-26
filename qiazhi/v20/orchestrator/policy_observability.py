from __future__ import annotations

from typing import Any


POLICY_OBSERVABILITY_VERSION = "v20.orchestrator_policy_observability.v1"


def build_policy_observability_summary(
    *,
    policy_pointer: dict[str, Any],
    mainline_arbitration: dict[str, Any],
    question_mainline_focus: dict[str, Any],
) -> dict[str, object]:
    mainline_effect = _effect(mainline_arbitration.get("runtime_policy_effect", {}))
    question_effect = _effect(question_mainline_focus.get("runtime_policy_effect", {}))
    consumers = (
        _consumer("mainline_arbitration", mainline_effect),
        _consumer("question_mainline_focus", question_effect),
    )
    applied = [row for row in consumers if row["status"] == "applied"]
    runtime_applied = bool(policy_pointer.get("runtime_applied"))
    fallback_active = not runtime_applied or str(policy_pointer.get("active_policy_version", "")) == str(policy_pointer.get("rollback_policy_version", ""))
    return {
        "version": POLICY_OBSERVABILITY_VERSION,
        "status": "candidate_consumed" if applied else ("baseline_active" if fallback_active else "candidate_active_no_consumer_match"),
        "active_policy_version": str(policy_pointer.get("active_policy_version", "")),
        "candidate_policy_version": str(policy_pointer.get("candidate_policy_version", "")),
        "rollback_policy_version": str(policy_pointer.get("rollback_policy_version", "")),
        "runtime_applied": runtime_applied,
        "fallback_active": fallback_active,
        "consumer_count": len(consumers),
        "applied_consumer_count": len(applied),
        "consumers": consumers,
        "observability_note": _note(runtime_applied, fallback_active, len(applied)),
        "runtime_mutation": False,
        "guardrails": [
            "POLICY_OBSERVABILITY_READ_ONLY",
            "NO_POLICY_WRITE_FROM_RUNTIME_OBSERVATION",
            "CONSUMER_EFFECTS_ARE_RERANK_ONLY",
            "ROLLBACK_POINTER_VISIBLE_TO_OPERATOR",
        ],
    }


def _effect(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def _consumer(module_key: str, effect: dict[str, object]) -> dict[str, object]:
    return {
        "module_key": module_key,
        "status": str(effect.get("status", "not_reported")),
        "active_policy_version": str(effect.get("active_policy_version", "")),
        "applied_adjustment_count": int(effect.get("applied_adjustment_count", 0) or 0),
        "domain_boost": float(effect.get("domain_boost", 0) or 0),
        "runtime_mutation": False,
    }


def _note(runtime_applied: bool, fallback_active: bool, applied_count: int) -> str:
    if fallback_active:
        return "当前使用 baseline 指针，候选策略尚未进入 runtime 消费。"
    if runtime_applied and applied_count:
        return "候选策略已进入 runtime，并被至少一个中枢模块消费。"
    if runtime_applied:
        return "候选策略已激活，但本轮没有匹配到可调整的中枢候选。"
    return "策略观测只读，不会写入或修改核心命盘事实。"
