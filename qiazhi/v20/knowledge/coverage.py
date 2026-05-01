from __future__ import annotations

from v20.answer.measurement_policy import DOMAIN_LABELS
from v20.interaction.questions import QUESTION_LABELS
from v20.knowledge.catalog import build_knowledge_catalog
from v20.knowledge.loader import default_knowledge_units
from v20.knowledge.schema import KnowledgeUnit
from v20.knowledge.source_catalog import build_knowledge_source_catalog


def build_knowledge_coverage_report(units: tuple[KnowledgeUnit, ...] | None = None) -> dict[str, object]:
    rows = tuple(units or default_knowledge_units())
    catalog = build_knowledge_catalog(rows)
    source_catalog = build_knowledge_source_catalog(units=rows)
    covered_domains = {unit.domain for unit in rows if unit.status == "reviewed"}
    required_domains = set(DOMAIN_LABELS)
    missing_domains = sorted(required_domains - covered_domains)
    unknown_question_hooks = sorted(
        {
            hook
            for unit in rows
            for hook in unit.question_hooks
            if hook not in QUESTION_LABELS
        }
    )
    gaps = []
    for domain in missing_domains:
        gaps.append({"gap_type": "missing_domain", "value": domain})
    for ref in source_catalog["missing_source_refs"]:
        gaps.append({"gap_type": "missing_source_ref", "value": ref})
    for hook in unknown_question_hooks:
        gaps.append({"gap_type": "unknown_question_hook", "value": hook})
    return {
        "version": "v20.knowledge_coverage_report.v1",
        "status": "pass" if not gaps else "needs_review",
        "required_domain_count": len(required_domains),
        "covered_domain_count": len(covered_domains),
        "missing_domains": missing_domains,
        "unknown_question_hooks": unknown_question_hooks,
        "gap_count": len(gaps),
        "gaps": gaps,
        "catalog_status": catalog["status"],
        "source_catalog_status": source_catalog["status"],
        "runtime_mutation": False,
        "guardrails": [
            "KNOWLEDGE_COVERAGE_AUDIT_ONLY",
            "GAPS_DO_NOT_BLOCK_RUNTIME_BY_THEMSELVES",
            "RELEASE_REQUIRES_REVIEWED_SOURCE_COVERAGE",
        ],
    }
