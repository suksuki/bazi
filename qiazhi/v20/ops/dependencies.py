from __future__ import annotations

import os

from v20.llm.provider import llm_provider_readiness_report
from v20.ops.config import load_runtime_config_from_env


def dependency_readiness_report() -> dict[str, object]:
    config = load_runtime_config_from_env()
    profile = config.profile(config.active_profile)
    postgres = profile.postgres
    redis = profile.redis
    postgres_secrets_present = bool(
        os.getenv(postgres.url_env)
        or (os.getenv(postgres.username_env) and os.getenv(postgres.password_env))
    )
    redis_url_present = bool(os.getenv(redis.url_env))
    llm = llm_provider_readiness_report()
    return {
        "version": "v20.dependency_readiness.v1",
        "active_profile": profile.name,
        "postgres": {
            "enabled": postgres.enabled,
            "host": postgres.host,
            "port": postgres.port,
            "database": postgres.database,
            "url_env": postgres.url_env,
            "username_env": postgres.username_env,
            "password_env": postgres.password_env,
            "secrets_present": postgres_secrets_present,
            "ready_for_connection": bool(postgres.enabled and postgres_secrets_present),
            "connection_policy": "explicit_repository_command_only",
        },
        "redis": {
            "enabled": redis.enabled,
            "host": redis.host,
            "port": redis.port,
            "db": redis.db,
            "url_env": redis.url_env,
            "url_present": redis_url_present,
            "ready_for_connection": bool(redis.enabled and (redis_url_present or redis.host)),
            "connection_policy": "ephemeral_cache_queue_lock_only",
        },
        "llm": llm,
        "runtime_mutation": False,
        "guardrails": [
            "DEPENDENCY_READINESS_ONLY",
            "NO_NETWORK_CONNECTION_ATTEMPTED",
            "NO_SECRET_VALUES_RENDERED",
            "POSTGRES_IS_AUTHORITY_REDIS_IS_EPHEMERAL",
        ],
    }
