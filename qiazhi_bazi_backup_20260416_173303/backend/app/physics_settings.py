"""兼容入口：文档中若引用 `app.physics_settings`，由此转发至 `app.core.config.physics_settings`。"""
from __future__ import annotations

from app.core.config.physics_settings import DEFAULT_PHYSICS_SETTINGS, resolve_physics_settings

__all__ = ["DEFAULT_PHYSICS_SETTINGS", "resolve_physics_settings"]
