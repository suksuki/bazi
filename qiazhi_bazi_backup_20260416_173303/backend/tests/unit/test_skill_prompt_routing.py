"""盲派 skill_prompt 与因果路由 sovereignty 排序的契约。"""
from __future__ import annotations

from app.plugins.blind_school import skill_prompt as sp


def test_format_blind_skill_order_respects_sovereignty(monkeypatch) -> None:
    monkeypatch.setattr(
        sp,
        "list_blind_skills",
        lambda: [
            {"id": "low_skill", "name": "L", "description": "d1"},
            {"id": "high_skill", "name": "H", "description": "d2"},
        ],
    )
    pt = {
        "meta": {
            "enabled_plugins": ["classical.blind_school.v1"],
            "causal_routing": {
                "skill_sovereignty_rank": [
                    {"skill_id": "high_skill", "sovereignty": 0.99},
                    {"skill_id": "low_skill", "sovereignty": 0.1},
                ]
            },
        }
    }
    out = sp.format_blind_skill_registry_for_prompt(pt)
    i_high = out.index("### high_skill")
    i_low = out.index("### low_skill")
    assert i_high < i_low


def test_format_blind_skill_compact_mode_truncates_templates(monkeypatch) -> None:
    monkeypatch.setattr(
        sp,
        "list_blind_skills",
        lambda: [
            {"id": "mp_tomb_01", "name": "墓库", "description": "很长说明" * 20, "assertion_template": "x"},
        ],
    )
    pt = {"meta": {"enabled_plugins": ["classical.blind_school.v1"]}}
    full = sp.format_blind_skill_registry_for_prompt(pt, compact=False)
    short = sp.format_blind_skill_registry_for_prompt(pt, compact=True)
    assert "assertion_template" in full
    assert "assertion_template" not in short
    assert "mp_tomb_01" in short
    assert len(short) < len(full) // 2
