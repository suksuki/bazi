"""V17 插件契约：事实净化 + Inbox 决策。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class ArbiterType(str, Enum):
    SYSTEM = "system"  # 确定性规则裁决
    LLM = "llm"        # 智能语义仲裁
    USER = "user"      # 终端用户终审

class AuditStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

@dataclass(frozen=True)
class V17Fact:
    """经插件净化后的事实。"""
    text: str
    causal_tier: int = 1
    priority: float = 0.5
    salience_weight: float = 1.0
    suggested_arbiter: ArbiterType = ArbiterType.SYSTEM
    decision_hint: Optional[str] = None
    target_god: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)
    plugin_id: Optional[str] = None

    @property
    def source(self) -> str:
        return self.plugin_id or ""

@dataclass
class V17Decision:
    """
    V17.99：代表法庭上的一份“待裁决案卷”。
    只有 AuditStatus.APPROVED 的决策，其物理后果才会被固化。
    """
    id: str
    title: str
    label: str
    hint: str
    priority: float = 0.5
    target_god: str = ""
    arbiter_type: ArbiterType = ArbiterType.SYSTEM
    status: AuditStatus = AuditStatus.PENDING
    physical_impact: Dict[str, Any] = field(default_factory=dict)
    causal_tier: int = 3
    applied: bool = False
    plugin_id: Optional[str] = None

    @property
    def source(self) -> str:
        return self.plugin_id or ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "plugin_id": self.plugin_id,
            "title": self.title,
            "label": self.label,
            "hint": self.hint,
            "priority": self.priority,
            "arbiter_type": self.arbiter_type.value,
            "status": self.status.value,
            "physical_impact": self.physical_impact,
            "causal_tier": self.causal_tier
        }

class V17PluginSpec(ABC):
    """
    V17 插件规范。
    """
    plugin_id: str
    causal_tier: int = 3

    @abstractmethod
    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        """输入原始张量，只输出 V17Fact。"""

    def get_pending_decisions(self, facts: List[V17Fact]) -> List[V17Decision]:
        out: List[V17Decision] = []
        for i, f in enumerate(facts):
            if f.plugin_id != self.plugin_id:
                continue
            hint = str(f.decision_hint or "").strip()
            if not hint:
                continue
            title = str(f.text or "").strip() or "建议动作"
            out.append(
                V17Decision(
                    id=f"{self.plugin_id}_{i}",
                    plugin_id=self.plugin_id,
                    label=hint,
                    title=title,
                    hint=hint, # 兼容老字段
                    priority=float(f.priority or 0.5),
                    causal_tier=f.causal_tier,
                    arbiter_type=f.suggested_arbiter,
                    physical_impact=dict(f.meta) if isinstance(f.meta, dict) else {},
                )
            )
        return out
