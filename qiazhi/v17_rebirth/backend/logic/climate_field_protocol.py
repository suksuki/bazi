from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from v17_rebirth.backend.logic.configs.manager import get_v17_constants


STEM_ELEMENT: Dict[str, str] = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

STEM_YIN: Dict[str, bool] = {
    "甲": False, "乙": True,
    "丙": False, "丁": True,
    "戊": False, "己": True,
    "庚": False, "辛": True,
    "壬": False, "癸": True,
}

ELEMENT_CYCLE: List[str] = ["木", "火", "土", "金", "水"]

BRANCH_HIDDEN: Dict[str, List[Tuple[str, float]]] = {
    "子": [("癸", 1.00)],
    "丑": [("己", 0.60), ("癸", 0.20), ("辛", 0.20)],
    "寅": [("甲", 0.70), ("丙", 0.20), ("戊", 0.10)],
    "卯": [("乙", 1.00)],
    "辰": [("戊", 0.60), ("乙", 0.20), ("癸", 0.20)],
    "巳": [("丙", 0.70), ("庚", 0.20), ("戊", 0.10)],
    "午": [("丁", 0.70), ("己", 0.30)],
    "未": [("己", 0.60), ("丁", 0.20), ("乙", 0.20)],
    "申": [("庚", 0.70), ("壬", 0.20), ("戊", 0.10)],
    "酉": [("辛", 1.00)],
    "戌": [("戊", 0.60), ("辛", 0.20), ("丁", 0.20)],
    "亥": [("壬", 0.70), ("甲", 0.30)],
}

ELEMENT_CLIMATE_VECTORS: Dict[str, Tuple[float, float]] = {
    "木": (0.18, 0.34),
    "火": (0.82, -0.78),
    "土": (0.24, -0.16),
    "金": (-0.46, -0.44),
    "水": (-0.84, 0.88),
}

ELEMENT_CLIMATE_IDEALS: Dict[str, Tuple[float, float]] = {
    "木": (0.26, 0.56),
    "火": (0.88, -0.22),
    "土": (0.30, -0.08),
    "金": (-0.36, -0.54),
    "水": (-0.78, 0.74),
}

ELEMENT_TO_STEMS: Dict[str, Tuple[str, str]] = {
    "木": ("甲", "乙"),
    "火": ("丙", "丁"),
    "土": ("戊", "己"),
    "金": ("庚", "辛"),
    "水": ("壬", "癸"),
}

_PILLAR_ORDER: Tuple[str, ...] = ("year", "month", "day", "hour")


def _cfg() -> Dict[str, Any]:
    return get_v17_constants().get("CLIMATE_FIELD", {})


def _cfg_float(key: str, default: float) -> float:
    try:
        return float(_cfg().get(key, default))
    except (TypeError, ValueError):
        return float(default)


def _scope_weight(scope: str, layer: str) -> float:
    layer_key = "STEM_SCOPE" if layer == "stem" else "BRANCH_SCOPE"
    return _cfg_float(f"{layer_key}_{str(scope).upper()}", 1.0)


def _parse_gz(gz: str) -> Tuple[str, str]:
    text = str(gz or "").strip()
    if len(text) < 2:
        return "", ""
    return text[0], text[1]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _round4(value: Any) -> float:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return 0.0


def ten_god_from_stems(daymaster: str, target: str) -> str:
    dm_el = STEM_ELEMENT.get(daymaster, "")
    tg_el = STEM_ELEMENT.get(target, "")
    if not dm_el or not tg_el:
        return "比肩"
    dm_yin = STEM_YIN.get(daymaster, False)
    tg_yin = STEM_YIN.get(target, False)
    dm_idx = ELEMENT_CYCLE.index(dm_el)
    produces = ELEMENT_CYCLE[(dm_idx + 1) % 5]
    produced_by = ELEMENT_CYCLE[(dm_idx - 1) % 5]
    controls = ELEMENT_CYCLE[(dm_idx + 2) % 5]
    controlled_by = ELEMENT_CYCLE[(dm_idx - 2) % 5]
    if tg_el == dm_el:
        return "劫财" if tg_yin != dm_yin else "比肩"
    if tg_el == produces:
        return "伤官" if tg_yin != dm_yin else "食神"
    if tg_el == produced_by:
        return "偏印" if tg_yin == dm_yin else "正印"
    if tg_el == controls:
        return "偏财" if tg_yin == dm_yin else "正财"
    if tg_el == controlled_by:
        return "七杀" if tg_yin == dm_yin else "正官"
    return "比肩"


def _climate_state(thermal_index: float, moisture_index: float) -> str:
    thermal = _clamp(thermal_index, -1.25, 1.25)
    moisture = _clamp(moisture_index, -1.25, 1.25)
    if thermal >= 0.45 and moisture <= -0.25:
        return "炎燥"
    if thermal >= 0.45 and moisture >= 0.25:
        return "炎湿"
    if thermal <= -0.45 and moisture >= 0.25:
        return "寒湿"
    if thermal <= -0.45 and moisture <= -0.25:
        return "寒燥"
    if thermal >= 0.25:
        return "偏暖"
    if thermal <= -0.25:
        return "偏寒"
    if moisture >= 0.25:
        return "偏湿"
    if moisture <= -0.25:
        return "偏燥"
    return "中和"


def _pattern_survival_delta(priority_map: Dict[str, float]) -> Dict[str, float]:
    def _avg(*gods: str) -> float:
        vals = [float(priority_map.get(god, 0.0)) for god in gods if god]
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    return {
        "印比": _avg("正印", "偏印", "比肩", "劫财"),
        "印官": _avg("正印", "偏印", "正官", "七杀"),
        "食伤财": _avg("食神", "伤官", "正财", "偏财"),
        "财官": _avg("正财", "偏财", "正官", "七杀"),
    }


def build_climate_field(
    *,
    four_pillars: Dict[str, str],
    luck_pillar: str = "",
    flow_pillar: str = "",
    daymaster: str = "",
) -> Dict[str, Any]:
    stem_layer_factor = _cfg_float("STEM_LAYER_FACTOR", 1.0)
    branch_layer_factor = _cfg_float("BRANCH_LAYER_FACTOR", 1.16)
    month_branch_boost = _cfg_float("MONTH_BRANCH_SEASON_BOOST", 1.24)
    thermal_normalizer = _cfg_float("THERMAL_NORMALIZER", 4.8)
    moisture_normalizer = _cfg_float("MOISTURE_NORMALIZER", 4.8)
    affinity_scale = _cfg_float("CLIMATE_AFFINITY_SCALE", 1.72)
    max_eff_delta = _cfg_float("MAX_EFFICIENCY_DELTA", 0.26)
    max_stability_delta = _cfg_float("MAX_STABILITY_DELTA", 0.22)
    tension_heat_weight = _cfg_float("TENSION_HEAT_WEIGHT", 0.44)
    tension_moisture_weight = _cfg_float("TENSION_MOISTURE_WEIGHT", 0.36)
    tension_mix_weight = _cfg_float("TENSION_MIX_WEIGHT", 0.28)

    raw_thermal = 0.0
    raw_moisture = 0.0
    source_rows: List[Dict[str, Any]] = []
    by_element: Dict[str, Dict[str, float]] = {element: {"thermal": 0.0, "moisture": 0.0} for element in ELEMENT_CLIMATE_VECTORS}
    by_scope: Dict[str, Dict[str, float]] = {}

    scope_rows: List[Tuple[str, str]] = [(scope, str(four_pillars.get(scope) or "").strip()) for scope in _PILLAR_ORDER]
    if luck_pillar:
        scope_rows.append(("luck", str(luck_pillar or "").strip()))
    if flow_pillar:
        scope_rows.append(("flow", str(flow_pillar or "").strip()))

    for scope, pillar in scope_rows:
        stem, branch = _parse_gz(pillar)
        scope_bucket = by_scope.setdefault(scope, {"thermal": 0.0, "moisture": 0.0})
        if stem:
            element = STEM_ELEMENT.get(stem, "")
            if element:
                thermal_vec, moisture_vec = ELEMENT_CLIMATE_VECTORS[element]
                weight = _scope_weight(scope, "stem") * stem_layer_factor
                thermal_delta = thermal_vec * weight
                moisture_delta = moisture_vec * weight
                raw_thermal += thermal_delta
                raw_moisture += moisture_delta
                by_element[element]["thermal"] += thermal_delta
                by_element[element]["moisture"] += moisture_delta
                scope_bucket["thermal"] += thermal_delta
                scope_bucket["moisture"] += moisture_delta
                source_rows.append(
                    {
                        "scope": scope,
                        "layer": "stem",
                        "member": stem,
                        "element": element,
                        "weight": _round4(weight),
                        "thermal_delta": _round4(thermal_delta),
                        "moisture_delta": _round4(moisture_delta),
                    }
                )

        if branch:
            branch_weight = _scope_weight(scope, "branch") * branch_layer_factor
            if scope == "month":
                branch_weight *= month_branch_boost
            for hidden_stem, hidden_weight in BRANCH_HIDDEN.get(branch, []):
                element = STEM_ELEMENT.get(hidden_stem, "")
                if not element:
                    continue
                thermal_vec, moisture_vec = ELEMENT_CLIMATE_VECTORS[element]
                weight = branch_weight * float(hidden_weight)
                thermal_delta = thermal_vec * weight
                moisture_delta = moisture_vec * weight
                raw_thermal += thermal_delta
                raw_moisture += moisture_delta
                by_element[element]["thermal"] += thermal_delta
                by_element[element]["moisture"] += moisture_delta
                scope_bucket["thermal"] += thermal_delta
                scope_bucket["moisture"] += moisture_delta
                source_rows.append(
                    {
                        "scope": scope,
                        "layer": "branch_hidden",
                        "member": f"{branch}:{hidden_stem}",
                        "element": element,
                        "weight": _round4(weight),
                        "thermal_delta": _round4(thermal_delta),
                        "moisture_delta": _round4(moisture_delta),
                    }
                )

    thermal_index = _clamp(raw_thermal / max(thermal_normalizer, 1e-6), -1.25, 1.25)
    moisture_index = _clamp(raw_moisture / max(moisture_normalizer, 1e-6), -1.25, 1.25)
    heat = max(thermal_index, 0.0)
    cold = max(-thermal_index, 0.0)
    humidity = max(moisture_index, 0.0)
    dryness = max(-moisture_index, 0.0)
    climate_tension = _clamp(
        abs(thermal_index) * tension_heat_weight
        + abs(moisture_index) * tension_moisture_weight
        + abs(thermal_index * moisture_index) * tension_mix_weight,
        0.0,
        1.0,
    )

    efficiency_map: Dict[str, float] = {}
    stability_map: Dict[str, float] = {}
    priority_map: Dict[str, float] = {}
    if daymaster:
        for element, stems in ELEMENT_TO_STEMS.items():
            ideal_thermal, ideal_moisture = ELEMENT_CLIMATE_IDEALS[element]
            distance = math.sqrt(
                ((thermal_index - ideal_thermal) ** 2) * 0.56
                + ((moisture_index - ideal_moisture) ** 2) * 0.44
            )
            affinity = _clamp(1.0 - distance / max(affinity_scale, 1e-6), 0.0, 1.0)
            eff_delta = _clamp((affinity - 0.5) * 2.0 * max_eff_delta, -max_eff_delta, max_eff_delta)
            stability_delta = _clamp(
                (affinity - 0.5) * 2.0 * max_stability_delta - climate_tension * 0.12,
                -max_stability_delta,
                max_stability_delta,
            )
            priority_delta = _clamp(eff_delta * 0.72 + stability_delta * 0.44, -0.35, 0.35)
            for stem in stems:
                god = ten_god_from_stems(daymaster, stem)
                efficiency_map[god] = _round4(eff_delta)
                stability_map[god] = _round4(stability_delta)
                priority_map[god] = _round4(priority_delta)

    return {
        "contract": "v17.climate_field.v1",
        "state": _climate_state(thermal_index, moisture_index),
        "thermal_index": _round4(thermal_index),
        "moisture_index": _round4(moisture_index),
        "heat": _round4(heat),
        "cold": _round4(cold),
        "humidity": _round4(humidity),
        "dryness": _round4(dryness),
        "climate_tension": _round4(climate_tension),
        "source_rows": source_rows[:24],
        "source_by_element": {
            element: {"thermal": _round4(values["thermal"]), "moisture": _round4(values["moisture"])}
            for element, values in by_element.items()
        },
        "source_by_scope": {
            scope: {"thermal": _round4(values["thermal"]), "moisture": _round4(values["moisture"])}
            for scope, values in by_scope.items()
        },
        "climate_modifier_layer": {
            "contract": "v17.climate_modifier_layer.v1",
            "ten_god_efficiency": dict(sorted(efficiency_map.items())),
            "ten_god_stability": dict(sorted(stability_map.items())),
            "yongshen_priority_delta": dict(sorted(priority_map.items())),
            "pattern_survival_delta": _pattern_survival_delta(priority_map),
        },
    }


def climate_field_prompt_lines() -> List[str]:
    return [
        "调候合同：调候先落为底层 climate field，不直接改写 L0 原始十神总量；当前采用寒热轴 thermal_index 与燥湿轴 moisture_index 两条主轴，再派生 heat/cold/humidity/dryness/climate_tension。",
        "调候合同：调候第一阶段只输出 climate modifier layer，优先影响 ten_god_efficiency、ten_god_stability、yongshen_priority_delta、pattern_survival_delta。",
    ]


def climate_field_protocol_payload() -> Dict[str, Any]:
    return {
        "contract": "v17.climate_field.protocol.v1",
        "element_vectors": {
            element: {"thermal": vector[0], "moisture": vector[1]}
            for element, vector in ELEMENT_CLIMATE_VECTORS.items()
        },
        "element_ideals": {
            element: {"thermal": vector[0], "moisture": vector[1]}
            for element, vector in ELEMENT_CLIMATE_IDEALS.items()
        },
        "stem_scope_weights": {
            scope: _scope_weight(scope, "stem")
            for scope in ("year", "month", "day", "hour", "luck", "flow")
        },
        "branch_scope_weights": {
            scope: _scope_weight(scope, "branch")
            for scope in ("year", "month", "day", "hour", "luck", "flow")
        },
        "stem_layer_factor": _cfg_float("STEM_LAYER_FACTOR", 1.0),
        "branch_layer_factor": _cfg_float("BRANCH_LAYER_FACTOR", 1.16),
        "month_branch_season_boost": _cfg_float("MONTH_BRANCH_SEASON_BOOST", 1.24),
    }
