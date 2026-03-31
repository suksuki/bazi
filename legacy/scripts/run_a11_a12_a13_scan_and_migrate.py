#!/usr/bin/env python3
"""
FDS Step 6：A-11、A-12、A-13 的 518k 海选扫描并迁入 DuckDB。
执行顺序：对每个格局运行 fds_pattern_scanner（生成 npz + meta），再运行 migrate_npz_to_duckdb 将新 npz 写入 DuckDB。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_LOCAL = ROOT / "data_local"
PHYSICS_DB = ROOT / "core" / "database" / "fds_physics.duckdb"


def main():
    print("第 046 号 Step 6：A-11 / A-12 / A-13 海选并迁入 DuckDB")
    for pid in ["A-11", "A-12", "A-13"]:
        print(f"\n--- {pid} 海选 ---")
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "fds_pattern_scanner.py"), "--target", pid],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=300000,
        )
        if r.returncode != 0:
            print(f"  ⚠️ 海选失败: {r.stderr or r.stdout}")
        else:
            print(r.stdout or "  ✅ 完成")
    print("\n--- 迁入 DuckDB（仅新增 a11/a12/a13）---")
    # 迁移脚本会处理 data_local 下所有 *_full_points.npz；若 a11/a12/a13 已生成则会写入
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "migrate_npz_to_duckdb.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=600000,
    )
    print(r.stdout or "")
    if r.returncode != 0:
        print(r.stderr or "")
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
