from __future__ import annotations

import json

from v20.storage import postgres_pool
from v20.storage.postgres_pool import pooled_postgres_connection, postgres_pool_status


class FakeConnection:
    def __init__(self) -> None:
        self.rollback_count = 0

    def rollback(self) -> None:
        self.rollback_count += 1


class FakePool:
    def __init__(self) -> None:
        self.conn = FakeConnection()
        self.get_count = 0
        self.put_count = 0

    def getconn(self):
        self.get_count += 1
        return self.conn

    def putconn(self, conn) -> None:  # noqa: ANN001
        assert conn is self.conn
        self.put_count += 1


def test_v20_postgres_pool_context_returns_connection(monkeypatch) -> None:
    pool = FakePool()
    monkeypatch.setattr(postgres_pool, "_pool_for_dsn", lambda _dsn: pool)

    with pooled_postgres_connection("postgres://user:secret@localhost/db") as conn:
        assert conn is pool.conn

    assert pool.get_count == 1
    assert pool.put_count == 1
    assert pool.conn.rollback_count == 0


def test_v20_postgres_pool_rolls_back_and_returns_on_exception(monkeypatch) -> None:
    pool = FakePool()
    monkeypatch.setattr(postgres_pool, "_pool_for_dsn", lambda _dsn: pool)

    try:
        with pooled_postgres_connection("postgres://user:secret@localhost/db"):
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    assert pool.get_count == 1
    assert pool.put_count == 1
    assert pool.conn.rollback_count == 1


def test_v20_postgres_pool_status_is_secret_free(monkeypatch) -> None:
    monkeypatch.setenv("V20_DATABASE_URL", "postgres://user:secret@localhost/db")

    status = postgres_pool_status()
    rendered = json.dumps(status, ensure_ascii=False)

    assert status["version"] == "v20.postgres_pool_status.v1"
    assert status["database_url_present"] is True
    assert "NO_SECRET_VALUES_RENDERED" in status["guardrails"]
    assert "secret" not in rendered
