from __future__ import annotations

from v40.contracts.base import AssertionLevel, EngineKey, EngineMode, Polarity, Topic
from v40.contracts.chart import ZiweiChartFacts
from v40.contracts.engine import EngineRunRequest, EngineRunResult
from v40.contracts.signal import RuntimeSignal, SignalSource


DOMAIN_PALACE_MAP: dict[Topic, list[str]] = {
    Topic.WEALTH: ["财帛", "官禄", "迁移", "田宅", "交友", "福德"],
    Topic.CAREER: ["官禄", "命宫", "迁移", "父母", "交友", "财帛"],
    Topic.RELATIONSHIP: ["夫妻", "命宫", "福德", "财帛", "迁移", "交友"],
    Topic.HEALTH: ["疾厄", "福德", "命宫", "官禄", "财帛"],
    Topic.FAMILY: ["父母", "兄弟", "田宅", "子女", "福德"],
    Topic.TIMING: ["迁移", "命宫", "官禄", "财帛", "田宅", "交友"],
    Topic.HIDDEN_ATTRIBUTE: ["福德", "疾厄", "命宫", "迁移"],
}

DOMAIN_PROBES: dict[Topic, str] = {
    Topic.WEALTH: "你的赚钱机会更常来自固定工资、项目客户、合伙团队，还是资产配置？",
    Topic.CAREER: "你的事业压力更常来自平台制度、职责边界、外部机会，还是团队协作？",
    Topic.RELATIONSHIP: "亲密关系里，现实条件、距离变化、责任分工或情绪安全感哪一项影响更大？",
    Topic.HEALTH: "最近更明显的是工作压力传导、作息恢复不足，还是财务/责任带来的精神负担？",
    Topic.TIMING: "重要机会更多来自本地稳定环境，还是外地、跨地区、远程客户或外部平台？",
    Topic.FAMILY: "家庭与资产议题更像支持来源，还是责任、居住或现金流压力？",
    Topic.HIDDEN_ATTRIBUTE: "是否有反复出现但不容易从表层经历解释的压力、机会或关系模式？",
}


def run_native_ziwei_engine(*, engine_request: EngineRunRequest, chart: ZiweiChartFacts) -> EngineRunResult:
    facts = [
        {"fact_id": "ziwei.life_palace", "label": "命宫", "value": chart.life_palace},
        {"fact_id": "ziwei.body_palace", "label": "身宫", "value": chart.body_palace},
        {"fact_id": "ziwei.palaces", "label": "十二宫", "value": chart.palaces},
        {"fact_id": "ziwei.major_stars", "label": "主星", "value": chart.major_stars},
        {"fact_id": "ziwei.annual_transformations", "label": "四化", "value": chart.annual_transformations},
        {"fact_id": "ziwei.decade_luck", "label": "大限", "value": chart.decade_luck},
        {"fact_id": "ziwei.flow_year", "label": "流年", "value": chart.flow_year},
        {"fact_id": "ziwei.palace_notes", "label": "宫位提示", "value": chart.palace_notes},
    ]
    features = [
        {
            "feature_id": "ziwei.domain_lenses",
            "label": "领域旁路",
            "value": chart.domain_lenses,
        },
        {
            "feature_id": "ziwei.domain_palace_map",
            "label": "领域宫位映射",
            "value": {topic.value: palaces for topic, palaces in DOMAIN_PALACE_MAP.items()},
        },
    ]
    signals = _build_domain_lens_signals(
        reading_id=engine_request.reading_id,
        chart=chart,
    )
    return EngineRunResult(
        result_id=f"ziwei-native:{engine_request.reading_id}",
        reading_id=engine_request.reading_id,
        engine=EngineKey.ZIWEI,
        mode=EngineMode.SIGNAL_SIDECAR,
        engine_version="v40.ziwei_domain_lens.v1",
        facts=facts,
        features=features,
        signals=signals,
        probe_candidates=_build_probe_candidates(signals),
        warnings=["ziwei_domain_lens_v1_is_sidecar_only_and_has_zero_decision_weight"],
        decision_weight=0.0,
    )


def _build_domain_lens_signals(*, reading_id: str, chart: ZiweiChartFacts) -> list[RuntimeSignal]:
    signals: list[RuntimeSignal] = []
    for index, (raw_topic, claim) in enumerate(chart.domain_lenses.items(), start=1):
        clean_claim = claim.strip()
        if not clean_claim:
            continue
        topic = _topic(raw_topic)
        signals.append(
            RuntimeSignal(
                signal_id=f"{reading_id}:ziwei:{topic.value}:{index}",
                reading_id=reading_id,
                source=SignalSource.ZIWEI_ENGINE,
                source_ref="native_ziwei_domain_lens_v1",
                topic=topic,
                claim=f"紫微旁路提示：{clean_claim}",
                polarity=Polarity.NEUTRAL,
                strength=0.42,
                confidence=0.42,
                assertion_hint=AssertionLevel.WEAK_CANDIDATE,
                evidence_refs=_evidence_refs(topic),
                role_visibility=["practitioner", "admin"],
                trainable_targets=["signal_weight.ziwei_domain_lens"],
            )
        )
    return signals


def _build_probe_candidates(signals: list[RuntimeSignal]) -> list[dict[str, object]]:
    probes: list[dict[str, object]] = []
    for signal in signals:
        question = DOMAIN_PROBES.get(signal.topic, "")
        if not question:
            continue
        probes.append(
            {
                "version": "v40.ziwei_probe_trigger.v1",
                "topic": signal.topic.value,
                "question": question,
                "source_signal_id": signal.signal_id,
                "reason": "紫微旁路只触发现实校准问题，不直接生成用户断语。",
                "expected_information_gain": 0.48,
                "user_cost": 0.22,
            }
        )
    return probes


def _evidence_refs(topic: Topic) -> list[str]:
    refs = ["ziwei.life_palace", "ziwei.body_palace", "ziwei.domain_lenses"]
    for palace in DOMAIN_PALACE_MAP.get(topic, []):
        refs.append(f"ziwei.palace.{palace}")
    return refs


def _topic(value: str) -> Topic:
    normalized = value.strip().lower()
    aliases = {
        "career": Topic.CAREER,
        "事业": Topic.CAREER,
        "wealth": Topic.WEALTH,
        "财运": Topic.WEALTH,
        "relationship": Topic.RELATIONSHIP,
        "感情": Topic.RELATIONSHIP,
        "health": Topic.HEALTH,
        "健康": Topic.HEALTH,
        "family": Topic.FAMILY,
        "亲情": Topic.FAMILY,
        "timing": Topic.TIMING,
        "时运": Topic.TIMING,
        "hidden_attribute": Topic.HIDDEN_ATTRIBUTE,
        "隐藏线索": Topic.HIDDEN_ATTRIBUTE,
        "overview": Topic.OVERVIEW,
        "总览": Topic.OVERVIEW,
    }
    return aliases.get(normalized, Topic.UNKNOWN)
