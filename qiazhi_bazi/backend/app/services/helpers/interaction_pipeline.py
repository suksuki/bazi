"""L1 原子交互流水线：按序执行 base 层插件并写入 physics_tensor。"""
from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

from app.core.config.physics_settings import resolve_physics_settings
from app.core.rules.junction import EnergyVaultStatus
from app.plugins.base.interactions.clash import run_clash
from app.plugins.base.interactions.combine import run_combine
from app.plugins.base.interactions.grave import run_grave
from app.plugins.base.interactions.pierce import run_pierce
from app.plugins.base.interactions.punish import run_punish
from app.skills.physics_rules import (
    SANHE_GROUPS,
    SANXING_EDGES,
    SELF_PUNISH_BRANCHES,
    STEM_TOMB_BRANCH,
)


def _pillars_blob(metadata: Any) -> Dict[str, Any]:
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


def _branch_map(pillars: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for key in ("year", "month", "day", "hour"):
        col = pillars.get(key)
        if not col:
            continue
        if isinstance(col, dict):
            b = col.get("branch")
        else:
            b = getattr(col, "branch", None)
        if b:
            out[key] = str(b)
    return out


def _day_stem(pillars: Dict[str, Any]) -> str:
    col = pillars.get("day")
    if not col:
        return ""
    if isinstance(col, dict):
        return str(col.get("stem") or "")
    return str(getattr(col, "stem", "") or "")


def _conflict_points(metadata: Any) -> List[Any]:
    cm = getattr(metadata, "conflict_matrix", None)
    if cm is None and isinstance(metadata, dict):
        cm = (metadata.get("conflict_matrix") or {})
    if cm is None:
        return []
    pts = getattr(cm, "points", None)
    if pts is not None:
        return list(pts)
    if isinstance(cm, dict):
        return list(cm.get("points") or [])
    return []


def _pos_to_pillar(pos: str) -> str:
    s = str(pos)
    if s.endswith("_branch"):
        return s.replace("_branch", "")
    return s


def evaluate_interactions(
    *,
    physics_tensor: Dict[str, Any],
    metadata: Any,
    interaction_params: Dict[str, float],
    physics_config: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """遍历 L1 原子插件，结果写入 `physics_tensor`（原地）。"""
    settings = resolve_physics_settings(physics_config or {})
    params = dict(interaction_params or {})
    by_pillar = (physics_tensor or {}).get("by_pillar") or {}

    def pillar_raw(name: str) -> float:
        block = by_pillar.get(name) or {}
        return float(block.get("raw_energy") or 0.0)

    pillars = _pillars_blob(metadata)
    branches = _branch_map(pillars)
    day_stem = _day_stem(pillars)
    points = _conflict_points(metadata)
    steps: List[Dict[str, Any]] = []

    for pt in points:
        kind = getattr(pt, "kind", None) or (pt.get("kind") if isinstance(pt, dict) else None)
        positions = getattr(pt, "positions", None) or (pt.get("positions") if isinstance(pt, dict) else None) or []
        if len(positions) < 2:
            continue
        p0, p1 = _pos_to_pillar(str(positions[0])), _pos_to_pillar(str(positions[1]))
        a0, a1 = pillar_raw(p0), pillar_raw(p1)
        if kind == "clash":
            out = run_clash(
                source_abs=a0,
                target_abs=a1,
                intensity=float(params.get("L1_CLASH_INTENSITY", 1.0)),
            )
            steps.append({"plugin": "base.clash", "edge": [p0, p1], "delta": out})
        elif kind == "combine":
            out = run_combine(
                source_abs=a0,
                target_abs=a1,
                lock_ratio=float(params.get("L1_COMBINE_LOCK_RATIO", 0.3)),
            )
            steps.append({"plugin": "base.combine", "edge": [p0, p1], "delta": out})

    for pt in points:
        kind = getattr(pt, "kind", None) or (pt.get("kind") if isinstance(pt, dict) else None)
        if kind != "harm":
            continue
        positions = getattr(pt, "positions", None) or (pt.get("positions") if isinstance(pt, dict) else None) or []
        if len(positions) < 2:
            continue
        p0, p1 = _pos_to_pillar(str(positions[0])), _pos_to_pillar(str(positions[1]))
        out = run_pierce(
            source_abs=pillar_raw(p0),
            target_abs=pillar_raw(p1),
            penetration_ratio=float(params.get("L1_PIERCE_RATIO", 0.45)),
        )
        steps.append({"plugin": "base.pierce", "edge": [p0, p1], "delta": out})

    k_san = float(params.get("L1_PUNISH_FRICTION_SANXING", 0.22))
    k_zi = float(params.get("L1_PUNISH_FRICTION_ZIXING", 0.18))
    branch_positions: Dict[str, List[str]] = {}
    for pname, br in branches.items():
        branch_positions.setdefault(br, []).append(pname)

    seen_punish: Set[Tuple[str, str]] = set()
    for b1, b2 in SANXING_EDGES:
        pnames_a = branch_positions.get(b1, [])
        pnames_b = branch_positions.get(b2, [])
        if not pnames_a or not pnames_b:
            continue
        for pa in pnames_a:
            for pb in pnames_b:
                if pa == pb:
                    continue
                edge_key = tuple(sorted((pa, pb)))
                if edge_key in seen_punish:
                    continue
                seen_punish.add(edge_key)
                out = run_punish(
                    source_abs=pillar_raw(pa),
                    target_abs=pillar_raw(pb),
                    friction_coeff=k_san,
                    mode="sanxing",
                )
                steps.append({"plugin": "base.punish", "edge": [pa, pb], "mode": "sanxing", "delta": out})

    for br, pnames in branch_positions.items():
        if br not in SELF_PUNISH_BRANCHES or len(pnames) < 2:
            continue
        for i in range(len(pnames)):
            for j in range(i + 1, len(pnames)):
                pa, pb = pnames[i], pnames[j]
                out = run_punish(
                    source_abs=pillar_raw(pa),
                    target_abs=pillar_raw(pb),
                    friction_coeff=k_zi,
                    mode="zixing",
                )
                steps.append({"plugin": "base.punish", "edge": [pa, pb], "mode": "zixing", "delta": out})

    present = frozenset(branches.values())
    composite: Dict[str, Any] = {"sanhe_clusters": []}
    for group in SANHE_GROUPS:
        if not group.issubset(present):
            continue
        cluster_abs = 0.0
        nodes: List[Dict[str, Any]] = []
        for pname, br in branches.items():
            if br in group:
                r = pillar_raw(pname)
                cluster_abs += r
                nodes.append({"pillar": pname, "branch": br, "raw_energy": round(r, 4)})
        composite["sanhe_clusters"].append(
            {
                "branches": sorted(group),
                "cluster_abs": round(cluster_abs, 4),
                "energy_vault_status": EnergyVaultStatus.AGGREGATED.value,
                "nodes": nodes,
            }
        )

    tomb_branch = STEM_TOMB_BRANCH.get(day_stem, "")
    if tomb_branch and tomb_branch in branches.values():
        tomb_pillars = [pn for pn, br in branches.items() if br == tomb_branch]
        base_abs = max((pillar_raw(pn) for pn in tomb_pillars), default=0.0)
        clash_branch_pairs: Set[Tuple[str, str]] = set()
        for pt in points:
            kind = getattr(pt, "kind", None) or (pt.get("kind") if isinstance(pt, dict) else None)
            if kind != "clash":
                continue
            positions = getattr(pt, "positions", None) or (pt.get("positions") if isinstance(pt, dict) else None) or []
            if len(positions) < 2:
                continue
            pa, pb = _pos_to_pillar(str(positions[0])), _pos_to_pillar(str(positions[1]))
            b_a, b_b = branches.get(pa, ""), branches.get(pb, "")
            clash_branch_pairs.add(tuple(sorted((b_a, b_b))))
        unlocked = any(tomb_branch in pair for pair in clash_branch_pairs if len(pair) == 2)
        burst_mult = float(settings.get("GRAVE_BURST_MULTIPLIER", 1.3))
        gout = run_grave(base_abs=base_abs, unlocked=unlocked, burst_multiplier=burst_mult)
        steps.append({"plugin": "base.grave", "tomb_branch": tomb_branch, "delta": gout})

    physics_tensor["l1_atomic_pipeline"] = {
        "version": "l1_pipeline.v1",
        "steps": steps,
    }
    physics_tensor["composite_field_impact"] = composite
    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["energy_vault_flags"] = {
            "sanhe_aggregated": len(composite.get("sanhe_clusters") or []) > 0,
        }
    return physics_tensor
