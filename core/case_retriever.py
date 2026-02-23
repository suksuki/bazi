"""
A-01 案例对撞机 (Case Collider)
==============================
从 A-01 已标注样本（registry benchmarks / 全量缓存）中，按 5D 欧氏距离检索与当前用户
物理坐标最相似的案例。支持 scipy KDTree 全量索引（<50ms）、奇点标记与 pickle 缓存。

Compliance: 公理一（零硬编码）、公理三（概率/相似度输出）
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

try:
    from scipy.spatial import cKDTree
    _SCIPY_AVAILABLE = True
except ImportError:
    cKDTree = None  # type: ignore
    _SCIPY_AVAILABLE = False

# 5D 轴顺序（与 FDS 一致）
DIM_ORDER = ["E", "O", "M", "S", "R"]

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_REGISTRY = _PROJECT_ROOT / "registry" / "holographic_pattern" / "A-01.json"


def _point_to_vector(point: Union[Dict[str, float], List[float]]) -> np.ndarray:
    """将 point（dict 或 list）转为 (5,) 向量，顺序 E,O,M,S,R。"""
    if isinstance(point, (list, tuple)):
        arr = np.asarray(point, dtype=float)
        if arr.shape != (5,):
            raise ValueError("point as list must have length 5")
        return arr
    if isinstance(point, dict):
        return np.array([float(point.get(k, 0.0)) for k in DIM_ORDER])
    raise TypeError("point must be dict (E,O,M,S,R) or list of 5 floats")


def _assign_subpattern_by_centroid(
    vector: np.ndarray,
    centroids: Dict[str, List[float]],
) -> str:
    """根据与质心的欧氏距离归属子格局。"""
    best = ""
    best_d = float("inf")
    for sp, c in centroids.items():
        cvec = np.array(c, dtype=float)
        d = float(np.linalg.norm(vector - cvec))
        if d < best_d:
            best_d = d
            best = sp
    return best or "A-01-S1"


def load_registry_benchmarks(registry_path: Optional[Path] = None) -> Tuple[List[Dict], Dict[str, List[float]]]:
    """
    从 A-01.json 读取 benchmarks（5D 样本）与 subpattern_centroids。
    返回 (cases, centroids)，cases 每项为 {"point": list, "ref": str, "note": str, "subpattern": str}。
    """
    path = registry_path or _DEFAULT_REGISTRY
    if not path.exists():
        logger.warning("Registry not found: %s", path)
        return [], {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # data.data.benchmarks, data.data.feature_anchors.subpattern_centroids
    inner = data.get("data") or data
    benchmarks = inner.get("benchmarks") or []
    anchors = inner.get("feature_anchors") or {}
    centroids_raw = (anchors.get("subpattern_centroids") or {}).copy()
    centroids = {
        k: (v.get("centroid_vector") if isinstance(v, dict) else v)
        for k, v in centroids_raw.items()
        if (v.get("centroid_vector") if isinstance(v, dict) else v) is not None
    }

    cases = []
    for b in benchmarks:
        t = b.get("t")
        if not t or len(t) != 5:
            continue
        vec = np.array(t, dtype=float)
        subpattern = _assign_subpattern_by_centroid(vec, centroids)
        cases.append({
            "point": t,
            "ref": b.get("ref", ""),
            "note": b.get("note", ""),
            "subpattern": subpattern,
        })
    return cases, centroids


def load_extended_samples(path: Path) -> List[Dict]:
    """
    从扩展样本文件加载案例（JSON 数组，每项含 t/point, ref, note, subpattern 等）。
    用于后续对接 11 万样本导出文件。
    """
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        raw = raw.get("samples", raw.get("cases", []))
    cases = []
    for item in raw:
        t = item.get("t") or item.get("point")
        if t is None or len(t) != 5:
            continue
        cases.append({
            "point": list(t),
            "ref": item.get("ref", ""),
            "note": item.get("note", ""),
            "subpattern": item.get("subpattern", "A-01-S1"),
            "is_singularity": item.get("is_singularity", False),
        })
    return cases


def load_full_index_cache(
    cache_dir: Path,
    registry_path: Optional[Path] = None,
) -> Tuple[List[Dict], Dict[str, List[float]]]:
    """
    第 028 号：从 scripts/build_a01_full_index 产出的缓存加载全量样本。
    需存在 a01_full_points.npz 与 a01_full_meta.json。
    返回 (cases, centroids)；cases 每项含 point, ref, subpattern, note 等，subpattern 由质心补全。
    """
    points_path = cache_dir / "a01_full_points.npz"
    meta_path = cache_dir / "a01_full_meta.json"
    if not points_path.exists() or not meta_path.exists():
        return [], {}

    points = np.load(points_path)["points"]
    with open(meta_path, "r", encoding="utf-8") as f:
        meta_list = json.load(f)
    if len(meta_list) != len(points):
        logger.warning("Full index meta length != points length, skipping cache")
        return [], {}

    _, centroids = load_registry_benchmarks(registry_path or _DEFAULT_REGISTRY)
    cases = []
    for i, m in enumerate(meta_list):
        pt = points[i].tolist()
        sp = m.get("subpattern") or _assign_subpattern_by_centroid(points[i], centroids)
        cases.append({
            "point": pt,
            "ref": m.get("ref", f"A01-{i}"),
            "note": m.get("note", ""),
            "subpattern": sp,
            "line_index": m.get("line_index"),
        })
    logger.info("Loaded full index from cache: %d samples", len(cases))
    return cases, centroids


class CaseRetriever:
    """
    基于 5D 坐标的最近邻案例检索器。
    全量索引时使用 scipy.spatial.cKDTree（<50ms）；否则 NumPy 暴力 KNN。
    """

    def __init__(
        self,
        registry_path: Optional[Path] = None,
        extended_path: Optional[Path] = None,
        cache_dir: Optional[Path] = None,
        singularities: Optional[List[str]] = None,
    ):
        """
        registry_path: A-01.json 路径
        extended_path: 可选扩展样本 JSON 路径（含更多 5D 样本）
        cache_dir: 第 028 号全量缓存目录（含 a01_full_points.npz + a01_full_meta.json）时优先加载
        singularities: 奇点 case ref 列表，检索结果中会标记并优先展示
        """
        self._cases: List[Dict] = []
        self._centroids: Dict[str, List[float]] = {}
        self._singularities = set(singularities or [])
        self._points: Optional[np.ndarray] = None  # (N, 5)
        self._tree: Optional[Any] = None  # scipy.spatial.cKDTree

        cache_dir = cache_dir or _PROJECT_ROOT / "data_local"
        full_cases, self._centroids = load_full_index_cache(cache_dir, registry_path)
        if full_cases:
            self._cases = full_cases
            self._points = np.array([c["point"] for c in self._cases], dtype=np.float64)
            for c in self._cases:
                c["is_singularity"] = c.get("ref", "") in self._singularities
            if _SCIPY_AVAILABLE and len(self._cases) > 1000:
                self._tree = cKDTree(self._points)
                logger.info("CaseRetriever: KDTree built for %d samples", len(self._cases))
            else:
                logger.info("CaseRetriever loaded %d A-01 samples (full index)", len(self._cases))
        else:
            cases, self._centroids = load_registry_benchmarks(registry_path)
            if extended_path:
                ext = load_extended_samples(extended_path)
                by_ref = {c["ref"]: c for c in cases}
                for c in ext:
                    by_ref[c["ref"]] = {**c, "point": c.get("point") or c.get("t")}
                cases = list(by_ref.values())
            for c in cases:
                c.setdefault("subpattern", _assign_subpattern_by_centroid(np.array(c["point"]), self._centroids))
                c["is_singularity"] = c.get("ref", "") in self._singularities
            self._cases = cases
            if self._cases:
                self._points = np.array([c["point"] for c in self._cases], dtype=float)
            logger.info("CaseRetriever loaded %d A-01 samples", len(self._cases))

    def find_nearest_cases(
        self,
        user_point: Union[Dict[str, float], List[float]],
        top_n: int = 3,
        include_singularity_hint: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        返回与 user_point 欧氏距离最近的 top_n 个案例。
        全量索引时走 KDTree，目标 <50ms；否则暴力 KNN。
        每项包含: point, ref, note, subpattern, distance, similarity_pct, is_singularity。
        """
        if not self._cases or self._points is None:
            return []

        vec = _point_to_vector(user_point)
        k = min(top_n, len(self._cases))

        if self._tree is not None:
            d_arr, i_arr = self._tree.query(vec.reshape(1, -1), k=k)
            d_arr = np.atleast_1d(d_arr.ravel())
            i_arr = np.atleast_1d(i_arr.ravel())
        else:
            vec2 = np.reshape(vec, (1, 5))
            dists_all = np.linalg.norm(self._points - vec2, axis=1)
            i_arr = np.argsort(dists_all)[:k]
            d_arr = dists_all[i_arr]

        d_max = float(np.max(d_arr)) if d_arr.size else 1.0
        if d_max <= 0:
            d_max = 1.0

        out = []
        for j in range(len(i_arr)):
            i = int(i_arr[j])
            d = float(d_arr[j])
            c = dict(self._cases[i])
            c["distance"] = round(d, 4)
            c["similarity_pct"] = round(max(0, 100 * (1 - d / d_max)), 1)
            c["is_singularity"] = c.get("ref", "") in self._singularities
            out.append(c)

        if include_singularity_hint and self._singularities:
            in_result = {r["ref"] for r in out}
            for ref in self._singularities:
                if ref in in_result:
                    continue
                for j, c in enumerate(self._cases):
                    if c.get("ref") == ref:
                        d = float(np.linalg.norm(self._points[j] - vec))
                        out.append({
                            **dict(c),
                            "distance": round(d, 4),
                            "similarity_pct": round(max(0, 100 * (1 - d / d_max)), 1),
                            "is_singularity": True,
                        })
                        break
            out.sort(key=lambda x: x["distance"])
            out = out[:top_n]

        return out

    @property
    def case_count(self) -> int:
        return len(self._cases)

    def get_singularities(self, limit: int = 10) -> List[Dict]:
        """返回已标记的奇点案例（用于固定展示）。若未配置 singularities，则按距离质心最远或代表性选取 limit 个。"""
        if self._singularities:
            out = [c for c in self._cases if c.get("ref") in self._singularities][:limit]
            return out
        # 否则用 benchmarks 前 limit 个作为“代表”（可改为按到质心距离等策略）
        return self._cases[:limit]


def get_default_retriever(
    extended_path: Optional[Path] = None,
    cache_dir: Optional[Path] = None,
    singularity_refs: Optional[List[str]] = None,
) -> CaseRetriever:
    """
    获取默认 A-01 案例检索器。
    若 cache_dir（默认 data_local）存在 a01_full_points.npz + a01_full_meta.json，则使用全量 KDTree 索引。
    singularity_refs: 奇点 ref 列表；None 时使用内置建议。
    """
    default_singularities = [
        "CASE-000003", "CASE-000008", "CASE-000022", "CASE-000039", "CASE-000051",
        "CASE-000060", "CASE-000080", "CASE-000119", "CASE-000117", "CASE-000044",
    ]
    refs = singularity_refs or default_singularities
    return CaseRetriever(
        registry_path=_DEFAULT_REGISTRY,
        extended_path=extended_path,
        cache_dir=cache_dir or _PROJECT_ROOT / "data_local",
        singularities=refs[:10],
    )
