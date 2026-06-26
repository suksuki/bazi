from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from pydantic import Field

from v30.config import V30Settings, load_settings
from v30.contracts import V30Model
from v30.storage.repository import _default_postgres_connect


DIAGNOSIS_STORAGE_VERSION = "v30.real_bazi_diagnosis.storage.v1"


class DiagnosisStorageWriteResult(V30Model):
    diagnosis_id: str
    reading_id: str
    backend: str
    searchable: bool
    rows: dict[str, int] = Field(default_factory=dict)
    error: str | None = None
    boundary: str = "diagnosis_storage_records_replay_data_not_authoritative_chart_facts"


def upsert_diagnosis_run_sql() -> str:
    return """
INSERT INTO v30_diagnosis_runs (diagnosis_id, reading_id, status, payload)
VALUES (%s, %s, %s, %s::jsonb)
ON CONFLICT (diagnosis_id)
DO UPDATE SET
  reading_id = EXCLUDED.reading_id,
  status = EXCLUDED.status,
  payload = EXCLUDED.payload;
""".strip()


def upsert_diagnosis_rule_match_sql() -> str:
    return """
INSERT INTO v30_diagnosis_rule_matches (rule_match_id, diagnosis_id, reading_id, rule_id, domain_targets, payload)
VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb)
ON CONFLICT (rule_match_id)
DO UPDATE SET
  diagnosis_id = EXCLUDED.diagnosis_id,
  reading_id = EXCLUDED.reading_id,
  rule_id = EXCLUDED.rule_id,
  domain_targets = EXCLUDED.domain_targets,
  payload = EXCLUDED.payload;
""".strip()


def upsert_diagnosis_path_sql() -> str:
    return """
INSERT INTO v30_diagnosis_paths (path_id, diagnosis_id, reading_id, mechanism, domain_targets, payload)
VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb)
ON CONFLICT (diagnosis_id, path_id)
DO UPDATE SET
  reading_id = EXCLUDED.reading_id,
  mechanism = EXCLUDED.mechanism,
  domain_targets = EXCLUDED.domain_targets,
  payload = EXCLUDED.payload;
""".strip()


def upsert_diagnosis_portrait_sql() -> str:
    return """
INSERT INTO v30_diagnosis_portraits (portrait_id, diagnosis_id, reading_id, domain, dimension, payload)
VALUES (%s, %s, %s, %s, %s, %s::jsonb)
ON CONFLICT (diagnosis_id, portrait_id)
DO UPDATE SET
  reading_id = EXCLUDED.reading_id,
  domain = EXCLUDED.domain,
  dimension = EXCLUDED.dimension,
  payload = EXCLUDED.payload;
""".strip()


def upsert_diagnosis_claim_sql() -> str:
    return """
INSERT INTO v30_diagnosis_claims (claim_id, diagnosis_id, reading_id, domain, claim_level, payload)
VALUES (%s, %s, %s, %s, %s, %s::jsonb)
ON CONFLICT (diagnosis_id, claim_id)
DO UPDATE SET
  reading_id = EXCLUDED.reading_id,
  domain = EXCLUDED.domain,
  claim_level = EXCLUDED.claim_level,
  payload = EXCLUDED.payload;
""".strip()


def insert_diagnosis_feedback_sql() -> str:
    return """
INSERT INTO v30_diagnosis_feedback (feedback_id, diagnosis_id, reading_id, payload)
VALUES (%s, %s, %s, %s::jsonb)
ON CONFLICT (feedback_id)
DO UPDATE SET
  diagnosis_id = EXCLUDED.diagnosis_id,
  reading_id = EXCLUDED.reading_id,
  payload = EXCLUDED.payload;
""".strip()


def select_diagnosis_run_sql() -> str:
    return "SELECT payload FROM v30_diagnosis_runs WHERE diagnosis_id = %s;"


def select_latest_diagnosis_run_sql() -> str:
    return """
SELECT payload FROM v30_diagnosis_runs
WHERE reading_id = %s
ORDER BY created_at DESC
LIMIT 1;
""".strip()


def diagnosis_id_for_payload(payload: dict[str, Any]) -> str:
    reading_id = str(payload.get("reading_id") or "")
    version = str(payload.get("version") or "v30.real_bazi_diagnosis.runtime_integration.v1")
    if not reading_id:
        raise ValueError("diagnosis payload requires reading_id")
    return str(payload.get("diagnosis_id") or f"{reading_id}:real-bazi-diagnosis:{version}")


def diagnosis_storage_record(payload: dict[str, Any]) -> dict[str, Any]:
    diagnosis_id = diagnosis_id_for_payload(payload)
    reading_id = str(payload.get("reading_id") or "")
    return {
        "version": DIAGNOSIS_STORAGE_VERSION,
        "table": "v30_diagnosis_runs",
        "diagnosis_id": diagnosis_id,
        "reading_id": reading_id,
        "status": str(payload.get("status") or "unknown"),
        "claim_count": len(_dict_rows(payload.get("claims"))),
        "path_count": len(_dict_rows(payload.get("paths"))),
        "portrait_count": len(_dict_rows(payload.get("portraits"))),
        "rule_match_count": len(_dict_rows(payload.get("matched_rules"))),
        "storage_policy": payload.get("storage_policy", {}),
        "authoritative_facts_stored_here": False,
        "boundary": "diagnosis_storage_record_indexes_rbd_replay_not_chart_facts",
    }


def write_real_bazi_diagnosis_to_postgres(
    diagnosis_payload: dict[str, Any],
    *,
    settings: V30Settings | None = None,
    connect: Callable[[str], Any] | None = None,
) -> DiagnosisStorageWriteResult:
    settings = settings or load_settings()
    diagnosis_id = diagnosis_id_for_payload(diagnosis_payload)
    reading_id = str(diagnosis_payload.get("reading_id") or "")
    if not settings.database_url:
        return DiagnosisStorageWriteResult(
            diagnosis_id=diagnosis_id,
            reading_id=reading_id,
            backend="json_fallback",
            searchable=False,
            rows=_row_counts(diagnosis_payload, persisted=False),
        )
    rows = _row_counts(diagnosis_payload, persisted=False)
    try:
        with (connect or _default_postgres_connect)(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL lock_timeout = '10s';", ())
                cursor.execute("SET LOCAL statement_timeout = '120s';", ())
                cursor.execute(
                    upsert_diagnosis_run_sql(),
                    (
                        diagnosis_id,
                        reading_id,
                        str(diagnosis_payload.get("status") or "unknown"),
                        json.dumps(diagnosis_payload, ensure_ascii=False),
                    ),
                )
                rows["diagnosis_runs"] = 1
                for rule in _dict_rows(diagnosis_payload.get("matched_rules")):
                    cursor.execute(
                        upsert_diagnosis_rule_match_sql(),
                        (
                            str(rule.get("rule_match_id") or ""),
                            diagnosis_id,
                            reading_id,
                            str(rule.get("rule_id") or ""),
                            json.dumps(rule.get("domain_targets") or [], ensure_ascii=False),
                            json.dumps(rule, ensure_ascii=False),
                        ),
                    )
                    rows["rule_matches"] += 1
                for path in _dict_rows(diagnosis_payload.get("paths")):
                    cursor.execute(
                        upsert_diagnosis_path_sql(),
                        (
                            str(path.get("path_id") or ""),
                            diagnosis_id,
                            reading_id,
                            str(path.get("mechanism") or ""),
                            json.dumps(path.get("domain_targets") or [], ensure_ascii=False),
                            json.dumps(path, ensure_ascii=False),
                        ),
                    )
                    rows["paths"] += 1
                for portrait in _dict_rows(diagnosis_payload.get("portraits")):
                    cursor.execute(
                        upsert_diagnosis_portrait_sql(),
                        (
                            str(portrait.get("portrait_id") or ""),
                            diagnosis_id,
                            reading_id,
                            str(portrait.get("domain") or ""),
                            str(portrait.get("dimension") or ""),
                            json.dumps(portrait, ensure_ascii=False),
                        ),
                    )
                    rows["portraits"] += 1
                for claim in _dict_rows(diagnosis_payload.get("claims")):
                    cursor.execute(
                        upsert_diagnosis_claim_sql(),
                        (
                            str(claim.get("claim_id") or ""),
                            diagnosis_id,
                            reading_id,
                            str(claim.get("domain") or ""),
                            str(claim.get("claim_level") or ""),
                            json.dumps(claim, ensure_ascii=False),
                        ),
                    )
                    rows["claims"] += 1
            connection.commit()
    except Exception as exc:  # pragma: no cover - depends on external DB state.
        return DiagnosisStorageWriteResult(
            diagnosis_id=diagnosis_id,
            reading_id=reading_id,
            backend="postgres_unavailable",
            searchable=False,
            rows=rows,
            error=str(exc),
        )
    return DiagnosisStorageWriteResult(
        diagnosis_id=diagnosis_id,
        reading_id=reading_id,
        backend="postgres",
        searchable=True,
        rows=rows,
    )


def query_latest_real_bazi_diagnosis_from_postgres(
    *,
    reading_id: str,
    settings: V30Settings | None = None,
    connect: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    settings = settings or load_settings()
    if not settings.database_url:
        return {
            "version": DIAGNOSIS_STORAGE_VERSION,
            "backend": "json_fallback",
            "searchable": False,
            "payload": {},
            "error": None,
        }
    try:
        with (connect or _default_postgres_connect)(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(select_latest_diagnosis_run_sql(), (reading_id,))
                row = cursor.fetchone()
        return {
            "version": DIAGNOSIS_STORAGE_VERSION,
            "backend": "postgres",
            "searchable": True,
            "payload": row[0] if row else {},
            "error": None,
        }
    except Exception as exc:  # pragma: no cover - depends on external DB state.
        return {
            "version": DIAGNOSIS_STORAGE_VERSION,
            "backend": "postgres_unavailable",
            "searchable": False,
            "payload": {},
            "error": str(exc),
        }


def _row_counts(payload: dict[str, Any], *, persisted: bool) -> dict[str, int]:
    return {
        "diagnosis_runs": 1 if persisted else 0,
        "rule_matches": 0 if not persisted else len(_dict_rows(payload.get("matched_rules"))),
        "paths": 0 if not persisted else len(_dict_rows(payload.get("paths"))),
        "portraits": 0 if not persisted else len(_dict_rows(payload.get("portraits"))),
        "claims": 0 if not persisted else len(_dict_rows(payload.get("claims"))),
    }


def _dict_rows(value: Any) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []
