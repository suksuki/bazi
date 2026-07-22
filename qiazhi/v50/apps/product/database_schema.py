from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "deploy" / "postgres_v50_schema.sql"
EXPECTED_SCHEMA_VERSION = "v50.consolidated.003"
EXPECTED_SCHEMA_BOUNDARY = "v50_database_single_migration_owner"
MIGRATION_COMMAND = (
    'PYTHONPATH=packages:apps python scripts/v50_migrate_product_database.py '
    'apply --database-url "$V50_DATABASE_URL"'
)

_schema_lock = threading.Lock()
_verified_databases: set[str] = set()


class ProductDatabaseSchemaError(RuntimeError):
    pass


class ProductDatabaseSchemaMismatch(ProductDatabaseSchemaError):
    pass


class ProductDatabaseMigrationError(ProductDatabaseSchemaError):
    pass


@dataclass(frozen=True)
class ProductDatabaseSchemaStatus:
    ready: bool
    version: str | None
    boundary: str | None
    reason: str


def product_schema_hash() -> str:
    return hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest()


def inspect_product_database_schema(database_url: str) -> ProductDatabaseSchemaStatus:
    """Read the installed schema identity without modifying the database."""

    database_key = _database_key(database_url)
    with _connect(database_key) as conn:
        with conn.cursor() as cur:
            return _read_schema_status(cur)


def check_product_database_schema(database_url: str) -> ProductDatabaseSchemaStatus:
    """Fail fast when the installed schema is missing or not the expected version."""

    database_key = _database_key(database_url)
    if database_key in _verified_databases:
        return _ready_status()
    with _schema_lock:
        if database_key in _verified_databases:
            return _ready_status()
        status = inspect_product_database_schema(database_key)
        if not status.ready:
            raise ProductDatabaseSchemaMismatch(_mismatch_message(status))
        _verified_databases.add(database_key)
        return status


def migrate_product_database_schema(database_url: str) -> ProductDatabaseSchemaStatus:
    """Apply the checked-in schema in one explicit database transaction."""

    database_key = _database_key(database_url)
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    try:
        with _connect(database_key) as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
                status = _read_schema_status(cur)
                if not status.ready:
                    raise ProductDatabaseMigrationError(
                        f"v50_database_migration_incomplete:{status.reason}"
                    )
    except ProductDatabaseMigrationError:
        raise
    except Exception as exc:  # noqa: BLE001 - preserve transactional rollback and add a stable boundary.
        raise ProductDatabaseMigrationError(
            f"v50_database_migration_failed:{type(exc).__name__}"
        ) from exc

    with _schema_lock:
        _verified_databases.add(database_key)
    return status


def _connect(database_url: str):
    import psycopg

    return psycopg.connect(database_url)


def _read_schema_status(cursor: Any) -> ProductDatabaseSchemaStatus:
    cursor.execute("SELECT to_regclass(%s)", ("public.v50_schema_version",))
    relation = cursor.fetchone()
    if not relation or relation[0] is None:
        return ProductDatabaseSchemaStatus(
            ready=False,
            version=None,
            boundary=None,
            reason="schema_table_missing",
        )

    cursor.execute(
        "SELECT version, boundary FROM v50_schema_version WHERE id = %s",
        ("v50.schema",),
    )
    row = cursor.fetchone()
    if not row:
        return ProductDatabaseSchemaStatus(
            ready=False,
            version=None,
            boundary=None,
            reason="schema_identity_missing",
        )

    version, boundary = str(row[0]), str(row[1])
    if version != EXPECTED_SCHEMA_VERSION:
        return ProductDatabaseSchemaStatus(
            ready=False,
            version=version,
            boundary=boundary,
            reason="schema_version_mismatch",
        )
    if boundary != EXPECTED_SCHEMA_BOUNDARY:
        return ProductDatabaseSchemaStatus(
            ready=False,
            version=version,
            boundary=boundary,
            reason="schema_boundary_mismatch",
        )
    return ProductDatabaseSchemaStatus(
        ready=True,
        version=version,
        boundary=boundary,
        reason="schema_ready",
    )


def _ready_status() -> ProductDatabaseSchemaStatus:
    return ProductDatabaseSchemaStatus(
        ready=True,
        version=EXPECTED_SCHEMA_VERSION,
        boundary=EXPECTED_SCHEMA_BOUNDARY,
        reason="schema_ready_cached",
    )


def _mismatch_message(status: ProductDatabaseSchemaStatus) -> str:
    current = status.version or "missing"
    return (
        f"v50_database_schema_not_ready:{status.reason}:"
        f"expected={EXPECTED_SCHEMA_VERSION}:current={current}:"
        f"run={MIGRATION_COMMAND}"
    )


def _database_key(database_url: str) -> str:
    value = database_url.strip()
    if not value:
        raise ProductDatabaseSchemaError("v50_database_url_required")
    return value


def _reset_schema_verification_cache_for_tests() -> None:
    with _schema_lock:
        _verified_databases.clear()
