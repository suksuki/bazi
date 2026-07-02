from __future__ import annotations

from v40.contracts.base import AssertionLevel, Polarity, Topic
from v40.contracts.signal import RuntimeSignal, SignalSource


DOMAIN_TOPICS = {
    Topic.CAREER,
    Topic.WEALTH,
    Topic.RELATIONSHIP,
    Topic.HEALTH,
    Topic.TIMING,
    Topic.USEFUL_GOD,
    Topic.HIDDEN_ATTRIBUTE,
}

CORE_TOPICS = {Topic.STRUCTURE, Topic.USEFUL_GOD, Topic.TIMING}


def build_domain_adapter_signals(
    *,
    reading_id: str,
    signals: list[RuntimeSignal],
    topics: list[Topic],
) -> list[RuntimeSignal]:
    adapter_signals: list[RuntimeSignal] = []
    for topic in topics:
        if topic not in DOMAIN_TOPICS:
            continue
        topic_signals = _topic_material(signals=signals, topic=topic)
        if not topic_signals:
            continue
        adapter_signals.append(_adapter_signal(reading_id=reading_id, topic=topic, signals=topic_signals))
    return adapter_signals


def _topic_material(*, signals: list[RuntimeSignal], topic: Topic) -> list[RuntimeSignal]:
    material = [signal for signal in signals if signal.topic == topic or signal.topic in CORE_TOPICS]
    ranked = sorted(material, key=_score, reverse=True)
    return ranked[:5]


def _adapter_signal(*, reading_id: str, topic: Topic, signals: list[RuntimeSignal]) -> RuntimeSignal:
    return RuntimeSignal(
        signal_id=f"{reading_id}:domain-adapter:{topic.value}",
        reading_id=reading_id,
        source=SignalSource.BAZI_ENGINE,
        source_ref="domain_verdict_adapter",
        topic=topic,
        claim=_domain_claim(topic=topic, signals=signals),
        claim_key=f"domain_adapter.{topic.value}",
        polarity=_domain_polarity(signals),
        strength=_domain_strength(signals),
        confidence=_domain_confidence(signals),
        assertion_hint=_domain_assertion(signals),
        evidence_refs=_evidence_refs(signals),
        counter_evidence_refs=_counter_evidence_refs(signals),
        trainable_targets=[
            f"domain_adapter.{topic.value}.claim_score",
            f"advice_priority.{topic.value}",
            f"signal_weight.domain_adapter.{topic.value}",
        ],
    )


def _domain_claim(*, topic: Topic, signals: list[RuntimeSignal]) -> str:
    text = " ".join(signal.claim for signal in signals)
    if topic == Topic.CAREER:
        if _has_any(text, ["官", "责任", "压力", "资质", "平台"]):
            return "事业领域先看压力是否能被资质、平台、流程和稳定交付承接，再判断稳定或突破。"
        return "事业领域先把结构、用神和时运入口合参，不直接把机会说成结果。"
    if topic == Topic.WEALTH:
        if _has_any(text, ["财", "输出", "食神", "伤官", "资源"]):
            return "财运领域先看资源入口、输出方式和分配边界，收益判断必须绑定可承接路径。"
        return "财运领域不宜只看机会大小，先确认钱从哪里来、风险由谁承担。"
    if topic == Topic.RELATIONSHIP:
        if _has_any(text, ["财星", "官杀", "合", "冲", "害", "破"]):
            return "关系领域先看关系星与地支互动，再落到相处节奏、边界和承诺推进。"
        return "关系领域先按互动节奏和边界校准，不用单一十神强断关系结果。"
    if topic == Topic.HEALTH:
        if _has_any(text, ["冲", "害", "破", "刑", "压力", "作息"]):
            return "健康领域只把刑冲害破当作压力和节奏线索，建议落到作息、消耗和反馈观察。"
        return "健康领域当前证据偏轻，先观察压力、作息和身体反馈，不下病症断语。"
    if topic == Topic.TIMING:
        return "时运领域把大运流年作为触发背景，先看触发的是职责、资源、关系还是身体节奏。"
    if topic == Topic.USEFUL_GOD:
        return "用神领域保留候选分支，用根气、月令、藏干和现实反馈逐步拉开权重。"
    if topic == Topic.HIDDEN_ATTRIBUTE:
        return "隐藏线索领域只在命盘表层解释不足时启动 Probe，用反复经历校准暗线。"
    return "领域 adapter 只整理证据口径，最终结论仍由 DecisionEngine 生成。"


def _domain_polarity(signals: list[RuntimeSignal]) -> Polarity:
    if any(signal.polarity == Polarity.MIXED for signal in signals):
        return Polarity.MIXED
    if any(signal.polarity == Polarity.SUPPORT for signal in signals):
        return Polarity.SUPPORT
    return Polarity.NEUTRAL


def _domain_strength(signals: list[RuntimeSignal]) -> float:
    if not signals:
        return 0.42
    top = max(_score(signal) for signal in signals)
    coverage_bonus = min(0.12, len(signals) * 0.02)
    return round(max(0.48, min(0.82, top + coverage_bonus)), 2)


def _domain_confidence(signals: list[RuntimeSignal]) -> float:
    if not signals:
        return 0.42
    avg = sum(signal.confidence for signal in signals) / len(signals)
    evidence_bonus = min(0.1, sum(1 for signal in signals if signal.evidence_refs) * 0.02)
    return round(max(0.5, min(0.78, avg + evidence_bonus)), 2)


def _domain_assertion(signals: list[RuntimeSignal]) -> AssertionLevel:
    if any(signal.assertion_hint == AssertionLevel.MIXED for signal in signals):
        return AssertionLevel.MIXED
    if _domain_confidence(signals) >= 0.58:
        return AssertionLevel.SUPPORTED
    return AssertionLevel.WEAK_CANDIDATE


def _evidence_refs(signals: list[RuntimeSignal]) -> list[str]:
    refs: list[str] = []
    for signal in signals[:4]:
        refs.append(signal.signal_id)
        refs.extend(signal.evidence_refs[:4])
    return _unique(refs)


def _counter_evidence_refs(signals: list[RuntimeSignal]) -> list[str]:
    refs: list[str] = []
    for signal in signals[:4]:
        refs.extend(signal.counter_evidence_refs[:3])
    return _unique(refs)


def _score(signal: RuntimeSignal) -> float:
    return round(signal.strength * 0.55 + signal.confidence * 0.45, 4)


def _has_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def _unique(rows: list[str]) -> list[str]:
    result: list[str] = []
    for row in rows:
        if row and row not in result:
            result.append(row)
    return result
