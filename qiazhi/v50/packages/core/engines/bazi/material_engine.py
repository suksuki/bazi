from __future__ import annotations

from collections import Counter
from itertools import combinations

from core.contracts.base import SourceEngine, Topic
from core.contracts.birth import BirthInputCanonical, CalendarNormalizationResult
from core.contracts.material import MaterialType, MingliMaterial, UnifiedMingliMaterialStore
from core.engines.bazi.knowledge import (
    BRANCH_ELEMENTS,
    CONTROLS,
    GENERATES,
    HIDDEN_STEMS,
    SIX_CLASH,
    SIX_HARMONY,
    STEM_ELEMENTS,
    STEM_POLARITY,
)


def build_bazi_material_store(
    *,
    reading_id: str,
    birth_input: BirthInputCanonical,
    calendar: CalendarNormalizationResult,
) -> UnifiedMingliMaterialStore:
    materials: list[MingliMaterial] = []
    pillars = _pillars(birth_input)
    if not all(pillars.values()):
        return _store(reading_id=reading_id, materials=materials)
    materials.extend(_chart_fact_materials(reading_id=reading_id, birth_input=birth_input, calendar=calendar, pillars=pillars))
    materials.extend(_ten_god_materials(reading_id=reading_id, birth_input=birth_input, pillars=pillars))
    materials.extend(_hidden_stem_materials(reading_id=reading_id, birth_input=birth_input, pillars=pillars))
    materials.extend(_strength_materials(reading_id=reading_id, birth_input=birth_input, pillars=pillars))
    materials.extend(_branch_relation_materials(reading_id=reading_id, birth_input=birth_input, pillars=pillars))
    return _store(reading_id=reading_id, materials=materials)


def _pillars(birth_input: BirthInputCanonical) -> dict[str, str]:
    return {
        "year": birth_input.year_pillar.strip(),
        "month": birth_input.month_pillar.strip(),
        "day": birth_input.day_pillar.strip(),
        "hour": birth_input.hour_pillar.strip(),
    }


def _chart_fact_materials(
    *,
    reading_id: str,
    birth_input: BirthInputCanonical,
    calendar: CalendarNormalizationResult,
    pillars: dict[str, str],
) -> list[MingliMaterial]:
    day_stem = pillars["day"][0]
    month_branch = pillars["month"][1]
    return [
        MingliMaterial(
            material_id=f"material:{reading_id}:bazi:chart:pillars",
            reading_id=reading_id,
            source_engine=SourceEngine.BAZI,
            material_type=MaterialType.BAZI_CHART_FACT,
            topic=Topic.STRUCTURE,
            raw_value={"pillars": pillars},
            normalized_value=" ".join(pillars.values()),
            evidence_refs=[birth_input.birth_input_id],
            knowledge_refs=["bazi.stem_branch.pillars"],
            rule_refs=["bazi.material_engine.explicit_pillars"],
            confidence=calendar.confidence,
        ),
        MingliMaterial(
            material_id=f"material:{reading_id}:bazi:chart:day_master",
            reading_id=reading_id,
            source_engine=SourceEngine.BAZI,
            material_type=MaterialType.BAZI_CHART_FACT,
            topic=Topic.STRUCTURE,
            raw_value={"day_stem": day_stem, "element": STEM_ELEMENTS.get(day_stem, ""), "polarity": STEM_POLARITY.get(day_stem, "")},
            normalized_value=day_stem,
            evidence_refs=[birth_input.birth_input_id, f"material:{reading_id}:bazi:chart:pillars"],
            knowledge_refs=["bazi.stem_elements", "bazi.stem_polarity"],
            rule_refs=["bazi.material_engine.day_master"],
            confidence=0.95,
        ),
        MingliMaterial(
            material_id=f"material:{reading_id}:bazi:chart:month_branch",
            reading_id=reading_id,
            source_engine=SourceEngine.BAZI,
            material_type=MaterialType.BAZI_CHART_FACT,
            topic=Topic.STRUCTURE,
            raw_value={"month_branch": month_branch, "element": BRANCH_ELEMENTS.get(month_branch, "")},
            normalized_value=month_branch,
            evidence_refs=[birth_input.birth_input_id, f"material:{reading_id}:bazi:chart:pillars"],
            knowledge_refs=["bazi.branch_elements"],
            rule_refs=["bazi.material_engine.month_branch"],
            confidence=0.95,
        ),
    ]


def _ten_god_materials(*, reading_id: str, birth_input: BirthInputCanonical, pillars: dict[str, str]) -> list[MingliMaterial]:
    day_stem = pillars["day"][0]
    rows: list[dict[str, object]] = []
    for slot, pillar in pillars.items():
        stem = pillar[0]
        if slot == "day":
            continue
        rows.append({"slot": slot, "stem": stem, "ten_god": resolve_ten_god(day_stem=day_stem, other_stem=stem)})
    return [
        MingliMaterial(
            material_id=f"material:{reading_id}:bazi:ten_god:visible",
            reading_id=reading_id,
            source_engine=SourceEngine.BAZI,
            material_type=MaterialType.BAZI_TEN_GOD,
            topic=Topic.STRUCTURE,
            raw_value={"day_stem": day_stem, "visible_ten_gods": rows},
            normalized_value=";".join(f"{row['slot']}:{row['ten_god']}" for row in rows),
            evidence_refs=[birth_input.birth_input_id, f"material:{reading_id}:bazi:chart:day_master"],
            knowledge_refs=["bazi.ten_god.relations"],
            rule_refs=["resolve_ten_god"],
            confidence=0.82,
        )
    ]


def _hidden_stem_materials(*, reading_id: str, birth_input: BirthInputCanonical, pillars: dict[str, str]) -> list[MingliMaterial]:
    day_stem = pillars["day"][0]
    rows: list[dict[str, object]] = []
    for slot, pillar in pillars.items():
        branch = pillar[1]
        hidden = HIDDEN_STEMS.get(branch, [])
        rows.append(
            {
                "slot": slot,
                "branch": branch,
                "hidden_stems": hidden,
                "hidden_ten_gods": [resolve_ten_god(day_stem=day_stem, other_stem=stem) for stem in hidden],
            }
        )
    return [
        MingliMaterial(
            material_id=f"material:{reading_id}:bazi:hidden_stems",
            reading_id=reading_id,
            source_engine=SourceEngine.BAZI,
            material_type=MaterialType.BAZI_HIDDEN_STEM,
            topic=Topic.STRUCTURE,
            raw_value={"rows": rows},
            normalized_value=";".join(f"{row['branch']}:{','.join(row['hidden_stems'])}" for row in rows),
            evidence_refs=[birth_input.birth_input_id, f"material:{reading_id}:bazi:chart:pillars"],
            knowledge_refs=["bazi.hidden_stems", "bazi.ten_god.relations"],
            rule_refs=["hidden_stem_lookup", "resolve_ten_god"],
            confidence=0.8,
        )
    ]


def _strength_materials(*, reading_id: str, birth_input: BirthInputCanonical, pillars: dict[str, str]) -> list[MingliMaterial]:
    day_stem = pillars["day"][0]
    day_element = STEM_ELEMENTS.get(day_stem, "")
    root_sources = _root_sources(day_stem=day_stem, pillars=pillars)
    branch_elements = [BRANCH_ELEMENTS.get(pillar[1], "") for pillar in pillars.values()]
    stem_elements = [STEM_ELEMENTS.get(pillar[0], "") for pillar in pillars.values()]
    counts = Counter([*branch_elements, *stem_elements])
    support = counts.get(day_element, 0)
    generated_by = _generating_element(day_element)
    support += counts.get(generated_by, 0) * 0.65
    pressure = counts.get(CONTROLS.get(day_element, ""), 0)
    strength = min(1.0, round((support + 0.5) / 5.0, 3))
    return [
        MingliMaterial(
            material_id=f"material:{reading_id}:bazi:strength:day_master",
            reading_id=reading_id,
            source_engine=SourceEngine.BAZI,
            material_type=MaterialType.BAZI_STRENGTH,
            topic=Topic.STRUCTURE,
            raw_value={
                "day_element": day_element,
                "element_counts": dict(counts),
                "support_score": support,
                "pressure_score": pressure,
            },
            normalized_value=f"{day_element}:strength:{strength}",
            evidence_refs=[birth_input.birth_input_id, f"material:{reading_id}:bazi:chart:day_master", f"material:{reading_id}:bazi:chart:pillars"],
            knowledge_refs=["bazi.element_generation", "bazi.element_control"],
            rule_refs=["bazi.material_engine.day_master_strength"],
            confidence=0.62,
        ),
        MingliMaterial(
            material_id=f"material:{reading_id}:bazi:root_strength",
            reading_id=reading_id,
            source_engine=SourceEngine.BAZI,
            material_type=MaterialType.BAZI_ROOT_STRENGTH,
            topic=Topic.STRUCTURE,
            raw_value={
                "day_stem": day_stem,
                "day_element": day_element,
                "has_root": bool(root_sources),
                "root_sources": root_sources,
            },
            normalized_value="rooted" if root_sources else "unrooted",
            evidence_refs=[birth_input.birth_input_id, f"material:{reading_id}:bazi:hidden_stems"],
            knowledge_refs=["bazi.hidden_stems"],
            rule_refs=["bazi.material_engine.root_strength"],
            confidence=0.7,
        ),
    ]


def _branch_relation_materials(*, reading_id: str, birth_input: BirthInputCanonical, pillars: dict[str, str]) -> list[MingliMaterial]:
    branches = [(slot, pillar[1]) for slot, pillar in pillars.items()]
    relations: list[dict[str, str]] = []
    for (slot_a, branch_a), (slot_b, branch_b) in combinations(branches, 2):
        pair = frozenset((branch_a, branch_b))
        if pair in SIX_CLASH:
            relations.append({"type": "clash", "slot_a": slot_a, "branch_a": branch_a, "slot_b": slot_b, "branch_b": branch_b})
        if pair in SIX_HARMONY:
            relations.append({"type": "harmony", "slot_a": slot_a, "branch_a": branch_a, "slot_b": slot_b, "branch_b": branch_b})
    return [
        MingliMaterial(
            material_id=f"material:{reading_id}:bazi:branch_relations",
            reading_id=reading_id,
            source_engine=SourceEngine.BAZI,
            material_type=MaterialType.BAZI_COMBINATION,
            topic=Topic.STRUCTURE,
            raw_value={"relations": relations},
            normalized_value=";".join(f"{row['type']}:{row['branch_a']}{row['branch_b']}" for row in relations) or "none",
            evidence_refs=[birth_input.birth_input_id, f"material:{reading_id}:bazi:chart:pillars"],
            knowledge_refs=["bazi.six_clash", "bazi.six_harmony"],
            rule_refs=["bazi.material_engine.branch_relations"],
            confidence=0.68,
        )
    ]


def resolve_ten_god(*, day_stem: str, other_stem: str) -> str:
    day_element = STEM_ELEMENTS.get(day_stem, "")
    other_element = STEM_ELEMENTS.get(other_stem, "")
    same_polarity = STEM_POLARITY.get(day_stem) == STEM_POLARITY.get(other_stem)
    if not day_element or not other_element:
        return "unknown"
    if day_element == other_element:
        return "bi_jian" if same_polarity else "jie_cai"
    if GENERATES.get(day_element) == other_element:
        return "shi_shen" if same_polarity else "shang_guan"
    if GENERATES.get(other_element) == day_element:
        return "pian_yin" if same_polarity else "zheng_yin"
    if CONTROLS.get(day_element) == other_element:
        return "pian_cai" if same_polarity else "zheng_cai"
    if CONTROLS.get(other_element) == day_element:
        return "qi_sha" if same_polarity else "zheng_guan"
    return "unknown"


def _generating_element(element: str) -> str:
    for source, target in GENERATES.items():
        if target == element:
            return source
    return ""


def _has_root(*, day_stem: str, pillars: dict[str, str]) -> bool:
    return bool(_root_sources(day_stem=day_stem, pillars=pillars))


def _root_sources(*, day_stem: str, pillars: dict[str, str]) -> list[dict[str, str]]:
    """Return branches whose hidden stems share the day master's element.

    Rooting is an element-level relation. Requiring the exact same heavenly stem
    incorrectly marks cases such as 丙坐午 or 丁坐巳 as rootless.
    """

    day_element = STEM_ELEMENTS.get(day_stem, "")
    if not day_element:
        return []
    sources: list[dict[str, str]] = []
    for slot, pillar in pillars.items():
        branch = pillar[1]
        matching = [stem for stem in HIDDEN_STEMS.get(branch, []) if STEM_ELEMENTS.get(stem) == day_element]
        if matching:
            sources.append({"slot": slot, "branch": branch, "hidden_stems": "".join(matching)})
    return sources


def _store(*, reading_id: str, materials: list[MingliMaterial]) -> UnifiedMingliMaterialStore:
    by_engine: dict[str, list[str]] = {}
    by_type: dict[str, list[str]] = {}
    for material in materials:
        by_engine.setdefault(material.source_engine.value, []).append(material.material_id)
        by_type.setdefault(material.material_type.value, []).append(material.material_id)
    return UnifiedMingliMaterialStore(
        store_id=f"material_store:{reading_id}",
        reading_id=reading_id,
        materials=materials,
        material_count=len(materials),
        material_ids_by_engine=by_engine,
        material_ids_by_type=by_type,
    )
