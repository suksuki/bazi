from __future__ import annotations

from v20.ops.schema import PostgresConfig, RedisConfig, RuntimeConfig, ServerProfile, SyncPlan


def default_runtime_config(*, active_profile: str = "local_macos") -> RuntimeConfig:
    profiles = (
        ServerProfile(
            name="local_macos",
            platform="macos",
            role="developer_workstation",
            bind_host="127.0.0.1",
            public_host="127.0.0.1",
            port=9020,
            runtime_dir="v20/.runtime/local",
            service_name="qiazhi-v20-local",
            postgres=PostgresConfig(
                enabled=True,
                host="127.0.0.1",
                port=5432,
                database="qiazhi_v20_local",
            ),
            redis=RedisConfig(
                enabled=True,
                host="127.0.0.1",
                port=6379,
                db=20,
            ),
        ),
        ServerProfile(
            name="linux_0_13",
            platform="linux",
            role="shared_staging_or_server",
            bind_host="0.0.0.0",
            public_host="0.13",
            port=9020,
            runtime_dir="v20/.runtime/linux_0_13",
            service_name="qiazhi-v20",
            postgres=PostgresConfig(
                enabled=True,
                host="127.0.0.1",
                port=5432,
                database="qiazhi_v20",
                sslmode="prefer",
            ),
            redis=RedisConfig(
                enabled=True,
                host="127.0.0.1",
                port=6379,
                db=20,
            ),
        ),
    )
    return RuntimeConfig(
        version="v20.ops_runtime_config.v1",
        active_profile=active_profile,
        profiles=profiles,
        sync_plans=(
            SyncPlan(
                version="v20.sync_plan.v1",
                source_profile="local_macos",
                target_profile="linux_0_13",
                code_sync="git_push_pull_or_rsync_worktree_after_tests",
                postgres_sync="migrations_and_reviewed_seed_promotions_only",
                redis_sync="disabled_ephemeral_cache_must_be_rebuilt",
                runtime_files_sync="disabled_except_explicit_backup_restore",
            ),
            SyncPlan(
                version="v20.sync_plan.v1",
                source_profile="linux_0_13",
                target_profile="local_macos",
                code_sync="git_pull_only",
                postgres_sync="anonymized_exports_only_after_backup",
                redis_sync="disabled_ephemeral_cache_must_be_rebuilt",
                runtime_files_sync="explicit_readonly_backup_snapshot_only",
            ),
        ),
    )


def validate_runtime_config(config: RuntimeConfig) -> dict[str, object]:
    failures: list[str] = []
    names = [profile.name for profile in config.profiles]
    if len(names) != len(set(names)):
        failures.append("duplicate_profile_name")
    for profile in config.profiles:
        if profile.postgres.enabled and not profile.postgres.database:
            failures.append(f"missing_postgres_database:{profile.name}")
        if profile.redis.enabled and not profile.redis.non_authoritative:
            failures.append(f"redis_must_be_non_authoritative:{profile.name}")
        if profile.platform == "linux" and profile.bind_host == "127.0.0.1" and profile.role != "private_local_only":
            failures.append(f"linux_server_not_exposed:{profile.name}")
    for plan in config.sync_plans:
        if plan.redis_sync != "disabled_ephemeral_cache_must_be_rebuilt":
            failures.append(f"redis_sync_not_disabled:{plan.source_profile}->{plan.target_profile}")
        if "secrets" not in plan.protected_scopes:
            failures.append(f"secret_scope_not_protected:{plan.source_profile}->{plan.target_profile}")
    return {
        "version": "v20.ops_runtime_config_validation.v1",
        "ok": not failures,
        "active_profile": config.active_profile,
        "profiles": names,
        "failures": failures,
        "guardrails": [
            "OPS_VALIDATION_ONLY",
            "NO_NETWORK_CONNECTION_ATTEMPTED",
            "NO_SECRET_VALUES_RENDERED",
        ],
    }
