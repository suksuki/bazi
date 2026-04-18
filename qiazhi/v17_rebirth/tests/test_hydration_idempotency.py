from __future__ import annotations

from v17_rebirth.backend.plugins.spec import ArbiterType, V17Fact
from v17_rebirth.backend.logic.L1_atomic_ops import l1_meta_hydration
from v17_rebirth.backend.logic import plugin_discovery


def test_hydration_preserves_existing_tensor_and_does_not_replay_applied_decision(monkeypatch) -> None:
    monkeypatch.setattr(plugin_discovery, "iter_all_plugin_specs", lambda: [])

    class _NoFlow:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def compute_flow(self, **_kwargs) -> dict:
            return {"ten_god_deltas": {}, "topology": []}

    monkeypatch.setattr(l1_meta_hydration, "FlowPhysicsEngine", _NoFlow)

    pt = {
        "session_id": "sid",
        "four_pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
        "luck_pillar": "戊辰",
        "flow_pillar": "己巳",
        "day_master_stem": "丙",
        "ten_gods_base_l0": {"七杀": 8.0},
        "ten_gods_runtime": {"七杀": 10.0},
        "ten_gods_absolute": {"七杀": 10.0},
        "deity_scores": {"七杀": 10.0},
        "ten_gods_absolute_intensity": {"七杀": 10.0},
        "energy_meta": {},
        "pending_decisions": [
            {
                "id": "d1",
                "label": "测试动作",
                "title": "测试动作",
                "target_god": "七杀",
                "applied": True,
                "physical_impact": {"impact_ratio": 0.5, "significance_weight": 1.0},
            }
        ],
        "will_proxy": "neutral",
        "_is_current_focus": False,
    }

    l1_meta_hydration.hydrate_v17_physics_tensor(pt)

    assert pt["ten_gods_absolute"]["七杀"] == 10.0
    assert pt["ten_gods_base_l0"]["七杀"] == 8.0
    assert pt["ten_gods_runtime"]["七杀"] == 10.0
    assert pt["pending_decisions"][0]["impact_committed"] is True


def test_hydration_does_not_reapply_same_plugin_proposal_on_second_pass(monkeypatch) -> None:
    class _AutoSpec:
        plugin_id = "l0.physics.auto_boost"
        causal_tier = 0

        def collect_v17_facts(self, _physics_tensor: dict) -> list:
            return [
                V17Fact(
                    plugin_id=self.plugin_id,
                    text="底层自动校正：七杀 能级提升 20%。",
                    causal_tier=0,
                    priority=0.9,
                    suggested_arbiter=ArbiterType.SYSTEM,
                    target_god="七杀",
                    meta={"impact_ratio": 0.2, "target_god": "七杀", "significance_weight": 1.0},
                )
            ]

    monkeypatch.setattr(plugin_discovery, "iter_all_plugin_specs", lambda: [_AutoSpec()])

    class _NoFlow:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def compute_flow(self, **_kwargs) -> dict:
            return {"ten_god_deltas": {}, "topology": []}

    monkeypatch.setattr(l1_meta_hydration, "FlowPhysicsEngine", _NoFlow)

    pt = {
        "session_id": "sid",
        "four_pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
        "luck_pillar": "戊辰",
        "flow_pillar": "己巳",
        "day_master_stem": "丙",
        "ten_gods_base_l0": {"七杀": 10.0},
        "ten_gods_runtime": {"七杀": 10.0},
        "energy_meta": {},
        "pending_decisions": [],
        "will_proxy": "neutral",
        "_is_current_focus": False,
    }

    l1_meta_hydration.hydrate_v17_physics_tensor(pt)
    first_runtime = pt["ten_gods_runtime"]["七杀"]
    l1_meta_hydration.hydrate_v17_physics_tensor(pt)

    assert first_runtime == 12.0
    assert pt["ten_gods_runtime"]["七杀"] == 12.0


def test_hydration_will_proxy_no_longer_mutates_runtime(monkeypatch) -> None:
    monkeypatch.setattr(plugin_discovery, "iter_all_plugin_specs", lambda: [])

    class _NoFlow:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def compute_flow(self, **_kwargs) -> dict:
            return {"ten_god_deltas": {}, "topology": []}

    monkeypatch.setattr(l1_meta_hydration, "FlowPhysicsEngine", _NoFlow)

    pt = {
        "session_id": "sid",
        "four_pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
        "luck_pillar": "戊辰",
        "flow_pillar": "己巳",
        "day_master_stem": "丙",
        "ten_gods_base_l0": {"正官": 10.0, "食神": 6.0},
        "ten_gods_runtime": {"正官": 10.0, "食神": 6.0},
        "energy_meta": {},
        "pending_decisions": [],
        "will_proxy": "stable",
        "_is_current_focus": False,
    }

    l1_meta_hydration.hydrate_v17_physics_tensor(pt)

    assert pt["ten_gods_runtime"]["正官"] == 10.0
    assert pt["ten_gods_runtime"]["食神"] == 6.0
