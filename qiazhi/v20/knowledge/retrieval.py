from __future__ import annotations

from v20.features.schema import FeatureLayer
from v20.knowledge.loader import default_knowledge_units
from v20.knowledge.schema import KnowledgeRef, KnowledgeRetrievalReport, KnowledgeUnit

KNOWLEDGE_RETRIEVAL_VERSION = "v20.knowledge_retrieval.v1"


def retrieve_knowledge_refs(feature_layer: FeatureLayer) -> tuple[KnowledgeRef, ...]:
    return retrieve_knowledge(feature_layer).refs


def retrieve_knowledge(
    feature_layer: FeatureLayer,
    *,
    units: tuple[KnowledgeUnit, ...] | None = None,
    requested_domains: tuple[str, ...] = (),
) -> KnowledgeRetrievalReport:
    domains = {feature.domain for feature in feature_layer.features}
    domains.update(requested_domains)
    feature_ids = {feature.feature_id for feature in feature_layer.features}
    selected: list[KnowledgeRef] = []
    for unit in units or default_knowledge_units():
        if unit.status != "reviewed":
            continue
        if unit.domain not in domains and not _hook_matches(unit, feature_ids):
            continue
        selected.append(
            KnowledgeRef(
                knowledge_id=unit.knowledge_id,
                title=unit.title,
                domain=unit.domain,
                evidence_template=unit.evidence_template,
                boundary=unit.boundary,
                source_refs=unit.source_refs,
                reviewed=True,
            )
        )
    return KnowledgeRetrievalReport(version=KNOWLEDGE_RETRIEVAL_VERSION, refs=tuple(selected))


def _hook_matches(unit: KnowledgeUnit, feature_ids: set[str]) -> bool:
    for hook in unit.feature_hooks:
        if any(feature_id.startswith(hook) for feature_id in feature_ids):
            return True
    return False
