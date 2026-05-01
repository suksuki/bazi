from __future__ import annotations

from v20.ops.config import load_runtime_config_from_env
from v20.ops.profiles import validate_runtime_config
from v20.ops.schema import RuntimeConfig, SyncPlan


def sync_readiness_report(config: RuntimeConfig | None = None) -> dict[str, object]:
    active_config = config or load_runtime_config_from_env()
    validation = validate_runtime_config(active_config)
    directions = tuple(_direction(row, active_config, validation["ok"]) for row in active_config.sync_plans)
    return {
        "version": "v20.sync_readiness_report.v1",
        "status": "ready_for_manual_sync" if validation["ok"] and all(row["ok"] for row in directions) else "blocked",
        "active_profile": active_config.active_profile,
        "profile_count": len(active_config.profiles),
        "direction_count": len(directions),
        "directions": list(directions),
        "runtime_mutation": False,
        "guardrails": [
            "SYNC_REPORT_IS_READ_ONLY",
            "SYNC_REQUIRES_HUMAN_OPERATOR",
            "POSTGRES_REQUIRES_BACKUP_AND_MIGRATION_REVIEW",
            "REDIS_STATE_IS_NOT_SYNCED",
            "NO_SECRET_VALUES_RENDERED",
        ],
    }


def _direction(plan: SyncPlan, config: RuntimeConfig, config_ok: bool) -> dict[str, object]:
    failures = []
    try:
        source = config.profile(plan.source_profile)
    except KeyError:
        source = None
        failures.append(f"missing_source_profile:{plan.source_profile}")
    try:
        target = config.profile(plan.target_profile)
    except KeyError:
        target = None
        failures.append(f"missing_target_profile:{plan.target_profile}")
    if plan.redis_sync != "disabled_ephemeral_cache_must_be_rebuilt":
        failures.append("redis_sync_must_stay_disabled")
    if "secrets" not in plan.protected_scopes:
        failures.append("secrets_scope_must_be_protected")
    if "backup" not in plan.postgres_sync and "migrations" not in plan.postgres_sync:
        failures.append("postgres_sync_must_be_backup_or_migration_scoped")
    ok = config_ok and not failures
    return {
        "source_profile": plan.source_profile,
        "target_profile": plan.target_profile,
        "source_base_url": source.base_url() if source else "",
        "target_base_url": target.base_url() if target else "",
        "status": "ready_for_manual_sync" if ok else "blocked",
        "ok": ok,
        "failures": failures,
        "code_sync": plan.code_sync,
        "postgres_sync": plan.postgres_sync,
        "redis_sync": plan.redis_sync,
        "runtime_files_sync": plan.runtime_files_sync,
        "preflight": (
            "run_v20_fast_or_full_tests",
            "confirm_git_status_clean",
            "review_migration_or_backup_scope",
            "confirm_redis_cache_rebuild",
            "confirm_no_secret_or_private_session_sync",
        ),
        "protected_scopes": plan.protected_scopes,
        "promotable_scopes": plan.promotable_scopes,
        "guardrails": plan.guardrails,
    }
