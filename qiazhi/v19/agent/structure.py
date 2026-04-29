from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Literal


Stem = Literal["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
Branch = Literal["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

STEMS: List[Stem] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES: List[Branch] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

STEM_ELEMENT = {
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

STEM_YIN_YANG = {
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

BRANCH_MAIN_STEM = {
    "子": "癸",
    "丑": "己",
    "寅": "甲",
    "卯": "乙",
    "辰": "戊",
    "巳": "丙",
    "午": "丁",
    "未": "己",
    "申": "庚",
    "酉": "辛",
    "戌": "戊",
    "亥": "壬",
}

MONTH_BRANCH_SEQUENCE: List[Branch] = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]

MONTH_START_STEM_BY_YEAR_STEM = {
    "甲": "丙",
    "己": "丙",
    "乙": "戊",
    "庚": "戊",
    "丙": "庚",
    "辛": "庚",
    "丁": "壬",
    "壬": "壬",
    "戊": "甲",
    "癸": "甲",
}

HOUR_START_STEM_BY_DAY_STEM = {
    "甲": "甲",
    "己": "甲",
    "乙": "丙",
    "庚": "丙",
    "丙": "戊",
    "辛": "戊",
    "丁": "庚",
    "壬": "庚",
    "戊": "壬",
    "癸": "壬",
}

SIX_COMBINATIONS = [("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")]
SIX_CLASHES = [("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")]
THREE_HARMONIES = [("申", "子", "辰"), ("亥", "卯", "未"), ("寅", "午", "戌"), ("巳", "酉", "丑")]


@dataclass(frozen=True)
class BirthInput:
    year: int
    month: int
    day: int
    hour: int
    gender: Literal["male", "female"]
    calendar_type: Literal["solar", "lunar"] = "solar"


def build_agent_turn(payload: Dict[str, Any]) -> Dict[str, Any]:
    birth = _birth_input(payload.get("birth_input") or {})
    selected_year = _int(payload.get("selected_year"), 2025)
    message = str(payload.get("message") or "").strip()

    if birth.calendar_type != "solar":
        return {
            "ok": False,
            "code": "lunar_calendar_not_supported",
            "message": "V19 standalone agent currently supports solar input only.",
        }

    chart = build_chart(birth)
    flow_year = build_flow_year(chart, selected_year)
    luck_cycles = build_luck_cycles(chart, birth)
    age = selected_year - birth.year
    active_luck_cycle = next((cycle for cycle in luck_cycles["cycles"] if cycle["start_age"] <= age <= cycle["end_age"]), None)

    return {
        "ok": True,
        "code": "OK",
        "data": {
            "mode": "v19_standalone_agent",
            "boundary": "structure_first_no_prediction",
            "birth_input": birth.__dict__,
            "chart": chart,
            "time_context": {
                "natal": chart,
                "luck_cycle": active_luck_cycle,
                "flow_year": flow_year,
            },
            "luck_cycles": luck_cycles,
            "agent_reply": _agent_reply(chart, flow_year, active_luck_cycle, message),
        },
    }


def build_chart(birth: BirthInput) -> Dict[str, Any]:
    _validate_solar_date(birth)
    year_pillar = _year_pillar(birth.year, birth.month, birth.day)
    month_pillar = _month_pillar(birth.month, birth.day, year_pillar["stem"])
    day_pillar = _day_pillar(birth.year, birth.month, birth.day)
    hour_pillar = _hour_pillar(birth.hour, day_pillar["stem"])
    pillars = {
        "year": year_pillar,
        "month": month_pillar,
        "day": day_pillar,
        "hour": hour_pillar,
    }
    branches = [(name, pillar["branch"]) for name, pillar in pillars.items()]

    return {
        "status": "ok",
        "calendar_note": "solar_mvp_approximate_jie_boundaries",
        "pillars": pillars,
        "day_master": {
            "stem": day_pillar["stem"],
            "element": STEM_ELEMENT[day_pillar["stem"]],
            "yin_yang": STEM_YIN_YANG[day_pillar["stem"]],
        },
        "relations": _relations_from_branches(branches),
    }


def build_flow_year(chart: Dict[str, Any], selected_year: int) -> Dict[str, Any]:
    pillar = _cycle_pillar(selected_year - 4)
    return {
        "year": selected_year,
        "pillar": pillar,
        "relations_with_natal": _relations_with_natal(chart, pillar["branch"]),
    }


def build_luck_cycles(chart: Dict[str, Any], birth: BirthInput) -> Dict[str, Any]:
    year_stem = chart["pillars"]["year"]["stem"]
    direction = _luck_direction(year_stem, birth.gender)
    month_pillar = chart["pillars"]["month"]
    month_index = _pillar_cycle_index(month_pillar["stem"], month_pillar["branch"])
    cycles = []

    for index in range(8):
        cycle_index = (month_index + index + 1) % 60 if direction == "forward" else (month_index - index - 1) % 60
        pillar = _cycle_pillar(cycle_index)
        start_age = 8 + index * 10
        cycles.append(
            {
                "start_age": start_age,
                "end_age": start_age + 9,
                "pillar": pillar,
                "relations_with_natal": _relations_with_natal(chart, pillar["branch"]),
            }
        )

    return {
        "direction": direction,
        "start_age_note": "approximate_start_age_pending_solar_term_engine",
        "cycles": cycles,
    }


def _birth_input(raw: Dict[str, Any]) -> BirthInput:
    return BirthInput(
        year=_int(raw.get("year"), 1990),
        month=_int(raw.get("month"), 5),
        day=_int(raw.get("day"), 12),
        hour=_int(raw.get("hour"), 10),
        gender="female" if raw.get("gender") == "female" else "male",
        calendar_type="lunar" if raw.get("calendar_type") == "lunar" else "solar",
    )


def _validate_solar_date(birth: BirthInput) -> None:
    date(birth.year, birth.month, birth.day)
    if birth.hour < 0 or birth.hour > 23:
        raise ValueError("invalid hour")


def _year_pillar(year: int, month: int, day: int) -> Dict[str, str]:
    bazi_year = year - 1 if month < 2 or (month == 2 and day < 4) else year
    return _cycle_pillar(bazi_year - 4)


def _month_pillar(month: int, day: int, year_stem: str) -> Dict[str, str]:
    offset = _solar_month_offset(month, day)
    start_stem = MONTH_START_STEM_BY_YEAR_STEM[year_stem]
    stem = STEMS[(STEMS.index(start_stem) + offset) % 10]
    branch = MONTH_BRANCH_SEQUENCE[offset]
    return _pillar(stem, branch)


def _day_pillar(year: int, month: int, day: int) -> Dict[str, str]:
    jdn = _julian_day_number(year, month, day)
    return _cycle_pillar(jdn + 49)


def _hour_pillar(hour: int, day_stem: str) -> Dict[str, str]:
    branch_index = ((hour + 1) // 2) % 12
    start_stem = HOUR_START_STEM_BY_DAY_STEM[day_stem]
    stem = STEMS[(STEMS.index(start_stem) + branch_index) % 10]
    return _pillar(stem, BRANCHES[branch_index])


def _pillar(stem: str, branch: str) -> Dict[str, str]:
    branch_stem = BRANCH_MAIN_STEM[branch]
    return {
        "stem": stem,
        "branch": branch,
        "display": f"{stem}{branch}",
        "stem_element": STEM_ELEMENT[stem],
        "stem_yin_yang": STEM_YIN_YANG[stem],
        "branch_element": STEM_ELEMENT[branch_stem],
        "branch_yin_yang": STEM_YIN_YANG[branch_stem],
    }


def _cycle_pillar(index: int) -> Dict[str, str]:
    return _pillar(STEMS[index % 10], BRANCHES[index % 12])


def _solar_month_offset(month: int, day: int) -> int:
    thresholds = {1: 6, 2: 4, 3: 6, 4: 5, 5: 6, 6: 6, 7: 7, 8: 8, 9: 8, 10: 8, 11: 7, 12: 7}
    if month == 1:
        return 11 if day >= thresholds[month] else 10
    if month == 2:
        return 0 if day >= thresholds[month] else 11
    return month - 2 if day >= thresholds[month] else month - 3


def _relations_from_branches(branches: List[tuple[str, str]]) -> Dict[str, List[Dict[str, Any]]]:
    rows = []
    for left_index, (left_name, left) in enumerate(branches):
        for right_name, right in branches[left_index + 1 :]:
            if _has_pair(SIX_COMBINATIONS, left, right):
                rows.append({"type": "six_combination", "branches": f"{left}{right}", "pillars": [left_name, right_name]})
            if _has_pair(SIX_CLASHES, left, right):
                rows.append({"type": "six_clash", "branches": f"{left}{right}", "pillars": [left_name, right_name]})
    present = {branch for _, branch in branches}
    for harmony in THREE_HARMONIES:
        if set(harmony) <= present:
            rows.append({"type": "three_harmony", "branches": "".join(harmony), "pillars": [name for name, branch in branches if branch in harmony]})
    return {"items": rows}


def _relations_with_natal(chart: Dict[str, Any], branch: str) -> Dict[str, List[str]]:
    natal = [pillar["branch"] for pillar in chart["pillars"].values()]
    clashes = [f"{left}{right}" for left, right in SIX_CLASHES if branch in (left, right) and any(item != branch and item in (left, right) for item in natal)]
    combinations = [f"{left}{right}" for left, right in SIX_COMBINATIONS if branch in (left, right) and any(item != branch and item in (left, right) for item in natal)]
    for harmony in THREE_HARMONIES:
        if branch in harmony and sum(1 for item in harmony if item != branch and item in natal) >= 2:
            combinations.append("".join(harmony))
    return {"clashes": sorted(set(clashes)), "combinations": sorted(set(combinations))}


def _luck_direction(year_stem: str, gender: str) -> str:
    yang_stem = year_stem in {"甲", "丙", "戊", "庚", "壬"}
    return "forward" if (yang_stem and gender == "male") or (not yang_stem and gender == "female") else "reverse"


def _pillar_cycle_index(stem: str, branch: str) -> int:
    for index in range(60):
        if STEMS[index % 10] == stem and BRANCHES[index % 12] == branch:
            return index
    return 0


def _agent_reply(chart: Dict[str, Any], flow_year: Dict[str, Any], luck_cycle: Dict[str, Any] | None, message: str) -> Dict[str, Any]:
    pillars = " ".join(f"{name}:{pillar['display']}" for name, pillar in chart["pillars"].items())
    flow_relations = [f"clash:{item}" for item in flow_year["relations_with_natal"]["clashes"]] + [
        f"combination:{item}" for item in flow_year["relations_with_natal"]["combinations"]
    ]
    luck = f"{luck_cycle['start_age']}-{luck_cycle['end_age']}:{luck_cycle['pillar']['display']}" if luck_cycle else "not_selected_by_age_range"
    return {
        "role": "v19_structure_agent",
        "content": [
            "已生成四柱、大运结构和所选流年结构。",
            f"四柱：{pillars}",
            f"流年：{flow_year['year']} ({flow_year['pillar']['display']})",
            f"当前大运：{luck}",
            f"流年关系：{', '.join(flow_relations) if flow_relations else 'none'}",
            f"用户问题已记录为结构上下文：{message}" if message else "可以继续询问结构层问题。",
        ],
        "guardrails": ["no fortune", "no narrative prediction", "no good/bad judgement", "time is context only"],
    }


def _julian_day_number(year: int, month: int, day: int) -> int:
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + ((153 * m + 2) // 5) + 365 * y + (y // 4) - (y // 100) + (y // 400) - 32045


def _has_pair(pairs: List[tuple[str, str]], left: str, right: str) -> bool:
    return any({a, b} == {left, right} for a, b in pairs)


def _int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback
