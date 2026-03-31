#!/usr/bin/env python3
"""
SOP V6.3：A-01～A-13 质心重校准（均值漂移消除）
================================================
从 DuckDB pattern_points 提取 A-01～A-13 的 518k 实测均值，热覆盖 core/engine/static_atlas.json。
无数据时保留原质心并记录告警。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

EARLY_PATTERNS = [f"A-{i:02d}" for i in range(1, 14)]
STATIC_ATLAS_PATH = ROOT / "core" / "engine" / "static_atlas.json"
DIM_ORDER = ["E", "O", "M", "S", "R"]


def main(pattern_filter: list[str] | None = None) -> None:
    from core.database import PHYSICS_DB
    from core.database.fds_physics import FDSPhysics

    if not STATIC_ATLAS_PATH.exists():
        print("❌ 未找到 static_atlas.json:", STATIC_ATLAS_PATH)
        sys.exit(1)

    with open(STATIC_ATLAS_PATH, "r", encoding="utf-8") as f:
        atlas = json.load(f)
    patterns = atlas.get("patterns") or []
    by_id = { (p.get("pattern_id") or "").strip().upper(): p for p in patterns }

    physics = FDSPhysics(PHYSICS_DB)
    updated = 0
    skipped = []
    patterns_to_run = [p for p in EARLY_PATTERNS if not pattern_filter or p in pattern_filter]

    for pid in patterns_to_run:
        cen = physics.get_centroid(pid)
        if cen is None:
            skipped.append((pid, "无数据"))
            continue
        mu, count = cen
        if count == 0:
            skipped.append((pid, "样本数 0"))
            continue
        p = by_id.get(pid)
        if not p:
            skipped.append((pid, "atlas 中无此 ID"))
            continue
        old = p.get("centroid_5d") or [0] * 5
        new_cen = [round(float(mu[i]), 6) for i in range(5)]
        p["centroid_5d"] = new_cen
        if not p.get("abundance"):
            p["abundance"] = {"match_count": count, "percentage": round(100.0 * count / 518400, 4), "total_scanned": 518400}
        else:
            p["abundance"]["match_count"] = count
            p["abundance"]["percentage"] = round(100.0 * count / 518400, 4)
        updated += 1
        print(f"  {pid}: n={count}, 质心 -> {new_cen}")

    physics.close()

    if updated > 0:
        with open(STATIC_ATLAS_PATH, "w", encoding="utf-8") as f:
            json.dump(atlas, f, ensure_ascii=False, indent=2)
        print("✅ A-01～A-13 质心重校准完成，已热覆盖:", STATIC_ATLAS_PATH)
        print("   更新数:", updated)
    else:
        print("⚠️ 未更新任何质心（DuckDB 中 A-01～A-13 无样本或 atlas 无对应项）")
    if skipped:
        print("   跳过:", skipped)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="A-01～A-13 质心重校准")
    p.add_argument("--pattern", type=str, default=None, help="仅处理指定格局，如 A-13")
    args = p.parse_args()
    pattern_filter = [args.pattern.strip().upper()] if args.pattern else None
    main(pattern_filter=pattern_filter)
