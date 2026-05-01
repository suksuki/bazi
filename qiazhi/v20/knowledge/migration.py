from __future__ import annotations

from collections import Counter
from pathlib import Path

DOMAIN_ALIASES = {
    "answer_expression": "answer_expression",
    "auxiliary_pillars": "auxiliary",
    "auxiliary_symbols": "auxiliary",
    "blind": "blind_method",
    "branch_advanced": "branch",
    "calendar": "calendar",
    "career": "career",
    "children": "children",
    "core": "core",
    "family": "family",
    "geo_context": "geo_context",
    "growth_phase": "growth_phase",
    "health": "health",
    "interaction": "ten_god_interaction",
    "nayin": "nayin",
    "palace": "palace",
    "pattern": "pattern",
    "personality": "personality",
    "relationship": "relationship",
    "rule_db": "rule_db",
    "shensha": "shensha",
    "strength": "strength",
    "ten_god": "ten_god",
    "time_context": "time",
    "timing": "time",
    "useful_god": "useful_god",
    "wealth": "wealth",
}


def build_v19_knowledge_migration_audit(root: Path | None = None) -> dict[str, object]:
    source_root = root or Path(__file__).resolve().parents[2] / "docs" / "bazi_knowledge"
    files = tuple(sorted(path for path in source_root.rglob("*") if path.is_file())) if source_root.exists() else ()
    candidates = tuple(_candidate(path, source_root) for path in files if path.suffix in {".md", ".json"})
    domain_counts = Counter(str(row["domain"]) for row in candidates)
    file_type_counts = Counter(str(row["file_type"]) for row in candidates)
    risky = [row for row in candidates if row["migration_risk"] != "low"]
    return {
        "version": "v20.v19_knowledge_migration_audit.v1",
        "status": "audit_ready" if candidates else "source_missing",
        "source_root": str(source_root),
        "candidate_count": len(candidates),
        "domain_count": len(domain_counts),
        "file_type_counts": dict(sorted(file_type_counts.items())),
        "domain_counts": dict(sorted(domain_counts.items())),
        "high_or_medium_risk_count": len(risky),
        "sample_candidates": list(candidates[:16]),
        "migration_lanes": [
            "reviewed_unit_seed",
            "draft_unit_review",
            "archive_only_reference",
            "rule_conversion_candidate",
            "blocked_until_source_review",
        ],
        "blocked_actions": [
            "direct_runtime_import",
            "automatic_reviewed_status",
            "rule_activation_from_legacy_docs",
            "llm_generated_knowledge_without_source",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "V19_KNOWLEDGE_MIGRATION_AUDIT_ONLY",
            "LEGACY_DOCS_ENTER_DRAFT_REVIEW_FIRST",
            "NO_DIRECT_RUNTIME_ACTIVATION",
            "SOURCE_AND_BOUNDARY_REVIEW_REQUIRED",
        ],
    }


def _candidate(path: Path, root: Path) -> dict[str, object]:
    relative = path.relative_to(root)
    first_part = relative.parts[0] if relative.parts else "unknown"
    domain = DOMAIN_ALIASES.get(first_part, first_part)
    file_type = path.suffix.lstrip(".")
    lane = _lane(relative, file_type)
    return {
        "relative_path": str(relative),
        "domain": domain,
        "file_type": file_type,
        "migration_lane": lane,
        "target_status": "draft_review_required" if lane != "archive_only_reference" else "archive_only",
        "migration_risk": _risk(relative, domain, lane),
    }


def _lane(relative: Path, file_type: str) -> str:
    text = str(relative)
    name = relative.name
    if "catalog/" in text or "source_archive/" in text:
        return "archive_only_reference"
    if file_type == "json" and ("draft_seeds" in name or "knowledge_draft" in name):
        return "draft_unit_review"
    if "rule_db" in text or "rule_conversion" in text:
        return "rule_conversion_candidate"
    if "archive" in name or "legacy" in name:
        return "archive_only_reference"
    return "reviewed_unit_seed"


def _risk(relative: Path, domain: str, lane: str) -> str:
    text = str(relative)
    if lane in {"rule_conversion_candidate", "draft_unit_review"}:
        return "medium"
    if domain in {"blind_method", "shensha", "personality", "health", "nayin"}:
        return "medium"
    if "legacy" in text or "archive" in text:
        return "medium"
    return "low"
