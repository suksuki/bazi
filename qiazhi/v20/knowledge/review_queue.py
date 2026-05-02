from __future__ import annotations

from collections import Counter, defaultdict

from v20.knowledge.draft_import import build_knowledge_draft_import_preview

CORE_DOMAIN_PRIORITY = (
    "strength",
    "ten_god",
    "useful_god",
    "element",
    "branch",
    "wealth",
    "pattern",
    "time",
    "career",
    "relationship",
    "health",
)


def build_knowledge_review_queue(*, limit_per_domain: int = 8) -> dict[str, object]:
    preview = build_knowledge_draft_import_preview(limit=10_000)
    candidates = tuple(row for row in preview["candidates"] if isinstance(row, dict))
    by_domain: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in candidates:
        by_domain[str(row.get("target_domain", "unknown"))].append(row)
    domain_rows = []
    for domain, rows in sorted(by_domain.items(), key=lambda item: (_domain_rank(item[0]), item[0])):
        risk_counts = Counter(str(row.get("risk_level", "unknown")) for row in rows)
        domain_rows.append(
            {
                "domain": domain,
                "priority_rank": _domain_rank(domain),
                "candidate_count": len(rows),
                "risk_counts": dict(sorted(risk_counts.items())),
                "recommended_first_batch": [
                    _compact_candidate(row)
                    for row in sorted(rows, key=lambda row: (str(row.get("risk_level", "")), str(row.get("target_knowledge_id", ""))))[:limit_per_domain]
                ],
                "review_policy": _review_policy(domain),
            }
        )
    return {
        "version": "v20.knowledge_review_queue.v1",
        "status": "ready" if candidates else "empty",
        "candidate_count": len(candidates),
        "domain_count": len(domain_rows),
        "core_domain_priority": CORE_DOMAIN_PRIORITY,
        "domains": domain_rows,
        "runtime_mutation": False,
        "guardrails": [
            "REVIEW_QUEUE_ONLY",
            "DRAFTS_REQUIRE_SOURCE_BOUNDARY_AND_HOOK_REVIEW",
            "QUEUE_FEEDS_ACTIVE_RUNTIME_AFTER_TRACE",
            "CORE_BAZI_DOMAINS_FIRST",
        ],
    }


def _compact_candidate(row: dict[str, object]) -> dict[str, object]:
    return {
        "draft_id": row.get("draft_id", ""),
        "target_knowledge_id": row.get("target_knowledge_id", ""),
        "title": row.get("title", ""),
        "source_file": row.get("source_file", ""),
        "risk_level": row.get("risk_level", ""),
        "target_status": row.get("target_status", ""),
    }


def _domain_rank(domain: str) -> int:
    try:
        return CORE_DOMAIN_PRIORITY.index(domain)
    except ValueError:
        return len(CORE_DOMAIN_PRIORITY) + 1


def _review_policy(domain: str) -> str:
    if domain in {"health", "personality", "shensha", "blind_method"}:
        return "high_caution_boundary_review"
    if domain in CORE_DOMAIN_PRIORITY:
        return "core_bazi_first_wave_review"
    return "secondary_archive_or_domain_review"
