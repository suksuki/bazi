from __future__ import annotations

from v17_rebirth.backend.logic.plugin_discovery import collect_all_spec_facts, iter_all_plugin_specs


def test_new_plugin_families_are_discoverable() -> None:
    plugin_ids = {spec.plugin_id for spec in iter_all_plugin_specs()}

    assert "l0.foundation.hidden_stems.v1" in plugin_ids
    assert "l0.foundation.rooted_stems.v1" in plugin_ids
    assert "l0.foundation.exposed_hidden_stems.v1" in plugin_ids
    assert "l0.foundation.month_command.v1" in plugin_ids
    assert "l1.physics.op_branch_sanhui" in plugin_ids
    assert "l1.physics.op_branch_liuchong" in plugin_ids
    assert "classical.blind.work_axis.v1" in plugin_ids
    assert "classical.blind.response_chain.v1" in plugin_ids
    assert "classical.blind.symbol_trigger.v1" in plugin_ids
    assert "classical.blind.timing_window.v1" in plugin_ids
    assert "classical.blind.summary.v1" in plugin_ids
    assert "classical.ziping.month_command.v1" in plugin_ids
    assert "classical.ziping.balance.v1" in plugin_ids
    assert "classical.ziping.yongshen.v1" in plugin_ids
    assert "classical.ziping.climate_bridge.v1" in plugin_ids
    assert "classical.ziping.pattern_bridge.v1" in plugin_ids
    assert "classical.ziping.god_ring_resolver.v1" in plugin_ids
    assert "classical.ziping.summary.v1" in plugin_ids
    assert "classical.climate.axis.v1" in plugin_ids
    assert "classical.climate.ten_god_fit.v1" in plugin_ids
    assert "classical.climate.pattern_survival.v1" in plugin_ids
    assert "classical.climate.summary.v1" in plugin_ids
    assert "classical.xiangfa.semantic_mapping.v1" in plugin_ids
    assert "classical.xiangfa.evidence.v1" in plugin_ids
    assert "classical.xiangfa.narrative_hint.v1" in plugin_ids
    assert "classical.xiangfa.event_framing.v1" in plugin_ids
    assert "classical.pattern.axis.v1" in plugin_ids
    assert "classical.pattern.dynamic_scope.v1" in plugin_ids
    assert "classical.pattern.jianlu_yuejie.v1" in plugin_ids
    assert "classical.pattern.congshi.v1" in plugin_ids
    assert "classical.pattern.finance_officer.v1" in plugin_ids
    assert "classical.pattern.wealth_star.v1" in plugin_ids
    assert "classical.pattern.seal_star.v1" in plugin_ids
    assert "classical.pattern.yangren.v1" in plugin_ids
    assert "classical.pattern.guanyin.v1" in plugin_ids
    assert "classical.pattern.shayin.v1" in plugin_ids
    assert "classical.pattern.shishen_zhisha.v1" in plugin_ids
    assert "classical.pattern.shangguan_peiyin.v1" in plugin_ids
    assert "classical.pattern.caipoyin.v1" in plugin_ids
    assert "classical.pattern.shishen_shengcai.v1" in plugin_ids
    assert "classical.pattern.shangguan_shengcai.v1" in plugin_ids
    assert "classical.pattern.yangren_jiasha.v1" in plugin_ids
    assert "classical.pattern.zaqi_caiguan.v1" in plugin_ids
    assert "classical.pattern.zaqi_yin.v1" in plugin_ids
    assert "classical.pattern.zaqi_qisha.v1" in plugin_ids
    assert "classical.pattern.congcai.v1" in plugin_ids
    assert "classical.pattern.congsha.v1" in plugin_ids
    assert "classical.pattern.conger.v1" in plugin_ids
    assert "classical.pattern.congwang.v1" in plugin_ids
    assert "classical.pattern.congqiang.v1" in plugin_ids
    assert "classical.pattern.congruo.v1" in plugin_ids
    assert "classical.pattern.huaqi.v1" in plugin_ids
    assert "classical.pattern.quzhi.v1" in plugin_ids
    assert "classical.pattern.yanshang.v1" in plugin_ids
    assert "classical.pattern.jiase.v1" in plugin_ids
    assert "classical.pattern.congge.v1" in plugin_ids
    assert "classical.pattern.runxia.v1" in plugin_ids
    assert "classical.pattern.liangshen.v1" in plugin_ids
    assert "classical.pattern.tianyuan.v1" in plugin_ids
    assert "classical.pattern.resolver.v1" in plugin_ids
    assert "classical.pattern.formation_gate.v1" in plugin_ids
    assert "classical.pattern.break_guard.v1" in plugin_ids


def test_new_plugin_families_emit_facts_on_structured_tensor() -> None:
    pt = {
        "four_pillars": {
            "year": "丁巳",
            "month": "乙巳",
            "day": "乙丑",
            "hour": "乙酉",
        },
        "luck_pillar": "庚子",
        "flow_pillar": "丙午",
        "ten_gods_base_l0": {
            "伤官": 74.0,
            "食神": 53.0,
            "比肩": 27.0,
            "偏财": 15.0,
            "正官": 13.0,
            "七杀": 8.0,
            "正印": 7.0,
            "偏印": 5.0,
            "正财": 4.0,
            "劫财": 48.0,
        },
        "ten_gods_runtime": {
            "伤官": 74.0,
            "食神": 53.0,
            "比肩": 27.0,
            "偏财": 15.0,
            "正官": 13.0,
            "七杀": 8.0,
            "正印": 7.0,
            "偏印": 5.0,
            "正财": 4.0,
            "劫财": 48.0,
        },
        "energy_meta": {
            "month_command_god": "伤官",
            "season_power": {"month_branch": "巳"},
            "climate_field": {
                "thermal_index": 1.26,
                "moisture_index": -0.94,
                "climate_tension": 0.88,
                "state": "燥热偏盛",
                "source_by_scope": {
                    "month": {"thermal": 0.72, "moisture": -0.36},
                    "flow": {"thermal": 0.38, "moisture": -0.22},
                },
            },
            "climate_modifier_layer": {
                "ten_god_efficiency": {"伤官": 0.24, "正官": -0.18},
                "ten_god_stability": {"伤官": 0.12, "正官": -0.1},
                "yongshen_priority_delta": {"伤官": 0.22, "正官": -0.16},
                "pattern_survival_delta": {"食伤财": 0.18, "印官": -0.12},
            },
        },
        "meta": {
            "interaction_v2": {
                "liu_chong": [{"pair": ["子", "午"], "pillars": ["luck", "flow"]}],
                "san_he": [{"group": ["巳", "酉", "丑"], "pillars": ["year", "hour", "day"]}],
                "ban_he": [],
                "sanxing": [],
            },
            "blind_work_hint": "冲中起事",
            "god_ring_authority": {
                "use_gods": ["伤官", "食神"],
                "taboo_gods": ["正官"],
            },
            "climate_theme": {
                "contract": "v17.climate.theme.v1",
                "confidence": 0.72,
                "state": "燥热偏盛",
                "favored_gods": ["伤官", "食神"],
                "strained_gods": ["正官"],
                "prompt_digest": "燥热偏盛；顺势 伤官/食神；承压 正官",
            },
        },
    }

    facts = collect_all_spec_facts(pt)
    fact_plugins = {str(f.plugin_id or "") for f in facts}

    assert "l0.foundation.hidden_stems.v1" in fact_plugins
    assert "l1.physics.op_branch_liuchong" in fact_plugins
    assert "classical.blind.work_axis.v1" in fact_plugins
    assert "classical.blind.timing_window.v1" in fact_plugins
    assert "classical.blind.summary.v1" in fact_plugins
    assert "classical.ziping.month_command.v1" in fact_plugins
    assert "classical.ziping.climate_bridge.v1" in fact_plugins
    assert "classical.ziping.pattern_bridge.v1" in fact_plugins
    assert "classical.ziping.god_ring_resolver.v1" in fact_plugins
    assert "classical.ziping.summary.v1" in fact_plugins
    assert "classical.climate.axis.v1" in fact_plugins
    assert "classical.climate.summary.v1" in fact_plugins
    assert "classical.xiangfa.semantic_mapping.v1" in fact_plugins
    assert "classical.xiangfa.event_framing.v1" in fact_plugins
    assert "classical.pattern.axis.v1" in fact_plugins
    assert "classical.pattern.dynamic_scope.v1" in fact_plugins
    by_plugin = {str(f.plugin_id or ""): f for f in facts}
    assert float(by_plugin["l1.physics.op_branch_sanhe"].meta.get("match_ratio", 0.0) or 0.0) < 1.0
    assert float(by_plugin["classical.pattern.axis.v1"].meta.get("match_ratio", 0.0) or 0.0) < 1.0


def test_pattern_resolver_emits_on_multiple_pattern_candidates() -> None:
    pt = {
        "four_pillars": {
            "year": "甲寅",
            "month": "甲寅",
            "day": "甲子",
            "hour": "己辰",
        },
        "ten_gods_runtime": {
            "比肩": 82.0,
            "劫财": 41.0,
            "正财": 36.0,
            "偏财": 30.0,
            "正官": 28.0,
            "七杀": 6.0,
            "食神": 12.0,
            "伤官": 9.0,
        },
    }

    facts = collect_all_spec_facts(pt)
    resolver_facts = [f for f in facts if str(f.plugin_id or "") == "classical.pattern.resolver.v1"]
    assert resolver_facts
    assert resolver_facts[0].meta.get("pattern_candidate_count", 0) >= 2


def test_advanced_classical_patterns_emit_on_specialized_tensor() -> None:
    pt = {
        "four_pillars": {
            "year": "甲寅",
            "month": "甲卯",
            "day": "甲寅",
            "hour": "乙卯",
        },
        "ten_gods_runtime": {
            "比肩": 72.0,
            "劫财": 40.0,
            "食神": 8.0,
            "伤官": 6.0,
            "正财": 5.0,
            "偏财": 4.0,
            "正官": 3.0,
            "七杀": 2.0,
            "正印": 12.0,
            "偏印": 10.0,
        },
    }

    facts = collect_all_spec_facts(pt)
    fact_plugins = {str(f.plugin_id or "") for f in facts}

    assert "classical.pattern.congwang.v1" in fact_plugins
    assert "classical.pattern.congqiang.v1" in fact_plugins
    assert "classical.pattern.liangshen.v1" in fact_plugins


def test_huaqi_and_tianyuan_emit_on_pure_alignment_tensor() -> None:
    pt = {
        "four_pillars": {
            "year": "甲寅",
            "month": "己未",
            "day": "甲寅",
            "hour": "己未",
        },
        "ten_gods_runtime": {
            "比肩": 36.0,
            "劫财": 18.0,
            "正财": 24.0,
            "偏财": 20.0,
            "正官": 4.0,
            "七杀": 3.0,
            "食神": 8.0,
            "伤官": 7.0,
            "正印": 6.0,
            "偏印": 5.0,
        },
    }

    facts = collect_all_spec_facts(pt)
    fact_plugins = {str(f.plugin_id or "") for f in facts}

    assert "classical.pattern.huaqi.v1" in fact_plugins


def test_tianyuan_emits_on_repeated_stem_tensor() -> None:
    pt = {
        "four_pillars": {
            "year": "甲寅",
            "month": "甲寅",
            "day": "甲寅",
            "hour": "甲寅",
        },
        "ten_gods_runtime": {
            "比肩": 50.0,
            "劫财": 22.0,
            "正印": 14.0,
            "偏印": 10.0,
            "食神": 6.0,
            "伤官": 5.0,
            "正财": 8.0,
            "偏财": 6.0,
            "正官": 2.0,
            "七杀": 1.0,
        },
    }

    facts = collect_all_spec_facts(pt)
    fact_plugins = {str(f.plugin_id or "") for f in facts}

    assert "classical.pattern.tianyuan.v1" in fact_plugins


def test_pattern_gate_and_break_emit_when_conditions_match() -> None:
    pt = {
        "four_pillars": {
            "year": "甲寅",
            "month": "甲寅",
            "day": "甲子",
            "hour": "己辰",
        },
        "ten_gods_runtime": {
            "比肩": 82.0,
            "劫财": 41.0,
            "正财": 36.0,
            "偏财": 30.0,
            "正官": 28.0,
            "七杀": 6.0,
            "食神": 12.0,
            "伤官": 9.0,
        },
        "meta": {
            "interaction_v2": {
                "liu_chong": [{"pair": ["子", "午"], "pillars": ["day", "flow"]}],
            }
        },
    }
    facts = collect_all_spec_facts(pt)
    plugins = {str(f.plugin_id or "") for f in facts}
    assert "classical.pattern.formation_gate.v1" in plugins
    assert "classical.pattern.break_guard.v1" in plugins
