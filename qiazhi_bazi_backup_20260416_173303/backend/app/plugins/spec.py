"""插件契约：Registry 挂载的统一类型与 runner 签名约定。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Literal

HookName = Literal["on_physics_complete", "on_verdict_ready"]
PluginLayer = Literal["L0", "L1", "L2", "L3", "L4"]

# 所有 runner 须接受（至少容忍）以下可选关键字，以便影子预览 / dry_run 穿透
PluginRunner = Callable[..., Dict[str, Any]]


@dataclass(frozen=True)
class PluginSpec:
    plugin_id: str
    category: str
    layer_id: PluginLayer
    label: str
    dependencies: List[str]
    priority: float
    audit_source: str
    hook: HookName
    runner: PluginRunner
