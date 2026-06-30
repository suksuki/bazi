from __future__ import annotations

from v40.contracts.base import AssertionLevel, EngineKey, EngineMode, Polarity, RoleKey, Topic
from v40.contracts.chart import BaziChartFacts
from v40.contracts.engine import EnginePlan, EnginePlanItem, EngineRunRequest, EngineRunResult, MultiEngineRunResult
from v40.contracts.runtime import RuntimeRequest, RuntimeResult
from v40.contracts.signal import RuntimeSignal, SignalRegistrySnapshot, SignalSource
from v40.decision import build_decision_output
from v40.engines.bazi_adapters import (
    BRANCH_ELEMENTS,
    DRAINING_ELEMENTS,
    STEM_ELEMENTS,
    SUPPORTING_ELEMENTS,
    build_branch_relation_profile,
    build_ten_god_profile,
    build_useful_god_profile,
)
from v40.presentation import build_product_projection, build_surface_bundle


def build_native_bazi_runtime(
    *,
    request_id: str,
    reading_id: str,
    chart: BaziChartFacts,
    user_question: str = "",
    topic: Topic = Topic.OVERVIEW,
    role_key: RoleKey = "user",
) -> RuntimeResult:
    request = RuntimeRequest(
        request_id=request_id,
        reading_id=reading_id,
        role_key=role_key,
        user_question=user_question,
        topic=topic,
        birth_input_ref=chart.chart_id,
    )
    engine_request = EngineRunRequest(
        request_id=f"engine:{request_id}",
        reading_id=reading_id,
        engine=EngineKey.BAZI,
        mode=EngineMode.SIGNAL_SIDECAR,
        topic=topic,
        role_key=role_key,
        user_question=user_question,
        input_refs=[chart.chart_id],
        engine_context={"chart_facts": chart.model_dump(mode="json")},
    )
    engine_result = run_native_bazi_engine(engine_request=engine_request, chart=chart)
    registry = SignalRegistrySnapshot(
        registry_id=f"registry:{reading_id}",
        reading_id=reading_id,
        signals=engine_result.signals,
    )
    plan = EnginePlan(
        plan_id=f"plan:{reading_id}",
        reading_id=reading_id,
        role_key=role_key,
        user_question=user_question,
        topic=topic,
        items=[
            EnginePlanItem(
                engine=EngineKey.BAZI,
                mode=EngineMode.SIGNAL_SIDECAR,
                required=True,
                reason="V40 原生八字引擎提供事实、特征和信号素材",
                topics=[topic],
                decision_weight=1.0,
                output_weight=1.0,
            )
        ],
    )
    multi_engine = MultiEngineRunResult(
        reading_id=reading_id,
        plan=plan,
        results=[engine_result],
        signal_registry=registry,
    )
    decision_output = build_decision_output(
        reading_id=reading_id,
        registry=registry,
        topic=topic,
        role_key=role_key,
        user_question=user_question,
    )
    product_projection = build_product_projection(
        reading_id=reading_id,
        role_key=role_key,
        verdicts=decision_output.verdicts,
        advice_plans=decision_output.advice_plans,
        branches=decision_output.branch_candidates,
    )
    return RuntimeResult(
        reading_id=reading_id,
        request=request,
        engine_result=multi_engine,
        signal_registry=registry,
        decision_input=decision_output.input_bundle,
        branches=decision_output.branch_candidates,
        verdicts=decision_output.verdicts,
        advice_plans=decision_output.advice_plans,
        probes=decision_output.probes,
        product_projection=product_projection,
        surface_bundle=build_surface_bundle(
            reading_id=reading_id,
            role_key=role_key,
            projection=product_projection,
            probes=decision_output.probes,
            signal_count=len(registry.signals),
            branch_count=len(decision_output.branch_candidates),
        ),
    )


def run_native_bazi_engine(*, engine_request: EngineRunRequest, chart: BaziChartFacts) -> EngineRunResult:
    day_element = STEM_ELEMENTS.get(chart.day_stem, "未知")
    month_element = BRANCH_ELEMENTS.get(chart.month_branch, "未知")
    support_score = _support_score(day_element=day_element, chart=chart)
    pressure_score = _pressure_score(day_element=day_element, chart=chart)
    structure = _structure_label(support_score=support_score, pressure_score=pressure_score)
    useful_candidates = _useful_candidates(day_element=day_element, structure=structure)
    ten_god_profile = build_ten_god_profile(chart)
    useful_god_profile = build_useful_god_profile(
        day_element=day_element,
        structure=structure,
        useful_candidates=useful_candidates,
    )
    branch_relation_profile = build_branch_relation_profile(chart)
    facts = [
        {"fact_id": "chart.pillars", "label": "四柱", "value": chart.pillars_text},
        {"fact_id": "chart.day_master", "label": "日主", "value": chart.day_stem},
        {"fact_id": "chart.month_branch", "label": "月令", "value": chart.month_branch},
        {"fact_id": "chart.day_element", "label": "日主五行", "value": day_element},
        {"fact_id": "chart.current_luck", "label": "当前大运", "value": chart.current_luck},
        {"fact_id": "chart.current_year", "label": "当前流年", "value": chart.current_year},
        {"fact_id": "adapter.ten_god_profile", "label": "十神显性", "value": ten_god_profile},
        {"fact_id": "adapter.branch_relations", "label": "地支关系", "value": branch_relation_profile},
    ]
    features = [
        {"feature_id": "feature.structure", "label": "结构强弱", "value": structure, "score": support_score},
        {"feature_id": "feature.pressure", "label": "承压程度", "value": pressure_score},
        {"feature_id": "feature.useful_god", "label": "用神候选", "value": useful_god_profile},
        {"feature_id": "feature.ten_god_counts", "label": "十神计数", "value": ten_god_profile["counts"]},
        {
            "feature_id": "feature.branch_relation_counts",
            "label": "合冲计数",
            "value": {
                "clash": branch_relation_profile["clash_count"],
                "harmony": branch_relation_profile["harmony_count"],
            },
        },
    ]
    signals = _build_signals(
        reading_id=engine_request.reading_id,
        chart=chart,
        day_element=day_element,
        month_element=month_element,
        structure=structure,
        useful_candidates=useful_candidates,
        ten_god_profile=ten_god_profile,
        useful_god_profile=useful_god_profile,
        branch_relation_profile=branch_relation_profile,
        support_score=support_score,
        pressure_score=pressure_score,
    )
    return EngineRunResult(
        result_id=f"bazi-native:{engine_request.reading_id}",
        reading_id=engine_request.reading_id,
        engine=EngineKey.BAZI,
        mode=engine_request.mode,
        engine_version="v40.bazi_native.adapter.v1",
        facts=facts,
        features=features,
        signals=signals,
        warnings=["native_bazi_engine_uses_input_chart_facts_without_calendar_conversion"],
        decision_weight=1.0,
    )


def _build_signals(
    *,
    reading_id: str,
    chart: BaziChartFacts,
    day_element: str,
    month_element: str,
    structure: str,
    useful_candidates: list[str],
    ten_god_profile: dict[str, object],
    useful_god_profile: dict[str, object],
    branch_relation_profile: dict[str, object],
    support_score: float,
    pressure_score: float,
) -> list[RuntimeSignal]:
    evidence = ["chart.day_master", "chart.month_branch", "feature.structure"]
    ten_god_evidence = [*evidence, "adapter.ten_god_profile", "feature.ten_god_counts"]
    branch_evidence = [*evidence, "adapter.branch_relations", "feature.branch_relation_counts"]
    signals = [
        RuntimeSignal(
            signal_id=f"{reading_id}:structure",
            reading_id=reading_id,
            source=SignalSource.BAZI_ENGINE,
            source_ref="native_bazi_skeleton",
            topic=Topic.STRUCTURE,
            claim=f"日主{chart.day_stem}{day_element}，月令{chart.month_branch}{month_element}，结构暂判为{structure}。",
            polarity=Polarity.NEUTRAL,
            strength=support_score,
            confidence=0.62,
            assertion_hint=AssertionLevel.SUPPORTED,
            evidence_refs=evidence,
            trainable_targets=["signal_weight.structure"],
        ),
        RuntimeSignal(
            signal_id=f"{reading_id}:useful-god",
            reading_id=reading_id,
            source=SignalSource.BAZI_ENGINE,
            source_ref="native_bazi_skeleton",
            topic=Topic.USEFUL_GOD,
            claim=f"用神候选先保留为{'、'.join(useful_candidates)}，后续需结合大运流年和现实反馈校准。",
            polarity=Polarity.MIXED,
            strength=0.58,
            confidence=0.58,
            assertion_hint=AssertionLevel.MIXED,
            evidence_refs=[*evidence, "feature.useful_god"],
            trainable_targets=["threshold.useful_god_candidate"],
        ),
        RuntimeSignal(
            signal_id=f"{reading_id}:ten-god",
            reading_id=reading_id,
            source=SignalSource.BAZI_ENGINE,
            source_ref="native_bazi_ten_god_adapter",
            topic=Topic.STRUCTURE,
            claim=_ten_god_claim(ten_god_profile),
            polarity=Polarity.NEUTRAL,
            strength=_count_strength(ten_god_profile),
            confidence=0.63,
            assertion_hint=AssertionLevel.SUPPORTED,
            evidence_refs=ten_god_evidence,
            trainable_targets=["signal_weight.ten_god_visible"],
        ),
        RuntimeSignal(
            signal_id=f"{reading_id}:branch-relations",
            reading_id=reading_id,
            source=SignalSource.BAZI_ENGINE,
            source_ref="native_bazi_branch_relation_adapter",
            topic=Topic.TIMING,
            claim=_branch_relation_claim(branch_relation_profile),
            polarity=_branch_relation_polarity(branch_relation_profile),
            strength=_branch_relation_strength(branch_relation_profile),
            confidence=0.61,
            assertion_hint=AssertionLevel.MIXED,
            evidence_refs=branch_evidence,
            trainable_targets=["signal_weight.branch_relation"],
        ),
        RuntimeSignal(
            signal_id=f"{reading_id}:career",
            reading_id=reading_id,
            source=SignalSource.BAZI_ENGINE,
            source_ref="native_bazi_skeleton",
            topic=Topic.CAREER,
            claim=_career_claim(structure=structure, useful_candidates=useful_candidates, pressure_score=pressure_score),
            polarity=Polarity.SUPPORT,
            strength=max(0.5, pressure_score),
            confidence=0.64,
            assertion_hint=AssertionLevel.SUPPORTED,
            evidence_refs=[*evidence, "feature.pressure"],
            trainable_targets=["advice_priority.career"],
        ),
    ]
    signals.extend(
        _domain_signals(
            reading_id=reading_id,
            chart=chart,
            ten_god_profile=ten_god_profile,
            branch_relation_profile=branch_relation_profile,
            useful_god_profile=useful_god_profile,
            evidence=evidence,
        )
    )
    if chart.current_luck or chart.current_year:
        signals.append(
            RuntimeSignal(
                signal_id=f"{reading_id}:timing",
                reading_id=reading_id,
                source=SignalSource.BAZI_ENGINE,
                source_ref="native_bazi_skeleton",
                topic=Topic.TIMING,
                claim=f"时运入口为大运{chart.current_luck or '未填'}、流年{chart.current_year or '未填'}，先作为触发背景，不直接下年份断语。",
                polarity=Polarity.NEUTRAL,
                strength=0.52,
                confidence=0.54,
                assertion_hint=AssertionLevel.WEAK_CANDIDATE,
                evidence_refs=["chart.current_luck", "chart.current_year"],
            )
        )
    return signals


def _domain_signals(
    *,
    reading_id: str,
    chart: BaziChartFacts,
    ten_god_profile: dict[str, object],
    branch_relation_profile: dict[str, object],
    useful_god_profile: dict[str, object],
    evidence: list[str],
) -> list[RuntimeSignal]:
    counts = ten_god_profile.get("counts", {})
    if not isinstance(counts, dict):
        counts = {}
    wealth_count = int(ten_god_profile.get("wealth_count") or 0)
    officer_count = int(ten_god_profile.get("officer_count") or 0)
    output_count = int(ten_god_profile.get("output_count") or 0)
    relation_count = int(branch_relation_profile.get("clash_count") or 0) + int(
        branch_relation_profile.get("harmony_count") or 0
    )
    candidates = useful_god_profile.get("candidates", [])
    candidate_text = "、".join(str(row) for row in candidates) if isinstance(candidates, list) else "待校准"
    signals = [
        RuntimeSignal(
            signal_id=f"{reading_id}:wealth",
            reading_id=reading_id,
            source=SignalSource.BAZI_ENGINE,
            source_ref="native_bazi_ten_god_domain_adapter",
            topic=Topic.WEALTH,
            claim=_wealth_claim(wealth_count=wealth_count, output_count=output_count, candidate_text=candidate_text),
            polarity=Polarity.SUPPORT if wealth_count or output_count else Polarity.NEUTRAL,
            strength=round(min(0.78, 0.44 + wealth_count * 0.12 + output_count * 0.06), 2),
            confidence=0.58 if wealth_count else 0.5,
            assertion_hint=AssertionLevel.WEAK_CANDIDATE if not wealth_count else AssertionLevel.SUPPORTED,
            evidence_refs=[*evidence, "adapter.ten_god_profile", "feature.useful_god"],
            trainable_targets=["advice_priority.wealth", "signal_weight.ten_god_wealth"],
        ),
        RuntimeSignal(
            signal_id=f"{reading_id}:relationship",
            reading_id=reading_id,
            source=SignalSource.BAZI_ENGINE,
            source_ref="native_bazi_relationship_adapter",
            topic=Topic.RELATIONSHIP,
            claim=_relationship_claim(chart=chart, wealth_count=wealth_count, officer_count=officer_count),
            polarity=Polarity.MIXED if relation_count else Polarity.NEUTRAL,
            strength=round(min(0.78, 0.42 + officer_count * 0.1 + wealth_count * 0.08 + relation_count * 0.06), 2),
            confidence=0.56,
            assertion_hint=AssertionLevel.MIXED,
            evidence_refs=[*evidence, "adapter.ten_god_profile", "adapter.branch_relations"],
            trainable_targets=["advice_priority.relationship", "signal_weight.relationship_indicator"],
        ),
        RuntimeSignal(
            signal_id=f"{reading_id}:health",
            reading_id=reading_id,
            source=SignalSource.BAZI_ENGINE,
            source_ref="native_bazi_health_adapter",
            topic=Topic.HEALTH,
            claim=_health_claim(branch_relation_profile=branch_relation_profile),
            polarity=Polarity.MIXED if relation_count else Polarity.NEUTRAL,
            strength=round(min(0.76, 0.4 + relation_count * 0.08), 2),
            confidence=0.52 if relation_count else 0.48,
            assertion_hint=AssertionLevel.WEAK_CANDIDATE,
            evidence_refs=[*evidence, "adapter.branch_relations"],
            trainable_targets=["probe_policy.health", "signal_weight.branch_health"],
        ),
    ]
    if counts:
        signals.append(
            RuntimeSignal(
                signal_id=f"{reading_id}:advice",
                reading_id=reading_id,
                source=SignalSource.BAZI_ENGINE,
                source_ref="native_bazi_useful_god_adapter",
                topic=Topic.ADVICE,
                claim=f"建议先围绕{candidate_text}对应的资源、输出、责任和边界来验证，不把单一十神当成最终答案。",
                polarity=Polarity.NEUTRAL,
                strength=0.54,
                confidence=0.55,
                assertion_hint=AssertionLevel.WEAK_CANDIDATE,
                evidence_refs=[*evidence, "feature.useful_god", "adapter.ten_god_profile"],
                trainable_targets=["advice_priority.overview"],
            )
        )
    return signals


def _ten_god_claim(profile: dict[str, object]) -> str:
    dominant = profile.get("dominant_ten_gods") or []
    counts = profile.get("counts") or {}
    if isinstance(dominant, list) and dominant:
        return f"显性十神以{'、'.join(str(row) for row in dominant)}较突出，需结合地支和用神候选判断落点。"
    if counts:
        return "显性十神已有分布，但尚未形成明显集中点，先作为领域判断素材。"
    return "显性天干十神不足，领域判断需要更多依赖地支、用神和现实反馈。"


def _branch_relation_claim(profile: dict[str, object]) -> str:
    relations = profile.get("relations") or []
    timing_relations = profile.get("timing_relations") or []
    labels = _relation_labels([*relations, *timing_relations])
    if labels:
        return f"地支关系出现{'、'.join(labels[:3])}，适合作为结构互动、时运触发和现实事件校准素材。"
    return "地支未见明显合冲入口，先按结构和十神素材推进，不强行制造动态关系。"


def _branch_relation_polarity(profile: dict[str, object]) -> Polarity:
    if int(profile.get("clash_count") or 0) > 0:
        return Polarity.MIXED
    if int(profile.get("harmony_count") or 0) > 0:
        return Polarity.SUPPORT
    return Polarity.NEUTRAL


def _branch_relation_strength(profile: dict[str, object]) -> float:
    count = int(profile.get("clash_count") or 0) + int(profile.get("harmony_count") or 0)
    return round(min(0.78, 0.42 + count * 0.08), 2)


def _count_strength(profile: dict[str, object]) -> float:
    rows = profile.get("rows") or []
    if isinstance(rows, list):
        return round(min(0.74, 0.44 + len(rows) * 0.08), 2)
    return 0.44


def _wealth_claim(*, wealth_count: int, output_count: int, candidate_text: str) -> str:
    if wealth_count:
        return f"财星已有显性入口，财运判断应看{candidate_text}能否承接资源、输出和分配边界。"
    if output_count:
        return f"财星不直接显，但输出星有入口，财运宜先看能力输出如何转成资源和回报。"
    return f"财运暂不宜强断，先看{candidate_text}是否能形成稳定资源或风险边界。"


def _relationship_claim(*, chart: BaziChartFacts, wealth_count: int, officer_count: int) -> str:
    is_female = "坤" in chart.gender or "女" in chart.gender
    indicator = officer_count if is_female else wealth_count
    label = "官杀" if is_female else "财星"
    if indicator:
        return f"关系判断先看{label}显性入口，再结合地支互动确认相处节奏和边界。"
    return f"关系判断暂不从{label}强断，先看地支互动、现实反馈和长期节奏。"


def _health_claim(*, branch_relation_profile: dict[str, object]) -> str:
    labels = _relation_labels(
        [
            *(branch_relation_profile.get("relations") or []),
            *(branch_relation_profile.get("timing_relations") or []),
        ]
    )
    if labels:
        return f"健康节奏先看{'、'.join(labels[:2])}对应的压力、作息和身体反馈，不直接下病症断语。"
    return "健康节奏暂无明显合冲触发点，先按压力、作息和现实反馈保守校准。"


def _relation_labels(rows: list[object]) -> list[str]:
    labels: list[str] = []
    for row in rows:
        if isinstance(row, dict):
            label = str(row.get("label") or "")
            if label and label not in labels:
                labels.append(label)
    return labels


def _support_score(*, day_element: str, chart: BaziChartFacts) -> float:
    if day_element == "未知":
        return 0.5
    elements = [
        BRANCH_ELEMENTS.get(chart.year_branch, ""),
        BRANCH_ELEMENTS.get(chart.month_branch, ""),
        BRANCH_ELEMENTS.get(chart.day_branch, ""),
        BRANCH_ELEMENTS.get(chart.hour_branch, ""),
        STEM_ELEMENTS.get(chart.year_stem, ""),
        STEM_ELEMENTS.get(chart.month_stem, ""),
        STEM_ELEMENTS.get(chart.hour_stem, ""),
    ]
    supporters = set(SUPPORTING_ELEMENTS.get(day_element, []))
    hits = sum(1 for element in elements if element in supporters)
    return round(max(0.2, min(0.85, hits / max(1, len([item for item in elements if item])))), 2)


def _pressure_score(*, day_element: str, chart: BaziChartFacts) -> float:
    if day_element == "未知":
        return 0.5
    elements = [
        BRANCH_ELEMENTS.get(chart.month_branch, ""),
        BRANCH_ELEMENTS.get(chart.day_branch, ""),
        STEM_ELEMENTS.get(chart.month_stem, ""),
        STEM_ELEMENTS.get(chart.hour_stem, ""),
    ]
    pressure_elements = set(DRAINING_ELEMENTS.get(day_element, []))
    hits = sum(1 for element in elements if element in pressure_elements)
    return round(max(0.25, min(0.85, hits / max(1, len([item for item in elements if item])))), 2)


def _structure_label(*, support_score: float, pressure_score: float) -> str:
    delta = support_score - pressure_score
    if delta >= 0.2:
        return "偏旺待复核"
    if delta <= -0.2:
        return "偏弱待复核"
    return "中和待复核"


def _useful_candidates(*, day_element: str, structure: str) -> list[str]:
    if day_element == "未知":
        return ["待校准"]
    if structure.startswith("偏旺"):
        return DRAINING_ELEMENTS.get(day_element, ["待校准"])
    if structure.startswith("偏弱"):
        return SUPPORTING_ELEMENTS.get(day_element, ["待校准"])
    return [*SUPPORTING_ELEMENTS.get(day_element, []), *DRAINING_ELEMENTS.get(day_element, [])][:3]


def _career_claim(*, structure: str, useful_candidates: list[str], pressure_score: float) -> str:
    useful = "、".join(useful_candidates)
    if pressure_score >= 0.6:
        return f"事业线索以压力转承接为主，适合先看{useful}能否形成资质、规则、平台或稳定交付。"
    return f"事业线索更适合从{useful}的资源与输出方式切入，先稳住主线再判断突破窗口。"
