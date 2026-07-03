from __future__ import annotations

from inspect import signature
from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.api.models import ConversationTurnRequest, ExpressionFromRuntimeRequest, NativeReadingReportRequest
from v40.contracts import (
    ReleaseRecommendation,
    Topic,
    TrainablePolicyRegistry,
    TrainableUnit,
    TrainableUnitType,
    TrainableUpdateScope,
    TrainingAttribution,
    TrainingLabelEvent,
)
from v40.contracts.output import AcceptanceStatus
from v40.contracts.training import LabelSource, LabelTargetType, LabelValue
from v40.conversation import build_conversation_turn
from v40.expression import OllamaExpressionError
from v40.project import build_project_status
from v40.synthetic import load_synthetic_seeds
from v40.training import build_batch_trainer_v1


def test_phase58_product_requests_default_to_ollama_without_fallback_status() -> None:
    assert NativeReadingReportRequest.model_fields["execution_mode"].default == "ollama"
    assert ConversationTurnRequest.model_fields["execution_mode"].default == "ollama"
    assert ExpressionFromRuntimeRequest.model_fields["execution_mode"].default == "ollama"
    assert signature(build_conversation_turn).parameters["execution_mode"].default == "ollama"
    assert "fallback" not in {status.value for status in AcceptanceStatus}


def test_phase58_native_report_without_execution_mode_fails_loudly_when_llm_is_down(monkeypatch) -> None:
    seed = load_synthetic_seeds("qiazhi/v40/data/synthetic/native_bazi_seeds.json")[0]

    def llm_down(**_kwargs):
        raise OllamaExpressionError("LLM 崩溃：Gemma4 不可用")

    monkeypatch.setattr("v40.api.app.render_ollama_expression_result", llm_down)
    response = TestClient(create_app()).post(
        f"{API_PREFIX}/readings/native-report",
        json={
            "request_id": "request.phase58.llm.required",
            "reading_id": "reading.phase58.llm.required",
            "chart_facts": seed.chart_facts.model_dump(mode="json"),
            "user_question": seed.question,
            "topic": Topic.CAREER.value,
            "role_key": "user",
            "persist": False,
        },
    )

    assert response.status_code == 503
    assert "LLM 崩溃" in response.json()["detail"]


def test_phase58_batch_training_directly_activates_validated_policy() -> None:
    registry = TrainablePolicyRegistry(
        registry_id="registry.phase58.base",
        active_policy_version="policy.phase58.base",
        units=[
            TrainableUnit(
                unit_id="rule_weight.career_pressure_to_platform",
                module="rule_engine",
                unit_type=TrainableUnitType.RULE_WEIGHT,
                domain=Topic.CAREER,
                claim_key="career_pressure_to_platform",
                default_value=0.5,
                current_value=0.5,
                update_scope=TrainableUpdateScope.CANDIDATE_POLICY,
                policy_version="policy.phase58.base",
            )
        ],
    )
    label = TrainingLabelEvent(
        event_id="label.phase58.direct",
        reading_id="reading.phase58.direct",
        source=LabelSource.PRACTITIONER_SELECTION,
        target_type=LabelTargetType.TRAINABLE_UNIT,
        target_ids=["rule_weight.career_pressure_to_platform"],
        label=LabelValue.SUPPORTS,
        strength=0.9,
        confidence=0.92,
        created_by_role="practitioner",
    )
    attribution = TrainingAttribution(
        attribution_id="attr.phase58.direct",
        label_event_id=label.event_id,
        affected_signal_ids=["signal.career.pressure.platform"],
        affected_trainable_refs=["rule_weight.career_pressure_to_platform"],
        affected_verdict_ids=["verdict.career.main"],
        attribution_confidence=0.9,
    )

    result = build_batch_trainer_v1(
        training_run_id="train.phase58.direct",
        base_registry=registry,
        attributions=[attribution],
        label_events=[label],
        candidate_policy_version="policy.phase58.active",
    )

    assert result.active_policy_applied is True
    assert result.candidate_registry.active is True
    assert result.candidate_registry.active_policy_version == "policy.phase58.active"
    assert result.rollback_registry_id == "registry.phase58.base"
    assert result.impact_diff.release_recommendation == ReleaseRecommendation.APPROVE
    assert "direct_policy_activation_after_validation" in result.impact_diff.improvement_summary
    assert "without_approval_gate" in result.boundary


def test_phase58_docs_and_status_record_hard_principles() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE58_HARD_LLM_AND_DIRECT_TRAINING_PRINCIPLES.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    ui_spec = Path("qiazhi/v40/docs/V40_UI_PRODUCT_FLOW_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "没有 LLM" in doc
    assert "不允许静默 fallback" in doc
    assert "不设置人工审核门" in doc
    assert "2026-07-02 Phase 58" in spec
    assert "No LLM means the product runtime fails loudly" in ui_spec
    assert "docs/V40_PHASE58_HARD_LLM_AND_DIRECT_TRAINING_PRINCIPLES.md" in readme
    assert status["current_phase"] == 73
    assert status["current_phase_name"] == "Real Case Acceptance Pack"
    assert any(row["range"] == "58" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "59" and row["status"] == "complete" for row in status["phase_groups"])
