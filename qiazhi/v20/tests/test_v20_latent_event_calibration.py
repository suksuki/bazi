from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from v20.api.schemas import LatentEventCalibrationRequest
from v20.interaction.latent_event_calibration import (
    LatentCalibrationAnswer,
    analyze_latent_event_calibration,
    latent_event_calibration_manifest,
    record_latent_event_calibration,
)
from v20.server import app
from v20.storage.local_jsonl import LocalJsonlStore


def _endpoint(path: str, method: str = "GET"):
    method = method.upper()
    for route in app.routes:
        if getattr(route, "path", "") == path and method in getattr(route, "methods", set()):
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def test_v20_latent_event_calibration_manifest_is_choice_based() -> None:
    manifest = latent_event_calibration_manifest()

    assert manifest["version"] == "v20.latent_event_calibration_manifest.v1"
    assert manifest["input_policy"]["free_text_allowed"] is False
    assert manifest["scenario_count"] >= 6
    assert all(row["year_options"] for row in manifest["scenarios"])
    assert all(row["result_options"] for row in manifest["scenarios"])
    assert "STRUCTURED_CHOICES_ONLY" in manifest["guardrails"]


def test_v20_latent_event_calibration_analyzes_factor_signals() -> None:
    report = analyze_latent_event_calibration(
        input_id="profile:test",
        source_role="user",
        answers=(
            LatentCalibrationAnswer(
                scenario_id="latent.wealth_change",
                year_option="25_to_30",
                result_option="income_up",
                intensity="strong",
                confidence="high",
            ),
        ),
    )

    factor_ids = {row["factor_id"] for row in report["factor_update_signals"]}
    assert report["runtime_mutation"] is False
    assert {"wealth_amplifier", "timing_sensitivity", "resource_support"} <= factor_ids
    assert report["factor_update_signals"][0]["evidence_strength"] > 0.8
    assert report["factor_update_signals"][0]["runtime_allowed"] is False


def test_v20_latent_event_calibration_rejects_uncontrolled_options() -> None:
    with pytest.raises(ValueError):
        analyze_latent_event_calibration(
            input_id="profile:test",
            source_role="user",
            answers=(
                LatentCalibrationAnswer(
                    scenario_id="latent.wealth_change",
                    year_option="2018",
                    result_option="我那年赚了很多钱",
                    intensity="strong",
                    confidence="high",
                ),
            ),
        )


def test_v20_latent_event_calibration_record_is_append_only(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    result = record_latent_event_calibration(
        input_id="profile:test",
        source_role="user",
        answers=(
            LatentCalibrationAnswer(
                scenario_id="latent.action_result",
                year_option="unknown",
                result_option="needs_repeated_attempts",
                intensity="clear",
                confidence="medium",
            ),
        ),
        store=store,
    )

    assert result["runtime_mutation"] is True
    assert result["storage"]["ledger_name"] == "latent_event_calibration_ledger"
    assert "NO_RUNTIME_RULE_MUTATION" in result["guardrails"]


def test_v20_latent_event_calibration_endpoints_are_guarded() -> None:
    manifest = _endpoint("/api/v20/learning/latent-event-calibration")()
    analyzed = _endpoint("/api/v20/latent-event/calibration/analyze", "POST")(
        LatentEventCalibrationRequest(
            input_id="profile:test",
            source_role="user",
            answers=[
                {
                    "scenario_id": "latent.career_transition",
                    "year_option": "31_to_36",
                    "result_option": "platform_change",
                    "intensity": "clear",
                    "confidence": "medium",
                }
            ],
        )
    )
    try:
        _endpoint("/api/v20/latent-event/calibration/analyze", "POST")(
            LatentEventCalibrationRequest(
                input_id="profile:test",
                source_role="user",
                answers=[
                    {
                        "scenario_id": "latent.career_transition",
                        "year_option": "2019",
                        "result_option": "platform_change",
                        "intensity": "clear",
                        "confidence": "medium",
                    }
                ],
            )
        )
        raise AssertionError("invalid latent event option should fail")
    except HTTPException as exc:
        rejected_status = exc.status_code

    assert manifest["scenario_count"] >= 6
    assert analyzed["factor_update_signals"]
    assert rejected_status == 400
