from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.runtime import create_smoke_runtime
from v30.storage.names import redis_key
from v30.storage.artifacts import select_518k_artifacts_sql, select_validation_artifacts_sql, upsert_artifact_sql
from v30.storage.postgres import (
    create_schema_sql,
    reading_record,
    select_reading_sql,
    trace_record,
    upsert_reading_sql,
    upsert_trace_sql,
)
from v30.storage.hidden_factor_state import (
    select_hidden_factor_state_sql,
    upsert_hidden_factor_state_sql,
)
from v30.storage.m3 import (
    insert_m3_validation_snapshot_sql,
    select_m3_source_backlog_sql,
    upsert_m3_source_backlog_sql,
    upsert_m3_knowledge_unit_sql,
    upsert_m3_portrait_asset_sql,
    upsert_m3_rule_spec_sql,
)
from v30.storage.diagnosis import (
    insert_diagnosis_feedback_sql,
    upsert_diagnosis_claim_sql,
    upsert_diagnosis_path_sql,
    upsert_diagnosis_portrait_sql,
    upsert_diagnosis_rule_match_sql,
    upsert_diagnosis_run_sql,
)
from v30.storage.redis_cache import V30RedisCache, V30RedisKeyspace


class FakeRedis:
    def __init__(self) -> None:
        self.rows: dict[str, str] = {}
        self.ttls: dict[str, int | None] = {}

    def get(self, key: str):
        return self.rows.get(key)

    def set(self, key: str, value: str, ex: int | None = None):
        self.rows[key] = value
        self.ttls[key] = ex
        return True


def _settings(tmp_path: Path) -> V30Settings:
    return V30Settings(
        database_url=None,
        redis_url=None,
        redis_prefix="v30",
        runtime_dir=tmp_path / ".runtime",
        host="127.0.0.1",
        port=9030,
        env="test",
        repository="memory",
    )


def test_postgres_schema_is_v30_only() -> None:
    sql = create_schema_sql()
    assert "v30_readings" in sql
    assert "v30_runtime_traces" in sql
    assert "v30_hidden_factor_states" in sql
    assert "v30_m3_knowledge_units" in sql
    assert "v30_m3_rule_specs" in sql
    assert "v30_m3_portrait_assets" in sql
    assert "v30_m3_validation_snapshots" in sql
    assert "v30_m3_source_backlog" in sql
    assert "v30_diagnosis_runs" in sql
    assert "v30_diagnosis_rule_matches" in sql
    assert "v30_diagnosis_paths" in sql
    assert "v30_diagnosis_portraits" in sql
    assert "v30_diagnosis_claims" in sql
    assert "v30_diagnosis_feedback" in sql
    assert "v20_" not in sql


def test_postgres_runtime_records_are_table_bound() -> None:
    runtime = create_smoke_runtime("storage-record")
    reading = reading_record(runtime)
    trace = trace_record(runtime)
    assert reading["table"] == "v30_readings"
    assert reading["key"] == "storage-record"
    assert trace["table"] == "v30_runtime_traces"
    assert trace["reading_id"] == "storage-record"
    assert trace["payload"]["reading_id"] == "storage-record"


def test_postgres_sql_uses_v30_tables_only() -> None:
    sql = "\n".join([
        upsert_reading_sql(),
        upsert_trace_sql(),
        select_reading_sql(),
        upsert_hidden_factor_state_sql(),
        select_hidden_factor_state_sql(),
        upsert_artifact_sql(),
        select_518k_artifacts_sql(),
        select_validation_artifacts_sql(),
        upsert_m3_knowledge_unit_sql(),
        upsert_m3_rule_spec_sql(),
        upsert_m3_portrait_asset_sql(),
        insert_m3_validation_snapshot_sql(),
        upsert_m3_source_backlog_sql(),
        select_m3_source_backlog_sql(),
        upsert_diagnosis_run_sql(),
        upsert_diagnosis_rule_match_sql(),
        upsert_diagnosis_path_sql(),
        upsert_diagnosis_portrait_sql(),
        upsert_diagnosis_claim_sql(),
        insert_diagnosis_feedback_sql(),
    ])
    assert "v30_readings" in sql
    assert "v30_runtime_traces" in sql
    assert "v30_hidden_factor_states" in sql
    assert "v30_artifacts" in sql
    assert "v30_m3_knowledge_units" in sql
    assert "v30_m3_rule_specs" in sql
    assert "v30_m3_portrait_assets" in sql
    assert "v30_m3_validation_snapshots" in sql
    assert "v30_m3_source_backlog" in sql
    assert "v30_diagnosis_runs" in sql
    assert "v30_diagnosis_rule_matches" in sql
    assert "v30_diagnosis_paths" in sql
    assert "v30_diagnosis_portraits" in sql
    assert "v30_diagnosis_claims" in sql
    assert "v30_diagnosis_feedback" in sql
    assert "v20_" not in sql


def test_redis_keyspace_is_v30_only(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    keys = V30RedisKeyspace(settings)
    assert keys.reading("abc") == "v30:test:reading:abc"
    assert keys.trace("trace") == "v30:test:trace:trace"
    assert keys.policy("structure_policy") == "v30:test:policy:structure_policy"
    assert redis_key("test", "lock", "x") == "v30:test:lock:x"


def test_redis_cache_round_trip_uses_v30_keys(tmp_path: Path) -> None:
    runtime = create_smoke_runtime("redis-record")
    client = FakeRedis()
    cache = V30RedisCache(client, _settings(tmp_path), ttl_seconds=30)
    key = cache.set_reading(runtime)
    payload = cache.get_reading_payload("redis-record")
    trace_key = cache.set_trace(runtime)
    trace_payload = cache.get_trace_payload(runtime.trace_id)
    assert key == "v30:test:reading:redis-record"
    assert trace_key == f"v30:test:trace:{runtime.trace_id}"
    assert payload is not None
    assert payload["reading_id"] == "redis-record"
    assert trace_payload is not None
    assert trace_payload["trace_id"] == runtime.trace_id
    assert client.ttls[key] == 30
    assert client.ttls[trace_key] == 30
