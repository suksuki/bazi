"""
V17.32 演化账本 (Evolution Ledger) 功能测试。
"""
from __future__ import annotations

from typing import Any, Dict

import pytest
from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores
from v17_rebirth.backend.logic.L0_physics_fields.evolution_ledger import EvolutionLedger


pytestmark = [pytest.mark.regression, pytest.mark.synthetic]


def test_evolution_ledger_initialization() -> None:
    """验证 L0 累加过程中 ledger 的正确填充。"""
    four_pillars = {"year": "壬子", "month": "癸卯", "day": "庚辰", "hour": "甲申"}
    
    scored, ten_gods, total, energy_meta = calc_deity_scores(
        four_pillars=four_pillars,
        gender="female"
    )
    
    ledger = energy_meta.get("ledger")
    assert isinstance(ledger, EvolutionLedger)
    assert ledger.__bool__()
    
    # 检查是否有阶段标签
    data = ledger.to_dict()
    # 至少应有比肩或食神（女命微调）
    assert "比肩" in data or "食神" in data
    
    for god, entries in data.items():
        assert len(entries) > 0
        # 首条 delta 应不存在或为计算结果
        assert "step" in entries[0]
        assert "val" in entries[0]
        assert "reason" in entries[0]


def test_ledger_to_dict_serialization() -> None:
    """验证 ledger 序列化后的 JSON 结构。"""
    ledger = EvolutionLedger()
    ledger.append_entry("伤官", 50.0, "STEP1", "REASON1")
    ledger.append_entry("伤官", 70.0, "STEP2", "REASON2")
    
    d = ledger.to_dict()
    assert "伤官" in d
    assert len(d["伤官"]) == 2
    assert d["伤官"][0]["val"] == 50.0
    assert d["伤官"][1]["val"] == 70.0
    assert d["伤官"][1]["delta"] == 20.0
    assert d["伤官"][1]["step"] == "STEP2"


def test_flow_settlement_marks_cyan_highlight() -> None:
    ledger = EvolutionLedger()
    ledger.append_entry("食神", 60.0, "L0_BASE", "基线")
    ledger.append_entry("食神", 72.0, "L1.5_FLOW_SETTLEMENT", "五行内生系统平衡流转")

    d = ledger.to_dict()
    assert d["食神"][1]["source"] == "SRC_FLOW"
    assert d["食神"][1]["highlight_type"] == "cyan"
