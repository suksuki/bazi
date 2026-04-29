from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

from v19.runtime import RUNTIME, utc_now

RULE_DB_VERSION = "v19.bazi_rule_db.v1"
RULE_DB_FILE = RUNTIME / "bazi_rule_db.json"
SOURCE_ARCHIVE_FILE = RUNTIME / "bazi_source_archive.json"

GUARDRAILS = [
    "RULE_DB_INGESTION",
    "NO_LLM_AUTHORITY",
    "NO_PLUGIN_BLACK_BOX",
    "R4_ARCHIVE_ONLY",
]


def bazi_rule_db_status() -> Dict[str, Any]:
    state, storage = _load_state()
    rules = list(state.get("rules") or [])
    return {
        "ok": True,
        "version": RULE_DB_VERSION,
        "storage": storage,
        "runtime_scope": "rule_database_available_for_engine_adapter",
        "counts": {
            "rules": len(rules),
            "by_domain": _count_by(rules, "domain"),
            "by_risk_level": _count_by(rules, "risk_level"),
            "by_status": _count_by(rules, "status"),
            "engine_enabled": len([row for row in rules if row.get("engine_enabled") is True]),
        },
        "guardrails": GUARDRAILS,
    }


def list_bazi_rules(*, domain: str = "", risk_level: str = "", q: str = "") -> Dict[str, Any]:
    state, storage = _load_state()
    rows = [dict(row) for row in state.get("rules") or []]
    if domain:
        rows = [row for row in rows if row.get("domain") == domain]
    if risk_level:
        rows = [row for row in rows if row.get("risk_level") == risk_level]
    if q:
        needle = q.lower().strip()
        rows = [row for row in rows if _rule_search_text(row).lower().find(needle) >= 0]
    rows.sort(key=lambda row: (str(row.get("domain") or ""), str(row.get("rule_id") or "")))
    return {
        "ok": True,
        "count": len(rows),
        "items": rows[:500],
        "storage": storage,
        "runtime_scope": "rule_database_available_for_engine_adapter",
        "guardrails": GUARDRAILS,
    }


def ingest_current_knowledge_drafts_to_rule_db(*, force: bool = False, enable_engine: bool = True) -> Dict[str, Any]:
    source = _load_source_archive()
    drafts = [dict(row) for row in source.get("knowledge_drafts") or []]
    state, _ = _load_state()
    if force:
        state["rules"] = []
    existing = {str(row.get("rule_id") or ""): row for row in state.get("rules") or []}
    imported = 0
    updated = 0
    blocked = []
    for draft in drafts:
        risk = _clean(draft.get("risk_level"), "R4")
        review_status = _clean(draft.get("review_status"), "pending")
        knowledge_id = _clean(draft.get("knowledge_id"))
        if not knowledge_id:
            continue
        if risk == "R4":
            blocked.append({"knowledge_id": knowledge_id, "reason": "R4_ARCHIVE_ONLY"})
            continue
        if review_status in {"rejected", "deprecated"}:
            blocked.append({"knowledge_id": knowledge_id, "reason": "DRAFT_REJECTED_OR_DEPRECATED"})
            continue
        rule = _rule_from_draft(draft, enable_engine=enable_engine)
        rule_id = rule["rule_id"]
        if rule_id in existing:
            merged = {**existing[rule_id], **rule, "rule_record_id": existing[rule_id].get("rule_record_id") or rule["rule_record_id"], "updated_at": utc_now()}
            merged.setdefault("history", []).append(_history("updated_from_draft", "system", "Rule DB record updated from knowledge draft ingestion."))
            existing[rule_id] = merged
            updated += 1
        else:
            existing[rule_id] = rule
            imported += 1
    state["rules"] = sorted(existing.values(), key=lambda row: str(row.get("rule_id") or ""))
    state["last_ingestion"] = {
        "created_at": utc_now(),
        "source": str(SOURCE_ARCHIVE_FILE),
        "draft_count": len(drafts),
        "imported_count": imported,
        "updated_count": updated,
        "blocked_count": len(blocked),
        "blocked": blocked,
        "enable_engine": enable_engine,
    }
    saved = _save_state(state)
    return {
        "ok": True,
        "status": "ingested",
        "draft_count": len(drafts),
        "imported_count": imported,
        "updated_count": updated,
        "blocked_count": len(blocked),
        "blocked": blocked,
        "rule_count": len(state["rules"]),
        "storage": saved,
        "guardrails": GUARDRAILS,
    }


def _rule_from_draft(draft: Dict[str, Any], *, enable_engine: bool) -> Dict[str, Any]:
    knowledge_id = _clean(draft.get("knowledge_id"))
    domain = _draft_to_rule_domain(draft)
    rule_id = "v19.rule." + knowledge_id
    now = utc_now()
    return {
        "rule_record_id": "brr_" + uuid.uuid4().hex[:16],
        "rule_id": rule_id,
        "knowledge_id": knowledge_id,
        "source_draft_id": _clean(draft.get("draft_id")),
        "domain": domain,
        "category": _clean(draft.get("category"), "uncategorized"),
        "title": _clean(draft.get("title"), knowledge_id),
        "statement": _clean(draft.get("statement")),
        "risk_level": _clean(draft.get("risk_level"), "R2"),
        "status": "active_in_rule_db",
        "engine_enabled": enable_engine,
        "engine_adapter_status": "available_for_structural_signal_adapter",
        "input_contract": {"required": _draft_input_contract(draft, domain)},
        "condition": {
            "structured_facts": draft.get("structured_facts") or {},
            "conditions": draft.get("conditions") or {},
            "category": draft.get("category"),
            "risk_level": draft.get("risk_level"),
        },
        "output_contract": {
            "signal": _draft_output_signal(draft, domain),
            "value_set": _draft_value_set(domain),
            "is_prediction": False,
            "prediction_scope": "structural_rule_signal",
        },
        "reasoning_path": [
            "load active_in_rule_db record",
            "match structured facts against chart/time context",
            "emit structural rule signal with attribution",
        ],
        "evidence": {
            "source_refs": draft.get("source_refs") or [],
            "source_excerpt_ids": draft.get("source_excerpt_ids") or [],
            "source_draft_id": draft.get("draft_id"),
            "review_status": draft.get("review_status") or "pending",
            "review_note": draft.get("review_note") or "",
        },
        "confidence": _bounded_float(draft.get("confidence_prior"), 0.5, 0.0, 1.0),
        "allowed_usage": draft.get("allowed_usage") or ["rule_db", "engine_adapter_candidate"],
        "forbidden_usage": draft.get("forbidden_usage") or ["direct_fortune_output", "traditional_prediction_text"],
        "created_at": now,
        "updated_at": now,
        "history": [_history("ingested", "system", "Directly ingested from V19 knowledge draft into Bazi Rule DB.")],
        "guardrails": GUARDRAILS,
    }


def _load_state() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if RULE_DB_FILE.exists():
        try:
            state = json.loads(RULE_DB_FILE.read_text(encoding="utf-8"))
            if isinstance(state, dict):
                state.setdefault("rules", [])
                state.setdefault("guardrails", GUARDRAILS)
                return state, {"backend": "file", "path": str(RULE_DB_FILE)}
        except Exception:
            pass
    return {
        "version": RULE_DB_VERSION,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "rules": [],
        "guardrails": GUARDRAILS,
    }, {"backend": "file", "path": str(RULE_DB_FILE)}


def _save_state(state: Dict[str, Any]) -> Dict[str, Any]:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    state["version"] = RULE_DB_VERSION
    state["updated_at"] = utc_now()
    state["guardrails"] = GUARDRAILS
    RULE_DB_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {"backend": "file", "path": str(RULE_DB_FILE)}


def _load_source_archive() -> Dict[str, Any]:
    if not SOURCE_ARCHIVE_FILE.exists():
        return {"knowledge_drafts": []}
    try:
        data = json.loads(SOURCE_ARCHIVE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"knowledge_drafts": []}
    return data if isinstance(data, dict) else {"knowledge_drafts": []}


def _draft_to_rule_domain(draft: Dict[str, Any]) -> str:
    domain = _clean(draft.get("domain"))
    category = _clean(draft.get("category"))
    if domain == "ten_god" or category == "ten_god":
        return "ten_god_relation"
    if domain == "luck_flow" or category == "timing_context":
        return "time_structure"
    if domain == "wealth":
        return "income_stability"
    if domain in {"five_element", "strength"} or category in {"stem_branch_attribute", "strength_model"}:
        return "day_master_element"
    if domain == "core_structure" and category in {"core_symbol", "hidden_stem", "five_element_relation"}:
        return "day_master_element"
    return "structural_relation"


def _draft_input_contract(draft: Dict[str, Any], domain: str) -> List[str]:
    if domain == "ten_god_relation":
        return ["chart.day_master", "chart.pillars"]
    if domain == "time_structure":
        return ["chart", "time_context"]
    if domain == "income_stability":
        return ["chart", "inference_context.income_stability"]
    if domain == "structural_relation":
        return ["chart.pillars", "time_context"]
    return ["chart"]


def _draft_output_signal(draft: Dict[str, Any], domain: str) -> str:
    category = _clean(draft.get("category"), "structure")
    if domain == "income_stability":
        return "income_stability_rule_feature"
    if domain == "time_structure":
        return "time_context_structure"
    if domain == "ten_god_relation":
        return "ten_god_signal"
    return category + "_signal"


def _draft_value_set(domain: str) -> List[str]:
    if domain == "time_structure":
        return ["present", "absent", "unknown"]
    return ["none", "low", "medium", "high", "unknown"]


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _rule_search_text(row: Dict[str, Any]) -> str:
    parts = [row.get("rule_id"), row.get("knowledge_id"), row.get("domain"), row.get("category"), row.get("title"), row.get("statement")]
    return " ".join(str(part or "") for part in parts)


def _history(status: str, actor_role: str, note: str) -> Dict[str, Any]:
    return {"created_at": utc_now(), "status": status, "actor_role": actor_role, "note": note}


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
