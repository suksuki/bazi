from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from v40.admin.app import ADMIN_PREFIX, create_admin_app
from v40.api.app import API_PREFIX, create_app
from v40.contracts import (
    RuntimeSignal,
    Topic,
    TrainablePolicyRegistry,
    TrainableUnit,
    TrainableUnitType,
    TrainableUpdateScope,
    TrainingAttribution,
    TrainingLabelEvent,
)
from v40.contracts.signal import SignalSource
from v40.contracts.training import LabelSource, LabelTargetType, LabelValue
from v40.project import build_trainable_runtime_spine_status
from v40.training import build_training_attribution_from_label


def test_runtime_signal_syncs_trainable_targets_and_refs() -> None:
    signal = RuntimeSignal(
        signal_id="sig-wealth-path",
        reading_id="r1",
        source=SignalSource.BAZI_ENGINE,
        topic=Topic.WEALTH,
        claim="食伤生财路径支持项目型财富",
        claim_key="food_output_to_wealth",
        trainable_targets=["rule_weight.food_output_to_wealth", "assertion_threshold.wealth.supported"],
    )

    assert signal.trainable_refs == [
        "rule_weight.food_output_to_wealth",
        "assertion_threshold.wealth.supported",
    ]
    assert signal.trainable_targets == signal.trainable_refs


def test_trainable_units_cannot_target_fact_modules() -> None:
    unit = TrainableUnit(
        unit_id="rule_weight.food_output_to_wealth",
        module="rule_engine",
        unit_type=TrainableUnitType.RULE_WEIGHT,
        domain=Topic.WEALTH,
        claim_key="food_output_to_wealth",
        default_value=0.6,
        current_value=0.62,
        min_value=0.0,
        max_value=1.0,
        update_scope=TrainableUpdateScope.CANDIDATE_POLICY,
    )
    registry = TrainablePolicyRegistry(
        registry_id="policy-registry-v1",
        active_policy_version="baseline",
        units=[unit],
    )

    assert registry.direct_global_update_allowed is False
    assert registry.release_gate_required_for_global is True

    with pytest.raises(ValueError, match="cannot target fact modules"):
        TrainableUnit(
            unit_id="fact.four_pillars",
            module="bazi_fact_engine_pro",
            unit_type=TrainableUnitType.SOURCE_WEIGHT,
        )


def test_training_label_and_attribution_are_local_first() -> None:
    signal = RuntimeSignal(
        signal_id="sig-competition-wealth",
        reading_id="r1",
        source=SignalSource.BAZI_ENGINE,
        topic=Topic.WEALTH,
        claim="比劫竞争经食伤转化为项目型财富",
        claim_key="competition_wealth_mode",
        trainable_refs=["rule_weight.competition_wealth_mode", "probe_voi.partnership_money_effect"],
    )
    label = TrainingLabelEvent(
        event_id="label-wealth-probe",
        reading_id="r1",
        source=LabelSource.PROBE_ANSWER,
        target_type=LabelTargetType.HIDDEN_ATTRIBUTE,
        target_ids=["partnership_money_effect.competitive_but_useful"],
        also_supports=["competition_wealth_mode"],
        weakens=["pure_bijie_robs_wealth"],
        label=LabelValue.SUPPORTS,
        strength=0.8,
        confidence=0.86,
        local_only=True,
    )
    attribution = build_training_attribution_from_label(
        attribution_id="attr-wealth-probe",
        label_event=label,
        signals=[signal],
    )

    assert attribution.update_scope == TrainableUpdateScope.LOCAL_OVERLAY
    assert attribution.affected_signal_ids == ["sig-competition-wealth"]
    assert "hidden_attribute.partnership_money_effect.competitive_but_useful" in attribution.affected_trainable_refs
    assert "rule_weight.competition_wealth_mode" in attribution.affected_trainable_refs

    with pytest.raises(ValueError, match="requires batch review"):
        TrainingLabelEvent(
            event_id="bad-global-label",
            reading_id="r1",
            source=LabelSource.PRACTITIONER_SELECTION,
            target_type=LabelTargetType.TRAINABLE_UNIT,
            target_ids=["rule_weight.competition_wealth_mode"],
            label=LabelValue.SUPPORTS,
            local_only=False,
        )

    with pytest.raises(ValueError, match="requires release gate"):
        TrainingAttribution(
            attribution_id="bad-global-attr",
            label_event_id="label-wealth-probe",
            affected_trainable_refs=["rule_weight.competition_wealth_mode"],
            update_scope=TrainableUpdateScope.GLOBAL_POLICY,
            release_gate_required=False,
        )


def test_trainable_runtime_spine_status_and_docs_are_available() -> None:
    status = build_trainable_runtime_spine_status()

    assert status["boundary"] == "trainable_runtime_spine_trains_policy_not_facts"
    assert "bazi_four_pillars" in status["immutable_fact_modules"]
    assert "rule_weight" in status["trainable_unit_types"]
    assert "TrainablePolicyRegistry" in status["contracts"]

    response = TestClient(create_app()).get(f"{API_PREFIX}/project/trainable-runtime-spine")
    assert response.status_code == 200
    body = response.json()
    assert body["status"]["version"] == "v40.trainable_runtime_spine_status.v1"
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False

    doc = Path("qiazhi/v40/docs/V40_RC2_TRAINABLE_RUNTIME_SPINE.md").read_text(encoding="utf-8")
    assert "事实型基础模块只验证，不训练" in doc
    assert "TrainableUnit" in doc
    assert "BatchTrainerV1" in doc


def test_admin_console_exposes_trainable_spine_panel() -> None:
    page = TestClient(create_admin_app()).get(ADMIN_PREFIX)

    assert page.status_code == 200
    assert "Trainable Spine" in page.text
    assert "/admin/v40/api/trainable-runtime-spine" in page.text
