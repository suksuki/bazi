from __future__ import annotations

import pytest

from typing import Any, Dict, List, Type

from v17_rebirth.backend.logic.L2_structure_patterns.blind_school_family import (
    BlindResponseChainPlugin,
    BlindSummaryPlugin,
    BlindSymbolTriggerPlugin,
    BlindTimingWindowPlugin,
    BlindWorkAxisPlugin,
)
from v17_rebirth.backend.logic.L2_structure_patterns.ziping_family import (
    ZiPingBalancePlugin,
    ZiPingMonthCommandPlugin,
    ZiPingYongShenPlugin,
)
from v17_rebirth.backend.logic.L2_structure_patterns.pattern_specializations import (
    PatternAxisPlugin,
    FinanceOfficerPatternPlugin,
    GuanYinPatternPlugin,
    SealStarPatternPlugin,
    ShaYinPatternPlugin,
    ShangGuanShengCaiPatternPlugin,
    ShangGuanPeiYinPatternPlugin,
    PatternResolverPlugin,
    ShiShenShengCaiPatternPlugin,
    ShiShenZhiShaPatternPlugin,
    WealthStarPatternPlugin,
    YangRenPatternPlugin,
    YangRenJiaShaPatternPlugin,
    ZaQiCaiGuanPatternPlugin,
    ZaQiQiShaPatternPlugin,
    ZaQiYinPatternPlugin,
)
from v17_rebirth.backend.plugins.spec import V17PluginSpec


def _tensor_for_blind() -> Dict[str, Any]:
    return {
        "four_pillars": {"year": "癸未", "month": "丁亥", "day": "乙丑", "hour": "甲子"},
        "ten_gods_base_l0": {"伤官": 60.0, "食神": 48.0, "正财": 20.0},
        "ten_gods_runtime": {"伤官": 60.0, "食神": 48.0, "正财": 20.0},
        "meta": {
            "interaction_v2": {
                "liu_chong": [{"pair": ["巳", "酉"], "origin_type": "natal"}],
                "sanxing": [],
                "san_he": [],
                "ban_he": [],
            }
        },
    }


def _tensor_for_ziping() -> Dict[str, Any]:
    return {
        "four_pillars": {"month": "丁亥", "day": "乙丑"},
        "ten_gods_base_l0": {"伤官": 62.0, "食神": 40.0, "正官": 20.0, "比肩": 10.0},
        "ten_gods_runtime": {"伤官": 62.0, "食神": 40.0, "正官": 20.0, "比肩": 10.0},
        "energy_meta": {"month_command_god": "伤官", "season_power": {"month_branch": "亥"}},
    }


def _assert_interaction_protocol(fact: Any) -> None:
    meta = fact.meta
    assert isinstance(meta, dict)
    assert meta["interaction_layer"] in {"branch", "stem", "hidden", "cross_layer", "unknown"}
    assert meta["manifestation_state"] in {"manifested", "supported", "contested", "latent"}
    static_basis = meta.get("static_basis")
    assert isinstance(static_basis, dict)
    assert static_basis.get("relation_family")


def test_blind_school_family_reports_interaction_protocol() -> None:
    plugins: List[Type[V17PluginSpec]] = [
        BlindWorkAxisPlugin,
        BlindResponseChainPlugin,
        BlindSymbolTriggerPlugin,
        BlindTimingWindowPlugin,
        BlindSummaryPlugin,
    ]
    for plugin_cls in plugins:
        plugin = plugin_cls()
        facts = plugin.collect_v17_facts(_tensor_for_blind())
        assert len(facts) >= 1, f"{plugin.plugin_id} should emit facts when interaction exists"
        for fact in facts:
            _assert_interaction_protocol(fact)


def test_ziping_family_reports_interaction_protocol() -> None:
    tensor = _tensor_for_ziping()
    plugins: List[Type[V17PluginSpec]] = [
        ZiPingMonthCommandPlugin,
        ZiPingBalancePlugin,
        ZiPingYongShenPlugin,
    ]
    for plugin_cls in plugins:
        plugin = plugin_cls()
        facts = plugin.collect_v17_facts(tensor)
        assert len(facts) >= 1, f"{plugin.plugin_id} should emit diagnostic fact"
        for fact in facts:
            _assert_interaction_protocol(fact)


def test_blind_and_ziping_configs_override_match_ratio(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.L2_structure_patterns.blind_school_family.get_plugin_config",
        lambda _plugin_id: {
            "MATCH_RATIO_BASE": 0.2,
            "MATCH_RATIO_CAP": 0.33,
        },
    )

    blind = BlindWorkAxisPlugin()
    tensor = _tensor_for_blind()
    facts = blind.collect_v17_facts(tensor)
    assert facts
    assert facts[0].meta["match_ratio"] <= 0.33

    def _ziping_cfg(_plugin_id: str) -> Dict[str, Any]:
        if _plugin_id == "classical.ziping.month_command.v1":
            return {"MATCH_RATIO_TOP": 0.91, "MATCH_RATIO_OTHER": 0.1}
        return {}

    monkeypatch.setattr(
        "v17_rebirth.backend.logic.L2_structure_patterns.ziping_family.get_plugin_config",
        _ziping_cfg,
    )
    ziping = ZiPingMonthCommandPlugin()
    zip_facts = ziping.collect_v17_facts(_tensor_for_ziping())
    assert zip_facts
    assert zip_facts[0].meta["match_ratio"] == 0.91


def _tensor_for_pattern() -> Dict[str, Any]:
    return {
        "four_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        "ten_gods_runtime": {"伤官": 90.0, "食神": 70.0, "正官": 18.0, "偏财": 16.0, "比肩": 12.0},
        "ten_gods_base_l0": {"伤官": 90.0, "食神": 70.0, "正官": 18.0, "偏财": 16.0, "比肩": 12.0},
        "meta": {"interaction_v2": {"liu_chong": []}},
    }


def test_pattern_axis_plugin_match_ratio_uses_plugin_config(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.L2_structure_patterns.pattern_specializations.get_plugin_config",
        lambda plugin_id: {
            "AXIS_MATCH_BASE": 0.1,
            "AXIS_TOP_SHARE_WEIGHT": 0.0,
            "AXIS_DOMINANT_WEIGHT": 0.2,
            "AXIS_DOMINANT_DIVISOR": 10.0,
            "AXIS_ORIGIN_SCALE_MIN": 1.0,
        },
    )
    facts = PatternAxisPlugin().collect_v17_facts(_tensor_for_pattern())
    assert facts
    assert facts[0].meta["match_ratio"] == pytest.approx(0.106, abs=1e-3)


def test_pattern_resolver_and_finance_configs_adjust_thresholds(monkeypatch: Any) -> None:
    tensor = _tensor_for_pattern()

    def _cfg(plugin_id: str) -> Dict[str, Any]:
        if plugin_id == "classical.pattern.axis.v1":
            return {"CANDIDATE_FOLLOWER_RATIO": 1.2}
        if plugin_id == "classical.pattern.finance_officer.v1":
            return {"FINANCE_MIN_GOD_SUM": 10.0}
        return {}

    monkeypatch.setattr(
        "v17_rebirth.backend.logic.L2_structure_patterns.pattern_specializations.get_plugin_config",
        _cfg,
    )

    resolver = PatternResolverPlugin().collect_v17_facts(tensor)
    assert resolver
    assert resolver[0].meta["pattern_candidate_count"] >= 2

    facts = FinanceOfficerPatternPlugin().collect_v17_facts(
        {
            "four_pillars": tensor["four_pillars"],
            "ten_gods_runtime": {"正官": 40.0, "七杀": 8.0, "正财": 10.0, "偏财": 12.0},
        }
    )
    assert facts
    assert facts[0].meta["pattern_candidate"] == "财官协同"


def test_new_classical_pattern_plugins_emit_candidates() -> None:
    wealth_facts = WealthStarPatternPlugin().collect_v17_facts(
        {
            "four_pillars": {"year": "甲子", "month": "丁卯", "day": "庚午", "hour": "乙酉"},
            "ten_gods_runtime": {"正财": 32.0, "偏财": 10.0, "正官": 18.0},
        }
    )
    assert wealth_facts
    assert wealth_facts[0].meta["pattern_candidate"] == "正财格"

    seal_facts = SealStarPatternPlugin().collect_v17_facts(
        {
            "four_pillars": {"year": "甲子", "month": "戊子", "day": "甲午", "hour": "乙亥"},
            "ten_gods_runtime": {"正印": 34.0, "偏印": 11.0, "比肩": 12.0},
        }
    )
    assert seal_facts
    assert seal_facts[0].meta["pattern_candidate"] == "正印格"

    yangren_facts = YangRenPatternPlugin().collect_v17_facts(
        {
            "four_pillars": {"year": "丙寅", "month": "辛卯", "day": "甲午", "hour": "丁未"},
            "ten_gods_runtime": {"劫财": 22.0, "比肩": 14.0, "伤官": 12.0},
        }
    )
    assert yangren_facts
    assert yangren_facts[0].meta["pattern_candidate"] == "羊刃格"

    guanyin_facts = GuanYinPatternPlugin().collect_v17_facts(
        {
            "four_pillars": {"year": "甲子", "month": "辛酉", "day": "甲午", "hour": "癸酉"},
            "ten_gods_runtime": {"正官": 28.0, "正印": 24.0, "偏印": 5.0},
        }
    )
    assert guanyin_facts
    assert guanyin_facts[0].meta["pattern_candidate"] == "官印相生"

    shayin_facts = ShaYinPatternPlugin().collect_v17_facts(
        {
            "four_pillars": {"year": "甲申", "month": "庚申", "day": "甲子", "hour": "癸酉"},
            "ten_gods_runtime": {"七杀": 30.0, "正印": 20.0, "偏印": 4.0},
        }
    )
    assert shayin_facts
    assert shayin_facts[0].meta["pattern_candidate"] == "杀印相生"

    zhisha_facts = ShiShenZhiShaPatternPlugin().collect_v17_facts(
        {
            "four_pillars": {"year": "甲申", "month": "庚申", "day": "壬午", "hour": "甲辰"},
            "ten_gods_runtime": {"七杀": 26.0, "食神": 22.0, "偏印": 3.0},
        }
    )
    assert zhisha_facts
    assert zhisha_facts[0].meta["pattern_candidate"] == "食神制杀"

    peiyin_facts = ShangGuanPeiYinPatternPlugin().collect_v17_facts(
        {
            "four_pillars": {"year": "甲子", "month": "丙午", "day": "乙酉", "hour": "壬辰"},
            "ten_gods_runtime": {"伤官": 28.0, "正印": 18.0, "偏印": 3.0},
        }
    )
    assert peiyin_facts
    assert peiyin_facts[0].meta["pattern_candidate"] == "伤官配印"

    shishen_shengcai_facts = ShiShenShengCaiPatternPlugin().collect_v17_facts(
        {
            "four_pillars": {"year": "甲子", "month": "壬寅", "day": "庚午", "hour": "乙酉"},
            "ten_gods_runtime": {"食神": 24.0, "正财": 18.0, "偏财": 5.0},
        }
    )
    assert shishen_shengcai_facts
    assert shishen_shengcai_facts[0].meta["pattern_candidate"] == "食神生财"

    shangguan_shengcai_facts = ShangGuanShengCaiPatternPlugin().collect_v17_facts(
        {
            "four_pillars": {"year": "甲子", "month": "丙午", "day": "辛酉", "hour": "甲辰"},
            "ten_gods_runtime": {"伤官": 26.0, "正财": 16.0, "偏财": 4.0},
        }
    )
    assert shangguan_shengcai_facts
    assert shangguan_shengcai_facts[0].meta["pattern_candidate"] == "伤官生财"

    yangren_jiasha_facts = YangRenJiaShaPatternPlugin().collect_v17_facts(
        {
            "four_pillars": {"year": "丙寅", "month": "辛卯", "day": "甲午", "hour": "庚申"},
            "ten_gods_runtime": {"劫财": 22.0, "比肩": 10.0, "七杀": 24.0},
        }
    )
    assert yangren_jiasha_facts
    assert yangren_jiasha_facts[0].meta["pattern_candidate"] == "阳刃驾杀"

    zaqi_caiguan_facts = ZaQiCaiGuanPatternPlugin().collect_v17_facts(
        {
            "four_pillars": {"year": "甲子", "month": "丙辰", "day": "庚午", "hour": "乙酉"},
            "ten_gods_runtime": {"正财": 18.0, "偏财": 7.0, "正官": 12.0},
        }
    )
    assert zaqi_caiguan_facts
    assert zaqi_caiguan_facts[0].meta["pattern_candidate"] == "杂气财官格"

    zaqi_yin_facts = ZaQiYinPatternPlugin().collect_v17_facts(
        {
            "four_pillars": {"year": "甲子", "month": "戊辰", "day": "甲午", "hour": "乙亥"},
            "ten_gods_runtime": {"正印": 17.0, "偏印": 6.0},
        }
    )
    assert zaqi_yin_facts
    assert zaqi_yin_facts[0].meta["pattern_candidate"] == "杂气印绶格"

    zaqi_qisha_facts = ZaQiQiShaPatternPlugin().collect_v17_facts(
        {
            "four_pillars": {"year": "甲子", "month": "庚戌", "day": "甲午", "hour": "乙酉"},
            "ten_gods_runtime": {"七杀": 19.0, "正印": 4.0},
        }
    )
    assert zaqi_qisha_facts
    assert zaqi_qisha_facts[0].meta["pattern_candidate"] == "杂气七杀格"
