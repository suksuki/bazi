from __future__ import annotations

import pytest

from v17_rebirth.backend.logic.L1_atomic_ops import l1_meta_hydration
from v17_rebirth.backend.logic import plugin_discovery


pytestmark = [pytest.mark.regression, pytest.mark.synthetic]


def _no_flow_class():
    class _NoFlow:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def compute_flow(self, **_kwargs) -> dict:
            return {"ten_god_deltas": {}, "topology": []}

    return _NoFlow


def test_hydration_preserves_extended_sanhe_geometry(monkeypatch) -> None:
    monkeypatch.setattr(plugin_discovery, "iter_all_plugin_specs", lambda: [])
    monkeypatch.setattr(l1_meta_hydration, "FlowPhysicsEngine", _no_flow_class())

    pt = {
        "session_id": "sid",
        "four_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        "luck_pillar": "辛丑",
        "flow_pillar": "乙未",
        "day_master_stem": "乙",
        "ten_gods_base_l0": {"七杀": 20.0, "正官": 6.0, "比肩": 30.0},
        "ten_gods_runtime": {"七杀": 20.0, "正官": 6.0, "比肩": 30.0},
        "energy_meta": {},
        "pending_decisions": [],
        "will_proxy": "stable",
        "_is_current_focus": False,
    }

    l1_meta_hydration.hydrate_v17_physics_tensor(pt)

    san_he = (((pt.get("meta") or {}).get("interaction_v2") or {}).get("san_he") or [])
    assert san_he
    row = san_he[0]
    assert row["matched_branches"].count("巳") == 2
    assert row["matched_branches"].count("丑") == 2
    assert row["duplicate_count"] >= 2
    assert row["mid_branch"] == "酉"
    assert row["pivot_factor"] >= 1.0
    assert row["strength"] > 1.0


def test_hydration_emits_master_reasoning_trace(monkeypatch) -> None:
    monkeypatch.setattr(plugin_discovery, "iter_all_plugin_specs", lambda: [])
    monkeypatch.setattr(l1_meta_hydration, "FlowPhysicsEngine", _no_flow_class())

    pt = {
        "session_id": "sid",
        "four_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        "luck_pillar": "辛丑",
        "flow_pillar": "乙未",
        "day_master_stem": "乙",
        "ten_gods_base_l0": {"七杀": 20.0, "正官": 6.0, "比肩": 30.0},
        "ten_gods_runtime": {"七杀": 20.0, "正官": 6.0, "比肩": 30.0},
        "energy_meta": {},
        "pending_decisions": [],
        "will_proxy": "stable",
        "_is_current_focus": False,
    }

    l1_meta_hydration.hydrate_v17_physics_tensor(pt)

    reasoning = ((pt.get("meta") or {}).get("master_reasoning") or {})
    assert reasoning.get("version") == "v17.master_reasoning.v1"
    assert reasoning.get("day_master") == "乙"
    steps = reasoning.get("reasoning_steps") or []
    stages = {str(step.get("stage")) for step in steps if isinstance(step, dict)}
    assert {"body", "visible_stems", "formation", "runtime", "suppression"} <= stages
    hooks = reasoning.get("learning_hooks") or {}
    assert hooks.get("requires_human_review") is True
