from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Request, Response


QIAZHI_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUTH_PATH = QIAZHI_ROOT / "v20" / ".runtime" / "local" / "auth.json"
SESSION_COOKIE = "v20_session"


def auth_status(request: Request) -> dict[str, object]:
    session = _session_from_request(request)
    return {
        "version": "v20.auth_status.v1",
        "authenticated": bool(session),
        "session": _public_session(session),
        "runtime_mutation": False,
        "guardrails": ["LOCAL_AUTH_STATUS_ONLY", "NO_PASSWORD_VALUES_RENDERED"],
    }


def guest_login(response: Response, *, locale: str = "zh") -> dict[str, object]:
    return _create_session_response(
        response,
        user_id=f"guest_{secrets.token_hex(6)}",
        username="guest",
        role="user",
        locale=locale,
    )


def register_user(payload: dict[str, Any], response: Response) -> dict[str, object]:
    username = _clean_username(payload.get("username"))
    password = str(payload.get("password") or "")
    role = _clean_role(payload.get("role"))
    locale = _clean_locale(payload.get("locale"))
    if not username or len(password) < 4:
        return _auth_error("invalid_credentials", "Username and a password with at least 4 characters are required.")
    store = _read_store()
    if username in store["users"]:
        return _auth_error("user_exists", "User already exists.")
    user_id = f"user_{secrets.token_hex(8)}"
    salt = secrets.token_hex(16)
    store["users"][username] = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "password_hash": _password_hash(password, salt),
        "salt": salt,
        "created_at": _now(),
    }
    _write_store(store)
    return _create_session_response(response, user_id=user_id, username=username, role=role, locale=locale)


def password_login(payload: dict[str, Any], response: Response) -> dict[str, object]:
    username = _clean_username(payload.get("username"))
    password = str(payload.get("password") or "")
    locale = _clean_locale(payload.get("locale"))
    store = _read_store()
    user = store["users"].get(username)
    if not user:
        return _auth_error("login_failed", "User not found.")
    expected = str(user.get("password_hash") or "")
    actual = _password_hash(password, str(user.get("salt") or ""))
    if not hmac.compare_digest(expected, actual):
        return _auth_error("login_failed", "Password is incorrect.")
    return _create_session_response(
        response,
        user_id=str(user.get("user_id") or username),
        username=username,
        role=_clean_role(user.get("role")),
        locale=locale,
    )


def logout(response: Response, request: Request) -> dict[str, object]:
    token = request.cookies.get(SESSION_COOKIE, "")
    store = _read_store()
    if token in store["sessions"]:
        del store["sessions"][token]
        _write_store(store)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"version": "v20.auth_logout.v1", "ok": True, "runtime_mutation": True}


def _create_session_response(
    response: Response,
    *,
    user_id: str,
    username: str,
    role: str,
    locale: str,
) -> dict[str, object]:
    token = secrets.token_urlsafe(24)
    session = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "locale": locale,
        "created_at": _now(),
    }
    store = _read_store()
    store["sessions"][token] = session
    _write_store(store)
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", path="/")
    return {
        "version": "v20.auth_session.v1",
        "ok": True,
        "session": _public_session(session),
        "runtime_mutation": True,
        "guardrails": ["LOCAL_SESSION_ONLY", "NO_PASSWORD_VALUES_RENDERED"],
    }


def _session_from_request(request: Request) -> dict[str, object] | None:
    token = request.cookies.get(SESSION_COOKIE, "")
    if not token:
        return None
    session = _read_store()["sessions"].get(token)
    return dict(session) if isinstance(session, dict) else None


def _public_session(session: dict[str, object] | None) -> dict[str, object]:
    if not session:
        return {}
    return {
        "user_id": session.get("user_id", ""),
        "username": session.get("username", ""),
        "role": session.get("role", "user"),
        "locale": session.get("locale", "zh"),
    }


def _read_store() -> dict[str, dict[str, object]]:
    path = Path(os.getenv("V20_AUTH_STORE", str(DEFAULT_AUTH_PATH)))
    if not path.exists():
        return {"users": {}, "sessions": {}}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        "users": raw.get("users", {}) if isinstance(raw.get("users"), dict) else {},
        "sessions": raw.get("sessions", {}) if isinstance(raw.get("sessions"), dict) else {},
    }


def _write_store(payload: dict[str, object]) -> None:
    path = Path(os.getenv("V20_AUTH_STORE", str(DEFAULT_AUTH_PATH)))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _password_hash(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def _clean_username(value: object) -> str:
    return str(value or "").strip().lower()[:80]


def _clean_role(value: object) -> str:
    role = str(value or "user").strip().lower()
    return role if role in {"user", "analyst", "admin"} else "user"


def _clean_locale(value: object) -> str:
    locale = str(value or "zh").strip().lower()
    return locale if locale in {"zh", "en", "ko"} else "zh"


def _auth_error(code: str, message: str) -> dict[str, object]:
    return {"version": "v20.auth_error.v1", "ok": False, "code": code, "message": message, "runtime_mutation": False}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
