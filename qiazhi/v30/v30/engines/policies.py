from __future__ import annotations

from v30.contracts import RoleKey
from v30.engines.contracts import EngineKey, EngineMode, EnginePlan, EnginePlanItem
from v30.production.contracts import BaziDomain, BaziTopic


_TOPIC_KEYWORDS: tuple[tuple[BaziTopic, BaziDomain, tuple[str, ...]], ...] = (
    (BaziTopic.WEALTH, BaziDomain.WEALTH, ("财", "钱", "收入", "赚钱", "投资", "资产")),
    (BaziTopic.CAREER, BaziDomain.CAREER, ("事业", "工作", "职业", "岗位", "创业", "转型")),
    (BaziTopic.RELATIONSHIP, BaziDomain.RELATIONSHIP, ("感情", "婚姻", "关系", "伴侣", "恋爱")),
    (BaziTopic.HEALTH, BaziDomain.HEALTH, ("健康", "身体", "压力", "过劳", "恢复")),
    (BaziTopic.MOBILITY, BaziDomain.MOBILITY, ("迁移", "外地", "出国", "搬家", "流动")),
    (BaziTopic.PROPERTY, BaziDomain.PROPERTY, ("房", "田宅", "不动产", "居住", "家庭资产")),
    (BaziTopic.TIMING, BaziDomain.TIMING, ("今年", "大运", "流年", "什么时候", "时间")),
)


def infer_engine_plan(
    *,
    reading_id: str,
    user_question: str = "",
    role: RoleKey = "user",
    topic: BaziTopic | None = None,
    domain: BaziDomain | None = None,
    include_ziwei_sidecar: bool = True,
    include_reality_probe: bool = True,
) -> EnginePlan:
    inferred_topic, inferred_domain = _infer_topic_domain(user_question)
    topic = topic or inferred_topic
    domain = domain or inferred_domain
    items = [
        EnginePlanItem(
            engine=EngineKey.BAZI,
            mode=EngineMode.DECISION_AUX,
            required=True,
            reason="八字是当前 V30 主引擎，负责输出主结构、规则、路径、画像和可裁决信号。",
            topics=[topic],
            domains=[domain],
            decision_weight=1.0,
            output_weight=1.0,
        )
    ]
    if include_ziwei_sidecar and _ziwei_applies(topic, domain):
        items.append(
            EnginePlanItem(
                engine=EngineKey.ZIWEI,
                mode=EngineMode.SIGNAL_SIDECAR,
                required=False,
                reason="紫微作为 Domain Lens，只提供领域旁路信号和 Probe 候选，V1 不参与裁决。",
                topics=[topic],
                domains=[domain],
                decision_weight=0.0,
                output_weight=0.2,
            )
        )
    if include_reality_probe:
        items.append(
            EnginePlanItem(
                engine=EngineKey.REALITY_PROBE,
                mode=EngineMode.PROBE_TRIGGER,
                required=False,
                reason="现实探针用于校准显化方式、隐藏属性和下一轮智能对话。",
                topics=[topic],
                domains=[domain],
                decision_weight=0.4,
                output_weight=0.5,
            )
        )
    return EnginePlan(
        plan_id=f"{reading_id}:engine-plan:v1",
        reading_id=reading_id,
        role=role,
        user_question=user_question,
        topic=topic,
        domain=domain,
        time_scope=_infer_time_scope(user_question),
        items=items,
        decision_policy={
            "bazi": 1.0,
            "ziwei": 0.0,
            "reality_probe": 0.4 if include_reality_probe else 0.0,
            "llm": 0.0,
        },
    )


def _infer_topic_domain(question: str) -> tuple[BaziTopic, BaziDomain]:
    for topic, domain, keywords in _TOPIC_KEYWORDS:
        if any(keyword in question for keyword in keywords):
            return topic, domain
    return BaziTopic.UNKNOWN, BaziDomain.OVERVIEW


def _infer_time_scope(question: str) -> str:
    if any(keyword in question for keyword in ("今年", "流年", "202", "203")):
        return "current_year"
    if any(keyword in question for keyword in ("大运", "十年")):
        return "current_luck"
    return "natal"


def _ziwei_applies(topic: BaziTopic, domain: BaziDomain) -> bool:
    return topic in {
        BaziTopic.WEALTH,
        BaziTopic.CAREER,
        BaziTopic.RELATIONSHIP,
        BaziTopic.HEALTH,
        BaziTopic.MOBILITY,
        BaziTopic.PROPERTY,
        BaziTopic.TIMING,
        BaziTopic.UNKNOWN,
    } or domain in {
        BaziDomain.WEALTH,
        BaziDomain.CAREER,
        BaziDomain.RELATIONSHIP,
        BaziDomain.HEALTH,
        BaziDomain.MOBILITY,
        BaziDomain.PROPERTY,
        BaziDomain.TIMING,
        BaziDomain.OVERVIEW,
    }
