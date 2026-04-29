from __future__ import annotations

from dataclasses import replace

import pytest

from v19.core import evaluate_core
from v19.domain_adapters import build_domain_adapter_input
from v19.mapping_registry import MappingRegistry, MappingUnit, validate_mapping_unit
from v19.mapping_registry.defaults import DEFAULT_WEALTH_MAPPING_UNITS
from v19.mapping_registry.registry import MappingRegistryError
from v19.synthetic_validation import DEFAULT_SYNTHETIC_CASES, run_synthetic_validation


def _chart() -> dict:
    return {
        "chart_id": "v19_mapping_registry_case",
        "four_pillars": {
            "year": "甲子",
            "month": "丙辰",
            "day": "戊午",
            "hour": "壬戌",
        },
        "luck_pillar": "癸亥",
        "flow_pillar": "甲辰",
    }


def _inference() -> dict:
    return evaluate_core(_chart())["inference"]


def test_mapping_registry_applies_reviewed_mapping_units() -> None:
    registry = MappingRegistry(DEFAULT_WEALTH_MAPPING_UNITS)
    adapter_input = build_domain_adapter_input(_inference(), mapping_registry=registry)

    assert adapter_input["kind"] == "DomainAdapterInput"
    assert adapter_input["wealth_signals"]["competition_pressure"]["mapping_id"] == "wealth.peer_vs_wealth.competition_pressure"
    assert adapter_input["wealth_signals"]["stability"]["source_signal"] == "structural_stability.state"


def test_missing_mapping_fails_closed() -> None:
    registry = MappingRegistry(DEFAULT_WEALTH_MAPPING_UNITS[:-1])

    with pytest.raises(MappingRegistryError, match="V19_MAPPING_MISSING_REVIEWED_UNITS"):
        build_domain_adapter_input(_inference(), mapping_registry=registry)


def test_invalid_mapping_value_map_fails_validation() -> None:
    invalid = MappingUnit(
        mapping_id="wealth.invalid.value_map",
        domain="wealth",
        source_signal="structural_stability.state",
        target_signal="stability",
        mapping_type="bounded_value_mapping",
        value_map={},
        status="reviewed",
        created_by="test",
        reviewed_by="test",
    )

    validation = validate_mapping_unit(invalid)

    assert validation["valid"] is False
    assert any("value_map" in error for error in validation["errors"])


def test_draft_mapping_is_not_effective() -> None:
    units = [
        replace(unit, status="draft", reviewed_by="")
        if unit.target_signal == "competition_pressure"
        else unit
        for unit in DEFAULT_WEALTH_MAPPING_UNITS
    ]
    registry = MappingRegistry(units)

    with pytest.raises(MappingRegistryError, match="V19_MAPPING_MISSING_REVIEWED_UNITS"):
        build_domain_adapter_input(_inference(), mapping_registry=registry)


def test_mapping_update_can_trigger_synthetic_validation_drift() -> None:
    units = [
        replace(
            unit,
            value_map={**unit.value_map, "unstable": "high", "conflicted": "high"},
            version="v2",
        )
        if unit.target_signal == "stability"
        else unit
        for unit in DEFAULT_WEALTH_MAPPING_UNITS
    ]
    registry = MappingRegistry(units)

    result = run_synthetic_validation(DEFAULT_SYNTHETIC_CASES, mapping_registry=registry)

    assert result["validation_run"]
    assert result["status"] == "fail"
    assert result["drift_report"]["items"]


def test_domain_adapter_does_not_add_reasoning_score_or_conclusion() -> None:
    registry = MappingRegistry(DEFAULT_WEALTH_MAPPING_UNITS)
    adapter_input = build_domain_adapter_input(_inference(), mapping_registry=registry)

    assert "NO_NEW_INFERENCE" in adapter_input["guardrails"]
    assert "NO_SCORE" in adapter_input["guardrails"]
    assert "NO_DOMAIN_CONCLUSION" in adapter_input["guardrails"]
    assert "score" not in adapter_input
    assert "conclusion" not in adapter_input
    assert {row["operation"] for row in adapter_input["wealth_signals"].values()} <= {"lookup", "bounded_value_mapping"}
