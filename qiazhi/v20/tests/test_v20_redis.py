from __future__ import annotations

from v20.redis.contracts import redis_contract_manifest, validate_redis_contract


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
