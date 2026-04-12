"""SessionConsensus：按 id 倒序取每个 decision_key 的最新一条，避免 DB 返回顺序不稳定导致共识漂移。"""
from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import desc
from sqlmodel import select

from app.db.models import SessionConsensus


def fetch_latest_session_consensus_rows(session: Any, session_pk: int) -> List[Dict[str, Any]]:
    """
    读取某 session（当前实现里与 consultation_id 同列）下共识历史。
    同一 decision_key 若有多条记录，仅保留 id 最大（最新）的一条。
    """
    if not session_pk:
        return []
    stmt = (
        select(SessionConsensus)
        .where(SessionConsensus.session_id == session_pk)
        .order_by(desc(SessionConsensus.id))
    )
    rows = list(session.exec(stmt).all())
    picked: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        key = str(row.decision_key or "").strip()
        if not key or key in picked:
            continue
        picked[key] = {
            "decision_key": key,
            "confirmed_value": float(row.confirmed_value) if row.confirmed_value is not None else None,
            "reasoning": str(row.reasoning or ""),
        }
    return sorted(picked.values(), key=lambda x: x["decision_key"])
