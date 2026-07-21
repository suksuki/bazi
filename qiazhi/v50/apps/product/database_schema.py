from __future__ import annotations

import hashlib
import threading
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "deploy" / "postgres_v50_schema.sql"

_schema_lock = threading.Lock()
_applied_databases: set[str] = set()


def product_schema_hash() -> str:
    return hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest()


def ensure_product_database_schema(database_url: str) -> None:
    """Apply the single checked-in V50 schema owner once per process/database."""

    database_key = database_url.strip()
    if not database_key or database_key in _applied_databases:
        return
    with _schema_lock:
        if database_key in _applied_databases:
            return
        import psycopg

        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        with psycopg.connect(database_key) as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
        _applied_databases.add(database_key)
