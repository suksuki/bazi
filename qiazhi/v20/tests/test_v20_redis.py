from __future__ import annotations

from v20.redis.contracts import redis_contract_manifest, validate_redis_contract
from v20.redis.runtime_cache import (
    attach_cache_miss_meta,
    cacheable_measure_payload,
    runtime_cache_status,
    runtime_cache_key,
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
