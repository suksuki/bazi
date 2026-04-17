"""M5 训练账本：把同化案例标注为黄金训练集。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, Session, select

from app.db.m5_preference_axes import infer_m5_preference_axes
from app.db.models import BrainHtnSnapshot


class ArbiterPreferenceLedger(SQLModel, table=True):
    __tablename__ = "arbiter_preference_ledger"

    id: Optional[int] = Field(default=None, primary_key=True)
    snapshot_id: int = Field(index=True, unique=True)
    session_id: Optional[int] = Field(default=None, index=True)
    version_id: str = Field(default="", index=True)
    preference_tier: str = Field(default="GOLD", index=True)
    training_weight: float = Field(default=1.0)
    source: str = Field(default="arbiter_feedback")
    interaction_pattern_id: str = Field(
        default="",
        max_length=256,
        index=True,
        description="冲突/意志模式主键（如 conflict_pattern_signature），供子午冲等偏好自适应对齐",
    )
    logic_school_axis: str = Field(
        default="UNKNOWN",
        max_length=32,
        index=True,
        description="V13.06：偏好覆盖的意象轴（CLASSICAL_GRID / MODERN_IMAGERY / MIXED / UNKNOWN）",
    )
    authority_scope_peak: Optional[int] = Field(
        default=None,
        index=True,
        description="V13.06：快照载荷中出现插件的 plugin_authority_level 峰值（1–5），供 M5 权重统计",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)


def sync_gold_training_set(session: Session) -> int:
    """把 BrainHtnSnapshot 中 assimilated=true 的样本同步为 GOLD。"""
    snapshots = session.exec(
        select(BrainHtnSnapshot).where(BrainHtnSnapshot.assimilated == True)  # noqa: E712
    ).all()
    changed = 0
    for s in snapshots:
        axis, peak = infer_m5_preference_axes(getattr(s, "snapshot_payload", None))
        row = session.exec(
            select(ArbiterPreferenceLedger).where(ArbiterPreferenceLedger.snapshot_id == int(s.id or 0))
        ).first()
        if row is None:
            session.add(
                ArbiterPreferenceLedger(
                    snapshot_id=int(s.id or 0),
                    session_id=s.session_id,
                    version_id=s.version_id,
                    preference_tier="GOLD",
                    training_weight=1.0,
                    logic_school_axis=axis,
                    authority_scope_peak=peak,
                )
            )
            changed += 1
            continue
        row.preference_tier = "GOLD"
        row.training_weight = 1.0
        row.logic_school_axis = axis
        row.authority_scope_peak = peak
        row.updated_at = datetime.utcnow()
        session.add(row)
        changed += 1
    return changed


__all__ = ["ArbiterPreferenceLedger", "sync_gold_training_set"]
