from __future__ import annotations

from v17_rebirth.backend.logic.plugin_discovery import collect_all_spec_facts, iter_all_plugin_specs


def test_new_plugin_families_are_discoverable() -> None:
    plugin_ids = {spec.plugin_id for spec in iter_all_plugin_specs()}

    assert "l0.foundation.hidden_stems.v1" in plugin_ids
    assert "l0.foundation.rooted_stems.v1" in plugin_ids
    assert "l0.foundation.exposed_hidden_stems.v1" in plugin_ids
    assert "l0.foundation.month_command.v1" in plugin_ids
    assert "l1.physics.op_branch_liuchong" in plugin_ids
    assert "classical.blind.work_axis.v1" in plugin_ids
    assert "classical.blind.response_chain.v1" in plugin_ids
    assert "classical.blind.symbol_trigger.v1" in plugin_ids
    assert "classical.blind.timing_window.v1" in plugin_ids
    assert "classical.blind.summary.v1" in plugin_ids
    assert "classical.ziping.month_command.v1" in plugin_ids
    assert "classical.ziping.balance.v1" in plugin_ids
    assert "classical.ziping.yongshen.v1" in plugin_ids
    assert "classical.pattern.axis.v1" in plugin_ids
    assert "classical.pattern.jianlu_yuejie.v1" in plugin_ids
    assert "classical.pattern.congshi.v1" in plugin_ids
    assert "classical.pattern.finance_officer.v1" in plugin_ids
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
        },
        "meta": {
            "interaction_v2": {
                "liu_chong": [{"pair": ["子", "午"], "pillars": ["luck", "flow"]}],
                "san_he": [{"group": ["巳", "酉", "丑"], "pillars": ["year", "hour", "day"]}],
                "ban_he": [],
                "sanxing": [],
            },
            "blind_work_hint": "冲中起事",
            "hit_pattern_name": "食伤外放格",
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
    assert "classical.pattern.axis.v1" in fact_plugins


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
