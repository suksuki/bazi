from __future__ import annotations

import json

from v20.llm.provider import load_llm_provider_config_from_env
from v20.ops import admin_status
from v20.ops.admin_config import admin_config_status, save_admin_database_config, save_admin_llm_config
from v20.ops.config import load_runtime_config_from_env


def test_v20_admin_config_saves_runtime_overrides_without_rendering_secrets(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_ADMIN_CONFIG_PATH", str(tmp_path / "admin_config.json"))
    monkeypatch.setenv("V20_POSTGRES_PASSWORD", "")
    monkeypatch.setenv("V20_LLM_API_KEY", "")

    db = save_admin_database_config(
        {
            "enabled": True,
            "host": "db.internal",
            "port": 5433,
            "database": "qiazhi_admin",
            "username": "qiazhi_admin",
            "password": "secret-db-pass",
        }
    )
    llm = save_admin_llm_config(
        {
            "enabled": True,
            "execute_llm": True,
            "provider": "openai_compatible",
            "base_url": "https://llm.example.test/v1",
            "model": "qwen-admin",
            "api_key": "secret-llm-key",
        }
    )
    status = admin_config_status()
    runtime = load_runtime_config_from_env()
    provider = load_llm_provider_config_from_env()

    rendered = json.dumps({"db": db, "llm": llm, "status": status}, ensure_ascii=False)
    assert "secret-db-pass" not in rendered
    assert "secret-llm-key" not in rendered
    assert db["secret_fields_written"] == ["password"]
    assert llm["secret_fields_written"] == ["api_key"]
    assert status["database"]["password_configured"] is True
    assert status["llm"]["api_key_configured"] is True
    assert runtime.profile(runtime.active_profile).postgres.host == "db.internal"
    assert runtime.profile(runtime.active_profile).postgres.port == 5433
    assert provider.model == "qwen-admin"
    assert provider.execute_llm is True


def test_v20_admin_llm_test_uses_ollama_chat_without_rendering_secrets(monkeypatch) -> None:
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({"message": {"content": "测试通过"}}).encode("utf-8")

    def fake_urlopen(request, timeout=0):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setenv("V20_LLM_ENABLED", "1")
    monkeypatch.setenv("V20_ADMIN_CONFIG_PATH", "/tmp/v20_admin_config_test_missing.json")
    monkeypatch.setenv("V20_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("V20_LLM_HOST", "127.0.0.1")
    monkeypatch.setenv("V20_LLM_PORT", "11434")
    monkeypatch.setenv("V20_LLM_MODEL", "qwen-admin")
    monkeypatch.setenv("V20_LLM_API_KEY", "secret-llm-key")
    monkeypatch.setattr(admin_status.urllib.request, "urlopen", fake_urlopen)

    result = admin_status.llm_admin_test({"prompt": "ping"})
    rendered = json.dumps(result, ensure_ascii=False)

    assert result["status"] == "ok"
    assert result["sample"] == "测试通过"
    assert captured["url"].endswith("/api/chat")
    assert captured["body"]["model"] == "qwen-admin"
    assert captured["timeout"] == result["timeout_sec"]
    assert result["timeout_sec"] >= 30.0
    assert "secret-llm-key" not in rendered


def test_v20_admin_ollama_model_probe_falls_back_to_native_tags(monkeypatch) -> None:
    captured_urls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({"models": [{"name": "qwen:7b"}, {"model": "llama:latest"}]}).encode("utf-8")

    def fake_urlopen(request, timeout=0):
        captured_urls.append(request.full_url)
        if request.full_url.endswith("/v1/models"):
            raise OSError("compatible endpoint unavailable")
        return FakeResponse()

    monkeypatch.setenv("V20_LLM_ENABLED", "1")
    monkeypatch.setenv("V20_ADMIN_CONFIG_PATH", "/tmp/v20_admin_config_test_missing.json")
    monkeypatch.setenv("V20_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("V20_LLM_HOST", "127.0.0.1")
    monkeypatch.setenv("V20_LLM_PORT", "11434")
    monkeypatch.setenv("V20_LLM_MODEL", "qwen-admin")
    monkeypatch.setattr(admin_status.urllib.request, "urlopen", fake_urlopen)

    result = admin_status.llm_admin_status(probe_models=True)

    assert result["status"] == "model_probe_ready"
    assert result["models"] == [
        {"id": "qwen:7b", "owned_by": "ollama"},
        {"id": "llama:latest", "owned_by": "ollama"},
    ]
    assert captured_urls[0].endswith("/v1/models")
    assert captured_urls[1].endswith("/api/tags")
