"""Pure calculation helpers for the physics engine.

月令季节矩阵缺省在 ``physics_rules.DEFAULT_SEASONAL_BASE`` 与 DB 种子表维护；
本模块不重复定义季节系数。冲突折损由 ``conflict_auditor_v1`` 法典驱动，不在此实现 γ 惩罚分支。
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import re
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.bazi_metadata import BaziMetadata
from app.core.bazi.engine import (
    blend_position_weights_l0,
    branch_hidden_stems_effective,
    ensure_l0_for_physics,
    get_root_resonance,
)
from app.skills.physics_rules import (
    DEFAULT_POSITION_WEIGHTS,
    MONTH_BRANCH_TO_SEASON,
    ROOT_MAP,
    STEM_TO_ELEMENT,
    TEN_DEITIES,
    WEIGHT_LUCK,
    WEIGHT_YEAR,
    deity_from_self_and_target_stem,
)

_ELEMENT_KEYS = ("wood", "fire", "earth", "metal", "water")


def _element_conflict_scale(conflict_element_mods: Optional[Dict[str, float]], element: str) -> float:
    """冲突法典五行折损：在全局 ``conflict_factor`` 之后按元素再乘（默认 1.0）。"""
    if not conflict_element_mods:
        return 1.0
    try:
        return max(0.0, float(conflict_element_mods.get(element, 1.0) or 1.0))
    except (TypeError, ValueError):
        return 1.0


def normalize_element_vector(vector: Dict[str, float]) -> Dict[str, float]:
    """将五行 raw 场强归一为分布（与 ``PhysicsInferenceSkill`` 最终 normalized 同形，供调候前后对比）。"""
    t = sum(max(0.0, float(vector.get(k, 0.0))) for k in _ELEMENT_KEYS) or 1.0
    return {k: round(max(0.0, float(vector.get(k, 0.0))) / t, 4) for k in _ELEMENT_KEYS}


def root_coupling_check(metadata: BaziMetadata, floating_decay: float) -> tuple[Dict[str, Any], float]:
    day_stem = metadata.pillars.day.stem
    day_element = STEM_TO_ELEMENT.get(day_stem, "")
    branches = [
        metadata.pillars.year.branch,
        metadata.pillars.month.branch,
        metadata.pillars.day.branch,
        metadata.pillars.hour.branch,
    ]
    roots = ROOT_MAP.get(day_stem, set())
    matched = [branch for branch in branches if branch in roots]
    no_root = len(matched) == 0
    decay_factor = max(0.0, 1.0 - float(floating_decay)) if no_root and day_element == "wood" else 1.0
    record = (
        f"[ROOT_CHECK] Target: {day_stem}木, Result: NULL, Action: CF_FLOATING_DECAY({floating_decay}) applied."
        if no_root and day_stem == "乙"
        else (
            f"[ROOT_CHECK] Target: {day_stem}, Result: NULL, Action: CF_FLOATING_DECAY({floating_decay}) applied."
            if no_root
            else f"[ROOT_CHECK] Target: {day_stem}, Result: ROOT_FOUND({','.join(matched)}), Action: no_decay."
        )
    )
    return {
        "target_stem": day_stem,
        "branches": branches,
        "matched_roots": matched,
        "no_root": no_root,
        "decay_factor": round(decay_factor, 4),
        "record": record,
    }, decay_factor


def build_energy_fields(
    *,
    metadata: BaziMetadata,
    position_weights: Dict[str, float],
    climate_mods: Dict[str, float],
    day_stem: str,
    stem_boost: float,
    root_decay: float,
    conflict_factor: float,
    protrusion: float,
    floating_deities: set[str],
    root_decay_factor: float,
    dayun: str | None,
    liunian: str | None,
    weight_luck: float = WEIGHT_LUCK,
    weight_year: float = WEIGHT_YEAR,
    runtime_physics: Dict[str, float] | None = None,
    conflict_element_mods: Dict[str, float] | None = None,
) -> tuple[Dict[str, Dict[str, float]], Dict[str, float], Dict[str, float], Dict[str, List[Dict[str, Any]]]]:
    ensure_l0_for_physics()
    rp = runtime_physics or {}
    hidden_table = branch_hidden_stems_effective()
    pos_weights = blend_position_weights_l0(position_weights, rp)
    pillar_branches = [str(getattr(metadata.pillars, p).branch) for p in ("year", "month", "day", "hour")]
    l0_hidden_scale = float(rp.get("L0_HIDDEN_ENERGY_SCALE", 1.0))

    result_by_pillar: Dict[str, Dict[str, float]] = {}
    vector = {"wood": 0.0, "fire": 0.0, "earth": 0.0, "metal": 0.0, "water": 0.0}
    raw_deity_energy: Dict[str, float] = {key: 0.0 for key in TEN_DEITIES}
    deity_contribution_sources: Dict[str, List[Dict[str, Any]]] = {key: [] for key in TEN_DEITIES}

    for pillar in ("year", "month", "day", "hour"):
        pair = getattr(metadata.pillars, pillar)
        pos_weight = pos_weights.get(pillar, DEFAULT_POSITION_WEIGHTS[pillar])
        stem_char = pair.stem
        stem_element = STEM_TO_ELEMENT.get(stem_char, "earth")
        climate_el = float(climate_mods.get(stem_element, 1.0))
        raw = float(pair.energy_value)
        root_fac = get_root_resonance(stem_char, pillar_branches, rp)
        el_cf = _element_conflict_scale(conflict_element_mods, stem_element)
        stem_energy = raw * pos_weight * climate_el * stem_boost * root_decay * conflict_factor * el_cf * protrusion * root_fac

        vector[stem_element] += stem_energy
        deity_stem = deity_from_self_and_target_stem(day_stem=day_stem, target_stem=stem_char)
        if not (pillar == "day" and stem_char == day_stem):
            adjusted_stem_energy = stem_energy * root_decay_factor if deity_stem in floating_deities else stem_energy
            raw_deity_energy[deity_stem] += adjusted_stem_energy
            deity_contribution_sources[deity_stem].append(
                {
                    "source": f"{pillar}.stem:{stem_char}",
                    "raw_energy": round(raw, 4),
                    "position_weight": round(pos_weight, 4),
                    "climate_mod": round(climate_el, 4),
                    "hidden_ratio": 1.0,
                    "contribution_energy": round(adjusted_stem_energy, 4),
                }
            )
        else:
            adjusted_stem_energy = stem_energy

        branch_char = pair.branch
        hidden = hidden_table.get(branch_char, {})
        for hidden_stem, ratio in hidden.items():
            hidden_element = STEM_TO_ELEMENT.get(hidden_stem, "earth")
            climate_h = float(climate_mods.get(hidden_element, 1.0))
            hid_root = get_root_resonance(hidden_stem, pillar_branches, rp)
            h_cf = _element_conflict_scale(conflict_element_mods, hidden_element)
            hidden_energy = (
                raw
                * (float(ratio) / 100.0)
                * pos_weight
                * climate_h
                * stem_boost
                * root_decay
                * conflict_factor
                * h_cf
                * protrusion
                * l0_hidden_scale
                * hid_root
            )
            vector[hidden_element] += hidden_energy
            deity_hidden = deity_from_self_and_target_stem(day_stem=day_stem, target_stem=hidden_stem)
            adjusted_hidden_energy = hidden_energy * root_decay_factor if deity_hidden in floating_deities else hidden_energy
            raw_deity_energy[deity_hidden] += adjusted_hidden_energy
            deity_contribution_sources[deity_hidden].append(
                {
                    "source": f"{pillar}.branch:{branch_char}.hidden:{hidden_stem}",
                    "raw_energy": round(raw, 4),
                    "position_weight": round(pos_weight, 4),
                    "climate_mod": round(climate_h, 4),
                    "hidden_ratio": round(float(ratio) / 100.0, 4),
                    "contribution_energy": round(adjusted_hidden_energy, 4),
                }
            )

        result_by_pillar[pillar] = {
            "element": stem_element,
            "raw_energy": raw,
            "weight": pos_weight,
            "climate_mod": round(climate_el, 4),
            "stem_energy": round(adjusted_stem_energy, 4),
        }

    inject_disturbance(
        ganzhi=dayun,
        weight=weight_luck,
        tag="luck",
        vector=vector,
        raw_deity_energy=raw_deity_energy,
        deity_contribution_sources=deity_contribution_sources,
        climate_mods=climate_mods,
        day_stem=day_stem,
        stem_boost=stem_boost,
        root_decay=root_decay,
        conflict_factor=conflict_factor,
        protrusion=protrusion,
        floating_deities=floating_deities,
        root_decay_factor=root_decay_factor,
        branch_hidden=hidden_table,
        runtime_physics=rp,
        conflict_element_mods=conflict_element_mods,
    )
    inject_disturbance(
        ganzhi=liunian,
        weight=weight_year,
        tag="year",
        vector=vector,
        raw_deity_energy=raw_deity_energy,
        deity_contribution_sources=deity_contribution_sources,
        climate_mods=climate_mods,
        day_stem=day_stem,
        stem_boost=stem_boost,
        root_decay=root_decay,
        conflict_factor=conflict_factor,
        protrusion=protrusion,
        floating_deities=floating_deities,
        root_decay_factor=root_decay_factor,
        branch_hidden=hidden_table,
        runtime_physics=rp,
        conflict_element_mods=conflict_element_mods,
    )
    return result_by_pillar, vector, raw_deity_energy, deity_contribution_sources


def inject_disturbance(
    *,
    ganzhi: str | None,
    weight: float,
    tag: str,
    vector: Dict[str, float],
    raw_deity_energy: Dict[str, float],
    deity_contribution_sources: Dict[str, List[Dict[str, Any]]],
    climate_mods: Dict[str, float],
    day_stem: str,
    stem_boost: float,
    root_decay: float,
    conflict_factor: float,
    protrusion: float,
    floating_deities: set[str],
    root_decay_factor: float,
    branch_hidden: Dict[str, Dict[str, float]] | None = None,
    runtime_physics: Dict[str, float] | None = None,
    conflict_element_mods: Dict[str, float] | None = None,
) -> None:
    if not ganzhi or len(str(ganzhi)) < 2:
        return
    ensure_l0_for_physics()
    rp = runtime_physics or {}
    ht = branch_hidden if branch_hidden is not None else branch_hidden_stems_effective()
    l0_hidden_scale = float(rp.get("L0_HIDDEN_ENERGY_SCALE", 1.0))
    stem_char = str(ganzhi)[0]
    branch_char = str(ganzhi)[1]
    stem_element = STEM_TO_ELEMENT.get(stem_char, "earth")
    climate_stem = float(climate_mods.get(stem_element, 1.0))
    s_cf = _element_conflict_scale(conflict_element_mods, stem_element)
    stem_energy = (
        100.0
        * weight
        * climate_stem
        * stem_boost
        * root_decay
        * conflict_factor
        * s_cf
        * protrusion
        * get_root_resonance(stem_char, [branch_char], rp)
    )
    stem_deity = deity_from_self_and_target_stem(day_stem=day_stem, target_stem=stem_char)
    adjusted_stem = stem_energy * root_decay_factor if stem_deity in floating_deities else stem_energy
    vector[stem_element] += adjusted_stem
    raw_deity_energy[stem_deity] += adjusted_stem
    deity_contribution_sources[stem_deity].append(
        {
            "source": f"{tag}.stem:{stem_char}",
            "raw_energy": 100.0,
            "position_weight": round(weight, 4),
            "climate_mod": round(climate_stem, 4),
            "hidden_ratio": 1.0,
            "contribution_energy": round(adjusted_stem, 4),
        }
    )
    for hidden_stem, ratio in ht.get(branch_char, {}).items():
        hidden_element = STEM_TO_ELEMENT.get(hidden_stem, "earth")
        climate_hidden = float(climate_mods.get(hidden_element, 1.0))
        hc = _element_conflict_scale(conflict_element_mods, hidden_element)
        hidden_energy = (
            100.0
            * weight
            * (float(ratio) / 100.0)
            * climate_hidden
            * stem_boost
            * root_decay
            * conflict_factor
            * hc
            * protrusion
            * l0_hidden_scale
            * get_root_resonance(hidden_stem, [branch_char], rp)
        )
        hidden_deity = deity_from_self_and_target_stem(day_stem=day_stem, target_stem=hidden_stem)
        adjusted_hidden = hidden_energy * root_decay_factor if hidden_deity in floating_deities else hidden_energy
        vector[hidden_element] += adjusted_hidden
        raw_deity_energy[hidden_deity] += adjusted_hidden
        deity_contribution_sources[hidden_deity].append(
            {
                "source": f"{tag}.branch:{branch_char}.hidden:{hidden_stem}",
                "raw_energy": 100.0,
                "position_weight": round(weight, 4),
                "climate_mod": round(climate_hidden, 4),
                "hidden_ratio": round(float(ratio) / 100.0, 4),
                "contribution_energy": round(adjusted_hidden, 4),
            }
        )


def apply_climate_correction(
    *,
    metadata: BaziMetadata,
    vector: Dict[str, float],
    raw_deity_energy: Dict[str, float],
    deity_contribution_sources: Dict[str, List[Dict[str, Any]]],
    climate_enabled: bool,
    climate_factors: Dict[str, float] | None = None,
) -> tuple[Dict[str, float], Dict[str, float], Dict[str, Any]]:
    """
    Apply month-branch climate hard correction to elemental vector and deity Abs.
    Opposing element in current season is penalized (e.g. 子月 suppresses fire).
    """
    month_branch = metadata.pillars.month.branch
    season = MONTH_BRANCH_TO_SEASON.get(month_branch, "spring")
    factors = {el: 1.0 for el in ("wood", "fire", "earth", "metal", "water")}
    if climate_enabled and isinstance(climate_factors, dict):
        for el in factors.keys():
            factors[el] = float(climate_factors.get(el, 1.0))

    corrected_vector = {
        el: float(vector.get(el, 0.0)) * float(factors.get(el, 1.0))
        for el in ("wood", "fire", "earth", "metal", "water")
    }

    def _source_element(source: str) -> str:
        match = re.search(r"(?:\.stem:|\.hidden:)(.)", source or "")
        if match:
            return STEM_TO_ELEMENT.get(match.group(1), "earth")
        return "earth"

    corrected_deity: Dict[str, float] = {}
    for deity in TEN_DEITIES:
        entries = list((deity_contribution_sources or {}).get(deity) or [])
        if not entries:
            corrected_deity[deity] = float(raw_deity_energy.get(deity, 0.0))
            continue
        total = 0.0
        for item in entries:
            source = str(item.get("source", ""))
            contribution = float(item.get("contribution_energy", 0.0))
            total += contribution * float(factors.get(_source_element(source), 1.0))
        corrected_deity[deity] = total

    trace = {
        "enabled": bool(climate_enabled),
        "month_branch": month_branch,
        "season": season,
        "factors": factors,
    }
    return corrected_vector, corrected_deity, trace


def calculate_deity_scores(
    *,
    raw_deity_energy: Dict[str, float],
    interaction_params: Dict[str, float],
    contribution_sources: Dict[str, List[Dict[str, Any]]] | None,
    root_check: Dict[str, Any] | None,
) -> Tuple[Dict[str, float], Dict[str, Dict[str, Any]], Dict[str, Dict[str, float]], Dict[str, Dict[str, Any]]]:
    raw_deity_energy = {key: float(raw_deity_energy.get(key, 0.0)) for key in TEN_DEITIES}
    raw_self = raw_deity_energy["比肩"] + raw_deity_energy["劫财"]
    raw_output = raw_deity_energy["食神"] + raw_deity_energy["伤官"]
    raw_wealth = raw_deity_energy["正财"] + raw_deity_energy["偏财"]
    raw_power = raw_deity_energy["正官"] + raw_deity_energy["七杀"]
    raw_support = raw_deity_energy["正印"] + raw_deity_energy["偏印"]

    support_same = raw_deity_energy["偏印"]
    support_diff = raw_deity_energy["正印"]
    output_same = raw_deity_energy["食神"]
    output_diff = raw_deity_energy["伤官"]
    wealth_same = raw_deity_energy["偏财"]
    wealth_diff = raw_deity_energy["正财"]
    power_same = raw_deity_energy["七杀"]
    power_diff = raw_deity_energy["正官"]

    eff_promoting_same = interaction_params.get("EFF_PROMOTING_SAME", interaction_params.get("EFF_PROMOTING", 1.0))
    eff_promoting_diff = interaction_params.get("EFF_PROMOTING_DIFF", interaction_params.get("EFF_PROMOTING", 1.0))
    eff_exhausting_same = interaction_params.get("EFF_EXHAUSTING_SAME", interaction_params.get("EFF_EXHAUSTING", 1.0))
    eff_exhausting_diff = interaction_params.get("EFF_EXHAUSTING_DIFF", interaction_params.get("EFF_EXHAUSTING", 1.0))
    eff_restraining_same = interaction_params.get("EFF_RESTRAINING_SAME", interaction_params.get("EFF_RESTRAINING", 1.0))
    eff_restraining_diff = interaction_params.get("EFF_RESTRAINING_DIFF", interaction_params.get("EFF_RESTRAINING", 1.0))
    eff_consuming_same = interaction_params.get("EFF_CONSUMING_SAME", interaction_params.get("EFF_CONSUMING", 1.0))
    eff_consuming_diff = interaction_params.get("EFF_CONSUMING_DIFF", interaction_params.get("EFF_CONSUMING", 1.0))

    def weighted_eff(same_energy: float, diff_energy: float, eff_same: float, eff_diff: float, base: float) -> float:
        total = same_energy + diff_energy
        if total <= 0:
            return base
        return (same_energy * eff_same + diff_energy * eff_diff) / total

    eff_promoting = weighted_eff(support_same, support_diff, eff_promoting_same, eff_promoting_diff, interaction_params.get("EFF_PROMOTING", 1.0))
    eff_exhausting = weighted_eff(output_same, output_diff, eff_exhausting_same, eff_exhausting_diff, interaction_params.get("EFF_EXHAUSTING", 1.0))
    eff_restraining = weighted_eff(power_same, power_diff, eff_restraining_same, eff_restraining_diff, interaction_params.get("EFF_RESTRAINING", 1.0))
    eff_consuming = weighted_eff(wealth_same, wealth_diff, eff_consuming_same, eff_consuming_diff, interaction_params.get("EFF_CONSUMING", 1.0))

    e_self_new = raw_self + raw_support * (eff_promoting - 1.0)
    e_self_final = e_self_new * eff_restraining * eff_exhausting * eff_consuming
    self_change = max(0.0, raw_self - e_self_final)
    e_output_final = raw_output + self_change * (1.0 - eff_exhausting)
    e_wealth_final = raw_wealth + self_change * (1.0 - eff_consuming)
    e_power_final = raw_power + self_change * (1.0 - eff_restraining)
    e_support_final = raw_support * eff_promoting

    final = {key: 0.0 for key in TEN_DEITIES}
    if raw_self > 0:
        final["比肩"] = e_self_final * (raw_deity_energy["比肩"] / raw_self)
        final["劫财"] = e_self_final * (raw_deity_energy["劫财"] / raw_self)
    if raw_output > 0:
        final["食神"] = e_output_final * (raw_deity_energy["食神"] / raw_output)
        final["伤官"] = e_output_final * (raw_deity_energy["伤官"] / raw_output)
    if raw_wealth > 0:
        final["正财"] = e_wealth_final * (raw_deity_energy["正财"] / raw_wealth)
        final["偏财"] = e_wealth_final * (raw_deity_energy["偏财"] / raw_wealth)
    if raw_power > 0:
        final["正官"] = e_power_final * (raw_deity_energy["正官"] / raw_power)
        final["七杀"] = e_power_final * (raw_deity_energy["七杀"] / raw_power)
    if raw_support > 0:
        final["正印"] = e_support_final * (raw_deity_energy["正印"] / raw_support)
        final["偏印"] = e_support_final * (raw_deity_energy["偏印"] / raw_support)

    total = sum(final.values()) or 1.0
    pct = {key: (Decimal(str(value)) / Decimal(str(total)) * Decimal("100")) for key, value in final.items()}
    quantized = {key: value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) for key, value in pct.items()}
    diff = Decimal("100.00") - sum(quantized.values())
    if diff != Decimal("0.00"):
        anchor = max(quantized.keys(), key=lambda key: quantized[key])
        quantized[anchor] = (quantized[anchor] + diff).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    final_scores = {key: float(value) for key, value in quantized.items()}

    deity_components: Dict[str, Dict[str, Any]] = {}
    deity_energy_axes: Dict[str, Dict[str, float]] = {}
    trace_details: Dict[str, Dict[str, Any]] = {}
    sum_final = sum(final.values()) or 1.0
    intervention_params = {
        "EFF_PROMOTING": round(float(eff_promoting), 4),
        "EFF_EXHAUSTING": round(float(eff_exhausting), 4),
        "EFF_RESTRAINING": round(float(eff_restraining), 4),
        "EFF_CONSUMING": round(float(eff_consuming), 4),
        "EFF_PROMOTING_SAME": round(float(eff_promoting_same), 4),
        "EFF_PROMOTING_DIFF": round(float(eff_promoting_diff), 4),
        "EFF_EXHAUSTING_SAME": round(float(eff_exhausting_same), 4),
        "EFF_EXHAUSTING_DIFF": round(float(eff_exhausting_diff), 4),
        "EFF_RESTRAINING_SAME": round(float(eff_restraining_same), 4),
        "EFF_RESTRAINING_DIFF": round(float(eff_restraining_diff), 4),
        "EFF_CONSUMING_SAME": round(float(eff_consuming_same), 4),
        "EFF_CONSUMING_DIFF": round(float(eff_consuming_diff), 4),
        "CF_FLOATING_DECAY": round(float(interaction_params.get("CF_FLOATING_DECAY", 0.0)), 4),
        "A_PROTRUSION": round(float(interaction_params.get("A_PROTRUSION", 1.0)), 4),
    }
    for deity in TEN_DEITIES:
        contribution = list((contribution_sources or {}).get(deity, []))
        final_energy = float(final.get(deity, 0.0))
        raw_total = float(raw_deity_energy.get(deity, 0.0))
        raw_stem = sum(float(item.get("contribution_energy", 0.0)) for item in contribution if ".stem:" in str(item.get("source", "")))
        raw_root = max(0.0, raw_total - raw_stem)
        stem_final_energy = (final_energy * raw_stem / raw_total) if raw_total > 0 else 0.0
        root_final_energy = (final_energy * raw_root / raw_total) if raw_total > 0 else 0.0
        stem_score = round((stem_final_energy / sum_final) * 100.0, 2) if sum_final > 0 else 0.0
        total_score = round(float(final_scores.get(deity, 0.0)), 2)
        root_score = round(total_score - stem_score, 2)
        root_sources = sorted({
            f"{source.split('.branch:', 1)[0]}_branch"
            for source in [str(item.get("source", "")) for item in contribution]
            if ".branch:" in source
        })
        stem_sources = sorted({
            f"{source.split('.stem:', 1)[0]}_stem"
            for source in [str(item.get("source", "")) for item in contribution]
            if ".stem:" in source
        })
        deity_components[deity] = {
            "total_score": total_score,
            "stem_score": stem_score,
            "root_score": root_score,
            "root_sources": root_sources,
            "stem_sources": stem_sources,
            "is_floating": bool((root_check or {}).get("no_root", False)),
        }
        deity_energy_axes[deity] = {
            "absolute_energy": round(final_energy, 4),
            "relative_percentage": total_score,
        }
        trace_details[deity] = {
            "base_energy": {
                "raw_deity_energy": round(float(raw_deity_energy.get(deity, 0.0)), 4),
                "contribution_sources": contribution,
            },
            "root_strength": deity_components[deity],
            "interventions": {
                "applied_params": intervention_params,
                "self_pipeline": {
                    "raw_self": round(raw_self, 4),
                    "e_self_new": round(e_self_new, 4),
                    "e_self_final": round(e_self_final, 4),
                    "self_change": round(self_change, 4),
                },
            },
            "normalization": {
                "final_energy_before_pct": round(final_energy, 4),
                "all_deities_final_energy_sum": round(sum_final, 4),
                "final_percent": round(final_scores.get(deity, 0.0), 2),
                "formula": f"{round(final_energy, 4)} / {round(sum_final, 4)} * 100",
            },
        }
    return final_scores, deity_components, deity_energy_axes, trace_details
