from __future__ import annotations

import pytest

from v40.contracts import (
    AdvicePlan,
    AssertionLevel,
    DecisionInputBundle,
    DecisionVerdict,
    EngineKey,
    EngineMode,
    EnginePlan,
    EnginePlanItem,
    EngineRunResult,
    EvaluationCaseSpec,
    LLMExpressionTask,
    MetricSummary,
    ProbeCandidate,
    ReleaseGateResult,
    ReleaseRecommendation,
    RuntimeSignal,
    Topic,
    TrainingExampleV2,
    TrainingImpactDiff,
    TrainingLabelEvent,
)
from v40.contracts.evaluation import ExpectedVerdict, ForbiddenAssertion
from v40.contracts.signal import SignalSource
from v40.contracts.training import LabelSource, LabelTargetType, LabelValue
from v40.evaluation import build_release_gate_from_metrics
from v40.migration.v30_export import V30ExportEnvelope, V30ToV40MigrationPlan
from v40.training import build_training_example_from_labels


def test_engine_plan_requires_bazi_and_keeps_ziwei_weight_zero() -> None:
    plan = EnginePlan(
        plan_id="plan-1",
        reading_id="r1",
        items=[
            EnginePlanItem(
                engine=EngineKey.BAZI,
                mode=EngineMode.SIGNAL_SIDECAR,
                reason="八字是主引擎",
                decision_weight=1.0,
            ),
            EnginePlanItem(
                engine=EngineKey.ZIWEI,
                mode=EngineMode.SIGNAL_SIDECAR,
                reason="紫微只做旁路观察",
                decision_weight=0.0,
            ),
        ],
    )
    assert plan.items[0].engine == EngineKey.BAZI

    with pytest.raises(ValueError, match="ZiweiEngine V1 decision_weight must be 0"):
        EnginePlanItem(
            engine=EngineKey.ZIWEI,
            mode=EngineMode.DECISION_AUX,
            reason="错误地让紫微参与裁决",
            decision_weight=0.2,
        )


def test_signal_engine_and_verdict_cannot_claim_illegal_authority() -> None:
    signal = RuntimeSignal(
        signal_id="s1",
        reading_id="r1",
        source=SignalSource.BAZI_ENGINE,
        topic=Topic.CAREER,
        claim="事业压力需要通过资质和规则承接",
        evidence_refs=["e1"],
        confidence=0.7,
    )
    assert signal.decision_authority is False

    with pytest.raises(ValueError, match="RuntimeSignal cannot have decision authority"):
        RuntimeSignal(
            signal_id="bad-signal",
            reading_id="r1",
            source=SignalSource.LLM_HYPOTHESIS,
            claim="LLM 直接裁决",
            decision_authority=True,
        )

    with pytest.raises(ValueError, match="EngineRunResult cannot have verdict authority"):
        EngineRunResult(
            result_id="er1",
            reading_id="r1",
            engine=EngineKey.BAZI,
            mode=EngineMode.SIGNAL_SIDECAR,
            verdict_authority=True,
        )

    verdict = DecisionVerdict(
        verdict_id="v1",
        reading_id="r1",
        topic=Topic.CAREER,
        headline="事业适合先稳定承接压力，再看突破",
        assertion_level=AssertionLevel.SUPPORTED,
        evidence_refs=["e1"],
    )
    assert verdict.llm_decision_authority is False

    with pytest.raises(ValueError, match="LLM cannot be verdict authority"):
        DecisionVerdict(
            verdict_id="bad-verdict",
            reading_id="r1",
            headline="LLM 裁决",
            llm_decision_authority=True,
        )


def test_decision_advice_probe_and_llm_boundaries() -> None:
    with pytest.raises(ValueError, match="DecisionInputBundle cannot use LLM output"):
        DecisionInputBundle(bundle_id="b1", reading_id="r1", llm_input_used=True)

    advice = AdvicePlan(
        advice_id="a1",
        reading_id="r1",
        topic=Topic.CAREER,
        source_verdict_ids=["v1"],
        action_points=["先补资质和稳定交付"],
    )
    assert advice.source_verdict_ids == ["v1"]

    with pytest.raises(ValueError, match="AdvicePlan cannot exceed verdict boundary"):
        AdvicePlan(
            advice_id="bad-advice",
            reading_id="r1",
            source_verdict_ids=["v1"],
            action_points=["直接重仓投资"],
            exceeds_verdict_boundary=True,
        )

    with pytest.raises(ValueError, match="information gain exceeds user cost"):
        ProbeCandidate(
            probe_id="p1",
            reading_id="r1",
            question="最近事业压力主要来自职责还是人际？",
            target_verdict_ids=["v1"],
            expected_information_gain=0.3,
            user_cost=0.5,
            ask_now=True,
        )

    with pytest.raises(ValueError, match="LLMExpressionTask cannot change verdict"):
        LLMExpressionTask(
            task_id="llm1",
            reading_id="r1",
            instruction="润色",
            can_change_verdict=True,
        )


def test_evaluation_training_and_release_gate_are_safe_by_default() -> None:
    case = EvaluationCaseSpec(
        case_id="golden-1",
        expected_verdicts=[ExpectedVerdict(topic=Topic.CAREER)],
        forbidden_assertions=[ForbiddenAssertion(text="一定发财", reason="过度断言")],
    )
    assert case.chart_fact_mutation_allowed is False

    label_event = TrainingLabelEvent(
        event_id="label-1",
        reading_id="r1",
        source=LabelSource.PRACTITIONER_SELECTION,
        target_type=LabelTargetType.VERDICT,
        target_ids=["v1"],
        label=LabelValue.SUPPORTS,
        strength=0.7,
        confidence=0.8,
        created_by_role="practitioner",
    )
    example = build_training_example_from_labels(
        example_id="ex1",
        reading_id="r1",
        topic=Topic.CAREER,
        label_events=[label_event],
    )
    assert isinstance(example, TrainingExampleV2)
    assert example.attribution_targets == ["v1"]
    assert example.global_update_allowed is False

    with pytest.raises(ValueError, match="TrainingImpactDiff cannot write production directly"):
        TrainingImpactDiff(
            training_run_id="run1",
            base_version="base",
            candidate_version="candidate",
            production_write_allowed=True,
        )

    metrics = MetricSummary(
        case_id="golden-1",
        reading_id="r1",
        evidence_coverage_rate=0.9,
        overclaim_rate=0.0,
        assertion_calibration_score=0.9,
        conflict_resolution_score=0.8,
        advice_grounding_rate=0.9,
        probe_yield_score=0.6,
        llm_boundary_violation_rate=0.0,
        surface_leakage_rate=0.0,
        overall_score=0.9,
    )
    gate = build_release_gate_from_metrics(metrics, gate_id="gate1", candidate_version="candidate")
    assert gate.recommendation == ReleaseRecommendation.APPROVE
    assert gate.production_write_allowed is False

    with pytest.raises(ValueError, match="cannot approve"):
        ReleaseGateResult(
            gate_id="bad-gate",
            candidate_version="candidate",
            fact_gate_passed=False,
            recommendation=ReleaseRecommendation.APPROVE,
        )


def test_v30_migration_accepts_plain_json_only() -> None:
    envelope = V30ExportEnvelope(
        export_id="export-1",
        reading_id="r1",
        signal_rows=[{"signal_id": "s1", "claim": "事业压力"}],
    )
    assert envelope.source_version == "v30"

    plan = V30ToV40MigrationPlan(
        plan_id="migration-plan-1",
        export_id="export-1",
        target_reading_id="r1-v40",
        enabled_importers=["signals"],
    )
    assert plan.shadow_compare_only is True

    with pytest.raises(ValueError, match="raw V30 runtime paths"):
        V30ExportEnvelope(
            export_id="bad-export",
            reading_id="r1",
            raw_runtime_path="/tmp/v30-runtime.json",
        )
