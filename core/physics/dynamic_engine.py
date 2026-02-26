"""
FDS 动态时空位移引擎 (第 049/050 号 · SOP V5.6)
================================================
原局为格，动变为局。法理刚性：引透权重翻倍、地理阻尼λ、刑冲合化、格局对撞态。
P_dynamic = P_natal + (ΔT_time × λ_geo) + geo_offset；流形捕获返回位移矢量与双格对撞态。
所有权重/阈值/刑冲合化/阻尼均来自 config/dynamic_manifold.json，零硬编码。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT / "config" / "dynamic_manifold.json"
DIM_ORDER = ["E", "O", "M", "S", "R"]

_GAN_WUXING = ["木", "木", "火", "火", "土", "土", "金", "金", "水", "水"]
_ZHI_WUXING = ["水", "土", "木", "木", "土", "火", "火", "土", "金", "金", "土", "水"]


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("dynamic_manifold 配置加载失败: %s", e)
        return {}


def _pillar_to_5d_delta(gan_zhi: str, config: Dict[str, Any]) -> Dict[str, float]:
    """单柱干支 → 5D 位移（五行→5D，天干 0.55 / 地支 0.45）。"""
    wuxing_map = config.get("wuxing_to_5d_delta") or {}
    scale = float((config.get("time") or {}).get("scale_pillar", 1.0))
    out = {k: 0.0 for k in DIM_ORDER}
    if not gan_zhi or len(gan_zhi) < 2:
        return out
    gan, zhi = gan_zhi[0], gan_zhi[1]
    try:
        gan_idx = "甲乙丙丁戊己庚辛壬癸".index(gan)
    except ValueError:
        gan_idx = 0
    try:
        zhi_idx = "子丑寅卯辰巳午未申酉戌亥".index(zhi)
    except ValueError:
        zhi_idx = 0
    w_gan = _GAN_WUXING[gan_idx]
    w_zhi = _ZHI_WUXING[zhi_idx]
    d_gan = wuxing_map.get(w_gan)
    d_zhi = wuxing_map.get(w_zhi)
    if isinstance(d_gan, dict):
        for k in DIM_ORDER:
            out[k] += float(d_gan.get(k, 0)) * 0.55
    if isinstance(d_zhi, dict):
        for k in DIM_ORDER:
            out[k] += float(d_zhi.get(k, 0)) * 0.45
    for k in DIM_ORDER:
        out[k] *= scale
    return out


def _is_tougan_month(
    pillar_gan: str,
    month_branch: str,
    day_master: str,
) -> bool:
    """某柱天干是否为月令本气之透出（同十神即透）。用于流年或大运。"""
    if not pillar_gan or not month_branch or not day_master:
        return False
    try:
        from core.classical_tougan import _get_month_main_stem, get_ten_god_code
        month_main_stem = _get_month_main_stem(month_branch)
        if not month_main_stem:
            return False
        god_month = get_ten_god_code(day_master, month_main_stem)
        god_pillar = get_ten_god_code(day_master, pillar_gan)
        return god_month == god_pillar and bool(god_month)
    except Exception:
        return False


def _is_annual_tougan_month(
    annual_gan: str,
    month_branch: str,
    day_master: str,
) -> bool:
    """流年干是否为月令本气之透出（同十神即透）。"""
    return _is_tougan_month(annual_gan, month_branch, day_master)


def _is_major_tougan_month(
    major_gan: str,
    month_branch: str,
    day_master: str,
) -> bool:
    """大运干是否为月令本气之透出。物理含义：埋藏的欲望被时代唤醒。"""
    return _is_tougan_month(major_gan, month_branch, day_master)


def _interaction_delta(z1: str, z2: str, config: Dict[str, Any]) -> Dict[str, float]:
    """两地支是否构成刑冲合化，返回 5D delta（无则零向量）。"""
    out = {k: 0.0 for k in DIM_ORDER}
    interactions = config.get("stem_branch_interactions") or []
    if not z1 or not z2:
        return out
    for item in interactions:
        name = (item.get("interaction") or "").strip()
        if len(name) < 2:
            continue
        a, b = name[0], name[1]
        if (a == z1 and b == z2) or (a == z2 and b == z1):
            delta = item.get("delta")
            if isinstance(delta, dict):
                for k in DIM_ORDER:
                    out[k] += float(delta.get(k, 0))
            break
    return out


def _natal_to_vector(natal_5d: Any) -> List[float]:
    if isinstance(natal_5d, (list, tuple)) and len(natal_5d) >= 5:
        return [float(natal_5d[i]) for i in range(5)]
    if isinstance(natal_5d, dict):
        return [float(natal_5d.get(k, 0)) for k in DIM_ORDER]
    return [0.0] * 5


def compute_dynamic_tensor(
    natal_5d: Any,
    major_pillar: str = "",
    annual_pillar: str = "",
    geo_region: str = "",
    month_branch: str = "",
    day_master: str = "",
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    动态张量注入（V5.6）：
    - 引透：流年透出月令时，流年位移权重 × tougan_scale。
    - 刑冲合化：大运/流年与月支两两查表叠加 delta。
    - 地理阻尼：ΔT 先乘 λ_geo（再可加小量 geo_offset），公式 ΔP = ΔT · λ_geo + geo_offset。
    返回 natal_point, dynamic_point, time_delta, geo_damping_applied, displacement, tougan_triggered, interaction_deltas。
    """
    config = config or load_config()
    vec = _natal_to_vector(natal_5d)
    time_cfg = config.get("time") or {}
    w_major = float(time_cfg.get("weight_major", 0.4))
    w_annual = float(time_cfg.get("weight_annual", 0.6))
    tougan_scale = float(time_cfg.get("tougan_scale", 2.0))

    delta_major = _pillar_to_5d_delta(major_pillar or "", config)
    delta_annual = _pillar_to_5d_delta(annual_pillar or "", config)
    annual_gan = (annual_pillar or "")[0:1]
    major_gan = (major_pillar or "")[0:1]
    tougan_triggered = _is_annual_tougan_month(annual_gan, month_branch, day_master)
    major_tougan_triggered = _is_major_tougan_month(major_gan, month_branch, day_master)
    if tougan_triggered:
        for k in DIM_ORDER:
            delta_annual[k] *= tougan_scale
    if major_tougan_triggered:
        for k in DIM_ORDER:
            delta_major[k] *= tougan_scale

    time_delta = {k: delta_major[k] * w_major + delta_annual[k] * w_annual for k in DIM_ORDER}

    # 刑冲合化：大运支-流年支、大运支-月支、流年支-月支
    z_major = (major_pillar or "")[1:2]
    z_annual = (annual_pillar or "")[1:2]
    interaction_deltas = []
    for za, zb in [(z_major, z_annual), (z_major, month_branch), (z_annual, month_branch)]:
        d = _interaction_delta(za, zb, config)
        if any(d[k] != 0 for k in DIM_ORDER):
            time_delta = {k: time_delta[k] + d[k] for k in DIM_ORDER}
            interaction_deltas.append({"pair": f"{za}{zb}", "delta": d})

    # 地理阻尼：ΔT · λ_geo
    geo_damping = (config.get("geo_damping") or {}).get(geo_region) or (config.get("geo_damping") or {}).get("中") or {}
    if isinstance(geo_damping, dict):
        time_delta_damped = {k: time_delta[k] * float(geo_damping.get(k, 1.0)) for k in DIM_ORDER}
    else:
        time_delta_damped = dict(time_delta)
    geo_offset_cfg = config.get("geo_5d_offset") or {}
    geo_offset = geo_offset_cfg.get(geo_region) or geo_offset_cfg.get("中") or {}
    if isinstance(geo_offset, dict):
        geo_offset = {k: float(geo_offset.get(k, 0)) for k in DIM_ORDER}
    else:
        geo_offset = {k: 0.0 for k in DIM_ORDER}

    dynamic_vec = [
        vec[i] + time_delta_damped[DIM_ORDER[i]] + geo_offset[DIM_ORDER[i]]
        for i in range(5)
    ]
    dynamic_point = dict(zip(DIM_ORDER, dynamic_vec))
    displacement = {k: dynamic_point[k] - vec[i] for i, k in enumerate(DIM_ORDER)}

    return {
        "natal_point": dict(zip(DIM_ORDER, vec)),
        "dynamic_point": dynamic_point,
        "time_delta": time_delta,
        "time_delta_damped": time_delta_damped,
        "geo_damping": geo_damping if isinstance(geo_damping, dict) else {},
        "geo_offset": geo_offset,
        "displacement": displacement,
        "tougan_triggered": tougan_triggered,
        "major_tougan_triggered": major_tougan_triggered,
        "interaction_deltas": interaction_deltas,
    }


def _manifold_capture_impl(
    vec: List[float],
    pattern_ids: List[str],
) -> Tuple[Optional[str], Optional[str], float, float, Dict[str, float], Optional[Dict[str, float]]]:
    """
    返回 (最近 id, 次近 id, 最近距, 次近距离, 全量距离, 最近质心向量)。
    """
    try:
        from core.database import PHYSICS_DB
        from core.database.fds_physics import FDSPhysics
        physics = FDSPhysics(PHYSICS_DB)
        distances = {}
        centroids = {}
        for pid in pattern_ids:
            cen = physics.get_centroid(pid)
            if not cen:
                distances[pid] = float("inf")
                continue
            mu = cen[0]
            d = sum((vec[i] - float(mu[i])) ** 2 for i in range(5)) ** 0.5
            distances[pid] = d
            centroids[pid] = [float(mu[i]) for i in range(5)]
        physics.close()
        sorted_pids = sorted(distances.keys(), key=lambda p: distances[p])
        best_id = sorted_pids[0] if sorted_pids and distances.get(sorted_pids[0], float("inf")) < float("inf") else None
        best_d = distances[best_id] if best_id else float("inf")
        second_id = sorted_pids[1] if len(sorted_pids) > 1 else None
        second_d = distances[second_id] if second_id else float("inf")
        best_centroid = dict(zip(DIM_ORDER, centroids[best_id])) if best_id and best_id in centroids else None
        return best_id, second_id, best_d, second_d, distances, best_centroid
    except Exception:
        return None, None, float("inf"), float("inf"), {}, None


def manifold_capture(
    dynamic_5d: Any,
    natal_5d: Optional[Any] = None,
    pattern_ids: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    流形捕获（V5.6）：最近格局、次近格局、全量距离、流形位移矢量、格局对撞态。
    流形位移矢量 = dynamic - natal（轨迹）；若 natal_5d 未传则仅返回 to_centroid_vector（指向最近质心）。
    """
    config = config or load_config()
    vec = _natal_to_vector(dynamic_5d)
    if len(vec) != 5:
        return {"pattern_id": None, "distance": None, "distances": {}, "displacement_vector": None, "is_double_capture": False}
    pattern_ids = pattern_ids or [f"A-{i:02d}" for i in range(1, 31)]
    best_id, second_id, best_d, second_d, distances, best_centroid = _manifold_capture_impl(vec, pattern_ids)

    ratio_thr = float((config.get("manifold_capture") or {}).get("double_capture_ratio_threshold", 1.35))
    is_double_capture = (
        best_id and second_id and best_d > 0 and (second_d / best_d) <= ratio_thr
    )

    displacement_vector = None
    if natal_5d is not None:
        natal_vec = _natal_to_vector(natal_5d)
        if len(natal_vec) == 5:
            displacement_vector = {k: round(vec[i] - natal_vec[i], 6) for i, k in enumerate(DIM_ORDER)}
    elif best_centroid:
        displacement_vector = {k: round(vec[i] - best_centroid[k], 6) for i, k in enumerate(DIM_ORDER)}

    return {
        "pattern_id": best_id,
        "second_pattern_id": second_id if is_double_capture else None,
        "distance": round(best_d, 6) if best_d != float("inf") else None,
        "second_distance": round(second_d, 6) if second_id else None,
        "distances": {k: round(v, 6) for k, v in distances.items()},
        "displacement_vector": displacement_vector,
        "is_double_capture": is_double_capture,
        "to_centroid_vector": {k: round(vec[i] - best_centroid[k], 6) for i, k in enumerate(DIM_ORDER)} if best_centroid else None,
    }


def collision_warning(
    dynamic_5d: Any,
    s_threshold: Optional[float] = None,
    manifold_result: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    对撞预警（V5.6）：S 轴高压 或 格局对撞态（流形不稳定性）。
    返回 in_collision_zone, s_value, source_pattern, target_pattern, collision_type, message，供 RAG 应灾检索 (source_pattern, target_pattern, collision_type)。
    """
    config = config or load_config()
    thr = s_threshold
    if thr is None:
        thr = float((config.get("collision_warning") or {}).get("s_threshold", 1.8))
    vec = _natal_to_vector(dynamic_5d)
    s_idx = DIM_ORDER.index("S")
    s_val = vec[s_idx] if len(vec) > s_idx else 0.0
    high_stress = s_val > thr

    source_pattern = None
    target_pattern = None
    collision_type = None
    message = None

    if manifold_result and manifold_result.get("is_double_capture"):
        source_pattern = manifold_result.get("pattern_id")
        target_pattern = manifold_result.get("second_pattern_id")
        collision_type = "manifold_instability"
        message = "格局对撞态（流形不稳定性），建议 RAG 输出决策摇摆/多重人格冲突类判词"
    if high_stress:
        if not collision_type:
            collision_type = "high_stress"
            message = "进入高压对撞区，建议调 RAG 应灾指引"
        else:
            message = (message or "") + "；S 轴超阈值，建议调 RAG 应灾指引"

    in_zone = high_stress or (manifold_result or {}).get("is_double_capture", False)
    return {
        "in_collision_zone": in_zone,
        "s_value": round(s_val, 4),
        "s_threshold": thr,
        "source_pattern": source_pattern,
        "target_pattern": target_pattern,
        "collision_type": collision_type,
        "message": message,
    }
