"""
FDS 元数据层 (SQLite) — 第 045 号指令
存储 A-01~A-10 古典正名、TMM 矩阵、SOP 状态；历次物理溢出报告与纠偏备注。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DIM_ORDER = ["E", "O", "M", "S", "R"]


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS pattern_definitions (
        pattern_id TEXT PRIMARY KEY,
        chinese_name TEXT NOT NULL,
        display_name TEXT,
        category TEXT,
        sop_status TEXT DEFAULT 'ACTIVE',
        tmm_ten_gods TEXT NOT NULL,
        tmm_weights_json TEXT NOT NULL,
        centroid_json TEXT,
        source_ref TEXT,
        updated_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_type TEXT NOT NULL,
        pattern_id TEXT,
        iou_value REAL,
        note TEXT,
        payload_json TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_audit_pattern ON audit_logs(pattern_id);
    CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_logs(report_type);
    """)


class FDSRegistry:
    """FDS 元数据层：格局定义与审计日志。"""

    def __init__(self, db_path: Optional[Path] = None):
        self._path = Path(db_path) if db_path else None
        self._conn: Optional[sqlite3.Connection] = None

    def _ensure_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            path = self._path
            if not path:
                from core.database import REGISTRY_DB
                path = REGISTRY_DB
            path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(path))
            self._conn.row_factory = sqlite3.Row
            _init_schema(self._conn)
        return self._conn

    def upsert_pattern(
        self,
        pattern_id: str,
        chinese_name: str,
        tmm_ten_gods: List[str],
        tmm_weights: Dict[str, List[float]],
        *,
        display_name: Optional[str] = None,
        category: Optional[str] = None,
        sop_status: str = "ACTIVE",
        centroid_json: Optional[str] = None,
        source_ref: Optional[str] = None,
    ) -> None:
        """写入或更新格局定义；TMM 须与审计师签发的古典修正版一致（法典一致性锁）。"""
        conn = self._ensure_conn()
        conn.execute(
            """
            INSERT INTO pattern_definitions (
                pattern_id, chinese_name, display_name, category, sop_status,
                tmm_ten_gods, tmm_weights_json, centroid_json, source_ref, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(pattern_id) DO UPDATE SET
                chinese_name=excluded.chinese_name,
                display_name=excluded.display_name,
                category=excluded.category,
                sop_status=excluded.sop_status,
                tmm_ten_gods=excluded.tmm_ten_gods,
                tmm_weights_json=excluded.tmm_weights_json,
                centroid_json=excluded.centroid_json,
                source_ref=excluded.source_ref,
                updated_at=datetime('now')
            """,
            (
                pattern_id,
                chinese_name,
                display_name or chinese_name,
                category or "",
                sop_status,
                json.dumps(tmm_ten_gods, ensure_ascii=False),
                json.dumps(tmm_weights, ensure_ascii=False),
                centroid_json,
                source_ref or "",
            ),
        )
        conn.commit()

    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """按格局 ID 查询；返回含 tmm_weights（已解析）、centroid（已解析）的字典。"""
        conn = self._ensure_conn()
        row = conn.execute(
            "SELECT * FROM pattern_definitions WHERE pattern_id = ?",
            (pattern_id.strip().upper(),),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["tmm_ten_gods"] = json.loads(d["tmm_ten_gods"])
        d["tmm_weights"] = json.loads(d["tmm_weights_json"])
        if d.get("centroid_json"):
            d["centroid"] = json.loads(d["centroid_json"])
        else:
            d["centroid"] = None
        return d

    def list_patterns(self) -> List[Dict[str, Any]]:
        """返回所有格局定义列表（含 TMM 解析）。"""
        conn = self._ensure_conn()
        rows = conn.execute(
            "SELECT pattern_id, chinese_name, sop_status, tmm_ten_gods, tmm_weights_json, centroid_json, source_ref FROM pattern_definitions ORDER BY pattern_id"
        ).fetchall()
        out = []
        for row in rows:
            d = dict(row)
            d["tmm_ten_gods"] = json.loads(d["tmm_ten_gods"])
            d["tmm_weights"] = json.loads(d["tmm_weights_json"])
            d["centroid"] = json.loads(d["centroid_json"]) if d.get("centroid_json") else None
            out.append(d)
        return out

    def append_audit_log(
        self,
        report_type: str,
        *,
        pattern_id: Optional[str] = None,
        iou_value: Optional[float] = None,
        note: Optional[str] = None,
        payload_json: Optional[str] = None,
    ) -> int:
        """追加一条审计日志；返回 id。"""
        conn = self._ensure_conn()
        cur = conn.execute(
            "INSERT INTO audit_logs (report_type, pattern_id, iou_value, note, payload_json) VALUES (?, ?, ?, ?, ?)",
            (report_type, pattern_id, iou_value, note, payload_json),
        )
        conn.commit()
        return cur.lastrowid or 0

    def get_audit_logs(
        self,
        pattern_id: Optional[str] = None,
        report_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """查询审计日志。"""
        conn = self._ensure_conn()
        q = "SELECT * FROM audit_logs WHERE 1=1"
        params: List[Any] = []
        if pattern_id:
            q += " AND pattern_id = ?"
            params.append(pattern_id)
        if report_type:
            q += " AND report_type = ?"
            params.append(report_type)
        q += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
