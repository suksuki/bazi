import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from v17_rebirth.paths import RUNTIME_DIR

class EvolutionDB:
    """V17 智脑进化数据库：负责物理演化账本与 RLHF 反馈的持久化。"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (RUNTIME_DIR / "v17_evolution.db")
        self._init_db()

    def _init_db(self):
        """初始化进化表结构。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evolution_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ten_god TEXT,
                    step TEXT,
                    old_val REAL,
                    new_val REAL,
                    delta REAL,
                    reason TEXT,
                    plugin_id TEXT,
                    fingerprint TEXT -- 物理特征指纹 (JSON)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rlhf_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    decision_id TEXT,
                    action TEXT,
                    status TEXT, -- APPROVED / REJECTED
                    residual_correction REAL, -- 用户修正残差
                    meta JSON
                )
            """)
            conn.commit()

    def log_evolution(self, session_id: str, ten_god: str, step: str, old_val: float, new_val: float, reason: str, plugin_id: str, fingerprint: Optional[Dict] = None):
        """记录一次物理演变。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO evolution_ledger (session_id, ten_god, step, old_val, new_val, delta, reason, plugin_id, fingerprint)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, ten_god, step, old_val, new_val, new_val - old_val, reason, plugin_id,
                json.dumps(fingerprint) if fingerprint else None
            ))
            conn.commit()

    def log_feedback(self, session_id: str, decision_id: str, action: str, status: str, residual: float = 0.0, meta: Optional[Dict] = None):
        """记录用户反馈（RLHF）。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO rlhf_feedback (session_id, decision_id, action, status, residual_correction, meta)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, decision_id, action, status, residual, json.dumps(meta) if meta else None))
            conn.commit()

    def get_recent_evolution(self, limit: int = 50) -> List[Dict]:
        """获取最近的演化记录。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM evolution_ledger ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

# 全局单例
evolution_storage = EvolutionDB()
