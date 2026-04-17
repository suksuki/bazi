"""地支交互条件模块（三合旺支门控等）。"""
from __future__ import annotations

from app.plugins.base_physics.core_operators.op_sub_branch_interaction import is_sanhe_triggered
from app.plugins.base_physics.core_operators.sub_branch_condition_eval import (
    SANHE_GROUP_TO_ZHONGSHEN,
    sanhe_trine_allowed_by_wang_zhi_switch,
)


def test_sanhe_zhong_shen_map_covers_four_groups() -> None:
    assert len(SANHE_GROUP_TO_ZHONGSHEN) == 4
    metal = frozenset({"巳", "酉", "丑"})
    assert SANHE_GROUP_TO_ZHONGSHEN[metal] == "酉"


def test_wang_zhi_switch_off_always_allows() -> None:
    g = frozenset({"巳", "酉", "丑"})
    branches = {"year": "酉", "month": "巳", "day": "丑", "hour": "寅"}
    assert sanhe_trine_allowed_by_wang_zhi_switch(g, branches, {"SUB_BRANCH_SANHE_REQ_WANG_ZHI": 0.0}) is True


def test_wang_zhi_switch_on_requires_zhong_on_month_or_day() -> None:
    g = frozenset({"巳", "酉", "丑"})
    branches_bad = {"year": "酉", "month": "巳", "day": "丑", "hour": "寅"}
    assert sanhe_trine_allowed_by_wang_zhi_switch(g, branches_bad, {"SUB_BRANCH_SANHE_REQ_WANG_ZHI": 1.0}) is False
    branches_ok = {"year": "巳", "month": "酉", "day": "丑", "hour": "寅"}
    assert sanhe_trine_allowed_by_wang_zhi_switch(g, branches_ok, {"SUB_BRANCH_SANHE_REQ_WANG_ZHI": 1.0}) is True


def test_wang_zhi_temporal_bridge_accepts_liunian_zhong_shen() -> None:
    """中神在流年支时，在 SANHE_TEMPORAL_WANG_ZHI_BRIDGE 开启下满足旺支门控。"""
    g = frozenset({"巳", "酉", "丑"})
    branches = {"year": "巳", "month": "寅", "day": "丑", "hour": "子", "liunian": "酉"}
    settings = {
        "SUB_BRANCH_SANHE_REQ_WANG_ZHI": 1.0,
        "SANHE_TEMPORAL_WANG_ZHI_BRIDGE": 1.0,
    }
    assert sanhe_trine_allowed_by_wang_zhi_switch(g, branches, settings) is True


def test_is_sanhe_triggered_requires_three_branches_and_wang_zhi() -> None:
    g = frozenset({"巳", "酉", "丑"})
    incomplete = {"year": "巳", "month": "酉", "day": "寅", "hour": "子"}
    assert is_sanhe_triggered(g, incomplete, {"SUB_BRANCH_SANHE_REQ_WANG_ZHI": 0.0}) is False
    branches_bad = {"year": "酉", "month": "巳", "day": "丑", "hour": "寅"}
    assert is_sanhe_triggered(g, branches_bad, {"SUB_BRANCH_SANHE_REQ_WANG_ZHI": 1.0}) is False
    branches_ok = {"year": "巳", "month": "酉", "day": "丑", "hour": "寅"}
    assert is_sanhe_triggered(g, branches_ok, {"SUB_BRANCH_SANHE_REQ_WANG_ZHI": 1.0}) is True
