#!/usr/bin/env python3
"""
第 045 号指令：将 data_local/*_full_points.npz 与 *_full_meta.json 迁移至 DuckDB。
迁移后执行物理等效性校验：DuckDB 均值 vs NPZ 均值，误差 < 1e-7。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 确保与当前解释器一致，避免「pip 装了一个 Python、脚本用另一个」导致找不到 duckdb
try:
    import duckdb
except ImportError:
    print("❌ 未检测到 duckdb。请用【当前运行本脚本的 Python】安装：", file=sys.stderr)
    print(f"   {sys.executable} -m pip install duckdb", file=sys.stderr)
    sys.exit(1)

import numpy as np

from core.database import PHYSICS_DB
from core.database.fds_physics import FDSPhysics, DIM_ORDER


def migrate_npz_to_duckdb(data_local: Path, physics_db_path: Path) -> dict:
    """
    扫描 data_local 下 *_full_points.npz，将对应 *_full_meta.json 的 ref/line_index 与 points 写入 DuckDB。
    返回 { pattern_id: { "inserted": N, "npz_mean": list, "duckdb_mean": list, "max_diff": float } }
    """
    physics = FDSPhysics(physics_db_path)
    results = {}

    for npz_path in sorted(data_local.glob("*_full_points.npz")):
        # 例: a02_full_points.npz -> A-02
        stem = npz_path.stem.replace("_full_points", "")
        pattern_id = f"{stem[0].upper()}-{stem[1:]}" if len(stem) >= 2 and stem[0].lower() == "a" else stem.upper()

        meta_path = data_local / f"{stem}_full_meta.json"
        if not meta_path.exists():
            print(f"⚠️ 跳过 {pattern_id}: 无 {meta_path.name}")
            continue

        data = np.load(npz_path)
        points = data["points"]
        if points.shape[1] != 5:
            print(f"⚠️ 跳过 {pattern_id}: points 列数 != 5")
            continue

        n_rows = points.shape[0]
        refs = [f"{pattern_id}-{i}" for i in range(n_rows)]
        line_indices = list(range(n_rows))
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        if isinstance(meta, list) and len(meta) == n_rows:
            refs = [m.get("ref", refs[i]) for i, m in enumerate(meta)]
            line_indices = [m.get("line_index", i) for i, m in enumerate(meta)]

        print(f"  迁移 {pattern_id} ({points.shape[0]:,} 行)...", end=" ", flush=True)
        n_insert = physics.insert_points(pattern_id, refs, line_indices, points)
        npz_mean = np.mean(points, axis=0)
        cen = physics.get_centroid(pattern_id)
        duckdb_mean = cen[0].tolist() if cen else None
        max_diff = None
        if duckdb_mean is not None:
            max_diff = float(np.max(np.abs(np.array(duckdb_mean) - npz_mean)))
        results[pattern_id] = {
            "inserted": n_insert,
            "npz_mean": npz_mean.tolist(),
            "duckdb_mean": duckdb_mean,
            "max_diff": max_diff,
        }
        print(f"✅ 插入 {n_insert:,} 行, max_diff={max_diff}", flush=True)

    physics.close()
    return results


def run_equivalence_check(results: dict, tolerance: float = 1e-7) -> bool:
    """物理等效性校验：所有格局 max_diff < tolerance。"""
    ok = True
    for pid, r in results.items():
        if r.get("max_diff") is None:
            continue
        if r["max_diff"] >= tolerance:
            print(f"❌ {pid} 物理等效性不通过: max_diff={r['max_diff']} >= {tolerance}")
            ok = False
        else:
            print(f"✅ {pid} 物理等效性通过: max_diff={r['max_diff']} < {tolerance}")
    return ok


def main():
    data_local = ROOT / "data_local"
    if not data_local.exists():
        print("❌ data_local 不存在")
        sys.exit(1)
    print("第 045 号：NPZ → DuckDB 迁移与物理等效性校验")
    print(f"  data_local: {data_local}")
    print(f"  DuckDB: {PHYSICS_DB}")
    results = migrate_npz_to_duckdb(data_local, PHYSICS_DB)
    if not results:
        print("未迁移任何格局，跳过等效性校验")
        sys.exit(0)
    ok = run_equivalence_check(results, tolerance=1e-7)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
