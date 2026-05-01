from __future__ import annotations

from collections import Counter

from v20.knowledge.loader import default_knowledge_units
from v20.knowledge.schema import KnowledgeSource, KnowledgeUnit


def default_knowledge_sources() -> tuple[KnowledgeSource, ...]:
    return (
        KnowledgeSource("docs/v20.prestart.strength", "V20 prestart strength boundary", "design_doc", "docs/v20/V20_PRESTART_V19_DEEP_REVIEW.md"),
        KnowledgeSource("docs/v20.prestart.branch", "V20 prestart branch boundary", "design_doc", "docs/v20/V20_PRESTART_V19_DEEP_REVIEW.md"),
        KnowledgeSource("docs/v20.prestart.time_layer", "V20 prestart time-layer boundary", "design_doc", "docs/v20/V20_PRESTART_V19_DEEP_REVIEW.md"),
        KnowledgeSource("docs/v20.prestart.wealth", "V20 prestart wealth boundary", "design_doc", "docs/v20/V20_PRESTART_V19_DEEP_REVIEW.md"),
        KnowledgeSource("docs/v20.prestart.career", "V20 prestart career projection", "design_doc", "docs/v20/V20_PRESTART_V19_DEEP_REVIEW.md"),
        KnowledgeSource("docs/v20.prestart.relationship", "V20 prestart relationship projection", "design_doc", "docs/v20/V20_PRESTART_V19_DEEP_REVIEW.md"),
        KnowledgeSource("docs/v20.prestart.health", "V20 prestart health boundary", "design_doc", "docs/v20/V20_PRESTART_V19_DEEP_REVIEW.md"),
        KnowledgeSource("docs/v20.prestart.useful_god", "V20 prestart useful-god gate", "design_doc", "docs/v20/V20_PRESTART_V19_DEEP_REVIEW.md"),
        KnowledgeSource("docs/v20.prestart.ten_god", "V20 prestart ten-god boundary", "design_doc", "docs/v20/V20_PRESTART_V19_DEEP_REVIEW.md"),
        KnowledgeSource("docs/v20.prestart.element_distribution", "V20 prestart element distribution boundary", "design_doc", "docs/v20/V20_PRESTART_V19_DEEP_REVIEW.md"),
        KnowledgeSource("docs/v20.prestart.pattern", "V20 prestart pattern review boundary", "design_doc", "docs/v20/V20_PRESTART_V19_DEEP_REVIEW.md"),
        KnowledgeSource("docs/v20.useful_god_candidates", "V20 useful-god candidate paths", "implementation_doc", "docs/v20/V20_USEFUL_GOD_CANDIDATES.md"),
    )


def build_knowledge_source_catalog(
    *,
    units: tuple[KnowledgeUnit, ...] | None = None,
    sources: tuple[KnowledgeSource, ...] | None = None,
) -> dict[str, object]:
    rows = tuple(units or default_knowledge_units())
    source_rows = tuple(sources or default_knowledge_sources())
    source_ids = {source.source_ref for source in source_rows}
    unit_refs = sorted({ref for unit in rows for ref in unit.source_refs})
    missing_refs = [ref for ref in unit_refs if ref not in source_ids]
    duplicate_refs = _duplicate_refs(source_rows)
    unreviewed_sources = [source.source_ref for source in source_rows if source.review_status != "reviewed"]
    return {
        "version": "v20.knowledge_source_catalog.v1",
        "status": "ready" if not missing_refs and not duplicate_refs and not unreviewed_sources else "needs_review",
        "source_count": len(source_rows),
        "unit_source_ref_count": len(unit_refs),
        "sources": [source.to_dict() for source in source_rows],
        "missing_source_refs": missing_refs,
        "duplicate_source_refs": duplicate_refs,
        "unreviewed_sources": unreviewed_sources,
        "source_type_counts": dict(Counter(source.source_type for source in source_rows)),
        "runtime_mutation": False,
        "guardrails": [
            "SOURCE_CATALOG_IS_READ_ONLY",
            "ALL_KNOWLEDGE_UNITS_REQUIRE_SOURCE_TRACEABILITY",
            "NO_SOURCE_FREE_KNOWLEDGE_RELEASE",
        ],
    }


def _duplicate_refs(sources: tuple[KnowledgeSource, ...]) -> list[str]:
    counts = Counter(source.source_ref for source in sources)
    return sorted(ref for ref, count in counts.items() if count > 1)
