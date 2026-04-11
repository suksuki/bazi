"""L1 原子交互流水线：按序执行 base 层插件并写入 physics_tensor。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Set

from app.core.config.physics_settings import resolve_physics_settings
from app.core.rules.junction import EnergyVaultStatus, build_l1_operator_audit_items_from_steps, sync_l1_junction_flags_to_meta
from app.plugins.base.interactions.l1_atomic_plugin import run_l1_atomic_plugin_pool
from app.plugins.base_physics.core_operators.op_status import apply_l1_status_to_physics_tensor
from app.plugins.chronos.core import run_chronos_plugin
from app.plugins.base_physics.core_operators.op_interdimensional import compute_solid_ghost_ratio


def _utc_audit_ts() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def _clamp_node_metric(
    *,
    composite: Dict[str, Any],
    steps: List[Dict[str, Any]],
    branches: Dict[str, str],
) -> float:
    """AGGREGATED 或墓库 LOCKED 所触及柱位占四柱比例，归一化到 0..1。"""
    touched: Set[str] = set()
    for cl in composite.get("sanhe_clusters") or []:
        for node in cl.get("nodes") or []:
            p = str(node.get("pillar") or "")
            if p:
                touched.add(p)
    for s in steps:
        if s.get("plugin") != "base.grave":
            continue
        d = s.get("delta") or {}
        if str(d.get("energy_vault_status") or "") != EnergyVaultStatus.LOCKED.value:
            continue
        tb = str(s.get("tomb_branch") or "")
        for pname, br in branches.items():
            if br == tb:
                touched.add(pname)
    return min(1.0, len(touched) / 4.0)


def _synthesize_global_entropy(
    *,
    params: Dict[str, float],
    steps: List[Dict[str, Any]],
    audit: Dict[str, Any],
    composite: Dict[str, Any],
    branches: Dict[str, str],
) -> Dict[str, Any]:
    """L1 审计指标加权合成全局熵，系数来自 interaction_params。"""
    w_t = float(params.get("ENTROPY_W_TORQUE", 0.4))
    w_c = float(params.get("ENTROPY_W_CLAMP", 0.3))
    w_k = float(params.get("ENTROPY_W_CLASH", 0.3))
    ref_torque = max(1e-6, float(params.get("ENTROPY_TORQUE_REF", 180.0)))
    ref_clash = max(1e-6, float(params.get("ENTROPY_CLASH_REF", 160.0)))

    torque_total = float(audit.get("l1_impact_torque_total") or 0.0)
    m_torque = min(1.0, torque_total / ref_torque)

    m_clamp = _clamp_node_metric(composite=composite, steps=steps, branches=branches)

    clash_loss = 0.0
    for s in steps:
        if s.get("plugin") != "base.clash":
            continue
        clash_loss += float((s.get("delta") or {}).get("abs_loss") or 0.0)
    m_clash = min(1.0, clash_loss / ref_clash)

    raw = w_t * m_torque + w_c * m_clamp + w_k * m_clash
    damp = float(params.get("governance_constraint_damping", 1.0))
    damp = max(0.0, min(2.0, damp))
    entropy = max(0.0, min(1.0, raw * damp))
    return {
        "value": round(entropy, 4),
        "metrics": {
            "m_torque": round(m_torque, 4),
            "m_clamp": round(m_clamp, 4),
            "m_clash": round(m_clash, 4),
            "torque_total": round(torque_total, 4),
            "clash_abs_loss_total": round(clash_loss, 4),
            "raw_entropy_mix": round(raw, 4),
            "governance_constraint_damping": round(damp, 4),
        },
    }


def _composite_consistency_check(
    *,
    clusters: List[Dict[str, Any]],
    steps: List[Dict[str, Any]],
    clamp_on: bool,
) -> Dict[str, Any]:
    """校验：AGGREGATED 节点在流水线上 φ 显式为 0，除非对应 cluster 已标记解锁。"""
    gates = [
        s
        for s in steps
        if s.get("plugin") == "composite.aggregated_phi"
    ]
    if not clamp_on:
        return {"ok": True, "reasons": [], "phi_gate_count": len(gates), "skipped_clamp": True}
    ok = True
    reasons: List[str] = []
    for cl in clusters:
        if (cl.get("energy_vault_status") or "") != EnergyVaultStatus.AGGREGATED.value:
            continue
        unlocked = bool(cl.get("cluster_phi_unlock", False))
        for node in cl.get("nodes") or []:
            pname = str(node.get("pillar") or "")
            found = [g for g in gates if g.get("pillar") == pname]
            if not found:
                ok = False
                reasons.append(f"missing_phi_gate:{pname}")
                continue
            phi = float(found[0].get("phi_work", -1.0))
            if clamp_on and not unlocked and phi != 0.0:
                ok = False
                reasons.append(f"phi_not_zero:{pname}")
            if clamp_on and unlocked and phi != 1.0:
                ok = False
                reasons.append(f"phi_not_released:{pname}")
    return {"ok": ok, "reasons": reasons, "phi_gate_count": len(gates)}


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
    for k in ("L1_OP_PROD_ETA", "L1_OP_DEST_ETA", "L1_OP_CONN_ETA"):
        if k not in params:
            params[k] = float(settings.get(k, 1.0))
    _idim_keys = (
        "INTERDIMENSIONAL_CONDUCTIVITY",
        "INTERDIMENSIONAL_BARRIER_STRENGTH",
        "CONDUCTIVITY_DECAY_RATE",
        "GHOST_ENERGY_DAMPING",
        "MANGPAI_ETA_DIMENSIONAL_CRUSH",
        "MANGPAI_ROOT_RESONANCE",
        "INTERDIMENSIONAL_SHIELD_ENABLE",
        "STEM_BRANCH_ROOT_RESONANCE_ENABLE",
        "STEM_BRANCH_VERTICAL_CRUSH_ENABLE",
    )
    for _k in _idim_keys:
        if _k not in params:
            params[_k] = float(settings.get(_k, 0.0))
    by_pillar = (physics_tensor or {}).get("by_pillar") or {}

    def pillar_raw(name: str) -> float:
        block = by_pillar.get(name) or {}
        return float(block.get("raw_energy") or 0.0)

    pillars = _pillars_blob(metadata)
    branches = _branch_map(pillars)
    day_stem = _day_stem(pillars)
    points = _conflict_points(metadata)
    steps, punish_torque_trace, composite, dimensional_shield_logs = run_l1_atomic_plugin_pool(
        points=points,
        branches=branches,
        pillars=pillars,
        day_stem=day_stem,
        pillar_raw=pillar_raw,
        params=params,
        settings=settings,
    )
    status_steps = apply_l1_status_to_physics_tensor(physics_tensor=physics_tensor, metadata=metadata, settings=settings)
    combined_steps = list(steps) + list(status_steps or [])
    clamp_on = float(params.get("L1_SANHE_PHI_CLAMP", 1.0)) >= 1.0

    consistency = _composite_consistency_check(
        clusters=list(composite.get("sanhe_clusters") or []),
        steps=combined_steps,
        clamp_on=clamp_on,
    )

    audit = physics_tensor.setdefault("audit_log", {})
    if isinstance(audit, dict):
        audit["l1_punish_torque_trace"] = punish_torque_trace
        audit["l1_impact_torque_total"] = round(
            sum(float(x.get("impact_torque") or 0.0) for x in punish_torque_trace),
            4,
        )
        l1_rows = build_l1_operator_audit_items_from_steps(combined_steps, timestamp=_utc_audit_ts())
        chrono_out = run_chronos_plugin(
            physics_tensor=physics_tensor,
            metadata=metadata,
            physics_config=physics_config,
        )
        chrono_rows = list(chrono_out.get("audit_items") or [])
        audit["chronos_audit_items"] = chrono_rows
        audit["l1_operator_audit_items"] = l1_rows + chrono_rows
        audit["dimensional_shield_logs"] = list(dimensional_shield_logs or [])

    physics_tensor["l1_atomic_pipeline"] = {
        "version": "l1_pipeline.v1",
        "steps": combined_steps,
        "composite_consistency_check": consistency,
    }
    physics_tensor["composite_field_impact"] = composite
    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["energy_vault_flags"] = {
            "sanhe_aggregated": len(composite.get("sanhe_clusters") or []) > 0,
        }
        grave_locked = any(
            s.get("plugin") == "base.grave"
            and (s.get("delta") or {}).get("energy_vault_status") == EnergyVaultStatus.LOCKED.value
            for s in combined_steps
        )
        agg_clamps_work = False
        if clamp_on:
            for cl in composite.get("sanhe_clusters") or []:
                if (cl.get("energy_vault_status") or "") == EnergyVaultStatus.AGGREGATED.value and not cl.get(
                    "cluster_phi_unlock", False
                ):
                    agg_clamps_work = True
                    break
        meta["work_eligible"] = not (agg_clamps_work or grave_locked)
        synth = _synthesize_global_entropy(
            params=params,
            steps=combined_steps,
            audit=audit if isinstance(audit, dict) else {},
            composite=composite,
            branches=branches,
        )
        meta["global_entropy"] = synth["value"]
        meta["global_entropy_metrics"] = synth["metrics"]
        meta["solid_ghost_ratio"] = compute_solid_ghost_ratio(
            steps=combined_steps,
            dimensional_shield_logs=list(dimensional_shield_logs or []),
            ghost_damping=float(settings.get("GHOST_ENERGY_DAMPING", 0.3)),
        )
        md = metadata.model_dump() if hasattr(metadata, "model_dump") else dict(metadata or {})
        sync_l1_junction_flags_to_meta(
            metadata=md, physics_tensor=physics_tensor, physics_settings=settings
        )
    return physics_tensor
