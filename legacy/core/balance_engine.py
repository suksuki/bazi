"""
FDS 喜忌神识别引擎 (Balance Auditor) — 第 040 号工程指令
=========================================================
基于 5D 物理位移 ΔV 与格局质心的「跑模拟」识别：用神、忌神、通关神。
不翻书、不硬编码喜忌，纯由 TMM 投影与质心距离变化推导。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from core.config_manager import ConfigManager
from core.pattern_collider import DIM_ORDER, PatternCollider, _get_collider

logger = logging.getLogger(__name__)


def _get_balance_auditor_params() -> Dict[str, float]:
    """从 config/physics/algorithm_params.json 读取喜忌神引擎参数，支持无重启调整。"""
    params = (ConfigManager.get_algorithm_params() or {}).get("balance_auditor") or {}
    return {
        "overload_threshold": float(params.get("overload_threshold", 1.2)),
        "weak_threshold": float(params.get("weak_threshold", -0.5)),
        "inject_delta": float(params.get("inject_delta", 0.25)),
        "bridge_m_min": float(params.get("bridge_m_min", 0.6)),
        "conflict_s_offset": float(params.get("conflict_s_offset", 0.2)),
    }

# 十神代码 → 中文名（输出用）
TEN_GOD_CODE_TO_CN: Dict[str, str] = {
    "ZG": "正官", "PG": "七杀", "ZR": "正财", "PR": "偏财",
    "ZS": "食神", "PS": "伤官", "ZC": "正印", "PC": "偏印",
    "ZB": "比肩", "PB": "劫财",
}

# 轴索引
_AXIS_IDX = {d: i for i, d in enumerate(DIM_ORDER)}


def _vec_from_5d(point_5d: Dict[str, float]) -> np.ndarray:
    """从 E/O/M/S/R 字典得到 (5,) 向量。"""
    return np.array([float(point_5d.get(d, 0.0)) for d in DIM_ORDER], dtype=float)


def _inject_ten_god_and_project(
    ten_gods: Dict[str, float],
    order: List[str],
    W: np.ndarray,
    inject_code: str,
    delta: float = 0.25,
) -> np.ndarray:
    """在十神 inject_code 上增加 delta，用 TMM 投影到 5D，返回新 5D 点。"""
    vec = np.array([float(ten_gods.get(g, 0)) for g in order], dtype=float)
    try:
        idx = order.index(inject_code)
        vec[idx] += delta
    except ValueError:
        pass
    return np.dot(W.T, vec)


def _distance_to_centroid(point: np.ndarray, centroid: np.ndarray) -> float:
    """欧氏距离到质心。"""
    return float(np.linalg.norm(point - centroid))


class BalanceAuditor:
    """
    喜忌神自动化识别：基于 5D 位移与格局质心的模拟结果，输出用神、忌神、通关神及物理理由。
    """

    def __init__(self, collider: Optional[PatternCollider] = None):
        self._collider = collider if collider is not None else _get_collider()

    def audit(
        self,
        point_5d: Dict[str, float],
        ten_gods: Dict[str, float],
        dominant_pattern_id: str,
        overload_threshold: Optional[float] = None,
        weak_threshold: Optional[float] = None,
        bridge_candidates: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        基于当前 5D 与十神向量，识别用神、忌神、通关神及理由。
        阈值从 config/physics/algorithm_params.json 读取，传参可覆盖。

        Args:
            point_5d: 命主当前 5D 坐标 {E,O,M,S,R}
            ten_gods: 十神向量，键为 ZG, PG, ... 
            dominant_pattern_id: 主格局 ID（如 A-02），用于取 TMM 与质心
            overload_threshold: 轴过载判定阈值（不传则从配置读取）
            weak_threshold: 轴薄弱判定阈值（不传则从配置读取）
            bridge_candidates: 通关神候选（默认 ZS, PS, ZC, PC）

        Returns:
            {
                "useful_god": "正印",           # 用神中文名
                "harmful_god": "七杀",
                "bridge_god": "食神" | None,
                "reason_useful": "注入该十神可使 ΔV 指向质心、拉高 M/平衡 S…",
                "reason_harmful": "当前 S 轴过载，该十神对 S 正向贡献最大",
                "reason_bridge": "财杀双高，食伤制杀/印星化杀…" | None,
                "meta": { "axis_overloaded": "S", "axis_weak": "O" | None, ... }
            }
        """
        algo = _get_balance_auditor_params()
        overload_threshold = overload_threshold if overload_threshold is not None else algo["overload_threshold"]
        weak_threshold = weak_threshold if weak_threshold is not None else algo["weak_threshold"]
        inject_delta = algo["inject_delta"]
        bridge_m_min = algo["bridge_m_min"]
        conflict_s_offset = algo["conflict_s_offset"]

        out: Dict[str, Any] = {
            "useful_god": "",
            "harmful_god": "",
            "bridge_god": None,
            "reason_useful": "",
            "reason_harmful": "",
            "reason_bridge": None,
            "meta": {},
        }
        W, order, mu = self._collider.get_tmm_and_centroid(dominant_pattern_id)
        if W is None or not order or mu is None:
            logger.warning("BalanceAuditor: 未找到格局 %s 的 TMM 或质心", dominant_pattern_id)
            return out

        point = _vec_from_5d(point_5d)
        gap = mu - point  # 指向质心的缺口方向

        # ---------- 用神：模拟注入各十神，选使 ΔV 最指向质心者 ----------
        best_useful_code = None
        best_useful_improve = -float("inf")
        for code in order:
            new_point = _inject_ten_god_and_project(ten_gods, order, W, code, delta=inject_delta)
            dist_before = _distance_to_centroid(point, mu)
            dist_after = _distance_to_centroid(new_point, mu)
            improve = dist_before - dist_after
            if improve > best_useful_improve:
                best_useful_improve = improve
                best_useful_code = code
        if best_useful_code:
            out["useful_god"] = TEN_GOD_CODE_TO_CN.get(best_useful_code, best_useful_code)
            out["reason_useful"] = (
                f"模拟注入「{out['useful_god']}」增量后，命主 5D 向格局质心位移最大，"
                "有利于拉高财富轴或平衡应力轴。"
            )

        # ---------- 忌神：最过载或最薄弱轴 → 对该轴贡献最「恶化」的十神 ----------
        values = [float(point[_AXIS_IDX[d]]) for d in DIM_ORDER]
        overload_axis = None
        weak_axis = None
        for i, (dim, v) in enumerate(zip(DIM_ORDER, values)):
            if v >= overload_threshold:
                overload_axis = (dim, i)
                break
        if overload_axis is None:
            for i, (dim, v) in enumerate(zip(DIM_ORDER, values)):
                if v <= weak_threshold:
                    weak_axis = (dim, i)
                    break

        if overload_axis is not None:
            dim, idx = overload_axis
            # 该轴过载：忌神 = 对该轴正向贡献最大的十神
            col = W[:, idx]
            worst_g = order[int(np.argmax(col))]
            out["harmful_god"] = TEN_GOD_CODE_TO_CN.get(worst_g, worst_g)
            out["reason_harmful"] = (
                f"当前{_axis_cn(dim)}过载（{values[idx]:.2f}），"
                f"「{out['harmful_god']}」对该轴正向贡献最大，宜减不宜增。"
            )
            out["meta"]["axis_overloaded"] = dim
        elif weak_axis is not None:
            dim, idx = weak_axis
            # 该轴薄弱：忌神 = 对该轴负向贡献最大的十神（再加重薄弱）
            col = W[:, idx]
            worst_g = order[int(np.argmin(col))]
            out["harmful_god"] = TEN_GOD_CODE_TO_CN.get(worst_g, worst_g)
            out["reason_harmful"] = (
                f"当前{_axis_cn(dim)}偏弱（{values[idx]:.2f}），"
                f"「{out['harmful_god']}」会进一步削弱该轴，宜避。"
            )
            out["meta"]["axis_weak"] = dim
        else:
            # 无极端轴：选注入后使质心距离变大的十神为忌
            worst_dist = -float("inf")
            worst_code = None
            for code in order:
                new_point = _inject_ten_god_and_project(ten_gods, order, W, code, delta=inject_delta)
                dist_after = _distance_to_centroid(new_point, mu)
                if dist_after > worst_dist:
                    worst_dist = dist_after
                    worst_code = code
            if worst_code:
                out["harmful_god"] = TEN_GOD_CODE_TO_CN.get(worst_code, worst_code)
                out["reason_harmful"] = (
                    f"模拟注入「{out['harmful_god']}」后，命主点更远离格局质心，不利归位。"
                )

        # ---------- 通关神：财杀双高时，在候选里选能缩短质心距离者 ----------
        bridge_candidates = bridge_candidates or ["ZS", "PS", "ZC", "PC"]
        S_idx = _AXIS_IDX["S"]
        M_idx = _AXIS_IDX["M"]
        s_val = values[S_idx]
        m_val = values[M_idx]
        conflict = s_val >= (overload_threshold - conflict_s_offset) and m_val >= bridge_m_min
        if conflict:
            best_bridge_code = None
            best_bridge_improve = -float("inf")
            for code in bridge_candidates:
                if code not in order:
                    continue
                new_point = _inject_ten_god_and_project(ten_gods, order, W, code, delta=inject_delta * 0.8)
                dist_before = _distance_to_centroid(point, mu)
                dist_after = _distance_to_centroid(new_point, mu)
                improve = dist_before - dist_after
                if improve > best_bridge_improve:
                    best_bridge_improve = improve
                    best_bridge_code = code
            if best_bridge_code:
                out["bridge_god"] = TEN_GOD_CODE_TO_CN.get(best_bridge_code, best_bridge_code)
                out["reason_bridge"] = (
                    "财杀双高，压力与财富并存；"
                    f"「{out['bridge_god']}」可制杀或化杀，使位移向质心收敛。"
                )
            out["meta"]["conflict_caishashuang"] = True

        return out


def _axis_cn(dim: str) -> str:
    a = {"E": "能量轴", "O": "秩序轴", "M": "财富轴", "S": "应力轴", "R": "智慧轴"}
    return a.get(dim, dim)


def run_balance_audit(
    point_5d: Dict[str, float],
    ten_gods: Dict[str, float],
    dominant_pattern_id: str,
) -> Dict[str, Any]:
    """
    便捷入口：对当前 5D 与十神、主格局做喜忌神审计，返回结构化结果。
    供 Controller / AI Prompt 注入使用。
    """
    auditor = BalanceAuditor()
    return auditor.audit(point_5d, ten_gods, dominant_pattern_id)
