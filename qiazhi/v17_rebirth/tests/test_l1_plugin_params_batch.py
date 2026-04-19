from __future__ import annotations

import pytest

from v17_rebirth.backend.logic.L1_atomic_ops.muku_gate import PLUGIN as MukuPlugin
from v17_rebirth.backend.logic.L1_atomic_ops.six_break import PLUGIN as SixBreakPlugin
from v17_rebirth.backend.logic.L1_atomic_ops.six_harmony import PLUGIN as SixHarmonyPlugin


def test_muku_open_gate_boost_controls_open_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {"STORAGE_EFFICIENCY": 0.2, "OPEN_GATE_BOOST": 1.6},
    )
    facts = MukuPlugin.collect_v17_facts(
        {
            "four_pillars": {"year": "辰", "day": "乙丑"},
            "meta": {"interaction_v2": {"liu_chong": [{"pair": ["辰", "戌"]}]}},
        }
    )

    assert len(facts) == 1
    meta = facts[0].meta
    assert meta["muku_state"] == "OPEN"
    assert meta["impact_ratio"] > 0
    assert meta["condition_multiplier"] > 0
    assert meta["open_gate_boost"] == 1.6


def test_liuhe_stability_weight_controls_locked_energy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {"HARMONY_GAIN": 1.2, "STABILITY_WEIGHT": 0.5},
    )
    facts = SixHarmonyPlugin.collect_v17_facts(
        {
            "ten_gods_absolute": {"正财": 20.0, "正官": 12.0},
            "four_pillars": {"day": "壬戌"},
            "meta": {"interaction_v2": {"liu_he": [{"pair": ["午", "未"]}]}},
        }
    )

    assert len(facts) == 1
    meta = facts[0].meta
    assert meta["stability_weight"] == 0.5
    assert meta["locked_energy"] == 6.0
    assert meta["impact_ratio"] == 0.1


def test_liupo_friction_coeff_controls_effective_loss(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {"BREAK_LOSS": 0.1, "FRICTION_COEFF": 0.5},
    )
    facts = SixBreakPlugin.collect_v17_facts(
        {
            "four_pillars": {"day": "壬戌"},
            "meta": {"interaction_v2": {"liu_po": [{"pair": ["子", "午"]}]}},
        }
    )

    assert len(facts) == 1
    meta = facts[0].meta
    assert meta["friction_coeff"] == 0.5
    assert meta["break_loss"] == 0.1
    assert meta["impact_ratio"] == -0.15
