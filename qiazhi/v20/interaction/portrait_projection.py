from __future__ import annotations

from v20.answer.measurement_policy import domain_label, feature_label, measurement_focus, measurement_stage
from v20.features.schema import BaziFeature
from v20.features.schema import FeatureLayer
from v20.interaction.portrait_schema import (
    PortraitAxis,
    PortraitItem,
    PortraitKnowledgeLink,
    PortraitProjection,
)
from v20.knowledge.retrieval import retrieve_knowledge
from v20.knowledge.schema import KnowledgeRef, KnowledgeRetrievalReport


def portrait_projection(
    feature_layer: FeatureLayer,
    knowledge_report: KnowledgeRetrievalReport | None = None,
) -> dict[str, object]:
    report = knowledge_report or retrieve_knowledge(feature_layer)
    projection = PortraitProjection(
        version="v20.portrait_projection.v2",
        status="ready" if feature_layer.features else "empty",
        role="bazi_feature_projection_and_calibration_surface_only",
        measurement_role="命理画像只投影已编译特征，知识库只提供语义边界和校准语境，不驱动结论。",
        axes=tuple(_profile_axes(feature_layer, report.refs)),
        items=tuple(_profile_items(feature_layer, report.refs)),
    )
    return projection.to_dict()


def _profile_axes(feature_layer: FeatureLayer, knowledge_refs: tuple[KnowledgeRef, ...]) -> list[PortraitAxis]:
    rows: dict[str, list[BaziFeature]] = {}
    for feature in feature_layer.features:
        rows.setdefault(feature.domain, []).append(feature)
    axes = [
        PortraitAxis(
            axis_id=f"portrait.axis.{domain}",
            domain=domain,
            label=domain_label(domain),
            measurement_stage=measurement_stage(domain),
            feature_ids=tuple(feature.feature_id for feature in features),
            feature_count=len(features),
            peak_confidence=max(feature.confidence for feature in features),
            calibration_state=_axis_calibration_state(features),
            knowledge_links=_knowledge_links_for_domain(knowledge_refs, domain),
            evidence_boundaries=_knowledge_boundaries_for_domain(knowledge_refs, domain),
            calibration_prompt=f"校准“{domain_label(domain)}”画像轴是否符合当前命理特征证据。",
        )
        for domain, features in rows.items()
    ]
    return sorted(axes, key=lambda row: (row.measurement_stage, row.label))


def _profile_items(feature_layer: FeatureLayer, knowledge_refs: tuple[KnowledgeRef, ...]) -> list[PortraitItem]:
    return [
        PortraitItem(
            feature_id=feature.feature_id,
            title=feature_label(feature),
            domain=feature.domain,
            measurement_topic=domain_label(feature.domain),
            measurement_stage=measurement_stage(feature.domain),
            measurement_focus=measurement_focus(feature),
            confidence=feature.confidence,
            calibration_state=feature.calibration_state,
            knowledge_links=_knowledge_links_for_domain(knowledge_refs, feature.domain),
        )
        for feature in feature_layer.features[:8]
    ]


def _axis_calibration_state(features: list[BaziFeature]) -> str:
    states = {feature.calibration_state for feature in features}
    if len(states) == 1:
        return next(iter(states))
    return "mixed_feature_calibration_states"


def _knowledge_links_for_domain(
    knowledge_refs: tuple[KnowledgeRef, ...],
    domain: str,
) -> tuple[PortraitKnowledgeLink, ...]:
    return tuple(
        PortraitKnowledgeLink(
            knowledge_id=ref.knowledge_id,
            title=ref.title,
            domain=ref.domain,
            boundary=ref.boundary,
            source_refs=ref.source_refs,
            reviewed=ref.reviewed,
        )
        for ref in knowledge_refs
        if ref.domain == domain and ref.reviewed
    )


def _knowledge_boundaries_for_domain(knowledge_refs: tuple[KnowledgeRef, ...], domain: str) -> tuple[str, ...]:
    boundaries = []
    for ref in knowledge_refs:
        if ref.domain == domain and ref.reviewed and ref.boundary:
            boundaries.append(ref.boundary)
    return tuple(boundaries[:3])
