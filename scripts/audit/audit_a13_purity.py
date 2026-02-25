#!/usr/bin/env python3
"""
FDS Step 6 专项：A-13 专旺格 流形纯度审计
筛选 E > 2.0 样本，观测 M/S 受排斥程度；红线：M、S 若仍高则非专旺而是身强，须加纯度过滤。
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
PATTERN_ID = "A-13"
E_MIN = 2.0


def run_audit(db_path: Path = PHYSICS_DB) -> dict:
    if not db_path.exists():
        return {"error": "DuckDB 不存在", "n_total": 0}
    conn = duckdb.connect(str(db_path))
    n_total = conn.execute(
        "SELECT COUNT(*) FROM pattern_points WHERE pattern_id = ?", [PATTERN_ID]
    ).fetchone()[0]
    if n_total == 0:
        conn.close()
        return {
            "pattern_id": PATTERN_ID,
            "n_total": 0,
            "n_E_gt_2": 0,
            "message": "无 A-13 数据，请先运行 518k 海选并迁入 DuckDB",
        }
    # E > 2.0 的样本的 M、S 分布（应显著负/低）
    row = conn.execute("""
        SELECT COUNT(*), AVG(M), AVG(S), STDDEV(M), STDDEV(S),
               SUM(CASE WHEN M > 0.5 OR S > 0.5 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS pct_M_or_S_high
        FROM pattern_points WHERE pattern_id = ? AND E > ?
    """, [PATTERN_ID, E_MIN]).fetchone()
    n_e_high = row[0] or 0
    if n_e_high == 0:
        conn.close()
        return {
            "pattern_id": PATTERN_ID,
            "n_total": int(n_total),
            "n_E_gt_2": 0,
            "message": f"无 E > {E_MIN} 样本，专旺纯度待海选后复核",
        }
    return {
        "pattern_id": PATTERN_ID,
        "n_total": int(n_total),
        "n_E_gt_2": int(n_e_high),
        "mean_M_E_high": round(float(row[1]), 4),
        "mean_S_E_high": round(float(row[2]), 4),
        "std_M": round(float(row[3] or 0), 4),
        "std_S": round(float(row[4] or 0), 4),
        "pct_M_or_S_high": round(float(row[5] or 0), 4),
        "red_line_check": "M/S 仍高，疑身强非专旺，须加纯度过滤" if (row[5] or 0) > 0.2 else "通过",
    }


def main():
    out = AUDIT_LOGS / "audit_a13_purity.json"
    AUDIT_LOGS.mkdir(parents=True, exist_ok=True)
    report = run_audit()
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"A-13 流形纯度审计 (E>{E_MIN}) → {out}")
    if report.get("n_total", 0) == 0:
        print("  ⚠️ 无 A-13 数据，请先执行 518k 海选并迁入 DuckDB")
    else:
        print(f"  n_total={report['n_total']}, n_E_gt_2={report.get('n_E_gt_2')}, mean_M={report.get('mean_M_E_high')}, mean_S={report.get('mean_S_E_high')}, red_line={report.get('red_line_check')}")
    sys.exit(0)


if __name__ == "__main__":
    main()
