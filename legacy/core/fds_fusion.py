"""
FDS 2.5：流形重心坍缩 (Manifold Centroid Collapse)
=================================================
将前 K 个格局的 D_M 与质心做指数归一化加权，得到合成 5D 张量 P_final；
并据此计算宏观指数：财富、事业、健康（0-100），供判词与全息页展示。
SOP V6.9：高级语义映射 — 社交、学研、风险，由 config advanced_macro_mapping 控制。
SOP V6.10：逻辑回归平滑 — Sigmoid 映射替代线性/截断，分数集中在 30-80 理性区间。
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.engine import load_static_atlas

DIM_ORDER = ["E", "O", "M", "S", "R"]


def _sigmoid_score(v: float, v_mid: float, k: float) -> float:
    """
    SOP V6.10：Score = 100 / (1 + exp(-k*(V - V_mid)))，再裁剪到 [0, 100]。
    使普通样本落在 45-65，小富/小成 75-85，极值才接近 0 或 100。
    """
    if k <= 0:
        k = 0.8
    try:
        x = -k * (float(v) - float(v_mid))
        if x > 100:
            return 100.0
        if x < -100:
            return 0.0
        return 100.0 / (1.0 + math.exp(x))
    except Exception:
        return 50.0


def _load_dynamic_manifold_config() -> Dict[str, Any]:
    try:
        root = Path(__file__).resolve().parent.parent
        path = root / "config" / "dynamic_manifold.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _vec_5d(x: Any) -> List[float]:
    if isinstance(x, (list, tuple)) and len(x) >= 5:
        return [float(x[i]) for i in range(5)]
    if isinstance(x, dict):
        return [float(x.get(k, 0)) for k in DIM_ORDER]
    return [0.0] * 5


def calculate_manifold_fusion_tensor(
    overlay: List[Dict[str, Any]],
    atlas: Optional[Dict[str, Any]] = None,
    top_k: int = 3,
) -> Dict[str, float]:
    """
    流形重心坍缩：取前 K 个格局的 D_M 与质心，指数归一化权重 W_i = exp(-D_M,i)/Σexp(-D_M,j)，
    合成 5D 张量 P_final = Σ(W_i * C_i)。
    """
    atlas = atlas or load_static_atlas()
    patterns = atlas.get("patterns") or []
    pid_to_centroid: Dict[str, List[float]] = {}
    for p in patterns:
        pid = (p.get("pattern_id") or "").strip()
        cen = p.get("centroid_5d")
        if pid and cen:
            pid_to_centroid[pid] = _vec_5d(cen)

    taken = []
    for item in overlay[:top_k]:
        pid = (item.get("pattern_id") or "").strip()
        d_m = float(item.get("D_M", 0.0))
        cen = pid_to_centroid.get(pid)
        if cen is not None:
            taken.append((d_m, cen))

    if not taken:
        return {k: 0.0 for k in DIM_ORDER}

    d_vals = [t[0] for t in taken]
    d_max = max(d_vals)
    exp_vals = [math.exp(-(d - d_max)) for d in d_vals]
    total = sum(exp_vals)
    weights = [e / total if total > 0 else 1.0 / len(exp_vals) for e in exp_vals]

    p_final = [0.0] * 5
    for w, (_, cen) in zip(weights, taken):
        for i in range(5):
            p_final[i] += w * cen[i]

    return dict(zip(DIM_ORDER, p_final))


def analyze_macro_indices(
    p_final: Dict[str, float],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, float]:
    """
    根据合成张量 P_final = [E,O,M,S,R] 计算宏观指数（0-100）。
    SOP V6.10：改用 Sigmoid 平滑，避免 0/100 二元对立。raw 公式（加权加法，避免乘法爆炸）：
    - 财富 V_wealth = (E + M) - S*wealth_s_penalty
    - 事业 V_career = O + M - S*career_s_penalty
    - 健康 V_health = E - S*health_s_penalty
    Score = 100/(1+exp(-k*(V-V_mid)))，V_mid、k 与各维度的 S 惩罚系数均来自 config.scaling_params。
    """
    full_cfg = _load_dynamic_manifold_config()
    scale = full_cfg.get("scaling_params") or {}
    k = float(scale.get("sigmoid_k", 0.8))
    wealth_mid = float(scale.get("wealth_mid", 2.5))
    career_mid = float(scale.get("career_mid", 2.0))
    health_mid = float(scale.get("health_mid", 1.5))
    wealth_s_penalty = float(scale.get("wealth_s_penalty", 0.2))
    career_s_penalty = float(scale.get("career_s_penalty", 0.3))
    health_s_penalty = float(scale.get("health_s_penalty", 0.5))

    E = float(p_final.get("E", 0))
    O = float(p_final.get("O", 0))
    M = float(p_final.get("M", 0))
    S = max(0.0, float(p_final.get("S", 0)))

    wealth_raw = (E + M) - S * wealth_s_penalty
    career_raw = O + M - S * career_s_penalty
    health_raw = E - S * health_s_penalty

    wealth = _sigmoid_score(wealth_raw, wealth_mid, k)
    career = _sigmoid_score(career_raw, career_mid, k)
    health = _sigmoid_score(health_raw, health_mid, k)

    out = {
        "wealth": round(min(100.0, max(0.0, wealth)), 1),
        "career": round(min(100.0, max(0.0, career)), 1),
        "health": round(min(100.0, max(0.0, health)), 1),
    }

    # SOP V6.9：高级语义映射（社交、学研、风险），同样做 Sigmoid 软化
    adv = (full_cfg.get("advanced_macro_mapping") or {}) if full_cfg else {}
    if adv.get("enabled"):
        social_mid = float(scale.get("social_mid", 1.0))
        intellect_mid = float(scale.get("intellect_mid", 0.5))
        risk_mid = float(scale.get("risk_mid", 0.5))

        sw = adv.get("social_weights") or {}
        m_w = float(sw.get("M", 0.6))
        r_w = float(sw.get("R", 0.4))
        penalty = float(sw.get("penalty_S_O", 0.2))
        R = max(0.0, float(p_final.get("R", 0)))
        social_raw = (M * m_w + R * r_w) * (1.0 - min(1.0, abs(S - O) * penalty))
        out["social"] = round(min(100.0, max(0.0, _sigmoid_score(social_raw, social_mid, k))), 1)

        iw = adv.get("intellect_weights") or {}
        o_w = float(iw.get("O", 1.0))
        r_iw = float(iw.get("R", 1.0))
        intellect_raw = O * o_w * R * r_iw * 1.2
        out["intellect"] = round(min(100.0, max(0.0, _sigmoid_score(intellect_raw, intellect_mid, k))), 1)

        rw = adv.get("risk_weights") or {}
        s_rw = float(rw.get("S", 1.5))
        o_rw = float(rw.get("O", -0.5))
        risk_raw = S * s_rw + O * o_rw
        out["risk"] = round(min(100.0, max(0.0, _sigmoid_score(risk_raw, risk_mid, k))), 1)

    return out
