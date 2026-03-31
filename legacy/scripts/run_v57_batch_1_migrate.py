#!/usr/bin/env python3
"""
FDS SOP V5.7：Phase 3 质心校准与迁库
======================================
在 Phase 1+2 通过后执行：提取 L1 匹配样本的 5D 张量，写入 DuckDB pattern_points（替换 TMM_SEED）。
使用 V4.0-BETA 矩阵将 ten_gods 投影为 5D；若缺 V4 则跳过迁库并提示。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np


def _load_v4_tmm():
    """加载 V4 矩阵用于 ten_gods → 5D。"""
    v4 = ROOT / "config" / "physics" / "tensor_mapping_matrix_V4.0_BETA.json"
    if not v4.exists():
        return None, None
    with open(v4, "r", encoding="utf-8") as f:
        data = json.load(f)
    gods = data.get("ten_gods") or []
    weights = data.get("weights") or {}
    if not gods or not weights:
        return None, None
    matrix = np.array([weights.get(g, [0] * 5) for g in gods], dtype=np.float64)
    return matrix, gods


def _case_to_5d(case: dict, weights: np.ndarray, god_index: dict) -> np.ndarray:
    vec = np.zeros(10)
    for g, idx in god_index.items():
        val = (case.get("ten_gods") or {}).get(g, 0)
        if isinstance(val, (int, float)):
            vec[idx] = float(val)
        elif isinstance(val, dict):
            vec[idx] = float(val.get("mean", val.get("strength", 0)))
    return np.dot(weights.T, vec)


def main():
    import argparse
    p = argparse.ArgumentParser(description="V5.7 Phase 3: 质心校准与迁库")
    p.add_argument("--data", type=Path, default=None)
    p.add_argument("--abundance", type=Path, default=None, help="Phase 1 丰度报告，默认 audit_logs/v57_batch_1_abundance.json")
    p.add_argument("--limit", type=int, default=None, help="每格局最多迁入条数（测试用）")
    args = p.parse_args()

    weights, gods = _load_v4_tmm()
    if weights is None or gods is None:
        print("⚠️ 未找到 V4.0-BETA 矩阵，无法计算 5D。请配置 config/physics/tensor_mapping_matrix_V4.0_BETA.json 后重试。")
        sys.exit(1)
    god_index = {g: i for i, g in enumerate(gods)}

    abundance_path = args.abundance or (ROOT / "audit_logs" / "v57_batch_1_abundance.json")
    if not abundance_path.exists():
        print(f"❌ 未找到丰度报告: {abundance_path}，请先运行 run_v57_batch_1_scan.py")
        sys.exit(1)
    with open(abundance_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    data_path = args.data or Path(report.get("data_path", ""))
    if not data_path or not data_path.exists():
        data_path = ROOT / "data" / "holographic_universe_518k.jsonl"
        if not data_path.exists():
            data_path = ROOT / "data_local" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        print("❌ 未找到 518k 数据")
        sys.exit(1)

    from pattern_scanner_v57 import l1_match_a14_through_a20, _bazi_to_pillars

    # A-16 化水格能量纯度：地支见辰戌丑未（强土）则污染，不进入质心计算
    STRONG_EARTH_ZHI = {"辰", "戌", "丑", "未"}

    pattern_ids = [f"A-{i:02d}" for i in range(14, 21)]
    by_pattern: dict = {pid: {"refs": [], "line_indices": [], "points": []} for pid in pattern_ids}

    total = 0
    with open(data_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            total += 1
            try:
                case = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not case.get("bazi") or not case.get("ten_gods"):
                continue
            matched = l1_match_a14_through_a20(case)
            _, branches, _, _, _, _ = _bazi_to_pillars(case)
            ref = case.get("uid") or case.get("id") or case.get("case_id") or f"line_{i}"
            try:
                pt = _case_to_5d(case, weights, god_index)
            except Exception:
                continue
            for pid in matched:
                if pid not in by_pattern:
                    continue
                if pid == "A-16" and branches:
                    if STRONG_EARTH_ZHI & set(branches):
                        continue  # 化水格见强土则排除
                bag = by_pattern[pid]
                if args.limit and len(bag["refs"]) >= args.limit:
                    continue
                bag["refs"].append(str(ref))
                bag["line_indices"].append(i)
                bag["points"].append(pt)
            if total % 100000 == 0 and total > 0:
                print(f"   已扫描 {total:,} 行…")

    from core.database import PHYSICS_DB
    from core.database.fds_physics import FDSPhysics

    physics = FDSPhysics(PHYSICS_DB)
    for pid in pattern_ids:
        bag = by_pattern[pid]
        if not bag["refs"]:
            print(f"  {pid} 无匹配点，跳过")
            continue
        refs = bag["refs"]
        line_indices = bag["line_indices"]
        points = np.array(bag["points"], dtype=np.float64)
        physics.insert_points(pid, refs, line_indices, points, replace=True, commit=True)
        print(f"  ✅ {pid} 迁入 {len(refs):,} 点")
    physics.close()
    print("Phase 3 迁库完成。")
    sys.exit(0)


if __name__ == "__main__":
    main()
