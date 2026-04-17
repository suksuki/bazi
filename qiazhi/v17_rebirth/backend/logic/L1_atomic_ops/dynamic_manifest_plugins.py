"""V17.12：从 l1_physics_manifest.json 物化 L1 原子算子 Spec（考古占位 + 可接 meta 命中）。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from v17_rebirth.backend.logic.L1_atomic_ops.v17_op_fact import strip_score_noise
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.paths import RUNTIME_DIR

_BUILTIN_MANIFEST = Path(__file__).resolve().parent / "manifests" / "l1_physics_manifest.json"


def _manifest_paths() -> List[Path]:
    out = [RUNTIME_DIR / "l1_physics_manifest.json", _BUILTIN_MANIFEST]
    seen: set[str] = set()
    uniq: List[Path] = []
    for p in out:
        k = str(p.resolve())
        if k in seen:
            continue
        seen.add(k)
        uniq.append(p)
    return uniq


def _load_manifest_blob() -> Dict[str, Any]:
    for path in _manifest_paths():
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            continue
    return {}


class ManifestOperatorPlugin(V17PluginSpec):
    """单条 manifest 行 → 可执行 Spec；命中由 `l1_meta_hydration.hydrate_v17_physics_tensor` 写入 meta.l1_manifest_hits。"""

    __slots__ = ("plugin_id", "causal_tier", "registry_priority", "manifest_summary", "manifest_rationale", "legacy_op_id")

    def __init__(self, row: Dict[str, Any]) -> None:
        self.plugin_id = str(row.get("id") or "").strip() or "l1_manifest_unknown"
        self.causal_tier = int(row.get("causal_tier", 4))
        self.registry_priority = float(row.get("registry_priority", 0.5))
        self.manifest_summary = str(row.get("summary") or "").strip()
        self.manifest_rationale = str(row.get("rationale") or "").strip()
        self.legacy_op_id = str(row.get("legacy_op_id") or "").strip()

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        pt = physics_tensor if isinstance(physics_tensor, dict) else {}
        meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
        hits = meta.get("l1_manifest_hits")
        if not isinstance(hits, dict):
            return []
        hit = hits.get(self.plugin_id)
        if not isinstance(hit, dict):
            return []
        text = strip_score_noise(str(hit.get("fact") or "").strip())
        if not text:
            return []
        return [
            V17Fact(
                plugin_id=self.plugin_id,
                text=text,
                causal_tier=int(self.causal_tier),
                priority=float(hit.get("priority", 0.55) or 0.55),
                decision_hint=str(hit.get("label") or "").strip(),
                meta={"legacy_op_id": self.legacy_op_id} if self.legacy_op_id else {},
            )
        ]


def build_manifest_operator_specs() -> List[V17PluginSpec]:
    blob = _load_manifest_blob()
    ops = blob.get("operators")
    if not isinstance(ops, list):
        return []
    out: List[V17PluginSpec] = []
    for row in ops:
        if not isinstance(row, dict):
            continue
        pid = str(row.get("id") or "").strip()
        if not pid:
            continue
        out.append(ManifestOperatorPlugin(row))
    return out
