from __future__ import annotations

from app.services.helpers.structural_preview_semantics import (
    build_structural_preview_pattern_alert_bundle,
    build_structural_preview_vf_payloads,
    normalize_structural_preview_hint,
)


def test_normalize_rejects_unknown_kind():
    assert normalize_structural_preview_hint({"kind": "NOPE", "label": "x"}) is None


def test_l1_structure_vf_and_alert():
    h = normalize_structural_preview_hint({"kind": "L1_STRUCTURE", "label": "巳酉丑金局 · AGGREGATED", "card_id": "c1"})
    assert h is not None
    rows = build_structural_preview_vf_payloads(h)
    assert len(rows) == 1
    assert "[PREVIEW]" in rows[0]["line"]
    assert "巳酉丑金局" in rows[0]["line"]
    tensor = {"meta": {"pattern_profile": {"sovereignty_priority": True}}}
    bundle = build_structural_preview_pattern_alert_bundle(h, tensor)
    alert = str(bundle.get("fallback_zh") or "")
    assert "跃迁" in alert or "主权" in alert


def test_plugin_enable_requires_plugin_id():
    assert normalize_structural_preview_hint({"kind": "PLUGIN_ENABLE", "label": "x"}) is None
    h = normalize_structural_preview_hint({"kind": "PLUGIN_ENABLE", "plugin_id": "classical.blind_school.v1"})
    assert h is not None
    assert "blind_school" in build_structural_preview_vf_payloads(h)[0]["line"]


def test_pattern_alert_critical_when_baseline_was_pingchang_normalized():
    """V9.1：「平常局」归一为常规格，仍视为无显著格，可触发 CRITICAL 退化路径。"""
    h = normalize_structural_preview_hint(
        {
            "kind": "L1_STRUCTURE",
            "label": "测试",
            "baseline_pattern_kind": "cong_metal",
            "baseline_pattern_name_zh": "平常局",
        }
    )
    assert h is not None
    tensor = {"meta": {"pattern_profile": {"pattern_kind": "none", "pattern_name_zh": "常规格"}}}
    bundle = build_structural_preview_pattern_alert_bundle(h, tensor)
    assert "[CRITICAL]" in str(bundle.get("fallback_zh") or "")


def test_pattern_alert_critical_when_known_degrades_to_chaotic():
    h = normalize_structural_preview_hint(
        {
            "kind": "L1_STRUCTURE",
            "label": "测试局",
            "baseline_pattern_kind": "cong_metal",
            "baseline_pattern_name_zh": "从金格（能量集中度）",
        }
    )
    assert h is not None
    tensor = {"meta": {"pattern_profile": {"pattern_kind": "none", "pattern_name_zh": "常规格"}}}
    bundle = build_structural_preview_pattern_alert_bundle(h, tensor)
    alert = str(bundle.get("fallback_zh") or "")
    assert "[CRITICAL]" in alert
    assert "解体" in alert
    assert bundle.get("i18n", {}).get("template") == "shadowPreview.pattern.critical"
