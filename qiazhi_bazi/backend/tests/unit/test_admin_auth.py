"""Admin HTTP 鉴权：未配置 token 时不得放行。"""
from __future__ import annotations

import os

import pytest
from fastapi import HTTPException

from app.api import admin_auth


def test_admin_token_guard_rejects_when_token_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QIAZHI_ADMIN_TOKEN", raising=False)
    with pytest.raises(HTTPException) as ei:
        admin_auth.admin_token_guard(None)
    assert ei.value.status_code == 503


def test_admin_token_guard_rejects_when_token_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QIAZHI_ADMIN_TOKEN", "   ")
    with pytest.raises(HTTPException) as ei:
        admin_auth.admin_token_guard(None)
    assert ei.value.status_code == 503


def test_admin_token_guard_rejects_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QIAZHI_ADMIN_TOKEN", "secret")
    with pytest.raises(HTTPException) as ei:
        admin_auth.admin_token_guard("wrong")
    assert ei.value.status_code == 401


def test_admin_token_guard_accepts_match(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QIAZHI_ADMIN_TOKEN", "secret")
    admin_auth.admin_token_guard("secret")
