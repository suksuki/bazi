from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts import Topic, TrainablePolicyRegistry, TrainableUnit, TrainableUnitType, TrainableUpdateScope
from v40.contracts.training import LabelSource, LabelTargetType, LabelValue, TrainingAttribution, TrainingLabelEvent
from v40.project import build_direct_training_activation_evidence, build_project_status
from v40.training import build_batch_trainer_v1


def _base_registry() -> TrainablePolicyRegistry:
    return TrainablePolicyRegistry(
        registry_id="registry.phase70.base",
        active_policy_version="policy.phase70.base",
        units=[
            TrainableUnit(
                unit_id="advice_priority.career",
                module="advice_engine",
                unit_type=TrainableUnitType.ADVICE_PRIORITY,
                domain=Topic.CAREER,
                claim_key="career",
                default_value=0.5,
                current_value=0.5,
                update_scope=TrainableUpdateScope.CANDIDATE_POLICY,
                policy_version="policy.phase70.base",
            )
        ],
    )


def _label() -> TrainingLabelEvent:
    return TrainingLabelEvent(
        event_id="label.phase70",
        reading_id="reading.phase70",
        source=LabelSource.PRACTITIONER_SELECTION,
        target_type=LabelTargetType.TRAINABLE_UNIT,
        target_ids=["advice_priority.career"],
        label=LabelValue.GOOD_ADVICE,
        strength=0.8,
        confidence=0.9,
        created_by_role="practitioner",
        local_only=True,
    )


def _attribution() -> TrainingAttribution:
    return TrainingAttribution(
        attribution_id="attr.phase70",
        label_event_id="label.phase70",
        affected_signal_ids=["signal.career"],
        affected_verdict_ids=["verdict.career"],
        affected_advice_ids=["advice.career"],
        affected_probe_ids=["probe.career"],
        affected_trainable_refs=[
            "advice_priority.career",
            "probe_voi.career_hidden",
            "assertion_threshold.career.supported",
        ],
        attribution_confidence=0.86,
    )


def _trainer_result():
    return build_batch_trainer_v1(
        training_run_id="train.phase70",
        base_registry=_base_registry(),
        attributions=[_attribution()],
        label_events=[_label()],
        candidate_policy_version="policy.phase70.active",
    )


def test_phase70_activation_evidence_explains_direct_training_effect_and_rollback() -> None:
    result = _trainer_result()

    evidence = build_direct_training_activation_evidence(result=result)

    assert evidence["active_policy_applied"] is True
    assert evidence["active_policy_version"] == "policy.phase70.active"
    assert evidence["rollback_registry_id"] == "registry.phase70.base"
    assert evidence["rollback_ready"] is True
    assert evidence["automatic_status"] == "ready"
    assert evidence["changed_unit_count"] == result.changed_unit_count
    assert evidence["weight_changes"]
    assert evidence["threshold_changes"]
    assert evidence["changed_probe_policy_count"] == 1
    assert evidence["changed_advice_priority_count"] == 1
    assert evidence["affected_counts"]["verdicts"] == 1
    assert evidence["writes_v40_production"] is False


def test_phase70_activation_evidence_api_is_readonly() -> None:
    result = _trainer_result()

    response = TestClient(create_app()).post(
        f"{API_PREFIX}/project/direct-training-activation-evidence",
        json={"result": result.model_dump(mode="json")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "v40.direct_training_activation_evidence_response.v1"
    assert body["evidence"]["automatic_status"] == "ready"
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False
    assert body["boundary"] == "direct_training_activation_evidence_reads_active_policy_without_mutation"


def test_phase70_docs_and_project_status_track_direct_training_activation_evidence() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE70_DIRECT_TRAINING_ACTIVATION_EVIDENCE.md").read_text(
        encoding="utf-8"
    )
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "Direct Training Activation Evidence" in doc
    assert "POST /api/v40/project/direct-training-activation-evidence" in doc
    assert "docs/V40_PHASE70_DIRECT_TRAINING_ACTIVATION_EVIDENCE.md" in readme
    assert status["current_phase"] == 73
    assert status["current_phase_name"] == "Real Case Acceptance Pack"
    assert any(row["range"] == "69" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "70" and row["status"] == "complete" for row in status["phase_groups"])
    assert status["next_mainline_tasks"][0] == "QA-19: live LLM report/conversation acceptance on selected real cases"
