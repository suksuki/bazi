from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

from fastapi import Request, Response

from v20.access.auth import auth_status, import_v19_auth_sessions, password_login, register_user


def test_v20_auth_register_uses_bcrypt_hash(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_AUTH_STORE", str(tmp_path / "auth.json"))
    monkeypatch.setenv("V20_BCRYPT_ROUNDS", "4")

    result = register_user(
        {"username": "secure_user", "password": "pass1234", "role": "user", "locale": "zh"},
        Response(),
    )
    store = json.loads((tmp_path / "auth.json").read_text(encoding="utf-8"))
    user = store["users"]["secure_user"]

    assert result["ok"] is True
    assert user["password_hash_algorithm"] == "bcrypt.v20"
    assert user["password_hash"].startswith("$2")
    assert user["salt"] == ""
    session = next(iter(store["sessions"].values()))
    assert session["expires_at"]


def test_v20_auth_login_upgrades_legacy_sha256_hash(tmp_path, monkeypatch) -> None:
    auth_path = tmp_path / "auth.json"
    monkeypatch.setenv("V20_AUTH_STORE", str(auth_path))
    monkeypatch.setenv("V20_BCRYPT_ROUNDS", "4")
    password = "legacy1234"
    salt = "abc123"
    legacy_hash = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    auth_path.write_text(
        json.dumps(
            {
                "users": {
                    "legacy_user": {
                        "user_id": "legacy_user",
                        "username": "legacy_user",
                        "role": "user",
                        "password_hash": legacy_hash,
                        "salt": salt,
                    },
                },
                "sessions": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = password_login({"username": "legacy_user", "password": password}, Response())
    store = json.loads(auth_path.read_text(encoding="utf-8"))
    user = store["users"]["legacy_user"]

    assert result["ok"] is True
    assert user["password_hash_algorithm"] == "bcrypt.v20"
    assert user["password_hash"].startswith("$2")
    assert user["password_hash"] != legacy_hash
    assert user["salt"] == ""
    assert user["updated_at"]


def test_v20_auth_imported_admin_uses_bcrypt_hash(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_AUTH_STORE", str(tmp_path / "auth.json"))
    monkeypatch.setenv("V20_BCRYPT_ROUNDS", "4")

    result = import_v19_auth_sessions(apply=True, admin_password="adminpw")
    store = json.loads((tmp_path / "auth.json").read_text(encoding="utf-8"))
    admin = store["users"]["admin"]

    assert result["admin_password_configured"] is True
    assert admin["password_hash_algorithm"] == "bcrypt.v20"
    assert admin["password_hash"].startswith("$2")
    assert admin["salt"] == ""
    imported_session = next(iter(store["sessions"].values()))
    assert imported_session["expires_at"]


def test_v20_auth_expired_session_is_rejected_and_removed(tmp_path, monkeypatch) -> None:
    auth_path = tmp_path / "auth.json"
    monkeypatch.setenv("V20_AUTH_STORE", str(auth_path))
    expired = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
    auth_path.write_text(
        json.dumps(
            {
                "users": {},
                "sessions": {
                    "expired-token": {
                        "user_id": "u1",
                        "username": "u1",
                        "role": "user",
                        "locale": "zh",
                        "created_at": expired,
                        "expires_at": expired,
                    },
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    request = Request({"type": "http", "headers": [(b"cookie", b"v20_session=expired-token")]})

    result = auth_status(request)
    store = json.loads(auth_path.read_text(encoding="utf-8"))

    assert result["authenticated"] is False
    assert "expired-token" not in store["sessions"]
    assert "SESSION_EXPIRY_ENFORCED" in result["guardrails"]
