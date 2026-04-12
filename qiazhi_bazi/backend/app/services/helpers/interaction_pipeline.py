"""L1 原子交互流水线：按序执行 base 层插件并写入 physics_tensor。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from app.core.config.physics_settings import resolve_physics_settings
from app.core.rules.junction import EnergyVaultStatus, build_l1_operator_audit_items_from_steps, sync_l1_junction_flags_to_meta
from app.plugins.base.interactions.l1_atomic_plugin import run_l1_atomic_plugin_pool
from app.plugins.base_physics.core_operators.core_conflict_runner import apply_l1_core_conflict_operators
from app.plugins.base_physics.core_operators.op_stem_fusion import apply_op_stem_fusion
from app.plugins.base_physics.core_operators.op_sub_branch_interaction import (
    apply_op_sub_branch_interaction,
    clamp_node_metric_for_entropy,
    verify_sanhe_phi_consistency,
)
from app.core.routing.pattern_recognition_router import evaluate_pattern_profile
from app.services.helpers.flow_auditor import apply_energy_flow_audit
from app.plugins.base_physics.core_operators.op_status import apply_l1_status_to_physics_tensor
from app.services.helpers.sys_core_physics_plugin import SYS_CORE_PHYSICS_BUNDLE_SRC_KEY
from app.plugins.chronos.core import run_chronos_plugin
from app.plugins.chronos.temporal_v2 import append_temporal_trigger_audits
from app.plugins.base_physics.core_operators.op_interdimensional import compute_solid_ghost_ratio
from app.skills.physics_rules import TEN_DEITIES


def _utc_audit_ts() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _refresh_deity_axis_percentages(physics_tensor: Dict[str, Any]) -> None:
    axes = physics_tensor.get("deity_energy_axes")
    if not isinstance(axes, dict):
        return
    total = sum(
        float((axes.get(d) or {}).get("absolute_energy") or 0.0) for d in TEN_DEITIES if isinstance(axes.get(d), dict)
    ) or 1.0
    for d in TEN_DEITIES:
        blk = axes.get(d)
        if isinstance(blk, dict):
            ae = float(blk.get("absolute_energy") or 0.0)
            blk["relative_percentage"] = round(100.0 * ae / total, 2)


def _reconcile_robber_wealth_under_pattern_sovereignty(physics_tensor: Dict[str, Any]) -> None:
    """从格等格局主权：在 pattern_profile 已定型后，撤销劫财见财对正财 Abs 的损耗记账（与 CausalRouter 反转一致）。"""
    meta = physics_tensor.get("meta")
    if not isinstance(meta, dict):
        return
    pp = meta.get("pattern_profile")
    rw = meta.get("l1_robber_wealth_v1")
    if not isinstance(pp, dict) or not pp.get("sovereignty_priority"):
        return
    if not isinstance(rw, dict) or rw.get("sovereignty_gain"):
        return
    pk = str(pp.get("pattern_kind") or "")
    if not pk.startswith("cong_"):
        return
    axes = physics_tensor.get("deity_energy_axes")
    before = rw.get("正财_abs_before")
    if isinstance(axes, dict) and isinstance(axes.get("正财"), dict) and before is not None:
        try:
            axes["正财"]["absolute_energy"] = round(float(before), 4)
        except (TypeError, ValueError):
            pass
    meta["l1_robber_wealth_v1"] = {
        **rw,
        "sovereignty_gain": True,
        "alloc_loss_effective": 0.0,
        "note": "格局主权(从势)：劫财见财之 L1 损耗在格局层纠偏为主权增益记账",
    }
    meta["PATTERN_SOVEREIGNTY_PROTECTION"] = {
        "active": True,
        "pattern_kind": pk,
        "scope": "l1_robber_wealth_alloc",
    }
    _refresh_deity_axis_percentages(physics_tensor)


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


def _ganzhi_branch_char(ganzhi: str) -> str:
    """标准干支字符串取地支（末字）。"""
    s = (ganzhi or "").strip()
    if len(s) < 2:
        return ""
    return str(s[-1])


def _branch_map_natal(pillars: Dict[str, Any]) -> Dict[str, str]:
    """四柱地支键（year/month/day/hour）。"""
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


def _branch_map_extended(pillars: Dict[str, Any], metadata: Any, settings: Dict[str, Any]) -> Dict[str, str]:
    """
    地支池：默认四柱；`SANHE_INCLUDE_TEMPORAL_BRANCHES`≥0.5 时并入 `temporal_context` 的大运/流年支
    （键 `dayun` / `liunian`），供三合全支与 `is_sanhe_triggered` 使用。
    """
    out = _branch_map_natal(pillars)
    if float(settings.get("SANHE_INCLUDE_TEMPORAL_BRANCHES", 1.0)) < 0.5:
        return out
    tc: Dict[str, Any] = {}
    if metadata is not None:
        if hasattr(metadata, "model_dump"):
            raw = metadata.model_dump().get("temporal_context")
            tc = raw if isinstance(raw, dict) else {}
        elif isinstance(metadata, dict):
            raw = metadata.get("temporal_context")
            tc = raw if isinstance(raw, dict) else {}
    dy = str(tc.get("dayun_ganzhi") or "").strip()
    if dy:
        b = _ganzhi_branch_char(dy)
        if b:
            out["dayun"] = b
    ln = str(tc.get("liunian_ganzhi") or "").strip()
    if ln:
        b = _ganzhi_branch_char(ln)
        if b:
            out["liunian"] = b
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

    m_clamp = clamp_node_metric_for_entropy(composite=composite, steps=steps, branches=branches)

    clash_loss = 0.0
    for s in steps:
        if s.get("plugin") != "base.clash":
            continue
        clash_loss += float((s.get("delta") or {}).get("abs_loss") or 0.0)
    m_clash = min(1.0, clash_loss / ref_clash)

    blade_raw = 0.0
    for s in steps:
        if s.get("plugin") != "base.core_conflict.blade_clash":
            continue
        blade_raw += float((s.get("delta") or {}).get("instability_score") or 0.0)
    w_blade = float(params.get("ENTROPY_W_BLADE", 0.25))
    ref_blade = max(1e-6, float(params.get("ENTROPY_BLADE_REF", 0.6)))
    m_blade = min(1.0, blade_raw / ref_blade)

    raw = w_t * m_torque + w_c * m_clamp + w_k * m_clash + w_blade * m_blade
    damp = float(params.get("governance_constraint_damping", 1.0))
    damp = max(0.0, min(2.0, damp))
    entropy = max(0.0, min(1.0, raw * damp))
    return {
        "value": round(entropy, 4),
        "metrics": {
            "m_torque": round(m_torque, 4),
            "m_clamp": round(m_clamp, 4),
            "m_clash": round(m_clash, 4),
            "m_blade_instability": round(m_blade, 4),
            "blade_instability_raw": round(blade_raw, 4),
            "torque_total": round(torque_total, 4),
            "clash_abs_loss_total": round(clash_loss, 4),
            "raw_entropy_mix": round(raw, 4),
            "governance_constraint_damping": round(damp, 4),
        },
    }


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
    for _ek in ("ENTROPY_W_BLADE", "ENTROPY_BLADE_REF"):
        if _ek not in params:
            params[_ek] = float(settings.get(_ek, 0.25 if _ek == "ENTROPY_W_BLADE" else 0.6))
    by_pillar = (physics_tensor or {}).get("by_pillar") or {}

    def pillar_raw(name: str) -> float:
        block = by_pillar.get(name) or {}
        return float(block.get("raw_energy") or 0.0)

    pillars = _pillars_blob(metadata)
    branches = _branch_map_extended(pillars, metadata, settings)
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
    sanhe_protocol_audits = list(composite.get("sanhe_protocol_audits") or [])
    status_steps = apply_l1_status_to_physics_tensor(physics_tensor=physics_tensor, metadata=metadata, settings=settings)
    conflict_steps = apply_l1_core_conflict_operators(
        physics_tensor=physics_tensor,
        metadata=metadata,
        settings=settings,
        conflict_points=points,
        physics_config=physics_config,
    )
    fusion_steps = apply_op_stem_fusion(physics_tensor=physics_tensor, metadata=metadata, settings=settings)
    combined_steps = list(steps) + list(status_steps or []) + list(conflict_steps or []) + list(fusion_steps or [])
    combined_steps.extend(
        apply_op_sub_branch_interaction(
            physics_tensor=physics_tensor,
            metadata=metadata,
            settings=settings,
            combined_steps=list(combined_steps),
            composite=composite,
            branches=branches,
            pillars=pillars,
        )
    )
    clamp_on = float(params.get("L1_SANHE_PHI_CLAMP", 1.0)) >= 1.0

    consistency = verify_sanhe_phi_consistency(
        clusters=list(composite.get("sanhe_clusters") or []),
        steps=combined_steps,
        clamp_on=clamp_on,
    )

    audit = physics_tensor.setdefault("audit_log", {})
    if isinstance(audit, dict):
        if sanhe_protocol_audits:
            audit["sanhe_protocol_audits"] = sanhe_protocol_audits
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
        temporal_rows = append_temporal_trigger_audits(
            physics_tensor=physics_tensor,
            metadata=metadata,
            branches=branches,
            settings=settings,
        )
        audit["l1_operator_audit_items"] = l1_rows + chrono_rows + temporal_rows
        audit["dimensional_shield_logs"] = list(dimensional_shield_logs or [])

    physics_tensor[SYS_CORE_PHYSICS_BUNDLE_SRC_KEY] = {
        "composite_field_impact": composite,
        "l1_atomic_pipeline": {
            "version": "l1_pipeline.v1",
            "steps": combined_steps,
            "composite_consistency_check": consistency,
        },
    }
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
        sc_gate = [c for c in (composite.get("sanhe_clusters") or []) if isinstance(c, dict)]
        sync_l1_junction_flags_to_meta(
            metadata=md,
            physics_tensor=physics_tensor,
            physics_settings=settings,
            sanhe_clusters_precomputed=sc_gate,
        )
        apply_energy_flow_audit(physics_tensor=physics_tensor, physics_config=physics_config)
        evaluate_pattern_profile(physics_tensor=physics_tensor, metadata=md, settings=settings)
        _reconcile_robber_wealth_under_pattern_sovereignty(physics_tensor)
    return physics_tensor
