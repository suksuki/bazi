from __future__ import annotations

from collections import Counter

from v20.knowledge.audit import audit_default_knowledge_units
from v20.knowledge.loader import default_knowledge_units
from v20.knowledge.schema import KnowledgeUnit
from v20.knowledge.source_catalog import build_knowledge_source_catalog


def build_knowledge_catalog(units: tuple[KnowledgeUnit, ...] | None = None) -> dict[str, object]:
    rows = tuple(units or default_knowledge_units())
    domain_counts = Counter(unit.domain for unit in rows)
    feature_hooks = sorted({hook for unit in rows for hook in unit.feature_hooks})
    question_hooks = sorted({hook for unit in rows for hook in unit.question_hooks})
    retrieval_tags = sorted({tag for unit in rows for tag in unit.retrieval_tags})
    duplicate_ids = _duplicate_ids(rows)
    audit = audit_default_knowledge_units() if units is None else _audit_units(rows)
    source_catalog = build_knowledge_source_catalog(units=rows)
    status = "ready" if audit["status"] == "pass" and not duplicate_ids and source_catalog["status"] == "ready" else "needs_review"
    return {
        "version": "v20.knowledge_catalog.v1",
        "status": status,
        "completeness_status": "phase1_seed_coverage_ready_depth_incomplete",
        "completion_scope": "reviewed_core_domain_seed_units_not_full_bazi_canon",
        "unit_count": len(rows),
        "reviewed_unit_count": sum(1 for unit in rows if unit.status == "reviewed"),
        "domain_count": len(domain_counts),
        "domains": [
            {
                "domain": domain,
                "unit_count": count,
                "reviewed": all(unit.status == "reviewed" for unit in rows if unit.domain == domain),
            }
            for domain, count in sorted(domain_counts.items())
        ],
        "feature_hooks": feature_hooks,
        "question_hooks": question_hooks,
        "retrieval_tags": retrieval_tags,
        "duplicate_ids": duplicate_ids,
        "audit": audit,
        "source_catalog_status": source_catalog["status"],
        "missing_source_refs": source_catalog["missing_source_refs"],
        "known_limits": [
            "classical_source_corpus_not_fully_imported",
            "school_variant_rules_not_exhaustive",
            "combination_exception_rules_need_review",
            "time_layer_and_domain_specific_rules_need_expansion",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "KNOWLEDGE_CATALOG_IS_READ_ONLY",
            "REVIEWED_UNITS_ONLY_FOR_RUNTIME_RETRIEVAL",
            "KNOWLEDGE_SUPPORTS_FEATURES_NOT_RULE_TRUTH",
        ],
    }


def _duplicate_ids(units: tuple[KnowledgeUnit, ...]) -> list[str]:
    counts = Counter(unit.knowledge_id for unit in units)
    return sorted(knowledge_id for knowledge_id, count in counts.items() if count > 1)


def _audit_units(units: tuple[KnowledgeUnit, ...]) -> dict[str, object]:
    failures: list[str] = []
    for unit in units:
        if unit.status != "reviewed":
            failures.append(f"not_reviewed:{unit.knowledge_id}")
        if not unit.source_refs:
            failures.append(f"missing_source_refs:{unit.knowledge_id}")
        if not unit.feature_hooks and not unit.question_hooks:
            failures.append(f"missing_hooks:{unit.knowledge_id}")
        if "direct_rule_truth" not in unit.forbidden_usage:
            failures.append(f"missing_forbidden_rule_truth:{unit.knowledge_id}")
        if not unit.evidence_template or not unit.boundary:
            failures.append(f"missing_evidence_or_boundary:{unit.knowledge_id}")
    return {
        "version": "v20.knowledge_catalog_audit.v1",
        "status": "pass" if not failures else "fail",
        "unit_count": len(units),
        "failures": failures,
        "guardrails": ["CATALOG_AUDIT_ONLY", "NO_RULE_ACTIVATION"],
    }
