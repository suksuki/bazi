"""运行时配置：由 Admin 保存，用户端推演直接读取。"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


def _default_llm() -> Dict[str, Any]:
    return {
        "base_url": (os.getenv("QIAZHI_BAZI_LLM_BASE_URL") or "").rstrip("/"),
        "api_key": os.getenv("QIAZHI_BAZI_LLM_API_KEY", ""),
        "model": os.getenv("QIAZHI_BAZI_LLM_MODEL", ""),
        "provider": os.getenv("QIAZHI_LLM_PROVIDER", "ollama"),
        # 物理审计 LLM：compact 缩短 system/user、压缩盲派注册表，利于弱模型输出合法 JSON
        "audit_prompt_tier": (os.getenv("QIAZHI_AUDIT_PROMPT_TIER", "compact") or "compact").strip().lower(),
        # 终判 Prompt：开启后 plugin evidence 不做碎片化截断，走全量逻辑溯源（强模型日切）
        "is_high_reasoning_mode": (
            str(os.getenv("QIAZHI_LLM_HIGH_REASONING", "") or "").strip().lower() in ("1", "true", "yes")
        ),
        "narrative_strategy": (os.getenv("QIAZHI_NARRATIVE_STRATEGY", "assertion_tree") or "assertion_tree").strip(),
        # V13.08：终判单次 LLM 超时（秒）；弱模型大 JSON 时过短易触发前端 [SYSTEM_FALLBACK]
        "final_verdict_timeout_s": float((os.getenv("QIAZHI_FINAL_VERDICT_TIMEOUT_S", "") or "30").strip() or 30),
    }


_DEFAULT_ROUTING: Dict[str, Any] = {
    "conflict_strategy": "conservative",
    "school_sovereignty": False,
    "priority_base_physics": 100,
    "priority_blind_school": 80,
    "layer_L1": 100,
    "layer_L2": 80,
}

_DEFAULT_BRAIN: Dict[str, Any] = {
    # V12.94：低于该 global_entropy 才可能走 AUTO_LLM（仍须黄金账本模式命中）
    "auto_arbiter_max_entropy": float((os.getenv("QIAZHI_AUTO_ARBITER_ENTROPY_MAX", "") or "0.3").strip() or 0.3),
}


def _default_config() -> Dict[str, Any]:
    return {
        "llm": _default_llm(),
        "causal_routing": dict(_DEFAULT_ROUTING),
        "brain": dict(_DEFAULT_BRAIN),
    }


_CONFIG_FILE = Path(__file__).resolve().parents[2] / "runtime_config.json"


def get_runtime_config() -> Dict[str, Any]:
    if not _CONFIG_FILE.exists():
        return _default_config()
    try:
        data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return _default_config()
        merged = _default_config()
        merged.update(data)
        llm = _default_llm()
        if isinstance(merged.get("llm"), dict):
            llm.update(merged["llm"])
        merged["llm"] = llm
        cr = dict(_DEFAULT_ROUTING)
        raw_cr = merged.get("causal_routing")
        if isinstance(raw_cr, dict):
            cr.update(raw_cr)
        merged["causal_routing"] = cr
        br = dict(_DEFAULT_BRAIN)
        raw_br = merged.get("brain")
        if isinstance(raw_br, dict):
            br.update(raw_br)
        merged["brain"] = br
        return merged
    except Exception:
        return _default_config()


def set_runtime_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    current = get_runtime_config()
    merged = dict(current)
    merged.update(payload)
    if "llm" in payload and isinstance(payload["llm"], dict):
        llm = dict(current.get("llm", {}))
        llm.update(payload["llm"])
        merged["llm"] = llm
    if "causal_routing" in payload and isinstance(payload["causal_routing"], dict):
        base_cr = dict(current.get("causal_routing") or _DEFAULT_ROUTING)
        base_cr.update(payload["causal_routing"])
        merged["causal_routing"] = base_cr
    if "brain" in payload and isinstance(payload["brain"], dict):
        base_br = dict(current.get("brain") or _DEFAULT_BRAIN)
        base_br.update(payload["brain"])
        merged["brain"] = base_br
    _CONFIG_FILE.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged
