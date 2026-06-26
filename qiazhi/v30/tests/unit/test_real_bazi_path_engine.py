from __future__ import annotations

from v30.diagnosis import PATH_ENGINE_VERSION, summarize_diagnosis_paths, translate_dynamic_paths
from v30.runtime import create_smoke_runtime


def test_path_engine_translates_runtime_dynamic_paths() -> None:
    runtime = create_smoke_runtime(
        "rbd-path-engine-runtime",
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    paths = translate_dynamic_paths(
        runtime.structure_state,
        timing_context=runtime.chart_context.time_layers,
    )
    summary = summarize_diagnosis_paths(paths)

    assert len(paths) >= 10
    assert summary["version"] == PATH_ENGINE_VERSION
    assert summary["path_count"] == len(paths)
    assert summary["high_confidence_path_count"] > 0
    assert any(path.mechanism in {"官印相生", "财官印制化", "食伤生财", "印星通关"} for path in paths)
    assert any("career" in path.domain_targets for path in paths)
    assert any("wealth" in path.domain_targets for path in paths)
    assert all(path.diagnosis_statement for path in paths)
    assert all(path.evidence_ids for path in paths)
    assert all("fixed_event_prediction" in path.blocked_overclaim for path in paths)


def test_path_engine_generates_bazi_path_statement_for_wealth_authority_resource() -> None:
    runtime = create_smoke_runtime(
        "rbd-path-engine-wealth-authority-resource",
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    paths = translate_dynamic_paths(runtime.structure_state, timing_context=runtime.chart_context.time_layers)
    target = next(path for path in paths if path.mechanism == "财官印制化")

    assert "财官印路径" in target.diagnosis_statement
    assert "财星不是单独成财" in target.diagnosis_statement
    assert "印星承接" in target.diagnosis_statement
    assert "wealth" in target.domain_targets
    assert "career" in target.domain_targets
    assert target.timing_trigger["luck_pillar"] == "戊寅"
    assert target.timing_trigger["flow_year_pillar"] == "庚子"


def test_path_engine_preserves_conflict_and_health_boundaries() -> None:
    runtime = create_smoke_runtime("rbd-path-engine-conflict")
    paths = translate_dynamic_paths(runtime.structure_state, timing_context=runtime.chart_context.time_layers)
    conflict_paths = [path for path in paths if path.counter_evidence_ids]

    assert conflict_paths
    assert any("health" in path.domain_targets for path in conflict_paths)
    assert all("medical_diagnosis" in path.blocked_overclaim for path in conflict_paths if "health" in path.domain_targets)
    assert all("事件预测" in path.risk_statement or "定论" in path.risk_statement or "结果" in path.risk_statement for path in conflict_paths)


def test_path_engine_can_limit_sorted_paths() -> None:
    runtime = create_smoke_runtime("rbd-path-engine-limit")
    paths = translate_dynamic_paths(runtime.structure_state, timing_context=runtime.chart_context.time_layers, limit=3)

    assert len(paths) == 3
    assert paths == sorted(paths, key=lambda row: row.score, reverse=True)
