from __future__ import annotations

from fastapi.testclient import TestClient

from v20.ops.config import load_runtime_config_from_env
from v20.ops.dependencies import dependency_readiness_report
from v20.ops.profiles import default_runtime_config, validate_runtime_config
from v20.ops.sync import sync_readiness_report
from v20.server import app


def test_v20_ops_profiles_cover_macos_linux_postgres_and_redis() -> None:
    config = default_runtime_config()
    validation = validate_runtime_config(config)
    local = config.profile("local_macos")
    linux = config.profile("linux_0_13")

    assert validation["ok"] is True
    assert local.platform == "macos"
    assert linux.platform == "linux"
    assert linux.public_host == "0.13"
    assert local.postgres.enabled and linux.postgres.enabled
    assert local.redis.enabled and linux.redis.enabled
    assert local.redis.non_authoritative is True
    assert linux.redis.non_authoritative is True
    assert any(plan.redis_sync == "disabled_ephemeral_cache_must_be_rebuilt" for plan in config.sync_plans)


def test_v20_ops_env_overrides_do_not_render_secret_values(monkeypatch) -> None:
    monkeypatch.setenv("V20_ENV", "linux_0_13")
    monkeypatch.setenv("V20_PUBLIC_HOST", "0.13")
    monkeypatch.setenv("V20_PORT", "9021")
    monkeypatch.setenv("V20_POSTGRES_DB", "qiazhi_v20_test")
    monkeypatch.setenv("V20_REDIS_DB", "21")

    config = load_runtime_config_from_env()
    profile = config.profile("linux_0_13")
    payload = profile.to_dict()

    assert config.active_profile == "linux_0_13"
    assert profile.port == 9021
    assert profile.postgres.database == "qiazhi_v20_test"
    assert profile.redis.db == 21
    assert payload["postgres"]["secret_policy"] == "env_names_only_no_secret_values"
    assert payload["redis"]["secret_policy"] == "env_names_only_no_secret_values"


def test_v20_dependency_readiness_hides_secret_values(monkeypatch) -> None:
    monkeypatch.setenv("V20_DATABASE_URL", "postgres://secret-user:secret-pass@localhost/db")
    monkeypatch.setenv("V20_REDIS_URL", "redis://:secret@localhost:6379/0")

    report = dependency_readiness_report()
    text = str(report)

    assert report["postgres"]["ready_for_connection"] is True
    assert report["redis"]["ready_for_connection"] is True
    assert report["runtime_mutation"] is False
    assert "secret-pass" not in text
    assert "redis://:secret" not in text


def test_v20_dependency_endpoint_is_read_only() -> None:
    client = TestClient(app)
    response = client.get("/api/v20/runtime/dependencies")

    assert response.status_code == 200
    data = response.json()
    assert data["runtime_mutation"] is False
    assert data["postgres"]["connection_policy"] == "explicit_repository_command_only"
    assert data["redis"]["connection_policy"] == "ephemeral_cache_queue_lock_only"


def test_v20_sync_readiness_keeps_redis_ephemeral_and_postgres_reviewed() -> None:
    report = sync_readiness_report(default_runtime_config())

    assert report["status"] == "ready_for_manual_sync"
    assert report["runtime_mutation"] is False
    assert report["direction_count"] == 2
    assert all(row["redis_sync"] == "disabled_ephemeral_cache_must_be_rebuilt" for row in report["directions"])
    assert all("confirm_git_status_clean" in row["preflight"] for row in report["directions"])
    assert all("secrets" in row["protected_scopes"] for row in report["directions"])


def test_v20_sync_readiness_endpoint_is_read_only() -> None:
    client = TestClient(app)
    response = client.get("/api/v20/ops/sync-readiness")

    assert response.status_code == 200
    data = response.json()
    assert data["runtime_mutation"] is False
    assert data["direction_count"] == 2
    assert "NO_SECRET_VALUES_RENDERED" in data["guardrails"]
