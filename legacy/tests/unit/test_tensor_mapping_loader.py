# -*- coding: utf-8 -*-
"""
单元测试：core.tensor_mapping_loader
验证 V4.0 优先加载与回退逻辑。
"""

import json
import tempfile
from pathlib import Path

import pytest

# 确保项目根在 path 中（conftest 已做）
from core.tensor_mapping_loader import (
    load_tensor_mapping_matrix,
    get_matrix_version_used,
)


@pytest.fixture
def sample_manifest():
    """与 manifest_A01 同构的 TMM 片段"""
    return {
        "tensor_mapping_matrix": {
            "ten_gods": ["ZG", "PG", "ZR", "PR", "ZS", "PS", "ZC", "PC", "ZB", "PB"],
            "dimensions": ["E", "O", "M", "S", "R"],
            "weights": {
                "ZG": [-0.1, 0.9, 0.3, -0.5, 0.8],
                "PG": [-0.5, 0.4, -0.2, 0.9, -0.3],
                "ZR": [-0.2, 0.4, 0.9, 0.1, 0.3],
                "PR": [-0.3, 0.2, 0.9, 0.3, 0.4],
                "ZS": [-0.1, 0.3, 0.5, -0.2, 0.2],
                "PS": [-0.2, -0.8, 0.4, 0.9, -0.5],
                "ZC": [0.9, 0.2, -0.2, -0.6, 0.3],
                "PC": [0.4, -0.5, -0.3, 0.6, -0.4],
                "ZB": [0.7, -0.1, -0.2, 0.1, 0.6],
                "PB": [0.8, -0.3, -0.5, 0.4, 0.5],
            },
        }
    }


def test_load_from_manifest_when_no_v4(sample_manifest):
    """无 V4 文件时，应从 manifest 加载并返回版本 3.0"""
    with tempfile.TemporaryDirectory() as tmp:
        v4_path = Path(tmp) / "tensor_mapping_matrix_V4.0_BETA.json"
        assert not v4_path.exists()
        tmm, version = load_tensor_mapping_matrix(sample_manifest, v4_path=v4_path)
    assert version == "3.0"
    assert tmm["ten_gods"] == sample_manifest["tensor_mapping_matrix"]["ten_gods"]
    assert "ZG" in tmm["weights"]
    assert len(tmm["weights"]["ZG"]) == 5


def test_load_from_v4_when_exists(sample_manifest):
    """存在有效 V4 文件时，应加载 V4 并返回 4.0-BETA"""
    with tempfile.TemporaryDirectory() as tmp:
        v4_path = Path(tmp) / "tensor_mapping_matrix_V4.0_BETA.json"
        v4_data = {
            "version": "4.0-BETA",
            "ten_gods": ["ZG", "PG", "ZR", "PR", "ZS", "PS", "ZC", "PC", "ZB", "PB"],
            "dimensions": ["E", "O", "M", "S", "R"],
            "weights": {g: [0.1] * 5 for g in ["ZG", "PG", "ZR", "PR", "ZS", "PS", "ZC", "PC", "ZB", "PB"]},
        }
        with open(v4_path, "w", encoding="utf-8") as f:
            json.dump(v4_data, f)
        tmm, version = load_tensor_mapping_matrix(sample_manifest, v4_path=v4_path)
    assert version == "4.0-BETA"
    assert tmm["weights"]["ZG"] == [0.1] * 5


def test_get_matrix_version_used(sample_manifest):
    """get_matrix_version_used 应返回 3.0 或 4.0-BETA"""
    with tempfile.TemporaryDirectory() as tmp:
        v4_path = Path(tmp) / "nonexistent.json"
        ver = get_matrix_version_used(sample_manifest, v4_path=v4_path)
    assert ver == "3.0"


def test_fallback_when_v4_invalid(sample_manifest):
    """V4 文件存在但内容无效时，应回退到 manifest"""
    with tempfile.TemporaryDirectory() as tmp:
        v4_path = Path(tmp) / "tensor_mapping_matrix_V4.0_BETA.json"
        with open(v4_path, "w", encoding="utf-8") as f:
            json.dump({"version": "4.0-BETA"}, f)  # 缺少 weights/ten_gods
        tmm, version = load_tensor_mapping_matrix(sample_manifest, v4_path=v4_path)
    assert version == "3.0"
    assert tmm["ten_gods"] == sample_manifest["tensor_mapping_matrix"]["ten_gods"]
