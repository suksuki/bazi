"""L1 atomic plugin pool executor."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Set, Tuple

from app.core.rules.junction import EnergyVaultStatus
from app.plugins.base.interactions.clash import run_clash
from app.plugins.base.interactions.combine import run_combine
from app.plugins.base.interactions.grave import run_grave
from app.plugins.base.interactions.pierce import run_pierce
from app.plugins.base.interactions.punish import run_punish
from app.skills.physics_rules import SANHE_GROUPS, SANXING_EDGES, SELF_PUNISH_BRANCHES, STEM_TOMB_BRANCH


def _pos_to_pillar(pos: str) -> str:
    s = str(pos)
    if s.endswith("_branch"):
        return s.replace("_branch", "")
    return s


def _cluster_touched_by_clash(*, group: frozenset[str], points: List[Any], branches: Dict[str, str]) -> bool:
    for pt in points:
        kind = getattr(pt, "kind", None) or (pt.get("kind") if isinstance(pt, dict) else None)
        if kind != "clash":
            continue
        positions = getattr(pt, "positions", None) or (pt.get("positions") if isinstance(pt, dict) else None) or []
        if len(positions) < 2:
            continue
        pa, pb = _pos_to_pillar(str(positions[0])), _pos_to_pillar(str(positions[1]))
        b_a, b_b = branches.get(pa, ""), branches.get(pb, "")
        if b_a in group or b_b in group:
            return True
    return False


def _run_pairwise_plugins(
    *,
    points: List[Any],
    pillar_raw: Callable[[str], float],
    params: Dict[str, float],
) -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    handler_map: Dict[str, Callable[[float, float], Dict[str, Any]]] = {
        "clash": lambda a0, a1: run_clash(
            source_abs=a0,
            target_abs=a1,
            intensity=float(params.get("L1_CLASH_INTENSITY", 1.0)),
        ),
        "combine": lambda a0, a1: run_combine(
            source_abs=a0,
            target_abs=a1,
            lock_ratio=float(params.get("L1_COMBINE_LOCK_RATIO", 0.3)),
        ),
        "harm": lambda a0, a1: run_pierce(
            source_abs=a0,
            target_abs=a1,
            penetration_ratio=float(params.get("L1_PIERCE_RATIO", 0.45)),
        ),
    }
    plugin_name_map = {"clash": "base.clash", "combine": "base.combine", "harm": "base.pierce"}

    for pt in points:
        kind = getattr(pt, "kind", None) or (pt.get("kind") if isinstance(pt, dict) else None)
        runner = handler_map.get(str(kind))
        if not runner:
            continue
        positions = getattr(pt, "positions", None) or (pt.get("positions") if isinstance(pt, dict) else None) or []
        if len(positions) < 2:
            continue
        p0, p1 = _pos_to_pillar(str(positions[0])), _pos_to_pillar(str(positions[1]))
        out = runner(pillar_raw(p0), pillar_raw(p1))
        steps.append({"plugin": plugin_name_map[str(kind)], "edge": [p0, p1], "delta": out})
    return steps


def _run_punish_plugin(
    *,
    branches: Dict[str, str],
    pillar_raw: Callable[[str], float],
    params: Dict[str, float],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    steps: List[Dict[str, Any]] = []
    torque_trace: List[Dict[str, Any]] = []
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
                torque_trace.append({"edge": [pa, pb], "mode": "sanxing", "impact_torque": out.get("impact_torque")})

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
                torque_trace.append({"edge": [pa, pb], "mode": "zixing", "impact_torque": out.get("impact_torque")})
    return steps, torque_trace


def _run_composite_plugins(
    *,
    branches: Dict[str, str],
    points: List[Any],
    pillar_raw: Callable[[str], float],
    day_stem: str,
    params: Dict[str, float],
    settings: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
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
        clash_unlock = float(params.get("L1_SANHE_PHI_UNLOCK_ON_CLASH", 1.0)) >= 1.0
        force_unlock = float(params.get("L1_SANHE_FORCE_PHI_UNLOCK", 0.0)) >= 1.0
        cluster_phi_unlock = force_unlock or (clash_unlock and _cluster_touched_by_clash(group=group, points=points, branches=branches))
        composite["sanhe_clusters"].append(
            {
                "branches": sorted(group),
                "cluster_abs": round(cluster_abs, 4),
                "energy_vault_status": EnergyVaultStatus.AGGREGATED.value,
                "nodes": nodes,
                "cluster_phi_unlock": cluster_phi_unlock,
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

    clamp_on = float(params.get("L1_SANHE_PHI_CLAMP", 1.0)) >= 1.0
    if clamp_on:
        for cl in composite.get("sanhe_clusters") or []:
            if (cl.get("energy_vault_status") or "") != EnergyVaultStatus.AGGREGATED.value:
                continue
            unlocked = bool(cl.get("cluster_phi_unlock", False))
            for node in cl.get("nodes") or []:
                pname = str(node.get("pillar") or "")
                br = str(node.get("branch") or "")
                phi_work = 0.0 if not unlocked else 1.0
                steps.append(
                    {
                        "plugin": "composite.aggregated_phi",
                        "pillar": pname,
                        "branch": br,
                        "phi_work": phi_work,
                        "energy_vault_status": EnergyVaultStatus.AGGREGATED.value,
                        "cluster_unlock": unlocked,
                    }
                )
    return steps, composite


def run_l1_atomic_plugin_pool(
    *,
    points: List[Any],
    branches: Dict[str, str],
    day_stem: str,
    pillar_raw: Callable[[str], float],
    params: Dict[str, float],
    settings: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    punish_torque_trace: List[Dict[str, Any]] = []
    composite: Dict[str, Any] = {"sanhe_clusters": []}

    pair_steps = _run_pairwise_plugins(points=points, pillar_raw=pillar_raw, params=params)
    steps.extend(pair_steps)

    punish_steps, torque_trace = _run_punish_plugin(branches=branches, pillar_raw=pillar_raw, params=params)
    steps.extend(punish_steps)
    punish_torque_trace.extend(torque_trace)

    composite_steps, composite = _run_composite_plugins(
        branches=branches,
        points=points,
        pillar_raw=pillar_raw,
        day_stem=day_stem,
        params=params,
        settings=settings,
    )
    steps.extend(composite_steps)

    return steps, punish_torque_trace, composite
