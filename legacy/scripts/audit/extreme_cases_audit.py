#!/usr/bin/env python3
"""
FDS V5.5 Step 6.1：DuckDB 极值扫描，输出「到质心距离 Top100」极端异类点，供判词回测。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

try:
    import duckdb
except ImportError:
    print("❌ 需要 duckdb", file=sys.stderr)
    sys.exit(1)

PHYSICS_DB = ROOT / "core" / "database" / "fds_physics.duckdb"
AUDIT_LOGS = ROOT / "audit_logs"


def run_extreme_top100(pattern_id: str, limit: int = 100, db_path: Path = PHYSICS_DB) -> list:
    """返回该格局到质心欧氏距离最大的 limit 个点（ref, line_index, E,O,M,S,R, d_to_centroid）。"""
    if not db_path.exists():
        return []
    conn = duckdb.connect(str(db_path))
    pid = pattern_id.strip().upper()
    rows = conn.execute("""
        WITH cen AS (
            SELECT AVG(E) AS e, AVG(O) AS o, AVG(M) AS m, AVG(S) AS s, AVG(R) AS r
            FROM pattern_points WHERE pattern_id = ?
        )
        SELECT p.ref, p.line_index, p.E, p.O, p.M, p.S, p.R,
            SQRT(POWER(p.E - c.e, 2) + POWER(p.O - c.o, 2) + POWER(p.M - c.m, 2) + POWER(p.S - c.s, 2) + POWER(p.R - c.r, 2)) AS d_to_centroid
        FROM pattern_points p, cen c
        WHERE p.pattern_id = ?
        ORDER BY d_to_centroid DESC
        LIMIT ?
    """, [pid, pid, limit]).fetchall()
    conn.close()
    return [
        {
            "ref": r[0], "line_index": r[1],
            "E": round(float(r[2]), 4), "O": round(float(r[3]), 4), "M": round(float(r[4]), 4),
            "S": round(float(r[5]), 4), "R": round(float(r[6]), 4),
            "d_to_centroid": round(float(r[7]), 4),
        }
        for r in rows
    ]


def main():
    import argparse
    p = argparse.ArgumentParser(description="V5.5 极端异类点 Top100")
    p.add_argument("--pattern", type=str, default="A-07", help="格局 ID")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--out", type=Path, default=None, help="输出 JSON 路径，默认 audit_logs/extreme_cases_audit.json")
    args = p.parse_args()
    out = args.out or AUDIT_LOGS / "extreme_cases_audit.json"
    cases = run_extreme_top100(args.pattern, limit=args.limit)
    payload = {
        "schema_version": "1.0",
        "description": "FDS V5.5 Step 6.1 极端异类点（到质心距离 Top N）",
        "pattern_id": args.pattern.strip().upper(),
        "limit": args.limit,
        "count": len(cases),
        "cases": cases,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"✅ {args.pattern} 极端异类点 {len(cases)} 条 → {out}")
    sys.exit(0)


if __name__ == "__main__":
    main()
