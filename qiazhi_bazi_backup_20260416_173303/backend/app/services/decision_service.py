"""裁决链服务：意志指纹捕获（写入 decision_audit_logs，供进化训练）。"""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.db.models import DecisionAuditLog
from app.db.session import session_scope


def resolve_conflict(
    *,
    consultation_id: Optional[int],
    skill_id: str,
    abs_delta: float,
    processing_preference: str,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    记录裁决人对某次冲突的意志注入（进化训练集）。

    - skill_id: 裁决选用的 Skill（manifest id）
    - abs_delta: 当时盘面相关的 Abs 变化量或代理指标
    - processing_preference: 处理偏好（如 accept / defer / override）
    """
    payload = {
        "skill_id": str(skill_id).strip(),
        "abs_delta": float(abs_delta),
        "processing_preference": str(processing_preference or "").strip(),
        **(extra or {}),
    }
    row = DecisionAuditLog(
        consultation_id=consultation_id,
        record_type="evolution_training_set",
        payload=payload,
    )
    with session_scope() as s:
        s.add(row)
        s.flush()
        s.refresh(row)
        rid = row.id
    return {"ok": True, "id": rid, "record_type": "evolution_training_set"}
