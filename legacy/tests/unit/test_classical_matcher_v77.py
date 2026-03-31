#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SOP V7.7：古典格局弹性定性单元测试

目的：
- 确认 get_classical_patterns 返回的新字段存在且形状正确：
  - qualitative_match / ephemeral / energy_tier / structural_rescue / tier
- 确认 rank_classical_patterns 能消费上述字段，不抛异常。
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))


def _sample_case():
    """复用 FDS 单测中的示例八字：庚午 壬午 戊午 甲寅。"""
    chart = ["庚午", "壬午", "戊午", "甲寅"]
    day_master = "戊"
    context = {
        "luck_pillar": "庚子",
        "annual_pillar": "甲辰",
        "geo_city": None,
    }
    return chart, day_master, context


def test_get_classical_patterns_returns_qualitative_fields():
    from core.classical_matcher import get_classical_patterns

    chart, day_master, context = _sample_case()
    res = get_classical_patterns(chart, day_master, context)
    assert isinstance(res, dict)
    items = res.get("items") or []
    by_pattern_id = res.get("by_pattern_id") or {}

    # 至少返回一个结构（若 registry 为空，可跳过）
    if not by_pattern_id:
        pytest.skip("classical_registry 未配置 patterns，跳过 V7.7 形状测试")

    # 所有格成项应带有 V7.7 新字段
    for it in items:
        assert "tier" in it
        assert "state" in it
        assert "qualitative_match" in it
        assert "ephemeral" in it
        assert "energy_tier" in it
        assert "structural_rescue" in it
        if it.get("status") == "格成":
            assert it["qualitative_match"] is True
            assert it["energy_tier"] in ("high", "mid", "low")

    # by_pattern_id 中也应镜像 tier 字段
    sample_pid, sample_entry = next(iter(by_pattern_id.items()))
    assert "tier" in sample_entry
    assert "status" in sample_entry


def test_rank_classical_patterns_consumes_structural_rescue():
    """rank_classical_patterns 应能处理 structural_rescue/energy_tier 等字段。"""
    from core.classical_matcher import get_classical_patterns, rank_classical_patterns

    chart, day_master, context = _sample_case()
    res = get_classical_patterns(chart, day_master, context)
    items = res.get("items") or []

    if not items:
        pytest.skip("无格成项，跳过 V7.7 排序测试")

    ranked = rank_classical_patterns(items, context, {"O": 0.6}, day_master)
    assert isinstance(ranked, list)
    if ranked:
        top = ranked[0]
        # V7.2/V7.7：应有 final_score 与 llm_role
        assert "final_score" in top
        assert "llm_role" in top

