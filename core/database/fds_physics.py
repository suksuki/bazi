"""
FDS 特征计算层 (DuckDB) — 第 045 号指令
518k 样本 5D 张量批量存储；向量化聚合（均值/协方差）替代 Numpy 循环，支撑秒级物理审计。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

DIM_ORDER = ["E", "O", "M", "S", "R"]


def _init_schema(conn: Any) -> None:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS pattern_points (
        pattern_id VARCHAR(10) NOT NULL,
        ref VARCHAR(128) NOT NULL,
        line_index INTEGER,
        E DOUBLE NOT NULL,
        O DOUBLE NOT NULL,
        M DOUBLE NOT NULL,
        S DOUBLE NOT NULL,
        R DOUBLE NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_pp_pattern ON pattern_points(pattern_id);
    """)
    conn.commit()


class FDSPhysics:
    """DuckDB 特征层：pattern_points 表，向量化聚合。"""

    def __init__(self, db_path: Optional[Path] = None):
        self._path = Path(db_path) if db_path else None
        self._conn: Any = None

    def _ensure_conn(self) -> Any:
        if self._conn is None:
            try:
                import duckdb
            except ImportError:
                import sys
                raise ImportError(
                    "第 045 号指令需要 DuckDB。当前 Python: %s\n"
                    "请用【同一解释器】安装: %s -m pip install duckdb"
                    % (sys.executable, sys.executable)
                )
            path = self._path
            if not path:
                from core.database import PHYSICS_DB
                path = PHYSICS_DB
            path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = duckdb.connect(str(path))
            _init_schema(self._conn)
        return self._conn

    def delete_pattern_points(self, pattern_id: str) -> int:
        """删除指定格局全部点（迁移前清空，保证幂等）。返回删除行数。"""
        conn = self._ensure_conn()
        cur = conn.execute("DELETE FROM pattern_points WHERE pattern_id = ?", (pattern_id.strip().upper(),))
        conn.commit()
        return cur.rowcount

    def insert_points(
        self,
        pattern_id: str,
        refs: List[str],
        line_indices: List[int],
        points: np.ndarray,
    ) -> int:
        """
        批量插入 5D 点阵。points 形状 (N, 5)，顺序 E,O,M,S,R。
        优先用 DataFrame 整表写入（秒级），无 pandas 时回退为分块 executemany。
        返回插入行数。
        """
        conn = self._ensure_conn()
        pattern_id = pattern_id.strip().upper()
        conn.execute("DELETE FROM pattern_points WHERE pattern_id = ?", (pattern_id,))
        n = len(refs)
        if n != points.shape[0] or points.shape[1] != 5:
            raise ValueError("refs 长度与 points 行数一致，且 points 列为 5")
        line_indices = line_indices if len(line_indices) == n else [0] * n

        try:
            import pandas as pd
            df = pd.DataFrame({
                "pattern_id": pattern_id,
                "ref": refs,
                "line_index": line_indices,
                "E": points[:, 0],
                "O": points[:, 1],
                "M": points[:, 2],
                "S": points[:, 3],
                "R": points[:, 4],
            })
            conn.register("_batch", df)
            conn.execute("INSERT INTO pattern_points SELECT * FROM _batch")
            conn.unregister("_batch")
        except ImportError:
            chunk = 50_000
            for start in range(0, n, chunk):
                end = min(start + chunk, n)
                conn.executemany(
                    """
                    INSERT INTO pattern_points (pattern_id, ref, line_index, E, O, M, S, R)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            pattern_id,
                            refs[i],
                            int(line_indices[i]),
                            float(points[i, 0]),
                            float(points[i, 1]),
                            float(points[i, 2]),
                            float(points[i, 3]),
                            float(points[i, 4]),
                        )
                        for i in range(start, end)
                    ],
                )
        conn.commit()
        return n

    def get_centroid(self, pattern_id: str) -> Optional[Tuple[np.ndarray, int]]:
        """
        向量化计算指定格局的 5D 质心（均值）与样本数。
        返回 (mu_5d, count)，无数据时返回 None。
        """
        conn = self._ensure_conn()
        pattern_id = pattern_id.strip().upper()
        row = conn.execute(
            """
            SELECT AVG(E) AS E, AVG(O) AS O, AVG(M) AS M, AVG(S) AS S, AVG(R) AS R, COUNT(*) AS n
            FROM pattern_points WHERE pattern_id = ?
            """,
            (pattern_id,),
        ).fetchone()
        if not row or row[-1] == 0:
            return None
        mu = np.array([float(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4])], dtype=np.float64)
        return mu, int(row[5])

    def get_centroid_and_cov(self, pattern_id: str) -> Optional[Tuple[np.ndarray, Optional[np.ndarray], int]]:
        """
        质心 + 协方差矩阵（DuckDB 向量化）。返回 (mu, cov, n)；n<2 时 cov 为 None。
        """
        conn = self._ensure_conn()
        pattern_id = pattern_id.strip().upper()
        # 先取质心与数量
        cen = self.get_centroid(pattern_id)
        if not cen:
            return None
        mu, n = cen
        if n < 2:
            return (mu, None, n)
        # 协方差: E[(x - mu)(x - mu)^T]，用 DuckDB 聚合
        cols = DIM_ORDER
        cov = np.zeros((5, 5))
        for i, a in enumerate(cols):
            for j, b in enumerate(cols):
                r = conn.execute(
                    f"""
                    SELECT AVG(({a} - (SELECT AVG({a}) FROM pattern_points WHERE pattern_id = ?))
                               * ({b} - (SELECT AVG({b}) FROM pattern_points WHERE pattern_id = ?)))
                    FROM pattern_points WHERE pattern_id = ?
                    """,
                    (pattern_id, pattern_id, pattern_id),
                ).fetchone()
                cov[i, j] = float(r[0]) if r and r[0] is not None else 0.0
        return (mu, cov, n)

    def query_by_axis(
        self,
        pattern_id: str,
        axis: str,
        operator: str,
        value: float,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        按轴条件查询命例，用于「A-07 下 S 轴 > 1.5」等审计查询。
        operator: '>', '>=', '<', '<=', '=', '!='
        """
        conn = self._ensure_conn()
        if axis not in DIM_ORDER:
            raise ValueError(f"axis 须为 {DIM_ORDER} 之一")
        safe_op = {"=": "=", "!=": "!=", ">": ">", ">=": ">=", "<": "<", "<=": "<="}.get(operator, ">=")
        rows = conn.execute(
            f"""
            SELECT ref, line_index, E, O, M, S, R
            FROM pattern_points
            WHERE pattern_id = ? AND {axis} {safe_op} ?
            ORDER BY {axis} DESC
            LIMIT ?
            """,
            (pattern_id.strip().upper(), value, limit),
        ).fetchall()
        return [
            {"ref": r[0], "line_index": r[1], "E": r[2], "O": r[3], "M": r[4], "S": r[5], "R": r[6]}
            for r in rows
        ]

    def count_by_pattern(self, pattern_id: Optional[str] = None) -> Dict[str, int]:
        """各格局样本数；pattern_id 为空时返回全部。"""
        conn = self._ensure_conn()
        if pattern_id:
            r = conn.execute(
                "SELECT COUNT(*) FROM pattern_points WHERE pattern_id = ?",
                (pattern_id.strip().upper(),),
            ).fetchone()
            return {pattern_id.strip().upper(): int(r[0])} if r else {}
        rows = conn.execute(
            "SELECT pattern_id, COUNT(*) AS n FROM pattern_points GROUP BY pattern_id"
        ).fetchall()
        return {r[0]: int(r[1]) for r in rows}

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
