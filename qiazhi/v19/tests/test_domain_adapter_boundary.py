from __future__ import annotations

from copy import deepcopy

import pytest

from v19.core import evaluate_core
from v19.domain_adapters import build_domain_adapter_input, validate_domain_adapter_input


def _chart() -> dict:
    return {
        "chart_id": "v19_domain_adapter_boundary_case",
        "four_pillars": {
            "year": "甲子",
            "month": "丙辰",
            "day": "戊午",
            "hour": "壬戌",
        },
        "luck_pillar": "癸亥",
        "flow_pillar": "甲辰",
    }


def _walk_keys(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield str(key)
            yield from _walk_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _walk_keys(item)


def test_domain_adapter_maps_inference_signals_without_final_conclusion() -> None:
    inference = evaluate_core(_chart())["inference"]
    adapter_input = build_domain_adapter_input(inference, domain="wealth")

    assert adapter_input["kind"] == "DomainAdapterInput"
    assert adapter_input["domain"] == "wealth"
    assert adapter_input["wealth_signals"]["competition_pressure"]["value"] in {"none", "low", "medium", "high"}
    assert adapter_input["wealth_signals"]["stability"]["value"] in {"unknown", "low", "medium", "high", "active", "locked"}
    assert "NO_NEW_INFERENCE" in adapter_input["guardrails"]
    assert "NO_DOMAIN_CONCLUSION" in adapter_input["guardrails"]
    forbidden = {"wealth_type", "score", "conclusion", "prediction", "evidence"}
    assert not (set(_walk_keys(adapter_input)) & forbidden)
    assert validate_domain_adapter_input(adapter_input, inference)["valid"] is True


def test_domain_adapter_only_references_inference_signals() -> None:
    inference = evaluate_core(_chart())["inference"]
    adapter_input = build_domain_adapter_input(inference, domain="wealth")
    inference_keys = set(inference)

    for signal in adapter_input["wealth_signals"].values():
        assert signal["operation"] in adapter_input["allowed_operations"]
        assert signal["source_signal"].split(".")[0] in inference_keys


def test_domain_adapter_rejects_invalid_inference_bundle() -> None:
    inference = evaluate_core(_chart())["inference"]
    broken = deepcopy(inference)
    broken["day_master_state"]["tendency"] = "比较强"

    with pytest.raises(ValueError, match="V19_DOMAIN_ADAPTER_INPUT_INVALID"):
        build_domain_adapter_input(broken, domain="wealth")


def test_domain_adapter_rejects_free_text_and_domain_conclusion_in_inference() -> None:
    inference = evaluate_core(_chart())["inference"]
    broken = deepcopy(inference)
    broken["free_text"] = "财星偏弱"
    broken["domain_conclusion"] = {"wealth_type": "strong"}

    with pytest.raises(ValueError, match="V19_DOMAIN_ADAPTER_INPUT_INVALID"):
        build_domain_adapter_input(broken, domain="wealth")


def test_domain_adapter_validation_rejects_undefined_target_signal() -> None:
    inference = evaluate_core(_chart())["inference"]
    adapter_input = build_domain_adapter_input(inference, domain="wealth")
    broken = deepcopy(adapter_input)
    broken["wealth_signals"]["new_signal"] = {
        "value": "high",
        "source_signal": "structural_stability.state",
        "sources": ["structure_effects"],
        "operation": "lookup",
    }

    validation = validate_domain_adapter_input(broken, inference)

    assert validation["valid"] is False
    assert any("undefined target signal" in error for error in validation["errors"])


def test_domain_adapter_validation_rejects_missing_source_signal() -> None:
    inference = evaluate_core(_chart())["inference"]
    adapter_input = build_domain_adapter_input(inference, domain="wealth")
    broken = deepcopy(adapter_input)
    broken["wealth_signals"]["stability"]["source_signal"] = "unknown_signal.path"

    validation = validate_domain_adapter_input(broken, inference)

    assert validation["valid"] is False
    assert any("unknown source_signal" in error for error in validation["errors"])


def test_domain_adapter_rejects_unsupported_domain() -> None:
    inference = evaluate_core(_chart())["inference"]

    with pytest.raises(ValueError, match="V19_DOMAIN_ADAPTER_UNSUPPORTED_DOMAIN"):
        build_domain_adapter_input(inference, domain="career")
