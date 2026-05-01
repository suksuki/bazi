from __future__ import annotations

from v20.knowledge.draft_import import build_knowledge_draft_import_preview
from v20.knowledge.review_queue import CORE_DOMAIN_PRIORITY


def build_knowledge_review_packet(domain: str, *, limit: int = 8) -> dict[str, object]:
    normalized = domain.strip()
    candidates = [
        row
        for row in build_knowledge_draft_import_preview(limit=10_000)["candidates"]
        if isinstance(row, dict) and row.get("target_domain") == normalized
    ]
    selected = sorted(candidates, key=lambda row: (str(row.get("risk_level", "")), str(row.get("target_knowledge_id", ""))))[:limit]
    proposed_units = [_proposed_unit(row, normalized) for row in selected]
    missing_fields = [_missing_fields(row) for row in selected]
    blockers = _release_blockers(selected, missing_fields)
    return {
        "version": "v20.knowledge_review_packet.v1",
        "domain": normalized,
        "status": "ready_for_review" if selected else "empty",
        "candidate_count": len(candidates),
        "selected_count": len(selected),
        "candidates": selected,
        "proposed_units": proposed_units,
        "missing_fields": missing_fields,
        "release_blockers": blockers,
        "review_checklist": (
            "verify_source_refs",
            "confirm_or_rewrite_summary",
            "write_evidence_template",
            "write_boundary",
            "map_feature_hooks",
            "map_question_hooks",
            "run_synthetic_validation",
            "record_decision_registry_review",
        ),
        "validation_requirements": (
            "knowledge_catalog_audit_pass",
            "source_catalog_ready",
            "coverage_report_pass",
            "no_direct_rule_truth",
            "no_fortune_verdict",
        ),
        "runtime_mutation": False,
        "guardrails": [
            "REVIEW_PACKET_ONLY",
            "PROPOSED_UNITS_ARE_DRAFTS",
            "NO_RUNTIME_KNOWLEDGE_ACTIVATION",
            "DECISION_RECORD_REQUIRED_FOR_RELEASE",
        ],
    }


def build_first_wave_review_packets(*, limit_per_domain: int = 5) -> dict[str, object]:
    packets = [
        build_knowledge_review_packet(domain, limit=limit_per_domain)
        for domain in CORE_DOMAIN_PRIORITY
    ]
    packets = [packet for packet in packets if packet["status"] != "empty"]
    return {
        "version": "v20.knowledge_first_wave_review_packets.v1",
        "status": "ready" if packets else "empty",
        "domain_count": len(packets),
        "core_domain_priority": CORE_DOMAIN_PRIORITY,
        "packets": packets,
        "runtime_mutation": False,
        "guardrails": [
            "FIRST_WAVE_REVIEW_PACKETS_ONLY",
            "CORE_BAZI_DOMAINS_FIRST",
            "NO_AUTOMATIC_REVIEWED_STATUS",
        ],
    }


def _proposed_unit(row: dict[str, object], domain: str) -> dict[str, object]:
    knowledge_id = str(row.get("target_knowledge_id", ""))
    return {
        "knowledge_id": f"v20.draft.{knowledge_id}",
        "title": row.get("title", knowledge_id),
        "domain": domain,
        "summary": row.get("summary_preview", ""),
        "evidence_template": "",
        "boundary": "",
        "status": "draft_review_required",
        "source_refs": row.get("source_refs", ()),
        "feature_hooks": (),
        "question_hooks": (),
        "allowed_usage": row.get("allowed_usage", ()),
        "forbidden_usage": row.get("forbidden_usage", ()),
        "guardrails": [
            "DRAFT_UNIT_SKELETON",
            "MISSING_BOUNDARY_AND_HOOK_REVIEW",
            "NOT_RUNTIME_RETRIEVABLE",
        ],
    }


def _missing_fields(row: dict[str, object]) -> dict[str, object]:
    missing = ["evidence_template", "boundary", "feature_hooks", "question_hooks"]
    if not row.get("source_refs"):
        missing.append("source_refs")
    return {
        "draft_id": row.get("draft_id", ""),
        "target_knowledge_id": row.get("target_knowledge_id", ""),
        "missing": tuple(missing),
    }


def _release_blockers(selected: list[dict[str, object]], missing_fields: list[dict[str, object]]) -> tuple[str, ...]:
    blockers = []
    if not selected:
        blockers.append("no_candidates_selected")
    if any(row["missing"] for row in missing_fields):
        blockers.append("draft_units_have_missing_required_fields")
    if any(str(row.get("risk_level", "")).upper() in {"R3", "R4"} for row in selected):
        blockers.append("high_risk_candidates_require_extra_review")
    return tuple(blockers)
