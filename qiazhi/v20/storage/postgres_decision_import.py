from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from v20.learning.decision_registry_review import read_decision_registry_review_artifact

TARGET_TABLE = "v20_decision_registry"


def build_decision_registry_postgres_import_plan(
    *,
    apply: bool = False,
    batch_size: int = 500,
    database_url: str | None = None,
    artifact_dir: Path | None = None,
) -> dict[str, object]:
    artifact = read_decision_registry_review_artifact(output_dir=artifact_dir)
    records = [row for row in artifact.get("records", ()) if isinstance(row, dict)]
    url = database_url if database_url is not None else os.getenv("V20_DATABASE_URL", "")
    payload = {
        "version": "v20.decision_registry_postgres_import_plan.v1",
        "source_status": artifact.get("status", "not_built"),
        "source_path": artifact.get("latest_path", ""),
        "target_table": TARGET_TABLE,
        "record_count": len(records),
        "apply": apply,
        "batch_size": batch_size,
        "database_url_present": bool(url),
        "runtime_mutation": bool(apply),
        "guardrails": [
            "EXPLICIT_APPLY_REQUIRED",
            "NO_SECRET_VALUES_RENDERED",
            "REVIEW_RECORDS_ARE_NOT_RUNTIME_PROMOTIONS",
            "APPEND_OR_UPSERT_ONLY",
        ],
    }
    if artifact.get("status") == "not_built":
        return payload | {"status": "blocked_missing_decision_registry_review_artifact", "imported_or_updated": 0}
    if not apply:
        return payload | {"status": "dry_run", "imported_or_updated": 0}
    return _apply_decision_registry_import(payload, records, url, batch_size)


def _apply_decision_registry_import(
    payload: dict[str, object],
    records: list[dict[str, Any]],
    database_url: str,
    batch_size: int,
) -> dict[str, object]:
    if not database_url:
        return payload | {"status": "blocked_missing_V20_DATABASE_URL", "imported_or_updated": 0}
    try:
        import psycopg2
        from psycopg2.extras import Json, execute_values
    except Exception as exc:
        return payload | {"status": "blocked_missing_psycopg2", "error": str(exc), "imported_or_updated": 0}

    imported = 0
    try:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                _ensure_table(cur)
                batch = []
                for record in records:
                    batch.append(_postgres_row(record, Json))
                    if len(batch) >= batch_size:
                        imported += _insert_batch(cur, execute_values, batch)
                        batch.clear()
                if batch:
                    imported += _insert_batch(cur, execute_values, batch)
            conn.commit()
    except Exception as exc:
        return payload | {"status": "blocked_postgres_error", "error": str(exc), "imported_or_updated": imported}
    return payload | {"status": "imported", "imported_or_updated": imported}


def _postgres_row(record: dict[str, Any], json_type) -> tuple[object, ...]:
    return (
        str(record.get("decision_id", "")),
        str(record.get("subject_id", "")),
        str(record.get("decision_status", "needs_human_review")),
        json_type(record),
    )


def _ensure_table(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS v20_decision_registry (
          decision_id text PRIMARY KEY,
          subject_id text NOT NULL,
          decision_status text NOT NULL,
          created_at timestamptz NOT NULL DEFAULT now(),
          updated_at timestamptz NOT NULL DEFAULT now(),
          payload jsonb NOT NULL
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_v20_decision_registry_subject_id ON v20_decision_registry(subject_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_v20_decision_registry_status ON v20_decision_registry(decision_status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_v20_decision_registry_payload_gin ON v20_decision_registry USING gin (payload)")


def _insert_batch(cur, execute_values, batch: list[tuple[object, ...]]) -> int:
    execute_values(
        cur,
        """
        INSERT INTO v20_decision_registry (decision_id, subject_id, decision_status, payload)
        VALUES %s
        ON CONFLICT (decision_id) DO UPDATE SET
          subject_id = EXCLUDED.subject_id,
          decision_status = EXCLUDED.decision_status,
          payload = EXCLUDED.payload,
          updated_at = now()
        """,
        batch,
    )
    return len(batch)
