"""V17 插件契约：事实净化 + Inbox 决策（与主仓 qiazhi_bazi Registry 分层命名对齐，体量更轻）。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class V17Fact:
    """经插件净化后的事实；禁止承载 HTML、工程前缀或原始张量键名上屏。"""

    plugin_id: str
    text: str
    causal_tier: int
    priority: float = 0.5
    decision_hint: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class V17Decision:
    """Decision Inbox 气泡；全字段须过 NarrativeSanitizer 后再下发。"""

    id: str
    label: str
    title: str
    source: str
    priority: float


class V17PluginSpec(ABC):
    """
    V17 插件规范：
    - causal_tier: 5 最接近物理核，1 最接近叙事/话术层（与 qiazhi_bazi 门控方向一致：数值越大越“硬”）。
    - registry_priority（可选，具体类上用 dataclass 字段）：同 causal_tier 内越大越先执行，与 Admin「执行序」细排序一致。
    - collect_v17_facts: 只读 physics_tensor，返回净化事实。
    - get_pending_decisions: 默认把本插件产出且带 decision_hint 的事实映射为 Inbox 项；子类可覆盖。
    """

    plugin_id: str
    causal_tier: int = 3

    @abstractmethod
    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        """输入原始张量（dict），只输出 V17Fact；禁止 HTML / Abs 裸值 / VF. 前缀字符串。"""

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
                    label=hint,
                    title=title,
                    source=self.plugin_id,
                    priority=float(f.priority or 0.0),
                )
            )
        return out
