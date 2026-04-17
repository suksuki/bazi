from __future__ import annotations

import asyncio
import os
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:tester@127.0.0.1/qiazhi_test")

from fastapi import HTTPException

from app.api.contracts import DbStatusRequest, LlmTestRequest
from app.services import admin_service


class _FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one(self):
        return self._value


class _FakeFetchResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeConnection:
    def __init__(self):
        self._calls = 0

    def execute(self, statement):
        sql = str(statement)
        self._calls += 1
        if "SELECT 1" in sql:
            return _FakeScalarResult(1)
        if "COUNT(*) FROM information_schema.tables" in sql:
            return _FakeScalarResult(2)
        if "COUNT(*) FROM consultation" in sql:
            return _FakeScalarResult(3)
        if "COUNT(*) FROM decision_step" in sql:
            return _FakeScalarResult(5)
        if "SELECT raw_data FROM decision_step" in sql:
            return _FakeFetchResult([({"stage": "x"},), ({"stage": "y"},)])
        if "FROM information_schema.columns" in sql:
            return _FakeFetchResult([("raw_data",), ("human_choice",)])
        raise AssertionError(f"unexpected SQL: {sql}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeEngine:
    def connect(self):
        return _FakeConnection()


class _FakeClient:
    def __init__(self, *args, **kwargs):
        self.calls = []

    async def chat(self, *, messages, temperature, max_tokens, stop):
        self.calls.append(
            {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stop": stop,
            }
        )
        return "最终结论：适合推进。"


class _FakeLogger:
    def __init__(self):
        self.logs = []

    def info(self, message, *args):
        self.logs.append(("info", message, args))

    def warning(self, message, *args):
        self.logs.append(("warning", message, args))


def test_get_db_status_payload_collects_counts(monkeypatch):
    monkeypatch.setattr(admin_service, "_engine", _FakeEngine())
    payload = admin_service.get_db_status_payload(None)
    assert payload["ok"] is True
    assert payload["counts"]["consultation"] == 3
    assert payload["counts"]["decision_step"] == 5
    assert payload["recent_raw_data"][0]["stage"] == "x"
    assert payload["jsonb_check"]["ok"] is True


def test_get_db_status_response_masks_error_for_bad_host():
    # 公网单播；勿用 203.0.113.0/24 等文档地址——在 Python 中 is_private 为 True，会误走连库逻辑导致超时
    response = admin_service.get_db_status_response(DbStatusRequest(db_url="postgresql://x:x@1.1.1.1/test"))
    assert response["ok"] is False
    assert "未放行" in response["error"] or "白名单" in response["error"] or "未在白名单" in response["error"]
    assert "***" in response["db_url"]


def test_get_db_status_response_allows_rfc1918_without_extra_env(monkeypatch):
    monkeypatch.setattr(admin_service, "_engine", _FakeEngine())
    monkeypatch.setattr(admin_service, "create_engine", lambda *_a, **_k: _FakeEngine())
    payload = admin_service.get_db_status_payload("postgresql://tester:tester@10.0.0.5:15432/qiazhi_test")
    assert payload["ok"] is True


def test_initialize_database_wraps_errors(monkeypatch):
    def _boom():
        raise RuntimeError("db init failed")

    monkeypatch.setattr(admin_service, "init_db", _boom)
    try:
        admin_service.initialize_database(None)
    except HTTPException as exc:
        assert exc.status_code == 500
        assert "db init failed" in str(exc.detail)
    else:
        raise AssertionError("expected HTTPException")


def test_execute_llm_test_returns_content_without_rewrite():
    logger = _FakeLogger()

    async def _rewrite(_client, _source, _language):
        raise AssertionError("rewrite should not be called")

    async def _compress(_client, content, _language):
        return content

    async def _ollama(*args, **kwargs):
        return ""

    with patch.object(admin_service, "QwenClient", _FakeClient):
        result = asyncio.run(
            admin_service.execute_llm_test(
                LlmTestRequest(
                    base_url="http://127.0.0.1:9999/v1",
                    api_key="x",
                    model="demo",
                    system_prompt="你是助手",
                    user_prompt="给我结论",
                    language="ZH",
                    temperature=0.1,
                    max_tokens=64,
                ),
                rewrite_final_only=_rewrite,
                compress_final_only=_compress,
                ollama_chat_no_think=_ollama,
                logger=logger,
            )
        )

    assert result["ok"] is True
    assert result["content"] == "适合推进。"
    assert result["language"] == "ZH"


def test_execute_llm_test_uses_rewrite_fallback():
    class _EmptyClient(_FakeClient):
        async def chat(self, *, messages, temperature, max_tokens, stop):
            return "思考过程：略"

    logger = _FakeLogger()

    async def _rewrite(_client, _source, _language):
        return "重写后的结论"

    async def _compress(_client, content, _language):
        return content

    async def _ollama(*args, **kwargs):
        return ""

    with patch.object(admin_service, "QwenClient", _EmptyClient):
        result = asyncio.run(
            admin_service.execute_llm_test(
                LlmTestRequest(
                    base_url="http://127.0.0.1:9999/v1",
                    api_key="x",
                    model="demo",
                    system_prompt="你是助手",
                    user_prompt="给我结论",
                    language="ZH",
                    temperature=0.1,
                    max_tokens=64,
                    fast_path=False,
                ),
                rewrite_final_only=_rewrite,
                compress_final_only=_compress,
                ollama_chat_no_think=_ollama,
                logger=logger,
            )
        )

    assert result["content"] == "重写后的结论"


def test_execute_llm_test_fast_path_skips_rewrite_when_strip_empty():
    logger = _FakeLogger()

    class _OnlyThinking(_FakeClient):
        async def chat(self, *, messages, temperature, max_tokens, stop):
            return "思考过程：略"

    async def _rewrite(_client, _source, _language):
        raise AssertionError("rewrite must not run in fast_path")

    async def _compress(_client, content, _language):
        raise AssertionError("compress must not run in fast_path")

    async def _ollama(*args, **kwargs):
        return ""

    with patch.object(admin_service, "QwenClient", _OnlyThinking):
        result = asyncio.run(
            admin_service.execute_llm_test(
                LlmTestRequest(
                    base_url="http://127.0.0.1:9999/v1",
                    api_key="x",
                    model="demo",
                    system_prompt="你是助手",
                    user_prompt="给我结论",
                    language="ZH",
                    temperature=0.1,
                    max_tokens=64,
                    fast_path=True,
                ),
                rewrite_final_only=_rewrite,
                compress_final_only=_compress,
                ollama_chat_no_think=_ollama,
                logger=logger,
            )
        )

    assert result["ok"] is True
    assert "未返回可提取" in result["content"]


def test_execute_llm_test_fast_path_skips_compress_for_long_markers():
    logger = _FakeLogger()

    async def _rewrite(_client, _source, _language):
        raise AssertionError("rewrite must not run")

    async def _compress(_client, content, _language):
        raise AssertionError("compress must not run in fast_path")

    async def _ollama(*args, **kwargs):
        return ""

    class _Long(_FakeClient):
        async def chat(self, *, messages, temperature, max_tokens, stop):
            return "一、" + ("结" * 180)

    with patch.object(admin_service, "QwenClient", _Long):
        result = asyncio.run(
            admin_service.execute_llm_test(
                LlmTestRequest(
                    base_url="http://127.0.0.1:9999/v1",
                    api_key="x",
                    model="demo",
                    system_prompt="你是助手",
                    user_prompt="给我结论",
                    language="ZH",
                    temperature=0.1,
                    max_tokens=64,
                    fast_path=True,
                ),
                rewrite_final_only=_rewrite,
                compress_final_only=_compress,
                ollama_chat_no_think=_ollama,
                logger=logger,
            )
        )

    assert result["ok"] is True
    assert len(result["content"]) <= 130
