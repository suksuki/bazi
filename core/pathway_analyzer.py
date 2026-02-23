"""
A-01 路径模拟与流形修复 (Pathway Analyzer & Manifold Deficit Repair)
====================================================================
第 029 号工程指令：从「现状诊断」到「路径指引」。
缺憾识别（相对质心的瓶颈维度）→ 路径检索（相似起点但成功补齐的样本）→ 位移矢量 ΔV 提取。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from core.case_retriever import CaseRetriever, DIM_ORDER

logger = logging.getLogger(__name__)

AXIS_LABELS = {"E": "能量", "O": "秩序", "M": "财富", "S": "压力", "R": "关系"}


def _point_to_vec(point: Union[Dict[str, float], List[float]]) -> np.ndarray:
    if isinstance(point, dict):
        return np.array([float(point.get(k, 0.0)) for k in DIM_ORDER])
    return np.asarray(point, dtype=float).ravel()[:5]


def get_reference_centroid(centroids: Dict[str, List[float]], user_vec: np.ndarray) -> np.ndarray:
    """取与用户最近的子格局质心作为参考。"""
    if not centroids:
        return np.zeros(5)
    best = None
    best_d = float("inf")
    for _, c in centroids.items():
        cvec = np.array(c, dtype=float)
        d = float(np.linalg.norm(user_vec - cvec))
        if d < best_d:
            best_d = d
            best = cvec
    return best if best is not None else np.zeros(5)


def identify_deficit(
    user_point: Union[Dict[str, float], List[float]],
    centroids: Dict[str, List[float]],
) -> Dict[str, Any]:
    """
    对比用户 5D 与 A-01 参考质心，识别「瓶颈维度」（相对质心短差最大的轴）。
    返回: axis, deficit (需补齐量), current, target_from_centroid, centroid_vec。
    """
    user_vec = _point_to_vec(user_point)
    ref = get_reference_centroid(centroids, user_vec)
    diff = ref - user_vec  # 正 = 用户低于质心，需补齐
    # 瓶颈 = 短差最大的轴（diff 最大为正；若全负则取 diff 最大即“最接近质心”的轴）
    axis_idx = int(np.argmax(diff))
    axis = DIM_ORDER[axis_idx]
    deficit = float(diff[axis_idx])
    current = float(user_vec[axis_idx])
    target_from_centroid = float(ref[axis_idx])
    return {
        "axis": axis,
        "axis_label": AXIS_LABELS.get(axis, axis),
        "deficit": round(deficit, 4),
        "current": round(current, 4),
        "target_from_centroid": round(target_from_centroid, 4),
        "centroid_ref": ref.tolist(),
        "offset_vector": {DIM_ORDER[i]: round(float(diff[i]), 4) for i in range(5)},
    }


def find_repair_paths(
    retriever: CaseRetriever,
    user_point: Union[Dict[str, float], List[float]],
    deficit_axis: str,
    top_neighbors: int = 400,
    top_repair: int = 5,
) -> List[Dict[str, Any]]:
    """
    在样本库中寻找与用户起点相似、但在瓶颈轴上已「修复」的案例（该轴取值更高）。
    返回这些案例及其相对用户的位移矢量 ΔV 与在该轴上的提升量。
    """
    if deficit_axis not in DIM_ORDER:
        return []
    axis_idx = DIM_ORDER.index(deficit_axis)
    user_vec = _point_to_vec(user_point)
    # 多取近邻，再筛出在 deficit 轴上高于用户的
    candidates = retriever.find_nearest_cases(user_point, top_n=top_neighbors, include_singularity_hint=False)
    repair_cases = []
    for c in candidates:
        pt = c.get("point")
        if isinstance(pt, dict):
            pt = [pt.get(k, 0) for k in DIM_ORDER]
        if len(pt) != 5:
            continue
        pt_arr = np.array(pt, dtype=float)
        if pt_arr[axis_idx] <= user_vec[axis_idx]:
            continue
        delta = pt_arr - user_vec
        repair_cases.append({
            "ref": c.get("ref", ""),
            "subpattern": c.get("subpattern", ""),
            "point": pt,
            "delta_vector": {DIM_ORDER[i]: round(float(delta[i]), 4) for i in range(5)},
            "improvement_on_axis": round(float(pt_arr[axis_idx] - user_vec[axis_idx]), 4),
            "distance": c.get("distance", 0),
        })
    # 按该轴提升量降序，取 top_repair
    repair_cases.sort(key=lambda x: -x["improvement_on_axis"])
    return repair_cases[:top_repair]


def compute_repair_vector(
    repair_paths: List[Dict[str, Any]],
    deficit_axis: str,
    user_point: Union[Dict[str, float], List[float]],
) -> Dict[str, Any]:
    """
    根据「修复路径」样本汇总出建议的位移矢量 ΔV（各轴均值或中位数）。
    """
    if not repair_paths or deficit_axis not in DIM_ORDER:
        return {"delta_vector": {k: 0.0 for k in DIM_ORDER}, "target_delta_on_axis": 0.0}

    axis_idx = DIM_ORDER.index(deficit_axis)
    deltas = np.array([[p["delta_vector"].get(k, 0) for k in DIM_ORDER] for p in repair_paths])
    median_delta = np.median(deltas, axis=0)
    mean_delta = np.mean(deltas, axis=0)
    user_vec = _point_to_vec(user_point)
    target_delta_on_axis = float(median_delta[axis_idx])  # 建议在该轴上的位移量

    return {
        "delta_vector": {DIM_ORDER[i]: round(float(median_delta[i]), 4) for i in range(5)},
        "delta_vector_mean": {DIM_ORDER[i]: round(float(mean_delta[i]), 4) for i in range(5)},
        "target_delta_on_axis": round(target_delta_on_axis, 4),
        "target_value_approx": round(float(user_vec[axis_idx]) + target_delta_on_axis, 4),
        "samples_used": len(repair_paths),
    }


def analyze_repair_pathway(
    retriever: CaseRetriever,
    user_point: Union[Dict[str, float], List[float]],
    top_repair: int = 5,
) -> Dict[str, Any]:
    """
    一站式：缺憾识别 → 路径检索 → 位移矢量。
    返回 deficit_info, repair_paths, repair_vector。
    """
    if not retriever or retriever.case_count == 0:
        return {"deficit_info": None, "repair_paths": [], "repair_vector": None}

    centroids = getattr(retriever, "_centroids", {})
    deficit_info = identify_deficit(user_point, centroids)
    axis = deficit_info["axis"]
    if deficit_info["deficit"] >= 0:
        # 用户在该轴已不低于质心，可视为无瓶颈或轻微
        return {
            "deficit_info": deficit_info,
            "repair_paths": [],
            "repair_vector": None,
        }

    repair_paths = find_repair_paths(retriever, user_point, axis, top_repair=top_repair)
    repair_vector = compute_repair_vector(repair_paths, axis, user_point) if repair_paths else None

    return {
        "deficit_info": deficit_info,
        "repair_paths": repair_paths,
        "repair_vector": repair_vector,
    }
