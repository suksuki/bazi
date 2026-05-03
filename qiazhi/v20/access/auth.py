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
LEGACY_V19_SESSION_COOKIE = "v19_auth_session"
DEFAULT_V19_AUTH_PATH = QIAZHI_ROOT / "v19" / ".runtime" / "auth_sessions.json"


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
    if role == "admin":
        return _auth_error("admin_registration_disabled", "Admin is a singleton account and cannot be selected during registration.")
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
    if user.get("login_policy") == "imported_v19_session_only_password_reset_required":
        return _auth_error("password_reset_required", "This V19 user was imported from session metadata and needs a V20 password reset.")
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
    response.delete_cookie(LEGACY_V19_SESSION_COOKIE, path="/")
    return {"version": "v20.auth_logout.v1", "ok": True, "runtime_mutation": True}


def v19_auth_migration_preview(source_path: Path | None = None) -> dict[str, object]:
    path = source_path or DEFAULT_V19_AUTH_PATH
    sessions = _read_v19_auth_sessions(path)
    users = _unique_v19_users(sessions)
    return {
        "version": "v20.v19_auth_migration_preview.v1",
        "status": "ready" if path.exists() else "source_missing",
        "source_path": str(path),
        "session_count": len(sessions),
        "user_count": len(users),
        "role_counts": _role_counts(sessions),
        "sample_users": [_public_session(row) for row in users[:8]],
        "target_store": str(Path(os.getenv("V20_AUTH_STORE", str(DEFAULT_AUTH_PATH)))),
        "runtime_mutation": False,
        "guardrails": [
            "PREVIEW_ONLY",
            "NO_SESSION_TOKENS_RENDERED",
            "NO_PASSWORD_VALUES_AVAILABLE_IN_V19_AUTH_SESSIONS",
        ],
    }


def import_v19_auth_sessions(
    *,
    apply: bool = False,
    source_path: Path | None = None,
    admin_password: str = "",
) -> dict[str, object]:
    path = source_path or DEFAULT_V19_AUTH_PATH
    sessions = _read_v19_auth_sessions(path)
    users = _unique_v19_users(sessions)
    payload = {
        "version": "v20.v19_auth_session_import.v1",
        "status": "dry_run",
        "source_path": str(path),
        "session_count": len(sessions),
        "user_count": len(users),
        "apply": apply,
        "admin_password_present": bool(admin_password),
        "runtime_mutation": bool(apply),
        "guardrails": [
            "EXPLICIT_APPLY_REQUIRED",
            "NO_PASSWORD_VALUES_AVAILABLE_IN_V19_AUTH_SESSIONS",
            "NO_SESSION_TOKENS_RENDERED",
            "V19_SOURCE_IS_READ_ONLY",
        ],
    }
    if not apply:
        return payload
    store = _read_store()
    _dedupe_imported_v19_users(store)
    imported_users = 0
    imported_sessions = 0
    for user in users:
        username = _clean_username(user.get("username")) or str(user.get("user_id") or "")
        if not username:
            continue
        user_id = str(user.get("user_id") or username)
        role = _map_v19_role(user.get("role"))
        store_key = _v19_user_store_key(store, username, user_id, role)
        existing = store["users"].get(store_key)
        if not existing:
            store["users"][store_key] = {
                "store_key": store_key,
                "user_id": str(user.get("user_id") or username),
                "username": username,
                "role": role,
                "password_hash": "",
                "salt": "",
                "login_policy": "imported_v19_session_only_password_reset_required",
                "imported_from": "v19.auth_sessions",
                "created_at": user.get("created_at") or _now(),
            }
            imported_users += 1
    for token, session in sessions.items():
        normalized = {
            "user_id": str(session.get("user_id") or ""),
            "username": str(session.get("username") or ""),
            "role": _map_v19_role(session.get("role")),
            "locale": "zh",
            "legacy_role": str(session.get("role") or ""),
            "legacy_token_source": "v19_auth_session",
            "created_at": session.get("created_at") or _now(),
            "updated_at": session.get("updated_at") or session.get("created_at") or _now(),
        }
        if token not in store["sessions"]:
            imported_sessions += 1
        store["sessions"][token] = normalized
    admin_password_configured = False
    if admin_password:
        salt = secrets.token_hex(16)
        prior = dict(store["users"].get("admin") or {})
        store["users"]["admin"] = {
            **prior,
            "store_key": "admin",
            "user_id": "admin",
            "username": "admin",
            "role": "admin",
            "password_hash": _password_hash(admin_password, salt),
            "salt": salt,
            "login_policy": "local_password_enabled",
            "imported_from": "v19.admin_fixed_password",
            "updated_at": _now(),
        }
        admin_password_configured = True
    _write_store(store)
    return payload | {
        "status": "imported",
        "imported_users": imported_users,
        "imported_sessions": imported_sessions,
        "admin_password_configured": admin_password_configured,
        "recognized_cookie_names": [SESSION_COOKIE, LEGACY_V19_SESSION_COOKIE],
    }


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
    token = request.cookies.get(SESSION_COOKIE, "") or request.cookies.get(LEGACY_V19_SESSION_COOKIE, "")
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


def _read_v19_auth_sessions(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    return {str(key): value for key, value in raw.items() if isinstance(value, dict)}


def _unique_v19_users(sessions: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    seen: set[tuple[str, str, str]] = set()
    users: list[dict[str, object]] = []
    for session in sessions.values():
        user_id = str(session.get("user_id") or "")
        username = str(session.get("username") or user_id or "")
        role = str(session.get("role") or "user")
        key = (user_id, username, role)
        if key in seen:
            continue
        seen.add(key)
        users.append(
            {
                "user_id": user_id,
                "username": username,
                "role": _map_v19_role(role),
                "created_at": session.get("created_at") or "",
            }
        )
    return users


def _role_counts(sessions: dict[str, dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for session in sessions.values():
        role = _map_v19_role(session.get("role"))
        counts[role] = counts.get(role, 0) + 1
    return counts


def _map_v19_role(value: object) -> str:
    role = str(value or "user").strip().lower()
    if role == "practitioner":
        return "analyst"
    if role == "admin":
        return "admin"
    return "user"


def _v19_user_store_key(store: dict[str, dict[str, object]], username: str, user_id: str, role: str) -> str:
    for key, row in store["users"].items():
        if (
            str(row.get("user_id") or "") == user_id
            and _clean_username(row.get("username")) == username
            and str(row.get("role") or "") == role
            and str(row.get("imported_from") or "").startswith("v19.")
        ):
            return key
    existing = store["users"].get(username)
    if not existing:
        return username
    if str(existing.get("user_id") or "") == user_id and str(existing.get("role") or "") == role:
        return username
    suffix = user_id or role
    key = f"{username}__{suffix}"
    if key not in store["users"]:
        return key
    digest = hashlib.sha256(f"{username}:{user_id}:{role}".encode("utf-8")).hexdigest()[:8]
    return f"{username}__{digest}"


def _dedupe_imported_v19_users(store: dict[str, dict[str, object]]) -> None:
    seen: dict[tuple[str, str, str], str] = {}
    remove: list[str] = []
    for key, row in store["users"].items():
        imported_from = str(row.get("imported_from") or "")
        if not imported_from.startswith("v19.auth_sessions"):
            continue
        identity = (
            str(row.get("user_id") or ""),
            _clean_username(row.get("username")),
            str(row.get("role") or ""),
        )
        if identity in seen:
            remove.append(key)
        else:
            seen[identity] = key
    for key in remove:
        store["users"].pop(key, None)


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
