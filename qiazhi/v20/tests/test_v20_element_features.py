from __future__ import annotations

from v20.api.runtime import run_runtime_from_pillars
from v20.core.chart import build_chart_facts, chart_input_from_displays
from v20.core.elements import element_distribution, strongest_elements, weakest_elements
from v20.core.strength import infer_core
from v20.features.compiler import compile_features


def test_v20_element_distribution_uses_visible_and_hidden_stems() -> None:
    facts = build_chart_facts(chart_input_from_displays("甲子", "戊辰", "甲午", "辛酉"))
    distribution = element_distribution(facts)

    assert set(distribution) == {"wood", "fire", "earth", "metal", "water"}
    assert distribution["wood"] >= 2.0
    assert distribution["water"] > 0
    assert strongest_elements(distribution)
    assert weakest_elements(distribution)


def test_v20_feature_layer_includes_element_balance_feature() -> None:
    facts = build_chart_facts(chart_input_from_displays("甲子", "戊辰", "甲午", "辛酉"))
    layer = compile_features(facts, infer_core(facts))
    feature = next(row for row in layer.features if row.feature_id == "feature.element.balance_distribution")
    emphasis_features = [row for row in layer.features if row.feature_id.startswith("feature.element.prominent.")]

    assert feature.domain == "element"
    assert feature.evidence_refs
    assert "q_element_balance" in feature.question_hooks
    assert feature.boundary
    assert emphasis_features
    assert any(row.evidence_refs[0].kind == "element_emphasis" for row in emphasis_features)


def test_v20_runtime_routes_element_questions_and_knowledge() -> None:
    result = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="element.runtime",
        user_text="我想看五行分布",
    )

    assert "element" in {row["domain"] for row in result["feature_layer"]["features"]}
    assert "element" in {row["domain"] for row in result["knowledge_refs"]}
    assert result["selected_question"]["domain"] == "element"
    assert result["selected_question"]["question_key"] == "q_element_balance"
    assert "结构摘要" in result["answer_text"]
    assert "strongest=" not in result["answer_text"]
    assert "五行分布" in result["answer_text"]
