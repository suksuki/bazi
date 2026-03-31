"""MVP 数据表：Consultation / DecisionChain / KnowledgeBase。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlmodel import Field, SQLModel


class Consultation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subject_ref: Optional[str] = None
    basic_info_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(SQLITE_JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DecisionChain(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    consultation_id: Optional[int] = Field(default=None, index=True)
    step_name: str = Field(index=True)
    decision_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(SQLITE_JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeBase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source: str = Field(index=True)
    title: str
    content: str
    tags_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(SQLITE_JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
