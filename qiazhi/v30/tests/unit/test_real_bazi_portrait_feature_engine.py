from __future__ import annotations

from v30.diagnosis import (
    FEATURE_ENGINE_VERSION,
    PORTRAIT_ENGINE_VERSION,
    extract_diagnosis_features,
    extract_diagnosis_portraits,
    match_real_bazi_rules,
    summarize_diagnosis_features,
    summarize_diagnosis_portraits,
    translate_dynamic_paths,
)
from v30.runtime import create_smoke_runtime


def _runtime_parts():
    runtime = create_smoke_runtime(
        "rbd-portrait-feature-runtime",
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    paths = translate_dynamic_paths(
        runtime.structure_state,
        timing_context=runtime.chart_context.time_layers,
    )
    matches = match_real_bazi_rules(
        feature_evidence=runtime.feature_evidence,
        structure_state=runtime.structure_state,
        model_signal_summary=runtime.question_plan.policy_effect["model_signal_summary"],
        krp_units=runtime.question_plan.policy_effect["krp_library_units"],
    )
    return runtime, matches, paths


def test_feature_engine_projects_bazi_specific_features() -> None:
    runtime, matches, paths = _runtime_parts()
    features = extract_diagnosis_features(
        feature_evidence=runtime.feature_evidence,
        matched_rules=matches,
        diagnosis_paths=paths,
    )
    summary = summarize_diagnosis_features(features)
    statements = "\n".join(feature.statement for feature in features)

    assert len(features) >= 25
    assert summary["version"] == FEATURE_ENGINE_VERSION
    assert summary["feature_count"] == len(features)
    assert summary["domain_counts"]["structure"] >= 8
    assert "显性十神为" in statements
    assert "藏干十神为" in statements
    assert "五行分布显示" in statements
    assert "领域规则已触发" in statements
    assert all(feature.evidence_ids for feature in features)


def test_feature_engine_preserves_boundaries_and_limit_order() -> None:
    runtime, matches, paths = _runtime_parts()
    features = extract_diagnosis_features(
        feature_evidence=runtime.feature_evidence,
        matched_rules=matches,
        diagnosis_paths=paths,
        limit=8,
    )

    assert len(features) == 8
    assert features[0].domain == "overview"
    assert any("blocks:chart_fact_mutation" in note for feature in features for note in feature.counter_notes)
    assert all("新增排盘事实" not in feature.statement or feature.boundary for feature in features)


def test_portrait_engine_builds_rule_and_path_portraits() -> None:
    runtime, matches, paths = _runtime_parts()
    portraits = extract_diagnosis_portraits(
        matched_rules=matches,
        diagnosis_paths=paths,
        krp_units=runtime.question_plan.policy_effect["krp_library_units"],
    )
    summary = summarize_diagnosis_portraits(portraits)
    statements = "\n".join(portrait.statement for portrait in portraits)

    assert len(portraits) >= 20
    assert summary["version"] == PORTRAIT_ENGINE_VERSION
    assert summary["portrait_count"] == len(portraits)
    assert summary["domain_counts"]["career"] >= 3
    assert summary["domain_counts"]["wealth"] >= 2
    assert "财官印" in statements or "官印相生" in statements
    assert "财富画像" in statements
    assert "事业画像" in statements
    assert all(portrait.evidence_ids or portrait.path_ids for portrait in portraits)


def test_portrait_engine_blocks_health_and_hidden_overclaims() -> None:
    runtime, matches, paths = _runtime_parts()
    portraits = extract_diagnosis_portraits(
        matched_rules=matches,
        diagnosis_paths=paths,
        krp_units=runtime.question_plan.policy_effect["krp_library_units"],
    )
    health = [portrait for portrait in portraits if portrait.domain == "health"]
    hidden = [portrait for portrait in portraits if portrait.domain == "hidden_factor"]

    assert health
    assert hidden
    assert any("不做疾病预测" in portrait.statement or "medical_diagnosis" in portrait.counter_notes for portrait in health)
    assert any("不能变成确定事实" in portrait.statement for portrait in hidden)
