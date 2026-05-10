from __future__ import annotations

import os
from typing import Any

from v20.ops.config import load_runtime_config_from_env
from v20.ops.profiles import validate_runtime_config


def liveness_report() -> dict[str, object]:
    config = load_runtime_config_from_env()
    validation = validate_runtime_config(config)
    return {
        "version": "v20.service_liveness.v1",
        "status": "ok" if validation["ok"] else "degraded",
        "active_profile": config.active_profile,
        "runtime_mutation": False,
        "connection_policy": "no_external_dependency_connection_on_liveness_check",
        "guardrails": [
            "LIVENESS_IS_PROCESS_ONLY",
            "NO_SECRET_VALUES_RENDERED",
            "NO_NETWORK_CONNECTION_ATTEMPTED",
        ],
    }


def readiness_report() -> dict[str, object]:
    config = load_runtime_config_from_env()
    profile = config.profile(config.active_profile)
    validation = validate_runtime_config(config)
    postgres = _postgres_probe(profile.postgres)
    redis = _redis_probe(profile.redis)
    ready = bool(validation["ok"] and postgres["ready"] and redis["ready"])
    return {
        "version": "v20.service_readiness.v1",
        "status": "ready" if ready else "degraded",
        "ready": ready,
        "active_profile": profile.name,
        "ops_validation": validation,
        "postgres": postgres,
        "redis": redis,
        "runtime_mutation": False,
        "connection_policy": "dependency_ping_without_secret_rendering",
        "guardrails": [
            "READINESS_CHECK_MAY_CONNECT_TO_DEPENDENCIES",
            "NO_SECRET_VALUES_RENDERED",
            "POSTGRES_IS_AUTHORITY_REDIS_IS_EPHEMERAL",
        ],
    }


def _postgres_probe(postgres: Any) -> dict[str, object]:
    base = {
        "enabled": bool(postgres.enabled),
        "host": postgres.host,
        "port": postgres.port,
        "database": postgres.database,
        "url_env": postgres.url_env,
        "username_env": postgres.username_env,
        "password_env": postgres.password_env,
        "ready": False,
        "status": "disabled" if not postgres.enabled else "unavailable",
        "runtime_mutation": False,
        "guardrails": ["POSTGRES_READINESS_QUERY_ONLY", "NO_SECRET_VALUES_RENDERED"],
    }
    if not postgres.enabled:
        return base | {"ready": True}
    url = os.getenv(postgres.url_env, "")
    user = os.getenv(postgres.username_env, "")
    password = os.getenv(postgres.password_env, "")
    if not url and not (user and password):
        return base | {"failure": "missing_postgres_credentials"}
    try:
        import psycopg2
    except Exception:
        return base | {"failure": "missing_psycopg2"}
    try:
        if url:
            conn = psycopg2.connect(url, connect_timeout=1)
        else:
            conn = psycopg2.connect(
                host=postgres.host,
                port=postgres.port,
                dbname=postgres.database,
                user=user,
                password=password,
                connect_timeout=1,
                sslmode=postgres.sslmode,
            )
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return base | {"ready": True, "status": "ready"}
    except Exception as exc:
        return base | {"failure": type(exc).__name__}


def _redis_probe(redis: Any) -> dict[str, object]:
    base = {
        "enabled": bool(redis.enabled),
        "host": redis.host,
        "port": redis.port,
        "db": redis.db,
        "url_env": redis.url_env,
        "ready": False,
        "status": "disabled" if not redis.enabled else "unavailable",
        "runtime_mutation": False,
        "guardrails": ["REDIS_READINESS_PING_ONLY", "REDIS_REMAINS_EPHEMERAL", "NO_SECRET_VALUES_RENDERED"],
    }
    if not redis.enabled:
        return base | {"ready": True}
    try:
        import redis as redis_module
    except Exception:
        return base | {"failure": "missing_redis_client"}
    try:
        url = os.getenv(redis.url_env, "")
        if url:
            client = redis_module.Redis.from_url(url, socket_connect_timeout=0.2, socket_timeout=0.2)
        else:
            client = redis_module.Redis(
                host=redis.host,
                port=redis.port,
                db=redis.db,
                socket_connect_timeout=0.2,
                socket_timeout=0.2,
            )
        client.ping()
        return base | {"ready": True, "status": "ready"}
    except Exception as exc:
        return base | {"failure": type(exc).__name__}
