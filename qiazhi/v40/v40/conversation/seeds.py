from __future__ import annotations

from v40.contracts.base import RoleKey, Topic
from v40.contracts.output import ConversationSeed
from v40.contracts.runtime import RuntimeResult


def build_conversation_seeds(
    *,
    runtime: RuntimeResult,
    accepted_text: str,
    role_key: RoleKey = "user",
    limit: int = 3,
) -> list[ConversationSeed]:
    if not accepted_text.strip():
        return []
    rows: list[ConversationSeed] = []
    for probe in runtime.probes:
        rows.append(
            ConversationSeed(
                seed_id=f"seed:{probe.probe_id}",
                reading_id=runtime.reading_id,
                topic=probe.topic,
                question=probe.question,
                intent="resolve_probe",
                options=_options_for_topic(probe.topic),
                source_probe_ids=[probe.probe_id],
                source_verdict_ids=probe.target_verdict_ids,
                relevance_score=_score_probe(probe.expected_information_gain, probe.user_cost),
                role_visibility=_role_visibility(role_key),
            )
        )
    for verdict in runtime.verdicts:
        if len(rows) >= limit:
            break
        rows.append(
            ConversationSeed(
                seed_id=f"seed:{verdict.verdict_id}:explain",
                reading_id=runtime.reading_id,
                topic=verdict.topic,
                question=_explain_question(verdict.topic),
                intent="explain_verdict",
                options=["先看结论", "先看依据", "先看建议"],
                source_verdict_ids=[verdict.verdict_id],
                relevance_score=min(1.0, max(0.45, verdict.confidence)),
                role_visibility=_role_visibility(role_key),
            )
        )
    for advice in runtime.advice_plans:
        if len(rows) >= limit:
            break
        rows.append(
            ConversationSeed(
                seed_id=f"seed:{advice.advice_id}:action",
                reading_id=runtime.reading_id,
                topic=advice.topic,
                question=_action_question(advice.topic),
                intent="turn_advice_into_action",
                options=["先看行动", "先看风险", "先看节奏"],
                source_advice_ids=[advice.advice_id],
                relevance_score=min(1.0, max(0.42, advice.priority)),
                role_visibility=_role_visibility(role_key),
            )
        )
    return sorted(_dedupe(rows), key=lambda row: row.relevance_score, reverse=True)[:limit]


def _score_probe(information_gain: float, user_cost: float) -> float:
    return round(max(0.2, min(1.0, information_gain - user_cost + 0.35)), 4)


def _options_for_topic(topic: Topic) -> list[str]:
    options = {
        Topic.CAREER: ["稳定发展", "转型突破", "先看压力来源"],
        Topic.WEALTH: ["主动争取", "保守积累", "先看风险边界"],
        Topic.RELATIONSHIP: ["相处模式", "反复矛盾", "关系节奏"],
        Topic.HEALTH: ["压力消耗", "作息负荷", "身体反馈"],
        Topic.USEFUL_GOD: ["先看用神", "先看忌神", "先看反证"],
        Topic.HIDDEN_ATTRIBUTE: ["反复经历", "暗线校准", "暂不明显"],
    }
    return options.get(topic, ["先看结论", "先看风险", "先看建议"])


def _explain_question(topic: Topic) -> str:
    labels = {
        Topic.CAREER: "这条事业判断最关键的依据是什么？",
        Topic.WEALTH: "这条财运判断最关键的依据是什么？",
        Topic.RELATIONSHIP: "这条关系判断最关键的依据是什么？",
        Topic.HEALTH: "这条健康判断最关键的依据是什么？",
    }
    return labels.get(topic, "这个判断最关键的依据是什么？")


def _action_question(topic: Topic) -> str:
    labels = {
        Topic.CAREER: "事业上下一步最适合怎么做？",
        Topic.WEALTH: "财务上下一步最适合怎么做？",
        Topic.RELATIONSHIP: "关系里下一步最适合怎么处理？",
        Topic.HEALTH: "身心负荷下一步最需要先调整什么？",
    }
    return labels.get(topic, "下一步最适合怎么做？")


def _role_visibility(role_key: RoleKey) -> list[RoleKey]:
    if role_key == "practitioner":
        return ["practitioner"]
    return ["user", "practitioner"]


def _dedupe(rows: list[ConversationSeed]) -> list[ConversationSeed]:
    seen: set[str] = set()
    result: list[ConversationSeed] = []
    for row in rows:
        if row.question in seen:
            continue
        seen.add(row.question)
        result.append(row)
    return result
