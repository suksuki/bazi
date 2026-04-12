"""Decision Inbox v1：登记与 PluginMatchScore。"""
from __future__ import annotations

from app.core.plugins.registry import PluginRegistry
from app.services.decision_inbox_plugin_service import apply_decision_inbox_pipeline, compute_plugin_match_scores


def test_apply_decision_inbox_writes_meta_v1() -> None:
    reg = PluginRegistry()
    pt: dict = {"meta": {}, "deity_energy_axes": {"比肩": {"absolute_energy": 8.0}, "七杀": {"absolute_energy": 1.0}}}
    po = {
        "sys.core.physics": {"confidence_score": 0.9, "payload": {}, "verdict": "x", "evidence": [], "ok": True},
        "classical.wangshuai.v1": {
            "confidence_score": 0.7,
            "payload": {"self_abs": 12.0},
            "verdict": "y",
            "evidence": [],
            "ok": True,
        },
    }
    apply_decision_inbox_pipeline(physics_tensor=pt, plugin_outputs=po, registry=reg)
    inv = pt.get("meta", {}).get("decision_inbox_v1")
    assert isinstance(inv, dict)
    assert inv.get("dispatcher_version") == "PluginMatchScore_v1"
    assert isinstance(inv.get("signals"), list)
    assert isinstance(inv.get("lifecycle_traces"), list)
    assert any(s.get("plugin_id") == "classical.wangshuai.v1" for s in inv["signals"])


def test_match_scores_order() -> None:
    reg = PluginRegistry()
    pt = {"deity_energy_axes": {"比肩": {"absolute_energy": 20.0}, "正财": {"absolute_energy": 1.0}}, "meta": {}}
    po = {
        "sys.core.physics": {"confidence_score": 0.95, "payload": {}, "verdict": "", "evidence": [], "ok": True},
        "classical.blind_school.v1": {"confidence_score": 0.6, "payload": {}, "verdict": "", "evidence": [], "ok": True},
    }
    scores = compute_plugin_match_scores(physics_tensor=pt, plugin_outputs=po, registry=reg)
    assert scores and scores[0]["plugin_id"] == "classical.blind_school.v1"
