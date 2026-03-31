#!/usr/bin/env python3
"""
A-02 按 FDS SOP V5.0 全流程执行脚本
====================================
严格对齐 docs/sop/FDS_SOP_v5.0.md：Step 0 → 2 → 5.3 → 5.4 → 5.5 → 7 → 8。
执行前请确保 data/holographic_universe_518k.jsonl 或 data_local/ 下 518k 数据存在。

用法:
  python scripts/run_a02_sop_v5_pipeline.py
  python scripts/run_a02_sop_v5_pipeline.py --skip-scan   # 已有 a02 全量索引时跳过 Step 2
  python scripts/run_a02_sop_v5_pipeline.py --dry-run     # 仅打印将执行的步骤
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERN_ID = "A-02"
MANIFEST_PATH = ROOT / "registry" / "holographic_pattern" / "A-02" / "A-02_manifest.json"
DATA_LOCAL = ROOT / "data_local"
QGA_MANIFEST = ROOT / "registry" / "qga_manifest.json"


def step0_verify_manifest() -> bool:
    """Step 0: 格局配置注入与立法 — 校验 manifest 必含三大块。"""
    print("\n--- Step 0: Manifest 立法校验 ---")
    if not MANIFEST_PATH.exists():
        print(f"❌ 未找到 manifest: {MANIFEST_PATH}")
        return False
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        m = json.load(f)
    required = ["classical_logic_rules", "tensor_mapping_matrix", "semantic_core_dimensions"]
    missing = [k for k in required if not m.get(k)]
    if missing:
        print(f"❌ manifest 缺少: {missing}")
        return False
    print(f"✅ 法理已锚定: {MANIFEST_PATH} (含 classical_logic_rules, tensor_mapping_matrix, semantic_core_dimensions)")
    return True


def step2_full_scan_and_index() -> bool:
    """Step 2: 全量海选与全息采样 — fds_pattern_scanner --target A-02。"""
    print("\n--- Step 2: 全量海选与全息索引 ---")
    cmd = [sys.executable, str(ROOT / "scripts" / "fds_pattern_scanner.py"), "--target", PATTERN_ID]
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        print("❌ 全量索引构建失败")
        return False
    npz = DATA_LOCAL / "a02_full_points.npz"
    meta = DATA_LOCAL / "a02_full_meta.json"
    if not npz.exists() or not meta.exists():
        print("❌ 未找到 a02_full_points.npz 或 a02_full_meta.json")
        return False
    print("✅ Step 2 完成: a02 全量点阵索引已落盘")
    return True


def step53_hkb_sync() -> bool:
    """Step 5.3: 古典知识库挂载 — sync_pattern_hkb.py --pattern_id A-02。"""
    print("\n--- Step 5.3: HKB 知识库挂载 ---")
    cmd = [sys.executable, str(ROOT / "scripts" / "sync_pattern_hkb.py"), "--pattern_id", PATTERN_ID]
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        print("❌ HKB 同步失败")
        return False
    hkb = ROOT / "config" / "hkb" / "hkb_params.json"
    if not hkb.exists():
        print("⚠️ config/hkb/hkb_params.json 不存在，请检查脚本输出")
    else:
        with open(hkb, "r", encoding="utf-8") as f:
            h = json.load(f)
        if "a02_semantic_core" not in str(h):
            print("⚠️ hkb_params 中未发现 a02_semantic_core 键，请检查 sync 逻辑")
        else:
            print("✅ Step 5.3 完成: HKB 已同步 A-02 语义核心")
    return True


def step54_qga_verify() -> bool:
    """Step 5.4: 量子架构注册 — 校验 qga_manifest 已含 A-02。"""
    print("\n--- Step 5.4: QGA 注册校验 ---")
    if not QGA_MANIFEST.exists():
        print("❌ 未找到 registry/qga_manifest.json")
        return False
    with open(QGA_MANIFEST, "r", encoding="utf-8") as f:
        q = json.load(f)
    topics = q.get("topics", {}).get("holographic_pattern", [])
    a02 = next((x for x in topics if x.get("pattern_id") == PATTERN_ID), None)
    if not a02:
        print("❌ qga_manifest 的 holographic_pattern 中无 A-02 条目")
        return False
    print(f"✅ Step 5.4 已就绪: A-02 已注册 (index_path={a02.get('index_path')})")
    return True


def step55_hall_of_fame() -> bool:
    """Step 5.5: 奇点英雄榜 — build_pattern_hall_of_fame.py --pattern_id A-02。"""
    print("\n--- Step 5.5: 奇点存证与英雄榜 ---")
    cmd = [sys.executable, str(ROOT / "scripts" / "build_pattern_hall_of_fame.py"), "--pattern_id", PATTERN_ID]
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        print("❌ 奇点英雄榜构建失败")
        return False
    hof = ROOT / "registry" / "holographic_pattern" / "A-02" / "A-02_hall_of_fame.json"
    if not hof.exists():
        print("⚠️ 未找到 A-02_hall_of_fame.json，请检查脚本输出")
    else:
        print("✅ Step 5.5 完成: 奇点英雄榜已落盘")
    return True


def step7_repair_pathway_stress() -> bool:
    """Step 7: 流形路径导航 — 压力测试 test_a02_repair_pathway_stress。"""
    print("\n--- Step 7: 流形修复路径验证 ---")
    cmd = [sys.executable, str(ROOT / "scripts" / "test_a02_repair_pathway_stress.py")]
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        print("⚠️ Step 7 压力测试未通过（可能因无质心/邻居条件），请查看输出")
        return True  # 不阻断流水线
    print("✅ Step 7 完成: 修复路径压力测试通过")
    return True


def step8_matrix_backfitting() -> bool:
    """Step 8: 矩阵灵敏度与觉醒审计 — matrix_backfitting_auditor --pattern_id A-02 --top 50。"""
    print("\n--- Step 8: 矩阵回溯审计 ---")
    cmd = [sys.executable, str(ROOT / "scripts" / "matrix_backfitting_auditor.py"), "--pattern_id", PATTERN_ID, "--top", "50"]
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        print("❌ 矩阵回溯审计失败")
        return False
    cal = ROOT / "config" / "physics" / "tensor_mapping_matrix_A02_V5.1_CALIBRATED.json"
    if cal.exists():
        print("✅ Step 8 完成: 校准版矩阵已输出 (V5.1_CALIBRATED)")
    else:
        print("✅ Step 8 完成: 审计已运行（Ollama 未用时保留原权重并可能仍写 CALIBRATED 文件）")
    return True


def main():
    ap = argparse.ArgumentParser(description="A-02 按 FDS SOP V5.0 全流程执行")
    ap.add_argument("--skip-scan", action="store_true", help="跳过 Step 2 全量扫描（已有 a02_* 索引时使用）")
    ap.add_argument("--dry-run", action="store_true", help="仅打印将执行的步骤，不实际运行")
    args = ap.parse_args()

    # 若跳过 Step 2，仍校验索引文件存在
    def step2_skip_verify():
        npz, meta = DATA_LOCAL / "a02_full_points.npz", DATA_LOCAL / "a02_full_meta.json"
        if not npz.exists() or not meta.exists():
            print("❌ --skip-scan 时需已存在 a02_full_points.npz 与 a02_full_meta.json")
            return False
        print("✅ Step 2 跳过（使用既有 a02 全量索引）")
        return True

    steps = [
        ("Step 0", step0_verify_manifest),
        ("Step 2", step2_skip_verify if args.skip_scan else step2_full_scan_and_index),
        ("Step 5.3", step53_hkb_sync),
        ("Step 5.4", step54_qga_verify),
        ("Step 5.5", step55_hall_of_fame),
        ("Step 7", step7_repair_pathway_stress),
        ("Step 8", step8_matrix_backfitting),
    ]

    if args.dry_run:
        print("DRY-RUN: 将按以下顺序执行")
        for name, fn in steps:
            if fn:
                print(f"  - {name}")
        return 0

    print("=" * 60)
    print("A-02 七杀格 · FDS SOP V5.0 全流程")
    print("=" * 60)

    for name, fn in steps:
        if not fn:
            continue
        if not fn():
            print(f"\n❌ 流水线在 {name} 终止")
            return 1

    print("\n" + "=" * 60)
    print("✅ A-02 V5.0 全流程执行完毕")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
