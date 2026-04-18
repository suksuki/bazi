import pytest
from typing import Dict, Any

from v17_rebirth.backend.logic.L1_atomic_ops.six_pierce import PLUGIN as SixPiercePlugin
from v17_rebirth.backend.logic.L1_atomic_ops.three_harmony import PLUGIN as ThreeHarmonyPlugin

def test_six_pierce_does_not_crash_on_meta() -> None:
    """验证 six_pierce 的 collect_v17_facts 不会因为传入 scalars 而触发 .get('meta') 崩溃"""
    pt: Dict[str, Any] = {
        "ten_gods_absolute": {"正官": 50.0, "比肩": 40.0},
        "meta": {
            "clash_stress_map": {
                "events": [
                    {
                        "relation_type": "pierce",
                        "source_key": "liu_po",
                        "branches": ["子", "酉"],
                        "god_i": "偏印",
                        "god_j": "正官"
                    }
                ]
            }
        }
    }
    
    facts = SixPiercePlugin.collect_v17_facts(pt)
    assert len(facts) == 1
    assert "六穿激活" in facts[0].text
    assert facts[0].plugin_id == "six_pierce"


def test_three_harmony_sanhe_key_mapping() -> None:
    """验证 three_harmony 能正确捕捉 sanhe 和 san_he"""
    pt: Dict[str, Any] = {
        "ten_gods_absolute": {"七杀": 50.0},
        "meta": {
            "clash_stress_map": {
                "events": [
                    {
                        "relation_type": "combination",
                        "source_key": "sanhe",  # The frontend spelling
                        "branches": ["巳", "酉", "丑"],
                        "god_j": "七杀"
                    }
                ]
            }
        }
    }
    
    facts = ThreeHarmonyPlugin.collect_v17_facts(pt)
    assert len(facts) == 1
    assert "三合/半合聚势激活" in facts[0].text
    assert "七杀" in facts[0].text
