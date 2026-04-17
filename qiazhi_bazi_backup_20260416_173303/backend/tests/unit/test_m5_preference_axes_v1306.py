from __future__ import annotations

from app.db.m5_preference_axes import infer_m5_preference_axes


def test_infer_classical_only() -> None:
    payload = {"brain_hub": {"rows": [{"plugin_id": "classical.blind_school.v1", "score": 0.8}]}}
    axis, peak = infer_m5_preference_axes(payload)
    assert axis == "CLASSICAL_GRID"
    assert peak == 3


def test_infer_mixed() -> None:
    payload = {
        "x": [{"plugin_id": "modern.wealth_risk.v1"}],
        "y": {"plugin_id": "classical.wangshuai.v1"},
    }
    axis, peak = infer_m5_preference_axes(payload)
    assert axis == "MIXED"
    assert peak is not None and peak >= 3


def test_infer_empty() -> None:
    axis, peak = infer_m5_preference_axes({})
    assert axis == "UNKNOWN"
    assert peak is None
