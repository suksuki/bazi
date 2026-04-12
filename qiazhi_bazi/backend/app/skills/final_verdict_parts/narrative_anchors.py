"""终判正文段落与四柱 / conflict_point 的弱锚点（启发式，供 Debug 联动）。"""
from __future__ import annotations

import re
from typing import Any, Dict, List

_BRANCH_CHARS = "子丑寅卯辰巳午未申酉戌亥"


def build_verdict_narrative_chunks(verdict_body: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not verdict_body or not str(verdict_body).strip():
        return []
    parts = [p.strip() for p in re.split(r"\n\s*\n+", str(verdict_body)) if p.strip()]
    pillars_meta = (metadata or {}).get("pillars") or {}
    points = (((metadata or {}).get("conflict_matrix") or {}).get("points") or [])

    out: List[Dict[str, Any]] = []
    for j, para in enumerate(parts):
        branches_in = [c for c in _BRANCH_CHARS if c in para]
        pillar_keys: List[str] = []
        if isinstance(pillars_meta, dict):
            for pk in ("year", "month", "day", "hour"):
                col = pillars_meta.get(pk)
                br = col.get("branch") if isinstance(col, dict) else None
                if br and str(br) in para:
                    pillar_keys.append(pk)
        cids: List[str] = []
        for idx, p in enumerate(points):
            if not isinstance(p, dict):
                continue
            pid = str(p.get("id") or f"cp_{idx}")
            did = str(p.get("detail") or "")
            pos_s = " ".join(str(x) for x in (p.get("positions") or []))
            hit = any(c in did or c in pos_s for c in branches_in)
            if hit:
                cids.append(pid)
        out.append(
            {
                "chunk_id": f"n{j}",
                "text": para[:8000],
                "branch_chars": branches_in[:16],
                "pillar_keys": pillar_keys,
                "conflict_point_ids": sorted(set(cids))[:24],
            }
        )
    return out
