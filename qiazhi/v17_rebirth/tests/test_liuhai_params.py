from __future__ import annotations

import pytest

from v17_rebirth.backend.logic.L1_atomic_ops.six_pierce import PLUGIN as SixPiercePlugin
from v17_rebirth.backend.logic.configs.manager import resolve_config_number


def test_resolve_config_number_supports_global_ref(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_constant",
        lambda key, fallback, plugin_id=None: 0.18 if key == "CLASH_LOSS_RATIO" else fallback,
    )
    assert resolve_config_number("ref(global.CLASH_LOSS_RATIO)", 0.12) == 0.18


def test_liuhai_params_control_effective_loss(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.L1_atomic_ops.six_pierce.get_plugin_config",
        lambda _plugin_id: {"PENETRATION_RATIO": 0.5, "CLASH_LOSS_RATIO": 0.2},
    )
    facts = SixPiercePlugin.collect_v17_facts(
        {
            "ten_gods_absolute": {"偏印": 30.0, "正官": 20.0},
            "four_pillars": {"day": "乙丑"},
            "meta": {"interaction_v2": {"liu_hai": [{"pair": ["子", "酉"]}]}},
        }
    )

    assert len(facts) == 1
    fact = facts[0]
    assert fact.plugin_id == "l1.physics.op_branch_liuhai"
    assert fact.meta["penetration_ratio"] == 0.5
    assert fact.meta["clash_loss_ratio"] == 0.2
    assert fact.meta["impact_ratio"] == -0.1
