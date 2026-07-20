from __future__ import annotations

from core.contracts import BirthInputCanonical, CalendarType, Gender, MaterialType
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store, resolve_ten_god


def _birth_with_pillars() -> BirthInputCanonical:
    return BirthInputCanonical(
        birth_input_id="birth.v50.bazi.001",
        name="case001",
        gender=Gender.MALE,
        calendar_type=CalendarType.SOLAR,
        birth_date="1988-05-12",
        birth_time="09:30",
        birth_location="Shanghai",
        timezone="Asia/Shanghai",
        year_pillar="戊辰",
        month_pillar="丁巳",
        day_pillar="甲寅",
        hour_pillar="己巳",
        input_quality="explicit_pillars",
    )


def test_v50_calendar_normalization_resolves_hour_branch_without_chart_judgment() -> None:
    birth = _birth_with_pillars()
    calendar = normalize_birth_input(birth)

    assert calendar.hour_branch == "巳"
    assert calendar.confidence > 0.7
    assert "pillars" not in calendar.missing_fields
    assert calendar.boundary == "calendar_normalization_is_deterministic_and_does_not_create_judgment"


def test_v50_ten_god_resolution_is_deterministic_material_logic() -> None:
    assert resolve_ten_god(day_stem="甲", other_stem="戊") == "pian_cai"
    assert resolve_ten_god(day_stem="甲", other_stem="己") == "zheng_cai"
    assert resolve_ten_god(day_stem="甲", other_stem="丙") == "shi_shen"
    assert resolve_ten_god(day_stem="甲", other_stem="辛") == "zheng_guan"


def test_v50_bazi_material_engine_outputs_materials_only_from_explicit_pillars() -> None:
    birth = _birth_with_pillars()
    calendar = normalize_birth_input(birth)
    store = build_bazi_material_store(
        reading_id="reading.v50.bazi.001",
        birth_input=birth,
        calendar=calendar,
    )

    assert store.material_count >= 8
    assert "bazi" in store.material_ids_by_engine
    material_types = {material.material_type for material in store.materials}
    assert MaterialType.BAZI_CHART_FACT in material_types
    assert MaterialType.BAZI_TEN_GOD in material_types
    assert MaterialType.BAZI_HIDDEN_STEM in material_types
    assert MaterialType.BAZI_STRENGTH in material_types
    assert MaterialType.BAZI_ROOT_STRENGTH in material_types
    assert MaterialType.BAZI_COMBINATION in material_types

    for material in store.materials:
        assert material.verdict_authority is False
        assert material.llm_decision_authority is False
        assert material.evidence_refs


def test_v50_root_strength_uses_element_level_hidden_stem_roots() -> None:
    birth = _birth_with_pillars().model_copy(update={
        "birth_input_id": "birth.v50.bazi.fire-root",
        "year_pillar": "壬辰",
        "month_pillar": "戊申",
        "day_pillar": "丙午",
        "hour_pillar": "丁丑",
    })
    store = build_bazi_material_store(
        reading_id="reading.v50.bazi.fire-root",
        birth_input=birth,
        calendar=normalize_birth_input(birth),
    )

    root = next(material for material in store.materials if material.material_type == MaterialType.BAZI_ROOT_STRENGTH)

    assert root.raw_value["has_root"] is True
    assert root.raw_value["root_sources"] == [{"slot": "day", "branch": "午", "hidden_stems": "丁"}]
    assert root.normalized_value == "rooted"


def test_v50_bazi_material_engine_does_not_invent_missing_pillars() -> None:
    birth = BirthInputCanonical(
        birth_input_id="birth.v50.bazi.missing",
        gender=Gender.FEMALE,
        calendar_type=CalendarType.SOLAR,
        birth_date="1990-01-01",
        birth_time="子时",
        timezone="Asia/Shanghai",
    )
    calendar = normalize_birth_input(birth)
    store = build_bazi_material_store(
        reading_id="reading.v50.bazi.missing",
        birth_input=birth,
        calendar=calendar,
    )

    assert "pillars" in calendar.missing_fields
    assert store.material_count == 0
