"""意志 vs 系统基准的张力启发式（无 LLM），供 verdict_skeleton 风险段与审计上下文。"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Set

# 与官杀/权力场、刃冲、财印战相关的可调键（意志注塑常见）
_OFFICER_TENSION_KEYS: Set[str] = {
    "OFFICER_RESTRAINT_ALPHA",
    "L1_GOV_KILL_EFFICIENCY_LOSS",
    "L1_BLADE_CLASH_INSTABILITY",
    "POWER_DISTRIBUTION_GAMMA",
    "L1_ROBBER_WEALTH_ALLOC_LOSS",
}


def _blind_payload(plugin_outputs: Mapping[str, Any]) -> Dict[str, Any]:
    blk = plugin_outputs.get("classical.blind_school.v1")
    if not isinstance(blk, dict):
        return {}
    p = blk.get("payload")
    return dict(p) if isinstance(p, dict) else {}


def build_will_conflict_risk_lines(
    *,
    merged_physics_keys: Set[str],
    merged_interaction_keys: Set[str],
    plugin_outputs: Mapping[str, Any],
    physics_tensor: Mapping[str, Any],
) -> List[str]:
    """基于盲派做工向量与意志键名的轻量对垒提示（确定性规则）。"""
    keys = set(merged_physics_keys) | set(merged_interaction_keys)
    if not keys:
        return []
    blind = _blind_payload(plugin_outputs)
    net = str(blind.get("net_effect") or "").strip().lower()
    morph = blind.get("morphing_hints") or []
    morph_set = {str(x) for x in morph if x}
    risk_ratio = float(blind.get("risk_ratio") or 0.0)
    backfire = float(blind.get("backfire_risk") or 0.0)
    bdm = blind.get("body_damage_estimation") if isinstance(blind.get("body_damage_estimation"), dict) else {}
    crit = any(
        bool(n.get("critical_stress")) for n in (bdm.get("nodes") or []) if isinstance(n, dict)
    )
    officer_tune = bool(keys & _OFFICER_TENSION_KEYS)
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    solid_ghost = meta.get("solid_ghost_ratio")
    try:
        sg = float(solid_ghost) if solid_ghost is not None else None
    except (TypeError, ValueError):
        sg = None

    lines: List[str] = []
    if officer_tune and (net == "risk" or crit or "DANGEROUS_TURBULENCE" in morph_set or risk_ratio > 0.35):
        lines.append(
            "【意志对垒】侧车参数触及官杀/权力场相关键，而盲派做工呈 risk 或「危险湍流」体伤标记："
            "存在「意志加压」与「系统反噬张力」并存的可能，宜结合流年引动复核做功路径。"
        )
    if officer_tune and backfire > 8.0 and net != "gain":
        lines.append(
            f"【意志对垒】盲派累计 backfire_risk={backfire:.2f} 且净效应非 gain；"
            "在继续强化官杀侧参数前，建议阅读插件 unlock_advice 与墓库/穿害审计。"
        )
    if officer_tune and sg is not None and sg < 0.35:
        lines.append(
            f"【意志对垒】solid_ghost_ratio={sg:.2f} 偏低（虚实偏「虚」），与官杀侧意志叠加时叙事上须防「外强中干」式误判。"
        )
    if keys and not lines:
        lines.append(
            "【意志对垒】已记录结构化物理意志；本轮插件未返回强盲派冲突标签，仍以 VF 与审计 LLM 结论为准。"
        )
    return lines[:4]
