"""Consultation + DecisionStep：存过程，不单存结果。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel

# SQLite 用 JSON；PostgreSQL 可用 JSONB
_JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class Consultation(SQLModel, table=True):
    """单次测算主记录。"""

    __tablename__ = "consultation"

    id: Optional[int] = Field(default=None, primary_key=True)
    subject_ref: Optional[str] = Field(default=None, index=True)
    # 公历/真太阳时等由前端传入，MVP 用 JSON 存原始输入
    input_meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(_JSON_TYPE))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DecisionStep(SQLModel, table=True):
    """推演链上的一步：类型 + 当时物理快照 + 人裁决。"""

    __tablename__ = "decision_step"

    id: Optional[int] = Field(default=None, primary_key=True)
    consultation_id: int = Field(foreign_key="consultation.id", index=True)
    step_type: str = Field(
        index=True,
        description="如：旺衰判定、墓库确认、刑冲扫描",
    )
    raw_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(_JSON_TYPE),
        description="该步当时的物理指标/中间态",
    )
    human_choice: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(_JSON_TYPE),
        description="裁决人打钩/选项结果",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
