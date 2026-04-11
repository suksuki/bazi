"""运行时配置：由 Admin 保存，用户端推演直接读取。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

_DEFAULT = {
    "llm": {
        "base_url": "http://192.168.0.10:11434/v1",
        "api_key": "ollama",
        "model": "",
        "provider": "ollama",
    },
    "causal_routing": {
        "conflict_strategy": "conservative",
        "school_sovereignty": False,
        "priority_base_physics": 100,
        "priority_blind_school": 80,
        "layer_L1": 100,
        "layer_L2": 80,
    },
}

_CONFIG_FILE = Path(__file__).resolve().parents[2] / "runtime_config.json"


def get_runtime_config() -> Dict[str, Any]:
    if not _CONFIG_FILE.exists():
        return dict(_DEFAULT)
    try:
        data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return dict(_DEFAULT)
        merged = dict(_DEFAULT)
        merged.update(data)
        if "llm" in merged and isinstance(_DEFAULT["llm"], dict):
            llm = dict(_DEFAULT["llm"])
            llm.update(merged.get("llm", {}))
            merged["llm"] = llm
        if "causal_routing" in merged and isinstance(_DEFAULT.get("causal_routing"), dict):
            cr = dict(_DEFAULT["causal_routing"])
            raw_cr = merged.get("causal_routing")
            if isinstance(raw_cr, dict):
                cr.update(raw_cr)
            merged["causal_routing"] = cr
        return merged
    except Exception:
        return dict(_DEFAULT)


def set_runtime_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    current = get_runtime_config()
    merged = dict(current)
    merged.update(payload)
    if "llm" in payload and isinstance(payload["llm"], dict):
        llm = dict(current.get("llm", {}))
        llm.update(payload["llm"])
        merged["llm"] = llm
    if "causal_routing" in payload and isinstance(payload["causal_routing"], dict):
        base_cr = dict(current.get("causal_routing") or _DEFAULT.get("causal_routing") or {})
        base_cr.update(payload["causal_routing"])
        merged["causal_routing"] = base_cr
    _CONFIG_FILE.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged
