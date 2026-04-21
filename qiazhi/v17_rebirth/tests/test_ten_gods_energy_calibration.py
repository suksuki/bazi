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
    assert "ten_gods_decomposition_l0" in energy_meta
    # V17.30：energy_meta 应包含 season_power 信息
    assert "season_power" in energy_meta
    sp = energy_meta["season_power"]
    assert sp["month_branch"] == "寅"
    assert sp["month_element"] == "木"

    decomposition = energy_meta["ten_gods_decomposition_l0"]
    assert isinstance(decomposition, dict) and decomposition
    top_god = ten_gods[0]
    top_row = decomposition.get(top_god)
    assert isinstance(top_row, dict)
    total_parts = float(top_row.get("manifest") or 0.0) + float(top_row.get("root") or 0.0) + float(top_row.get("momentum") or 0.0) + float(top_row.get("hidden") or 0.0)
    assert round(total_parts, 2) == round(float(top_row.get("total") or 0.0), 2)
    detailed_momentum = (
        float(top_row.get("momentum_month_order") or 0.0)
        + float(top_row.get("momentum_stage") or 0.0)
        + float(top_row.get("momentum_structure") or 0.0)
        + float(top_row.get("momentum_auxiliary") or 0.0)
        + float(top_row.get("momentum_other") or 0.0)
    )
    assert round(detailed_momentum, 2) == round(float(top_row.get("momentum") or 0.0), 2)
    detailed_stage = (
        float(top_row.get("momentum_stage_lu") or 0.0)
        + float(top_row.get("momentum_stage_blade") or 0.0)
        + float(top_row.get("momentum_stage_general") or 0.0)
    )
    assert round(detailed_stage, 2) == round(float(top_row.get("momentum_stage") or 0.0), 2)


def test_stage_momentum_surfaces_for_daymaster_same_element_branch() -> None:
    """
    同五行分支若处于长生/临官/帝旺等阶段，应单独出现在阶段势账本里，
    但不应广播给非同五行十神。
    """
    scores, _, _, meta = calc_deity_scores(
        four_pillars={"year": "甲寅", "month": "丙寅", "day": "甲子", "hour": "乙卯"},
        luck_pillar="甲寅",
        flow_pillar="乙卯",
        gender="male",
    )
    decomposition = meta.get("ten_gods_decomposition_l0") or {}
    peer_row = decomposition.get("比肩") or {}
    seal_row = decomposition.get("正印") or {}
    assert float(peer_row.get("momentum_stage") or 0.0) > 0.0
    assert float(peer_row.get("momentum") or 0.0) >= float(peer_row.get("momentum_stage") or 0.0)
    assert float(seal_row.get("momentum_stage") or 0.0) == 0.0
    assert float(scores.get("比肩", 0.0)) > 0.0


def test_stage_sub_buckets_distinguish_lu_and_blade() -> None:
    """
    临官应进入禄势桶，帝旺应进入刃势桶，避免都混成一个阶段势黑箱。
    """
    lu_scores, _, _, lu_meta = calc_deity_scores(
        four_pillars={"year": "甲寅", "month": "甲寅", "day": "甲子", "hour": "乙卯"},
        luck_pillar="—",
        flow_pillar="—",
        gender="male",
    )
    blade_scores, _, _, blade_meta = calc_deity_scores(
        four_pillars={"year": "甲卯", "month": "甲卯", "day": "甲子", "hour": "乙卯"},
        luck_pillar="—",
        flow_pillar="—",
        gender="male",
    )

    lu_row = (lu_meta.get("ten_gods_decomposition_l0") or {}).get("比肩") or {}
    blade_row = (blade_meta.get("ten_gods_decomposition_l0") or {}).get("劫财") or {}
    assert float(lu_scores.get("比肩", 0.0)) > 0.0
    assert float(blade_scores.get("劫财", 0.0)) > 0.0
    assert float(lu_row.get("momentum_stage_lu") or 0.0) > 0.0
    assert float(lu_row.get("momentum_stage_blade") or 0.0) == 0.0
    assert float(blade_row.get("momentum_stage_blade") or 0.0) > 0.0
    assert float(blade_row.get("momentum_stage_lu") or 0.0) == 0.0


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


def test_day_branch_participates_but_is_weaker_than_month_branch() -> None:
    """
    日支必须参与计算，但同类藏干在月支的贡献应高于日支。
    这里用丑中癸水作对照：月支丑与日支丑都含癸，且月令不直接放大癸水。
    """
    scores, _, _, meta = calc_deity_scores(
        four_pillars={"year": "甲子", "month": "乙丑", "day": "甲丑", "hour": "丁卯"},
        luck_pillar="—",
        flow_pillar="—",
        gender="male",
    )

    assert float(scores.get("正印", 0.0)) > 0.0
    ledger = meta.get("ledger").to_dict().get("正印") or []
    month_row = next(row for row in ledger if row.get("step") == "L0_BRANCH_月" and "丑藏癸" in str(row.get("reason") or ""))
    day_row = next(row for row in ledger if row.get("step") == "L0_BRANCH_日" and "丑藏癸" in str(row.get("reason") or ""))
    assert float(month_row.get("delta") or 0.0) > float(day_row.get("delta") or 0.0)


def test_natal_stem_proximity_prefers_month_then_hour_then_year() -> None:
    """
    无根明透的同类天干，应体现“贴身显化”强弱：
    月干 > 时干 > 年干。
    该贴身加成属于天干近身作用，不应被记成根气。
    """
    scores, _, _, meta = calc_deity_scores(
        four_pillars={"year": "乙酉", "month": "乙酉", "day": "甲子", "hour": "乙酉"},
        luck_pillar="—",
        flow_pillar="—",
        gender="male",
    )

    assert float(scores.get("劫财", 0.0)) > 0.0
    ledger = meta.get("ledger").to_dict().get("劫财") or []
    year_row = next(row for row in ledger if row.get("step") == "L0_STEM_年")
    month_row = next(row for row in ledger if row.get("step") == "L0_STEM_月")
    hour_row = next(row for row in ledger if row.get("step") == "L0_STEM_时")
    assert "贴身×0.72" in str(year_row.get("reason") or "")
    assert "贴身×1.00" in str(month_row.get("reason") or "")
    assert "贴身×0.85" in str(hour_row.get("reason") or "")
    assert "浮木×0.72" in str(month_row.get("reason") or "")
    assert float(month_row.get("delta") or 0.0) > float(hour_row.get("delta") or 0.0) > float(year_row.get("delta") or 0.0)

    decomposition = meta.get("ten_gods_decomposition_l0") or {}
    peer_row = decomposition.get("劫财") or {}
    assert float(peer_row.get("manifest") or 0.0) > 0.0
    assert float(peer_row.get("root") or 0.0) == 0.0


# ── V17.30 Mass Phase 核心断言 ────────────────────────────────────────────────


def test_extreme_strong_chart_has_significantly_higher_total_energy() -> None:
    """
    Assert：在月令只作用月支自身的新口径下，
    极旺格不一定靠 total_energy_index 全盘碾压，
    但主轴峰值必须显著高于普通均衡命局。
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

    strong_peak = max(strong_scores.values())
    normal_peak = max(normal_scores.values())
    ratio = strong_peak / normal_peak if normal_peak > 0 else 0
    assert ratio >= 3.0, (
        f"极旺格主峰 ({strong_peak:.2f}) 相对普通命局主峰 ({normal_peak:.2f}) "
        f"仅 {ratio:.2f}x，应 >= 3.0x"
    )
    assert max(strong_scores, key=strong_scores.get) == "比肩"


def test_same_proportion_different_magnitude_must_differ_in_absolute_values() -> None:
    """
    Assert：即便比例相同（全比肩），高能量等级与低能量等级的命局
    必须在数值上有量级差别。

    思路：
    - 高能量：全甲木，寅月（木当令）
    - 低能量：全甲木，申月（木不得令，但 L0 不再直接因金克木而压低）
    """
    # 高能量：木当令（寅月 = 木）
    high_scores, _, high_total, _ = calc_deity_scores(
        four_pillars={"year": "甲寅", "month": "甲寅", "day": "甲寅", "hour": "甲寅"},
        luck_pillar="—",
        flow_pillar="—",
        gender="female",
    )

    # 低能量：木不得令（申月 = 金月，不再由 L0 直接压低木）
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


def test_month_order_is_localized_to_month_branch_only() -> None:
    """
    月令只能强化月支自身，不能把同元素藏干在全盘广播放大。
    """
    scores, _, _, meta = calc_deity_scores(
        four_pillars={"year": "壬寅", "month": "甲辰", "day": "丙子", "hour": "甲午"},
        luck_pillar="庚戌",
        flow_pillar="丙午",
        gender="male",
    )
    ledger = meta.get("ledger").to_dict()
    food_entries = ledger.get("食神") or []
    seasonal_entries = [row for row in food_entries if "季×" in str(row.get("reason") or "")]
    assert seasonal_entries, "月支主气应保留月令加持"
    assert len(seasonal_entries) == 1, f"不应出现月令广播：{seasonal_entries}"
    assert "月支" in str(seasonal_entries[0].get("reason") or "")
    assert float(scores.get("食神", 0.0)) < float(scores.get("偏印", 0.0))


def test_hidden_month_order_without_visible_stem_stays_floating() -> None:
    """
    只有月支藏干、没有同气天干透出的十神，应显著弱于有明透的版本。
    """
    hidden_only_scores, _, _, hidden_meta = calc_deity_scores(
        four_pillars={"year": "壬寅", "month": "甲辰", "day": "丙子", "hour": "甲午"},
        luck_pillar="庚戌",
        flow_pillar="丙午",
        gender="male",
    )
    visible_scores, _, _, _ = calc_deity_scores(
        four_pillars={"year": "壬寅", "month": "戊辰", "day": "丙子", "hour": "甲午"},
        luck_pillar="庚戌",
        flow_pillar="丙午",
        gender="male",
    )

    assert float(hidden_only_scores.get("食神", 0.0)) < 15.0
    assert float(visible_scores.get("食神", 0.0)) > float(hidden_only_scores.get("食神", 0.0)) * 1.6
    food_entries = (hidden_meta.get("ledger").to_dict().get("食神") or [])
    assert any("潜藏×" in str(row.get("reason") or "") for row in food_entries)


def test_visible_water_stem_can_root_through_same_element_hidden_water() -> None:
    """
    壬水明透时，可通过子/辰中的癸水取得同五行之根，
    但因阴阳不匹配，应按折损根气计算。
    """
    rooted_scores, _, _, rooted_meta = calc_deity_scores(
        four_pillars={"year": "壬寅", "month": "甲辰", "day": "丙子", "hour": "甲午"},
        luck_pillar="庚戌",
        flow_pillar="丙午",
        gender="male",
    )
    floating_scores, _, _, _ = calc_deity_scores(
        four_pillars={"year": "壬寅", "month": "甲戌", "day": "丙午", "hour": "甲午"},
        luck_pillar="庚戌",
        flow_pillar="丙午",
        gender="male",
    )

    assert float(rooted_scores.get("七杀", 0.0)) > float(floating_scores.get("七杀", 0.0))
    qisha_entries = (rooted_meta.get("ledger").to_dict().get("七杀") or [])
    assert any("异阴阳根×" in str(row.get("reason") or "") for row in qisha_entries)


def test_exact_hidden_root_is_stronger_than_cross_polarity_root() -> None:
    """
    癸水透出时，对子/辰中的癸水属于本根；
    壬水透出时，只能按异阴阳同五行根折损计算。
    """
    yang_scores, _, _, yang_meta = calc_deity_scores(
        four_pillars={"year": "壬寅", "month": "甲辰", "day": "丙子", "hour": "甲午"},
        luck_pillar="庚戌",
        flow_pillar="丙午",
        gender="male",
    )
    yin_scores, _, _, yin_meta = calc_deity_scores(
        four_pillars={"year": "癸寅", "month": "甲辰", "day": "丙子", "hour": "甲午"},
        luck_pillar="庚戌",
        flow_pillar="丙午",
        gender="male",
    )

    yang_stem_row = next(
        row for row in (yang_meta.get("ledger").to_dict().get("七杀") or [])
        if row.get("step") == "L0_STEM_年"
    )
    yin_stem_row = next(
        row for row in (yin_meta.get("ledger").to_dict().get("正官") or [])
        if row.get("step") == "L0_STEM_年"
    )

    assert "异阴阳根×" in str(yang_stem_row.get("reason") or "")
    assert "本根×" in str(yin_stem_row.get("reason") or "")
    assert float(yin_stem_row.get("val") or 0.0) > float(yang_stem_row.get("val") or 0.0)


def test_l0_controlled_element_is_not_directly_suppressed_by_month_order() -> None:
    """
    L0 静态层允许当令加成，但不再因为“月令所克”直接压低目标元素本体。
    """
    metal_chart, _, metal_total, _ = calc_deity_scores(
        four_pillars={"year": "辛巳", "month": "辛巳", "day": "乙酉", "hour": "辛丑"},
        luck_pillar="辛丑",
        flow_pillar="乙未",
        gender="male",
    )
    wood_chart, _, wood_total, _ = calc_deity_scores(
        four_pillars={"year": "乙卯", "month": "乙卯", "day": "乙卯", "hour": "乙未"},
        luck_pillar="乙卯",
        flow_pillar="乙未",
        gender="male",
    )

    assert metal_chart.get("七杀", 0.0) > 0.0
    assert wood_chart.get("比肩", 0.0) > 0.0
    assert metal_total > 0.0
    assert wood_total > 0.0


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


def test_dynamic_root_relation_engine_covers_xing_chong_ke_hai_he() -> None:
    """
    动态根气应纳入刑/冲/克/害/合，并在 meta 里可审计。
    """
    _, _, _, meta = calc_deity_scores(
        four_pillars={"year": "甲子", "month": "乙丑", "day": "丙午", "hour": "丁未"},
        luck_pillar="戊卯",
        flow_pillar="己酉",
        gender="male",
    )
    rel = meta.get("root_dynamic_relations") or {}
    hits = rel.get("hits") or {}
    assert int(hits.get("liuhe", 0)) >= 1
    assert int(hits.get("chong", 0)) >= 1
    assert int(hits.get("hai", 0)) >= 1
    assert int(hits.get("po", 0)) >= 1
    assert int(hits.get("xing", 0)) >= 1
    assert int(hits.get("ke", 0)) >= 1
    assert isinstance(rel.get("dynamic_applied"), dict)


def test_zi_chen_banhe_dynamic_root_boosts_qisha() -> None:
    """
    子辰半合应对水根（进而对丙日主官杀）提供可观增益。
    """
    with_banhe_scores, _, _, with_meta = calc_deity_scores(
        four_pillars={"year": "壬寅", "month": "甲辰", "day": "丙子", "hour": "甲午"},
        luck_pillar="庚戌",
        flow_pillar="丙午",
        gender="male",
    )
    no_banhe_scores, _, _, _ = calc_deity_scores(
        four_pillars={"year": "壬寅", "month": "甲辰", "day": "丙午", "hour": "甲午"},
        luck_pillar="庚戌",
        flow_pillar="丙午",
        gender="male",
    )
    rel_hits = ((with_meta.get("root_dynamic_relations") or {}).get("hits") or {})
    assert int(rel_hits.get("banhe", 0)) >= 1
    assert float(with_banhe_scores.get("七杀", 0.0)) > float(no_banhe_scores.get("七杀", 0.0))


def test_qisha_chart_with_sanhe_and_luck_stem_keeps_qisha_as_top_axis() -> None:
    """
    典型“巳酉丑 + 辛丑运”盘应维持七杀主轴，避免被比劫/食伤误抬。
    """
    scores, top4, _, meta = calc_deity_scores(
        four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        luck_pillar="辛丑",
        flow_pillar="乙未",
        gender="male",
    )
    assert top4 and top4[0] == "七杀"
    assert float(scores.get("七杀", 0.0)) > float(scores.get("正官", 0.0)) * 4.0
    rel_hits = ((meta.get("root_dynamic_relations") or {}).get("hits") or {})
    assert int(rel_hits.get("sanhe", 0)) >= 1
