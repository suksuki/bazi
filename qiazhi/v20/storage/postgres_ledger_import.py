from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env

ALLOWED_LEDGER_NAMES = (
    "feedback_ledger",
    "portrait_calibration_ledger",
    "practitioner_calibration_ledger",
    "latent_event_calibration_ledger",
    "orchestrator_memory_ledger",
    "orchestrator_policy_observability_ledger",
    "orchestrator_policy_rollback_audit",
)
TARGET_TABLE = "v20_feedback_ledger"


def build_ledger_postgres_import_plan(
    *,
    ledger_name: str,
    apply: bool = False,
    batch_size: int = 500,
    database_url: str | None = None,
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    _validate_ledger_name(ledger_name)
    storage = store or local_jsonl_store_from_env()
    records = _read_ledger_records(storage, ledger_name)
    url = database_url if database_url is not None else os.getenv("V20_DATABASE_URL", "")
    payload = {
        "version": "v20.ledger_postgres_import_plan.v1",
        "ledger_name": ledger_name,
        "source_path": str(_ledger_path(storage, ledger_name)),
        "target_table": TARGET_TABLE,
        "record_count": len(records),
        "apply": apply,
        "batch_size": batch_size,
        "database_url_present": bool(url),
        "runtime_mutation": bool(apply),
        "guardrails": [
            "EXPLICIT_APPLY_REQUIRED",
            "NO_SECRET_VALUES_RENDERED",
            "LOCAL_LEDGER_TO_POSTGRES_AUTHORITY",
            "APPEND_OR_UPSERT_ONLY",
        ],
    }
    if not apply:
        return payload | {"status": "dry_run"}
    return _apply_ledger_import(payload, records, url, batch_size)


def _apply_ledger_import(
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


def _read_ledger_records(store: LocalJsonlStore, ledger_name: str) -> list[dict[str, Any]]:
    path = _ledger_path(store, ledger_name)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            rows.append(record)
    return rows


def _postgres_row(record: dict[str, Any], json_type) -> tuple[object, ...]:
    payload = record.get("payload", {})
    source_hash = payload.get("source_hash", "") if isinstance(payload, dict) else ""
    return (
        str(record.get("record_id", "")),
        str(source_hash),
        "recorded_only",
        json_type(record),
    )


def _ensure_table(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS v20_feedback_ledger (
          feedback_id text PRIMARY KEY,
          source_hash text NOT NULL,
          calibration_status text NOT NULL,
          created_at timestamptz NOT NULL DEFAULT now(),
          updated_at timestamptz NOT NULL DEFAULT now(),
          payload jsonb NOT NULL
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_v20_feedback_ledger_source_hash ON v20_feedback_ledger(source_hash)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_v20_feedback_ledger_payload_gin ON v20_feedback_ledger USING gin (payload)")


def _insert_batch(cur, execute_values, batch: list[tuple[object, ...]]) -> int:
    execute_values(
        cur,
        """
        INSERT INTO v20_feedback_ledger (feedback_id, source_hash, calibration_status, payload)
        VALUES %s
        ON CONFLICT (feedback_id) DO UPDATE SET
          source_hash = EXCLUDED.source_hash,
          calibration_status = EXCLUDED.calibration_status,
          payload = EXCLUDED.payload,
          updated_at = now()
        """,
        batch,
    )
    return len(batch)


def _ledger_path(store: LocalJsonlStore, ledger_name: str) -> Path:
    return store.runtime_dir / "ledger" / f"{ledger_name}.jsonl"


def _validate_ledger_name(ledger_name: str) -> None:
    if ledger_name not in ALLOWED_LEDGER_NAMES:
        raise ValueError(f"Unsupported ledger import: {ledger_name}")
