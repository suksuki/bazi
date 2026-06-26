from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.runtime import create_smoke_runtime
from v30.storage.diagnosis import (
    DIAGNOSIS_STORAGE_VERSION,
    diagnosis_id_for_payload,
    diagnosis_storage_record,
    query_latest_real_bazi_diagnosis_from_postgres,
    select_latest_diagnosis_run_sql,
    upsert_diagnosis_claim_sql,
    upsert_diagnosis_path_sql,
    upsert_diagnosis_portrait_sql,
    upsert_diagnosis_rule_match_sql,
    upsert_diagnosis_run_sql,
    write_real_bazi_diagnosis_to_postgres,
)


class FakeCursor:
    def __init__(self, connection: "FakeConnection") -> None:
        self.connection = connection

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> None:
        self.connection.executed.append((sql, params))
        if "INSERT INTO v30_diagnosis_runs" in sql:
            self.connection.runs[str(params[0])] = params[3]
        if "SELECT payload FROM v30_diagnosis_runs" in sql:
            self.connection.next_row = (next(iter(self.connection.runs.values()), {}),)

    def fetchone(self):
        row = self.connection.next_row
        self.connection.next_row = None
        return row


class FakeConnection:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[object, ...]]] = []
        self.runs: dict[str, object] = {}
        self.next_row: tuple[object, ...] | None = None
        self.commits = 0

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def commit(self) -> None:
        self.commits += 1


def _settings(tmp_path: Path, *, database_url: str | None = None) -> V30Settings:
    return V30Settings(
        database_url=database_url,
        redis_url=None,
        redis_prefix="v30",
        runtime_dir=tmp_path / ".runtime",
        host="127.0.0.1",
        port=9030,
        env="test",
        repository="memory",
    )


def _payload():
    runtime = create_smoke_runtime(
        "rbd-storage",
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    return runtime.question_plan.policy_effect["real_bazi_diagnosis"]


def test_diagnosis_storage_record_indexes_runtime_payload() -> None:
    payload = _payload()
    record = diagnosis_storage_record(payload)

    assert record["version"] == DIAGNOSIS_STORAGE_VERSION
    assert record["table"] == "v30_diagnosis_runs"
    assert record["reading_id"] == "rbd-storage"
    assert record["claim_count"] >= 50
    assert record["rule_match_count"] > 0
    assert record["path_count"] > 0
    assert record["portrait_count"] > 0
    assert record["authoritative_facts_stored_here"] is False


def test_diagnosis_storage_sql_uses_v30_tables_only() -> None:
    sql = "\n".join(
        [
            upsert_diagnosis_run_sql(),
            upsert_diagnosis_rule_match_sql(),
            upsert_diagnosis_path_sql(),
            upsert_diagnosis_portrait_sql(),
            upsert_diagnosis_claim_sql(),
            select_latest_diagnosis_run_sql(),
        ]
    )

    assert "v30_diagnosis_runs" in sql
    assert "v30_diagnosis_rule_matches" in sql
    assert "v30_diagnosis_paths" in sql
    assert "v30_diagnosis_portraits" in sql
    assert "v30_diagnosis_claims" in sql
    assert "v20_" not in sql


def test_diagnosis_storage_uses_json_fallback_without_database(tmp_path: Path) -> None:
    payload = _payload()
    result = write_real_bazi_diagnosis_to_postgres(payload, settings=_settings(tmp_path))

    assert result.backend == "json_fallback"
    assert result.searchable is False
    assert result.diagnosis_id == diagnosis_id_for_payload(payload)
    assert result.rows["diagnosis_runs"] == 0
    assert result.boundary == "diagnosis_storage_records_replay_data_not_authoritative_chart_facts"


def test_diagnosis_storage_writes_postgres_rows(tmp_path: Path) -> None:
    payload = _payload()
    connection = FakeConnection()
    result = write_real_bazi_diagnosis_to_postgres(
        payload,
        settings=_settings(tmp_path, database_url="postgresql://user:pass@localhost:5432/qiazhi_v30"),
        connect=lambda database_url: connection,
    )
    executed_sql = "\n".join(sql for sql, _params in connection.executed)

    assert result.backend == "postgres"
    assert result.searchable is True
    assert result.rows["diagnosis_runs"] == 1
    assert result.rows["rule_matches"] == len(payload["matched_rules"])
    assert result.rows["paths"] == len(payload["paths"])
    assert result.rows["portraits"] == len(payload["portraits"])
    assert result.rows["claims"] == len(payload["claims"])
    assert connection.commits == 1
    assert "v30_diagnosis_runs" in executed_sql
    assert "v30_diagnosis_claims" in executed_sql
    assert "v20_" not in executed_sql


def test_diagnosis_storage_query_latest_uses_postgres(tmp_path: Path) -> None:
    payload = _payload()
    connection = FakeConnection()
    write_real_bazi_diagnosis_to_postgres(
        payload,
        settings=_settings(tmp_path, database_url="postgresql://user:pass@localhost:5432/qiazhi_v30"),
        connect=lambda database_url: connection,
    )
    query = query_latest_real_bazi_diagnosis_from_postgres(
        reading_id="rbd-storage",
        settings=_settings(tmp_path, database_url="postgresql://user:pass@localhost:5432/qiazhi_v30"),
        connect=lambda database_url: connection,
    )

    assert query["version"] == DIAGNOSIS_STORAGE_VERSION
    assert query["backend"] == "postgres"
    assert query["searchable"] is True
    assert query["payload"]
