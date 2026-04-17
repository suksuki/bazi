"""单元：六柱张量完备性与元数据稳定门控。"""
from __future__ import annotations

import asyncio

from v17_rebirth.backend.services.physics_canonical import (
    V17PhysicsMetadata,
    six_pillars_tensor_complete,
)


def test_six_pillars_incomplete_missing_hour() -> None:
    pt = {
        "four_pillars": {"year": "甲子", "month": "甲子", "day": "甲子", "hour": ""},
        "luck_pillar": "乙丑",
        "flow_pillar": "丙寅",
    }
    assert six_pillars_tensor_complete(pt) is False


def test_six_pillars_complete() -> None:
    pt = {
        "four_pillars": {"year": "甲子", "month": "甲子", "day": "甲子", "hour": "甲子"},
        "luck_pillar": "乙丑",
        "flow_pillar": "丙寅",
    }
    assert six_pillars_tensor_complete(pt) is True


def test_v17_physics_metadata_stable_requires_flag() -> None:
    ok_pt = {
        "four_pillars": {"year": "甲子", "month": "甲子", "day": "甲子", "hour": "甲子"},
        "luck_pillar": "乙丑",
        "flow_pillar": "丙寅",
        "meta": {"v17_physics_stable": True},
    }
    assert asyncio.run(V17PhysicsMetadata(ok_pt).is_stable()) is True

    bad = dict(ok_pt)
    bad["meta"] = {"v17_physics_stable": False}
    assert asyncio.run(V17PhysicsMetadata(bad).is_stable()) is False


def test_v17_physics_metadata_missing_meta_unstable() -> None:
    pt = {
        "four_pillars": {"year": "甲子", "month": "甲子", "day": "甲子", "hour": "甲子"},
        "luck_pillar": "乙丑",
        "flow_pillar": "丙寅",
    }
    assert asyncio.run(V17PhysicsMetadata(pt).is_stable()) is False
