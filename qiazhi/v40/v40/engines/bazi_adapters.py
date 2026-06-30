from __future__ import annotations

from itertools import combinations

from v40.contracts.chart import BaziChartFacts


STEM_ELEMENTS = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}

STEM_POLARITY = {
    "甲": "阳",
    "乙": "阴",
    "丙": "阳",
    "丁": "阴",
    "戊": "阳",
    "己": "阴",
    "庚": "阳",
    "辛": "阴",
    "壬": "阳",
    "癸": "阴",
}

BRANCH_ELEMENTS = {
    "寅": "木",
    "卯": "木",
    "巳": "火",
    "午": "火",
    "辰": "土",
    "戌": "土",
    "丑": "土",
    "未": "土",
    "申": "金",
    "酉": "金",
    "亥": "水",
    "子": "水",
}

GENERATES = {
    "木": "火",
    "火": "土",
    "土": "金",
    "金": "水",
    "水": "木",
}

CONTROLS = {
    "木": "土",
    "土": "水",
    "水": "火",
    "火": "金",
    "金": "木",
}

SUPPORTING_ELEMENTS = {
    "木": ["水", "木"],
    "火": ["木", "火"],
    "土": ["火", "土"],
    "金": ["土", "金"],
    "水": ["金", "水"],
}

DRAINING_ELEMENTS = {
    "木": ["火", "金"],
    "火": ["土", "水"],
    "土": ["金", "木"],
    "金": ["水", "火"],
    "水": ["木", "土"],
}

PILLAR_STEMS = [
    ("year", "年干", "year_stem"),
    ("month", "月干", "month_stem"),
    ("day", "日干", "day_stem"),
    ("hour", "时干", "hour_stem"),
]

PILLAR_BRANCHES = [
    ("year", "年支", "year_branch"),
    ("month", "月支", "month_branch"),
    ("day", "日支", "day_branch"),
    ("hour", "时支", "hour_branch"),
]

SIX_HARMONY = {
    frozenset(("子", "丑")): "子丑合",
    frozenset(("寅", "亥")): "寅亥合",
    frozenset(("卯", "戌")): "卯戌合",
    frozenset(("辰", "酉")): "辰酉合",
    frozenset(("巳", "申")): "巳申合",
    frozenset(("午", "未")): "午未合",
}

SIX_CLASH = {
    frozenset(("子", "午")): "子午冲",
    frozenset(("丑", "未")): "丑未冲",
    frozenset(("寅", "申")): "寅申冲",
    frozenset(("卯", "酉")): "卯酉冲",
    frozenset(("辰", "戌")): "辰戌冲",
    frozenset(("巳", "亥")): "巳亥冲",
}


def build_ten_god_profile(chart: BaziChartFacts) -> dict[str, object]:
    day_stem = chart.day_stem
    rows = []
    counts: dict[str, int] = {}
    for pillar_key, pillar_label, attr in PILLAR_STEMS:
        stem = getattr(chart, attr)
        if not stem or pillar_key == "day":
            continue
        ten_god = resolve_ten_god(day_stem=day_stem, other_stem=stem)
        if ten_god:
            counts[ten_god] = counts.get(ten_god, 0) + 1
        rows.append(
            {
                "pillar": pillar_key,
                "label": pillar_label,
                "stem": stem,
                "element": STEM_ELEMENTS.get(stem, "未知"),
                "polarity": STEM_POLARITY.get(stem, "未知"),
                "ten_god": ten_god or "未知",
            }
        )
    dominant = sorted(counts.items(), key=lambda row: (-row[1], row[0]))[:3]
    return {
        "profile_id": "ten_god.visible_stems",
        "day_stem": day_stem,
        "day_element": STEM_ELEMENTS.get(day_stem, "未知"),
        "rows": rows,
        "counts": counts,
        "dominant_ten_gods": [name for name, _count in dominant],
        "wealth_count": counts.get("正财", 0) + counts.get("偏财", 0),
        "officer_count": counts.get("正官", 0) + counts.get("七杀", 0),
        "resource_count": counts.get("正印", 0) + counts.get("偏印", 0),
        "output_count": counts.get("食神", 0) + counts.get("伤官", 0),
        "peer_count": counts.get("比肩", 0) + counts.get("劫财", 0),
    }


def build_useful_god_profile(
    *,
    day_element: str,
    structure: str,
    useful_candidates: list[str],
) -> dict[str, object]:
    if structure.startswith("偏旺"):
        strategy = "泄耗制衡"
        reason = "日主偏旺时，先看输出、财官或可制衡之气是否能流通。"
    elif structure.startswith("偏弱"):
        strategy = "扶助承接"
        reason = "日主偏弱时，先看印比、资源和根气是否能承接压力。"
    else:
        strategy = "候选并存"
        reason = "结构尚未拉开时，用神候选先并存，等待领域与现实反馈拉开权重。"
    return {
        "profile_id": "useful_god.candidates",
        "day_element": day_element,
        "structure": structure,
        "strategy": strategy,
        "candidates": useful_candidates,
        "reason": reason,
    }


def build_branch_relation_profile(chart: BaziChartFacts) -> dict[str, object]:
    branches = [
        {
            "pillar": pillar_key,
            "label": pillar_label,
            "branch": getattr(chart, attr),
            "element": BRANCH_ELEMENTS.get(getattr(chart, attr), "未知"),
        }
        for pillar_key, pillar_label, attr in PILLAR_BRANCHES
        if getattr(chart, attr)
    ]
    relations = []
    for left, right in combinations(branches, 2):
        relation = _branch_relation(left["branch"], right["branch"])
        if relation:
            relations.append({**relation, "left": left, "right": right, "dynamic": False})
    timing_relations = _timing_relations(chart=chart, branches=branches)
    clash_count = sum(1 for row in [*relations, *timing_relations] if row["type"] == "clash")
    harmony_count = sum(1 for row in [*relations, *timing_relations] if row["type"] == "harmony")
    return {
        "profile_id": "branch.relations",
        "relations": relations,
        "timing_relations": timing_relations,
        "clash_count": clash_count,
        "harmony_count": harmony_count,
    }


def resolve_ten_god(*, day_stem: str, other_stem: str) -> str:
    day_element = STEM_ELEMENTS.get(day_stem)
    other_element = STEM_ELEMENTS.get(other_stem)
    day_polarity = STEM_POLARITY.get(day_stem)
    other_polarity = STEM_POLARITY.get(other_stem)
    if not day_element or not other_element or not day_polarity or not other_polarity:
        return ""
    same_polarity = day_polarity == other_polarity
    if other_element == day_element:
        return "比肩" if same_polarity else "劫财"
    if GENERATES.get(other_element) == day_element:
        return "偏印" if same_polarity else "正印"
    if GENERATES.get(day_element) == other_element:
        return "食神" if same_polarity else "伤官"
    if CONTROLS.get(day_element) == other_element:
        return "偏财" if same_polarity else "正财"
    if CONTROLS.get(other_element) == day_element:
        return "七杀" if same_polarity else "正官"
    return ""


def _branch_relation(left: str, right: str) -> dict[str, object]:
    pair = frozenset((left, right))
    if pair in SIX_CLASH:
        return {"type": "clash", "label": SIX_CLASH[pair], "polarity": "movement"}
    if pair in SIX_HARMONY:
        return {"type": "harmony", "label": SIX_HARMONY[pair], "polarity": "binding"}
    return {}


def _timing_relations(*, chart: BaziChartFacts, branches: list[dict[str, str]]) -> list[dict[str, object]]:
    timing = []
    for key, label, value in [
        ("current_luck", "当前大运", chart.current_luck),
        ("current_year", "当前流年", chart.current_year),
    ]:
        branch = value[-1:] if value else ""
        if branch not in BRANCH_ELEMENTS:
            continue
        timing_branch = {"pillar": key, "label": label, "branch": branch, "element": BRANCH_ELEMENTS[branch]}
        for base in branches:
            relation = _branch_relation(timing_branch["branch"], base["branch"])
            if relation:
                timing.append({**relation, "left": timing_branch, "right": base, "dynamic": True})
    return timing
