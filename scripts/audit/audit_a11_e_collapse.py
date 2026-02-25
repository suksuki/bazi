#!/usr/bin/env python3
"""
FDS Step 6 专项：A-11 从财格 日主坍缩度审计
统计 E/O 联合分布；红线：若大量样本 E 在 0 附近则 L1 过宽，须找出「弃命」极值点。
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
PATTERN_ID = "A-11"


def run_audit(db_path: Path = PHYSICS_DB) -> dict:
    if not db_path.exists():
        return {"error": "DuckDB 不存在", "n": 0}
    conn = duckdb.connect(str(db_path))
    # 总样本数
    n_total = conn.execute(
        "SELECT COUNT(*) FROM pattern_points WHERE pattern_id = ?", [PATTERN_ID]
    ).fetchone()[0]
    if n_total == 0:
        conn.close()
        return {
            "pattern_id": PATTERN_ID,
            "n": 0,
            "message": "无 A-11 数据，请先运行 518k 海选并迁入 DuckDB（run_a11_a12_a13_scan_and_migrate.py）",
        }
    # E/O 联合：均值、标准差；E 在 [-0.2, 0.2] 的占比（红线）；E < -0.8 的占比（弃命典型）
    row = conn.execute("""
        SELECT
            AVG(E) AS mean_E, AVG(O) AS mean_O, STDDEV(E) AS std_E, STDDEV(O) AS std_O,
            SUM(CASE WHEN E BETWEEN -0.2 AND 0.2 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS pct_E_near_zero,
            SUM(CASE WHEN E < -0.8 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS pct_E_collapse
        FROM pattern_points WHERE pattern_id = ?
    """, [PATTERN_ID]).fetchone()
    # 弃命极值点：E 最低的 50 个
    extreme = conn.execute("""
        SELECT ref, E, O, M, S, R FROM pattern_points
        WHERE pattern_id = ? ORDER BY E ASC LIMIT 50
    """, [PATTERN_ID]).fetchall()
    conn.close()
    return {
        "pattern_id": PATTERN_ID,
        "n": int(n_total),
        "mean_E": round(float(row[0]), 4),
        "mean_O": round(float(row[1]), 4),
        "std_E": round(float(row[2] or 0), 4),
        "std_O": round(float(row[3] or 0), 4),
        "pct_E_near_zero": round(float(row[4] or 0), 4),
        "pct_E_collapse": round(float(row[5] or 0), 4),
        "red_line_check": "L1 过宽" if (row[4] or 0) > 0.3 else "通过",
        "extreme_abandon_self": [
            {"ref": r[0], "E": round(float(r[1]), 4), "O": round(float(r[2]), 4), "M": round(float(r[3]), 4), "S": round(float(r[4]), 4), "R": round(float(r[5]), 4)}
            for r in extreme
        ],
    }


def main():
    out = AUDIT_LOGS / "audit_a11_e_collapse.json"
    AUDIT_LOGS.mkdir(parents=True, exist_ok=True)
    report = run_audit()
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"A-11 日主坍缩度审计 → {out}")
    if report.get("n", 0) == 0:
        print("  ⚠️ 无 A-11 数据，请先执行 518k 海选并迁入 DuckDB")
    else:
        print(f"  n={report['n']}, mean_E={report.get('mean_E')}, pct_E_near_zero={report.get('pct_E_near_zero')}, red_line={report.get('red_line_check')}")
    sys.exit(0)


if __name__ == "__main__":
    main()
