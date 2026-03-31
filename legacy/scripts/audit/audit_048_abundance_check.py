#!/usr/bin/env python3
"""
第 048 号自检：A-01～A-10 总样本数不得超过 518k 的 20%（103,680）。
若超过则认定「泛滥误差」，审计不通过。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_LOCAL = ROOT / "data_local"
TOTAL_UNIVERSE = 518_400
MAX_PCT = 0.20
MAX_TOTAL = int(TOTAL_UNIVERSE * MAX_PCT)  # 103_680


def main() -> int:
    total_matched = 0
    counts = {}
    for pid in [f"A-{i:02d}" for i in range(1, 11)]:
        prefix = pid.lower().replace("-", "")
        npz_path = DATA_LOCAL / f"{prefix}_full_points.npz"
        if not npz_path.exists():
            counts[pid] = 0
            continue
        import numpy as np
        data = np.load(npz_path)
        n = data["points"].shape[0]
        counts[pid] = n
        total_matched += n

    print("第 048 号丰度自检：A-01～A-10 总样本 vs 518k 20% 红线")
    print(f"  518k 总量: {TOTAL_UNIVERSE:,}  红线: {MAX_TOTAL:,} ({MAX_PCT*100:.0f}%)")
    for pid, c in counts.items():
        print(f"  {pid}: {c:,}")
    print(f"  A-01～A-10 合计: {total_matched:,}")
    if total_matched > MAX_TOTAL:
        print(f"  ❌ 审计不通过：合计 {total_matched:,} > {MAX_TOTAL:,}（存在泛滥误差）")
        return 1
    print(f"  ✅ 审计通过：合计 {total_matched:,} ≤ {MAX_TOTAL:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
