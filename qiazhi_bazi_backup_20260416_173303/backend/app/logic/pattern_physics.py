"""
格局时空波动与 L2 兼容层：不再使用十神质心向量；格局达成度统一由 manifest 引擎计算。

`calculate_pattern_proximity` / `pattern_thresholds_for_sse` 仅为历史 API 名保留，
内部 **100%** 委托 `UniversalPatternEngine`（pattern_manifest.json）。
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

# 与 will_injection / 前端 TEN_GOD_ORDER 对齐
_TEN_GODS: Tuple[str, ...] = ("比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印")

# 格局名 → 在 conflict detail 中匹配的语义关键词（命中且为刑冲害破时计入波动）
PATTERN_CONFLICT_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "从财格": ("财", "偏财", "正财", "财星"),
    "从官格": ("官", "正官", "七杀", "官杀"),
    "从儿格": ("食神", "伤官", "食伤"),
    "专旺·比劫": ("比劫", "比肩", "劫财"),
    "印绶格": ("印", "正印", "偏印"),
}


def _float_scores(raw: Any) -> Dict[str, float]:
    out: Dict[str, float] = {}
    if not isinstance(raw, dict):
        return out
    for k, v in raw.items():
        ks = str(k).strip()
        if not ks:
            continue
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            fv = float(v)
            if fv == fv and fv >= 0.0:
                out[ks] = fv
    return out


def _normalize_distribution(weights: Mapping[str, float]) -> List[float]:
    vec = [max(0.0, float(weights.get(g, 0.0))) for g in _TEN_GODS]
    s = sum(vec)
    if s <= 1e-12:
        return [1.0 / len(_TEN_GODS)] * len(_TEN_GODS)
    return [v / s for v in vec]


def _conflict_points(metadata: Mapping[str, Any]) -> List[Dict[str, Any]]:
    cm = metadata.get("conflict_matrix") if isinstance(metadata.get("conflict_matrix"), dict) else {}
    pts = cm.get("points")
    if not isinstance(pts, list):
        return []
    return [p for p in pts if isinstance(p, dict)]


def _kind_base_severity(kind: str) -> float:
    k = str(kind or "").strip().lower()
    if k == "clash":
        return 0.28
    if k in ("punish", "xing", "刑"):
        return 0.2
    if k == "harm" or k == "害":
        return 0.14
    if k in ("po", "破"):
        return 0.11
    return 0.06


def _positions_blob(positions: Any) -> str:
    if not isinstance(positions, list):
        return ""
    return " ".join(str(x) for x in positions).lower()


def _temporal_lane_boost(positions_blob: str, detail: str) -> float:
    """流年/大运相关冲克加权（启发式）。"""
    mul = 1.0
    if "流年" in detail or "岁运" in detail or "liunian" in positions_blob or "annual" in positions_blob:
        mul *= 1.24
    if "大运" in detail or "dayun" in positions_blob or "luck" in positions_blob:
        mul *= 1.14
    return mul


def _pattern_keyword_hit(pattern_name: str, detail: str) -> float:
    keys = PATTERN_CONFLICT_KEYWORDS.get(pattern_name, ())
    if not keys:
        return 0.0
    for kw in keys:
        if kw and kw in detail:
            return 1.0
    return 0.0


def temporal_volatility_for_pattern(pattern_name: str, metadata: Mapping[str, Any]) -> float:
    """
    时空波动率 ∈[0,1]：冲突矩阵中与该格局语义相关、且偏「流年/大运」轴的刑冲害破累积。
    """
    acc = 0.0
    for p in _conflict_points(metadata):
        detail = str(p.get("detail") or "")
        hit = _pattern_keyword_hit(pattern_name, detail)
        if hit <= 0.0:
            continue
        kind = str(p.get("kind") or "")
        pos_b = _positions_blob(p.get("positions"))
        sev = _kind_base_severity(kind) * hit * _temporal_lane_boost(pos_b, detail)
        acc += sev
    return min(1.0, acc)


def _resolve_metadata(tensor: Mapping[str, Any], metadata: Optional[Mapping[str, Any]]) -> Mapping[str, Any]:
    if metadata is not None:
        return metadata
    meta = tensor.get("meta")
    if isinstance(meta, dict):
        return meta
    return {}


def calculate_pattern_proximity(
    tensor: Mapping[str, Any],
    metadata: Optional[Mapping[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    返回各格局的 progress、stability（manifest 引擎 affinity + temporal_volatility 下调 stability）。

    V7.0：已删除质心余弦近似，全部委托 ``UniversalPatternEngine.evaluate``。
    """
    from app.logic.patterns.engine import UniversalPatternEngine

    meta_bundle = _resolve_metadata(tensor, metadata)
    raw_rows = UniversalPatternEngine().evaluate(tensor, meta_bundle if isinstance(meta_bundle, dict) else {})
    rows: List[Dict[str, Any]] = []
    for r in raw_rows:
        if not isinstance(r, dict):
            continue
        name = str(r.get("name") or "").strip()
        if not name:
            continue
        prog = float(r.get("affinity_score") if r.get("affinity_score") is not None else r.get("progress") or 0.0)
        stab = float(r.get("stability") or 0.0)
        tv = float(r.get("temporal_volatility") or 0.0)
        pid = str(r.get("pattern_id") or "").strip()
        row_out: Dict[str, Any] = {
            "name": name,
            "progress": max(0.0, min(1.0, prog)),
            "stability": max(0.0, min(1.0, stab)),
            "temporal_volatility": max(0.0, min(1.0, tv)),
        }
        if pid:
            row_out["pattern_id"] = pid
        rows.append(row_out)
    rows.sort(key=lambda x: float(x["progress"]), reverse=True)
    return rows


def pattern_thresholds_for_sse(
    tensor: Mapping[str, Any],
    metadata: Optional[Mapping[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """兼容名：SSE 旧字段子集；数据仍全部来自 manifest 引擎。"""
    return [
        {
            "name": str(r["name"]),
            "progress": float(r["progress"]),
            "stability": float(r["stability"]),
            "temporal_volatility": float(r.get("temporal_volatility", 0.0)),
        }
        for r in calculate_pattern_proximity(tensor, metadata)
    ]


def benchmark_pattern_proximity_ms(tensor: Mapping[str, Any], iterations: int = 200) -> float:
    """开发/测试用：估算单次 manifest 格局评估耗时（毫秒）。"""
    t0 = time.perf_counter()
    for _ in range(max(1, iterations)):
        calculate_pattern_proximity(tensor)
    return (time.perf_counter() - t0) * 1000.0 / float(max(1, iterations))
