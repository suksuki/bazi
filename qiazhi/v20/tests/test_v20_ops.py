from __future__ import annotations

import json

from fastapi.testclient import TestClient

from v20.llm.client import call_structured_llm
from v20.llm.contracts import ANSWER_PLAN_REWRITE
from v20.llm.provider import LLMProviderConfig, llm_provider_readiness_report, resolve_llm_base_url
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
    assert report["llm"]["runtime_mutation"] is False
    assert report["runtime_mutation"] is False
    assert "secret-pass" not in text
    assert "redis://:secret" not in text


def test_v20_llm_provider_readiness_hides_secret_values(monkeypatch) -> None:
    monkeypatch.setenv("V20_LLM_ENABLED", "1")
    monkeypatch.setenv("V20_LLM_EXECUTE", "1")
    monkeypatch.setenv("V20_LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("V20_LLM_BASE_URL", "https://llm.example.test/v1")
    monkeypatch.setenv("V20_LLM_API_KEY", "secret-llm-key")
    monkeypatch.setenv("V20_LLM_MODEL", "gpt-compatible")

    report = llm_provider_readiness_report()
    text = str(report)

    assert report["ready_for_connection"] is True
    assert report["execute_llm"] is True
    assert report["resolved_base_url"] == "https://llm.example.test/v1"
    assert report["api_key_env"] == "V20_LLM_API_KEY"
    assert "secret-llm-key" not in text


def test_v20_llm_base_url_resolution_matches_v19_shape() -> None:
    assert resolve_llm_base_url("", "127.0.0.1", 11434) == "http://127.0.0.1:11434/v1"
    assert resolve_llm_base_url("http://localhost:8000/v1", "ignored", 1) == "http://localhost:8000/v1"


def test_v20_ollama_llm_calls_disable_thinking_stream(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self) -> bytes:
            return json.dumps({"choices": [{"message": {"content": "{\"text\":\"safe rewrite\"}"}}]}).encode()

    def fake_urlopen(request, timeout):  # noqa: ANN001
        captured.update(json.loads(request.data.decode()))
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("v20.llm.client.urllib.request.urlopen", fake_urlopen)
    result = call_structured_llm(
        ANSWER_PLAN_REWRITE,
        {"task": "answer_plan_rewrite", "context": {}, "instruction": "Rewrite safely."},
        config=LLMProviderConfig(
            enabled=True,
            execute_llm=True,
            provider="ollama",
            host="127.0.0.1",
            port=11434,
            base_url="",
            model="gemma4:latest",
            embedding_model="",
        ),
    )

    assert result["status"] == "accepted"
    assert captured["think"] is False
    assert captured["response_format"] == {"type": "json_object"}
    assert captured["timeout"] == 8.0


def test_v20_ollama_llm_calls_fallback_to_native_chat(monkeypatch) -> None:
    endpoints: list[str] = []
    native_body: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self) -> bytes:
            return json.dumps({"message": {"content": "{\"text\":\"native safe rewrite\"}"}}).encode()

    def fake_urlopen(request, timeout):  # noqa: ANN001
        endpoints.append(request.full_url)
        if request.full_url.endswith("/chat/completions"):
            raise TimeoutError("openai-compatible timed out")
        native_body.update(json.loads(request.data.decode()))
        native_body["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("v20.llm.client.urllib.request.urlopen", fake_urlopen)
    result = call_structured_llm(
        ANSWER_PLAN_REWRITE,
        {"task": "answer_plan_rewrite", "context": {}, "instruction": "Rewrite safely."},
        config=LLMProviderConfig(
            enabled=True,
            execute_llm=True,
            provider="ollama",
            host="127.0.0.1",
            port=11434,
            base_url="",
            model="gemma4:latest",
            embedding_model="",
        ),
    )

    assert result["status"] == "accepted"
    assert result["model"] == "gemma4:latest"
    assert result["fallback_reason"] == "openai_compatible_failed:TimeoutError"
    assert endpoints[-1].endswith("/api/chat")
    assert native_body["stream"] is False
    assert native_body["think"] is False
    assert native_body["options"]["num_predict"] == 800


def test_v20_dependency_endpoint_is_read_only() -> None:
    client = TestClient(app)
    response = client.get("/api/v20/runtime/dependencies")

    assert response.status_code == 200
    data = response.json()
    assert data["runtime_mutation"] is False
    assert data["postgres"]["connection_policy"] == "explicit_repository_command_only"
    assert data["redis"]["connection_policy"] == "ephemeral_cache_queue_lock_only"
    assert data["llm"]["connection_policy"] == "explicit_llm_task_only_no_healthcheck_network_call"


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
