"""Skill protocol base classes and audit schema."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from pydantic import BaseModel, Field


class AuditLog(BaseModel):
    skill_id: str
    skill_version: str
    param_version_id: str
    formula_refs: list[str] = Field(default_factory=list)
    param_snapshot: Dict[str, float] = Field(default_factory=dict)
    trace: Dict[str, Any] = Field(default_factory=dict)


class BaseSkill(ABC):
    skill_id: str = "base_skill"
    skill_version: str = "0.0.0"

    @abstractmethod
    def consume(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Read required upstream context, validate dependencies."""

    @abstractmethod
    def produce(self, consumed: Dict[str, Any]) -> Dict[str, Any]:
        """Produce normalized output payload."""

    @abstractmethod
    def audit(self, consumed: Dict[str, Any], produced: Dict[str, Any]) -> AuditLog:
        """Emit an auditable computation chain."""
