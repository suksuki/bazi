"""Chronos V2：流年/大运支与原局支的合、冲、刑引动 → audit_log TEMPORAL_TRIGGER。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Tuple

from app.skills.physics_rules import SANXING_EDGES

PLUGIN_ID = "base.chronos.v2"

_SIX_CLASH: frozenset[frozenset[str]] = frozenset(
    frozenset(p)
    for p in (
        ("子", "午"),
        ("丑", "未"),
        ("寅", "申"),
        ("卯", "酉"),
        ("辰", "戌"),
        ("巳", "亥"),
    )
)

_SIX_COMBINE: frozenset[frozenset[str]] = frozenset(
    frozenset(p)
    for p in (
        ("子", "丑"),
        ("寅", "亥"),
        ("卯", "戌"),
        ("辰", "酉"),
        ("巳", "申"),
        ("午", "未"),
    )
)


def _utc_audit_ts() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_ganzhi(g: str) -> Tuple[str, str]:
    s = (g or "").strip()
    if len(s) < 2:
        return "", ""
    ch = list(s)
    return str(ch[0]), str(ch[1])


def _natal_branches(pillars: Mapping[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for key in ("year", "month", "day", "hour"):
        col = pillars.get(key)
        if not col:
            continue
        if isinstance(col, dict):
            b = str(col.get("branch") or "")
        else:
            b = str(getattr(col, "branch", "") or "")
        if b:
            out[key] = b
    return out


def _pillars_from_metadata(metadata: Any) -> Dict[str, Any]:
    if metadata is None:
        return {}
    p = getattr(metadata, "pillars", None)
    if p is None and isinstance(metadata, dict):
        p = metadata.get("pillars")
    if p is None:
        return {}
    if hasattr(p, "model_dump"):
        return p.model_dump()
    if isinstance(p, dict):
        return p
    return {}


def _temporal_context(metadata: Any) -> Dict[str, Any]:
    if hasattr(metadata, "model_dump"):
        d = metadata.model_dump()
    elif isinstance(metadata, dict):
        d = metadata
    else:
        d = {}
    tc = d.get("temporal_context")
    return tc if isinstance(tc, dict) else {}


def _detect_triggers(flow_branches: List[str], natal: Mapping[str, str]) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for fb in flow_branches:
        if not fb:
            continue
        for pname, nb in natal.items():
            if not nb:
                continue
            pair = frozenset({fb, nb})
            if pair in _SIX_CLASH:
                hits.append(
                    {
                        "kind": "CLASH",
                        "natal_pillar": pname,
                        "natal_branch": nb,
                        "flow_branch": fb,
                        "detail": f"{nb}{fb}冲",
                    }
                )
            elif pair in _SIX_COMBINE:
                hits.append(
                    {
                        "kind": "COMBINE",
                        "natal_pillar": pname,
                        "natal_branch": nb,
                        "flow_branch": fb,
                        "detail": f"{nb}{fb}合",
                    }
                )
            for b1, b2 in SANXING_EDGES:
                if {b1, b2} == {fb, nb}:
                    hits.append(
                        {
                            "kind": "SANXING",
                            "natal_pillar": pname,
                            "natal_branch": nb,
                            "flow_branch": fb,
                            "detail": f"{nb}与{fb}刑",
                        }
                    )
                    break
    return hits


def append_temporal_trigger_audits(
    *,
    physics_tensor: MutableMapping[str, Any],
    metadata: Any,
    branches: Mapping[str, str],
    settings: Mapping[str, float],
) -> List[Dict[str, Any]]:
    if float(settings.get("CHRONOS_V2_TEMPORAL_ENABLE", 1.0)) < 0.5:
        return []

    tc = _temporal_context(metadata)
    pillars = _pillars_from_metadata(metadata)
    natal = branches if branches else _natal_branches(pillars)

    flow_branches: List[str] = []
    for key in ("liunian_ganzhi", "dayun_ganzhi"):
        raw = str(tc.get(key) or "").strip()
        if not raw:
            continue
        _, br = _parse_ganzhi(raw)
        if br:
            flow_branches.append(br)

    if not flow_branches or not natal:
        return []

    triggers = _detect_triggers(flow_branches, natal)
    if not triggers:
        return []

    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["chronos_v2_temporal"] = {
            "version": "chronos_temporal.v1",
            "triggers": triggers,
            "flow_branches": flow_branches,
        }

    ts = _utc_audit_ts()
    rows: List[Dict[str, Any]] = []
    for i, tr in enumerate(triggers):
        rows.append(
            {
                "id": f"temporal-trigger-{i + 1:02d}",
                "step": "CH-V2",
                "role": "Chronos",
                "action": f"TEMPORAL_TRIGGER · {tr.get('detail', tr.get('kind', ''))}",
                "timestamp": ts,
                "payload": {
                    "type": "TEMPORAL_TRIGGER",
                    "plugin": PLUGIN_ID,
                    "kind": tr.get("kind"),
                    "natal_pillar": tr.get("natal_pillar"),
                    "natal_branch": tr.get("natal_branch"),
                    "flow_branch": tr.get("flow_branch"),
                    "detail": tr.get("detail"),
                },
            }
        )
    return rows
