"""V17.12：与旧 registry `_register_defaults` 对齐的 L0 占位 Spec。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

PLUGIN_SUMMARY = "Registry parity L0：base.chronos 与 sys.core.physics 占位。"
PLUGIN_RATIONALE = "与旧 PluginRegistry 插件 ID 对齐；事实由全量物理管线渐进接入。"


@dataclass
class BaseChronosStub(V17PluginSpec):
    plugin_id: str = "base.chronos"
    causal_tier: int = 5
    registry_priority: float = 0.94
    doc_summary: str = "时空权重（司令 / 余气）：旧版 base.chronos 入口。"
    doc_rationale: str = "因果序优先于 classical；与 chronos 张量写回衔接。"

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return []


@dataclass
class SysCorePhysicsStub(V17PluginSpec):
    plugin_id: str = "sys.core.physics"
    causal_tier: int = 5
    registry_priority: float = 0.996
    doc_summary: str = "L0 物理引擎总线（sys.core.physics）占位。"
    doc_rationale: str = "旧链路口依赖 base.physics_l1；V17 以 L1 manifest 算子替代。"

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return []


PLUGINS: List[V17PluginSpec] = [BaseChronosStub(), SysCorePhysicsStub()]
