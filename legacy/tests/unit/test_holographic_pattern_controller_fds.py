# -*- coding: utf-8 -*-
"""
单元测试：HolographicPatternController FDS SOP V4.0 能力
覆盖 get_fds_sop_patterns、get_fds_pattern_detail、_chart_to_ten_gods、_calculate_fds_projection。
"""

from pathlib import Path

import pytest

# 项目根
ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def controller():
    from controllers.holographic_pattern_controller import HolographicPatternController
    return HolographicPatternController()


def test_get_fds_sop_patterns_returns_list(controller):
    """get_fds_sop_patterns 应返回列表，项含 pattern_id/name_cn/version/status"""
    out = controller.get_fds_sop_patterns()
    assert isinstance(out, list)
    for p in out:
        assert "pattern_id" in p and "name_cn" in p and "version" in p and "status" in p
        assert p["status"] in ("已审计", "在审计中")


def test_get_fds_sop_patterns_a01_audited(controller):
    """A-01 状态应为已审计"""
    out = controller.get_fds_sop_patterns()
    a01 = next((x for x in out if x["pattern_id"] == "A-01"), None)
    if a01:
        assert a01["status"] == "已审计"


def test_get_fds_sop_patterns_a02_in_audit(controller):
    """A-02 状态应为在审计中"""
    out = controller.get_fds_sop_patterns()
    a02 = next((x for x in out if x["pattern_id"] == "A-02"), None)
    if a02:
        assert a02["status"] == "在审计中"


def test_get_fds_pattern_detail_a01(controller):
    """get_fds_pattern_detail(A-01) 应返回 meta_info/classical_logic_rules/sub_pattern_definitions"""
    detail = controller.get_fds_pattern_detail("A-01")
    if detail is None:
        pytest.skip("A-01 manifest/registry 不可用")
    assert "meta_info" in detail
    assert "classical_logic_rules" in detail
    assert "sub_pattern_definitions" in detail
    assert detail.get("pattern_id") == "A-01"


def test_get_fds_pattern_detail_a02(controller):
    """get_fds_pattern_detail(A-02) 应返回含 semantic_core_dimensions、strong_correlation 的详情"""
    detail = controller.get_fds_pattern_detail("A-02")
    if detail is None:
        pytest.skip("A-02 manifest 不可用")
    assert detail.get("pattern_id") == "A-02"
    assert "meta_info" in detail
    assert "strong_correlation" in detail
    assert "semantic_core_dimensions" in detail


def test_chart_to_ten_gods_shape(controller):
    """_chart_to_ten_gods 应返回 ZG/PG/... 等 10 个码的字典"""
    chart = ["庚午", "壬午", "戊午", "甲寅"]
    day_master = "戊"
    out = controller._chart_to_ten_gods(chart, day_master)
    assert isinstance(out, dict)
    codes = ["ZG", "PG", "ZR", "PR", "ZS", "PS", "ZC", "PC", "ZB", "PB"]
    for c in codes:
        assert c in out
        assert isinstance(out[c], (int, float))


def test_calculate_fds_projection_a01_returns_structure(controller):
    """_calculate_fds_projection(A-01) 应返回 projection/sai/recognition/sub_id"""
    chart = ["庚午", "壬午", "戊午", "甲寅"]
    day_master = "戊"
    result = controller._calculate_fds_projection("A-01", chart, day_master, None)
    if result is None:
        pytest.skip("A-01 TMM/推理不可用")
    assert "projection" in result
    assert "sai" in result
    assert "recognition" in result
    assert result["projection"].keys() >= {"E", "O", "M", "S", "R"}


def test_calculate_tensor_projection_a01_no_error(controller):
    """calculate_tensor_projection(A-01) 不应返回 error 键（或 error 非格局不存在）"""
    chart = ["庚午", "壬午", "戊午", "甲寅"]
    day_master = "戊"
    result = controller.calculate_tensor_projection("A-01", chart, day_master, None)
    assert "error" not in result or "不存在" not in str(result.get("error", ""))
    if "error" not in result:
        assert "projection" in result and "sai" in result
