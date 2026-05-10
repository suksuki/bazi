from __future__ import annotations

import os
from dataclasses import replace

from v20.ops.profiles import default_runtime_config
from v20.ops.schema import RuntimeConfig, ServerProfile


def load_runtime_config_from_env() -> RuntimeConfig:
    active = os.getenv("V20_ENV", "local_macos")
    config = default_runtime_config(active_profile=active)
    overrides = {
        "bind_host": os.getenv("V20_HOST"),
        "public_host": os.getenv("V20_PUBLIC_HOST"),
        "port": _int_env("V20_PORT"),
        "runtime_dir": os.getenv("V20_RUNTIME_DIR"),
        "service_name": os.getenv("V20_SERVICE_NAME"),
    }
    profiles = tuple(_override_profile(row, overrides) if row.name == active else row for row in config.profiles)
    return RuntimeConfig(
        version=config.version,
        active_profile=active,
        profiles=profiles,
        sync_plans=config.sync_plans,
        guardrails=config.guardrails,
    )


def _override_profile(profile: ServerProfile, overrides: dict[str, object | None]) -> ServerProfile:
    values = {key: value for key, value in overrides.items() if value not in (None, "")}
    postgres = profile.postgres
    redis = profile.redis
    if os.getenv("V20_POSTGRES_HOST"):
        postgres = replace(postgres, host=os.environ["V20_POSTGRES_HOST"])
    if _int_env("V20_POSTGRES_PORT") is not None:
        postgres = replace(postgres, port=_int_env("V20_POSTGRES_PORT"))
    if os.getenv("V20_POSTGRES_DB"):
        postgres = replace(postgres, database=os.environ["V20_POSTGRES_DB"])
    if os.getenv("V20_POSTGRES_ENABLED") is not None:
        postgres = replace(postgres, enabled=_bool_env("V20_POSTGRES_ENABLED"))
    if os.getenv("V20_REDIS_HOST"):
        redis = replace(redis, host=os.environ["V20_REDIS_HOST"])
    if _int_env("V20_REDIS_PORT") is not None:
        redis = replace(redis, port=_int_env("V20_REDIS_PORT"))
    if _int_env("V20_REDIS_DB") is not None:
        redis = replace(redis, db=_int_env("V20_REDIS_DB"))
    if os.getenv("V20_REDIS_ENABLED") is not None:
        redis = replace(redis, enabled=_bool_env("V20_REDIS_ENABLED"))
    return replace(profile, **values, postgres=postgres, redis=redis)


def _int_env(name: str) -> int | None:
    raw = os.getenv(name)
    if raw in (None, ""):
        return None
    return int(raw)


def _bool_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}
