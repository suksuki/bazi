from __future__ import annotations

import pytest

from v30.engines import EngineKey, EngineRunResult, infer_engine_plan, run_engine_plan
from v30.engines.contracts import EngineMode
from v30.production.contracts import BaziDomain, BaziTopic, SignalSourceType
from v30.runtime import create_smoke_runtime


def test_engine_plan_routes_wealth_question_without_granting_ziwei_decision_weight() -> None:
    plan = infer_engine_plan(
        reading_id="pytest-engine-plan",
        user_question="我今年财运如何？",
        role="user",
    )

    assert plan.topic == BaziTopic.WEALTH
    assert plan.domain == BaziDomain.WEALTH
    assert plan.time_scope == "current_year"
    assert plan.decision_policy == {"bazi": 1.0, "ziwei": 0.0, "reality_probe": 0.4, "llm": 0.0}
    assert [item.engine for item in plan.items] == [EngineKey.BAZI, EngineKey.ZIWEI, EngineKey.REALITY_PROBE]
    assert next(item for item in plan.items if item.engine == EngineKey.BAZI).decision_weight == 1.0
    assert next(item for item in plan.items if item.engine == EngineKey.ZIWEI).decision_weight == 0.0
    assert plan.central_brain_verdict_authority is False


def test_multi_engine_manager_wraps_runtime_and_keeps_verdicts_unchanged() -> None:
    runtime = create_smoke_runtime("pytest-multi-engine-runtime")
    central = runtime.question_plan.policy_effect["central_reading_state"]
    before_verdicts = [
        (row["domain"], row["assertion_level"], row["headline"])
        for row in central["decision_result"]["verdicts"]
    ]
    plan = infer_engine_plan(
        reading_id=runtime.reading_id,
        user_question="事业适合稳定发展还是转型突破？",
        role="user",
    )
    result = run_engine_plan(
        plan,
        runtime=runtime,
        engine_contexts={"ziwei": {"ziwei_matched_rule_ids": ["ZW-CAREER-02"], "ziwei_chart_id": "pytest-ziwei-chart"}},
    )
    after_central = runtime.question_plan.policy_effect["central_reading_state"]
    after_verdicts = [
        (row["domain"], row["assertion_level"], row["headline"])
        for row in after_central["decision_result"]["verdicts"]
    ]

    assert before_verdicts == after_verdicts
    assert result.decision_engine_mutated is False
    assert result.verdict_mutated is False
    assert result.final_synthesis_mutated is False
    assert result.signal_registry.signals
    assert result.signal_registry.by_source_type(SignalSourceType.ZIWEI_SIGNAL)
    bazi_audit = next(row for row in result.audit if row.engine == EngineKey.BAZI)
    ziwei_audit = next(row for row in result.audit if row.engine == EngineKey.ZIWEI)
    assert bazi_audit.signal_count > 0
    assert ziwei_audit.signal_count == 1
    assert ziwei_audit.registered_signal_count == 1


def test_ziwei_engine_does_not_emit_fake_signal_without_matched_fact() -> None:
    runtime = create_smoke_runtime("pytest-ziwei-no-fake-signal")
    plan = infer_engine_plan(
        reading_id=runtime.reading_id,
        user_question="今年财运如何？",
        role="practitioner",
    )
    result = run_engine_plan(plan, runtime=runtime)
    ziwei_result = next(row for row in result.results if row.engine == EngineKey.ZIWEI)

    assert ziwei_result.signals == []
    assert ziwei_result.probe_candidates
    assert "ziwei_fact_layer_not_connected_no_matched_rule_signal_emitted" in ziwei_result.warnings
    assert not result.signal_registry.by_source_type(SignalSourceType.ZIWEI_SIGNAL)


def test_reality_probe_engine_wraps_existing_probe_candidates() -> None:
    runtime = create_smoke_runtime("pytest-reality-probe-engine")
    plan = infer_engine_plan(
        reading_id=runtime.reading_id,
        user_question="关系里最需要注意什么？",
        role="user",
    )
    result = run_engine_plan(plan, runtime=runtime)
    reality_probe = next(row for row in result.results if row.engine == EngineKey.REALITY_PROBE)

    assert reality_probe.mode == EngineMode.PROBE_TRIGGER
    assert reality_probe.probe_candidates
    assert reality_probe.diagnostics["reality_probe_affects_manifestation_not_chart_facts"] is True


def test_engine_run_result_rejects_verdict_authority() -> None:
    with pytest.raises(ValueError, match="verdict authority"):
        EngineRunResult(
            result_id="bad",
            reading_id="bad",
            engine=EngineKey.BAZI,
            mode=EngineMode.DECISION_AUX,
            engine_version="bad",
            verdict_authority=True,
        )
