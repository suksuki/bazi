from __future__ import annotations

import json
import os

import pytest

from app.core.llm_ollama import merge_ollama_chat_options


def test_merge_ollama_chat_options_request_overrides_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QIAZHI_OLLAMA_FAST_LITE", raising=False)
    monkeypatch.delenv("QIAZHI_OLLAMA_OPTIONS_JSON", raising=False)
    out = merge_ollama_chat_options(
        temperature=0.2,
        num_predict=100,
        runtime_options={"num_ctx": 8192, "num_batch": 64},
        request_options={"num_ctx": 1024},
    )
    assert out["temperature"] == 0.2
    assert out["num_predict"] == 100
    assert out["num_ctx"] == 1024
    assert out["num_batch"] == 64


def test_merge_ollama_fast_lite_sets_num_ctx(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QIAZHI_OLLAMA_FAST_LITE", "1")
    monkeypatch.delenv("QIAZHI_OLLAMA_OPTIONS_JSON", raising=False)
    out = merge_ollama_chat_options(temperature=0.1, num_predict=50, request_options={"num_batch": 32})
    assert out["num_ctx"] == 2048
    assert out["num_batch"] == 32


def test_merge_ollama_options_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QIAZHI_OLLAMA_FAST_LITE", raising=False)
    monkeypatch.setenv("QIAZHI_OLLAMA_OPTIONS_JSON", json.dumps({"num_ctx": 4096}))
    out = merge_ollama_chat_options(temperature=0.3, num_predict=80)
    assert out["num_ctx"] == 4096
