from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class PostgresConfig:
    enabled: bool
    host: str
    port: int
    database: str
    username_env: str = "V20_POSTGRES_USER"
    password_env: str = "V20_POSTGRES_PASSWORD"
    url_env: str = "V20_DATABASE_URL"
    sslmode: str = "prefer"
    role: str = "authoritative_persistent_store"
    owns: tuple[str, ...] = (
        "knowledge_units",
        "artifact_registry",
        "run_registry",
        "decision_registry",
        "feedback_ledger",
        "corpus_snapshots",
    )

    def to_dict(self, *, reveal_secrets: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        if not reveal_secrets:
            payload["secret_policy"] = "env_names_only_no_secret_values"
        return payload


@dataclass(frozen=True)
class RedisConfig:
    enabled: bool
    host: str
    port: int
    db: int
    url_env: str = "V20_REDIS_URL"
    role: str = "ephemeral_cache_queue_lock_store"
    owns: tuple[str, ...] = (
        "request_cache",
        "rate_limit",
        "background_job_queue",
        "distributed_lock",
        "short_ttl_runtime_state",
    )
    non_authoritative: bool = True

    def to_dict(self, *, reveal_secrets: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        if not reveal_secrets:
            payload["secret_policy"] = "env_names_only_no_secret_values"
        return payload


@dataclass(frozen=True)
class ServerProfile:
    name: str
    platform: str
    role: str
    bind_host: str
    public_host: str
    port: int
    runtime_dir: str
    service_name: str
    postgres: PostgresConfig
    redis: RedisConfig
    guardrails: tuple[str, ...] = (
        "SERVER_PROFILE_IS_CONFIG_ONLY",
        "NO_SECRET_VALUES_IN_REPO",
        "NO_RUNTIME_STATE_OVERWRITE_BY_DEFAULT",
    )

    def base_url(self) -> str:
        return f"http://{self.public_host}:{self.port}"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["base_url"] = self.base_url()
        payload["postgres"] = self.postgres.to_dict()
        payload["redis"] = self.redis.to_dict()
        return payload


@dataclass(frozen=True)
class SyncPlan:
    version: str
    source_profile: str
    target_profile: str
    code_sync: str
    postgres_sync: str
    redis_sync: str
    runtime_files_sync: str
    protected_scopes: tuple[str, ...] = (
        "secrets",
        "private_user_sessions",
        "raw_feedback_with_identifiers",
        "redis_ephemeral_state",
    )
    promotable_scopes: tuple[str, ...] = (
        "reviewed_knowledge_units",
        "validated_schema_migrations",
        "approved_artifacts",
        "anonymized_feedback_summaries",
        "synthetic_validation_results",
    )
    guardrails: tuple[str, ...] = (
        "SYNC_IS_EXPLICIT",
        "POSTGRES_DATA_REQUIRES_BACKUP",
        "REDIS_IS_NEVER_AUTHORITY",
        "NO_SECRET_SYNC",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeConfig:
    version: str
    active_profile: str
    profiles: tuple[ServerProfile, ...]
    sync_plans: tuple[SyncPlan, ...]
    guardrails: tuple[str, ...] = field(
        default_factory=lambda: (
            "V20_OPS_CONFIG_IS_INDEPENDENT",
            "MACOS_AND_LINUX_PROFILES_MUST_MATCH_CONTRACTS",
            "POSTGRES_IS_PERSISTENT_AUTHORITY",
            "REDIS_IS_EPHEMERAL",
        )
    )

    def profile(self, name: str) -> ServerProfile:
        for row in self.profiles:
            if row.name == name:
                return row
        raise KeyError(name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "active_profile": self.active_profile,
            "profiles": [row.to_dict() for row in self.profiles],
            "sync_plans": [row.to_dict() for row in self.sync_plans],
            "guardrails": list(self.guardrails),
        }
