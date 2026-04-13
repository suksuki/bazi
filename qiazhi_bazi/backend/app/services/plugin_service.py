"""插件调度：对 PluginRegistry 的稳定封装，供 Orchestrator 与其它服务复用。"""
from __future__ import annotations

import copy
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
        is_preview: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """对当前 `enabled_plugins` 执行 `on_physics_complete`（含 L0 常驻等 Registry 规则）。"""
        return self._registry.run_hook(
            hook="on_physics_complete",
            enabled_plugins=list(enabled_plugins or []),
            context={
                "physics_tensor": physics_tensor,
                "metadata": metadata,
                "blind_school_features": blind_school_features,
                "is_preview": bool(is_preview),
                "dry_run": bool(dry_run),
            },
        )

    def dry_run_on_physics_complete(
        self,
        *,
        enabled_plugins: List[str],
        physics_tensor: Dict[str, Any],
        metadata: Dict[str, Any],
        blind_school_features: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        真正的 dry_run：深拷贝入参后再跑插件链，调用方张量不变；
        `is_preview`/`dry_run` 置真，供插件侧抑制或标注持久化相关副作用（Orchestrator 仍负责跳过 trace 落库）。
        返回 ``plugin_outputs``（各插件 hook 输出）与 ``physics_tensor``（链上突变后的深拷贝）。
        """
        pt = copy.deepcopy(physics_tensor)
        md = copy.deepcopy(metadata)
        bf: Any = (
            copy.deepcopy(blind_school_features)
            if isinstance(blind_school_features, dict)
            else blind_school_features
        )
        outputs = self.run_on_physics_complete(
            enabled_plugins=enabled_plugins,
            physics_tensor=pt,
            metadata=md,
            blind_school_features=bf if isinstance(bf, dict) else {},
            is_preview=True,
            dry_run=True,
        )
        return {"plugin_outputs": outputs, "physics_tensor": pt}

    def list_specs(self) -> List[Dict[str, Any]]:
        return self._registry.list_specs()
