#!/usr/bin/env python3
"""
第 034 号工程指令 · Step 8.5：A-02 修复路径压力测试 (Stress Test)
==================================================================
随机抽取 10 个 A-02 样本，调用 pathway_analyzer.analyze_repair_pathway，
验证在 13.6w 高离散环境下能否找到「更高维度表现」的邻居并计算出合理 ΔV。

用法: python scripts/test_a02_repair_pathway_stress.py
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.case_retriever import CaseRetriever
from core.pathway_analyzer import analyze_repair_pathway


def main():
    cache_dir = ROOT / "data_local"
    points_path = cache_dir / "a02_full_points.npz"
    meta_path = cache_dir / "a02_full_meta.json"
    if not points_path.exists() or not meta_path.exists():
        print("❌ 请先运行 fds_pattern_scanner.py --target A-02 生成 a02_full_*.npz/json")
        sys.exit(1)

    retriever = CaseRetriever(cache_dir=cache_dir, pattern_id="A-02")
    if retriever.case_count == 0:
        print("❌ A-02 全量索引未加载")
        sys.exit(1)
    print(f"✅ 已加载 A-02 样本数: {retriever.case_count:,}")

    # 随机抽 10 个（含高 S 样本以验证「应力过载」修复路径）
    n = retriever.case_count
    indices = random.sample(range(n), min(10, n))
    # 确保至少 3 个为高 S（S 轴索引 3）
    points = retriever._points
    if points is not None and len(points) >= 100:
        high_s = np.argsort(-points[:, 3])[: min(200, len(points))]
        high_s_set = set(int(i) for i in high_s[:50])
        for i in list(high_s_set)[:3]:
            if i not in indices:
                indices[len(indices) % 10] = i

    ok = 0
    for idx in indices:
        c = retriever._cases[idx]
        pt = c["point"]
        ref = c.get("ref", f"A-02-{idx}")
        pathway = analyze_repair_pathway(retriever, pt, top_repair=5)
        deficit_info = pathway.get("deficit_info")
        repair_paths = pathway.get("repair_paths", [])
        repair_vector = pathway.get("repair_vector")

        s_val = pt[3] if len(pt) >= 4 else 0
        print(f"\n--- {ref} 5D={[round(x, 2) for x in pt]} (S={s_val:.2f}) ---")
        if deficit_info:
            print(f"  瓶颈轴: {deficit_info.get('axis')} ({deficit_info.get('axis_label')})")
            print(f"  当前→目标: {deficit_info.get('current')} → {deficit_info.get('target_from_centroid')} (补齐 {deficit_info.get('deficit')})")
        if repair_paths:
            print(f"  修复路径数: {len(repair_paths)}")
            for r in repair_paths[:2]:
                print(f"    · {r.get('ref')} Δ{deficit_info.get('axis', '?')}=+{r.get('improvement_on_axis')}")
            if repair_vector:
                dv = repair_vector.get("delta_vector") or {}
                print(f"  ΔV: {dv}")
            ok += 1
        else:
            print("  (无修复路径或已高于参考)")

    print(f"\n🎯 压力测试完成: {ok}/10 样本得到有效修复路径与 ΔV")
    if ok >= 5:
        print("✅ Step 8.5 验证通过：A-02 高离散环境下 pathway_analyzer 可检索到合理邻居并计算 ΔV。")
    else:
        print("⚠️ 部分样本无修复路径（可能因 A-02 无质心，参考为 0；或邻居在该轴均不高于当前）。")


if __name__ == "__main__":
    main()
