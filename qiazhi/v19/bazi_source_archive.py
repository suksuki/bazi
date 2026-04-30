from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

from v19.runtime import RUNTIME, utc_now

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
CATALOG_FILE = PROJECT_ROOT / "docs" / "bazi_knowledge" / "source_archive" / "source_catalog_v1.json"
DEFAULT_KNOWLEDGE_DRAFT_SEED_FILE = PROJECT_ROOT / "docs" / "bazi_knowledge" / "database" / "current_knowledge_draft_seeds_v1.json"
KNOWLEDGE_DRAFT_SEED_FILE = DEFAULT_KNOWLEDGE_DRAFT_SEED_FILE
KNOWLEDGE_DRAFT_PACK_DIR = PROJECT_ROOT / "docs" / "bazi_knowledge" / "packs"
SOURCE_ARCHIVE_FILE = RUNTIME / "bazi_source_archive.json"
SOURCE_ARCHIVE_VERSION = "v19.bazi_source_archive.v1"

ALLOWED_SOURCE_TYPES = {
    "classical_text",
    "classical_commentary",
    "legacy_v17_v18",
    "modern_reference",
    "practitioner_note",
    "web_reference",
    "library_record",
    "pdf_scan",
}
ALLOWED_LANGUAGE = {"zh", "en", "ko", "mixed"}
ALLOWED_RELIABILITY = {"high", "medium", "low", "unknown"}
ALLOWED_SOURCE_PRIORITY = {"primary", "secondary", "tertiary"}
ALLOWED_RISK_LEVEL = {"R0", "R1", "R2", "R3", "R4"}
ALLOWED_INGESTION_STATUS = {"cataloged", "queued", "excerpting", "draft_units_created", "deprecated"}
ALLOWED_EXCERPT_STATUS = {"draft", "reviewed", "deprecated"}
ALLOWED_DRAFT_REVIEW_STATUS = {"pending", "reviewed", "needs_revision", "proposal_ready", "rejected", "deprecated"}
MAX_SHORT_EXCERPT_CHARS = 600
GUARDRAILS = [
    "SOURCE_ARCHIVE_ONLY",
    "NO_ACTIVE_RULE_CREATION",
    "NO_RUNTIME_INFERENCE_CHANGE",
    "NO_DIRECT_PLUGIN_RULE_REUSE",
    "ANALYST_REVIEW_REQUIRED_BEFORE_RULE_PROPOSAL",
]


def source_archive_status() -> Dict[str, Any]:
    state, storage = _load_state()
    sources = list(state.get("sources") or [])
    excerpts = list(state.get("excerpts") or [])
    drafts = list(state.get("knowledge_drafts") or [])
    return {
        "ok": True,
        "version": SOURCE_ARCHIVE_VERSION,
        "runtime_scope": "source_archive_only_no_inference",
        "storage": storage,
        "catalog_path": str(CATALOG_FILE),
        "runtime_path": str(SOURCE_ARCHIVE_FILE),
        "counts": {
            "sources": len(sources),
            "excerpts": len(excerpts),
            "knowledge_drafts": len(drafts),
            "by_type": _count_by(sources, "source_type"),
            "by_risk": _count_by(sources, "risk_level"),
            "by_status": _count_by(sources, "ingestion_status"),
            "excerpts_by_risk": _count_by(excerpts, "risk_level"),
            "drafts_by_risk": _count_by(drafts, "risk_level"),
            "drafts_by_status": _count_by(drafts, "review_status"),
        },
        "guardrails": GUARDRAILS,
    }


def source_governance_overview() -> Dict[str, Any]:
    state, storage = _load_state()
    drafts = [dict(row) for row in state.get("knowledge_drafts") or []]
    proposal_ready = [row for row in drafts if row.get("review_status") == "proposal_ready"]
    r4_blocked = [row for row in drafts if row.get("risk_level") == "R4"]
    needs_revision = [row for row in drafts if row.get("review_status") == "needs_revision"]
    pending = [row for row in drafts if row.get("review_status") in {"", None, "pending"}]
    return {
        "ok": True,
        "runtime_scope": "governance_overview_only_no_runtime_inference",
        "storage": storage,
        "counts": {
            "sources": len(state.get("sources") or []),
            "excerpts": len(state.get("excerpts") or []),
            "knowledge_drafts": len(drafts),
            "proposal_ready": len(proposal_ready),
            "r4_blocked": len(r4_blocked),
            "needs_revision": len(needs_revision),
            "pending": len(pending),
            "by_review_status": _count_by(drafts, "review_status"),
            "by_risk_level": _count_by(drafts, "risk_level"),
        },
        "proposal_ready_items": _draft_summary(proposal_ready),
        "r4_blocked_items": _draft_summary(r4_blocked),
        "needs_revision_items": _draft_summary(needs_revision),
        "pending_items": _draft_summary(pending),
        "guardrails": GUARDRAILS + ["OVERVIEW_ONLY", "NO_RUNTIME_INFERENCE_CHANGE"],
    }


def seed_source_archive(*, force: bool = False) -> Dict[str, Any]:
    state, _ = _load_state()
    catalog = _load_catalog_sources()
    if force:
        state["sources"] = []
    existing = {str(item.get("source_id") or ""): item for item in state.get("sources") or []}
    imported = 0
    updated = 0
    for item in catalog:
        source = _normalize_source_record(item, default_status="cataloged")
        source_id = source["source_id"]
        if source_id in existing:
            merged = {**existing[source_id], **source, "updated_at": utc_now()}
            merged.setdefault("history", []).append(_history("catalog_seed_update", "admin", "Source catalog seed updated; no runtime inference change."))
            existing[source_id] = merged
            updated += 1
        else:
            source["created_at"] = utc_now()
            source["updated_at"] = utc_now()
            source["history"] = [_history("catalog_seed_create", "admin", "Source catalog seed created; source archive only.")]
            existing[source_id] = source
            imported += 1
    state["sources"] = sorted(existing.values(), key=lambda row: str(row.get("source_id") or ""))
    saved = _save_state(state)
    return {
        "ok": True,
        "status": "seeded",
        "imported_count": imported,
        "updated_count": updated,
        "count": len(state["sources"]),
        "storage": saved,
        "guardrails": GUARDRAILS,
    }


def list_source_records(*, source_type: str = "", risk_level: str = "", ingestion_status: str = "", q: str = "") -> Dict[str, Any]:
    state, storage = _load_state()
    rows = [dict(row) for row in state.get("sources") or []]
    if source_type:
        rows = [row for row in rows if row.get("source_type") == source_type]
    if risk_level:
        rows = [row for row in rows if row.get("risk_level") == risk_level]
    if ingestion_status:
        rows = [row for row in rows if row.get("ingestion_status") == ingestion_status]
    if q:
        needle = q.lower().strip()
        rows = [row for row in rows if _source_search_text(row).lower().find(needle) >= 0]
    rows.sort(key=lambda row: (str(row.get("source_priority") or ""), str(row.get("risk_level") or ""), str(row.get("title") or "")))
    return {
        "ok": True,
        "count": len(rows),
        "items": rows[:300],
        "storage": storage,
        "runtime_scope": "source_archive_only_no_inference",
        "guardrails": GUARDRAILS,
    }


def list_excerpt_records(*, source_id: str = "", risk_level: str = "", status: str = "", q: str = "") -> Dict[str, Any]:
    state, storage = _load_state()
    rows = [dict(row) for row in state.get("excerpts") or []]
    if source_id:
        rows = [row for row in rows if row.get("source_id") == source_id]
    if risk_level:
        rows = [row for row in rows if row.get("risk_level") == risk_level]
    if status:
        rows = [row for row in rows if row.get("status") == status]
    if q:
        needle = q.lower().strip()
        rows = [row for row in rows if _excerpt_search_text(row).lower().find(needle) >= 0]
    rows.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return {
        "ok": True,
        "count": len(rows),
        "items": rows[:300],
        "storage": storage,
        "runtime_scope": "excerpt_archive_only_no_rule_creation",
        "guardrails": GUARDRAILS + ["SHORT_EXCERPT_ONLY", "NO_BULK_COPY"],
    }


def create_excerpt_record(payload: Dict[str, Any]) -> Dict[str, Any]:
    state, _ = _load_state()
    source_id = _clean(payload.get("source_id"))
    if not source_id:
        return {"ok": False, "code": "SOURCE_ID_REQUIRED", "message": "source_id is required."}
    if not any(row.get("source_id") == source_id for row in state.get("sources") or []):
        return {"ok": False, "code": "SOURCE_NOT_FOUND", "message": "source_id is not cataloged in Source Archive."}
    original = _clean(payload.get("original_excerpt_short"))
    summary = _clean(payload.get("normalized_summary"))
    if not original and not summary:
        return {"ok": False, "code": "EXCERPT_CONTENT_REQUIRED", "message": "original_excerpt_short or normalized_summary is required."}
    if len(original) > MAX_SHORT_EXCERPT_CHARS:
        return {
            "ok": False,
            "code": "EXCERPT_TOO_LONG",
            "message": f"original_excerpt_short must be <= {MAX_SHORT_EXCERPT_CHARS} characters. Store summaries, not full text.",
        }
    excerpt = {
        "excerpt_id": _clean(payload.get("excerpt_id")) or "ex_" + uuid.uuid4().hex[:16],
        "source_id": source_id,
        "locator": _clean(payload.get("locator")),
        "original_excerpt_short": original,
        "normalized_summary": summary,
        "keywords": _string_list(payload.get("keywords")),
        "risk_level": _enum(payload.get("risk_level"), ALLOWED_RISK_LEVEL, "R4"),
        "language": _enum(payload.get("language"), ALLOWED_LANGUAGE, "zh"),
        "status": _enum(payload.get("status"), ALLOWED_EXCERPT_STATUS, "draft"),
        "allowed_usage": _string_list(payload.get("allowed_usage")) or ["excerpt_archive", "knowledge_unit_draft_source"],
        "forbidden_usage": _string_list(payload.get("forbidden_usage")) or ["direct_active_rule", "direct_fortune_output", "bulk_copy"],
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "history": [_history("draft", _clean(payload.get("actor_role"), "admin"), "Excerpt created; short excerpt/archive only; no rule creation.")],
        "guardrails": GUARDRAILS + ["SHORT_EXCERPT_ONLY", "NO_BULK_COPY"],
    }
    state.setdefault("excerpts", []).append(excerpt)
    saved = _save_state(state)
    return {"ok": True, "item": excerpt, "storage": saved, "guardrails": excerpt["guardrails"]}


def list_knowledge_drafts(*, domain: str = "", risk_level: str = "", q: str = "") -> Dict[str, Any]:
    state, storage = _load_state()
    rows = [dict(row) for row in state.get("knowledge_drafts") or []]
    if domain:
        rows = [row for row in rows if row.get("domain") == domain]
    if risk_level:
        rows = [row for row in rows if row.get("risk_level") == risk_level]
    if q:
        needle = q.lower().strip()
        rows = [row for row in rows if _draft_search_text(row).lower().find(needle) >= 0]
    rows.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return {
        "ok": True,
        "count": len(rows),
        "items": rows[:300],
        "storage": storage,
        "runtime_scope": "knowledge_unit_draft_only_no_runtime_inference",
        "guardrails": GUARDRAILS + ["DRAFT_ONLY", "REQUIRES_RULE_PROPOSAL_BEFORE_RUNTIME"],
    }


def update_knowledge_draft_review(draft_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    state, _ = _load_state()
    target = None
    for row in state.get("knowledge_drafts") or []:
        if row.get("draft_id") == draft_id or row.get("knowledge_id") == draft_id:
            target = row
            break
    if not target:
        return {"ok": False, "code": "KNOWLEDGE_DRAFT_NOT_FOUND", "message": "knowledge draft not found."}
    status = _enum(payload.get("review_status"), ALLOWED_DRAFT_REVIEW_STATUS, "reviewed")
    actor_role = _clean(payload.get("actor_role"), "admin")
    note = _clean(payload.get("note"), "Knowledge draft reviewed; no runtime inference change.")
    target["review_status"] = status
    target["review_note"] = note
    target["reviewed_by_role"] = actor_role
    target["reviewed_at"] = utc_now()
    target["updated_at"] = utc_now()
    target.setdefault("history", []).append(_history(status, actor_role, note))
    saved = _save_state(state)
    return {"ok": True, "item": target, "storage": saved, "guardrails": GUARDRAILS + ["DRAFT_REVIEW_ONLY", "NO_RUNTIME_INFERENCE_CHANGE"]}


def build_rule_proposal_from_knowledge_draft(draft_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    state, _ = _load_state()
    draft = _find_knowledge_draft(state, draft_id)
    if not draft:
        return {"ok": False, "code": "KNOWLEDGE_DRAFT_NOT_FOUND", "message": "knowledge draft not found."}
    if draft.get("review_status") != "proposal_ready":
        return {
            "ok": False,
            "code": "KNOWLEDGE_DRAFT_NOT_PROPOSAL_READY",
            "message": "knowledge draft must be reviewed as proposal_ready before creating a rule proposal.",
        }
    if draft.get("risk_level") == "R4":
        return {
            "ok": False,
            "code": "R4_ARCHIVE_ONLY",
            "message": "R4 symbolic/saying/case knowledge is archive-only and cannot become a rule proposal.",
        }
    rule_domain = _clean(payload.get("domain")) or _draft_to_rule_domain(draft)
    if not rule_domain:
        return {"ok": False, "code": "RULE_DOMAIN_UNMAPPED", "message": "knowledge draft cannot be mapped to a supported Bazi rule domain."}
    knowledge_id = _clean(draft.get("knowledge_id"))
    rule_id = _clean(payload.get("rule_id")) or "v19.bazi." + knowledge_id
    input_required = _string_list(payload.get("input_required")) or _draft_input_contract(draft, rule_domain)
    output_signal = _clean(payload.get("output_signal")) or _draft_output_signal(draft, rule_domain)
    proposal_payload = {
        "actor_role": _clean(payload.get("actor_role"), "admin"),
        "rule_id": rule_id,
        "domain": rule_domain,
        "version": _bounded_int_local(payload.get("version"), 1, 1, 9999),
        "source_feedback_ids": _string_list(payload.get("source_feedback_ids")),
        "input_contract": {
            "required": input_required,
            "source_draft_id": draft.get("draft_id"),
            "source_knowledge_id": knowledge_id,
        },
        "condition": {
            "source_knowledge_id": knowledge_id,
            "category": draft.get("category"),
            "risk_level": draft.get("risk_level"),
            "review_status": draft.get("review_status"),
            "structured_facts": draft.get("structured_facts") or {},
            "conditions": draft.get("conditions") or {},
        },
        "output_contract": {
            "signal": output_signal,
            "value_set": _draft_value_set(rule_domain),
            "is_prediction": False,
            "runtime_scope": "proposal_only_no_runtime_inference_mutation",
        },
        "reasoning_path": [
            "read reviewed knowledge draft",
            "map draft structured facts into rule proposal schema",
            "require validation and analyst/admin approval before any future engine adapter work",
        ],
        "evidence": {
            "source_draft_id": draft.get("draft_id"),
            "source_knowledge_id": knowledge_id,
            "source_excerpt_ids": draft.get("source_excerpt_ids") or [],
            "source_refs": draft.get("source_refs") or [],
            "risk_level": draft.get("risk_level"),
            "forbidden_usage": draft.get("forbidden_usage") or [],
            "review_note": draft.get("review_note") or "",
        },
        "confidence": _bounded_float(draft.get("confidence_prior"), 0.5, 0.0, 1.0),
        "rationale": _clean(payload.get("rationale")) or f"Created from reviewed knowledge draft {knowledge_id}. Proposal only; no runtime inference mutation.",
        "guardrails": ["FROM_KNOWLEDGE_DRAFT", "RULE_PROPOSAL_ONLY", "NO_RUNTIME_INFERENCE_MUTATION", "VALIDATION_REQUIRED"],
    }
    draft.setdefault("history", []).append(_history("proposal_created", _clean(payload.get("actor_role"), "admin"), f"Rule proposal payload created from draft {knowledge_id}; no runtime inference change."))
    draft["updated_at"] = utc_now()
    saved = _save_state(state)
    return {"ok": True, "proposal_payload": proposal_payload, "source_draft": draft, "storage": saved, "guardrails": proposal_payload["guardrails"]}


def seed_current_knowledge_drafts(*, force: bool = False) -> Dict[str, Any]:
    state, _ = _load_state()
    seeds = _load_knowledge_draft_seeds()
    if force:
        state["knowledge_drafts"] = []
    existing = {str(item.get("knowledge_id") or ""): item for item in state.get("knowledge_drafts") or []}
    imported = 0
    updated = 0
    for payload in seeds:
        knowledge_id = _clean(payload.get("knowledge_id"))
        statement = _clean(payload.get("statement"))
        if not knowledge_id or not statement:
            continue
        draft = {
            "draft_id": _clean(payload.get("draft_id")) or "kud_" + uuid.uuid4().hex[:16],
            "knowledge_id": knowledge_id,
            "domain": _clean(payload.get("domain"), "core_structure"),
            "category": _clean(payload.get("category"), "uncategorized"),
            "title": _clean(payload.get("title"), knowledge_id),
            "statement": statement,
            "structured_facts": payload.get("structured_facts") if isinstance(payload.get("structured_facts"), (dict, list)) else {},
            "conditions": payload.get("conditions") if isinstance(payload.get("conditions"), dict) else {},
            "source_excerpt_ids": _string_list(payload.get("source_excerpt_ids")),
            "source_refs": _string_list(payload.get("source_refs")),
            "risk_level": _enum(payload.get("risk_level"), ALLOWED_RISK_LEVEL, "R2"),
            "confidence_prior": _bounded_float(payload.get("confidence_prior"), 0.5, 0.0, 1.0),
            "status": "draft",
            "review_status": "pending",
            "review_note": "",
            "allowed_usage": _string_list(payload.get("allowed_usage")) or ["knowledge_unit_draft", "rule_proposal_source"],
            "forbidden_usage": _string_list(payload.get("forbidden_usage")) or ["direct_active_rule", "direct_fortune_output", "runtime_inference_without_proposal"],
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "history": [_history("seed_create", "admin", "Current Bazi knowledge draft seeded; requires proposal before runtime.")],
            "guardrails": GUARDRAILS + ["DRAFT_ONLY", "REQUIRES_RULE_PROPOSAL_BEFORE_RUNTIME"],
        }
        if knowledge_id in existing:
            previous = existing[knowledge_id]
            preserved = {
                key: previous.get(key)
                for key in ["draft_id", "status", "review_status", "review_note", "reviewed_by_role", "reviewed_at"]
                if previous.get(key) not in {None, ""}
            }
            merged = {**previous, **draft, **preserved, "draft_id": previous.get("draft_id") or draft["draft_id"], "updated_at": utc_now()}
            merged["history"] = list(previous.get("history") or [])
            merged["history"].append(_history("seed_update", "admin", "Current Bazi knowledge draft seed updated; existing review state preserved."))
            existing[knowledge_id] = merged
            updated += 1
        else:
            existing[knowledge_id] = draft
            imported += 1
    state["knowledge_drafts"] = sorted(existing.values(), key=lambda row: str(row.get("knowledge_id") or ""))
    saved = _save_state(state)
    return {
        "ok": True,
        "status": "seeded",
        "imported_count": imported,
        "updated_count": updated,
        "count": len(state["knowledge_drafts"]),
        "seed_path": str(KNOWLEDGE_DRAFT_SEED_FILE),
        "storage": saved,
        "guardrails": GUARDRAILS + ["DRAFT_ONLY", "NO_RUNTIME_INFERENCE_CHANGE"],
    }


def create_knowledge_draft(payload: Dict[str, Any]) -> Dict[str, Any]:
    state, _ = _load_state()
    knowledge_id = _clean(payload.get("knowledge_id"))
    statement = _clean(payload.get("statement"))
    if not knowledge_id:
        return {"ok": False, "code": "KNOWLEDGE_ID_REQUIRED", "message": "knowledge_id is required."}
    if not statement:
        return {"ok": False, "code": "STATEMENT_REQUIRED", "message": "statement is required."}
    excerpt_ids = _string_list(payload.get("source_excerpt_ids"))
    existing_excerpts = {str(row.get("excerpt_id") or "") for row in state.get("excerpts") or []}
    missing = [item for item in excerpt_ids if item not in existing_excerpts]
    if missing:
        return {"ok": False, "code": "SOURCE_EXCERPT_NOT_FOUND", "message": "source_excerpt_ids not found: " + ", ".join(missing)}
    draft = {
        "draft_id": _clean(payload.get("draft_id")) or "kud_" + uuid.uuid4().hex[:16],
        "knowledge_id": knowledge_id,
        "domain": _clean(payload.get("domain"), "core_structure"),
        "category": _clean(payload.get("category"), "uncategorized"),
        "title": _clean(payload.get("title"), knowledge_id),
        "statement": statement,
        "structured_facts": payload.get("structured_facts") if isinstance(payload.get("structured_facts"), (dict, list)) else {},
        "conditions": payload.get("conditions") if isinstance(payload.get("conditions"), dict) else {},
        "source_excerpt_ids": excerpt_ids,
        "source_refs": _string_list(payload.get("source_refs")),
        "risk_level": _enum(payload.get("risk_level"), ALLOWED_RISK_LEVEL, "R2"),
        "confidence_prior": _bounded_float(payload.get("confidence_prior"), 0.5, 0.0, 1.0),
        "status": "draft",
        "review_status": "pending",
        "review_note": "",
        "allowed_usage": _string_list(payload.get("allowed_usage")) or ["knowledge_unit_draft", "rule_proposal_source"],
        "forbidden_usage": _string_list(payload.get("forbidden_usage")) or ["direct_active_rule", "direct_fortune_output", "runtime_inference_without_proposal"],
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "history": [_history("draft", _clean(payload.get("actor_role"), "admin"), "Knowledge unit draft created; requires proposal before runtime.")],
        "guardrails": GUARDRAILS + ["DRAFT_ONLY", "REQUIRES_RULE_PROPOSAL_BEFORE_RUNTIME"],
    }
    state.setdefault("knowledge_drafts", []).append(draft)
    saved = _save_state(state)
    return {"ok": True, "item": draft, "storage": saved, "guardrails": draft["guardrails"]}


def create_source_record(payload: Dict[str, Any]) -> Dict[str, Any]:
    state, _ = _load_state()
    source = _normalize_source_record(payload, default_status="queued")
    source_id = source["source_id"]
    if any(row.get("source_id") == source_id for row in state.get("sources") or []):
        return {"ok": False, "code": "SOURCE_ID_EXISTS", "message": "source_id already exists."}
    source["created_at"] = utc_now()
    source["updated_at"] = utc_now()
    source["history"] = [_history("created", _clean(payload.get("actor_role"), "admin"), "Source record created manually; no runtime inference change.")]
    state.setdefault("sources", []).append(source)
    saved = _save_state(state)
    return {"ok": True, "item": source, "storage": saved, "guardrails": GUARDRAILS}


def update_source_record_status(source_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    state, _ = _load_state()
    target = None
    for row in state.get("sources") or []:
        if row.get("source_id") == source_id:
            target = row
            break
    if not target:
        return {"ok": False, "code": "SOURCE_NOT_FOUND", "message": "source record not found."}
    status = _clean(payload.get("ingestion_status"), str(target.get("ingestion_status") or "cataloged"))
    if status not in ALLOWED_INGESTION_STATUS:
        return {"ok": False, "code": "INGESTION_STATUS_INVALID", "message": "unsupported ingestion_status."}
    target["ingestion_status"] = status
    target["updated_at"] = utc_now()
    target.setdefault("history", []).append(_history(status, _clean(payload.get("actor_role"), "admin"), _clean(payload.get("note"), "Source status updated; no runtime inference change.")))
    saved = _save_state(state)
    return {"ok": True, "item": target, "storage": saved, "guardrails": GUARDRAILS}


def _load_state() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if SOURCE_ARCHIVE_FILE.exists():
        try:
            state = json.loads(SOURCE_ARCHIVE_FILE.read_text(encoding="utf-8"))
            if isinstance(state, dict):
                state.setdefault("sources", [])
                state.setdefault("excerpts", [])
                state.setdefault("knowledge_drafts", [])
                state.setdefault("guardrails", GUARDRAILS)
                return state, {"backend": "file", "path": str(SOURCE_ARCHIVE_FILE)}
        except Exception:
            pass
    state = {
        "version": SOURCE_ARCHIVE_VERSION,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "runtime_scope": "source_archive_only_no_inference",
        "sources": [_normalize_source_record(item, default_status="cataloged") for item in _load_catalog_sources()],
        "excerpts": [],
        "knowledge_drafts": [],
        "guardrails": GUARDRAILS,
    }
    return state, {"backend": "catalog_fallback", "path": str(CATALOG_FILE)}


def _save_state(state: Dict[str, Any]) -> Dict[str, Any]:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    state["version"] = SOURCE_ARCHIVE_VERSION
    state["updated_at"] = utc_now()
    state["runtime_scope"] = "source_archive_only_no_inference"
    state["guardrails"] = GUARDRAILS
    SOURCE_ARCHIVE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {"backend": "file", "path": str(SOURCE_ARCHIVE_FILE)}


def _load_catalog_sources() -> List[Dict[str, Any]]:
    if not CATALOG_FILE.exists():
        return []
    try:
        data = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []
    sources = data.get("sources") if isinstance(data, dict) else []
    return [dict(item) for item in sources if isinstance(item, dict)]


def _load_knowledge_draft_seeds() -> List[Dict[str, Any]]:
    seed_files = [KNOWLEDGE_DRAFT_SEED_FILE]
    if KNOWLEDGE_DRAFT_SEED_FILE == DEFAULT_KNOWLEDGE_DRAFT_SEED_FILE and KNOWLEDGE_DRAFT_PACK_DIR.exists():
        seed_files.extend(sorted(KNOWLEDGE_DRAFT_PACK_DIR.glob("*_knowledge_draft_seeds_*.json")))
    rows: List[Dict[str, Any]] = []
    for seed_file in seed_files:
        rows.extend(_load_knowledge_draft_seed_file(seed_file))
    return rows


def _load_knowledge_draft_seed_file(seed_file: Path) -> List[Dict[str, Any]]:
    if not seed_file.exists():
        return []
    try:
        data = json.loads(seed_file.read_text(encoding="utf-8"))
    except Exception:
        return []
    rows = data.get("knowledge_drafts") if isinstance(data, dict) else []
    return [dict(item) for item in rows if isinstance(item, dict)]


def _find_knowledge_draft(state: Dict[str, Any], draft_id: str) -> Dict[str, Any] | None:
    key = _clean(draft_id)
    for row in state.get("knowledge_drafts") or []:
        if row.get("draft_id") == key or row.get("knowledge_id") == key:
            return row
    return None


def _draft_to_rule_domain(draft: Dict[str, Any]) -> str:
    domain = _clean(draft.get("domain"))
    category = _clean(draft.get("category"))
    if domain in {"ten_god", "interaction"} or category in {"ten_god", "ten_god_interaction", "ten_god_interaction_mechanism"}:
        return "ten_god_relation"
    if domain == "luck_flow" or category == "timing_context":
        return "time_structure"
    if domain == "wealth":
        return "income_stability"
    if domain in {"five_element", "strength"} or category in {"stem_branch_attribute", "strength_model"}:
        return "day_master_element"
    if domain == "core_structure" and category in {"core_symbol", "hidden_stem", "five_element_relation"}:
        return "day_master_element"
    if domain == "core_structure":
        return "structural_relation"
    return ""


def _draft_input_contract(draft: Dict[str, Any], rule_domain: str) -> List[str]:
    if rule_domain == "ten_god_relation":
        return ["chart.day_master", "chart.pillars"]
    if rule_domain == "time_structure":
        return ["chart", "time_context"]
    if rule_domain == "income_stability":
        return ["chart", "inference_context.income_stability"]
    if rule_domain == "structural_relation":
        return ["chart.pillars", "time_context"]
    return ["chart"]


def _draft_output_signal(draft: Dict[str, Any], rule_domain: str) -> str:
    category = _clean(draft.get("category"), "structure")
    if rule_domain == "income_stability":
        return "income_stability_candidate_feature"
    if rule_domain == "time_structure":
        return "time_context_structure"
    if rule_domain == "ten_god_relation":
        return "ten_god_signal_candidate"
    return category + "_candidate"


def _draft_value_set(rule_domain: str) -> List[str]:
    if rule_domain == "time_structure":
        return ["present", "absent", "unknown"]
    return ["none", "low", "medium", "high", "unknown"]


def _normalize_source_record(payload: Dict[str, Any], *, default_status: str) -> Dict[str, Any]:
    title = _clean(payload.get("title"), "Untitled Bazi Source")
    source_id = _clean(payload.get("source_id")) or "source." + uuid.uuid4().hex[:16]
    source_type = _enum(payload.get("source_type"), ALLOWED_SOURCE_TYPES, "web_reference")
    language = _enum(payload.get("language"), ALLOWED_LANGUAGE, "zh")
    reliability = _enum(payload.get("reliability"), ALLOWED_RELIABILITY, "unknown")
    priority = _enum(payload.get("source_priority"), ALLOWED_SOURCE_PRIORITY, "tertiary")
    risk = _enum(payload.get("risk_level"), ALLOWED_RISK_LEVEL, "R4")
    status = _enum(payload.get("ingestion_status"), ALLOWED_INGESTION_STATUS, default_status)
    return {
        "source_id": source_id,
        "title": title,
        "source_type": source_type,
        "author_or_compiler": _clean(payload.get("author_or_compiler")),
        "period": _clean(payload.get("period")),
        "language": language,
        "url": _clean(payload.get("url")),
        "local_path": _clean(payload.get("local_path")),
        "access_note": _clean(payload.get("access_note")),
        "license_note": _clean(payload.get("license_note")),
        "reliability": reliability,
        "source_priority": priority,
        "knowledge_scope": _string_list(payload.get("knowledge_scope")),
        "risk_level": risk,
        "allowed_usage": _string_list(payload.get("allowed_usage")) or ["source_archive"],
        "forbidden_usage": _string_list(payload.get("forbidden_usage")) or ["direct_active_rule", "direct_fortune_output"],
        "ingestion_status": status,
        "notes": _clean(payload.get("notes")),
        "guardrails": GUARDRAILS,
    }


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _draft_summary(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "draft_id": row.get("draft_id"),
            "knowledge_id": row.get("knowledge_id"),
            "domain": row.get("domain"),
            "category": row.get("category"),
            "risk_level": row.get("risk_level"),
            "review_status": row.get("review_status") or "pending",
            "review_note": row.get("review_note") or "",
        }
        for row in rows[:80]
    ]


def _source_search_text(row: Dict[str, Any]) -> str:
    parts = [row.get("source_id"), row.get("title"), row.get("author_or_compiler"), row.get("period"), row.get("notes")]
    parts.extend(row.get("knowledge_scope") or [])
    return " ".join(str(part or "") for part in parts)


def _excerpt_search_text(row: Dict[str, Any]) -> str:
    parts = [row.get("excerpt_id"), row.get("source_id"), row.get("locator"), row.get("original_excerpt_short"), row.get("normalized_summary")]
    parts.extend(row.get("keywords") or [])
    return " ".join(str(part or "") for part in parts)


def _draft_search_text(row: Dict[str, Any]) -> str:
    parts = [row.get("draft_id"), row.get("knowledge_id"), row.get("domain"), row.get("category"), row.get("title"), row.get("statement")]
    parts.extend(row.get("source_excerpt_ids") or [])
    parts.extend(row.get("source_refs") or [])
    return " ".join(str(part or "") for part in parts)


def _history(status: str, actor_role: str, note: str) -> Dict[str, Any]:
    return {"created_at": utc_now(), "status": status, "actor_role": actor_role, "note": note}


def _enum(value: Any, allowed: set[str], default: str) -> str:
    text = _clean(value, default)
    return text if text in allowed else default


def _string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw = value.split(",")
    elif isinstance(value, list):
        raw = value
    else:
        raw = [value]
    return [_clean(item) for item in raw if _clean(item)]


def _clean(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _bounded_float(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        raw = float(value)
    except (TypeError, ValueError):
        raw = default
    if raw != raw:
        raw = default
    return max(minimum, min(maximum, raw))


def _bounded_int_local(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        raw = int(value)
    except (TypeError, ValueError):
        raw = default
    return max(minimum, min(maximum, raw))
