from __future__ import annotations

from v40.contracts.base import AssertionLevel, EngineKey, EngineMode, Polarity, RoleKey, Topic
from v40.contracts.chart import BaziChartFacts
from v40.contracts.engine import EnginePlan, EnginePlanItem, EngineRunRequest, EngineRunResult, MultiEngineRunResult
from v40.contracts.runtime import RuntimeRequest, RuntimeResult
from v40.contracts.signal import RuntimeSignal, SignalRegistrySnapshot, SignalSource
from v40.decision import build_decision_output
from v40.presentation import build_product_projection, build_surface_bundle


STEM_ELEMENTS = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}

BRANCH_ELEMENTS = {
    "寅": "木",
    "卯": "木",
    "巳": "火",
    "午": "火",
    "辰": "土",
    "戌": "土",
    "丑": "土",
    "未": "土",
    "申": "金",
    "酉": "金",
    "亥": "水",
    "子": "水",
}

SUPPORTING_ELEMENTS = {
    "木": ["水", "木"],
    "火": ["木", "火"],
    "土": ["火", "土"],
    "金": ["土", "金"],
    "水": ["金", "水"],
}

DRAINING_ELEMENTS = {
    "木": ["火", "金"],
    "火": ["土", "水"],
    "土": ["金", "木"],
    "金": ["水", "火"],
    "水": ["木", "土"],
}


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
    facts = [
        {"fact_id": "chart.pillars", "label": "四柱", "value": chart.pillars_text},
        {"fact_id": "chart.day_master", "label": "日主", "value": chart.day_stem},
        {"fact_id": "chart.month_branch", "label": "月令", "value": chart.month_branch},
        {"fact_id": "chart.day_element", "label": "日主五行", "value": day_element},
        {"fact_id": "chart.current_luck", "label": "当前大运", "value": chart.current_luck},
        {"fact_id": "chart.current_year", "label": "当前流年", "value": chart.current_year},
    ]
    features = [
        {"feature_id": "feature.structure", "label": "结构强弱", "value": structure, "score": support_score},
        {"feature_id": "feature.pressure", "label": "承压程度", "value": pressure_score},
        {"feature_id": "feature.useful_candidates", "label": "用神候选", "value": useful_candidates},
    ]
    signals = _build_signals(
        reading_id=engine_request.reading_id,
        chart=chart,
        day_element=day_element,
        month_element=month_element,
        structure=structure,
        useful_candidates=useful_candidates,
        support_score=support_score,
        pressure_score=pressure_score,
    )
    return EngineRunResult(
        result_id=f"bazi-native:{engine_request.reading_id}",
        reading_id=engine_request.reading_id,
        engine=EngineKey.BAZI,
        mode=engine_request.mode,
        engine_version="v40.bazi_native.skeleton.v1",
        facts=facts,
        features=features,
        signals=signals,
        warnings=["native_bazi_engine_is_skeleton_without_calendar_conversion"],
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
    support_score: float,
    pressure_score: float,
) -> list[RuntimeSignal]:
    evidence = ["chart.day_master", "chart.month_branch", "feature.structure"]
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
            evidence_refs=[*evidence, "feature.useful_candidates"],
            trainable_targets=["threshold.useful_god_candidate"],
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
