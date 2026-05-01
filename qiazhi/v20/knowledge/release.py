from __future__ import annotations

from datetime import datetime, timezone

from v20.knowledge.catalog import build_knowledge_catalog
from v20.knowledge.coverage import build_knowledge_coverage_report
from v20.knowledge.loader import default_knowledge_units
from v20.knowledge.schema import KnowledgeUnit
from v20.knowledge.source_catalog import build_knowledge_source_catalog


def build_knowledge_release_manifest(
    *,
    units: tuple[KnowledgeUnit, ...] | None = None,
    release_id: str = "v20.knowledge.release.current",
) -> dict[str, object]:
    rows = tuple(units or default_knowledge_units())
    catalog = build_knowledge_catalog(rows)
    source_catalog = build_knowledge_source_catalog(units=rows)
    coverage = build_knowledge_coverage_report(rows)
    blockers = []
    if catalog["status"] != "ready":
        blockers.append("knowledge_catalog_not_ready")
    if source_catalog["status"] != "ready":
        blockers.append("source_catalog_not_ready")
    if coverage["status"] != "pass":
        blockers.append("coverage_report_has_gaps")
    status = "ready_for_release_review" if not blockers else "blocked"
    return {
        "version": "v20.knowledge_release_manifest.v1",
        "release_id": release_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "unit_count": len(rows),
        "reviewed_unit_count": sum(1 for unit in rows if unit.status == "reviewed"),
        "source_count": source_catalog["source_count"],
        "domain_count": catalog["domain_count"],
        "unit_ids": [unit.knowledge_id for unit in rows],
        "domains": [row["domain"] for row in catalog["domains"]],
        "blockers": blockers,
        "release_steps": [
            "audit_units",
            "verify_source_catalog",
            "verify_domain_and_question_hook_coverage",
            "run_synthetic_validation",
            "record_decision_registry_approval",
            "promote_reviewed_release_to_postgres_seed_or_artifact",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "RELEASE_MANIFEST_ONLY",
            "NO_DATABASE_WRITE",
            "NO_RULE_ACTIVATION",
            "DECISION_RECORD_REQUIRED_FOR_PROMOTION",
        ],
    }
