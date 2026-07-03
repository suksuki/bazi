from __future__ import annotations

import pytest

from v30.engines import infer_engine_plan, run_engine_plan
from v30.engines.contracts import EngineKey
from v30.runtime import create_smoke_runtime
from v30.training.mingli_training import (
    EngineTrainingExample,
    build_engine_training_example,
    build_mingli_training_quality_gate,
    load_phase1_mingli_golden_cases,
)
from v30.validation.mingli_training_quality_gate import run_mingli_training_quality_gate


def test_phase1_golden_cases_cover_core_mingli_domains() -> None:
    cases = load_phase1_mingli_golden_cases()

    assert len(cases) == 3
    assert {case.case_id for case in cases} == {
        "mtl-phase1-career-pressure",
        "mtl-phase1-wealth-current-year",
        "mtl-phase1-relationship-boundary",
    }
    assert all(case.expected_verdict_domains for case in cases)
    assert all(case.forbidden_assertions for case in cases)
    assert any(EngineKey.ZIWEI in case.required_engines for case in cases)
    assert all(case.chart_fact_mutation_allowed is False for case in cases)


def test_phase1_builds_engine_training_example_from_multi_engine_result() -> None:
    case = next(row for row in load_phase1_mingli_golden_cases() if row.case_id == "mtl-phase1-wealth-current-year")
    runtime = create_smoke_runtime("pytest-mingli-training-example")
    plan = infer_engine_plan(reading_id=runtime.reading_id, user_question=case.user_question, role="practitioner")
    multi_engine = run_engine_plan(
        plan,
        runtime=runtime,
        engine_contexts={"ziwei": {"ziwei_matched_rule_ids": case.ziwei_matched_rule_ids, "ziwei_chart_id": "pytest-ziwei"}},
    )
    example = build_engine_training_example(
        golden_case=case,
        multi_engine_result=multi_engine,
        runtime_payload=runtime.model_dump(mode="json"),
        example_id="pytest-engine-training-example",
    )

    assert example.version == "v30.engine_training_example.v1"
    assert example.example_id == "pytest-engine-training-example"
    assert example.quality_score.passed is True
    assert example.quality_score.verdict_domain_alignment == 1.0
    assert example.quality_score.evidence_binding == 1.0
    assert example.signal_registry_summary["signal_count"] > 0
    assert example.signal_registry_summary["source_type_counts"]["ziwei_signal"] == 2
    assert "engine_signal_weight" in example.trainable_targets
    assert "chart_facts" not in example.trainable_targets
    assert "chart_facts" in example.blocked_targets
    assert example.chart_fact_mutation_allowed is False
    assert example.production_policy_write_allowed is False


def test_phase1_gate_passes_default_golden_pack() -> None:
    payload = run_mingli_training_quality_gate()

    assert payload["version"] == "v30.mingli_training_quality_gate_runner.v1"
    assert payload["status"] == "passed"
    assert payload["decision"]["mingli_training_phase1_ready"] is True
    assert payload["decision"]["case_count"] == 3
    assert payload["decision"]["passed_case_count"] == 3
    assert payload["decision"]["average_quality_score"] >= 0.68
    assert payload["decision"]["chart_fact_mutation_allowed"] is False
    assert payload["decision"]["production_policy_write_allowed"] is False
    assert payload["decision"]["production_pointer_write_allowed"] is False
    assert all(example["quality"]["passed"] for example in payload["examples"])


def test_phase1_gate_blocks_low_quality_or_too_few_examples() -> None:
    case = load_phase1_mingli_golden_cases()[0]
    runtime = create_smoke_runtime("pytest-mingli-training-blocked")
    plan = infer_engine_plan(reading_id=runtime.reading_id, user_question=case.user_question, role="user")
    multi_engine = run_engine_plan(plan, runtime=runtime)
    example = build_engine_training_example(
        golden_case=case.model_copy(update={"min_quality_score": 0.99}),
        multi_engine_result=multi_engine,
        runtime_payload=runtime.model_dump(mode="json"),
    )
    gate = build_mingli_training_quality_gate([example], min_case_count=3, min_average_quality=0.99)

    assert gate.status == "blocked"
    assert gate.case_count == 1
    assert gate.failed_case_ids == [case.case_id]
    assert gate.chart_fact_mutation_allowed is False
    assert gate.production_policy_write_allowed is False


def test_phase1_training_example_rejects_chart_fact_training_target() -> None:
    case = load_phase1_mingli_golden_cases()[0]
    runtime = create_smoke_runtime("pytest-mingli-training-safe")
    plan = infer_engine_plan(reading_id=runtime.reading_id, user_question=case.user_question, role="user")
    multi_engine = run_engine_plan(plan, runtime=runtime)
    example = build_engine_training_example(
        golden_case=case,
        multi_engine_result=multi_engine,
        runtime_payload=runtime.model_dump(mode="json"),
    )

    with pytest.raises(ValueError, match="cannot train chart_facts"):
        EngineTrainingExample(
            **example.model_copy(update={"trainable_targets": [*example.trainable_targets, "chart_facts"]}).model_dump(mode="json")
        )
