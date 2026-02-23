# -*- coding: utf-8 -*-
"""
FDS SOP V4.0 回归测试
=====================
覆盖：A-02 manifest、pipeline_expression、全息控制器 FDS 分支、calculate_tensor_projection(A-01/A-02)。
可与 pytest 或独立 run_all_tests() 运行。
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_all_tests():
    failed = []
    # 1. A-02 manifest 存在且含 pipeline_expression
    a02_manifest = ROOT / "registry" / "holographic_pattern" / "A-02" / "A-02_manifest.json"
    if a02_manifest.exists():
        with open(a02_manifest, "r", encoding="utf-8") as f:
            data = json.load(f)
        rules = data.get("classical_logic_rules") or {}
        if not (rules.get("pipeline_expression") or rules.get("expression")):
            failed.append("A-02 manifest 缺少 classical_logic_rules.expression 或 pipeline_expression")
        if not data.get("semantic_core_dimensions"):
            failed.append("A-02 manifest 缺少 semantic_core_dimensions")
    else:
        failed.append("A-02_manifest.json 不存在")

    # 2. 全息控制器 FDS 格局列表与详情
    try:
        from controllers.holographic_pattern_controller import HolographicPatternController
        ctrl = HolographicPatternController()
        patterns = ctrl.get_fds_sop_patterns()
        if not patterns:
            failed.append("get_fds_sop_patterns 返回空列表")
        a01_detail = ctrl.get_fds_pattern_detail("A-01")
        if not a01_detail and any(p.get("pattern_id") == "A-01" for p in patterns):
            failed.append("get_fds_pattern_detail('A-01') 返回 None 但列表中有 A-01")
        # A-02 详情（若存在 manifest）
        if a02_manifest.exists():
            a02_detail = ctrl.get_fds_pattern_detail("A-02")
            if not a02_detail:
                failed.append("get_fds_pattern_detail('A-02') 返回 None")
            elif "strong_correlation" not in a02_detail:
                failed.append("A-02 detail 缺少 strong_correlation")
    except Exception as e:
        failed.append(f"全息控制器 FDS 调用异常: {e}")

    # 3. calculate_tensor_projection(A-01) 不报「格局不存在」
    try:
        from controllers.holographic_pattern_controller import HolographicPatternController
        ctrl = HolographicPatternController()
        chart = ["庚午", "壬午", "戊午", "甲寅"]
        result = ctrl.calculate_tensor_projection("A-01", chart, "戊", None)
        if result.get("error") and "不存在" in str(result.get("error", "")):
            failed.append("calculate_tensor_projection('A-01') 仍报格局不存在")
        if "projection" not in result and "error" not in result:
            failed.append("calculate_tensor_projection('A-01') 既无 projection 也无 error")
    except Exception as e:
        failed.append(f"calculate_tensor_projection 异常: {e}")

    # 4. build_a01_full_index pipeline_expression 优先
    try:
        from scripts.build_a01_full_index import load_manifest, resolve_manifest_for_pattern
        p = resolve_manifest_for_pattern("A-02")
        if p.exists():
            m = load_manifest(p)
            rules = m.get("classical_logic_rules") or {}
            expr = rules.get("pipeline_expression") or rules.get("expression")
            if not expr:
                failed.append("build_a01_full_index 用 A-02 时无 expression/pipeline_expression")
    except Exception as e:
        failed.append(f"build_a01_full_index A-02 解析异常: {e}")

    if failed:
        print("FDS SOP V4.0 回归测试失败:")
        for msg in failed:
            print("  -", msg)
        return 1
    print("FDS SOP V4.0 回归测试全部通过")
    return 0


def test_fds_sop_v4_regression():
    """Pytest 可收集的入口：运行全部 V4 回归项。"""
    assert run_all_tests() == 0


if __name__ == "__main__":
    sys.exit(run_all_tests())
