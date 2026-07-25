from __future__ import annotations

from core.contracts.base import Topic
from core.contracts.material import MaterialType, MingliMaterial
from core.contracts.reasoning import FlowObservation, LocalizedClaimRef
from core.contracts.ziwei import ZiweiDynamicEvidence, ZiweiDynamicEvidenceBundle, ZiweiMaterialBundle
from core.engines.ziwei.knowledge import TOPIC_PALACE_NAMES, canonical_palace_name


DYNAMIC_TOPICS = (Topic.CAREER, Topic.WEALTH, Topic.RELATIONSHIP, Topic.HEALTH, Topic.MIGRATION)


def build_ziwei_dynamic_evidence_bundle(
    *,
    material_bundle: ZiweiMaterialBundle,
    topics: tuple[Topic, ...] = DYNAMIC_TOPICS,
    include_pressure: bool = False,
) -> ZiweiDynamicEvidenceBundle:
    items: list[ZiweiDynamicEvidence] = []
    for topic in topics:
        if (evidence := _topic_evidence(material_bundle=material_bundle, topic=topic)) is not None:
            items.append(evidence)
        if include_pressure and (pressure := _topic_pressure_evidence(material_bundle=material_bundle, topic=topic)) is not None:
            items.append(pressure)
    return ZiweiDynamicEvidenceBundle(
        bundle_id=f"ziwei_dynamic_evidence_bundle:{material_bundle.reading_id}",
        reading_id=material_bundle.reading_id,
        evidence_items=items,
        evidence_count=len(items),
    )


def build_ziwei_dynamic_evidence_flows(evidence_bundle: ZiweiDynamicEvidenceBundle) -> list[FlowObservation]:
    return [
        FlowObservation(
            flow_id=f"flow:{item.reading_id}:{item.evidence_type}",
            reading_id=item.reading_id,
            flow_type=item.evidence_type,
            from_node=f"ziwei_topic:{item.topic.value}",
            to_node=_flow_to_node(item.evidence_type),
            claim=LocalizedClaimRef(
                raw_code=_flow_claim_code(item),
                label_key=f"{_flow_claim_code(item)}.label",
                message_key=f"{_flow_claim_code(item)}.message",
                display_params={
                    "topic": item.topic.value,
                    "palace_refs": item.palace_refs,
                    "star_refs": item.star_refs,
                    "transformation_refs": item.transformation_refs,
                    "cycle_refs": item.cycle_refs,
                },
            ),
            structure_refs=[*item.palace_refs, *item.star_refs, *item.transformation_refs, *item.cycle_refs],
            material_refs=item.material_refs,
            confidence=item.confidence,
        )
        for item in evidence_bundle.evidence_items
    ]


def _flow_claim_code(item: ZiweiDynamicEvidence) -> str:
    if item.evidence_type.endswith("_short_term_pressure"):
        return f"flow.ziwei.{item.topic.value}.short_term_pressure"
    return f"flow.ziwei.{item.topic.value}.timing_activation"


def _flow_to_node(evidence_type: str) -> str:
    if evidence_type.endswith("_short_term_pressure"):
        return "ziwei_short_term_pressure_window"
    return "ziwei_dynamic_time_window"


def _topic_evidence(*, material_bundle: ZiweiMaterialBundle, topic: Topic) -> ZiweiDynamicEvidence | None:
    materials = material_bundle.material_store.materials
    palace_refs = _topic_palace_refs(materials=materials, topic=topic) or material_bundle.palace_refs
    star_refs = _topic_star_refs(materials=materials, topic=topic) or material_bundle.star_refs
    transformation_refs = material_bundle.transformation_refs
    cycle_refs = material_bundle.cycle_refs
    if not palace_refs or not star_refs or not transformation_refs or not cycle_refs:
        return None
    material_refs = _unique([*palace_refs, *star_refs, *transformation_refs, *cycle_refs])
    return ZiweiDynamicEvidence(
        evidence_id=f"ziwei_dynamic_evidence:{material_bundle.reading_id}:{topic.value}",
        reading_id=material_bundle.reading_id,
        topic=topic,
        evidence_type=f"ziwei_{topic.value}_timing_activation",
        palace_refs=palace_refs,
        star_refs=star_refs,
        transformation_refs=transformation_refs,
        cycle_refs=cycle_refs,
        material_refs=material_refs,
        confidence=_confidence(materials=materials, refs=material_refs),
    )


def _topic_pressure_evidence(*, material_bundle: ZiweiMaterialBundle, topic: Topic) -> ZiweiDynamicEvidence | None:
    if not _topic_has_hua_ji_pressure(material_bundle=material_bundle, topic=topic):
        return None
    materials = material_bundle.material_store.materials
    palace_refs = _topic_palace_refs(materials=materials, topic=topic) or material_bundle.palace_refs
    star_refs = _topic_star_refs(materials=materials, topic=topic) or material_bundle.star_refs
    transformation_refs = material_bundle.transformation_refs
    cycle_refs = material_bundle.cycle_refs
    if not palace_refs or not star_refs or not transformation_refs or not cycle_refs:
        return None
    material_refs = _unique([*palace_refs, *star_refs, *transformation_refs, *cycle_refs])
    return ZiweiDynamicEvidence(
        evidence_id=f"ziwei_dynamic_evidence:{material_bundle.reading_id}:{topic.value}:short_term_pressure",
        reading_id=material_bundle.reading_id,
        topic=topic,
        evidence_type=f"ziwei_{topic.value}_short_term_pressure",
        palace_refs=palace_refs,
        star_refs=star_refs,
        transformation_refs=transformation_refs,
        cycle_refs=cycle_refs,
        material_refs=material_refs,
        confidence=round(_confidence(materials=materials, refs=material_refs) * 0.94, 3),
    )


def _topic_has_hua_ji_pressure(*, material_bundle: ZiweiMaterialBundle, topic: Topic) -> bool:
    focus_palaces = {canonical_palace_name(name) for name in TOPIC_PALACE_NAMES.get(topic, ())}
    if not focus_palaces:
        return False
    for palace in material_bundle.plate_input.palaces.values():
        if canonical_palace_name(palace.palace_name) not in focus_palaces:
            continue
        if "忌" in palace.transformations:
            return True
    return False


def _topic_palace_refs(*, materials: list[MingliMaterial], topic: Topic) -> list[str]:
    refs = [
        material.material_id
        for material in materials
        if material.material_type == MaterialType.ZIWEI_PALACE and material.topic == topic
    ]
    if refs:
        return refs
    focus_palaces = set(TOPIC_PALACE_NAMES.get(topic, ()))
    return [
        material.material_id
        for material in materials
        if material.material_type == MaterialType.ZIWEI_PALACE
        and any(
            isinstance(row, dict) and str(row.get("palace_name") or row.get("palace") or "") in focus_palaces
            for row in _rows(material)
        )
    ]


def _topic_star_refs(*, materials: list[MingliMaterial], topic: Topic) -> list[str]:
    return [
        material.material_id
        for material in materials
        if material.material_type == MaterialType.ZIWEI_STAR and material.topic == topic
    ]


def _rows(material: MingliMaterial) -> list[object]:
    raw = material.raw_value
    for key in ("palaces", "star_rows", "transformations", "time_windows"):
        value = raw.get(key)
        if isinstance(value, list):
            return value
    return []


def _confidence(*, materials: list[MingliMaterial], refs: list[str]) -> float:
    ref_set = set(refs)
    values = [material.confidence for material in materials if material.material_id in ref_set]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
