"""Centralized configurable physics constants for runtime injection."""
from __future__ import annotations

from typing import Any, Dict

DEFAULT_PHYSICS_SETTINGS: Dict[str, float] = {
    "WEIGHT_LUCK": 0.4,
    "WEIGHT_YEAR": 0.2,
    "BASE_BACKFIRE_RISK": 0.20,
    "HIGH_IMBALANCE_RISK": 0.35,
    "TOMB_LOCK_RATE": 0.90,
    "GRAVE_BURST_MULTIPLIER": 1.3,
    "ENABLE_CLIMATE_HARD_FACTOR": 1.0,
    "CLIMATE_INTENSITY": 1.0,
    "STEM_RESONANCE_BOOST": 1.5,
    "TRANSFER_DISTANCE_DECAY": 0.1,
    "WORK_MIN_THRESHOLD": 0.5,
    "SHOW_WEAK_WORK_PATHS": 0.0,
    # 盲派六穿（害）：η 下限，高于普通「害」档（见 blind_work_evaluator.ETA_MAP）
    "MANGPAI_SIX_HARM_ETA": 0.99,
    # 盲派微模块 η：可独立调参（pierce 默认与 MANGPAI_SIX_HARM_ETA 对齐）
    "MANGPAI_ETA_PIERCE": 0.99,
    # 默认与 TOMB_LOCK_RATE 一致；可在 overrides 中单独覆盖 MANGPAI_ETA_TOMB
    "MANGPAI_ETA_TOMB": 0.90,
    "MANGPAI_ETA_HOST_GUEST": 1.0,
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
    # 墓库微模块 η 未单独覆盖时，与全局 TOMB_LOCK_RATE 对齐
    if not overrides or "MANGPAI_ETA_TOMB" not in overrides:
        settings["MANGPAI_ETA_TOMB"] = float(settings["TOMB_LOCK_RATE"])
    # 穿局 η 未单独覆盖时，与兼容键 MANGPAI_SIX_HARM_ETA 对齐
    if not overrides or "MANGPAI_ETA_PIERCE" not in overrides:
        settings["MANGPAI_ETA_PIERCE"] = float(settings["MANGPAI_SIX_HARM_ETA"])
    return settings
