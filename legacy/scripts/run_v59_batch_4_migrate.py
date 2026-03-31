#!/usr/bin/env python3
"""
FDS SOP V5.9：第四梯队（A-36～A-40）Phase 3 迁库
==================================================
- A-36（从儿格）全量迁入，不设 limit。
- A-37（从气格）增加稳定性系数核验：仅迁入与质心距离在 mean + a37_max_std*std 以内的样本。
- 其余格局按 --limit 执行。
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
    p = argparse.ArgumentParser(description="V5.9 第四梯队 Phase 3 迁库（A-36 全量，A-37 稳定性核验）")
    p.add_argument("--data", type=Path, default=None)
    p.add_argument("--abundance", type=Path, default=None, help="默认 audit_logs/v59_batch_4_abundance.json")
    p.add_argument("--limit", type=int, default=2000, help="每格局最多迁入条数（默认 2000）；A-36 不受此限")
    p.add_argument("--a37-max-std", type=float, default=1.5, help="A-37 稳定性核验：仅迁入距离质心 ≤ mean+此值*std 的样本（默认 1.5）")
    args = p.parse_args()

    weights, gods = _load_v4_tmm()
    if weights is None or gods is None:
        print("⚠️ 未找到 V4.0-BETA 矩阵，无法计算 5D。")
        sys.exit(1)
    god_index = {g: i for i, g in enumerate(gods)}

    abundance_path = args.abundance or (ROOT / "audit_logs" / "v59_batch_4_abundance.json")
    if not abundance_path.exists():
        print(f"❌ 未找到丰度报告: {abundance_path}，请先运行 run_v59_batch_4_scan.py")
        sys.exit(1)
    with open(abundance_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    data_path = args.data or Path(report.get("data_path", ""))
    if not data_path or not Path(data_path).exists():
        data_path = ROOT / "data" / "holographic_universe_518k.jsonl"
        if not data_path.exists():
            data_path = ROOT / "data_local" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        print("❌ 未找到 518k 数据")
        sys.exit(1)
    data_path = Path(data_path)

    from pattern_scanner_v59 import l1_match_a36_through_a40

    pattern_ids = [f"A-{i}" for i in range(36, 41)]
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
            matched = l1_match_a36_through_a40(case)
            ref = case.get("uid") or case.get("id") or case.get("case_id") or f"line_{i}"
            try:
                pt = _case_to_5d(case, weights, god_index)
            except Exception:
                continue
            for pid in matched:
                if pid not in by_pattern:
                    continue
                bag = by_pattern[pid]
                # A-36 从儿格全量迁入，不设 limit
                cap = None if pid == "A-36" else args.limit
                if cap is not None and len(bag["refs"]) >= cap:
                    continue
                bag["refs"].append(str(ref))
                bag["line_indices"].append(i)
                bag["points"].append(pt)
            if total % 100000 == 0 and total > 0:
                print(f"   已扫描 {total:,} 行…")

    # A-37 稳定性系数核验：仅保留距离质心 ≤ mean + a37_max_std * std 的样本
    if by_pattern["A-37"]["points"]:
        pts = np.array(by_pattern["A-37"]["points"], dtype=np.float64)
        cen = np.mean(pts, axis=0)
        dist = np.linalg.norm(pts - cen, axis=1)
        mean_d, std_d = float(np.mean(dist)), float(np.std(dist)) or 1e-9
        thresh = mean_d + args.a37_max_std * std_d
        mask = dist <= thresh
        n_before = len(pts)
        n_after = int(np.sum(mask))
        by_pattern["A-37"]["refs"] = [by_pattern["A-37"]["refs"][j] for j in range(n_before) if mask[j]]
        by_pattern["A-37"]["line_indices"] = [by_pattern["A-37"]["line_indices"][j] for j in range(n_before) if mask[j]]
        by_pattern["A-37"]["points"] = [pts[j].tolist() for j in range(n_before) if mask[j]]
        print(f"  A-37 稳定性核验: 保留 {n_after:,} / {n_before:,}（距离质心 ≤ mean+{args.a37_max_std}×std）")

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
    print("第四梯队 Phase 3 迁库完成。")
    sys.exit(0)


if __name__ == "__main__":
    main()
