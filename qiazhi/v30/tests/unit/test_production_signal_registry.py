from __future__ import annotations

from v30.presentation.thinking import build_thinking_projection
from v30.production import SignalSourceType, build_production_sidecar
from v30.runtime import create_smoke_runtime


def test_runtime_attaches_production_sidecar_without_changing_verdicts() -> None:
    runtime = create_smoke_runtime("pytest-production-sidecar")
    policy = runtime.question_plan.policy_effect
    central = policy["central_reading_state"]
    verdicts = central["decision_verdicts"]
    registry = policy["production_signal_registry"]
    usage = policy["production_usage_audit"]
    module_audit = policy["production_module_audit"]
    summary = policy["production_audit_summary"]

    assert verdicts
    assert len(verdicts) == len(central["decision_result"]["verdicts"])
    assert registry["version"] == "v30.signal_registry.v1"
    assert registry["signals"]
    assert usage
    assert module_audit
    assert summary["signal_count"] == len(registry["signals"])
    assert summary["module_count"] == len(module_audit)
    assert summary["decision_consumed_signal_count"] > 0
    assert summary["verdict_consumed_signal_count"] > 0
    assert summary["status_counts"]
    assert central["decision_result"]["llm_expression_contract"]["llm_can_override_verdict"] is False
    assert policy["production_sidecar"]["decision_engine_mutated"] is False
    assert policy["production_sidecar"]["verdict_mutated"] is False
    assert policy["production_sidecar"]["final_synthesis_mutated"] is False
    assert policy["production_sidecar"]["llm_decision_authority"] is False


def test_bazi_signal_keeps_usage_state_out_of_raw_signal() -> None:
    runtime = create_smoke_runtime("pytest-production-signal-clean")
    policy = runtime.question_plan.policy_effect
    signal = policy["production_signal_registry"]["signals"][0]
    usage = policy["production_usage_audit"][0]

    assert "consumed_by_decision" not in signal
    assert "runtime_used" not in signal
    assert "user_output_bound" not in signal
    assert "consumed_by_decision" in usage
    assert "output_bound" in usage
    assert signal["source_type"] in {item.value for item in SignalSourceType}
    assert signal["claim"]
    assert signal["role_visibility"]


def test_stage_points_are_registered_as_presentation_only_signals() -> None:
    runtime = create_smoke_runtime("pytest-production-stage-points")
    policy = runtime.question_plan.policy_effect
    central = policy["central_reading_state"]
    thinking = build_thinking_projection(runtime)
    sidecar = build_production_sidecar(
        reading_id=runtime.reading_id,
        feature_evidence=runtime.feature_evidence,
        macro_signals=policy.get("macro_dimension_signals", []),
        ranked_decisions=policy.get("ranked_decisions", {}),
        practical_context=policy.get("practical_reading_context", {}),
        diagnosis=policy.get("real_bazi_diagnosis", {}),
        central_state=central,
        decision_result=central.get("decision_result", {}),
        final_synthesis=central.get("final_synthesis", {}),
        reading_surface={},
        thinking_projection=thinking,
    )
    payload = sidecar.model_dump(mode="json")
    stage_signals = [
        row for row in payload["registry"]["signals"]
        if row["source_type"] == SignalSourceType.STAGE_POINT.value
    ]
    stage_usage = {
        row["signal_id"]: row
        for row in payload["usage_audit"]
        if row["signal_id"] in {signal["signal_id"] for signal in stage_signals}
    }

    assert stage_signals
    assert all(signal["boundary"] == "stage_point_signal_is_presentation_projection_only_not_decision_input" for signal in stage_signals)
    assert all("presentation_only_do_not_feed_decision_v1" in row["notes"] for row in stage_usage.values())
    assert any(row["consumed_by_ui"] for row in stage_usage.values())
