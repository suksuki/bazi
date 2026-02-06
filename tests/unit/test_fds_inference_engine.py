# -*- coding: utf-8 -*-
"""
单元测试：core.fds_inference_engine
验证 A-01 推理引擎的投影、归位与报告结构。
"""

import json
from pathlib import Path

import numpy as np
import pytest

from core.fds_inference_engine import FDSInferenceEngine, ENGINE_NOTE_FALLBACK


@pytest.fixture
def project_root():
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def engine(project_root):
    """使用项目内真实 A-01 配置（需存在 manifest + registry）。"""
    try:
        return FDSInferenceEngine(
            registry_path=project_root / "registry/holographic_pattern/A-01.json",
            kb_path=project_root / "knowledge/holographic_pattern/A-01_kb.json",
            manifest_path=project_root / "config/patterns/manifest_A01.json",
        )
    except Exception as e:
        pytest.skip(f"FDS inference engine init failed (missing data): {e}")


def test_engine_loads_and_has_matrix_version(engine):
    """引擎应成功加载并具有 matrix_version 属性"""
    assert hasattr(engine, "matrix_version")
    assert engine.matrix_version in ("3.0", "4.0-BETA")


def test_normalize_ten_gods(engine):
    """十神别名应被规范化为标准码"""
    raw = {"ZhengGuan": 2, "BiJian": 1, "ZG": 3}
    out = engine.normalize_ten_gods(raw)
    assert "ZG" in out
    assert out["ZG"] == 3.0  # ZG 覆盖 ZhengGuan
    assert out.get("ZB") == 1.0


def test_project_to_5d(engine):
    """5D 投影应返回长度为 5 的向量"""
    ten_gods = {g: 1.0 for g in engine.ten_god_order}
    point = engine.project_to_5d(ten_gods)
    assert isinstance(point, np.ndarray)
    assert point.shape == (5,)


def test_infer_returns_matrix_version(engine):
    """infer() 返回中应包含 matrix_version"""
    raw = {"ZG": 2, "ZR": 1, "PS": 0}
    result = engine.infer(raw)
    assert "matrix_version" in result
    assert result["matrix_version"] in ("3.0", "4.0-BETA")
    assert result["pattern_id"] == "A-01"
    assert result["best_subpattern"] in ("A-01-S1", "A-01-S2")
    assert "point" in result and "offset" in result
    assert "distances" in result and "similarity_percent" in result


def test_infer_hybrid_and_knowledge(engine):
    """归位结果应包含 is_hybrid 与 knowledge"""
    result = engine.infer({"ZG": 2, "ZR": 1})
    assert "is_hybrid" in result
    assert "knowledge" in result


def test_format_offsets(engine):
    """format_offsets 应返回可读字符串"""
    offset = {"E": 0.1, "O": -0.2, "M": 0.0, "S": 0.3, "R": -0.1}
    s = engine.format_offsets(offset)
    assert "E:" in s and "O:" in s


def test_strict_logic_available_is_bool():
    """strict_logic_available 应返回布尔值"""
    assert isinstance(FDSInferenceEngine.strict_logic_available(), bool)


def test_engine_note_fallback_constant():
    """ENGINE_NOTE_FALLBACK 应为非空字符串"""
    assert isinstance(ENGINE_NOTE_FALLBACK, str)
    assert "基础逻辑" in ENGINE_NOTE_FALLBACK or "判定" in ENGINE_NOTE_FALLBACK
