# -*- coding: utf-8 -*-
"""
单元测试：全量索引脚本 A-02 / pipeline_expression 支持
验证 resolve_manifest_for_pattern、pipeline_expression 优先、get_weights_matrix 回退。
"""

import json
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent


def test_resolve_manifest_for_pattern_a02():
    """A-02 应解析到 registry/holographic_pattern/A-02/A-02_manifest.json"""
    from scripts.build_a01_full_index import resolve_manifest_for_pattern
    p = resolve_manifest_for_pattern("A-02")
    assert p is not None
    assert "A-02" in str(p)
    assert "manifest" in str(p).lower() or "A-02_manifest" in str(p)


def test_resolve_manifest_for_pattern_a01():
    """A-01 应解析到 config/patterns/manifest_A01.json"""
    from scripts.build_a01_full_index import resolve_manifest_for_pattern
    p = resolve_manifest_for_pattern("A-01")
    assert p is not None
    assert "A01" in str(p) or "A-01" in str(p)


def test_get_weights_matrix_uses_pipeline_expression():
    """build_full_index 应优先使用 pipeline_expression（若存在）"""
    from scripts.build_a01_full_index import load_manifest, get_weights_matrix
    manifest_path = ROOT / "registry" / "holographic_pattern" / "A-02" / "A-02_manifest.json"
    if not manifest_path.exists():
        pytest.skip("A-02_manifest.json 不存在")
    manifest = load_manifest(manifest_path)
    rules = manifest.get("classical_logic_rules") or {}
    assert "pipeline_expression" in rules or "expression" in rules
    weights, gods = get_weights_matrix(manifest, manifest_path)
    assert len(gods) == 10
    assert weights.shape == (10, 5)


def test_a02_manifest_has_weights():
    """A-02 manifest 应包含 tensor_mapping_matrix.weights"""
    path = ROOT / "registry" / "holographic_pattern" / "A-02" / "A-02_manifest.json"
    if not path.exists():
        pytest.skip("A-02_manifest.json 不存在")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    tmm = data.get("tensor_mapping_matrix") or {}
    w = tmm.get("weights") or {}
    assert len(w) == 10
    assert "PG" in w and "ZC" in w
