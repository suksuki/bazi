from __future__ import annotations

from core.contracts import BirthInputCanonical, CalendarType, Gender, Topic
from core.engines.ziwei import (
    build_ziwei_dynamic_evidence_bundle,
    build_ziwei_material_bundle_from_birth_input,
    build_ziwei_plate_from_birth_input,
)


def _birth_input() -> BirthInputCanonical:
    return BirthInputCanonical(
        birth_input_id="birth.v50.ziwei.dynamic.001",
        name="ziwei_dynamic_case",
        gender=Gender.MALE,
        calendar_type=CalendarType.SOLAR,
        birth_date="1988-05-12",
        birth_time="09:30",
        birth_location="Shanghai",
        timezone="Asia/Shanghai",
        year_pillar="戊辰",
        month_pillar="丙巳",
        day_pillar="甲寅",
        hour_pillar="辛巳",
        input_quality="explicit_pillars",
    )


def test_v50_ziwei_chart_builder_generates_base_plate_from_birth_input() -> None:
    plate = build_ziwei_plate_from_birth_input(birth_input=_birth_input(), analysis_year=2026)

    assert plate.source == "iztro_verified_chart_bridge_v1"
    assert plate.calculator == "iztro@2.5.8"
    assert plate.input_quality == "blocked_source_conflict"
    assert plate.reasoning_ready is False
    assert "ziwei_bazi_pillar_mismatch" in plate.warnings
    assert plate.birth_input_id == "birth.v50.ziwei.dynamic.001"
    assert len(plate.palaces) == 12
    assert plate.life_palace
    assert plate.body_palace
    assert plate.decade_palace
    assert plate.annual_palace
    assert set(plate.four_transformations) == {"禄", "权", "科", "忌"}

    major_stars = [star for palace in plate.palaces.values() for star in palace.major_stars]
    support_stars = [star for palace in plate.palaces.values() for star in palace.support_stars]
    malefic_stars = [star for palace in plate.palaces.values() for star in palace.malefic_stars]
    assert len(set(major_stars)) == 14
    assert {"左辅", "右弼", "文昌", "文曲"}.issubset(set(support_stars))
    assert {"擎羊", "陀罗", "火星", "铃星"}.issubset(set(malefic_stars))


def test_v50_ziwei_material_bundle_from_birth_has_required_refs_without_judgment() -> None:
    bundle = build_ziwei_material_bundle_from_birth_input(
        reading_id="reading.v50.ziwei.dynamic.bundle",
        birth_input=_birth_input(),
        topic=Topic.OVERVIEW,
        analysis_year=2026,
    )

    assert bundle.generated_from_birth_input is True
    assert bundle.creates_judgment is False
    assert bundle.llm_used is False
    assert bundle.material_store.material_count >= 5
    assert bundle.palace_refs
    assert bundle.star_refs
    assert bundle.transformation_refs
    assert bundle.cycle_refs
    assert bundle.plate_input.source == "iztro_verified_chart_bridge_v1"


def test_v50_ziwei_dynamic_evidence_outputs_five_topic_activations_with_required_refs() -> None:
    material_bundle = build_ziwei_material_bundle_from_birth_input(
        reading_id="reading.v50.ziwei.dynamic.evidence",
        birth_input=_birth_input(),
        topic=Topic.OVERVIEW,
        analysis_year=2026,
    )
    evidence_bundle = build_ziwei_dynamic_evidence_bundle(material_bundle=material_bundle)

    assert evidence_bundle.creates_judgment is False
    assert evidence_bundle.llm_used is False
    assert evidence_bundle.evidence_count == 5
    assert {item.evidence_type for item in evidence_bundle.evidence_items} == {
        "ziwei_career_timing_activation",
        "ziwei_wealth_timing_activation",
        "ziwei_relationship_timing_activation",
        "ziwei_health_timing_activation",
        "ziwei_migration_timing_activation",
    }
    for item in evidence_bundle.evidence_items:
        assert item.palace_refs
        assert item.star_refs
        assert item.transformation_refs
        assert item.cycle_refs
        assert item.material_refs
        assert item.creates_judgment is False
        assert item.llm_used is False

