from __future__ import annotations

from collections import Counter
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

HIDDEN_STEMS = {
    "子": [("癸", "本气", 1.0)],
    "丑": [("己", "本气", 0.7), ("癸", "中气", 0.2), ("辛", "余气", 0.1)],
    "寅": [("甲", "本气", 0.7), ("丙", "中气", 0.2), ("戊", "余气", 0.1)],
    "卯": [("乙", "本气", 1.0)],
    "辰": [("戊", "本气", 0.7), ("乙", "中气", 0.2), ("癸", "余气", 0.1)],
    "巳": [("丙", "本气", 0.7), ("戊", "中气", 0.2), ("庚", "余气", 0.1)],
    "午": [("丁", "本气", 0.7), ("己", "中气", 0.3)],
    "未": [("己", "本气", 0.7), ("丁", "中气", 0.2), ("乙", "余气", 0.1)],
    "申": [("庚", "本气", 0.7), ("壬", "中气", 0.2), ("戊", "余气", 0.1)],
    "酉": [("辛", "本气", 1.0)],
    "戌": [("戊", "本气", 0.7), ("辛", "中气", 0.2), ("丁", "余气", 0.1)],
    "亥": [("壬", "本气", 0.7), ("甲", "中气", 0.3)],
}

BRANCH_SEASONS = {
    "寅": ("春初", "木"),
    "卯": ("春旺", "木"),
    "辰": ("春末", "土"),
    "巳": ("夏初", "火"),
    "午": ("夏旺", "火"),
    "未": ("夏末", "土"),
    "申": ("秋初", "金"),
    "酉": ("秋旺", "金"),
    "戌": ("秋末", "土"),
    "亥": ("冬初", "水"),
    "子": ("冬旺", "水"),
    "丑": ("冬末", "土"),
}

THREE_HARMONY_GROUPS = {
    "申子辰水局": ("水", ("申", "子", "辰")),
    "亥卯未木局": ("木", ("亥", "卯", "未")),
    "寅午戌火局": ("火", ("寅", "午", "戌")),
    "巳酉丑金局": ("金", ("巳", "酉", "丑")),
}

THREE_MEETING_GROUPS = {
    "寅卯辰东方木": ("木", ("寅", "卯", "辰")),
    "巳午未南方火": ("火", ("巳", "午", "未")),
    "申酉戌西方金": ("金", ("申", "酉", "戌")),
    "亥子丑北方水": ("水", ("亥", "子", "丑")),
}

BRANCH_HARMS = {
    frozenset(("子", "未")): "子未害",
    frozenset(("丑", "午")): "丑午害",
    frozenset(("寅", "巳")): "寅巳害",
    frozenset(("卯", "辰")): "卯辰害",
    frozenset(("申", "亥")): "申亥害",
    frozenset(("酉", "戌")): "酉戌害",
}

BRANCH_BREAKS = {
    frozenset(("子", "酉")): "子酉破",
    frozenset(("丑", "辰")): "丑辰破",
    frozenset(("寅", "亥")): "寅亥破",
    frozenset(("卯", "午")): "卯午破",
    frozenset(("巳", "申")): "巳申破",
    frozenset(("未", "戌")): "未戌破",
}

BRANCH_PUNISHMENT_GROUPS = {
    "寅巳申刑": ("寅", "巳", "申"),
    "丑未戌刑": ("丑", "未", "戌"),
    "子卯刑": ("子", "卯"),
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


def build_fact_engine_pro_profile(chart: BaziChartFacts) -> dict[str, object]:
    day_element = STEM_ELEMENTS.get(chart.day_stem, "未知")
    base_branches = _branch_rows(chart)
    timing_branches = _timing_branch_rows(chart)
    hidden_stem_rows = _hidden_stem_rows(chart=chart, branches=base_branches)
    hidden_ten_god_counts = _weighted_counts(
        {"key": row["ten_god"], "weight": row["weight"]} for row in hidden_stem_rows
    )
    hidden_element_counts = _weighted_counts(
        {"key": row["element"], "weight": row["weight"]} for row in hidden_stem_rows
    )
    root_profile = _root_profile(
        day_stem=chart.day_stem,
        day_element=day_element,
        hidden_rows=hidden_stem_rows,
    )
    month_profile = _month_authority_profile(
        day_element=day_element,
        month_branch=chart.month_branch,
    )
    advanced_relations = _advanced_branch_relations(
        base_branches=base_branches,
        timing_branches=timing_branches,
    )
    return {
        "profile_id": "bazi_fact_engine_pro.v1",
        "day_stem": chart.day_stem,
        "day_element": day_element,
        "hidden_stems": hidden_stem_rows,
        "hidden_ten_god_counts": hidden_ten_god_counts,
        "hidden_element_counts": hidden_element_counts,
        "root_profile": root_profile,
        "month_profile": month_profile,
        "advanced_branch_relations": advanced_relations,
        "dynamic_profile": {
            "timing_branches": timing_branches,
            "dynamic_relation_count": sum(1 for row in advanced_relations["relations"] if row.get("dynamic")),
        },
        "fact_training_allowed": False,
        "trainable_policy_targets": [
            "signal_weight.bazi_fact_pro_root_season",
            "signal_weight.hidden_ten_god",
            "signal_weight.advanced_branch_relation",
            "claim_score.useful_god_candidate",
        ],
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


def _branch_rows(chart: BaziChartFacts) -> list[dict[str, str]]:
    return [
        {
            "pillar": pillar_key,
            "label": pillar_label,
            "branch": getattr(chart, attr),
            "element": BRANCH_ELEMENTS.get(getattr(chart, attr), "未知"),
            "dynamic": False,
        }
        for pillar_key, pillar_label, attr in PILLAR_BRANCHES
        if getattr(chart, attr)
    ]


def _timing_branch_rows(chart: BaziChartFacts) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for pillar, label, value in [
        ("current_luck", "当前大运", chart.current_luck),
        ("current_year", "当前流年", chart.current_year),
    ]:
        branch = value[-1:] if value else ""
        if branch in BRANCH_ELEMENTS:
            rows.append(
                {
                    "pillar": pillar,
                    "label": label,
                    "branch": branch,
                    "element": BRANCH_ELEMENTS[branch],
                    "dynamic": True,
                }
            )
    return rows


def _hidden_stem_rows(*, chart: BaziChartFacts, branches: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for branch_row in branches:
        branch = branch_row["branch"]
        for stem, layer, weight in HIDDEN_STEMS.get(branch, []):
            rows.append(
                {
                    "pillar": branch_row["pillar"],
                    "label": branch_row["label"],
                    "branch": branch,
                    "stem": stem,
                    "layer": layer,
                    "weight": weight,
                    "element": STEM_ELEMENTS.get(stem, "未知"),
                    "polarity": STEM_POLARITY.get(stem, "未知"),
                    "ten_god": resolve_ten_god(day_stem=chart.day_stem, other_stem=stem) or "未知",
                }
            )
    return rows


def _weighted_counts(values: object) -> dict[str, float]:
    counts: dict[str, float] = {}
    for row in values:
        if isinstance(row, dict):
            key = str(row.get("key") or "")
            weight = float(row.get("weight") or 0)
        else:
            key = str(row)
            weight = 1.0
        if not key or key == "未知":
            continue
        counts[key] = round(counts.get(key, 0.0) + weight, 3)
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _root_profile(
    *,
    day_stem: str,
    day_element: str,
    hidden_rows: list[dict[str, object]],
) -> dict[str, object]:
    same_stem_rows = [row for row in hidden_rows if row["stem"] == day_stem]
    same_element_rows = [row for row in hidden_rows if row["element"] == day_element]
    supporting_rows = [
        row
        for row in hidden_rows
        if row["element"] in SUPPORTING_ELEMENTS.get(day_element, []) and row["element"] != day_element
    ]
    weighted_root = sum(float(row["weight"]) for row in same_element_rows) + sum(
        float(row["weight"]) * 0.45 for row in supporting_rows
    )
    root_score = round(min(1.0, weighted_root / 2.2), 3)
    if root_score >= 0.68:
        root_level = "有根"
    elif root_score >= 0.36:
        root_level = "有气待复核"
    else:
        root_level = "根气偏弱"
    root_branches = sorted({str(row["branch"]) for row in [*same_element_rows, *supporting_rows]})
    return {
        "day_stem": day_stem,
        "day_element": day_element,
        "root_score": root_score,
        "root_level": root_level,
        "root_branches": root_branches,
        "same_stem_count": len(same_stem_rows),
        "same_element_count": len(same_element_rows),
        "supporting_count": len(supporting_rows),
        "day_master_has_root": bool(same_element_rows),
    }


def _month_authority_profile(*, day_element: str, month_branch: str) -> dict[str, object]:
    season, month_element = BRANCH_SEASONS.get(month_branch, ("未知", BRANCH_ELEMENTS.get(month_branch, "未知")))
    relation = _element_relation_to_day(day_element=day_element, other_element=month_element)
    authority_score = 0.5
    if relation in {"same", "resource"}:
        authority_score = 0.72
    elif relation in {"officer_pressure", "output", "wealth"}:
        authority_score = 0.38
    return {
        "month_branch": month_branch,
        "season": season,
        "month_element": month_element,
        "relation_to_day": relation,
        "authority_score": authority_score,
    }


def _advanced_branch_relations(
    *,
    base_branches: list[dict[str, str]],
    timing_branches: list[dict[str, str]],
) -> dict[str, object]:
    all_branches = [*base_branches, *timing_branches]
    relations: list[dict[str, object]] = []
    for left, right in combinations(all_branches, 2):
        pair = frozenset((left["branch"], right["branch"]))
        for relation_type, table, polarity in [
            ("harm", BRANCH_HARMS, "friction"),
            ("break", BRANCH_BREAKS, "disruption"),
        ]:
            if pair in table:
                relations.append(
                    {
                        "type": relation_type,
                        "label": table[pair],
                        "polarity": polarity,
                        "left": left,
                        "right": right,
                        "dynamic": bool(left.get("dynamic") or right.get("dynamic")),
                    }
                )
    relations.extend(_group_relations(all_branches, THREE_HARMONY_GROUPS, "three_harmony"))
    relations.extend(_group_relations(all_branches, THREE_MEETING_GROUPS, "three_meeting"))
    relations.extend(_punishment_relations(all_branches))
    counts = Counter(str(row["type"]) for row in relations)
    return {
        "relations": relations,
        "counts": dict(sorted(counts.items())),
        "relation_count": len(relations),
    }


def _group_relations(
    branches: list[dict[str, str]],
    groups: dict[str, tuple[str, tuple[str, ...]]],
    relation_type: str,
) -> list[dict[str, object]]:
    relations: list[dict[str, object]] = []
    branch_values = [row["branch"] for row in branches]
    for label, (element, members) in groups.items():
        matched = [row for row in branches if row["branch"] in members]
        unique_match_count = len(set(branch_values).intersection(members))
        if unique_match_count < 2:
            continue
        relations.append(
            {
                "type": relation_type,
                "label": label,
                "element": element,
                "members": list(members),
                "matched_branches": [row["branch"] for row in matched],
                "complete": unique_match_count == 3,
                "dynamic": any(row.get("dynamic") for row in matched),
            }
        )
    return relations


def _punishment_relations(branches: list[dict[str, str]]) -> list[dict[str, object]]:
    values = {row["branch"] for row in branches}
    relations: list[dict[str, object]] = []
    for label, members in BRANCH_PUNISHMENT_GROUPS.items():
        matched = [row for row in branches if row["branch"] in members]
        if len(values.intersection(members)) < len(members):
            continue
        relations.append(
            {
                "type": "punishment",
                "label": label,
                "members": list(members),
                "matched_branches": [row["branch"] for row in matched],
                "complete": True,
                "dynamic": any(row.get("dynamic") for row in matched),
            }
        )
    return relations


def _element_relation_to_day(*, day_element: str, other_element: str) -> str:
    if not day_element or not other_element or "未知" in {day_element, other_element}:
        return "unknown"
    if other_element == day_element:
        return "same"
    if GENERATES.get(other_element) == day_element:
        return "resource"
    if GENERATES.get(day_element) == other_element:
        return "output"
    if CONTROLS.get(day_element) == other_element:
        return "wealth"
    if CONTROLS.get(other_element) == day_element:
        return "officer_pressure"
    return "neutral"


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
