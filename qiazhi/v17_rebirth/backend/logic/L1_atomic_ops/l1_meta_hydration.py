"""
V17.13：将四柱地支/天干几何判定写入 physics_tensor.meta，驱动 ManifestOperatorPlugin 从占位 → 命中。
"""
from __future__ import annotations

from typing import Any, Dict, List

from v17_rebirth.backend.logic.L1_atomic_ops.branch_stem_geometry import (
    branches_and_stems_from_four_pillars,
    detect_stem_fusion_cases,
    eval_banhe_hits,
    eval_liu_chong_hits,
    eval_liu_hai_hits,
    eval_liu_po_hits,
    eval_liuhe_hits,
    sanxing_detect_geometry,
    summarize_sanxing_branches,
)
from v17_rebirth.backend.logic.L1_atomic_ops.v17_op_fact import generate_v17_fact_from_op


def _scalar_intensity(count: int, *, per: float = 0.36, bump: float = 0.09) -> float:
    """冲/害/破等：条数越多烈度越高，上限 1.0（内部标量，不上屏为 Abs）。"""
    if count <= 0:
        return 0.0
    return min(1.0, per * count + max(0, count - 1) * bump)


def _tier_cn(x: float) -> str:
    if x >= 0.72:
        return "猛"
    if x >= 0.38:
        return "中"
    if x <= 1e-9:
        return "无"
    return "轻"


def _sanxing_intensity(n_edges: int, branches_present: set[str]) -> float:
    if n_edges <= 0:
        return 0.0
    trip = all(b in branches_present for b in ("寅", "巳", "申"))
    base = min(1.0, 0.26 * n_edges + (0.34 if trip else 0.0))
    return min(1.0, base + (0.18 if n_edges >= 3 else 0.0))


def _pair_labels(hits: List[Dict[str, Any]]) -> List[str]:
    out: List[str] = []
    for h in hits:
        pr = h.get("pair")
        if isinstance(pr, list) and len(pr) >= 2:
            out.append(f"{pr[0]}{pr[1]}")
    return out


def hydrate_v17_physics_tensor(pt: Dict[str, Any]) -> None:
    """幂等：向 pt.meta 写入 interaction_v2 / l1_manifest_hits / L2 辅助键。"""
    if not isinstance(pt, dict):
        return
    meta = pt.get("meta")
    if isinstance(meta, dict) and meta.get("_v17_hydrated"):
        meta.setdefault("v17_physics_stable", True)
        return

    branches, stems = branches_and_stems_from_four_pillars(pt.get("four_pillars"))
    liu_chong = eval_liu_chong_hits(branches) if branches else []
    liu_hai = eval_liu_hai_hits(branches) if branches else []
    liu_po = eval_liu_po_hits(branches) if branches else []
    liu_he = eval_liuhe_hits(branches) if branches else []
    ban_he = eval_banhe_hits(branches) if branches else []
    sanxing_geo = sanxing_detect_geometry(branches) if branches else []
    stem_cases = detect_stem_fusion_cases(stems, branches) if stems else []

    meta = pt.setdefault("meta", {})
    if not isinstance(meta, dict):
        return

    meta["interaction_v2"] = {
        "version": "interaction_v2.v1",
        "liu_chong": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in liu_chong],
        "liu_hai": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in liu_hai],
        "liu_po": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in liu_po],
        "liu_he": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in liu_he],
        "ban_he": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in ban_he],
        "sanxing": [{"branches": h.get("branches"), "edge": h.get("edge")} for h in sanxing_geo],
    }

    meta["stem_fusion_v1"] = {
        "version": "stem_fusion.v1",
        "cases": stem_cases,
        "has_stuck": any(str(c.get("mode")) == "stuck" for c in stem_cases),
        "has_transform": any(str(c.get("mode")) == "transformed" for c in stem_cases),
    }

    br_set = {str(b) for b in branches.values() if b}
    ch_i = _scalar_intensity(len(liu_chong), per=0.39, bump=0.11)
    hai_i = _scalar_intensity(len(liu_hai), per=0.33, bump=0.07)
    po_i = _scalar_intensity(len(liu_po), per=0.33, bump=0.07)
    he_i = _scalar_intensity(len(liu_he), per=0.28, bump=0.05)
    ban_i = _scalar_intensity(len(ban_he), per=0.3, bump=0.06)
    sx_i = _sanxing_intensity(len(sanxing_geo), br_set)
    stem_i = _scalar_intensity(len(stem_cases), per=0.31, bump=0.04)

    pt["interaction_delta"] = {
        "version": "l1_delta.v2",
        "n_liu_chong": len(liu_chong),
        "n_liu_hai": len(liu_hai),
        "n_liu_po": len(liu_po),
        "n_liu_he": len(liu_he),
        "n_ban_he": len(ban_he),
        "n_sanxing_edges": len(sanxing_geo),
        "n_stem_fusion_cases": len(stem_cases),
        "chong_intensity": round(ch_i, 4),
        "chong_tier": _tier_cn(ch_i),
        "sanxing_intensity": round(sx_i, 4),
        "sanxing_tier": _tier_cn(sx_i),
        "hai_intensity": round(hai_i, 4),
        "hai_tier": _tier_cn(hai_i),
        "po_intensity": round(po_i, 4),
        "po_tier": _tier_cn(po_i),
        "he_intensity": round(he_i, 4),
        "he_tier": _tier_cn(he_i),
        "ban_he_intensity": round(ban_i, 4),
        "ban_he_tier": _tier_cn(ban_i),
        "stem_fusion_intensity": round(stem_i, 4),
        "stem_fusion_tier": _tier_cn(stem_i),
        "yin_si_shen_complete": all(b in br_set for b in ("寅", "巳", "申")),
    }

    hits: Dict[str, Dict[str, Any]] = {}

    if liu_chong:
        labs = _pair_labels(liu_chong)
        hits["l1.physics.op_branch_liuchong"] = {
            "fact": generate_v17_fact_from_op(kind="liu_chong", detail="".join(labs)),
            "label": "六冲",
            "priority": 0.72,
        }

    if sanxing_geo:
        sx = summarize_sanxing_branches(sanxing_geo)
        hits["l1.physics.op_branch_sanxing"] = {
            "fact": generate_v17_fact_from_op(kind="sanxing", branches=[sx] if sx else []),
            "label": "三刑",
            "priority": 0.71,
        }

    if liu_hai:
        hits["l1.physics.op_branch_liuhai"] = {
            "fact": generate_v17_fact_from_op(kind="liu_hai", detail="".join(_pair_labels(liu_hai))),
            "label": "六害",
            "priority": 0.7,
        }

    if liu_po:
        hits["l1.physics.op_branch_liupo"] = {
            "fact": generate_v17_fact_from_op(kind="liu_po", detail="".join(_pair_labels(liu_po))),
            "label": "六破",
            "priority": 0.69,
        }

    if liu_he:
        hits["l1.physics.op_branch_liuhe"] = {
            "fact": generate_v17_fact_from_op(kind="liu_he", detail="".join(_pair_labels(liu_he))),
            "label": "六合",
            "priority": 0.68,
        }

    for c in stem_cases:
        mode = str(c.get("mode") or "")
        sa, sb = (c.get("stems") or ["", ""])[:2]
        hua = str(c.get("hua_element") or "")
        detail = f"{sa}{sb}→{hua}" if hua else f"{sa}{sb}"
        if mode == "stuck":
            pid = "l1.physics.op_stem_fusion_stuck"
            if pid not in hits:
                hits[pid] = {
                    "fact": generate_v17_fact_from_op(kind="stem_stuck", detail=detail),
                    "label": "天干羁绊",
                    "priority": 0.67,
                }
        elif mode == "transformed":
            pid = "l1.physics.op_stem_fusion_transform"
            if pid not in hits:
                hits[pid] = {
                    "fact": generate_v17_fact_from_op(kind="stem_transform", detail=detail),
                    "label": "天干化气",
                    "priority": 0.66,
                }

    meta["l1_manifest_hits"] = hits

    # L2 轻量：格局名供 classical.pattern_detector.v2 读取（无数值）
    deity_scores = pt.get("deity_scores") if isinstance(pt.get("deity_scores"), dict) else {}
    meta["hit_pattern_name"] = _resolve_pattern_label(deity_scores)
    meta["blind_work_hint"] = _blind_work_hint(branches, sanxing_geo, liu_chong)

    meta["_v17_hydrated"] = True
    meta["v17_physics_stable"] = True


def _resolve_pattern_label(deity_scores: Dict[str, Any]) -> str:
    if not deity_scores:
        return "未定格局"
    try:
        ranked = sorted(
            ((str(k), float(v)) for k, v in deity_scores.items()),
            key=lambda kv: kv[1],
            reverse=True,
        )
    except (TypeError, ValueError):
        return "未定格局"
    if not ranked:
        return "未定格局"
    name, score = ranked[0]
    if name == "正官" and score >= 40:
        return "正官格势强"
    if name in {"食神", "伤官"} and score >= 35:
        return "食伤外放格"
    if name in {"偏财", "正财"} and score >= 35:
        return "财星主导格"
    return f"{name}主轴格"


def _blind_work_hint(
    _branches: Dict[str, str],
    sanxing: List[Dict[str, Any]],
    chong: List[Dict[str, Any]],
) -> str:
    """极简盲派做功提示：三刑聚势 / 冲动做功。"""
    sx = summarize_sanxing_branches(sanxing)
    if sx and all(x in sx for x in ("寅", "巳", "申")):
        return "无恩三刑聚势"
    if chong:
        return "支冲牵动做功"
    return ""
