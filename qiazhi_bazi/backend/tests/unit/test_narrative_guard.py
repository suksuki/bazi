from __future__ import annotations

from app.skills.final_verdict_parts.narrative_guard import (
    extract_reasoning_feedback_loop,
    filter_logical_evidence_for_narrative_factory,
    inject_label_only_semantic_slices,
    weak_mode_requires_physics_fallback,
)


def test_filter_logical_evidence_strips_ten_god_abs_in_weak_mode() -> None:
    lines = [
        "十神.比肩.Abs=12.3",
        "语义.十神.比肩=偏强",
        "插件.conflict_zone=BLUE",
    ]
    weak = filter_logical_evidence_for_narrative_factory(lines, high_reasoning=False)
    assert "十神.比肩.Abs=" not in "".join(weak)
    assert any("语义.十神.比肩" in x for x in weak)
    strong = filter_logical_evidence_for_narrative_factory(lines, high_reasoning=True)
    assert any("十神.比肩.Abs=" in x for x in strong)


def test_weak_mode_requires_fallback_without_plugin_ref() -> None:
    obj = {
        "assertions": [
            {"assertion_id": "a1", "text": "x", "evidence_refs": ["year.branch"]},
        ]
    }
    assert weak_mode_requires_physics_fallback(obj, high_reasoning=False) is True
    assert weak_mode_requires_physics_fallback(obj, high_reasoning=True) is False


def test_weak_mode_ok_with_plugin_ref() -> None:
    obj = {
        "assertions": [
            {"assertion_id": "a1", "text": "x", "evidence_refs": ["plugin.sys.core.physics"]},
        ]
    }
    assert weak_mode_requires_physics_fallback(obj, high_reasoning=False) is False


def test_inject_label_only_semantic_slices_after_sanhe() -> None:
    pt = {"deity_energy_axes": {"比肩": {"absolute_energy": 1.5}}}
    base = [
        "地支.三合.火局=寅午戌|Status=X|Nodes=Y",
        "语义.十神.比肩=偏弱（Abs≈1.50）",
        "四柱=甲子/乙丑/丙寅/丁卯",
    ]
    out = inject_label_only_semantic_slices(base, physics_tensor=pt, enabled=True)
    assert out[0].startswith("地支.三合.")
    assert any(str(x).startswith("语义.十神总览") for x in out)
    assert not any("Abs≈" in str(x) for x in out)
    assert any(str(x).startswith("四柱=") for x in out)
    assert inject_label_only_semantic_slices(base, physics_tensor=pt, enabled=False) == base


def test_extract_reasoning_feedback_loop() -> None:
    assert extract_reasoning_feedback_loop({}) is None
    assert extract_reasoning_feedback_loop({"reasoning_feedback_loop": ""}) is None
    v = {"summary": "step1"}
    assert extract_reasoning_feedback_loop({"reasoning_feedback_loop": v}) == v
