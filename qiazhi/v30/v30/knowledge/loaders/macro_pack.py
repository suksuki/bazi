from __future__ import annotations

from pydantic import Field

from v30.contracts import FeatureEvidence, V30Model
from v30.knowledge.packs import MACRO_DIMENSIONS, MULTIDIMENSIONAL_TAXONOMY_VERSION, MacroKnowledgeDimension


CORE_MACRO_PACK_ID = "v30.knowledge.pack.core_macro_zh_v1"
CORE_MACRO_PACK_VERSION = "2026-05-21"


class MacroKnowledgePackItem(V30Model):
    item_id: str
    pack_id: str = CORE_MACRO_PACK_ID
    pack_version: str = CORE_MACRO_PACK_VERSION
    taxonomy_version: str = MULTIDIMENSIONAL_TAXONOMY_VERSION
    dimension_id: str
    domain: str
    label_zh: str
    scope: str
    evidence_domains: list[str] = Field(default_factory=list)
    structure_hooks: list[str] = Field(default_factory=list)
    question_hooks: list[str] = Field(default_factory=list)
    portrait_dimensions: list[str] = Field(default_factory=list)
    training_tags: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)
    source_hints: list[str] = Field(default_factory=list)


class MacroKnowledgePack(V30Model):
    pack_id: str = CORE_MACRO_PACK_ID
    pack_version: str = CORE_MACRO_PACK_VERSION
    taxonomy_version: str = MULTIDIMENSIONAL_TAXONOMY_VERSION
    items: list[MacroKnowledgePackItem]
    source_policy: str = "converted_source_material_v30_owned_runtime_pack"
    runtime_rule: str = "Runtime consumes this V30 pack only; V20 assets are source hints, not imports."


class MacroDimensionSignal(V30Model):
    signal_id: str
    pack_id: str = CORE_MACRO_PACK_ID
    pack_version: str = CORE_MACRO_PACK_VERSION
    dimension_id: str
    domain: str
    label_zh: str
    matched_evidence_domains: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    question_hooks: list[str] = Field(default_factory=list)
    structure_hooks: list[str] = Field(default_factory=list)
    portrait_dimensions: list[str] = Field(default_factory=list)
    training_tags: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)
    score: float
    boundary: str


def load_core_macro_pack() -> MacroKnowledgePack:
    return MacroKnowledgePack(items=[_item_from_dimension(row) for row in MACRO_DIMENSIONS])


def summarize_core_macro_pack(
    pack: MacroKnowledgePack | None = None,
    evidence: list[FeatureEvidence] | None = None,
) -> dict[str, object]:
    pack = pack or load_core_macro_pack()
    evidence_domains = {row.domain for row in evidence or []}
    active_items = [
        item
        for item in pack.items
        if not evidence_domains or evidence_domains.intersection(item.evidence_domains)
    ]
    return {
        "pack_id": pack.pack_id,
        "pack_version": pack.pack_version,
        "taxonomy_version": pack.taxonomy_version,
        "item_count": len(pack.items),
        "active_item_count": len(active_items),
        "domains": sorted({item.domain for item in pack.items}),
        "active_domains": sorted({item.domain for item in active_items}),
        "question_hooks": sorted({hook for item in active_items for hook in item.question_hooks}),
        "structure_hooks": sorted({hook for item in active_items for hook in item.structure_hooks}),
        "portrait_dimensions": sorted({row for item in active_items for row in item.portrait_dimensions}),
        "training_tags": sorted({row for item in active_items for row in item.training_tags}),
        "boundary_count": sum(len(item.boundaries) for item in active_items),
        "runtime_rule": pack.runtime_rule,
    }


def build_macro_dimension_signals(
    evidence: list[FeatureEvidence],
    pack: MacroKnowledgePack | None = None,
) -> list[MacroDimensionSignal]:
    pack = pack or load_core_macro_pack()
    evidence_by_domain: dict[str, list[FeatureEvidence]] = {}
    for row in evidence:
        evidence_by_domain.setdefault(row.domain, []).append(row)
    signals: list[MacroDimensionSignal] = []
    for item in pack.items:
        matched_domains = sorted(set(item.evidence_domains) & set(evidence_by_domain))
        if not matched_domains:
            continue
        matched_evidence = [
            row
            for domain in matched_domains
            for row in evidence_by_domain.get(domain, [])
        ]
        score = min(1.0, 0.42 + 0.08 * len(matched_domains) + 0.015 * len(matched_evidence))
        signals.append(
            MacroDimensionSignal(
                signal_id=f"{item.item_id}:signal",
                dimension_id=item.dimension_id,
                domain=item.domain,
                label_zh=item.label_zh,
                matched_evidence_domains=matched_domains,
                evidence_ids=[row.evidence_id for row in matched_evidence],
                question_hooks=item.question_hooks,
                structure_hooks=item.structure_hooks,
                portrait_dimensions=item.portrait_dimensions,
                training_tags=item.training_tags,
                boundaries=item.boundaries,
                score=round(score, 3),
                boundary="macro_dimension_signal_is_context_projection_not_verdict",
            )
        )
    return sorted(signals, key=lambda row: (-row.score, row.domain))


def _item_from_dimension(dimension: MacroKnowledgeDimension) -> MacroKnowledgePackItem:
    return MacroKnowledgePackItem(
        item_id=f"{CORE_MACRO_PACK_ID}:{dimension.domain}",
        dimension_id=dimension.dimension_id,
        domain=dimension.domain,
        label_zh=dimension.label_zh,
        scope=dimension.scope,
        evidence_domains=dimension.evidence_domains,
        structure_hooks=dimension.structure_hooks,
        question_hooks=dimension.question_hooks,
        portrait_dimensions=dimension.portrait_dimensions,
        training_tags=dimension.training_tags,
        boundaries=dimension.boundaries,
        source_hints=[*dimension.v20_source_hints, *dimension.public_source_hints],
    )
