from __future__ import annotations

from v20.redis.schema import RedisKeyspaceSpec, RedisRuntimeContract


def redis_contract_manifest() -> RedisRuntimeContract:
    return RedisRuntimeContract(
        version="v20.redis_runtime_contract.v1",
        keyspaces=(
            RedisKeyspaceSpec(
                name="request_cache",
                prefix="v20:cache:request:",
                owner_module="v20.api",
                purpose="Short-lived response fragments and deterministic runtime cache.",
                ttl_seconds=300,
                value_shape="json:cache_entry",
            ),
            RedisKeyspaceSpec(
                name="rate_limit",
                prefix="v20:rate:",
                owner_module="v20.server",
                purpose="Per-route or per-session rate counters.",
                ttl_seconds=60,
                value_shape="json:counter_window",
            ),
            RedisKeyspaceSpec(
                name="background_job_queue",
                prefix="v20:queue:job:",
                owner_module="v20.learning",
                purpose="Ephemeral job dispatch handles for eval, corpus, and learning workers.",
                ttl_seconds=86400,
                value_shape="json:job_envelope",
            ),
            RedisKeyspaceSpec(
                name="distributed_lock",
                prefix="v20:lock:",
                owner_module="v20.ops",
                purpose="Short TTL lock for migration, sync, and long-running job coordination.",
                ttl_seconds=120,
                value_shape="string:lock_owner_token",
            ),
            RedisKeyspaceSpec(
                name="short_ttl_runtime_state",
                prefix="v20:runtime:short:",
                owner_module="v20.interaction",
                purpose="Temporary interaction state that can be reconstructed or safely lost.",
                ttl_seconds=1800,
                value_shape="json:runtime_state",
            ),
        ),
    )


def validate_redis_contract(contract: RedisRuntimeContract | None = None) -> dict[str, object]:
    contract = contract or redis_contract_manifest()
    failures: list[str] = []
    prefixes: set[str] = set()
    for keyspace in contract.keyspaces:
        if keyspace.prefix in prefixes:
            failures.append(f"duplicate_prefix:{keyspace.prefix}")
        prefixes.add(keyspace.prefix)
        if keyspace.ttl_seconds <= 0:
            failures.append(f"missing_ttl:{keyspace.name}")
        if keyspace.persistent_authority:
            failures.append(f"redis_marked_authoritative:{keyspace.name}")
        if "NO_AUTHORITY_IN_REDIS" not in keyspace.guardrails:
            failures.append(f"missing_no_authority_guardrail:{keyspace.name}")
    return {
        "version": "v20.redis_contract_validation.v1",
        "ok": not failures,
        "failures": failures,
        "keyspace_count": len(contract.keyspaces),
        "runtime_mutation": False,
        "guardrails": ["REDIS_VALIDATION_ONLY", "NO_CONNECTION_ATTEMPTED"],
    }
