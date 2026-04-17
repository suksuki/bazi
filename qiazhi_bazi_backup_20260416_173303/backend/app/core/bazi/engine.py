"""L0 与排盘/能量场衔接入口：计算前加载元数据，提供通根共振与藏干视图。"""
from __future__ import annotations

from typing import Dict, List, Mapping, Optional, Sequence

from app.core.bazi.l0_manager import L0PluginManager


def ensure_l0_for_physics() -> None:
    """物理推断前调用：从 DB（或回退常量）装载 L0 缓存。"""
    L0PluginManager.instance().ensure_loaded()


def branch_hidden_stems_effective() -> Dict[str, Dict[str, float]]:
    return L0PluginManager.instance().get_branch_hidden_stems()


def branch_main_stem_effective() -> Dict[str, str]:
    return L0PluginManager.instance().get_branch_main_stem()


def get_root_resonance(stem: str, branches: Sequence[str], merged: Optional[Mapping[str, float]] = None) -> float:
    """
    透干通根加权：按各支藏干中该天干的占比与分层系数累加，再乘 `L0_ROOT_BOOST_FACTOR`（physics_settings / Lab）。
    """
    mgr = L0PluginManager.instance()
    mgr.ensure_loaded()
    coeffs = mgr.get_resonance_coeffs()
    hidden = mgr.get_branch_hidden_stems()
    m = merged or {}
    acc = 0.0
    st = str(stem or "")
    if not st:
        return float(m.get("L0_ROOT_BOOST_FACTOR", 1.0))
    for br in branches:
        brs = str(br)
        row = hidden.get(brs, {})
        if st not in row:
            continue
        ratio = float(row[st]) / 100.0
        tier = mgr.hidden_tier(brs, st).upper()
        w = float(coeffs.get(f"ROOT_TIER_{tier}", coeffs.get("ROOT_TIER_MAIN", 1.0)))
        acc += ratio * w * 0.18
    fac = 1.0 + min(0.45, acc)
    fac *= float(m.get("L0_ROOT_BOOST_FACTOR", 1.0))
    return max(0.55, min(2.0, fac))


def blend_position_weights_l0(
    base: Mapping[str, float],
    merged: Optional[Mapping[str, float]],
) -> Dict[str, float]:
    """年月 vs 日时：`L0_YM_DH_WEIGHT_RATIO` >1 增强年月柱相对权重，再归一化。"""
    if not merged:
        return {k: float(v) for k, v in base.items()}
    r = float(merged.get("L0_YM_DH_WEIGHT_RATIO", 1.0))
    r = max(0.25, min(4.0, r))
    out = {k: float(v) for k, v in base.items()}
    for k in ("year", "month"):
        if k in out:
            out[k] *= r
    for k in ("day", "hour"):
        if k in out:
            out[k] /= r
    s = sum(out.values()) or 1.0
    return {k: out[k] / s for k in out}
