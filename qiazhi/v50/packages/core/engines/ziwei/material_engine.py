from __future__ import annotations

from core.contracts.base import SourceEngine, Topic
from core.contracts.birth import BirthInputCanonical
from core.contracts.material import MaterialType, MingliMaterial, UnifiedMingliMaterialStore
from core.contracts.ziwei import ZiweiMaterialBundle, ZiweiPalaceInput, ZiweiPlateInput
from core.engines.ziwei.chart_builder import build_ziwei_plate_from_birth_input
from core.engines.ziwei.knowledge import FOUR_TRANSFORMATION_MEANINGS, TOPIC_PALACE_NAMES, canonical_palace_name


def build_ziwei_material_store(
    *,
    reading_id: str,
    plate_input: ZiweiPlateInput,
    topic: Topic = Topic.OVERVIEW,
) -> UnifiedMingliMaterialStore:
    materials: list[MingliMaterial] = []
    if not _has_plate_material(plate_input):
        return _store(reading_id=reading_id, materials=materials)
    materials.extend(_identity_palace_materials(reading_id=reading_id, plate_input=plate_input, topic=topic))
    materials.extend(_topic_palace_materials(reading_id=reading_id, plate_input=plate_input, topic=topic))
    materials.extend(_star_materials(reading_id=reading_id, plate_input=plate_input, topic=topic))
    materials.extend(_four_transformation_materials(reading_id=reading_id, plate_input=plate_input, topic=topic))
    materials.extend(_time_window_materials(reading_id=reading_id, plate_input=plate_input, topic=topic))
    materials.extend(_palace_relation_materials(reading_id=reading_id, plate_input=plate_input, topic=topic))
    return _store(reading_id=reading_id, materials=materials)


def build_ziwei_material_bundle_from_birth_input(
    *,
    reading_id: str,
    birth_input: BirthInputCanonical,
    topic: Topic = Topic.OVERVIEW,
    analysis_year: int | None = None,
) -> ZiweiMaterialBundle:
    plate_input = build_ziwei_plate_from_birth_input(birth_input=birth_input, analysis_year=analysis_year)
    material_store = build_ziwei_material_store(reading_id=reading_id, plate_input=plate_input, topic=topic)
    return ZiweiMaterialBundle(
        bundle_id=f"ziwei_material_bundle:{reading_id}:{topic.value}",
        reading_id=reading_id,
        birth_input_id=birth_input.birth_input_id,
        plate_input=plate_input,
        material_store=material_store,
        palace_refs=_material_refs_by_type(material_store, MaterialType.ZIWEI_PALACE),
        star_refs=_material_refs_by_type(material_store, MaterialType.ZIWEI_STAR),
        transformation_refs=_material_refs_by_type(material_store, MaterialType.ZIWEI_FOUR_TRANSFORMATION),
        cycle_refs=_material_refs_by_type(material_store, MaterialType.ZIWEI_TIME_WINDOW),
        generated_from_birth_input=True,
    )


def _has_plate_material(plate_input: ZiweiPlateInput) -> bool:
    return any(
        [
            plate_input.life_palace.strip(),
            plate_input.body_palace.strip(),
            plate_input.palaces,
            plate_input.four_transformations,
            plate_input.decade_palace.strip(),
            plate_input.annual_palace.strip(),
        ]
    )


def _identity_palace_materials(*, reading_id: str, plate_input: ZiweiPlateInput, topic: Topic) -> list[MingliMaterial]:
    rows = []
    if plate_input.life_palace.strip():
        rows.append({"role": "life_palace", "palace": canonical_palace_name(plate_input.life_palace)})
    if plate_input.body_palace.strip():
        rows.append({"role": "body_palace", "palace": canonical_palace_name(plate_input.body_palace)})
    if not rows:
        return []
    return [
        MingliMaterial(
            material_id=f"material:{reading_id}:ziwei:identity_palaces",
            reading_id=reading_id,
            source_engine=SourceEngine.ZIWEI,
            material_type=MaterialType.ZIWEI_PALACE,
            topic=topic,
            raw_value={"palaces": rows},
            normalized_value=";".join(f"{row['role']}:{row['palace']}" for row in rows),
            evidence_refs=[plate_input.plate_input_id],
            knowledge_refs=["ziwei.palace.identity"],
            rule_refs=["ziwei.material_engine.explicit_identity_palaces"],
            confidence=0.86,
        )
    ]


def _topic_palace_materials(*, reading_id: str, plate_input: ZiweiPlateInput, topic: Topic) -> list[MingliMaterial]:
    topic_palaces = TOPIC_PALACE_NAMES.get(topic, TOPIC_PALACE_NAMES[Topic.UNKNOWN])
    palaces = []
    for expected in topic_palaces:
        palace = _find_palace(plate_input.palaces, expected)
        if palace is not None:
            palaces.append(_palace_payload(palace))
    if not palaces:
        return []
    return [
        MingliMaterial(
            material_id=f"material:{reading_id}:ziwei:topic_palaces:{topic.value}",
            reading_id=reading_id,
            source_engine=SourceEngine.ZIWEI,
            material_type=MaterialType.ZIWEI_PALACE,
            topic=topic,
            raw_value={"topic": topic.value, "palaces": palaces},
            normalized_value=";".join(f"{row['palace_name']}:{row['branch']}" for row in palaces),
            evidence_refs=[plate_input.plate_input_id],
            knowledge_refs=["ziwei.topic_palace_names"],
            rule_refs=["ziwei.material_engine.topic_palace_lookup"],
            confidence=0.74,
        )
    ]


def _star_materials(*, reading_id: str, plate_input: ZiweiPlateInput, topic: Topic) -> list[MingliMaterial]:
    rows = []
    for palace in _selected_palaces(plate_input=plate_input, topic=topic):
        stars = [*palace.major_stars, *palace.support_stars, *palace.malefic_stars]
        if stars:
            rows.append(
                {
                    "palace_name": canonical_palace_name(palace.palace_name),
                    "major_stars": palace.major_stars,
                    "support_stars": palace.support_stars,
                    "malefic_stars": palace.malefic_stars,
                }
            )
    if not rows:
        return []
    return [
        MingliMaterial(
            material_id=f"material:{reading_id}:ziwei:stars:{topic.value}",
            reading_id=reading_id,
            source_engine=SourceEngine.ZIWEI,
            material_type=MaterialType.ZIWEI_STAR,
            topic=topic,
            raw_value={"topic": topic.value, "star_rows": rows},
            normalized_value=";".join(f"{row['palace_name']}:{','.join(row['major_stars'])}" for row in rows),
            evidence_refs=[plate_input.plate_input_id, f"material:{reading_id}:ziwei:topic_palaces:{topic.value}"],
            knowledge_refs=["ziwei.stars.by_palace"],
            rule_refs=["ziwei.material_engine.star_collection"],
            confidence=0.72,
        )
    ]


def _four_transformation_materials(*, reading_id: str, plate_input: ZiweiPlateInput, topic: Topic) -> list[MingliMaterial]:
    rows = []
    for transformation, star in plate_input.four_transformations.items():
        if transformation.strip() and star.strip():
            rows.append(
                {
                    "transformation": transformation,
                    "star": star,
                    "meaning": FOUR_TRANSFORMATION_MEANINGS.get(transformation, "unknown"),
                }
            )
    if not rows:
        return []
    return [
        MingliMaterial(
            material_id=f"material:{reading_id}:ziwei:four_transformations",
            reading_id=reading_id,
            source_engine=SourceEngine.ZIWEI,
            material_type=MaterialType.ZIWEI_FOUR_TRANSFORMATION,
            topic=topic,
            raw_value={"transformations": rows},
            normalized_value=";".join(f"{row['transformation']}:{row['star']}" for row in rows),
            evidence_refs=[plate_input.plate_input_id],
            knowledge_refs=["ziwei.four_transformations"],
            rule_refs=["ziwei.material_engine.four_transformation_lookup"],
            confidence=0.8,
        )
    ]


def _time_window_materials(*, reading_id: str, plate_input: ZiweiPlateInput, topic: Topic) -> list[MingliMaterial]:
    rows = []
    if plate_input.decade_palace.strip() or plate_input.decade_label.strip():
        rows.append({"type": "decade", "palace": canonical_palace_name(plate_input.decade_palace), "label": plate_input.decade_label})
    if plate_input.annual_palace.strip() or plate_input.annual_label.strip():
        rows.append({"type": "annual", "palace": canonical_palace_name(plate_input.annual_palace), "label": plate_input.annual_label})
    if not rows:
        return []
    return [
        MingliMaterial(
            material_id=f"material:{reading_id}:ziwei:time_windows",
            reading_id=reading_id,
            source_engine=SourceEngine.ZIWEI,
            material_type=MaterialType.ZIWEI_TIME_WINDOW,
            topic=topic,
            raw_value={"time_windows": rows},
            normalized_value=";".join(f"{row['type']}:{row['palace']}:{row['label']}" for row in rows),
            evidence_refs=[plate_input.plate_input_id],
            knowledge_refs=["ziwei.decade_luck", "ziwei.annual_luck"],
            rule_refs=["ziwei.material_engine.time_window_collection"],
            confidence=0.7,
        )
    ]


def _palace_relation_materials(*, reading_id: str, plate_input: ZiweiPlateInput, topic: Topic) -> list[MingliMaterial]:
    selected = [canonical_palace_name(palace.palace_name) for palace in _selected_palaces(plate_input=plate_input, topic=topic)]
    if len(selected) < 2:
        return []
    return [
        MingliMaterial(
            material_id=f"material:{reading_id}:ziwei:palace_relations:{topic.value}",
            reading_id=reading_id,
            source_engine=SourceEngine.ZIWEI,
            material_type=MaterialType.ZIWEI_PALACE_RELATION,
            topic=topic,
            raw_value={"topic": topic.value, "focus_palaces": selected, "relation_type": "topic_domain_cluster"},
            normalized_value="topic_domain_cluster:" + ",".join(selected),
            evidence_refs=[plate_input.plate_input_id, f"material:{reading_id}:ziwei:topic_palaces:{topic.value}"],
            knowledge_refs=["ziwei.topic_palace_names"],
            rule_refs=["ziwei.material_engine.topic_domain_relation"],
            confidence=0.62,
        )
    ]


def _find_palace(palaces: dict[str, ZiweiPalaceInput], expected: str) -> ZiweiPalaceInput | None:
    expected_name = canonical_palace_name(expected)
    for key, palace in palaces.items():
        if canonical_palace_name(key) == expected_name or canonical_palace_name(palace.palace_name) == expected_name:
            return palace
    return None


def _selected_palaces(*, plate_input: ZiweiPlateInput, topic: Topic) -> list[ZiweiPalaceInput]:
    selected = []
    for expected in TOPIC_PALACE_NAMES.get(topic, TOPIC_PALACE_NAMES[Topic.UNKNOWN]):
        palace = _find_palace(plate_input.palaces, expected)
        if palace is not None:
            selected.append(palace)
    if selected:
        return selected
    return list(plate_input.palaces.values())


def _palace_payload(palace: ZiweiPalaceInput) -> dict[str, object]:
    return {
        "palace_name": canonical_palace_name(palace.palace_name),
        "branch": palace.branch,
        "major_stars": palace.major_stars,
        "support_stars": palace.support_stars,
        "malefic_stars": palace.malefic_stars,
        "transformations": palace.transformations,
    }


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


def _material_refs_by_type(material_store: UnifiedMingliMaterialStore, material_type: MaterialType) -> list[str]:
    return [material.material_id for material in material_store.materials if material.material_type == material_type]
