from __future__ import annotations

from typing import Callable

from v20.learning.corpus_runtime_pointer import build_corpus_runtime_pointer
from v20.learning.knowledge_runtime_pointer import build_knowledge_runtime_pointer
from v20.learning.portrait_runtime_pointer import build_portrait_runtime_pointer
from v20.learning.question_runtime_pointer import build_question_runtime_pointer
from v20.learning.rule_runtime_pointer import build_rule_runtime_pointer
from v20.orchestrator.runtime_policy import build_runtime_policy_pointer
from v20.role_view.runtime_pointer import build_role_view_runtime_pointer


PointerBuilder = Callable[[], dict[str, object]]


POINTER_FAMILIES: tuple[dict[str, object], ...] = (
    {
        "family": "orchestrator",
        "label": "中枢策略",
        "builder": lambda: build_runtime_policy_pointer(brain_memory_signal={}),
        "pointer_path": "training/orchestrator_policy_versions/active_pointer.json",
        "expected_consumers": ("api.runtime", "orchestrator.mainline", "orchestrator.question_focus"),
        "runtime_consumer_status": "consumed",
    },
    {
        "family": "role_view",
        "label": "角色体验",
        "builder": build_role_view_runtime_pointer,
        "pointer_path": "training/role_view_policy_versions/active_pointer.json",
        "expected_consumers": ("api.runtime", "role_view.projection"),
        "runtime_consumer_status": "consumed",
    },
    {
        "family": "question",
        "label": "智能问答",
        "builder": build_question_runtime_pointer,
        "pointer_path": "training/question_policy_versions/active_pointer.json",
        "expected_consumers": ("interaction.question_ranker",),
        "runtime_consumer_status": "consumed",
    },
    {
        "family": "corpus",
        "label": "特征语料",
        "builder": build_corpus_runtime_pointer,
        "pointer_path": "training/corpus_policy_versions/active_pointer.json",
        "expected_consumers": ("corpus.artifacts.find_similar_cases",),
        "runtime_consumer_status": "consumed",
    },
    {
        "family": "rule",
        "label": "规则迭代",
        "builder": build_rule_runtime_pointer,
        "pointer_path": "training/rule_policy_versions/active_pointer.json",
        "expected_consumers": ("rules.engine", "decision.defeasible_model"),
        "runtime_consumer_status": "consumed",
    },
    {
        "family": "portrait",
        "label": "画像策略",
        "builder": build_portrait_runtime_pointer,
        "pointer_path": "training/portrait_policy_versions/active_pointer.json",
        "expected_consumers": ("interaction.portrait_projection", "role_view.projection"),
        "runtime_consumer_status": "consumed",
    },
    {
        "family": "knowledge",
        "label": "知识映射",
        "builder": build_knowledge_runtime_pointer,
        "pointer_path": "training/knowledge_policy_versions/active_pointer.json",
        "expected_consumers": ("decision.knowledge_bridge", "knowledge.rule_library"),
        "runtime_consumer_status": "consumed",
    },
)


def build_runtime_consumption_audit() -> dict[str, object]:
    rows = [_audit_family(row) for row in POINTER_FAMILIES]
    consumed = sum(1 for row in rows if row["runtime_consumer_status"] == "consumed")
    active = sum(1 for row in rows if row["runtime_applied"] is True)
    effect = _pointer_effect_summary(rows)
    return {
        "version": "v20.runtime_consumption_audit.v1",
        "status": "complete" if consumed == len(rows) else "needs_runtime_consumers",
        "family_count": len(rows),
        "consumed_family_count": consumed,
        "active_family_count": active,
        "consumption_percent": round(consumed / max(1, len(rows)) * 100),
        "active_percent": round(active / max(1, len(rows)) * 100),
        "pointer_effect_summary": effect,
        "families": rows,
        "next_actions": _next_actions(rows),
        "runtime_mutation": False,
        "guardrails": [
            "RUNTIME_CONSUMPTION_AUDIT_READ_ONLY",
            "NO_POINTER_WRITE_FROM_AUDIT",
            "NO_USER_TEXT_RENDERED",
            "CONSUMPTION_STATUS_MUST_BE_EXPLICIT",
            "POINTER_EFFECT_SUMMARY_EXPLAINS_BEFORE_AFTER_RUNTIME_USE",
        ],
    }


def _audit_family(spec: dict[str, object]) -> dict[str, object]:
    builder = spec["builder"]
    try:
        pointer = builder()
    except Exception as exc:
        pointer = {
            "version": "v20.runtime_pointer_unavailable.v1",
            "status": "error",
            "runtime_applied": False,
            "blocking_gate": f"pointer_build_failed:{exc}",
            "runtime_mutation": False,
        }
    payload = pointer.get("policy_payload", {}) if isinstance(pointer.get("policy_payload"), dict) else {}
    return {
        "family": spec["family"],
        "label": spec["label"],
        "pointer_version": pointer.get("version", ""),
        "pointer_status": pointer.get("status", ""),
        "active_policy_version": pointer.get("active_policy_version", ""),
        "candidate_policy_version": pointer.get("candidate_policy_version", ""),
        "rollback_policy_version": pointer.get("rollback_policy_version", ""),
        "runtime_applied": bool(pointer.get("runtime_applied")),
        "runtime_allowed": bool(pointer.get("runtime_allowed")),
        "runtime_consumer_status": spec["runtime_consumer_status"],
        "expected_consumers": list(spec["expected_consumers"]),
        "pointer_path": spec["pointer_path"],
        "payload_counts": _payload_counts(payload),
        "effect_scope": _effect_scope(str(spec["family"])),
        "before_after_effect": _before_after_effect(pointer),
        "blocking_gate": str(pointer.get("blocking_gate", "")),
        "runtime_mutation": False,
    }


def _pointer_effect_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    active = [row for row in rows if row["runtime_applied"] is True]
    blocked = [row for row in rows if row["runtime_applied"] is not True]
    return {
        "version": "v20.runtime_pointer_effect_summary.v1",
        "status": "active" if active else "baseline_only",
        "active_pointer_count": len(active),
        "blocked_pointer_count": len(blocked),
        "active_scopes": tuple(dict.fromkeys(scope for row in active for scope in row.get("effect_scope", ()))),
        "summary": (
            f"{len(active)} 个 runtime pointer 已被运行时消费；{len(blocked)} 个仍在 baseline 或 gate 阻断。"
            if active
            else "当前运行时主要使用 baseline；训练候选需要通过中枢调参包和 writer 后才会影响测算。"
        ),
        "runtime_mutation": False,
    }


def _effect_scope(family: str) -> tuple[str, ...]:
    return {
        "orchestrator": ("中枢主线", "问题聚焦", "结构动态排序"),
        "role_view": ("角色展示", "问题语气", "回答治理"),
        "question": ("智能问题排序", "问题来源", "DAG 跳转"),
        "corpus": ("相似案例", "特征语料", "518K 分布"),
        "rule": ("规则权重", "裁决主线", "结构动态"),
        "portrait": ("画像轴排序", "主题投射", "角色画像"),
        "knowledge": ("知识映射", "规则解释", "回答边界"),
    }.get(family, ())


def _before_after_effect(pointer: dict[str, object]) -> dict[str, object]:
    active = str(pointer.get("active_policy_version", ""))
    candidate = str(pointer.get("candidate_policy_version", ""))
    rollback = str(pointer.get("rollback_policy_version", ""))
    runtime_applied = bool(pointer.get("runtime_applied"))
    return {
        "version": "v20.runtime_pointer_before_after_effect.v1",
        "before_policy_version": rollback or "baseline",
        "active_policy_version": active or "baseline",
        "candidate_policy_version": candidate,
        "effect_status": "active_candidate_consumed" if runtime_applied else "baseline_or_blocked",
        "runtime_mutation": False,
    }


def _payload_counts(payload: dict[str, object]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key, value in sorted(payload.items()):
        if isinstance(value, list | tuple):
            counts[key] = len(value)
        elif isinstance(value, dict):
            counts[key] = len(value)
        elif value:
            counts[key] = 1
        else:
            counts[key] = 0
    return counts


def _next_actions(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    actions = []
    for row in rows:
        if row["runtime_consumer_status"] != "consumed":
            actions.append(
                {
                    "family": row["family"],
                    "action": "connect_runtime_consumer",
                    "target": ",".join(str(item) for item in row["expected_consumers"]),
                    "blocking_gate": row["blocking_gate"],
                }
            )
    return actions
