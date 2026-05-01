from __future__ import annotations

from v20.ops.config import load_runtime_config_from_env
from v20.ops.profiles import default_runtime_config, validate_runtime_config


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
