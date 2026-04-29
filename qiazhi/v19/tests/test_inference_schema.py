from __future__ import annotations

import json
from copy import deepcopy

from v19.core import evaluate_core
from v19.core.inference_schema import (
    ACTIVITY_VALUES,
    CONFLICT_DIRECTION_VALUES,
    CONFLICT_TYPE_VALUES,
    DAY_MASTER_TENDENCIES,
    PRESENCE_VALUES,
    STRENGTH_VALUES,
    STRUCTURAL_STABILITY_STATES,
    STRUCTURE_SIGNAL_VALUES,
    TEN_GOD_KEYS,
    UNCERTAINTY_TYPE_VALUES,
    validate_inference_bundle,
)


def _chart() -> dict:
    return {
        "chart_id": "v19_inference_schema_case",
        "four_pillars": {
            "year": "甲子",
            "month": "丙辰",
            "day": "戊午",
            "hour": "壬戌",
        },
    }


def test_inference_schema_completeness() -> None:
    bundle = evaluate_core(_chart())["inference"]

    assert validate_inference_bundle(bundle)["valid"] is True
    assert set(bundle["ten_god_structure"]) == set(TEN_GOD_KEYS)
    assert isinstance(bundle["energy_flow"], list)
    assert isinstance(bundle["internal_conflicts"], list)
    assert isinstance(bundle["uncertainty_sources"], list)


def test_inference_values_are_from_allowed_sets() -> None:
    bundle = evaluate_core(_chart())["inference"]

    assert bundle["day_master_state"]["tendency"] in DAY_MASTER_TENDENCIES
    for row in bundle["ten_god_structure"].values():
        assert row["presence"] in PRESENCE_VALUES
        assert row["strength"] in STRENGTH_VALUES
        assert row["activity"] in ACTIVITY_VALUES
    for flow in bundle["energy_flow"]:
        assert flow["strength"] in STRENGTH_VALUES
    assert bundle["structural_stability"]["state"] in STRUCTURAL_STABILITY_STATES
    assert set(bundle["structural_stability"]["signals"]) <= STRUCTURE_SIGNAL_VALUES
    for conflict in bundle["internal_conflicts"]:
        assert conflict["type"] in CONFLICT_TYPE_VALUES
        assert conflict["direction"] in CONFLICT_DIRECTION_VALUES
    for uncertainty in bundle["uncertainty_sources"]:
        assert uncertainty["type"] in UNCERTAINTY_TYPE_VALUES


def test_inference_rejects_free_text_and_unknown_values() -> None:
    bundle = evaluate_core(_chart())["inference"]
    broken = deepcopy(bundle)
    broken["day_master_state"]["tendency"] = "有点强"
    broken["free_text"] = "财星偏弱，结构复杂"

    validation = validate_inference_bundle(broken)

    assert validation["valid"] is False
    assert validation["errors"]


def test_inference_rejects_missing_sources() -> None:
    bundle = evaluate_core(_chart())["inference"]
    broken = deepcopy(bundle)
    del broken["day_master_state"]["sources"]

    validation = validate_inference_bundle(broken)

    assert validation["valid"] is False
    assert any("sources" in error for error in validation["errors"])


def test_inference_rejects_domain_conclusion_field() -> None:
    bundle = evaluate_core(_chart())["inference"]
    broken = deepcopy(bundle)
    broken["domain_conclusion"] = {"wealth_type": "strong"}

    validation = validate_inference_bundle(broken)

    assert validation["valid"] is False
    assert any("domain_conclusion" in error for error in validation["errors"])


def test_inference_bundle_is_json_serializable() -> None:
    bundle = evaluate_core(_chart())["inference"]

    encoded = json.dumps(bundle, ensure_ascii=False, sort_keys=True)

    assert encoded.startswith("{")


def test_energy_flow_only_contains_present_paths() -> None:
    bundle = evaluate_core(_chart())["inference"]

    for flow in bundle["energy_flow"]:
        source = bundle["ten_god_structure"][flow["from"]]
        target = bundle["ten_god_structure"][flow["to"]]
        assert source["presence"] in {"present", "dominant"}
        assert target["presence"] in {"present", "dominant"}
