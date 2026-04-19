import pytest
from typing import Dict, Any

from v17_rebirth.backend.logic.L1_atomic_ops.six_pierce import PLUGIN as SixPiercePlugin
from v17_rebirth.backend.logic.L1_atomic_ops.three_harmony import PLUGIN as ThreeHarmonyPlugin

def test_six_pierce_does_not_crash_on_meta() -> None:
    """验证 six_pierce 的 collect_v17_facts 不会因为传入 scalars 而触发 .get('meta') 崩溃"""
    pt: Dict[str, Any] = {
        "ten_gods_absolute": {"正官": 50.0, "比肩": 40.0},
        "four_pillars": {"day": "乙丑"},
        "meta": {
            "interaction_v2": {
                "liu_po": [
                    {
                        "pair": ["子", "酉"],
                        "pillars": ["year", "hour"],
                    }
                ]
            }
        }
    }
    
    facts = SixPiercePlugin.collect_v17_facts(pt)
    assert len(facts) == 1
    assert "六穿激活" in facts[0].text
    assert facts[0].plugin_id == "l1.physics.op_branch_liuhai"


def test_three_harmony_sanhe_key_mapping() -> None:
    """验证 three_harmony 能正确读取 interaction_v2 中的 san_he"""
    pt: Dict[str, Any] = {
        "ten_gods_absolute": {"七杀": 50.0},
        "four_pillars": {"day": "乙丑"},
        "meta": {
            "interaction_v2": {
                "san_he": [
                    {
                        "group": ["巳", "酉", "丑"],
                        "pillars": ["year", "month", "day"],
                    }
                ]
            }
        }
    }
    
    facts = ThreeHarmonyPlugin.collect_v17_facts(pt)
    assert len(facts) == 1
    assert "三合/半合聚势激活" in facts[0].text
    assert "七杀" in facts[0].text


def test_three_harmony_uses_lock_ratio_and_min_stress(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {
            "FUSION_MID_GAIN": 1.5,
            "LOCK_RATIO": 0.5,
            "MIN_HARMONY_STRESS": 0.6,
        },
    )
    pt: Dict[str, Any] = {
        "ten_gods_absolute": {"七杀": 50.0},
        "four_pillars": {"day": "乙丑"},
        "meta": {
            "interaction_v2": {
                "san_he": [{"group": ["巳", "酉", "丑"], "stress": 0.8}],
                "ban_he": [{"pair": ["巳", "酉"], "stress": 0.55}],
            }
        },
    }

    facts = ThreeHarmonyPlugin.collect_v17_facts(pt)
    assert len(facts) == 1
    meta = facts[0].meta
    assert meta["lock_ratio"] == 0.5
    assert meta["harmony_strength"] == 0.8
    assert meta["impact_ratio"] == 0.4
    assert meta["locked_energy"] == 25.0
