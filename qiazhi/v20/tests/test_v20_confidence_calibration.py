from __future__ import annotations

from v20.core.chart import build_chart_facts, chart_input_from_displays
from v20.core.strength import infer_core
from v20.features.calibration import (
    ConfidenceCalibrationPolicy,
    calibrate_features,
    confidence_calibration_manifest,
)
from v20.features.compiler import compile_features
from v20.server import app


def _endpoint(path: str):
    for route in app.routes:
        if getattr(route, "path", "") == path:
            return route.endpoint
    raise AssertionError(f"route not found: {path}")


def test_v20_confidence_calibration_adjusts_numeric_confidence_only() -> None:
    facts = build_chart_facts(chart_input_from_displays("甲子", "戊辰", "甲午", "辛酉"))
    layer = compile_features(facts, infer_core(facts))
    calibrated = calibrate_features(
        layer.features,
        ConfidenceCalibrationPolicy(policy_id="test.branch", domain_offsets={"branch": 0.8}, source="test", status="draft"),
    )

    before = {feature.feature_id: feature for feature in layer.features}
    after = {feature.feature_id: feature for feature in calibrated}
    assert set(before) == set(after)
    for feature_id, feature in before.items():
        assert after[feature_id].evidence_refs == feature.evidence_refs
        assert after[feature_id].question_hooks == feature.question_hooks
    assert after["feature.branch.visible_relation"].confidence <= 0.92
    assert after["feature.branch.visible_relation"].confidence > before["feature.branch.visible_relation"].confidence


def test_v20_compile_features_accepts_calibration_policy_without_new_features() -> None:
    facts = build_chart_facts(chart_input_from_displays("甲子", "戊辰", "甲午", "辛酉"))
    core = infer_core(facts)
    baseline = compile_features(facts, core)
    calibrated = compile_features(
        facts,
        core,
        calibration_policy=ConfidenceCalibrationPolicy(domain_offsets={"wealth": 0.4}, source="test", status="draft"),
    )

    assert {row.feature_id for row in baseline.features} == {row.feature_id for row in calibrated.features}
    assert max(row.confidence for row in calibrated.features if row.domain == "wealth") > max(
        row.confidence for row in baseline.features if row.domain == "wealth"
    )


def test_v20_confidence_calibration_manifest_endpoint_is_guarded() -> None:
    endpoint = _endpoint("/api/v20/features/confidence-calibration")()
    manifest = confidence_calibration_manifest()

    assert endpoint["runtime_mutation"] is False
    assert endpoint["blocked_learning_outputs"] == manifest["blocked_learning_outputs"]
    assert "new_feature" in endpoint["blocked_learning_outputs"]
    assert "FEATURE_IDS_AND_EVIDENCE_REFS_ARE_IMMUTABLE" in endpoint["guardrails"]
