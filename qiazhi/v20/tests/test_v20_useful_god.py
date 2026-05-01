from __future__ import annotations

from v20.api.runtime import run_runtime_from_pillars
from v20.core.chart import build_chart_facts, chart_input_from_displays
from v20.core.strength import infer_core
from v20.core.useful_god import derive_useful_god_candidates
from v20.features.compiler import compile_features


def test_v20_useful_god_candidates_are_candidate_only() -> None:
    facts = build_chart_facts(chart_input_from_displays("甲子", "戊辰", "甲午", "辛酉"))
    inference = infer_core(facts)
    candidates = derive_useful_god_candidates(facts, inference)

    assert candidates
    assert all(row.status == "candidate_only" for row in candidates)
    assert all("NO_FIXED_FAVORABLE_UNFAVORABLE_VERDICT" in row.guardrails for row in candidates)
    assert {row.path_type for row in candidates}
    assert all(row.evidence_refs for row in candidates)


def test_v20_feature_layer_includes_useful_god_candidate_paths() -> None:
    facts = build_chart_facts(chart_input_from_displays("甲子", "戊辰", "甲午", "辛酉"))
    layer = compile_features(facts, infer_core(facts))
    feature = next(row for row in layer.features if row.feature_id == "feature.useful_god.candidate_paths")

    assert feature.domain == "useful_god"
    assert feature.readiness == "review_ready"
    assert "q_useful_god_candidates" in feature.question_hooks
    assert "q_useful_god_evidence_gaps" in feature.question_hooks
    assert "candidate_only" in feature.calibration_state


def test_v20_runtime_routes_useful_god_candidates_without_verdict() -> None:
    result = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="useful-god.runtime",
        user_text="我想看用神候选",
    )

    useful_features = [
        row for row in result["feature_layer"]["features"] if row["domain"] == "useful_god"
    ]
    assert {row["feature_id"] for row in useful_features} >= {
        "feature.useful_god.evidence_gate",
        "feature.useful_god.candidate_paths",
    }
    assert result["selected_question"]["question_key"] == "q_useful_god_candidates"
    assert "useful_god" in {row["domain"] for row in result["knowledge_refs"]}
    assert "用神候选先看扶身路径" in result["answer_text"]
    assert "水方向可作为扶身候选" in result["answer_text"]
    assert "当前命局可见" in result["answer_text"]
    assert "固定吉凶" in result["answer_text"]
    assert "candidate_only" not in result["answer_text"]
    assert "feature." not in result["answer_text"]
    assert "core." not in result["answer_text"]
    assert "喜用神已定" not in result["answer_text"]
    assert "忌神已定" not in result["answer_text"]
