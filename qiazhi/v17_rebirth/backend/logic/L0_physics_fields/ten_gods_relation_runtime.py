from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set


def append_relation_trace(
    relation_traces: List[Dict[str, Any]],
    kind: str,
    members: List[str],
    pillars: List[str],
    intensity: float,
    relation_element: str = "",
    *,
    family_key: str = "",
    duplicate_bonus: float = 0.0,
    conflict_damping: float = 1.0,
    completion: float = 1.0,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    payload: Dict[str, Any] = {
        "kind": kind,
        "family_key": str(family_key or kind),
        "members": [str(x) for x in members if str(x).strip()],
        "pillars": [str(x) for x in pillars if str(x).strip()],
        "intensity": round(float(intensity), 4),
        "relation_element": str(relation_element or ""),
        "duplicate_bonus": round(float(duplicate_bonus or 0.0), 4),
        "conflict_damping": round(float(conflict_damping or 0.0), 4),
        "completion": round(float(completion or 0.0), 4),
    }
    if isinstance(details, dict):
        payload["details"] = dict(details)
        payload.update(details)
    relation_traces.append(payload)


def collect_conflict_sets(
    *,
    chong_hits: List[Dict[str, Any]],
    hai_hits: List[Dict[str, Any]],
    po_hits: List[Dict[str, Any]],
    xing_hits: List[Dict[str, Any]],
) -> tuple[Set[str], List[Set[str]]]:
    conflicted_branches: Set[str] = set()
    conflict_events: List[Set[str]] = []
    for hit in chong_hits:
        pair = {str(x) for x in (hit.get("pair") or []) if str(x).strip()}
        conflicted_branches.update(pair)
        if pair:
            conflict_events.append(pair)
    for hit in hai_hits:
        pair = {str(x) for x in (hit.get("pair") or []) if str(x).strip()}
        conflicted_branches.update(pair)
        if pair:
            conflict_events.append(pair)
    for hit in po_hits:
        pair = {str(x) for x in (hit.get("pair") or []) if str(x).strip()}
        conflicted_branches.update(pair)
        if pair:
            conflict_events.append(pair)
    for hit in xing_hits:
        members = {str(x) for x in (hit.get("branches") or []) if str(x).strip()}
        conflicted_branches.update(members)
        if members:
            conflict_events.append(members)
    return conflicted_branches, conflict_events


def detect_relation_runtime_hits(
    branches: Dict[str, str],
    *,
    eval_sanhe_hits: Callable[[Dict[str, str]], List[Dict[str, Any]]],
    eval_sanhui_hits: Callable[[Dict[str, str]], List[Dict[str, Any]]],
    eval_banhe_hits: Callable[[Dict[str, str]], List[Dict[str, Any]]],
    eval_gonghe_hits: Callable[[Dict[str, str]], List[Dict[str, Any]]],
    eval_liuhe_hits: Callable[[Dict[str, str]], List[Dict[str, Any]]],
    eval_anhe_hits: Callable[[Dict[str, str]], List[Dict[str, Any]]],
    eval_liu_chong_hits: Callable[[Dict[str, str]], List[Dict[str, Any]]],
    eval_liu_hai_hits: Callable[[Dict[str, str]], List[Dict[str, Any]]],
    eval_liu_po_hits: Callable[[Dict[str, str]], List[Dict[str, Any]]],
    sanxing_detect_geometry: Callable[[Dict[str, str]], List[Dict[str, Any]]],
) -> Dict[str, Any]:
    sanhe_hits = eval_sanhe_hits(branches)
    sanhui_hits = eval_sanhui_hits(branches)
    banhe_hits = eval_banhe_hits(branches)
    gonghe_hits = eval_gonghe_hits(branches)
    liuhe_hits = eval_liuhe_hits(branches)
    anhe_hits = eval_anhe_hits(branches)
    chong_hits = eval_liu_chong_hits(branches)
    hai_hits = eval_liu_hai_hits(branches)
    po_hits = eval_liu_po_hits(branches)
    xing_hits = sanxing_detect_geometry(branches)
    conflicted_branches, conflict_events = collect_conflict_sets(
        chong_hits=chong_hits,
        hai_hits=hai_hits,
        po_hits=po_hits,
        xing_hits=xing_hits,
    )
    return {
        "sanhe_hits": sanhe_hits,
        "sanhui_hits": sanhui_hits,
        "banhe_hits": banhe_hits,
        "gonghe_hits": gonghe_hits,
        "liuhe_hits": liuhe_hits,
        "anhe_hits": anhe_hits,
        "chong_hits": chong_hits,
        "hai_hits": hai_hits,
        "po_hits": po_hits,
        "xing_hits": xing_hits,
        "conflicted_branches": conflicted_branches,
        "conflict_events": conflict_events,
    }
