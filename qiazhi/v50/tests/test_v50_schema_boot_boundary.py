from __future__ import annotations

from dataclasses import dataclass
import ast

import pytest

from product import database_schema


@dataclass
class FakeDatabase:
    version: str | None = None
    boundary: str | None = None
    fail_migration: bool = False
    schema_executes: int = 0
    commits: int = 0
    rollbacks: int = 0

    def connect(self, _database_url: str):
        return FakeConnection(self)


class FakeConnection:
    def __init__(self, database: FakeDatabase) -> None:
        self.database = database
        self.pending_version = database.version
        self.pending_boundary = database.boundary

    def __enter__(self):
        return self

    def __exit__(self, exc_type, _exc, _traceback):
        if exc_type is None:
            self.database.version = self.pending_version
            self.database.boundary = self.pending_boundary
            self.database.commits += 1
        else:
            self.database.rollbacks += 1
        return False

    def cursor(self):
        return FakeCursor(self)


class FakeCursor:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _traceback):
        return False

    def execute(self, query: str, _params=None) -> None:
        if query.startswith("SELECT to_regclass"):
            relation = (
                "v50_schema_version"
                if self.connection.pending_version is not None
                else None
            )
            self.result = (relation,)
            return
        if query.startswith("SELECT version, boundary"):
            self.result = (
                (self.connection.pending_version, self.connection.pending_boundary)
                if self.connection.pending_version is not None
                else None
            )
            return
        if "CREATE TABLE IF NOT EXISTS v50_schema_version" in query:
            self.connection.database.schema_executes += 1
            if self.connection.database.fail_migration:
                raise RuntimeError("fixture_migration_failure")
            self.connection.pending_version = database_schema.EXPECTED_SCHEMA_VERSION
            self.connection.pending_boundary = database_schema.EXPECTED_SCHEMA_BOUNDARY
            self.result = None
            return
        raise AssertionError(f"unexpected_sql:{query[:80]}")

    def fetchone(self):
        return self.result


@pytest.fixture(autouse=True)
def reset_schema_cache(monkeypatch):
    database_schema._reset_schema_verification_cache_for_tests()
    yield
    database_schema._reset_schema_verification_cache_for_tests()


def bind_database(monkeypatch, database: FakeDatabase) -> None:
    monkeypatch.setattr(database_schema, "_connect", database.connect)


def test_fresh_database_requires_explicit_migration(monkeypatch) -> None:
    database = FakeDatabase()
    bind_database(monkeypatch, database)

    with pytest.raises(database_schema.ProductDatabaseSchemaMismatch) as exc_info:
        database_schema.check_product_database_schema("postgresql://fixture/fresh")

    assert "schema_table_missing" in str(exc_info.value)
    assert "v50_migrate_product_database.py apply" in str(exc_info.value)
    assert database.schema_executes == 0

    status = database_schema.migrate_product_database_schema(
        "postgresql://fixture/fresh"
    )
    assert status.ready is True
    assert database.version == database_schema.EXPECTED_SCHEMA_VERSION
    assert database.commits == 2  # one read-only inspection and one migration


def test_old_database_upgrade_and_repeat_are_idempotent(monkeypatch) -> None:
    database = FakeDatabase(
        version="v50.clean_room.001",
        boundary="v50_clean_room",
    )
    bind_database(monkeypatch, database)

    with pytest.raises(database_schema.ProductDatabaseSchemaMismatch):
        database_schema.check_product_database_schema("postgresql://fixture/old")

    first = database_schema.migrate_product_database_schema("postgresql://fixture/old")
    second = database_schema.migrate_product_database_schema("postgresql://fixture/old")

    assert first.ready and second.ready
    assert database.version == database_schema.EXPECTED_SCHEMA_VERSION
    assert database.schema_executes == 2


def test_failed_migration_rolls_back_old_schema(monkeypatch) -> None:
    database = FakeDatabase(
        version="v50.clean_room.001",
        boundary="v50_clean_room",
        fail_migration=True,
    )
    bind_database(monkeypatch, database)

    with pytest.raises(database_schema.ProductDatabaseMigrationError):
        database_schema.migrate_product_database_schema("postgresql://fixture/fail")

    assert database.version == "v50.clean_room.001"
    assert database.boundary == "v50_clean_room"
    assert database.rollbacks == 1


def test_service_restart_only_rechecks_schema(monkeypatch) -> None:
    database = FakeDatabase(
        version=database_schema.EXPECTED_SCHEMA_VERSION,
        boundary=database_schema.EXPECTED_SCHEMA_BOUNDARY,
    )
    bind_database(monkeypatch, database)

    first = database_schema.check_product_database_schema("postgresql://fixture/ready")
    cached = database_schema.check_product_database_schema("postgresql://fixture/ready")
    database_schema._reset_schema_verification_cache_for_tests()
    restarted = database_schema.check_product_database_schema("postgresql://fixture/ready")

    assert first.ready and cached.ready and restarted.ready
    assert database.schema_executes == 0
    assert database.commits == 2


def test_runtime_stores_only_call_read_only_checker() -> None:
    root = database_schema.ROOT
    for name in (
        "product_store_postgres.py",
        "agent_case_store_postgres.py",
        "agent_job_store.py",
        "theater_store.py",
        "voice_validation_store.py",
        "legacy_usage.py",
    ):
        source = (root / "apps" / "product" / name).read_text(encoding="utf-8")
        assert "check_product_database_schema(database_url)" in source
        assert "migrate_product_database_schema" not in source
        assert "ensure_product_database_schema" not in source


def test_product_package_does_not_start_application_during_migration_import() -> None:
    source = (database_schema.ROOT / "apps" / "product" / "__init__.py").read_text(
        encoding="utf-8"
    )
    module = ast.parse(source)
    eager_app_imports = [
        node
        for node in module.body
        if isinstance(node, ast.ImportFrom) and node.module == "app"
    ]
    assert eager_app_imports == []
