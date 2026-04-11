"""
全局物理/决策配置入口（兼容路径）。

单一数据源仍为 `app.core.config.physics_settings`；此处仅做便捷 re-export。
"""
from __future__ import annotations

from app.core.config.physics_settings import DEFAULT_PHYSICS_SETTINGS, resolve_physics_settings

GLOBAL_DECISION_ABS_THRESHOLD = float(DEFAULT_PHYSICS_SETTINGS["GLOBAL_DECISION_ABS_THRESHOLD"])

__all__ = [
    "DEFAULT_PHYSICS_SETTINGS",
    "GLOBAL_DECISION_ABS_THRESHOLD",
    "resolve_physics_settings",
]
