from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from v19.knowledge import KnowledgeKernel, KnowledgeKernelError
from v19.knowledge.seeds import core_seed_units
from v19.runtime import RUNTIME, _postgres_connection, resolve_postgres_url, utc_now

KNOWLEDGE_FILE = RUNTIME / "knowledge_units.json"


def seed_knowledge(settings: Dict[str, Any] | None = None, *, force: bool = False) -> Dict[str, Any]:
    existing, storage = _load_units(settings)

    kernel = KnowledgeKernel()
    records: Dict[str, Dict[str, Any]] = dict(existing)
    skipped: List[str] = []
    for payload in core_seed_units():
        knowledge_id = str(payload.get("knowledge_id") or "")
        if knowledge_id in records and not force:
            continue
        try:
            unit = kernel.register_unit(payload, actor="v19_seed")
            reviewed = kernel.review_unit(unit["knowledge_id"], reviewer="v19_seed")
            template = kernel.compile_evidence_template(unit["knowledge_id"])
            records[reviewed["knowledge_id"]] = {"unit": reviewed, "template": template}
        except KnowledgeKernelError:
            skipped.append(str(payload.get("knowledge_id") or ""))
    saved = _save_units(records, settings)
    status = "seeded" if len(records) != len(existing) or force else "already_seeded"
    return {"ok": True, "status": status, "count": len(records), "skipped": skipped, "storage": saved}


def list_knowledge_units(settings: Dict[str, Any] | None = None, *, domain: str = "", q: str = "") -> Dict[str, Any]:
    records = _ensure_seeded(settings)
    rows = [_public_record(record) for record in records.values()]
    if domain:
        rows = [row for row in rows if row.get("domain") == domain]
    query = _norm(q)
    if query:
        rows = [row for row in rows if query in _search_blob(row)]
    rows.sort(key=lambda row: str(row.get("knowledge_id") or ""))
    return {"ok": True, "count": len(rows), "items": rows}


def retrieve_knowledge(structure_payload: Dict[str, Any], user_message: str, settings: Dict[str, Any] | None = None, *, limit: int = 6) -> Dict[str, Any]:
    records = _ensure_seeded(settings)
    keywords = _context_keywords(structure_payload, user_message)
    scored: List[Tuple[int, Dict[str, Any]]] = []
    for record in records.values():
        row = _public_record(record)
        blob = _search_blob(row)
        score = 0
        knowledge_id = str(row.get("knowledge_id") or "")
        for keyword in keywords:
            if keyword and keyword in blob:
                score += 4 if keyword in {"flow_year", "luck_cycle", "income_stability", "大运", "流年"} else 2
        if "income_stability" in keywords and knowledge_id == "wealth.income_stability_rule_basis":
            score += 12
        if structure_payload.get("inference_context") and knowledge_id == "wealth.income_stability_rule_basis":
            score += 6
        domain = str(row.get("domain") or "")
        if domain in {"core_structure", "five_element"}:
            score += 1
        if structure_payload.get("time_context") and domain == "luck_flow":
            score += 3
        if "income" in _norm(user_message) and domain in {"ten_god", "strength", "theme_mapping"}:
            score += 3
        if score > 0:
            scored.append((score, row))
    if not scored:
        scored = [(1, _public_record(record)) for record in records.values()]
    scored.sort(key=lambda pair: (-pair[0], str(pair[1].get("knowledge_id") or "")))
    items = [{**row, "match_score": score} for score, row in scored[:limit]]
    return {
        "enabled": True,
        "mode": "reviewed_evidence_templates_only",
        "runtime_scope": "agent_context_not_prediction",
        "guardrails": ["NO_DIRECT_PREDICTION", "NO_SCORE", "NO_FORTUNE", "NO_TRADITIONAL_NARRATIVE"],
        "query_keywords": keywords,
        "items": items,
    }


def knowledge_status(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    records, storage = _load_units(settings)
    return {"ok": True, "count": len(records), "storage": storage, "path": str(KNOWLEDGE_FILE)}


def _ensure_seeded(settings: Dict[str, Any] | None = None) -> Dict[str, Dict[str, Any]]:
    records, _ = _load_units(settings)
    seed_ids = {str(row.get("knowledge_id") or "") for row in core_seed_units()}
    if records and seed_ids <= set(records.keys()):
        return records
    seed_knowledge(settings)
    records, _ = _load_units(settings)
    return records


def _public_record(record: Dict[str, Any]) -> Dict[str, Any]:
    unit = dict(record.get("unit") or {})
    template = dict(record.get("template") or {})
    conditions = dict(unit.get("conditions") or {})
    return {
        "knowledge_id": unit.get("knowledge_id"),
        "domain": unit.get("domain"),
        "title": unit.get("title"),
        "statement": unit.get("statement"),
        "status": unit.get("status"),
        "confidence_prior": unit.get("confidence_prior"),
        "structured_facts": list(conditions.get("structured_facts") or []),
        "keywords": list(conditions.get("keywords") or []),
        "forbidden_usage": list(conditions.get("forbidden_usage") or []),
        "evidence_type": template.get("evidence_type"),
        "guardrails": list(template.get("guardrails") or []),
        "source_refs": list(unit.get("source_refs") or []),
    }


def _context_keywords(structure_payload: Dict[str, Any], user_message: str) -> List[str]:
    raw = _norm(user_message)
    words = {item for item in raw.replace("/", " ").replace("_", " ").split() if item}
    for key in ["income", "income_stability", "stability", "流年", "大运", "四柱", "十神", "冲", "合"]:
        if key.lower() in raw:
            words.add(key.lower())
    if structure_payload.get("chart"):
        words.update(["chart", "pillar", "四柱", "stem", "branch"])
    time_context = structure_payload.get("time_context") if isinstance(structure_payload.get("time_context"), dict) else {}
    if time_context.get("flow_year"):
        words.update(["flow_year", "流年", "relation", "冲", "合"])
    if time_context.get("luck_cycle"):
        words.update(["luck_cycle", "大运", "relation"])
    return sorted(words)[:24]


def _search_blob(row: Dict[str, Any]) -> str:
    return _norm(json.dumps(row, ensure_ascii=False, sort_keys=True))


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _load_units(settings: Dict[str, Any] | None = None) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    db = dict((settings or {}).get("db") or {})
    url = resolve_postgres_url(db) if db.get("enabled") else ""
    if url:
        try:
            with _postgres_connection(url) as conn:
                _ensure_db_schema(conn)
                return _db_load_units(conn), {"backend": "postgres"}
        except Exception as exc:
            records = _file_load_units()
            return records, {"backend": "file", "fallback_reason": str(exc)}
    return _file_load_units(), {"backend": "file"}


def _save_units(records: Dict[str, Dict[str, Any]], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    db = dict((settings or {}).get("db") or {})
    url = resolve_postgres_url(db) if db.get("enabled") else ""
    _file_save_units(records)
    if url:
        try:
            with _postgres_connection(url) as conn:
                _ensure_db_schema(conn)
                _db_save_units(conn, records)
            return {"backend": "postgres", "fallback": "file_mirror"}
        except Exception as exc:
            return {"backend": "file", "fallback_reason": str(exc)}
    return {"backend": "file"}


def _file_load_units() -> Dict[str, Dict[str, Any]]:
    if not KNOWLEDGE_FILE.exists():
        return {}
    try:
        payload = json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {str(key): dict(value) for key, value in payload.items() if isinstance(value, dict)}


def _file_save_units(records: Dict[str, Dict[str, Any]]) -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _ensure_db_schema(conn: Any) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS v19_knowledge_units (
                knowledge_id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                status TEXT NOT NULL,
                payload JSONB NOT NULL,
                updated_at TIMESTAMPTZ
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_v19_knowledge_units_domain ON v19_knowledge_units(domain)")
    conn.commit()


def _db_load_units(conn: Any) -> Dict[str, Dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute("SELECT knowledge_id, payload FROM v19_knowledge_units ORDER BY knowledge_id")
        rows = cur.fetchall()
    records: Dict[str, Dict[str, Any]] = {}
    for knowledge_id, payload in rows:
        records[str(knowledge_id)] = dict(json.loads(payload) if isinstance(payload, str) else payload)
    return records


def _db_save_units(conn: Any, records: Dict[str, Dict[str, Any]]) -> None:
    with conn.cursor() as cur:
        for knowledge_id, record in records.items():
            unit = dict(record.get("unit") or {})
            cur.execute(
                """
                INSERT INTO v19_knowledge_units (knowledge_id, domain, status, payload, updated_at)
                VALUES (%s, %s, %s, %s::jsonb, %s)
                ON CONFLICT (knowledge_id)
                DO UPDATE SET domain = EXCLUDED.domain, status = EXCLUDED.status, payload = EXCLUDED.payload, updated_at = EXCLUDED.updated_at
                """,
                (knowledge_id, unit.get("domain") or "", unit.get("status") or "", json.dumps(record, ensure_ascii=False, sort_keys=True), utc_now()),
            )
    conn.commit()
