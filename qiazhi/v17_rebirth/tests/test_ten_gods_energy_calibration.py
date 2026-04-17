from __future__ import annotations

from datetime import datetime

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores
from v17_rebirth.backend.services.physics_canonical import PhysicsCanonicalService


def test_calc_deity_scores_returns_absolute_energy_and_total_index() -> None:
    scores, ten_gods, total_energy_index, energy_meta = calc_deity_scores(
        four_pillars={"year": "甲子", "month": "丙寅", "day": "庚辰", "hour": "丁亥"},
        luck_pillar="戊午",
        flow_pillar="己未",
        gender="female",
        birth_time=datetime(2024, 1, 1, 12, 0, 0),
    )

    assert scores
    assert ten_gods
    assert total_energy_index == round(sum(scores.values()), 2)
    assert max(scores.values()) > 60.0
    assert energy_meta.get("constants", {}).get("stem_base_energy") == 10.0
    assert "month_command_god" in energy_meta


def test_physics_canonical_materializes_absolute_energy_lines() -> None:
    rows = PhysicsCanonicalService.materialize_prompt_lines(
        {
            "four_pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
            "luck_pillar": "戊辰",
            "flow_pillar": "己巳",
            "flow_year": 2026,
            "ten_gods_absolute_intensity": {"偏财": 88.0, "食神": 42.0},
            "total_energy_index": 130.0,
        }
    )

    assert any("十神绝对强度（非比例）" in row for row in rows)
    assert any("全盘总能量指标：130.00" in row for row in rows)
