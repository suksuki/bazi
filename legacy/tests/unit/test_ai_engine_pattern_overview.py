# -*- coding: utf-8 -*-
"""
单元测试：core.ai_engine 格局解读与 A-02 语义 Prompt
覆盖 generate_pattern_overview、_get_system_prompt_for_pattern（A-01/A-02 分支）。
"""

import pytest

from core.ai_engine import (
    _get_system_prompt_for_pattern,
    _get_system_prompt_for_a02_semantic,
    generate_pattern_overview,
    is_ai_engine_available,
)


def test_get_system_prompt_for_pattern_a01():
    """pattern_id A-01 或 None 应返回 A-01 语义 Prompt"""
    s = _get_system_prompt_for_pattern("A-01")
    assert isinstance(s, str)
    assert "5D" in s or "流形" in s
    s2 = _get_system_prompt_for_pattern(None)
    assert isinstance(s2, str)


def test_get_system_prompt_for_pattern_a02():
    """pattern_id A-02 应返回含 A-02 七杀格语义的 Prompt"""
    s = _get_system_prompt_for_pattern("A-02")
    assert isinstance(s, str)
    # A-02 语义核心若已注入，应包含七杀或应力等关键词
    assert "A-02" in s or "七杀" in s or "应力" in s or "流形" in s


def test_get_system_prompt_a02_semantic_returns_str():
    """_get_system_prompt_for_a02_semantic 应返回非空字符串"""
    s = _get_system_prompt_for_a02_semantic()
    assert isinstance(s, str)
    assert len(s) > 0


def test_generate_pattern_overview_structure():
    """generate_pattern_overview 应返回 success/text/model/error 结构（subs 为列表格式）"""
    detail = {
        "pattern_id": "A-02",
        "meta_info": {"chinese_name": "七杀格", "display_name": "Seven Kill"},
        "classical_logic_rules": {"description": "七杀强旺"},
        "sub_pattern_definitions": [{"id": "A-02-S1", "name": "七杀无制"}],
        "semantic_core_dimensions": {},
        "strong_correlation": [],
    }
    out = generate_pattern_overview("A-02", detail)
    assert "success" in out
    assert "text" in out
    assert "model" in out
    assert "error" in out
    # 不强制 success=True（可能无 Ollama）
    assert isinstance(out["success"], bool)


def test_is_ai_engine_available_bool():
    """is_ai_engine_available 应返回布尔"""
    assert isinstance(is_ai_engine_available(), bool)
