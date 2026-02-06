"""
FDS Inference Engine (A-01)
---------------------------
Real-time manifold projection + sub-pattern mapping + KB injection.

Responsibilities:
- Normalize Ten-Gods vectors (accepts UI/engine-friendly keys)
- Project into 5D using tensor_mapping_matrix
- Compute Euclidean distance to subpattern centroids (A-01-S1/S2)
- Provide similarity score, offsets, and knowledge snippets
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from core.tensor_mapping_loader import load_tensor_mapping_matrix

try:
    from json_logic import jsonLogic  # type: ignore
    _JSON_LOGIC_AVAILABLE = True
except ImportError:
    jsonLogic = None  # type: ignore
    _JSON_LOGIC_AVAILABLE = False

# 当严格判定库缺失时，UI 可展示的降级提示
ENGINE_NOTE_FALLBACK = (
    "[ENGINE NOTE] 正在使用基础逻辑判定，建议安装严格判定库以激活 Manifest 法律全文校验。"
)


class FDSInferenceEngine:
    """Manifold projection and sub-pattern mapping for A-01."""

    DEFAULT_REGISTRY = Path("registry/holographic_pattern/A-01.json")
    DEFAULT_KB = Path("knowledge/holographic_pattern/A-01_kb.json")
    DEFAULT_MANIFEST = Path("config/patterns/manifest_A01.json")

    # UI/engine friendly aliases -> standard ten-god code
    TEN_GOD_ALIASES: Dict[str, str] = {
        "ZhengGuan": "ZG",
        "正官": "ZG",
        "ZG": "ZG",
        "QiSha": "PG",
        "偏官": "PG",
        "七杀": "PG",
        "PG": "PG",
        "ZhengCai": "ZR",
        "正财": "ZR",
        "ZR": "ZR",
        "PianCai": "PR",
        "偏财": "PR",
        "PR": "PR",
        "ShiShen": "ZS",
        "食神": "ZS",
        "ZS": "ZS",
        "ShangGuan": "PS",
        "伤官": "PS",
        "PS": "PS",
        "ZhengYin": "ZC",
        "正印": "ZC",
        "ZC": "ZC",
        "PianYin": "PC",
        "枭神": "PC",
        "PC": "PC",
        "BiJian": "ZB",
        "比肩": "ZB",
        "ZB": "ZB",
        "JieCai": "PB",
        "劫财": "PB",
        "PB": "PB",
    }

    DIM_KEYS = ["E", "O", "M", "S", "R"]

    def __init__(
        self,
        registry_path: Path | str | None = None,
        kb_path: Path | str | None = None,
        manifest_path: Path | str | None = None,
    ) -> None:
        self.registry_path = Path(registry_path or self.DEFAULT_REGISTRY)
        self.kb_path = Path(kb_path or self.DEFAULT_KB)
        self.manifest_path = Path(manifest_path or self.DEFAULT_MANIFEST)

        self.registry = self._load_json(self.registry_path)
        self.kb = self._load_json(self.kb_path)
        self.manifest = self._load_json(self.manifest_path)

        # 全局优先：V4.0-BETA 真理矩阵 > manifest > registry
        self.tmm, self.matrix_version = load_tensor_mapping_matrix(
            self.manifest, registry=self.registry
        )

        self.ten_god_order: List[str] = self.tmm["ten_gods"]
        self.weight_matrix = np.array(
            [self.tmm["weights"][god] for god in self.ten_god_order], dtype=float
        )  # shape: (10, 5)
        self.god_index_map = {g: i for i, g in enumerate(self.ten_god_order)}

        # Centroids
        centroids = (
            self.registry.get("data", {})
            .get("feature_anchors", {})
            .get("subpattern_centroids", {})
        )
        if not centroids:
            raise ValueError("subpattern_centroids missing in registry")
        self.centroids = {
            cid: np.array(info["centroid_vector"], dtype=float)
            for cid, info in centroids.items()
        }

        # Knowledge map keyed by pattern_id (A-01-S1/S2)
        self.knowledge_map = {
            entry.get("pattern_id"): entry
            for entry in self.kb.get("knowledge_entries", [])
        }

        # Classical logic (optional) for trigger gating
        self.classical_logic = self.manifest.get("classical_logic_rules", {}).get(
            "expression"
        )

    # ------------------------------------------------------------------ #
    # Data loaders
    # ------------------------------------------------------------------ #
    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------------------------------------------ #
    # Input normalization
    # ------------------------------------------------------------------ #
    def normalize_ten_gods(self, raw: Dict[str, Any]) -> Dict[str, float]:
        """
        Normalize incoming ten-god dict into standard codes used by TMM.
        Supports flat numeric values or {mean: x} objects.
        """
        normalized: Dict[str, float] = {}
        for k, v in raw.items():
            code = self.TEN_GOD_ALIASES.get(k)
            if not code:
                continue
            val = self._extract_value(v)
            normalized[code] = val
        return normalized

    @staticmethod
    def _extract_value(val: Any) -> float:
        """Extract numeric value from raw/mean container."""
        if isinstance(val, dict):
            for candidate in ("mean", "value", "strength", "score"):
                if candidate in val:
                    return float(val[candidate])
        try:
            return float(val)
        except Exception:
            return 0.0

    # ------------------------------------------------------------------ #
    # Projection & inference
    # ------------------------------------------------------------------ #
    def project_to_5d(self, ten_gods: Dict[str, float]) -> np.ndarray:
        """Project normalized ten-gods vector into 5D manifold coordinates."""
        vec = np.zeros(len(self.ten_god_order), dtype=float)
        for god, val in ten_gods.items():
            if god in self.god_index_map:
                vec[self.god_index_map[god]] = val
        # (10,5)^T dot (10,) -> (5,)
        return np.dot(self.weight_matrix.T, vec)

    def infer(
        self,
        raw_ten_gods: Dict[str, Any],
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Full inference pipeline:
        - normalize input
        - project to 5D
        - compute distances/similarity
        - attach knowledge
        """
        ten_gods = (
            raw_ten_gods
            if set(raw_ten_gods.keys()).issubset(set(self.ten_god_order))
            else self.normalize_ten_gods(raw_ten_gods)
        )
        point = self.project_to_5d(ten_gods)

        distances = {
            cid: float(np.linalg.norm(point - centroid))
            for cid, centroid in self.centroids.items()
        }
        # Lightweight similarity: score=1/(1+D) then normalized
        raw_scores = {cid: 1.0 / (1.0 + d) for cid, d in distances.items()}
        score_sum = sum(raw_scores.values()) or 1.0
        norm_scores = {cid: s / score_sum for cid, s in raw_scores.items()}
        ranked = sorted(norm_scores.items(), key=lambda x: x[1], reverse=True)
        best_id, best_score = ranked[0]
        second_id, second_score = ranked[1] if len(ranked) > 1 else (None, 0.0)

        # Hybrid if near perpendicular bisector
        hybrid = False
        if second_id and abs(distances[best_id] - distances[second_id]) <= max(
            0.1, 0.05 * max(distances[best_id], distances[second_id])
        ):
            hybrid = True

        offset_vector = point - self.centroids[best_id]

        knowledge = self.knowledge_map.get(best_id, {})

        return {
            "pattern_id": "A-01",
            "matrix_version": self.matrix_version,
            "best_subpattern": best_id,
            "runner_up": second_id,
            "point": self._vector_to_dict(point),
            "offset": self._vector_to_dict(offset_vector),
            "distances": distances,
            "raw_scores": raw_scores,
            "normalized_scores": norm_scores,
            "similarity_score": best_score,
            "similarity_percent": round(best_score * 100, 2),
            "is_hybrid": hybrid,
            "knowledge": knowledge,
            "extra_context": extra_context or {},
        }

    # ------------------------------------------------------------------ #
    # Logic gating
    # ------------------------------------------------------------------ #
    def matches_classical_logic(
        self, raw_ten_gods: Dict[str, Any], self_energy: Optional[Dict[str, Any]] = None
    ) -> Optional[bool]:
        """
        Evaluate classical logic expression (if available).
        Returns None when jsonLogic is unavailable.
        """
        if not self.classical_logic or not _JSON_LOGIC_AVAILABLE:
            return None

        normalized = self.normalize_ten_gods(raw_ten_gods)
        context = {
            "ten_gods": normalized,
            "self_energy": self_energy or {},
        }
        try:
            return bool(jsonLogic(self.classical_logic, context))
        except Exception:
            return None

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _vector_to_dict(self, vec: np.ndarray) -> Dict[str, float]:
        return {dim: float(val) for dim, val in zip(self.DIM_KEYS, vec)}

    def format_offsets(self, offset: Dict[str, float]) -> str:
        """Generate a compact offset string for UI."""
        return " | ".join(f"{k}:{v:+.2f}" for k, v in offset.items())

    @staticmethod
    def strict_logic_available() -> bool:
        """Whether Manifest 法律全文校验可用（依赖 json-logic-quibble）。"""
        return _JSON_LOGIC_AVAILABLE


__all__ = ["FDSInferenceEngine", "ENGINE_NOTE_FALLBACK"]
