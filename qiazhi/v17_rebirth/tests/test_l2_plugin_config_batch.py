from __future__ import annotations

import pytest

from v17_rebirth.backend.logic.L0_physics_fields.chang_sheng_12 import PLUGIN as StatusPlugin
from v17_rebirth.backend.logic.L2_structure_patterns.kong_wang import PLUGIN as KongWangPlugin
from v17_rebirth.backend.logic.L2_structure_patterns.shensha import PLUGIN as ShenshaPlugin
from v17_rebirth.backend.logic.L2_structure_patterns.ten_god_pattern import PLUGIN as TenGodPatternPlugin


def test_op_status_uses_plugin_id_and_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {
            "RESISTANCE_HIGH": 1.3,
            "RESISTANCE_LOW": 0.6,
            "STAGE_PRIORITY": 0.9,
        },
    )
    facts = StatusPlugin.collect_v17_facts(
        {
            "four_pillars": {"day": "乙丑", "month": "丁亥"},
            "meta": {},
        }
    )

    assert len(facts) == 1
    fact = facts[0]
    assert fact.plugin_id == "l1.physics.op_status"
    assert fact.priority == 0.9
    assert fact.meta["stage_name"] == "长生"
    assert fact.meta["resistance_ratio"] == 1.3


def test_ten_god_pattern_respects_thresholds_and_priority(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {
            "GUAN_THRESHOLD": 50.0,
            "SHI_SHANG_THRESHOLD": 20.0,
            "CAI_THRESHOLD": 35.0,
            "PATTERN_PRIORITY": 0.88,
        },
    )
    facts = TenGodPatternPlugin.collect_v17_facts(
        {
            "ten_gods_absolute": {"伤官": 55.0, "正官": 45.0, "偏财": 18.0},
            "ten_gods_runtime": {"伤官": 55.0, "正官": 45.0, "偏财": 18.0},
        }
    )

    assert len(facts) == 1
    assert "食伤主轴" in facts[0].text
    assert facts[0].priority == 0.88


def test_ten_god_pattern_reports_mixed_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {
            "PROFILE_TOP_GODS": 3,
            "PROFILE_MIN_SCORE": 10.0,
            "PATTERN_PRIORITY": 0.88,
            "GUAN_THRESHOLD": 40.0,
            "SHI_SHANG_THRESHOLD": 35.0,
            "CAI_THRESHOLD": 35.0,
            "AXIS_ORIGIN_SCALE_MIN": 1.0,
        },
    )
    facts = TenGodPatternPlugin.collect_v17_facts(
        {
            "ten_gods_absolute": {"伤官": 65.0, "正官": 45.0, "偏财": 22.0, "比肩": 8.0},
            "ten_gods_runtime": {"伤官": 65.0, "正官": 45.0, "偏财": 22.0, "比肩": 8.0},
        }
    )

    assert len(facts) == 1
    profile = facts[0].meta.get("pattern_profile")
    assert isinstance(profile, list) and len(profile) >= 2
    families = [str(item.get("family") or "") for item in profile]
    assert "食伤主轴" in families
    assert "官杀主轴" in families
    assert facts[0].meta.get("pattern_mix_mode") == "soft_mix"
    assert float(facts[0].meta.get("dominant_ratio", 0.0) or 0.0) > 1.0

def test_shensha_respects_thresholds_and_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {
            "TIAN_YI_THRESHOLD": 30.0,
            "YANG_REN_THRESHOLD": 20.0,
            "RESISTANCE_BUFF": 0.2,
            "TENSION_MULTIPLIER": 1.6,
            "PRIORITY_BASE": 0.9,
        },
    )
    facts = ShenshaPlugin.collect_v17_facts(
        {
            "four_pillars": {"month": "甲午", "day": "丙寅", "hour": "丁酉"},
            "ten_gods_absolute": {"正印": 35.0, "劫财": 22.0},
            "ten_gods_runtime": {"正印": 35.0, "劫财": 22.0},
        }
    )

    assert len(facts) >= 2
    tian_yi = next(f for f in facts if f.meta.get("gate") == "TIAN_YI_BUFF")
    yang_ren = next(f for f in facts if f.meta.get("gate") == "YANG_REN_STRESS")
    assert tian_yi.meta["resistance_buff"] == 0.2
    assert yang_ren.meta["tension_multiplier"] == 1.6


def test_shensha_emits_first_batch_branch_deities(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {
            "TIAN_YI_THRESHOLD": 99.0,
            "YANG_REN_THRESHOLD": 99.0,
            "RESISTANCE_BUFF": 0.2,
            "TENSION_MULTIPLIER": 1.6,
            "PRIORITY_BASE": 0.9,
            "BRANCH_SHENSHA_PRIORITY": 0.8,
            "BRANCH_SHENSHA_MATCH_RATIO": 0.66,
            "BRANCH_SHENSHA_MAX_ROWS": 8,
        },
    )
    facts = ShenshaPlugin.collect_v17_facts(
        {
            "four_pillars": {
                "year": "甲寅",
                "month": "乙卯",
                "day": "甲子",
                "hour": "丁巳",
            },
            "ten_gods_absolute": {"比肩": 20.0, "劫财": 18.0, "食神": 12.0, "正印": 8.0},
            "ten_gods_runtime": {"比肩": 20.0, "劫财": 18.0, "食神": 12.0, "正印": 8.0},
        }
    )

    gates = {str(f.meta.get("gate") or "") for f in facts}
    assert "SHENSHA_WENCHANG" in gates
    assert "SHENSHA_LU" in gates
    assert "SHENSHA_YANG_REN_BRANCH" in gates
    assert "SHENSHA_驿马" in gates
    assert "SHENSHA_将星" in gates
    assert all(f.meta.get("observe_only") is True for f in facts)


def test_kong_wang_respects_threshold_and_efficiency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {
            "VOID_THRESHOLD": 0.5,
            "EFFICIENCY": 0.25,
            "PRIORITY": 0.86,
        },
    )
    facts = KongWangPlugin.collect_v17_facts(
        {
            "ten_gods_absolute": {"比肩": 10.0, "劫财": 8.0, "正官": 6.0},
            "ten_gods_runtime": {"比肩": 10.0, "劫财": 8.0, "正官": 6.0},
        }
    )

    assert len(facts) == 1
    fact = facts[0]
    assert fact.priority == 0.86
    assert fact.meta["transmission_efficiency"] == 0.25
