#!/usr/bin/env python3
"""
第 045 号并网验收：生成 FDS 2.0 全量物理分布统计，写入 audit_logs/v2_0_physics_baseline.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.database import PHYSICS_DB
from core.database.fds_physics import FDSPhysics


def run_baseline(physics_db_path: Path, out_path: Path) -> dict:
    """对 A-01～A-10 各格局做 COUNT/AVG/STDDEV，写入 JSON。"""
    try:
        import duckdb
    except ImportError:
        print("❌ 需要 duckdb", file=sys.stderr)
        return {}
    conn = duckdb.connect(str(physics_db_path))
    rows = conn.execute("""
        SELECT
            pattern_id,
            COUNT(*) AS n,
            AVG(E) AS mean_E, AVG(O) AS mean_O, AVG(M) AS mean_M, AVG(S) AS mean_S, AVG(R) AS mean_R,
            STDDEV(E) AS std_E, STDDEV(O) AS std_O, STDDEV(M) AS std_M, STDDEV(S) AS std_S, STDDEV(R) AS std_R,
            MIN(E) AS min_E, MAX(E) AS max_E, MIN(M) AS min_M, MAX(M) AS max_M, MIN(S) AS min_S, MAX(S) AS max_S
        FROM pattern_points
        GROUP BY pattern_id
        ORDER BY pattern_id
    """).fetchall()
    conn.close()
    patterns = []
    for r in rows:
        patterns.append({
            "pattern_id": r[0],
            "n": int(r[1]),
            "mean": {"E": round(float(r[2]), 4), "O": round(float(r[3]), 4), "M": round(float(r[4]), 4), "S": round(float(r[5]), 4), "R": round(float(r[6]), 4)},
            "std": {"E": round(float(r[7] or 0), 4), "O": round(float(r[8] or 0), 4), "M": round(float(r[9] or 0), 4), "S": round(float(r[10] or 0), 4), "R": round(float(r[11] or 0), 4)},
            "min_E": round(float(r[12]), 4), "max_E": round(float(r[13]), 4),
            "min_M": round(float(r[14]), 4), "max_M": round(float(r[15]), 4),
            "min_S": round(float(r[16]), 4), "max_S": round(float(r[17]), 4),
        })
    report = {
        "schema_version": "1.0",
        "description": "FDS 2.0 全量物理分布基线（第 045 号并网验收）",
        "source_db": str(physics_db_path),
        "patterns": patterns,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report


def main():
    out = ROOT / "audit_logs" / "v2_0_physics_baseline.json"
    print("第 045 号：生成 2.0 版审计综述（DuckDB 全量分布）")
    print(f"  输出: {out}")
    if not PHYSICS_DB.exists():
        print("❌ DuckDB 不存在，请先运行 scripts/migrate_npz_to_duckdb.py")
        sys.exit(1)
    report = run_baseline(PHYSICS_DB, out)
    print(f"  已写入 {len(report.get('patterns', []))} 个格局统计")
    sys.exit(0)


if __name__ == "__main__":
    main()
