"""Centralized configurable physics constants for runtime injection."""
from __future__ import annotations

from typing import Any, Dict

DEFAULT_PHYSICS_SETTINGS: Dict[str, float] = {
    "WEIGHT_LUCK": 0.4,
    "WEIGHT_YEAR": 0.2,
    "BASE_BACKFIRE_RISK": 0.20,
    "HIGH_IMBALANCE_RISK": 0.35,
    "TOMB_LOCK_RATE": 0.90,
}


def resolve_physics_settings(overrides: Dict[str, Any] | None) -> Dict[str, float]:
    settings = dict(DEFAULT_PHYSICS_SETTINGS)
    for key in settings.keys():
        if overrides and key in overrides:
            try:
                settings[key] = float(overrides[key])
            except Exception:
                # Ignore invalid override and keep default.
                pass
    return settings
