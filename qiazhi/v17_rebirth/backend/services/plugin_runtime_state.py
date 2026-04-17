"""V17 Admin：各插件最近一次 Facts 输出（内存态，进程重启清空）。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class _PluginRuntimeRow:
    causal_tier: int = 3
    last_facts: List[str] = field(default_factory=list)
    last_at: str = ""


_RUNTIME: Dict[str, _PluginRuntimeRow] = {}


def record_plugin_run(*, plugin_id: str, causal_tier: int, fact_texts: List[str]) -> None:
    pid = str(plugin_id or "").strip() or "unknown"
    row = _RUNTIME.setdefault(pid, _PluginRuntimeRow())
    row.causal_tier = int(causal_tier)
    row.last_facts = [str(t).strip() for t in fact_texts if str(t).strip()][:64]
    row.last_at = datetime.now(timezone.utc).isoformat()


def snapshot_runtime() -> Dict[str, Any]:
    return {
        "plugins": [
            {
                "plugin_id": k,
                "causal_tier": v.causal_tier,
                "last_facts": list(v.last_facts),
                "last_at": v.last_at,
            }
            for k, v in sorted(_RUNTIME.items(), key=lambda kv: (-kv[1].causal_tier, kv[0]))
        ]
    }


def merge_registry_with_runtime(registry_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """把 discovery 静态清单与运行时 last_facts 合并。"""
    rt = {p["plugin_id"]: p for p in snapshot_runtime().get("plugins", []) if isinstance(p, dict)}
    out: List[Dict[str, Any]] = []
    for row in registry_rows:
        rid = str(row.get("plugin_id", "")).strip()
        extra = rt.get(rid, {})
        facts = extra.get("last_facts") or row.get("last_facts") or []
        if not isinstance(facts, list):
            facts = []
        merged = {**row, "last_facts": facts}
        merged["last_at"] = extra.get("last_at") or row.get("last_at") or ""
        merged["causal_tier"] = int(extra.get("causal_tier") or row.get("causal_tier") or 3)
        merged["activated"] = bool([t for t in facts if str(t).strip()])
        out.append(merged)
    return out
