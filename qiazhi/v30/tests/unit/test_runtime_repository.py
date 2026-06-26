from __future__ import annotations

from pathlib import Path

import pytest

from v30.config import V30Settings
from v30.runtime import create_smoke_runtime
from v30.storage.repository import (
    LocalJsonRuntimeRepository,
    MemoryRuntimeRepository,
    PostgresRuntimeRepository,
    build_runtime_repository,
)


class FakePostgresCursor:
    def __init__(self, connection: "FakePostgresConnection") -> None:
        self.connection = connection

    def __enter__(self) -> "FakePostgresCursor":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def execute(self, sql: str, params: tuple[object, ...]) -> None:
        self.connection.executed.append((sql, params))
        if "SELECT payload FROM v30_readings;" in sql:
            self.connection.next_rows = [(payload,) for payload in self.connection.readings.values()]
            return
        if "INSERT INTO v30_readings" in sql:
            self.connection.readings[str(params[0])] = str(params[1])
        if "INSERT INTO v30_runtime_traces" in sql:
            self.connection.traces[str(params[0])] = str(params[2])
        if "SELECT payload FROM v30_readings" in sql:
            self.connection.next_row = (self.connection.readings[str(params[0])],)
        if "SELECT payload FROM v30_runtime_traces" in sql:
            self.connection.next_row = (self.connection.traces[str(params[0])],)

    def fetchone(self):
        row = self.connection.next_row
        self.connection.next_row = None
        return row

    def fetchall(self):
        rows = self.connection.next_rows
        self.connection.next_rows = []
        return rows


class FakePostgresConnection:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[object, ...]]] = []
        self.readings: dict[str, str] = {}
        self.traces: dict[str, str] = {}
        self.next_row: tuple[object, ...] | None = None
        self.next_rows: list[tuple[object, ...]] = []
        self.commits = 0

    def __enter__(self) -> "FakePostgresConnection":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def cursor(self) -> FakePostgresCursor:
        return FakePostgresCursor(self)

    def commit(self) -> None:
        self.commits += 1


def _settings(tmp_path: Path, repository: str) -> V30Settings:
    return V30Settings(
        database_url=None,
        redis_url=None,
        redis_prefix="v30",
        runtime_dir=tmp_path / ".runtime",
        host="127.0.0.1",
        port=9030,
        env="test",
        repository=repository,
    )


def test_memory_runtime_repository_round_trip() -> None:
    repo = MemoryRuntimeRepository()
    runtime = create_smoke_runtime("repo-memory")
    repo.save_runtime(runtime)
    repo.save_trace(runtime)
    payload = repo.get_runtime_payload("repo-memory")
    trace_payload = repo.get_trace_payload(runtime.trace_id)
    assert payload is not None
    assert payload["reading_id"] == "repo-memory"
    assert trace_payload is not None
    assert trace_payload["trace_id"] == runtime.trace_id


def test_memory_runtime_repository_lists_by_actor_and_session() -> None:
    repo = MemoryRuntimeRepository()
    first = create_smoke_runtime("repo-memory-history-1")
    second = create_smoke_runtime("repo-memory-history-2")
    third = create_smoke_runtime("repo-memory-history-3")
    first = _with_actor_context(first, actor_id="actor-1", session_id="session-1")
    second = _with_actor_context(second, actor_id="actor-2", session_id="session-2")
    third = _with_actor_context(third, actor_id="actor-1", session_id="session-2")
    repo.save_runtime(first)
    repo.save_runtime(second)
    repo.save_runtime(third)

    actor_rows = repo.list_runtime_payloads(actor_id="actor-1")
    session_rows = repo.list_runtime_payloads(session_id="session-2")
    exact_rows = repo.list_runtime_payloads(actor_id="actor-1", session_id="session-2")

    assert {row["reading_id"] for row in actor_rows} == {"repo-memory-history-1", "repo-memory-history-3"}
    assert {row["reading_id"] for row in session_rows} == {"repo-memory-history-2", "repo-memory-history-3"}
    assert [row["reading_id"] for row in exact_rows] == ["repo-memory-history-3"]


def test_memory_runtime_repository_ignores_unowned_rows_for_history() -> None:
    repo = MemoryRuntimeRepository()
    owned = _with_actor_context(create_smoke_runtime("repo-owned"), actor_id="actor-owned", session_id="session-owned")
    unowned = create_smoke_runtime("repo-unowned")
    repo.save_runtime(owned)
    repo.save_runtime(unowned)

    assert [row["reading_id"] for row in repo.list_runtime_payloads(actor_id="actor-owned")] == ["repo-owned"]
    assert {row["reading_id"] for row in repo.list_runtime_payloads()} == {"repo-owned", "repo-unowned"}


def test_local_json_runtime_repository_round_trip(tmp_path: Path) -> None:
    repo = LocalJsonRuntimeRepository(_settings(tmp_path, "local_json"))
    runtime = create_smoke_runtime("repo-local")
    repo.save_runtime(runtime)
    repo.save_trace(runtime)
    payload = repo.get_runtime_payload("repo-local")
    trace_payload = repo.get_trace_payload(runtime.trace_id)
    reading_path = tmp_path / ".runtime" / "readings" / "repo-local.json"
    trace_path = tmp_path / ".runtime" / "traces" / f"{runtime.trace_id}.json"
    assert reading_path.exists()
    assert trace_path.exists()
    assert payload is not None
    assert payload["reading_id"] == "repo-local"
    assert trace_payload is not None
    assert trace_payload["trace_id"] == runtime.trace_id
    assert '"runtime_import":"v20' not in reading_path.read_text(encoding="utf-8")
    assert '"runtime_import":"v20' not in trace_path.read_text(encoding="utf-8")


def test_local_json_runtime_repository_lists_by_actor_and_session(tmp_path: Path) -> None:
    repo = LocalJsonRuntimeRepository(_settings(tmp_path, "local_json"))
    first = _with_actor_context(create_smoke_runtime("repo-local-history-1"), actor_id="actor-1", session_id="session-1")
    second = _with_actor_context(create_smoke_runtime("repo-local-history-2"), actor_id="actor-1", session_id="session-2")
    third = _with_actor_context(create_smoke_runtime("repo-local-history-3"), actor_id="actor-2", session_id="session-2")
    repo.save_runtime(first)
    repo.save_runtime(second)
    repo.save_runtime(third)

    rows = repo.list_runtime_payloads(actor_id="actor-1", session_id="session-2")
    session_rows = repo.list_runtime_payloads(session_id="session-2")

    assert len(rows) == 1
    assert rows[0]["reading_id"] == "repo-local-history-2"
    assert {row["reading_id"] for row in session_rows} == {"repo-local-history-2", "repo-local-history-3"}


def test_runtime_repository_factory_rejects_unknown(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported V30_REPOSITORY"):
        build_runtime_repository(_settings(tmp_path, "unknown"))


def test_postgres_runtime_repository_requires_database_url(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="V30_DATABASE_URL is required"):
        build_runtime_repository(_settings(tmp_path, "postgres"))


def test_postgres_runtime_repository_round_trip_uses_v30_tables(tmp_path: Path) -> None:
    settings = V30Settings(
        database_url="postgresql://user:pass@localhost:5432/qiazhi_v30",
        redis_url=None,
        redis_prefix="v30",
        runtime_dir=tmp_path / ".runtime",
        host="127.0.0.1",
        port=9030,
        env="test",
        repository="postgres",
    )
    connection = FakePostgresConnection()
    repo = PostgresRuntimeRepository(settings, connect=lambda database_url: connection)
    runtime = create_smoke_runtime("repo-postgres")

    repo.save_runtime(runtime)
    repo.save_trace(runtime)
    payload = repo.get_runtime_payload("repo-postgres")
    trace_payload = repo.get_trace_payload(runtime.trace_id)
    executed_sql = "\n".join(sql for sql, _params in connection.executed)

    assert payload is not None
    assert payload["reading_id"] == "repo-postgres"
    assert trace_payload is not None
    assert trace_payload["trace_id"] == runtime.trace_id
    assert "v30_readings" in executed_sql
    assert "v30_runtime_traces" in executed_sql
    assert "v20_" not in executed_sql
    assert connection.commits == 2


def test_postgres_runtime_repository_lists_by_actor(tmp_path: Path) -> None:
    settings = V30Settings(
        database_url="postgresql://user:pass@localhost:5432/qiazhi_v30",
        redis_url=None,
        redis_prefix="v30",
        runtime_dir=tmp_path / ".runtime",
        host="127.0.0.1",
        port=9030,
        env="test",
        repository="postgres",
    )
    connection = FakePostgresConnection()
    repo = PostgresRuntimeRepository(settings, connect=lambda database_url: connection)
    repo.save_runtime(_with_actor_context(create_smoke_runtime("repo-postgres-history"), actor_id="actor-pg", session_id="session-pg"))

    rows = repo.list_runtime_payloads(actor_id="actor-pg")

    assert [row["reading_id"] for row in rows] == ["repo-postgres-history"]
    assert any("SELECT payload FROM v30_readings;" in sql for sql, _params in connection.executed)


def _with_actor_context(runtime, *, actor_id: str, session_id: str):
    plan = runtime.question_plan.model_copy(
        update={
            "policy_effect": {
                **runtime.question_plan.policy_effect,
                "actor_context": {
                    "version": "v30.actor_context.v1",
                    "actor_id": actor_id,
                    "session_id": session_id,
                    "boundary": "actor_context_routes_identity_and_session_not_chart_fact",
                },
            }
        }
    )
    return runtime.model_copy(update={"question_plan": plan})
