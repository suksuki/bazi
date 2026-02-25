#!/usr/bin/env python3
"""
FDS Step 6 合拢：法理一致性终审报告。
对比 DuckDB 中各格局（含 A-11～A-13）的物理实测均值与审计师签发的 TMM 初始向量，写入 audit_logs/v5_5_extreme_patterns_alignment.json。
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

# 审计师签发的 TMM 主向量（E,O,M,S,R 顺序，与 manifest 一致）
AUDITOR_TMM_MAIN = {
    "A-11": [-1.2, -1.0, 2.0, -0.5, -0.8],
    "A-12": [-1.5, 1.2, -0.5, 2.0, -1.0],
    "A-13": [2.2, 1.2, -1.0, -1.0, 0.8],
}
DIMS = ["E", "O", "M", "S", "R"]


def run_alignment(db_path: Path = PHYSICS_DB) -> dict:
    if not db_path.exists():
        return {"error": "DuckDB 不存在", "patterns": []}
    conn = duckdb.connect(str(db_path))
    rows = conn.execute("""
        SELECT pattern_id, COUNT(*) AS n,
               AVG(E) AS E, AVG(O) AS O, AVG(M) AS M, AVG(S) AS S, AVG(R) AS R
        FROM pattern_points
        GROUP BY pattern_id ORDER BY pattern_id
    """).fetchall()
    conn.close()
    by_pid = {r[0]: r for r in rows}
    all_pids = sorted(set(by_pid.keys()) | set(AUDITOR_TMM_MAIN.keys()))
    patterns = []
    for pid in all_pids:
        r = by_pid.get(pid)
        if r is None:
            n = 0
            measured = None
            expected = AUDITOR_TMM_MAIN.get(pid)
            diff = None
        else:
            n = int(r[1])
            measured = [round(float(r[2]), 4), round(float(r[3]), 4), round(float(r[4]), 4), round(float(r[5]), 4), round(float(r[6]), 4)]
            expected = AUDITOR_TMM_MAIN.get(pid)
            if expected is None:
                expected = "（无签发主向量，仅记录实测）"
                diff = None
            else:
                diff = [round(measured[i] - expected[i], 4) for i in range(5)]
        patterns.append({
            "pattern_id": pid,
            "n": n,
            "measured_mean": dict(zip(DIMS, measured)) if measured else None,
            "auditor_tmm_main": expected if isinstance(expected, list) else expected,
            "diff": dict(zip(DIMS, diff)) if diff else None,
        })
    return {
        "schema_version": "1.0",
        "description": "V5.5 极端格局法理一致性：DuckDB 实测均值 vs 审计师签发 TMM 主向量",
        "source_db": str(db_path),
        "patterns": patterns,
    }


def main():
    out = AUDIT_LOGS / "v5_5_extreme_patterns_alignment.json"
    AUDIT_LOGS.mkdir(parents=True, exist_ok=True)
    report = run_alignment()
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"法理一致性终审报告 → {out}")
    for p in report.get("patterns", []):
        mm = p.get("measured_mean")
        e_val = mm.get("E") if mm else None
        print(f"  {p['pattern_id']}: n={p['n']}, measured_E={e_val}, diff={p.get('diff')}")
    sys.exit(0)


if __name__ == "__main__":
    main()
