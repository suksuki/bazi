"""_collect_llm_model_names：Ollama /api/tags 与 OpenAI /v1/models 组合顺序（httpx 打桩）。"""
from __future__ import annotations

import asyncio

import httpx
import pytest
from fastapi import HTTPException


class _Resp:
    def __init__(self, payload: dict | None = None, *, boom: bool = False) -> None:
        self._payload = payload or {}
        self._boom = boom

    def raise_for_status(self) -> None:
        if self._boom:
            raise RuntimeError("bad status")

    def json(self) -> dict:
        return self._payload


class _StubClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def get(self, url: str, headers: dict | None = None) -> _Resp:
        raise NotImplementedError


class _AsyncCM:
    def __init__(self, stub: _StubClient) -> None:
        self._stub = stub

    async def __aenter__(self) -> _StubClient:
        return self._stub

    async def __aexit__(self, *args: object) -> None:
        return None


def _patch_async_client(monkeypatch: pytest.MonkeyPatch, stub: _StubClient) -> None:
    def _factory(*args: object, **kwargs: object) -> _AsyncCM:
        return _AsyncCM(stub)

    monkeypatch.setattr(httpx, "AsyncClient", _factory)


class _Tags11434(_StubClient):
    async def get(self, url: str, headers: dict | None = None) -> _Resp:
        self.calls.append(url)
        assert "api/tags" in url
        return _Resp({"models": [{"model": "alpha"}, {"model": "beta"}]})


def test_collect_llm_models_11434_prefers_api_tags(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _Tags11434()
    _patch_async_client(monkeypatch, stub)

    from app.api import admin as admin_module

    out = asyncio.run(admin_module._collect_llm_model_names("http://127.0.0.1:11434/v1", None))
    assert out == ["alpha", "beta"]
    assert len(stub.calls) == 1


class _TagsNameOnly11434(_StubClient):
    """Ollama 部分版本仅返回 name，无 model 键。"""

    async def get(self, url: str, headers: dict | None = None) -> _Resp:
        self.calls.append(url)
        if "api/tags" in url:
            return _Resp({"models": [{"name": "qwen2.5:7b", "size": 1}]})
        return _Resp(None, boom=True)


def test_collect_llm_models_ollama_tags_accepts_name_field(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _TagsNameOnly11434()
    _patch_async_client(monkeypatch, stub)

    from app.api import admin as admin_module

    out = asyncio.run(admin_module._collect_llm_model_names("http://127.0.0.1:11434/v1", None))
    assert out == ["qwen2.5:7b"]


def test_collect_llm_models_empty_tags_falls_back_to_openai_on_11434(monkeypatch: pytest.MonkeyPatch) -> None:
    """/api/tags 返回空列表时继续请求 /v1/models。"""

    class _EmptyThenOpenAi(_StubClient):
        async def get(self, url: str, headers: dict | None = None) -> _Resp:
            self.calls.append(url)
            if "api/tags" in url:
                return _Resp({"models": []})
            if url.endswith("/v1/models"):
                return _Resp({"data": [{"id": "llama3"}]})
            return _Resp(None, boom=True)

    stub = _EmptyThenOpenAi()
    _patch_async_client(monkeypatch, stub)

    from app.api import admin as admin_module

    out = asyncio.run(admin_module._collect_llm_model_names("http://127.0.0.1:11434/v1", None))
    assert out == ["llama3"]
    assert any("api/tags" in c for c in stub.calls)
    assert any(c.endswith("/v1/models") for c in stub.calls)


class _OpenAiV1Models(_StubClient):
    async def get(self, url: str, headers: dict | None = None) -> _Resp:
        self.calls.append(url)
        if url.endswith("/v1/models"):
            return _Resp({"data": [{"id": "gpt-test"}]})
        return _Resp(None, boom=True)


def test_collect_llm_models_without_v1_suffix_tries_v1_models(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _OpenAiV1Models()
    _patch_async_client(monkeypatch, stub)

    from app.api import admin as admin_module

    out = asyncio.run(admin_module._collect_llm_model_names("http://127.0.0.1:9", None))
    assert out == ["gpt-test"]
    assert stub.calls[0] == "http://127.0.0.1:9/v1/models"


class _OpenAiFailsThenTags(_StubClient):
    async def get(self, url: str, headers: dict | None = None) -> _Resp:
        self.calls.append(url)
        if url.endswith("/v1/models") or url == "http://127.0.0.1:8/models":
            return _Resp(None, boom=True)
        if url.endswith("/api/tags"):
            return _Resp({"models": [{"model": "phi"}]})
        return _Resp(None, boom=True)


def test_collect_llm_models_falls_back_to_tags_when_openai_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _OpenAiFailsThenTags()
    _patch_async_client(monkeypatch, stub)

    from app.api import admin as admin_module

    out = asyncio.run(admin_module._collect_llm_model_names("http://127.0.0.1:8", None))
    assert out == ["phi"]
    assert "http://127.0.0.1:8/api/tags" in stub.calls


class _AllBad(_StubClient):
    async def get(self, url: str, headers: dict | None = None) -> _Resp:
        self.calls.append(url)
        return _Resp(None, boom=True)


def test_collect_llm_models_raises_502_when_all_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _AllBad()
    _patch_async_client(monkeypatch, stub)

    from app.api import admin as admin_module

    with pytest.raises(HTTPException) as ei:
        asyncio.run(admin_module._collect_llm_model_names("http://127.0.0.1:7", None))
    assert ei.value.status_code == 502
    assert "模型列表获取失败" in str(ei.value.detail)
