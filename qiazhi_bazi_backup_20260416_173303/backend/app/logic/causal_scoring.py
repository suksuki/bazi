"""
V6.1 因果评分：比较 physics 张量前后态，输出加权决策分（0..1）。
"""
from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Mapping, Optional, Tuple

from app.logic.pattern_physics import calculate_pattern_proximity

W_PATTERN = 0.4
W_STABILITY = 0.3
W_ENTROPY = 0.2
W_RISK = 0.1

_FOLLOWER_PATTERN_IDS = frozenset({"FOLLOW_CHILD", "FOLLOW_WEALTH", "FOLLOW_STRONG"})


def _resolve_metadata(tensor: Mapping[str, Any], metadata: Optional[Mapping[str, Any]]) -> Mapping[str, Any]:
    if metadata is not None:
        return metadata if isinstance(metadata, dict) else {}
    meta = tensor.get("meta")
    return meta if isinstance(meta, dict) else {}


def _follower_progress_stability(
    tensor: Mapping[str, Any], metadata: Optional[Mapping[str, Any]]
) -> Tuple[float, float, str]:
    """从格系：manifest 引擎中 FOLLOW_* 格局最高 affinity 及其 stability 与显示名。"""
    rows = calculate_pattern_proximity(tensor, metadata)
    follower = [r for r in rows if str(r.get("pattern_id") or "") in _FOLLOWER_PATTERN_IDS]
    if not follower:
        top = rows[0] if rows else {}
        return (
            float(top.get("progress") or 0.0),
            float(top.get("stability") or 0.0),
            str(top.get("name") or ""),
        )
    best = max(follower, key=lambda r: float(r.get("progress") or 0.0))
    return (
        float(best.get("progress") or 0.0),
        float(best.get("stability") or 0.0),
        str(best.get("name") or ""),
    )


def _entropy_value(tensor: Mapping[str, Any]) -> Optional[float]:
    meta = tensor.get("meta") if isinstance(tensor.get("meta"), dict) else {}
    ge = meta.get("global_entropy")
    if isinstance(ge, (int, float)) and not isinstance(ge, bool) and ge == ge:
        v = float(ge)
        if math.isfinite(v):
            return max(0.0, min(1.0, v))
    return None


def _risk_hits(tensor: Mapping[str, Any], metadata: Optional[Mapping[str, Any]]) -> int:
    """玫瑰色 / [CRITICAL] 在整包快照中的出现次数（越高越糟）。"""
    bundle: Dict[str, Any] = {"physics_tensor": dict(tensor) if isinstance(tensor, dict) else {}}
    if metadata is not None:
        bundle["metadata"] = dict(metadata) if isinstance(metadata, dict) else metadata
    s = json.dumps(bundle, ensure_ascii=False, default=str)
    return s.count("[CRITICAL]") + s.count("玫瑰色")


def _clamp01(x: float) -> float:
    if not math.isfinite(x):
        return 0.0
    return max(0.0, min(1.0, x))


def calculate_decision_score(
    tensor_before: Mapping[str, Any],
    tensor_after: Mapping[str, Any],
    metadata_before: Optional[Mapping[str, Any]] = None,
    metadata_after: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """
    加权总分 ∈[0,1]；各子项先归一化到 [0,1] 再乘权重。
    - Pattern_Boost：从格系达成度 Progress 的提升
    - Stability_Gain：同上主格局的 stability 提升
    - Entropy_Reduction：meta.global_entropy 下降（缺失则子项记 0）
    - Risk_Avoidance：CRITICAL/玫瑰色 命中次数下降
    """
    mb = _resolve_metadata(tensor_before, metadata_before)
    ma = _resolve_metadata(tensor_after, metadata_after)

    prog_b, stab_b, name_b = _follower_progress_stability(tensor_before, mb)
    prog_a, stab_a, name_a = _follower_progress_stability(tensor_after, ma)

    pattern_delta = max(0.0, prog_a - prog_b)
    # 若主格局名变化，稳定性差分取「after 主从格」相对「before 同名的 stability」若存在，否则用 after stab - before stab
    if name_a and name_a == name_b:
        stab_delta = max(0.0, stab_a - stab_b)
    else:
        rows_b = {str(r.get("name")): float(r.get("stability") or 0.0) for r in calculate_pattern_proximity(tensor_before, mb)}
        stab_prev_for_name = float(rows_b.get(name_a, stab_b))
        stab_delta = max(0.0, stab_a - stab_prev_for_name)

    ent_b = _entropy_value(tensor_before)
    ent_a = _entropy_value(tensor_after)
    if ent_b is not None and ent_a is not None:
        ent_reduction = max(0.0, ent_b - ent_a)
        entropy_component = _clamp01(ent_reduction / 0.35)
    else:
        entropy_component = 0.0

    risk_b = _risk_hits(tensor_before, mb)
    risk_a = _risk_hits(tensor_after, ma)
    risk_drop = max(0.0, float(risk_b - risk_a))
    denom = max(1, risk_b, risk_a)
    risk_component = _clamp01(risk_drop / float(denom))

    pattern_component = _clamp01(pattern_delta / 0.14)
    stability_component = _clamp01(stab_delta / 0.12)

    total = (
        W_PATTERN * pattern_component
        + W_STABILITY * stability_component
        + W_ENTROPY * entropy_component
        + W_RISK * risk_component
    )

    return {
        "total_score": round(float(total), 6),
        "weights": {
            "pattern": W_PATTERN,
            "stability": W_STABILITY,
            "entropy": W_ENTROPY,
            "risk": W_RISK,
        },
        "components": {
            "pattern_boost": round(pattern_component, 6),
            "stability_gain": round(stability_component, 6),
            "entropy_reduction": round(entropy_component, 6),
            "risk_avoidance": round(risk_component, 6),
        },
        "raw": {
            "follower_progress_before": round(prog_b, 6),
            "follower_progress_after": round(prog_a, 6),
            "follower_stability_before": round(stab_b, 6),
            "follower_stability_after": round(stab_a, 6),
            "follower_name_before": name_b,
            "follower_name_after": name_a,
            "entropy_before": ent_b,
            "entropy_after": ent_a,
            "risk_hits_before": risk_b,
            "risk_hits_after": risk_a,
        },
    }
