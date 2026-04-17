from __future__ import annotations

import app.services.analysis_service  # noqa: F401 — 预热 registry

from app.logic.brain.decision_hub import DecisionInboxFeedbackCollector


def test_feedback_collector_appends_logical_patches() -> None:
    meta: dict = {}
    DecisionInboxFeedbackCollector.record_inbox_step(
        meta,
        action="toggle_plugin",
        payload={"plugin_id": "classical.blind_school.v1", "on": True},
        conflict_signature="clash|子午冲",
    )
    ic = meta.get("incremental_context_v14") or {}
    patches = ic.get("logical_patches") or []
    assert len(patches) == 1
    assert patches[0].get("protocol") == "logical_patch.v14"
    assert patches[0].get("action") == "toggle_plugin"


def test_m5_checkbox_adjusts_plugin_weight_deltas() -> None:
    meta: dict = {}
    DecisionInboxFeedbackCollector.apply_checkbox_to_m5_will(
        meta, plugin_id="classical.blind_school.v1", checked=True, delta=0.2
    )
    m5 = meta.get("m5_will_anchor_v14") or {}
    d = m5.get("plugin_weight_deltas") or {}
    assert abs(float(d.get("classical.blind_school.v1", 0.0)) - 0.2) < 1e-6
    DecisionInboxFeedbackCollector.apply_checkbox_to_m5_will(
        meta, plugin_id="classical.blind_school.v1", checked=False, delta=0.2
    )
    d2 = (meta.get("m5_will_anchor_v14") or {}).get("plugin_weight_deltas") or {}
    assert abs(float(d2.get("classical.blind_school.v1", 0.0)) - 0.0) < 1e-6
