"""L1 atomic plugin pool executor."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Set, Tuple

from app.core.rules.junction import EnergyVaultStatus
from app.plugins.base.interactions.clash import run_clash
from app.plugins.base.interactions.combine import run_combine
from app.plugins.base.interactions.grave import run_grave
from app.plugins.base.interactions.pierce import run_pierce
from app.plugins.base.interactions.punish import run_punish
from app.plugins.base_physics.core_operators import op_connection, op_destruction, op_interdimensional, op_production
from app.plugins.base_physics.skill_manifest_loader import skill_id_for_l1_operator
from app.plugins.base_physics.core_operators.op_interdimensional import StemBranchCouplingEngine
from app.skills.physics_rules import SANHE_GROUPS, SANXING_EDGES, SELF_PUNISH_BRANCHES, STEM_TOMB_BRANCH


def _pos_to_pillar(pos: str) -> str:
    s = str(pos)
    if s.endswith("_branch"):
        return s.replace("_branch", "")
    if s.endswith("_stem"):
        return s.replace("_stem", "")
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
    pillars: Dict[str, Any],
    branches: Dict[str, str],
    pillar_raw: Callable[[str], float],
    params: Dict[str, float],
    settings: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    steps: List[Dict[str, Any]] = []
    shield_logs: List[str] = []
    stems_map: Dict[str, str] = {}
    for k in ("year", "month", "day", "hour"):
        col = pillars.get(k)
        if not col:
            continue
        if isinstance(col, dict):
            st = col.get("stem")
        else:
            st = getattr(col, "stem", None)
        if st:
            stems_map[k] = str(st)
    eta_prod = float(params.get("L1_OP_PROD_ETA", 1.0))
    eta_dest = float(params.get("L1_OP_DEST_ETA", 1.0))
    eta_conn = float(params.get("L1_OP_CONN_ETA", 1.0))
    idim_alpha = float(params.get("INTERDIMENSIONAL_CONDUCTIVITY", 0.0))
    merged_cfg: Dict[str, float] = {**{k: float(v) for k, v in (settings or {}).items()}, **params}
    coupling = StemBranchCouplingEngine(
        pillars=pillars,
        stems_by_pillar=stems_map,
        branches_by_pillar=branches,
        merged_config=merged_cfg,
    )
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

    for i, pt in enumerate(points):
        kind = getattr(pt, "kind", None) or (pt.get("kind") if isinstance(pt, dict) else None)
        runner = handler_map.get(str(kind))
        if not runner:
            continue
        positions = getattr(pt, "positions", None) or (pt.get("positions") if isinstance(pt, dict) else None) or []
        if len(positions) < 2:
            continue
        p0, p1 = _pos_to_pillar(str(positions[0])), _pos_to_pillar(str(positions[1]))
        raw = runner(pillar_raw(p0), pillar_raw(p1))
        kind_str = str(kind)
        if kind_str == "clash":
            out = op_destruction.apply_eta(raw, eta_dest)
            out = op_production.apply_eta(out, eta_prod)
            op_ids = [op_destruction.OP_ID, op_production.OP_ID]
            skill_ids_pair = [skill_id_for_l1_operator(op_destruction.OP_ID), skill_id_for_l1_operator(op_production.OP_ID)]
            primary = op_destruction.OP_ID
        elif kind_str == "harm":
            out = op_destruction.apply_eta(raw, eta_dest)
            op_ids = [op_destruction.OP_ID]
            skill_ids_pair = [skill_id_for_l1_operator(op_destruction.OP_ID)]
            primary = op_destruction.OP_ID
        elif kind_str == "combine":
            out = op_connection.apply_eta(raw, eta_conn)
            op_ids = [op_connection.OP_ID]
            skill_ids_pair = [skill_id_for_l1_operator(op_connection.OP_ID)]
            primary = op_connection.OP_ID
        else:
            out = raw
            op_ids = []
            skill_ids_pair = []
            primary = None

        step_extra: Dict[str, Any] = {}
        pair = op_interdimensional.resolve_stem_branch_pair(
            str(positions[0]), str(positions[1]), pillars=pillars
        )
        if pair is not None:
            stem_n, branch_n = pair
            activation_pts = [points[j] for j in range(len(points)) if j != i]
            c_phys, eff = coupling.effective_conductivity(
                stem_n,
                branch_n,
                interdimensional_alpha=idim_alpha,
                activation_conflict_points=activation_pts,
            )
            abs_before_dim = float(out.get("abs_loss") or 0.0)
            locked_before = float(out.get("abs_locked") or 0.0)
            if eff < 1.0:
                if kind_str == "combine":
                    op_interdimensional.scale_delta_abs_locked(out, eff)
                else:
                    op_interdimensional.scale_delta_abs_loss(out, eff)
            if kind_str == "clash" and coupling.root_penetration_resonance_active(stem_n, branch_n):
                coupling.apply_resonance_abs_gain(out)
            step_extra = {"conductivity_physics": c_phys, "conductivity_effective": eff}
            loss_after = float(out.get("abs_loss") or 0.0)
            locked_after = float(out.get("abs_locked") or 0.0)
            sg = str(stem_n.get("stem") or "?")
            bg = str(branch_n.get("branch") or "?")
            heavily_damped = abs_before_dim > 1e-9 and loss_after < 0.12 * max(abs_before_dim, 1e-9)
            if eff < 1e-9 and (abs_before_dim > 1e-9 or locked_before > 1e-9) and (loss_after < 1e-9 and locked_after < 1e-9):
                shield_logs.append(op_interdimensional.shield_log_line(sg, bg))
                step_extra["dimensional_shield"] = True
            elif eff < 0.1 and heavily_damped:
                shield_logs.append(op_interdimensional.shield_log_line(sg, bg))
                step_extra["dimensional_shield"] = True

        step: Dict[str, Any] = {
            "plugin": plugin_name_map[kind_str],
            "edge": [p0, p1],
            "delta": out,
            "l1_operator_ids": op_ids,
            **step_extra,
        }
        if skill_ids_pair:
            step["skill_ids"] = skill_ids_pair
        if primary:
            step["l1_operator_id"] = primary
        steps.append(step)
    return steps, shield_logs


def _run_punish_plugin(
    *,
    branches: Dict[str, str],
    pillar_raw: Callable[[str], float],
    params: Dict[str, float],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    steps: List[Dict[str, Any]] = []
    torque_trace: List[Dict[str, Any]] = []
    eta_dest = float(params.get("L1_OP_DEST_ETA", 1.0))
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
                raw = run_punish(
                    source_abs=pillar_raw(pa),
                    target_abs=pillar_raw(pb),
                    friction_coeff=k_san,
                    mode="sanxing",
                )
                out = op_destruction.apply_eta(raw, eta_dest)
                steps.append(
                    {
                        "plugin": "base.punish",
                        "edge": [pa, pb],
                        "mode": "sanxing",
                        "delta": out,
                        "l1_operator_id": op_destruction.OP_ID,
                        "l1_operator_ids": [op_destruction.OP_ID],
                        "skill_ids": [skill_id_for_l1_operator(op_destruction.OP_ID)],
                    }
                )
                torque_trace.append({"edge": [pa, pb], "mode": "sanxing", "impact_torque": out.get("impact_torque")})

    for br, pnames in branch_positions.items():
        if br not in SELF_PUNISH_BRANCHES or len(pnames) < 2:
            continue
        for i in range(len(pnames)):
            for j in range(i + 1, len(pnames)):
                pa, pb = pnames[i], pnames[j]
                raw = run_punish(
                    source_abs=pillar_raw(pa),
                    target_abs=pillar_raw(pb),
                    friction_coeff=k_zi,
                    mode="zixing",
                )
                out = op_destruction.apply_eta(raw, eta_dest)
                steps.append(
                    {
                        "plugin": "base.punish",
                        "edge": [pa, pb],
                        "mode": "zixing",
                        "delta": out,
                        "l1_operator_id": op_destruction.OP_ID,
                        "l1_operator_ids": [op_destruction.OP_ID],
                        "skill_ids": [skill_id_for_l1_operator(op_destruction.OP_ID)],
                    }
                )
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
        steps.append(
            {
                "plugin": "base.grave",
                "tomb_branch": tomb_branch,
                "delta": gout,
                "l1_operator_id": "L1_OP_GRAVE",
                "l1_operator_ids": ["L1_OP_GRAVE"],
                "skill_ids": [skill_id_for_l1_operator("L1_OP_GRAVE")],
            }
        )

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
                        "l1_operator_id": "L1_OP_PHI_CLAMP",
                        "l1_operator_ids": ["L1_OP_PHI_CLAMP"],
                        "skill_ids": [skill_id_for_l1_operator("L1_OP_PHI_CLAMP")],
                    }
                )
    return steps, composite


def run_l1_atomic_plugin_pool(
    *,
    points: List[Any],
    branches: Dict[str, str],
    pillars: Dict[str, Any],
    day_stem: str,
    pillar_raw: Callable[[str], float],
    params: Dict[str, float],
    settings: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any], List[str]]:
    steps: List[Dict[str, Any]] = []
    punish_torque_trace: List[Dict[str, Any]] = []
    composite: Dict[str, Any] = {"sanhe_clusters": []}

    merged_for_coupling: Dict[str, float] = {**{k: float(v) for k, v in settings.items()}, **params}
    stems_fix: Dict[str, str] = {}
    for k in ("year", "month", "day", "hour"):
        col = pillars.get(k)
        if not col:
            continue
        if isinstance(col, dict):
            st = col.get("stem")
        else:
            st = getattr(col, "stem", None)
        if st:
            stems_fix[k] = str(st)
    coupling_pool = StemBranchCouplingEngine(
        pillars=pillars,
        stems_by_pillar=stems_fix,
        branches_by_pillar=branches,
        merged_config=merged_for_coupling,
    )

    pair_steps, dimensional_shield_logs = _run_pairwise_plugins(
        points=points,
        pillars=pillars,
        branches=branches,
        pillar_raw=pillar_raw,
        params=params,
        settings=settings,
    )
    steps.extend(pair_steps)

    vertical_steps = coupling_pool.vertical_crush_steps(pillar_raw)
    steps.extend(vertical_steps)

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

    return steps, punish_torque_trace, composite, dimensional_shield_logs
