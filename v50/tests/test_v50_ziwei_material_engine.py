from __future__ import annotations

from core.contracts import MaterialType, Topic, ZiweiPalaceInput, ZiweiPlateInput
from core.engines.ziwei import build_ziwei_material_store


def _explicit_ziwei_plate() -> ZiweiPlateInput:
    return ZiweiPlateInput(
        plate_input_id="ziwei.plate.v50.001",
        birth_input_id="birth.v50.ziwei.001",
        life_palace="命宫",
        body_palace="身宫",
        palaces={
            "命宫": ZiweiPalaceInput(palace_name="命宫", branch="寅", major_stars=["紫微", "天府"]),
            "身宫": ZiweiPalaceInput(palace_name="身宫", branch="午", major_stars=["太阳"]),
            "官禄宫": ZiweiPalaceInput(palace_name="官禄宫", branch="戌", major_stars=["武曲", "七杀"], support_stars=["左辅"]),
            "财帛宫": ZiweiPalaceInput(palace_name="财帛宫", branch="午", major_stars=["太阳"], transformations={"权": "太阳"}),
            "夫妻宫": ZiweiPalaceInput(palace_name="夫妻宫", branch="子", major_stars=["天同"]),
            "疾厄宫": ZiweiPalaceInput(palace_name="疾厄宫", branch="辰", major_stars=["廉贞"], malefic_stars=["擎羊"]),
            "迁移宫": ZiweiPalaceInput(palace_name="迁移宫", branch="申", major_stars=["天机"]),
        },
        four_transformations={"禄": "武曲", "权": "太阳", "科": "天梁", "忌": "巨门"},
        decade_palace="官禄宫",
        annual_palace="财帛宫",
        decade_label="甲申大限",
        annual_label="丙午流年",
        input_quality="fixture_explicit_plate",
    )


def test_v50_ziwei_material_engine_outputs_dynamic_materials_only() -> None:
    store = build_ziwei_material_store(
        reading_id="reading.v50.ziwei.001",
        plate_input=_explicit_ziwei_plate(),
        topic=Topic.WEALTH,
    )

    assert store.material_count >= 5
    assert "ziwei" in store.material_ids_by_engine
    material_types = {material.material_type for material in store.materials}
    assert MaterialType.ZIWEI_PALACE in material_types
    assert MaterialType.ZIWEI_STAR in material_types
    assert MaterialType.ZIWEI_FOUR_TRANSFORMATION in material_types
    assert MaterialType.ZIWEI_TIME_WINDOW in material_types
    assert MaterialType.ZIWEI_PALACE_RELATION in material_types

    for material in store.materials:
        assert material.source_engine.value == "ziwei"
        assert material.verdict_authority is False
        assert material.llm_decision_authority is False
        assert material.evidence_refs
        assert material.boundary == "material_is_engine_output_not_judgment"


def test_v50_ziwei_material_engine_does_not_invent_missing_plate() -> None:
    plate = ZiweiPlateInput(
        plate_input_id="ziwei.plate.v50.empty",
        birth_input_id="birth.v50.ziwei.empty",
        input_quality="empty_plate",
    )
    store = build_ziwei_material_store(
        reading_id="reading.v50.ziwei.empty",
        plate_input=plate,
        topic=Topic.CAREER,
    )

    assert store.material_count == 0
    assert store.material_ids_by_engine == {}
