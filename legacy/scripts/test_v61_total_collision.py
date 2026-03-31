#!/usr/bin/env python3
"""
FDS V6.1：全息坍缩压力测试 (Total Collision Test)
=================================================
从 518k 随机抽取 10,000 条，计算到 60 个质心的欧氏距离 D_M，
标记双重捕获（is_double_capture），产出 v61_collision_density.json。
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np

# 双重捕获判定：第二近与第一近距离比 ≤ 此值视为重叠捕获
RATIO_DOUBLE_CAPTURE = 1.2


def _load_v4_tmm():
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


def _case_to_5d(case: dict, weights: np.ndarray, god_index: dict) -> np.ndarray | None:
    try:
        vec = np.zeros(10)
        for g, idx in god_index.items():
            val = (case.get("ten_gods") or {}).get(g, 0)
            if isinstance(val, (int, float)):
                vec[idx] = float(val)
            elif isinstance(val, dict):
                vec[idx] = float(val.get("mean", val.get("strength", 0)))
        return np.dot(weights.T, vec)
    except Exception:
        return None


def main():
    import argparse
    p = argparse.ArgumentParser(description="V6.1 全量对撞压力测试")
    p.add_argument("--sample-size", type=int, default=10_000, help="随机采样条数")
    p.add_argument("--seed", type=int, default=42, help="随机种子")
    p.add_argument("--atlas", type=Path, default=None, help="图谱路径，默认 audit_logs/atlas_v6.1_final.json")
    p.add_argument("--out", type=Path, default=None, help="输出路径，默认 audit_logs/v61_collision_density.json")
    args = p.parse_args()

    atlas_path = args.atlas or (ROOT / "audit_logs" / "atlas_v6.1_final.json")
    if not atlas_path.exists():
        print(f"❌ 未找到图谱: {atlas_path}")
        sys.exit(1)
    with open(atlas_path, "r", encoding="utf-8") as f:
        atlas = json.load(f)
    patterns = atlas.get("patterns") or []
    if len(patterns) != 60:
        print(f"⚠️ 图谱格局数 {len(patterns)}，非 60")
    pids = [p["pattern_id"] for p in patterns]
    centroids = np.array([p["centroid_5d"] for p in patterns], dtype=np.float64)

    weights, gods = _load_v4_tmm()
    if weights is None or gods is None:
        print("❌ 未找到 V4 矩阵")
        sys.exit(1)
    god_index = {g: i for i, g in enumerate(gods)}

    data_path = ROOT / "data" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        data_path = ROOT / "data_local" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        print("❌ 未找到 518k 数据")
        sys.exit(1)

    # 第一遍：收集所有有效行的索引
    line_indices = []
    with open(data_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not case.get("bazi") or not case.get("ten_gods"):
                continue
            line_indices.append(i)
    total_eligible = len(line_indices)
    if total_eligible < args.sample_size:
        print(f"⚠️ 有效行 {total_eligible} < 采样数 {args.sample_size}，将全部使用")
        sample_indices = line_indices
    else:
        random.seed(args.seed)
        sample_indices = random.sample(line_indices, args.sample_size)

    sample_indices_set = set(sample_indices)
    points_by_line: dict[int, np.ndarray] = {}
    with open(data_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i not in sample_indices_set:
                continue
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError:
                continue
            pt = _case_to_5d(case, weights, god_index)
            if pt is not None:
                points_by_line[i] = pt

    # 构建样本点数组（保持与 line 对应）
    ordered_lines = sorted(points_by_line.keys())[: args.sample_size]
    sample_points = np.array([points_by_line[j] for j in ordered_lines], dtype=np.float64)
    n_sample = len(sample_points)

    # 到 60 质心的距离 (n_sample, 60)
    diff = sample_points[:, np.newaxis, :] - centroids[np.newaxis, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=2))
    order = np.argsort(dist, axis=1)
    d1 = np.take_along_axis(dist, order[:, 0:1], axis=1).ravel()
    d2 = np.take_along_axis(dist, order[:, 1:2], axis=1).ravel()
    capture_1st = [pids[order[i, 0]] for i in range(n_sample)]
    capture_2nd = [pids[order[i, 1]] for i in range(n_sample)]
    is_double = (d2 / (d1 + 1e-12)) <= RATIO_DOUBLE_CAPTURE

    double_count = int(np.sum(is_double))
    overlap_pairs: dict[str, int] = {}
    for i in range(n_sample):
        if not is_double[i]:
            continue
        a, b = capture_1st[i], capture_2nd[i]
        if a > b:
            a, b = b, a
        key = f"{a}+{b}"
        overlap_pairs[key] = overlap_pairs.get(key, 0) + 1

    report = {
        "schema": "FDS_V61_collision_density",
        "description": "全息坍缩压力测试：10k 随机样本对 60 质心的捕获与重叠",
        "total_sampled": n_sample,
        "double_capture_count": double_count,
        "double_capture_ratio": round(double_count / n_sample, 4) if n_sample else 0,
        "ratio_threshold": RATIO_DOUBLE_CAPTURE,
        "overlap_pairs": dict(sorted(overlap_pairs.items(), key=lambda x: -x[1])),
        "audit_note": "若 A-01 与 A-39 频繁重叠，说明 E 轴判定存在粘连。",
        "sample_detail_count": min(500, n_sample),
        "samples": [
            {
                "line_index": int(ordered_lines[i]),
                "capture_1st": capture_1st[i],
                "capture_2nd": capture_2nd[i],
                "d1": round(float(d1[i]), 4),
                "d2": round(float(d2[i]), 4),
                "is_double_capture": bool(is_double[i]),
            }
            for i in range(min(500, n_sample))
        ],
    }

    out_path = args.out or (ROOT / "audit_logs" / "v61_collision_density.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"📄 《全量对撞密度报告》已写入: {out_path}")
    print(f"   采样 {n_sample} 条，双重捕获 {double_count} 条（比例 {report['double_capture_ratio']}）")
    top_pairs = list(report["overlap_pairs"].items())[:10]
    for k, v in top_pairs:
        print(f"   重叠对 {k}: {v} 次")
    sys.exit(0)


if __name__ == "__main__":
    main()
