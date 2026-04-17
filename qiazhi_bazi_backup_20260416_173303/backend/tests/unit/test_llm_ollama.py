from __future__ import annotations

import pytest

from app.core.llm_ollama import looks_like_native_ollama_base_url


@pytest.mark.parametrize(
    "url,expected",
    [
        ("", False),
        ("http://127.0.0.1:11434/v1", True),
        ("https://host:11434", True),
        ("http://127.0.0.1:8000/v1", False),
    ],
)
def test_looks_like_native_default_ports(url: str, expected: bool, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QIAZHI_OLLAMA_NATIVE_PORTS", raising=False)
    assert looks_like_native_ollama_base_url(url) is expected


def test_looks_like_native_custom_ports(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QIAZHI_OLLAMA_NATIVE_PORTS", "11435")
    assert looks_like_native_ollama_base_url("http://127.0.0.1:11435/v1")
    assert not looks_like_native_ollama_base_url("http://127.0.0.1:11434/v1")
