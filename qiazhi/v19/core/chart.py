from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List, Tuple


STEM_ELEMENTS: Dict[str, str] = {
    "甲": "wood",
    "乙": "wood",
    "丙": "fire",
    "丁": "fire",
    "戊": "earth",
    "己": "earth",
    "庚": "metal",
    "辛": "metal",
    "壬": "water",
    "癸": "water",
}

STEM_POLARITY: Dict[str, str] = {
    "甲": "yang",
    "乙": "yin",
    "丙": "yang",
    "丁": "yin",
    "戊": "yang",
    "己": "yin",
    "庚": "yang",
    "辛": "yin",
    "壬": "yang",
    "癸": "yin",
}

BRANCH_HIDDEN_STEMS: Dict[str, List[Tuple[str, float]]] = {
    "子": [("癸", 1.0)],
    "丑": [("己", 0.55), ("癸", 0.25), ("辛", 0.2)],
    "寅": [("甲", 0.55), ("丙", 0.25), ("戊", 0.2)],
    "卯": [("乙", 1.0)],
    "辰": [("戊", 0.55), ("乙", 0.25), ("癸", 0.2)],
    "巳": [("丙", 0.55), ("庚", 0.25), ("戊", 0.2)],
    "午": [("丁", 0.7), ("己", 0.3)],
    "未": [("己", 0.55), ("丁", 0.25), ("乙", 0.2)],
    "申": [("庚", 0.55), ("壬", 0.25), ("戊", 0.2)],
    "酉": [("辛", 1.0)],
    "戌": [("戊", 0.55), ("辛", 0.25), ("丁", 0.2)],
    "亥": [("壬", 0.7), ("甲", 0.3)],
}

GENERATES = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}

CONTROLS = {
    "wood": "earth",
    "earth": "water",
    "water": "fire",
    "fire": "metal",
    "metal": "wood",
}

BRANCH_CLASHES = {
    frozenset(("子", "午")),
    frozenset(("丑", "未")),
    frozenset(("寅", "申")),
    frozenset(("卯", "酉")),
    frozenset(("辰", "戌")),
    frozenset(("巳", "亥")),
}

BRANCH_COMBINATIONS = {
    frozenset(("子", "丑")),
    frozenset(("寅", "亥")),
    frozenset(("卯", "戌")),
    frozenset(("辰", "酉")),
    frozenset(("巳", "申")),
    frozenset(("午", "未")),
}

BRANCH_HARMS = {
    frozenset(("子", "未")),
    frozenset(("丑", "午")),
    frozenset(("寅", "巳")),
    frozenset(("卯", "辰")),
    frozenset(("申", "亥")),
    frozenset(("酉", "戌")),
}

VAULT_BRANCHES = {"辰", "戌", "丑", "未"}


def stable_hash(payload: Dict[str, Any]) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_pillar(value: Any) -> Dict[str, str]:
    text = str(value or "").strip()
    if len(text) < 2:
        return {"stem": "", "branch": ""}
    return {"stem": text[0], "branch": text[1]}


def normalize_chart(chart: Dict[str, Any]) -> Dict[str, Any]:
    raw = dict(chart.get("chart_snapshot") or chart)
    pillars = dict(raw.get("four_pillars") or {})
    normalized = {
        "year": split_pillar(pillars.get("year")),
        "month": split_pillar(pillars.get("month")),
        "day": split_pillar(pillars.get("day")),
        "hour": split_pillar(pillars.get("hour")),
    }
    luck = split_pillar(raw.get("luck_pillar"))
    flow = split_pillar(raw.get("flow_pillar"))
    out = {
        "chart_id": str(raw.get("chart_id") or ""),
        "pillars": normalized,
        "luck": luck,
        "flow": flow,
    }
    if not out["chart_id"]:
        out["chart_id"] = "v19_chart_" + stable_hash(out)[:16]
    return out


def element_of_stem(stem: str) -> str:
    return STEM_ELEMENTS.get(stem, "")


def ten_god(day_stem: str, target_stem: str) -> str:
    day_element = element_of_stem(day_stem)
    target_element = element_of_stem(target_stem)
    if not day_element or not target_element:
        return "unknown"
    if target_element == day_element:
        return "peer"
    if GENERATES.get(day_element) == target_element:
        return "output"
    if CONTROLS.get(day_element) == target_element:
        return "wealth"
    if CONTROLS.get(target_element) == day_element:
        return "officer"
    if GENERATES.get(target_element) == day_element:
        return "seal"
    return "unknown"


def branch_pairs(branches: Iterable[str]) -> List[Tuple[str, str]]:
    clean = [branch for branch in branches if branch]
    out: List[Tuple[str, str]] = []
    for left_index, left in enumerate(clean):
        for right in clean[left_index + 1 :]:
            out.append((left, right))
    return out
