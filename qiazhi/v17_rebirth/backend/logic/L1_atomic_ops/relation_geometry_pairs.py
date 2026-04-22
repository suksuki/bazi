from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple


SANXING_EDGES: Tuple[Tuple[str, str], ...] = (
    ("寅", "巳"),
    ("巳", "申"),
    ("寅", "申"),
    ("丑", "戌"),
    ("戌", "未"),
    ("丑", "未"),
    ("子", "卯"),
)

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


def pillars_branches_set(branches: Mapping[str, str]) -> Set[str]:
    return {str(v) for v in branches.values() if v}


def eval_branch_pair_hits(
    branches: Mapping[str, str],
    pairs: Tuple[Tuple[str, str], ...],
) -> List[Dict[str, Any]]:
    present = pillars_branches_set(branches)
    hits: List[Dict[str, Any]] = []
    for a, b in pairs:
        if a not in present or b not in present:
            continue
        pa = next((p for p, br in branches.items() if br == a), "")
        pb = next((p for p, br in branches.items() if br == b), "")
        if pa and pb and pa != pb:
            hits.append({"pair": sorted([a, b]), "pillars": sorted([pa, pb])})
    return hits


def eval_liuhe_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
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
    present = pillars_branches_set(branches)
    hits: List[Dict[str, Any]] = []
    for pair in ANHE_PAIR_SETS:
        if not pair.issubset(present):
            continue
        a, b = sorted(pair)
        pa = next((p for p, br in branches.items() if br == a), "")
        pb = next((p for p, br in branches.items() if br == b), "")
        if pa and pb and pa != pb:
            hits.append({"pair": [a, b], "pillars": sorted([pa, pb])})
    return hits


def eval_liu_chong_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    return eval_branch_pair_hits(branches, LIU_CHONG_PAIRS)


def eval_liu_hai_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    return eval_branch_pair_hits(branches, LIU_HAI_PAIRS)


def eval_liu_po_hits(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    return eval_branch_pair_hits(branches, LIU_PO_PAIRS)


def sanxing_detect_geometry(branches: Mapping[str, str]) -> List[Dict[str, Any]]:
    present = pillars_branches_set(branches)
    hits: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str]] = set()
    for b1, b2 in SANXING_EDGES:
        if b1 not in present or b2 not in present:
            continue
        key = tuple(sorted((b1, b2)))
        if key in seen:
            continue
        seen.add(key)
        pa = next((p for p, br in branches.items() if br == b1), "")
        pb = next((p for p, br in branches.items() if br == b2), "")
        if pa and pb and pa != pb:
            hits.append({"edge": sorted([pa, pb]), "branches": sorted([b1, b2])})
    return hits


def summarize_sanxing_branches(hits: Sequence[Dict[str, Any]]) -> str:
    bag: Set[str] = set()
    for h in hits:
        for b in h.get("branches") or []:
            bag.add(str(b))
    return "".join(sorted(bag))
