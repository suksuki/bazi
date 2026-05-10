from __future__ import annotations

from v20.redis.contracts import redis_contract_manifest, validate_redis_contract
from v20.redis.runtime_cache import (
    attach_cache_miss_meta,
    cacheable_measure_payload,
    check_rate_limit,
    clear_runtime_request_cache,
    get_runtime_cache,
    runtime_cache_status,
    runtime_cache_key,
    set_runtime_cache,
    should_cache_measure,
)
from v20.api.schemas import MeasureRequest


def test_v20_redis_contract_is_ephemeral_and_ttl_bound() -> None:
    contract = redis_contract_manifest()
    validation = validate_redis_contract(contract)
    names = {row.name for row in contract.keyspaces}

    assert validation["ok"] is True
    assert names == {
        "request_cache",
        "rate_limit",
        "background_job_queue",
        "distributed_lock",
        "short_ttl_runtime_state",
    }
    assert all(row.ttl_seconds > 0 for row in contract.keyspaces)
    assert all(row.persistent_authority is False for row in contract.keyspaces)
    assert all(row.prefix.startswith("v20:") for row in contract.keyspaces)


def test_v20_redis_contract_manifest_does_not_connect_or_mutate() -> None:
    payload = redis_contract_manifest().to_dict()

    assert payload["runtime_mutation"] is False
    assert "NO_CONNECTION_BY_DEFAULT" in payload["guardrails"]
    assert "REBUILD_FROM_POSTGRES_OR_DETERMINISTIC_RUNTIME" in payload["guardrails"]


def test_v20_runtime_cache_key_is_stable_and_ephemeral_metadata_only() -> None:
    request = MeasureRequest(
        year="庚午",
        month="辛巳",
        day="丁丑",
        hour="乙巳",
        flow_year_pillar="丙午",
        luck_pillar="甲申",
        user_text="我想看事业",
    )
    payload = cacheable_measure_payload(
        request,
        pillars={"year": "庚午", "month": "辛巳", "day": "丁丑", "hour": "乙巳"},
        luck_pillar="甲申",
    )
    first_key = runtime_cache_key(payload, role_key="user")
    second_key = runtime_cache_key(dict(reversed(list(payload.items()))), role_key="user")

    assert first_key == second_key
    assert first_key.startswith("v20:cache:request:")
    assert should_cache_measure(request) is True

    result = {"version": "v20.runtime_result.v1", "runtime_mutation": False}
    attach_cache_miss_meta(result, first_key, stored=True)
    assert result["redis_cache"]["version"] == "v20.redis_runtime_cache.v1"
    assert result["redis_cache"]["cache_status"] == "miss_stored"
    assert result["redis_cache"]["ttl_seconds"] == 300
    assert result["redis_cache"]["runtime_mutation"] is False
    assert "REDIS_CACHE_IS_EPHEMERAL" in result["redis_cache"]["guardrails"]


def test_v20_runtime_cache_key_changes_for_practitioner_mainline_review() -> None:
    base_request = MeasureRequest(
        year="庚午",
        month="辛巳",
        day="丁丑",
        hour="乙巳",
        flow_year_pillar="丙午",
        luck_pillar="甲申",
        user_text="我想看事业",
    )
    reviewed_request = MeasureRequest(
        year="庚午",
        month="辛巳",
        day="丁丑",
        hour="乙巳",
        flow_year_pillar="丙午",
        luck_pillar="甲申",
        user_text="我想看事业",
        practitioner_selections=(
            {
                "control_key": "control.mainline_arbitration",
                "option": "采用第一主线",
                "source_decision_keys": (),
            },
        ),
    )

    pillars = {"year": "庚午", "month": "辛巳", "day": "丁丑", "hour": "乙巳"}
    base_key = runtime_cache_key(cacheable_measure_payload(base_request, pillars=pillars, luck_pillar="甲申"), role_key="user")
    reviewed_key = runtime_cache_key(cacheable_measure_payload(reviewed_request, pillars=pillars, luck_pillar="甲申"), role_key="user")

    assert base_key != reviewed_key


def test_v20_runtime_cache_skips_non_deterministic_llm_modes() -> None:
    assert should_cache_measure(MeasureRequest(year="甲子", month="戊辰", day="甲午", hour="辛酉", llm_mode="rewrite")) is False
    assert should_cache_measure(MeasureRequest(year="甲子", month="戊辰", day="甲午", hour="辛酉", llm_mode="practitioner")) is False


def test_v20_runtime_cache_status_does_not_render_values(monkeypatch) -> None:
    monkeypatch.setenv("V20_REDIS_URL", "redis://127.0.0.1:6379/0")
    status = runtime_cache_status()

    assert status["version"] == "v20.redis_runtime_cache_status.v1"
    assert status["keyspace"] == "request_cache"
    assert status["prefix"] == "v20:cache:request:"
    assert status["ttl_seconds"] == 300
    assert status["db"] == 0
    assert status["runtime_mutation"] is False
    assert "NO_CACHE_VALUES_RENDERED" in status["guardrails"]


def test_v20_runtime_cache_set_and_get_roundtrip_without_persisting_cache_meta(monkeypatch) -> None:
    class FakeRedis:
        def __init__(self) -> None:
            self.rows: dict[str, str] = {}
            self.ttls: dict[str, int] = {}

        def setex(self, key: str, ttl: int, value: str) -> None:
            self.rows[key] = value
            self.ttls[key] = ttl

        def get(self, key: str) -> str:
            return self.rows.get(key, "")

    client = FakeRedis()
    monkeypatch.setattr("v20.redis.runtime_cache._redis_client", lambda: client)
    key = "v20:cache:request:test"
    result = {
        "version": "v20.runtime_result.v1",
        "answer_text": "cached",
        "redis_cache": {"cache_status": "miss_stored"},
    }

    assert set_runtime_cache(key, result, ttl_seconds=12) is True
    cached = get_runtime_cache(key)

    assert client.ttls[key] == 12
    assert cached is not None
    assert cached["answer_text"] == "cached"
    assert cached["redis_cache"]["cache_status"] == "hit"
    assert cached["redis_cache"]["ttl_seconds"] == 12


def test_v20_runtime_cache_clear_deletes_request_cache_prefix_only(monkeypatch) -> None:
    class FakeRedis:
        def __init__(self) -> None:
            self.rows = {
                "v20:cache:request:a": "1",
                "v20:cache:request:b": "2",
                "v20:cache:other:c": "3",
            }

        def scan_iter(self, *, match: str, count: int):
            prefix = match.rstrip("*")
            return (key for key in list(self.rows) if key.startswith(prefix))

        def delete(self, *keys: str) -> int:
            deleted = 0
            for key in keys:
                if key in self.rows:
                    deleted += 1
                    del self.rows[key]
            return deleted

    client = FakeRedis()
    monkeypatch.setattr("v20.redis.runtime_cache._redis_client", lambda: client)

    result = clear_runtime_request_cache(batch_size=1)

    assert result["version"] == "v20.redis_runtime_cache_clear.v1"
    assert result["status"] == "cleared"
    assert result["deleted_count"] == 2
    assert result["runtime_mutation"] is True
    assert set(client.rows) == {"v20:cache:other:c"}
    assert "NO_CACHE_VALUES_RENDERED" in result["guardrails"]


def test_v20_rate_limit_counts_window_and_blocks_after_limit(monkeypatch) -> None:
    class FakeRedis:
        def __init__(self) -> None:
            self.rows: dict[str, int] = {}
            self.ttls: dict[str, int] = {}

        def incr(self, key: str) -> int:
            self.rows[key] = self.rows.get(key, 0) + 1
            return self.rows[key]

        def expire(self, key: str, ttl: int) -> None:
            self.ttls[key] = ttl

    client = FakeRedis()
    monkeypatch.setattr("v20.redis.runtime_cache._redis_client", lambda: client)
    monkeypatch.setattr("v20.redis.runtime_cache.time.time", lambda: 120.0)

    first = check_rate_limit("user-1", route_key="measure.stream.user", limit=2, window_seconds=60)
    second = check_rate_limit("user-1", route_key="measure.stream.user", limit=2, window_seconds=60)
    third = check_rate_limit("user-1", route_key="measure.stream.user", limit=2, window_seconds=60)

    assert first["status"] == "allowed"
    assert first["remaining"] == 1
    assert second["allowed"] is True
    assert second["remaining"] == 0
    assert third["status"] == "blocked"
    assert third["allowed"] is False
    assert third["retry_after_seconds"] == 60
    assert next(iter(client.ttls.values())) == 60
    assert "NO_RAW_IDENTITY_RENDERED" in third["guardrails"]


def test_v20_rate_limit_fails_open_when_redis_unavailable(monkeypatch) -> None:
    monkeypatch.setattr("v20.redis.runtime_cache._redis_client", lambda: None)

    result = check_rate_limit("user-1", route_key="measure.view.user", limit=1, window_seconds=60)

    assert result["status"] == "unavailable"
    assert result["allowed"] is True
    assert result["runtime_mutation"] is False
    assert "FAIL_OPEN_WHEN_REDIS_UNAVAILABLE" in result["guardrails"]
