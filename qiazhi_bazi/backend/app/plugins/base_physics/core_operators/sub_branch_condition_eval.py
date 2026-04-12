"""地支深度交互：条件判定（与 `op_sub_branch_interaction` 副作用分离，供蓝图/审计引用）。"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Set, Tuple

from app.skills.physics_rules import SANHE_GROUPS, SANXING_EDGES

# --- 静态表（与 `physics_rules` / 传统历表一致）---

LIUHE_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("子", "丑"),
    ("寅", "亥"),
    ("卯", "戌"),
    ("辰", "酉"),
    ("巳", "申"),
    ("午", "未"),
)

ANHE_PAIR_SETS: Tuple[frozenset[str], ...] = (
    frozenset({"子", "巳"}),
    frozenset({"丑", "午"}),
    frozenset({"寅", "未"}),
    frozenset({"卯", "申"}),
    frozenset({"亥", "午"}),
)

BANHE_TRIPLE: Tuple[Tuple[str, str, str], ...] = (
    ("申", "子", "water"),
    ("子", "辰", "water"),
    ("亥", "卯", "wood"),
    ("卯", "未", "wood"),
    ("寅", "午", "fire"),
    ("午", "戌", "fire"),
    ("巳", "酉", "metal"),
    ("酉", "丑", "metal"),
)

LIU_CHONG_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("子", "午"),
    ("丑", "未"),
    ("寅", "申"),
    ("卯", "酉"),
    ("辰", "戌"),
    ("巳", "亥"),
)

LIU_HAI_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("子", "未"),
    ("丑", "午"),
    ("寅", "巳"),
    ("卯", "辰"),
    ("申", "亥"),
    ("酉", "戌"),
)

LIU_PO_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("子", "酉"),
    ("午", "卯"),
    ("寅", "亥"),
    ("巳", "申"),
    ("辰", "丑"),
    ("戌", "未"),
)

# 三合局 → 中神（帝旺支，属子午卯酉）
SANHE_GROUP_TO_ZHONGSHEN: Dict[frozenset[str], str] = {
    frozenset({"寅", "午", "戌"}): "午",
    frozenset({"申", "子", "辰"}): "子",
    frozenset({"亥", "卯", "未"}): "卯",
    frozenset({"巳", "酉", "丑"}): "酉",
}


def pillars_branches_set(branches: Mapping[str, str]) -> Set[str]:
    return set(branches.values())


def eval_liuhe_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    """六合：两支同现四柱且须 **异柱**（`pillars` 两端不同）。"""
    present = pillars_branches_set(branches)
    hits: List[Dict[str, Any]] = []
    for a, b in LIUHE_PAIRS:
        if a not in present or b not in present:
            continue
        pa = next((p for p, br in branches.items() if br == a), "")
        pb = next((p for p, br in branches.items() if br == b), "")
        if pa and pb and pa != pb:
            hits.append({"pair": [a, b], "pillars": sorted([pa, pb])})
    return hits


def eval_anhe_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    """暗合：预置支对同现且异柱。"""
    present = pillars_branches_set(branches)
    out: List[Dict[str, Any]] = []
    for pair in ANHE_PAIR_SETS:
        if not pair.issubset(present):
            continue
        b1, b2 = sorted(pair)
        pa = next((p for p, br in branches.items() if br == b1), "")
        pb = next((p for p, br in branches.items() if br == b2), "")
        if pa and pb and pa != pb:
            out.append({"pair": sorted(list(pair)), "pillars": sorted([pa, pb])})
    return out


def sanhe_group_complete_for_pair(br1: str, br2: str, present: Set[str]) -> bool:
    """两支同属一三合局且该局三支已在盘中齐。"""
    for g in SANHE_GROUPS:
        if br1 in g and br2 in g:
            return set(g).issubset(present)
    return False


def eval_banhe_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    """半合：两支成三合缺一支；若 **全三合已齐** 则不再记半合。"""
    present = set(branches.values())
    hits: List[Dict[str, Any]] = []
    for a, b, el in BANHE_TRIPLE:
        if a not in present or b not in present:
            continue
        if sanhe_group_complete_for_pair(a, b, present):
            continue
        pa = next((p for p, br in branches.items() if br == a), "")
        pb = next((p for p, br in branches.items() if br == b), "")
        if pa and pb and pa != pb:
            hits.append({"pair": sorted([a, b]), "pillars": sorted([pa, pb]), "element": el})
    return hits


def eval_branch_pair_hits(branches: Mapping[str, str], pairs: Tuple[Tuple[str, str], ...]) -> List[Dict[str, Any]]:
    """通配：冲/害/破等对表命中且异柱。"""
    present = set(branches.values())
    hits: List[Dict[str, Any]] = []
    for a, b in pairs:
        if a not in present or b not in present:
            continue
        pa = next((p for p, br in branches.items() if br == a), "")
        pb = next((p for p, br in branches.items() if br == b), "")
        if pa and pb and pa != pb:
            hits.append({"pair": sorted([a, b]), "pillars": sorted([pa, pb])})
    return hits


def eval_liu_chong_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    return eval_branch_pair_hits(branches, LIU_CHONG_PAIRS)


def eval_liu_hai_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    return eval_branch_pair_hits(branches, LIU_HAI_PAIRS)


def eval_liu_po_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    return eval_branch_pair_hits(branches, LIU_PO_PAIRS)


def sanxing_from_steps(combined_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """三刑：来自 punish 原子步 `mode=sanxing`。"""
    out: List[Dict[str, Any]] = []
    for s in combined_steps:
        if s.get("plugin") != "base.punish":
            continue
        if str(s.get("mode") or "") != "sanxing":
            continue
        out.append({"edge": list(s.get("edge") or []), "mode": "sanxing"})
    return out


def sanxing_detect_geometry(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    """三刑：任两支成 `SANXING_EDGES` 即记（与 punish 步互补）。"""
    present = pillars_branches_set(branches)
    hits: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str]] = set()
    for b1, b2 in SANXING_EDGES:
        if b1 in present and b2 in present:
            key = tuple(sorted((b1, b2)))
            if key in seen:
                continue
            seen.add(key)
            pa = next((p for p, br in branches.items() if br == b1), "")
            pb = next((p for p, br in branches.items() if br == b2), "")
            if pa and pb and pa != pb:
                hits.append({"edge": sorted([pa, pb]), "branches": sorted([b1, b2])})
    return hits


def sanhe_trine_allowed_by_wang_zhi_switch(
    group: frozenset[str],
    branches: Mapping[str, str],
    settings: Mapping[str, Any],
) -> bool:
    """
    三合「旺支」门控：`SUB_BRANCH_SANHE_REQ_WANG_ZHI`≥0.5 时，该局 **中神**（子午卯酉之一）须落在 **月支或日支**。

    关闭（<0.5）：维持旧行为，三支齐于四柱任意位置即聚合。
    """
    if float(settings.get("SUB_BRANCH_SANHE_REQ_WANG_ZHI", 0.0)) < 0.5:
        return True
    zh = SANHE_GROUP_TO_ZHONGSHEN.get(frozenset(group))
    if not zh:
        return True
    if branches.get("month") == zh or branches.get("day") == zh:
        return True
    if float(settings.get("SANHE_TEMPORAL_WANG_ZHI_BRIDGE", 1.0)) >= 0.5:
        return branches.get("dayun") == zh or branches.get("liunian") == zh
    return False
