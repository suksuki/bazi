from __future__ import annotations

from collections import Counter

from v40.contracts.base import AssertionLevel, Polarity, Topic
from v40.contracts.signal import RuntimeSignal, SignalSource


SIDECAR_ENRICHMENT_POLICY_VERSION = "v40.sidecar_enrichment.v1"
EXPLANATION_ONLY_SOURCE_REFS = {
    "knowledge_card_enrichment_v1",
    "ziwei_sidecar_enrichment_v1",
}

DOMAIN_TOPICS = [
    Topic.CAREER,
    Topic.WEALTH,
    Topic.RELATIONSHIP,
    Topic.HEALTH,
    Topic.TIMING,
    Topic.USEFUL_GOD,
    Topic.HIDDEN_ATTRIBUTE,
]


def build_sidecar_enrichment_signals(
    *,
    reading_id: str,
    bazi_signals: list[RuntimeSignal],
    ziwei_signals: list[RuntimeSignal] | None = None,
) -> list[RuntimeSignal]:
    if not bazi_signals:
        return []
    ziwei_rows = ziwei_signals or []
    return [
        *_build_knowledge_card_signals(reading_id=reading_id, signals=bazi_signals),
        *_build_portrait_signals(reading_id=reading_id, signals=bazi_signals),
        *_build_ziwei_sidecar_enrichment(reading_id=reading_id, bazi_signals=bazi_signals, ziwei_signals=ziwei_rows),
    ]


def _build_knowledge_card_signals(*, reading_id: str, signals: list[RuntimeSignal]) -> list[RuntimeSignal]:
    topics = _rank_topics(signals)
    rows: list[RuntimeSignal] = []
    for index, topic in enumerate(topics[:2], start=1):
        topic_signals = [signal for signal in signals if signal.topic == topic]
        if not topic_signals:
            continue
        rows.append(
            RuntimeSignal(
                signal_id=f"{reading_id}:knowledge-card:{topic.value}:{index}",
                reading_id=reading_id,
                source=SignalSource.BAZI_ENGINE,
                source_ref="knowledge_card_enrichment_v1",
                topic=topic,
                claim=_knowledge_claim(topic, topic_signals),
                claim_key=f"knowledge_card.{topic.value}",
                polarity=Polarity.NEUTRAL,
                strength=0.34,
                confidence=0.56,
                assertion_hint=AssertionLevel.WEAK_CANDIDATE,
                evidence_refs=_evidence_refs(topic_signals, prefix="knowledge"),
                role_visibility=["user", "practitioner", "admin", "lab"],
                trainable_targets=[
                    f"knowledge_card.{topic.value}.acceptance",
                    f"explanation_basis.{topic.value}.priority",
                ],
            )
        )
    return rows


def _build_portrait_signals(*, reading_id: str, signals: list[RuntimeSignal]) -> list[RuntimeSignal]:
    topic = _portrait_topic(signals)
    topic_signals = [signal for signal in signals if signal.topic in {topic, Topic.STRUCTURE, Topic.USEFUL_GOD}]
    if not topic_signals:
        return []
    return [
        RuntimeSignal(
            signal_id=f"{reading_id}:portrait:{topic.value}",
            reading_id=reading_id,
            source=SignalSource.BAZI_ENGINE,
            source_ref="portrait_signal_enrichment_v1",
            topic=topic,
            claim=_portrait_claim(topic, topic_signals),
            claim_key=f"portrait_signal.{topic.value}",
            polarity=Polarity.NEUTRAL,
            strength=0.44,
            confidence=0.50,
            assertion_hint=AssertionLevel.WEAK_CANDIDATE,
            evidence_refs=_evidence_refs(topic_signals, prefix="portrait"),
            role_visibility=["user", "practitioner", "admin", "lab"],
            trainable_targets=[
                f"portrait_weight.{topic.value}",
                f"signal_weight.portrait.{topic.value}",
                f"claim_score.portrait.{topic.value}",
            ],
        )
    ]


def _build_ziwei_sidecar_enrichment(
    *,
    reading_id: str,
    bazi_signals: list[RuntimeSignal],
    ziwei_signals: list[RuntimeSignal],
) -> list[RuntimeSignal]:
    if not ziwei_signals:
        return []
    bazi_topics = {signal.topic for signal in bazi_signals if signal.topic in DOMAIN_TOPICS}
    rows: list[RuntimeSignal] = []
    for index, ziwei_signal in enumerate(ziwei_signals[:3], start=1):
        if ziwei_signal.topic not in DOMAIN_TOPICS:
            continue
        agreement = ziwei_signal.topic in bazi_topics
        rows.append(
            RuntimeSignal(
                signal_id=f"{reading_id}:ziwei-sidecar-enrichment:{ziwei_signal.topic.value}:{index}",
                reading_id=reading_id,
                source=SignalSource.ZIWEI_ENGINE,
                source_ref="ziwei_sidecar_enrichment_v1",
                topic=ziwei_signal.topic,
                claim=_ziwei_enrichment_claim(ziwei_signal=ziwei_signal, agreement=agreement),
                claim_key=f"ziwei_sidecar.{ziwei_signal.topic.value}",
                polarity=Polarity.NEUTRAL,
                strength=0.36 if agreement else 0.30,
                confidence=0.48 if agreement else 0.42,
                assertion_hint=AssertionLevel.WEAK_CANDIDATE,
                evidence_refs=[ziwei_signal.signal_id, *ziwei_signal.evidence_refs[:5]],
                role_visibility=["practitioner", "admin", "lab"],
                trainable_targets=[
                    "signal_weight.ziwei_sidecar_enrichment",
                    f"ziwei_lens.{ziwei_signal.topic.value}.agreement",
                ],
            )
        )
    return rows


def _rank_topics(signals: list[RuntimeSignal]) -> list[Topic]:
    counter: Counter[Topic] = Counter()
    for signal in signals:
        if signal.topic in DOMAIN_TOPICS or signal.topic in {Topic.STRUCTURE, Topic.USEFUL_GOD}:
            counter[signal.topic] += 1
    if not counter:
        return [Topic.STRUCTURE]
    return [topic for topic, _ in counter.most_common()]


def _portrait_topic(signals: list[RuntimeSignal]) -> Topic:
    for topic in DOMAIN_TOPICS:
        if any(signal.topic == topic for signal in signals):
            return topic
    return Topic.STRUCTURE


def _knowledge_claim(topic: Topic, signals: list[RuntimeSignal]) -> str:
    label = _topic_label(topic)
    if topic == Topic.USEFUL_GOD:
        return "知识卡：用神候选必须结合月令、根气、藏干和现实反馈逐步拉开权重，不能把候选直接说成唯一答案。"
    if topic == Topic.TIMING:
        return "知识卡：大运流年先作为触发背景，只能在事件线索集中时提高年份判断权重。"
    if topic == Topic.STRUCTURE:
        return "知识卡：结构强弱是领域判断入口，但需要十神、地支关系和反证共同约束。"
    return f"知识卡：{label}判断必须绑定可回放证据、反证和现实反馈，不允许脱离命盘素材直接下结论。"


def _portrait_claim(topic: Topic, signals: list[RuntimeSignal]) -> str:
    text = " ".join(signal.claim for signal in signals[:4])
    label = _topic_label(topic)
    if _has_any(text, ["官", "责任", "压力", "平台", "资质"]):
        return f"画像提示：{label}更容易围绕责任承接、规则压力和平台资源展开；这只是排序线索，不能替代主断。"
    if _has_any(text, ["财", "资源", "输出", "分配"]):
        return f"画像提示：{label}更容易围绕资源入口、输出方式和分配边界展开；这只是低权重画像信号。"
    if _has_any(text, ["合", "冲", "刑", "害", "破", "关系"]):
        return f"画像提示：{label}更容易受互动节奏和边界反复影响；需要现实反馈校准。"
    return f"画像提示：{label}当前只形成低权重倾向，后续必须由 verdict evidence 和用户反馈约束。"


def _ziwei_enrichment_claim(*, ziwei_signal: RuntimeSignal, agreement: bool) -> str:
    label = _topic_label(ziwei_signal.topic)
    if agreement:
        return f"紫微旁路增强：紫微在{label}主题上与八字信号同向，可作为命理师校准参考，但不参与最终裁决。"
    return f"紫微旁路增强：紫微在{label}主题上提供额外观察，只作为追问和命理师 Lens 参考。"


def _evidence_refs(signals: list[RuntimeSignal], *, prefix: str) -> list[str]:
    refs: list[str] = [f"{prefix}.sidecar_enrichment"]
    for signal in signals[:4]:
        refs.append(signal.signal_id)
        refs.extend(signal.evidence_refs[:4])
    return _unique(refs)


def _topic_label(topic: Topic) -> str:
    return {
        Topic.STRUCTURE: "结构",
        Topic.USEFUL_GOD: "用神",
        Topic.TIMING: "时运",
        Topic.WEALTH: "财务",
        Topic.CAREER: "事业",
        Topic.RELATIONSHIP: "关系",
        Topic.HEALTH: "健康",
        Topic.FAMILY: "家庭",
        Topic.HIDDEN_ATTRIBUTE: "隐藏线索",
    }.get(topic, "命局")


def _has_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def _unique(rows: list[str]) -> list[str]:
    result: list[str] = []
    for row in rows:
        if row and row not in result:
            result.append(row)
    return result
