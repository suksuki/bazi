from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts import (
    Topic,
    TrainablePolicyRegistry,
    TrainableUnit,
    TrainableUnitType,
    TrainableUpdateScope,
    TrainingAttribution,
    TrainingLabelEvent,
)
from v40.contracts.training import LabelSource, LabelTargetType, LabelValue
from v40.training import build_batch_trainer_v1


def _base_registry() -> TrainablePolicyRegistry:
    return TrainablePolicyRegistry(
        registry_id="registry.batch.v1",
        active_policy_version="policy.base.v1",
        units=[
            TrainableUnit(
                unit_id="rule_weight.food_output_to_wealth",
                module="rule_engine",
                unit_type=TrainableUnitType.RULE_WEIGHT,
                domain=Topic.WEALTH,
                claim_key="food_output_to_wealth",
                default_value=0.5,
                current_value=0.5,
                update_scope=TrainableUpdateScope.CANDIDATE_POLICY,
                policy_version="policy.base.v1",
            )
        ],
    )


def _label() -> TrainingLabelEvent:
    return TrainingLabelEvent(
        event_id="label.batch.v1",
        reading_id="reading.batch.v1",
        source=LabelSource.PRACTITIONER_SELECTION,
        target_type=LabelTargetType.TRAINABLE_UNIT,
        target_ids=["rule_weight.food_output_to_wealth"],
        label=LabelValue.SUPPORTS,
        strength=0.8,
        confidence=0.9,
        created_by_role="practitioner",
        local_only=True,
    )


def _attribution() -> TrainingAttribution:
    return TrainingAttribution(
        attribution_id="attr.batch.v1",
        label_event_id="label.batch.v1",
        affected_signal_ids=["signal.wealth.path"],
        affected_trainable_refs=[
            "rule_weight.food_output_to_wealth",
            "fact.chart.day_master",
            "advice_priority.wealth",
            "probe_voi.partnership_money_effect",
            "assertion_threshold.wealth.supported",
        ],
        affected_advice_ids=["advice.wealth"],
        affected_probe_ids=["probe.partnership"],
        attribution_confidence=0.86,
    )


def test_batch_trainer_v1_creates_candidate_policy_and_impact_diff() -> None:
    result = build_batch_trainer_v1(
        training_run_id="train.batch.v1",
        base_registry=_base_registry(),
        attributions=[_attribution()],
        label_events=[_label()],
        candidate_policy_version="policy.candidate.v1",
    )

    assert result.production_write_allowed is True
    assert result.active_policy_applied is True
    assert result.rollback_registry_id == "registry.batch.v1"
    assert result.previous_policy_version == "policy.base.v1"
    assert result.candidate_registry.active is True
    assert result.candidate_registry.active_policy_version == "policy.candidate.v1"
    assert result.candidate_registry.candidate_policy_version == "policy.candidate.v1"
    assert result.candidate_registry.previous_registry_id == "registry.batch.v1"
    assert result.changed_unit_count == 4
    unit_ids = {unit.unit_id for unit in result.candidate_registry.units}
    assert "rule_weight.food_output_to_wealth" in unit_ids
    assert "fact.chart.day_master" not in unit_ids
    changed_ids = {change.target_id for change in result.impact_diff.changed_weights}
    assert "rule_weight.food_output_to_wealth" in changed_ids
    assert "advice_priority.wealth" in result.impact_diff.changed_advice_priorities
    assert "probe_voi.partnership_money_effect" in result.impact_diff.changed_probe_policies
    assert result.impact_diff.changed_thresholds[0].target_id == "assertion_threshold.wealth.supported"
    assert "local_feedback_downweighted_until_batch_validation" in result.impact_diff.risk_summary


def test_batch_trainer_v1_api_can_run_as_dry_run_without_applying_policy() -> None:
    response = TestClient(create_app()).post(
        f"{API_PREFIX}/training/batch-trainer-v1",
        json={
            "training_run_id": "train.batch.api.v1",
            "base_registry": _base_registry().model_dump(mode="json"),
            "attributions": [_attribution().model_dump(mode="json")],
            "label_events": [_label().model_dump(mode="json")],
            "candidate_policy_version": "policy.candidate.api.v1",
            "persist_registry": False,
            "persist_impact": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["writes_v40_production"] is False
    assert body["writes_v40_policy"] is False
    assert body["changes_chart_facts"] is False
    assert body["impact_persisted"] is False
    assert body["registry_persisted"] is False
    assert body["active_policy_applied"] is False
    assert body["result"]["candidate_policy_version"] == "policy.candidate.api.v1"
    assert body["candidate_registry"]["active_policy_version"] == "policy.candidate.api.v1"
    assert body["impact"]["release_recommendation"] == "needs_review"


def test_batch_trainer_v1_docs_and_status_are_updated() -> None:
    doc = Path("qiazhi/v40/docs/V40_RC2_BATCH_TRAINER_V1.md").read_text(encoding="utf-8")
    status = Path("qiazhi/v40/v40/project/trainable_spine.py").read_text(encoding="utf-8")
    app_source = Path("qiazhi/v40/v40/api/app.py").read_text(encoding="utf-8")

    assert "POST /api/v40/training/batch-trainer-v1" in doc
    assert "BatchTrainerV1 deterministic active policy builder" in status
    assert "Direct effect after training with rollback registry pointer" in status
    assert "/training/batch-trainer-v1" in app_source
    assert "writes_v40_production" in app_source
