"""加载 `manifests/l1_physics_manifest.json`（进程内缓存，供 PluginRegistry 与测试复用）。"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

_MANIFEST_PATH = Path(__file__).resolve().parent / "manifests" / "l1_physics_manifest.json"


@lru_cache(maxsize=1)
def load_l1_physics_manifest() -> Dict[str, Any]:
    raw = _MANIFEST_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("l1_physics_manifest.json root must be an object")
    return data


def reload_l1_physics_manifest_for_tests() -> Dict[str, Any]:
    """单测热重载（勿在生产调用）。"""
    load_l1_physics_manifest.cache_clear()
    return load_l1_physics_manifest()
