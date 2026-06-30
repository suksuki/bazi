from __future__ import annotations

from v40.contracts.base import AssertionLevel, EngineKey, EngineMode, Polarity, Topic
from v40.contracts.chart import ZiweiChartFacts
from v40.contracts.engine import EngineRunRequest, EngineRunResult
from v40.contracts.signal import RuntimeSignal, SignalSource


def run_native_ziwei_engine(*, engine_request: EngineRunRequest, chart: ZiweiChartFacts) -> EngineRunResult:
    facts = [
        {"fact_id": "ziwei.life_palace", "label": "命宫", "value": chart.life_palace},
        {"fact_id": "ziwei.body_palace", "label": "身宫", "value": chart.body_palace},
        {"fact_id": "ziwei.major_stars", "label": "主星", "value": chart.major_stars},
        {"fact_id": "ziwei.palace_notes", "label": "宫位提示", "value": chart.palace_notes},
    ]
    features = [
        {
            "feature_id": "ziwei.domain_lenses",
            "label": "领域旁路",
            "value": chart.domain_lenses,
        }
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
                evidence_refs=["ziwei.life_palace", "ziwei.body_palace", "ziwei.domain_lenses"],
                role_visibility=["practitioner", "admin"],
                trainable_targets=["signal_weight.ziwei_domain_lens"],
            )
        )
    return signals


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
