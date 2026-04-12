"""天干五合：邻柱合、化神约束；不化则 STUCK（羁绊）路由锁死，化真则标记 Deprecated 并向化神五行泄漏向量。"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Tuple

from app.skills.physics_rules import STEM_TO_ELEMENT, TEN_DEITIES, deity_from_self_and_target_stem

OP_ID = "L1_OP_STEM_FUSION"

# (干甲, 干乙, 化气五行 key 与 physics vector 一致)
_FUSION_ROWS: Tuple[Tuple[str, str, str], ...] = (
    ("甲", "己", "earth"),
    ("乙", "庚", "metal"),
    ("丙", "辛", "water"),
    ("丁", "壬", "wood"),
    ("戊", "癸", "fire"),
)

_ADJ_PILLARS: Tuple[Tuple[str, str], ...] = (("year", "month"), ("month", "day"), ("day", "hour"))


def judgment_protocol_dynamic_lines_for_stem_fusion(
    operator_plugin_id: str,
    settings: Mapping[str, Any],
) -> List[str]:
    """与 `apply_op_stem_fusion` 中阈值同源，供卡片「判定协议」随 `resolve_physics_settings` 刷新。"""
    _ = operator_plugin_id
    en = float(settings.get("L1_STEM_FUSION_ENABLE", 1.0))
    thr = float(settings.get("STEM_FUSION_BRANCH_SUPPORT_RATIO", 0.26))
    leak = float(settings.get("STEM_FUSION_VECTOR_LEAK_RATIO", 0.12))
    thr_c = max(0.15, min(0.85, thr))
    leak_c = max(0.02, min(0.45, leak))
    return [
        f"[运行时] L1_STEM_FUSION_ENABLE={en:.2f}（<0.5 跳过五合算子）",
        f"[运行时] 邻柱遍历固定集: {list(_ADJ_PILLARS)}",
        f"[运行时] STEM_FUSION_BRANCH_SUPPORT_RATIO 生效值={thr_c:.3f}（化气支承门槛）",
        f"[运行时] STEM_FUSION_VECTOR_LEAK_RATIO 生效值={leak_c:.3f}（化气向量泄漏）",
        "[运行时] 化气判定: month_stem 五行==hua_el OR branch_hua_ratio>=thr",
    ]


# 地支配比：本气五行（与 hidden 表主气一致，供化神地支占比）
_BRANCH_DOMINANT_ELEMENT: Dict[str, str] = {
    "子": "water",
    "丑": "earth",
    "寅": "wood",
    "卯": "wood",
    "辰": "earth",
    "巳": "fire",
    "午": "fire",
    "未": "earth",
    "申": "metal",
    "酉": "metal",
    "戌": "earth",
    "亥": "water",
}


def _pillars_blob(metadata: Any) -> Dict[str, Any]:
    if metadata is None:
        return {}
    if isinstance(metadata, dict):
        p = metadata.get("pillars")
    else:
        p = getattr(metadata, "pillars", None)
    if p is None:
        return {}
    if hasattr(p, "model_dump"):
        return p.model_dump()
    if isinstance(p, dict):
        return p
    return {}


def _stem_of(pillars: Mapping[str, Any], key: str) -> str:
    col = pillars.get(key)
    if isinstance(col, dict):
        return str(col.get("stem") or "")
    return str(getattr(col, "stem", "") or "")


def _branch_of(pillars: Mapping[str, Any], key: str) -> str:
    col = pillars.get(key)
    if isinstance(col, dict):
        return str(col.get("branch") or "")
    return str(getattr(col, "branch", "") or "")


def _fusion_row(a: str, b: str) -> Optional[Tuple[str, str, str]]:
    if not a or not b:
        return None
    s = frozenset({a, b})
    for x, y, hua in _FUSION_ROWS:
        if s == frozenset({x, y}):
            return (x, y, hua)
    return None


def _branch_hua_ratio(branches: Mapping[str, str], hua_el: str) -> float:
    if not branches:
        return 0.0
    n = 0
    hit = 0
    for br in branches.values():
        if not br:
            continue
        n += 1
        if _BRANCH_DOMINANT_ELEMENT.get(str(br), "") == hua_el:
            hit += 1
    return hit / max(1, n)


def apply_op_stem_fusion(
    *,
    physics_tensor: MutableMapping[str, Any],
    metadata: Any,
    settings: Mapping[str, float],
) -> List[Dict[str, Any]]:
    if float(settings.get("L1_STEM_FUSION_ENABLE", 1.0)) < 0.5:
        return []

    pillars = _pillars_blob(metadata)
    day_stem = _stem_of(pillars, "day")
    if not day_stem:
        return []

    month_stem = _stem_of(pillars, "month")
    branches = {k: _branch_of(pillars, k) for k in ("year", "month", "day", "hour") if _branch_of(pillars, k)}

    thr = max(0.15, min(0.85, float(settings.get("STEM_FUSION_BRANCH_SUPPORT_RATIO", 0.26))))
    leak = max(0.02, min(0.45, float(settings.get("STEM_FUSION_VECTOR_LEAK_RATIO", 0.12))))

    cases: List[Dict[str, Any]] = []
    locked_deities: List[str] = []
    deprecated: Dict[str, float] = {}
    display_links: List[Dict[str, Any]] = []

    for pa, pb in _ADJ_PILLARS:
        sa, sb = _stem_of(pillars, pa), _stem_of(pillars, pb)
        row = _fusion_row(sa, sb)
        if not row:
            continue
        _, _, hua_el = row
        month_el = STEM_TO_ELEMENT.get(month_stem, "")
        branch_ratio = _branch_hua_ratio(branches, hua_el)
        month_supports = month_el == hua_el
        transform_ok = month_supports or branch_ratio >= thr

        d1 = deity_from_self_and_target_stem(day_stem=day_stem, target_stem=sa)
        d2 = deity_from_self_and_target_stem(day_stem=day_stem, target_stem=sb)
        pair_deities = sorted({d1, d2})

        if transform_ok:
            axes = physics_tensor.get("deity_energy_axes")
            abs1 = abs2 = 0.0
            if isinstance(axes, dict):
                b1 = axes.get(d1) if isinstance(axes.get(d1), dict) else {}
                b2 = axes.get(d2) if isinstance(axes.get(d2), dict) else {}
                abs1 = float((b1 or {}).get("absolute_energy") or 0.0)
                abs2 = float((b2 or {}).get("absolute_energy") or 0.0)
            combined = max(0.0, abs1 + abs2)
            move = combined * leak

            if isinstance(axes, dict):
                for d, old in ((d1, abs1), (d2, abs2)):
                    blk = axes.get(d)
                    if isinstance(blk, dict) and old > 1e-9:
                        factor = max(0.0, (old - move * (old / combined)) / old) if combined > 1e-9 else 0.35
                        factor = max(0.05, min(1.0, factor))
                        blk["absolute_energy"] = round(float(blk.get("absolute_energy") or 0.0) * factor, 4)
                        deprecated[d] = round(old, 4)

            vec = physics_tensor.get("vector")
            if isinstance(vec, dict) and hua_el in vec and move > 1e-9:
                try:
                    vec[hua_el] = float(vec.get(hua_el, 0.0) or 0.0) + move
                except (TypeError, ValueError):
                    pass
                tot = sum(float(vec.get(k, 0.0) or 0.0) for k in ("wood", "fire", "earth", "metal", "water"))
                if tot > 1e-9:
                    physics_tensor["normalized"] = {
                        k: round(float(vec.get(k, 0.0) or 0.0) / tot, 6) for k in ("wood", "fire", "earth", "metal", "water")
                    }

            if isinstance(axes, dict):
                total = sum(float((axes.get(d) or {}).get("absolute_energy") or 0.0) for d in TEN_DEITIES) or 1.0
                for d in TEN_DEITIES:
                    blk = axes.get(d)
                    if isinstance(blk, dict):
                        ae = float(blk.get("absolute_energy") or 0.0)
                        blk["relative_percentage"] = round(100.0 * ae / total, 2)

            cases.append(
                {
                    "pillars": [pa, pb],
                    "stems": [sa, sb],
                    "mode": "transformed",
                    "hua_element": hua_el,
                    "month_stem_supports": month_supports,
                    "branch_hua_ratio": round(branch_ratio, 4),
                    "deprecated_deities": pair_deities,
                    "transformed_node": {
                        "id": f"Transformed_{hua_el}",
                        "label_zh": f"合化{hua_el}",
                        "leaked_abs": round(move, 4),
                    },
                }
            )
            display_links.append({"deities": pair_deities, "stems": [sa, sb], "mode": "transformed"})
        else:
            for d in pair_deities:
                if d not in locked_deities:
                    locked_deities.append(d)
            cases.append(
                {
                    "pillars": [pa, pb],
                    "stems": [sa, sb],
                    "mode": "stuck",
                    "hua_element": hua_el,
                    "month_stem_supports": month_supports,
                    "branch_hua_ratio": round(branch_ratio, 4),
                    "locked_deities": pair_deities,
                }
            )
            display_links.append({"deities": pair_deities, "stems": [sa, sb], "mode": "stuck"})

    meta = physics_tensor.setdefault("meta", {})
    if not isinstance(meta, dict):
        return []

    out = {
        "version": "stem_fusion.v1",
        "cases": cases,
        "is_locked": any(c.get("mode") in ("stuck", "locked") for c in cases),
        "has_stuck": any(c.get("mode") == "stuck" for c in cases),
        "has_transform": any(c.get("mode") == "transformed" for c in cases),
        "locked_deities": sorted(set(locked_deities)),
        "deprecated_abs_snapshot": deprecated,
        "display_links": display_links,
    }
    meta["stem_fusion_v1"] = out

    skill_ids_step: List[str] = []
    if out.get("has_transform"):
        skill_ids_step.append("l1_stem_fusion_transformed")
    if out.get("has_stuck"):
        skill_ids_step.append("l1_stem_fusion_stuck")
    if not skill_ids_step:
        skill_ids_step.append("l1_stem_fusion_transformed")

    if deprecated:
        dep = meta.setdefault("deity_deprecation_flags", {})
        if isinstance(dep, dict):
            for k, v in deprecated.items():
                dep[k] = {"source": "stem_fusion", "abs_before": v}

    step = {
        "plugin": "base.stem_fusion",
        "edge": ["stem", "fusion"],
        "delta": {
            "case_count": len(cases),
            "locked_deities": out["locked_deities"],
            "has_transform": out["has_transform"],
            "has_stuck": out["has_stuck"],
        },
        "l1_operator_id": OP_ID,
        "l1_operator_ids": [OP_ID],
        "skill_ids": skill_ids_step,
    }
    return [step] if cases else []
