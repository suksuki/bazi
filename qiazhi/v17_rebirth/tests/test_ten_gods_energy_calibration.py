"""
V17.30 Mass Phase 验证断言：

1. calc_deity_scores 返回绝对能量 + total_energy_index
2. 极旺格 total_energy_index 显著高于普通命局
3. 即便比例相同，高能量等级与低能量等级必须在数值上有量级差别
4. Season Power 应用验证
5. PhysicsCanonicalService 物化行正确显示绝对能量
"""
from __future__ import annotations

from datetime import datetime

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores
from v17_rebirth.backend.services.physics_canonical import PhysicsCanonicalService


def test_calc_deity_scores_returns_absolute_energy_and_total_index() -> None:
    """基本断言：返回值结构正确，total_energy_index = sum(scores)。"""
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
    # V17.30：Season Power 已取代旧的 MONTH_COMMAND_AMPLIFIER，
    # 能量现在会在被 Season Power 放大后累加，总能量应在合理范围
    assert total_energy_index >= 50.0, f"total_energy_index too low: {total_energy_index}"
    assert energy_meta.get("constants", {}).get("stem_base") == 10.0
    assert energy_meta.get("constants", {}).get("branch_base") == 12.0
    assert "month_command_god" in energy_meta
    # V17.30：energy_meta 应包含 season_power 信息
    assert "season_power" in energy_meta
    sp = energy_meta["season_power"]
    assert sp["month_branch"] == "寅"
    assert sp["month_element"] == "木"


def test_physics_canonical_materializes_absolute_energy_lines() -> None:
    """PhysicsCanonicalService 能正确物化绝对能量行。"""
    rows = PhysicsCanonicalService.materialize_prompt_lines(
        {
            "four_pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
            "luck_pillar": "戊辰",
            "flow_pillar": "己巳",
            "flow_year": 2026,
            "ten_gods_absolute": {"偏财": 88.0, "食神": 42.0},
            "ten_gods_absolute_intensity": {"偏财": 88.0, "食神": 42.0},
            "total_energy_index": 130.0,
        }
    )

    assert any("十神绝对强度（非比例）" in row for row in rows)
    assert any("全盘总能量指标：130.00" in row for row in rows)


# ── V17.30 Mass Phase 核心断言 ────────────────────────────────────────────────


def test_extreme_strong_chart_has_significantly_higher_total_energy() -> None:
    """
    Assert：在一个极旺格（木旺命局，寅月，天干全木/水生木）中，
    total_energy_index 应显著高于普通均衡命局。
    """
    # 极旺格：日主甲木，月令寅木（当令），年时全木/水支撑
    strong_scores, _, strong_total, strong_meta = calc_deity_scores(
        four_pillars={"year": "甲寅", "month": "甲寅", "day": "甲寅", "hour": "甲寅"},
        luck_pillar="甲寅",
        flow_pillar="甲寅",
        gender="male",
    )

    # 普通命局：五行分散，无集中力量
    normal_scores, _, normal_total, normal_meta = calc_deity_scores(
        four_pillars={"year": "甲子", "month": "丙寅", "day": "戊辰", "hour": "庚午"},
        luck_pillar="壬申",
        flow_pillar="癸酉",
        gender="male",
    )

    # 极旺格总能量必须显著高于普通命局（至少 1.5 倍）
    ratio = strong_total / normal_total if normal_total > 0 else 0
    assert ratio >= 1.5, (
        f"极旺格 ({strong_total:.2f}) 相对普通命局 ({normal_total:.2f}) "
        f"量级比仅 {ratio:.2f}x，应 >= 1.5x"
    )

    # 极旺格总能量应在高位范围（>= 200）
    assert strong_total >= 200.0, (
        f"极旺格 total_energy_index = {strong_total:.2f}, "
        f"预期 >= 200.0（全木/水得令得势）"
    )


def test_same_proportion_different_magnitude_must_differ_in_absolute_values() -> None:
    """
    Assert：即便比例相同（全比肩），高能量等级与低能量等级的命局
    必须在数值上有量级差别。

    思路：
    - 高能量：全甲木，寅月（木当令）
    - 低能量：全甲木，申月（木被月令金所克）
    """
    # 高能量：木当令（寅月 = 木）
    high_scores, _, high_total, _ = calc_deity_scores(
        four_pillars={"year": "甲寅", "month": "甲寅", "day": "甲寅", "hour": "甲寅"},
        luck_pillar="—",
        flow_pillar="—",
        gender="female",
    )

    # 低能量：木被克（申月 = 金克木）
    low_scores, _, low_total, _ = calc_deity_scores(
        four_pillars={"year": "甲申", "month": "甲申", "day": "甲申", "hour": "甲申"},
        luck_pillar="—",
        flow_pillar="—",
        gender="female",
    )

    # 两者十神分布都应以比肩为主
    assert "比肩" in high_scores
    assert "比肩" in low_scores

    # 但绝对数值必须有量级差别
    assert high_total > low_total, (
        f"High energy ({high_total:.2f}) should be greater than low energy ({low_total:.2f})"
    )
    # 至少差 30%
    gap_ratio = (high_total - low_total) / max(low_total, 0.01)
    assert gap_ratio >= 0.3, (
        f"Absolute energy gap ratio = {gap_ratio:.2f}, should be >= 0.3 "
        f"(high={high_total:.2f}, low={low_total:.2f})"
    )


def test_season_power_amplifies_in_season_element() -> None:
    """
    验证月令当令五行确实获得 Season Power 放大。
    """
    # 火命月令午火（当令）
    fire_scores, _, fire_total, fire_meta = calc_deity_scores(
        four_pillars={"year": "丙午", "month": "丙午", "day": "丙午", "hour": "丙午"},
        luck_pillar="—",
        flow_pillar="—",
        gender="male",
    )

    # 火命月令子水（受制）
    water_scores, _, water_total, water_meta = calc_deity_scores(
        four_pillars={"year": "丙子", "month": "丙子", "day": "丙子", "hour": "丙子"},
        luck_pillar="—",
        flow_pillar="—",
        gender="male",
    )

    # 火当令的总能量应远高于火受制的（注意：子水月下水系藏干也获得 Season Power，
    # 因此对比不如纯五行阵那么悬殊，1.3x 为合理下限）
    assert fire_total > water_total * 1.3, (
        f"Fire in-season ({fire_total:.2f}) should be > 1.3x fire out-of-season ({water_total:.2f})"
    )


def test_total_energy_range_is_in_expected_band() -> None:
    """
    验证现实命局的 total_energy_index 落在 V17.30 预期范围（50.0 - 500.0+）。
    """
    # 一个典型的现实命局
    _, _, total, _ = calc_deity_scores(
        four_pillars={"year": "壬戌", "month": "辛亥", "day": "甲辰", "hour": "丁卯"},
        luck_pillar="庚戌",
        flow_pillar="丙午",
        gender="female",
        birth_time=datetime(1982, 11, 15, 5, 30, 0),
    )

    assert total >= 50.0, f"total_energy_index = {total:.2f}, expected >= 50.0"
    assert total <= 800.0, f"total_energy_index = {total:.2f}, expected <= 800.0 (sanity cap)"
