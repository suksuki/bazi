from __future__ import annotations

from app.llm.client import QwenClient


def test_headers_omit_authorization_when_api_key_empty() -> None:
    c = QwenClient(base_url="http://127.0.0.1:11434/v1", api_key="", model="m")
    h = c._headers()
    assert "Authorization" not in h
    assert h.get("Content-Type") == "application/json"


def test_headers_bearer_when_api_key_present() -> None:
    c = QwenClient(base_url="http://127.0.0.1:11434/v1", api_key="sk-test", model="m")
    assert c._headers().get("Authorization") == "Bearer sk-test"
