from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from v20.knowledge.migration import build_v19_knowledge_migration_audit


def build_knowledge_draft_import_preview(*, root: Path | None = None, limit: int = 120) -> dict[str, object]:
    source_root = root or Path(__file__).resolve().parents[2] / "docs" / "bazi_knowledge"
    seed_paths = _seed_paths(source_root)
    candidates = []
    failures = []
    for path in seed_paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive local-file guard
            failures.append({"relative_path": str(path.relative_to(source_root)), "error": str(exc)})
            continue
        for index, draft in enumerate(payload.get("knowledge_drafts", ()) if isinstance(payload, dict) else ()):
            if isinstance(draft, dict):
                candidates.append(_candidate(draft, path, source_root, index))
    audit = build_v19_knowledge_migration_audit(source_root)
    return {
        "version": "v20.knowledge_draft_import_preview.v1",
        "status": "preview_ready" if candidates and not failures else "needs_review",
        "source_root": str(source_root),
        "seed_file_count": len(seed_paths),
        "candidate_count": len(candidates),
        "returned_candidate_count": min(limit, len(candidates)),
        "candidates": candidates[:limit],
        "parse_failures": failures,
        "migration_audit_status": audit["status"],
        "migration_audit_candidate_count": audit["candidate_count"],
        "target_status": "draft_review_required",
        "runtime_mutation": False,
        "guardrails": [
            "DRAFT_IMPORT_PREVIEW_ONLY",
            "NO_AUTOMATIC_REVIEWED_STATUS",
            "NO_RUNTIME_KNOWLEDGE_ACTIVATION",
            "HUMAN_OR_VALIDATION_REVIEW_REQUIRED",
        ],
    }


def _seed_paths(source_root: Path) -> tuple[Path, ...]:
    if not source_root.exists():
        return ()
    paths = []
    database_seed = source_root / "database" / "current_knowledge_draft_seeds_v1.json"
    if database_seed.exists():
        paths.append(database_seed)
    pack_dir = source_root / "packs"
    if pack_dir.exists():
        paths.extend(sorted(pack_dir.glob("*knowledge_draft_seeds_v1.json")))
    return tuple(dict.fromkeys(paths))


def _candidate(draft: dict[str, Any], path: Path, source_root: Path, index: int) -> dict[str, object]:
    source_refs = tuple(str(row) for row in draft.get("source_refs", ()) if row)
    allowed_usage = tuple(str(row) for row in draft.get("allowed_usage", ()) if row)
    forbidden_usage = tuple(str(row) for row in draft.get("forbidden_usage", ()) if row)
    knowledge_id = str(draft.get("knowledge_id") or f"{path.stem}.{index:03d}")
    domain = str(draft.get("domain") or draft.get("category") or "unknown")
    return {
        "draft_id": f"v20.draft_import.{_slug(knowledge_id)}",
        "source_file": str(path.relative_to(source_root)),
        "source_index": index,
        "source_status": str(draft.get("status") or "legacy_draft"),
        "target_status": "draft_review_required",
        "target_domain": domain,
        "target_knowledge_id": knowledge_id,
        "title": str(draft.get("title") or knowledge_id),
        "summary_preview": str(draft.get("statement") or draft.get("summary") or "")[:240],
        "source_refs": source_refs,
        "allowed_usage": allowed_usage,
        "forbidden_usage": forbidden_usage,
        "risk_level": str(draft.get("risk_level") or _risk_level(domain, forbidden_usage)),
        "required_review_steps": (
            "verify_source_refs",
            "write_evidence_template",
            "write_boundary",
            "map_feature_and_question_hooks",
            "synthetic_validation_before_release",
        ),
        "blocked_outputs": (
            "reviewed_runtime_unit",
            "rule_activation",
            "answer_claim_without_boundary",
        ),
    }


def _risk_level(domain: str, forbidden_usage: tuple[str, ...]) -> str:
    if domain in {"health", "personality", "shensha", "blind_method"}:
        return "R2"
    if any("prediction" in row or "rule" in row for row in forbidden_usage):
        return "R1"
    return "R0"


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "." for ch in value).strip(".")[:120]
