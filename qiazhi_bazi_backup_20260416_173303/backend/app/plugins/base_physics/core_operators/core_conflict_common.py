"""L1 核心冲突算子共用：四柱抽取、羊刃支、极性种子写入 meta（供 CausalRouter）。"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Set, Tuple

from app.skills.physics_rules import deity_from_self_and_target_stem

PILLAR_KEYS = ("year", "month", "day", "hour")

# 羊刃支（禄后一位，与常见禄命表对齐；调参走 physics_settings 而非改表）
STEM_YANG_BLADE_BRANCH: Dict[str, str] = {
    "甲": "卯",
    "乙": "辰",
    "丙": "午",
    "丁": "未",
    "戊": "午",
    "己": "未",
    "庚": "酉",
    "辛": "戌",
    "壬": "子",
    "癸": "丑",
}


def pillars_dict(metadata: Any) -> Dict[str, Any]:
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


def day_stem(pillars: Mapping[str, Any]) -> str:
    day = pillars.get("day")
    if isinstance(day, dict) and day.get("stem"):
        return str(day["stem"])
    return ""


def stem_by_pillar(pillars: Mapping[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k in PILLAR_KEYS:
        col = pillars.get(k)
        if isinstance(col, dict) and col.get("stem"):
            out[k] = str(col["stem"])
    return out


def branch_by_pillar(pillars: Mapping[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k in PILLAR_KEYS:
        col = pillars.get(k)
        if isinstance(col, dict) and col.get("branch"):
            out[k] = str(col["branch"])
    return out


def axis_abs(axes: Mapping[str, Any], deity: str) -> float:
    blk = axes.get(deity) if isinstance(axes, dict) else None
    if not isinstance(blk, dict):
        return 0.0
    try:
        return float(blk.get("absolute_energy") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def append_polarity_seed(
    meta: MutableMapping[str, Any],
    *,
    pattern: str,
    deity: str,
    delta_a: float = 0.35,
    delta_b: float = -0.35,
    plugin_a: str = "base.l1.core_conflict",
    plugin_b: str = "base.physics.tensor",
) -> None:
    raw = meta.setdefault("l1_polarity_routing_seeds", [])
    if not isinstance(raw, list):
        raw = []
        meta["l1_polarity_routing_seeds"] = raw
    raw.append(
        {
            "pattern": pattern,
            "deity": deity,
            "plugin_a": plugin_a,
            "plugin_b": plugin_b,
            "delta_a": round(delta_a, 4),
            "delta_b": round(delta_b, 4),
        }
    )


def record_applied(meta: MutableMapping[str, Any], op_id: str) -> None:
    raw = meta.setdefault("l1_core_conflict_applied", [])
    if isinstance(raw, list) and op_id not in raw:
        raw.append(op_id)


def stems_have_official_kill_between(
    stems_ordered: List[str],
    *,
    day_stem: str,
    cai_indices: Set[int],
    yin_indices: Set[int],
) -> bool:
    """财印索引之间若存在透干正官/七杀，则视为有通关节点（财星破印不触发物理坍缩）。"""
    if not cai_indices or not yin_indices or not day_stem:
        return False
    lo = min(min(cai_indices), min(yin_indices))
    hi = max(max(cai_indices), max(yin_indices))
    for i in range(lo + 1, hi):
        if i < 0 or i >= len(stems_ordered):
            continue
        st = stems_ordered[i]
        if not st:
            continue
        if deity_from_self_and_target_stem(day_stem=day_stem, target_stem=st) in ("正官", "七杀"):
            return True
    return False


def ordered_stems_for_pass(pillars: Mapping[str, Any]) -> List[str]:
    return [str(stem_by_pillar(pillars).get(k) or "") for k in PILLAR_KEYS]


def pillar_deities(day_stem: str, pillars: Mapping[str, Any]) -> Dict[str, Set[str]]:
    """每柱出现的十神集合（由天干相对日主）。"""
    out: Dict[str, Set[str]] = {}
    if not day_stem:
        return out
    for pk in PILLAR_KEYS:
        col = pillars.get(pk)
        st = str(col.get("stem") or "") if isinstance(col, dict) else ""
        if not st:
            continue
        d = deity_from_self_and_target_stem(day_stem=day_stem, target_stem=st)
        out.setdefault(pk, set()).add(d)
    return out
