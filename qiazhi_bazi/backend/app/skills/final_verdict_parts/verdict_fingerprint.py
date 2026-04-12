"""终判 Markdown 尾部隐藏指纹：柱能快照 + 生效插件列表（供模型升级后审计对比）。"""
from __future__ import annotations

import base64
import json
from typing import Any, Dict


def build_pillar_energy_snapshot(physics_tensor: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    by_pillar = (physics_tensor or {}).get("by_pillar") if isinstance((physics_tensor or {}).get("by_pillar"), dict) else {}
    pillars = (metadata or {}).get("pillars") if isinstance((metadata or {}).get("pillars"), dict) else {}
    for k in ("year", "month", "day", "hour"):
        snap: Dict[str, Any] = {"raw_energy": None, "energy_value": None}
        blk = by_pillar.get(k) if isinstance(by_pillar.get(k), dict) else {}
        if isinstance(blk, dict) and blk.get("raw_energy") is not None:
            try:
                snap["raw_energy"] = float(blk.get("raw_energy"))
            except (TypeError, ValueError):
                pass
        col = pillars.get(k) if isinstance(pillars.get(k), dict) else {}
        if col.get("energy_value") is not None:
            try:
                snap["energy_value"] = int(col.get("energy_value"))
            except (TypeError, ValueError):
                pass
        out[k] = snap
    return out


def build_active_plugins_list(physics_tensor: Dict[str, Any]) -> List[str]:
    meta = (physics_tensor or {}).get("meta") if isinstance((physics_tensor or {}).get("meta"), dict) else {}
    raw = meta.get("enabled_plugins")
    if isinstance(raw, list):
        return [str(x) for x in raw if x is not None and str(x).strip()]
    return []


def append_verdict_fingerprint_html_comment(
    verdict_body: str,
    *,
    physics_tensor: Dict[str, Any],
    metadata: Dict[str, Any],
) -> str:
    """在 Markdown 末尾追加隐藏 HTML 注释；载荷为 URL-Safe Base64(JSON)，避免 `--` 破坏注释。"""
    fp: Dict[str, Any] = {
        "schema": "qiazhi.verdict_fingerprint.v1",
        "pillar_energy_snapshot": build_pillar_energy_snapshot(physics_tensor, metadata),
        "active_plugins": build_active_plugins_list(physics_tensor),
    }
    raw = json.dumps(fp, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    b64 = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    body = (verdict_body or "").rstrip()
    return f"{body}\n\n<!--qiazhi-fingerprint:v1 {b64}-->\n"
