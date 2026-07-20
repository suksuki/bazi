from __future__ import annotations

from datetime import date

from core.contracts.birth import BirthInputCanonical
from core.contracts.ziwei import ZiweiPalaceInput, ZiweiPlateInput
from core.engines.ziwei.knowledge import canonical_palace_name
from core.engines.ziwei.iztro_bridge import calculate_iztro_plate


def build_ziwei_plate_from_birth_input(
    *,
    birth_input: BirthInputCanonical,
    analysis_year: int | None = None,
) -> ZiweiPlateInput:
    raw = calculate_iztro_plate(birth_input=birth_input, analysis_year=analysis_year)
    palaces: dict[str, ZiweiPalaceInput] = {}
    transformations: dict[str, str] = {}
    body_palace = ""
    for item in raw["palaces"]:
        name = canonical_palace_name(str(item["name"]))
        major = [str(star["name"]) for star in item.get("major_stars", [])]
        support = [
            str(star["name"])
            for star in item.get("minor_stars", [])
            if str(star.get("type") or "") not in {"tough", "malefic"}
        ]
        malefic = [
            str(star["name"])
            for star in item.get("minor_stars", [])
            if str(star.get("type") or "") in {"tough", "malefic"}
        ]
        palace_transformations: dict[str, str] = {}
        for star in [*item.get("major_stars", []), *item.get("minor_stars", [])]:
            mutagen = str(star.get("mutagen") or "")
            if mutagen:
                palace_transformations[mutagen] = str(star["name"])
                transformations[mutagen] = str(star["name"])
        palaces[name] = ZiweiPalaceInput(
            palace_name=name,
            branch=str(item.get("earthly_branch") or ""),
            major_stars=major,
            support_stars=support,
            malefic_stars=malefic,
            transformations=palace_transformations,
            notes=[f"长生十二神:{item.get('changsheng_12')}"] if item.get("changsheng_12") else [],
        )
        if item.get("is_body_palace"):
            body_palace = name

    horoscope = dict(raw.get("horoscope") or {})
    decade_palace = _active_horoscope_palace(raw["palaces"], horoscope.get("decadal"))
    annual_palace = _active_horoscope_palace(raw["palaces"], horoscope.get("yearly"))

    return ZiweiPlateInput(
        plate_input_id=f"ziwei.plate.iztro:{birth_input.birth_input_id}:{analysis_year or date.today().year}",
        birth_input_id=birth_input.birth_input_id,
        source="iztro_verified_chart_bridge_v1",
        life_palace="命宫",
        body_palace=body_palace,
        palaces=palaces,
        four_transformations=transformations,
        decade_palace=decade_palace,
        annual_palace=annual_palace,
        decade_label=f"{analysis_year or date.today().year} 大限",
        annual_label=f"{analysis_year or date.today().year} 流年",
        input_quality="verified_iztro" if raw["reasoning_ready"] else "blocked_source_conflict",
        calculator=str(raw["source"]),
        soul_star=str(raw.get("soul_star") or ""),
        body_star=str(raw.get("body_star") or ""),
        five_elements_class=str(raw.get("five_elements_class") or ""),
        horoscope=horoscope,
        reasoning_ready=bool(raw["reasoning_ready"]),
        warnings=list(raw["warnings"]),
    )


def _active_horoscope_palace(palaces: list[dict[str, object]], layer: object) -> str:
    if not isinstance(layer, dict):
        return ""
    names = layer.get("palaceNames")
    if not isinstance(names, list) or "命宫" not in names:
        return ""
    index = names.index("命宫")
    if index >= len(palaces):
        return ""
    return canonical_palace_name(str(palaces[index].get("name") or ""))
