"""
FDS 格局对撞调度器 (Pattern Collider) — 第 037 号工程指令
=========================================================
多重格局「叠加态」：对 QGA 注册的所有格局并行投影，按马氏距离计算置信度，输出概率化格局列表。
物理投影 + 置信度评分，不做 if-else 排他。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
QGA_MANIFEST = ROOT / "registry" / "qga_manifest.json"
DIM_ORDER = ["E", "O", "M", "S", "R"]


def _load_qga_registered_patterns() -> List[Dict[str, Any]]:
    """从 qga_manifest.json 的 topics.holographic_pattern 读取已注册格局列表。"""
    if not QGA_MANIFEST.exists():
        return []
    with open(QGA_MANIFEST, "r", encoding="utf-8") as f:
        data = json.load(f)
    return (data.get("topics") or {}).get("holographic_pattern") or []


def _load_manifest(manifest_ref: str) -> Optional[Dict]:
    path = ROOT / manifest_ref
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _tmm_from_manifest(manifest: Dict) -> Tuple[Optional[np.ndarray], List[str]]:
    """从 manifest 提取 TMM 权重矩阵 (10,5) 与 ten_gods 顺序。"""
    tmm = manifest.get("tensor_mapping_matrix") or {}
    weights = tmm.get("weights", {})
    order = tmm.get("ten_gods", [])
    if not weights or not order:
        return None, []
    W = np.array([weights.get(g, [0] * 5) for g in order], dtype=float)
    if W.shape[1] != 5:
        return None, []
    return W, order


def _manifold_from_duckdb(pattern_id: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """第 045 号：优先从 DuckDB 向量化取质心（无 cov，用欧氏距离）。"""
    try:
        from core.database import PHYSICS_DB
        from core.database.fds_physics import FDSPhysics
        physics = FDSPhysics(PHYSICS_DB)
        cen = physics.get_centroid(pattern_id)
        physics.close()
        if cen:
            mu, _ = cen
            return mu, None
    except Exception as e:
        logger.debug("DuckDB manifold load failed for %s: %s", pattern_id, e)
    return None, None


def _manifold_from_registry(pattern_id: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """A-01 从 registry JSON 取 mean/cov；其余优先 DuckDB 质心，否则 NPZ 算均值。"""
    reg_path = ROOT / "registry" / "holographic_pattern" / f"{pattern_id}.json"
    if reg_path.exists():
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            data = raw.get("data") or raw
            anchors = data.get("feature_anchors", {}).get("standard_manifold", {})
            mu = anchors.get("mean_vector")
            cov = anchors.get("covariance_matrix")
            if mu:
                mu = np.array(mu, dtype=float)
                cov = np.array(cov, dtype=float) if cov else None
                return mu, cov
        except Exception as e:
            logger.debug("Registry manifold load failed for %s: %s", pattern_id, e)
    mu, _ = _manifold_from_duckdb(pattern_id)
    if mu is not None:
        return mu, None
    prefix = pattern_id.replace("-", "").lower()
    npz_path = ROOT / "data_local" / f"{prefix}_full_points.npz"
    if npz_path.exists():
        try:
            data = np.load(npz_path)
            points = data["points"]
            mu = np.mean(points, axis=0)
            if points.shape[0] > 1:
                cov = np.cov(points.T)
            else:
                cov = None
            return mu, cov
        except Exception as e:
            logger.debug("NPZ manifold load failed for %s: %s", pattern_id, e)
    return None, None


def _project_and_d_m(
    ten_gods: Dict[str, float],
    W: np.ndarray,
    order: List[str],
    mu: Optional[np.ndarray],
    cov: Optional[np.ndarray],
) -> Tuple[np.ndarray, float]:
    """用 TMM 将 ten_gods 投影到 5D，再计算到流形 (mu,cov) 的马氏距离；无 cov 时用欧氏距离。"""
    vec = np.array([float(ten_gods.get(g, 0)) for g in order], dtype=float)
    point = np.dot(W.T, vec)
    if mu is None:
        return point, float("inf")
    delta = point - mu
    if cov is not None:
        try:
            inv_cov = np.linalg.pinv(cov)
            d_sq = delta.T @ inv_cov @ delta
            return point, float(np.sqrt(max(0.0, d_sq)))
        except Exception:
            pass
    return point, float(np.linalg.norm(delta))


def _distances_to_confidences(distances: Dict[str, float], temperature: float = 1.0) -> Dict[str, float]:
    """将各格局的马氏距离转为归一化置信度（软max：exp(-d/temp) 后归一化）。"""
    if not distances:
        return {}
    inv = {pid: np.exp(-d / max(temperature, 0.1)) for pid, d in distances.items()}
    total = sum(inv.values()) or 1.0
    return {pid: v / total for pid, v in inv.items()}


class PatternCollider:
    """
    格局对撞调度器：多矩阵并行投影 + 马氏距离 + 概率化输出。
    """

    def __init__(self, qga_manifest_path: Optional[Path] = None):
        self._manifest_path = Path(qga_manifest_path) if qga_manifest_path else QGA_MANIFEST
        self._entries: List[Dict[str, Any]] = []
        self._cache: Dict[str, Tuple[np.ndarray, List[str], Optional[np.ndarray], Optional[np.ndarray]]] = {}
        self._reload()

    def _reload(self) -> None:
        if not self._manifest_path.exists():
            self._entries = []
            self._cache = {}
            return
        with open(self._manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._entries = (data.get("topics") or {}).get("holographic_pattern") or []
        self._cache = {}
        for entry in self._entries:
            pid = entry.get("pattern_id")
            if not pid:
                continue
            manifest_ref = entry.get("manifest_ref", "")
            manifest = _load_manifest(manifest_ref) if manifest_ref else None
            if not manifest:
                continue
            W, order = _tmm_from_manifest(manifest)
            if W is None:
                continue
            mu, cov = _manifold_from_registry(pid)
            self._cache[pid] = (W, order, mu, cov)
        logger.info("PatternCollider loaded %d patterns from QGA", len(self._cache))

    def run_collision(
        self,
        ten_gods: Dict[str, float],
        temperature: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """
        对同一组十神向量做多格局投影，按马氏距离计算置信度，返回概率化格局列表。

        Args:
            ten_gods: 十神向量（标准代码 ZG, PG, ... 或别名）
            temperature: 软max 温度，越小越尖锐

        Returns:
            Probabilistic_Patterns: [{"pattern_id": "A-02", "confidence_pct": 85.0, "d_m": 1.2, "point_5d": {...}}, ...]
        """
        distances: Dict[str, float] = {}
        points_5d: Dict[str, Dict[str, float]] = {}
        for pid, (W, order, mu, cov) in self._cache.items():
            point, d_m = _project_and_d_m(ten_gods, W, order, mu, cov)
            distances[pid] = d_m
            points_5d[pid] = {d: float(point[i]) for i, d in enumerate(DIM_ORDER)}

        confidences = _distances_to_confidences(distances, temperature=temperature)
        out = []
        for pid in sorted(confidences.keys(), key=lambda x: -confidences[x]):
            pct = round(confidences[pid] * 100.0, 2)
            out.append({
                "pattern_id": pid,
                "confidence_pct": pct,
                "d_m": round(distances[pid], 4),
                "point_5d": points_5d[pid],
            })
        return out

    def get_registered_pattern_ids(self) -> List[str]:
        return list(self._cache.keys())

    def get_tmm_and_centroid(self, pattern_id: str) -> Tuple[Optional[np.ndarray], List[str], Optional[np.ndarray]]:
        """
        返回指定格局的 TMM 权重矩阵 W(10,5)、十神顺序、质心 mu(5,)。
        供喜忌神引擎等模块使用；若格局未注册则返回 (None, [], None)。
        """
        entry = self._cache.get(pattern_id)
        if not entry:
            return None, [], None
        W, order, mu, _ = entry
        return W, order, mu


# 第 041 号：单例 PatternCollider，使格局 TMM 与 .npz 流形在首次调用时一次性加载，避免并发下重复 I/O
_collider_singleton: Optional[PatternCollider] = None


def _get_collider() -> PatternCollider:
    global _collider_singleton
    if _collider_singleton is None:
        _collider_singleton = PatternCollider()
    return _collider_singleton


def run_pattern_collision(
    ten_gods: Dict[str, float],
    temperature: float = 1.0,
) -> List[Dict[str, Any]]:
    """
    便捷入口：对十神向量运行对撞，返回 Probabilistic_Patterns。
    十神可由 Controller._chart_to_ten_gods(chart, day_master) 得到。
    使用单例 Collider，常用格局 .npz 在首次调用时加载至内存。
    """
    return _get_collider().run_collision(ten_gods, temperature=temperature)
