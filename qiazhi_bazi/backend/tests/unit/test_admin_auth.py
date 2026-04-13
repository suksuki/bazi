"""Admin HTTP 鉴权。"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api import admin_auth


def _non_prod(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QIAZHI_ENV", raising=False)
    monkeypatch.delenv("ENV", raising=False)


def test_admin_token_guard_rejects_when_token_unset_and_header_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    _non_prod(monkeypatch)
    monkeypatch.delenv("QIAZHI_ADMIN_TOKEN", raising=False)
    with pytest.raises(HTTPException) as ei:
        admin_auth.admin_token_guard(None)
    assert ei.value.status_code == 401


def test_admin_token_guard_rejects_when_token_empty_uses_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    _non_prod(monkeypatch)
    monkeypatch.setenv("QIAZHI_ADMIN_TOKEN", "   ")
    with pytest.raises(HTTPException) as ei:
        admin_auth.admin_token_guard(None)
    assert ei.value.status_code == 401


def test_admin_token_guard_accepts_fallback_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    _non_prod(monkeypatch)
    monkeypatch.delenv("QIAZHI_ADMIN_TOKEN", raising=False)
    admin_auth.admin_token_guard("local-dev-qiazhi-admin")


def test_admin_token_guard_rejects_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    _non_prod(monkeypatch)
    monkeypatch.setenv("QIAZHI_ADMIN_TOKEN", "secret")
    with pytest.raises(HTTPException) as ei:
        admin_auth.admin_token_guard("wrong")
    assert ei.value.status_code == 401


def test_admin_token_guard_accepts_match(monkeypatch: pytest.MonkeyPatch) -> None:
    _non_prod(monkeypatch)
    monkeypatch.setenv("QIAZHI_ADMIN_TOKEN", "secret")
    admin_auth.admin_token_guard("secret")


def test_admin_token_guard_production_requires_configured_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QIAZHI_ENV", "production")
    monkeypatch.delenv("QIAZHI_ADMIN_TOKEN", raising=False)
    with pytest.raises(HTTPException) as ei:
        admin_auth.admin_token_guard("local-dev-qiazhi-admin")
    assert ei.value.status_code == 503


def test_admin_token_guard_production_accepts_configured_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QIAZHI_ENV", "production")
    monkeypatch.setenv("QIAZHI_ADMIN_TOKEN", "prod-secret-xyz")
    admin_auth.admin_token_guard("prod-secret-xyz")
