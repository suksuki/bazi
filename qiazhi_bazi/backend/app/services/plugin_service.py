"""插件调度：对 PluginRegistry 的稳定封装，供 Orchestrator 与其它服务复用。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.plugins.registry import PluginRegistry


class PluginService:
    """遍历已挂载插件（经 Registry 的 hook 机制）；不负责物理引擎与语义翻译。"""

    def __init__(self, registry: Optional[PluginRegistry] = None) -> None:
        self._registry = registry or PluginRegistry()

    @property
    def registry(self) -> PluginRegistry:
        return self._registry

    def run_on_physics_complete(
        self,
        *,
        enabled_plugins: List[str],
        physics_tensor: Dict[str, Any],
        metadata: Dict[str, Any],
        blind_school_features: Dict[str, Any],
    ) -> Dict[str, Any]:
        """对当前 `enabled_plugins` 执行 `on_physics_complete`（含 L0 常驻等 Registry 规则）。"""
        return self._registry.run_hook(
            hook="on_physics_complete",
            enabled_plugins=list(enabled_plugins or []),
            context={
                "physics_tensor": physics_tensor,
                "metadata": metadata,
                "blind_school_features": blind_school_features,
            },
        )

    def list_specs(self) -> List[Dict[str, Any]]:
        return self._registry.list_specs()
