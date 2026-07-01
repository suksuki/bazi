from __future__ import annotations

import os

from fastapi import Request

from v40.contracts.base import RoleKey
from v40.contracts.context import RoleContext, UserAppSessionContext, default_role_context


USER_APP_ROLE_HEADER = "x-v40-user-role"
USER_APP_SESSION_HEADER = "x-v40-session-id"
USER_APP_ROLE_COOKIE = "v40_user_role"
USER_APP_SESSION_COOKIE = "v40_session_id"
USER_APP_ENV_ROLE = "V40_USER_APP_ROLE"


def resolve_user_app_session_context(request: Request | None = None) -> UserAppSessionContext:
    raw_role, source = _raw_role_from_request(request)
    role_key, admin_mapped = _user_app_role(raw_role)
    session_id = _session_id_from_request(request)
    return UserAppSessionContext(
        session_id=session_id,
        role_key=role_key,
        role_context=default_role_context(role_key),
        authenticated=source.startswith(("header:", "cookie:")),
        source=source,
        admin_mapped_to_practitioner=admin_mapped,
    )


def role_context_from_payload_or_session(
    *,
    request: Request | None,
    payload_role_key: RoleKey,
    payload_role_context: RoleContext | None,
) -> tuple[RoleKey, RoleContext, UserAppSessionContext]:
    session = resolve_user_app_session_context(request)
    payload_user_role, _admin_mapped = _user_app_role(str(payload_role_key))
    if payload_role_context is not None:
        if payload_role_context.role != payload_user_role:
            return payload_user_role, default_role_context(payload_user_role), session
        return payload_role_key, payload_role_context, session
    if payload_role_key != "user":
        return payload_user_role, default_role_context(payload_user_role), session
    return session.role_key, session.role_context, session


def _raw_role_from_request(request: Request | None) -> tuple[str, str]:
    if request is not None:
        header_role = request.headers.get(USER_APP_ROLE_HEADER, "").strip()
        if header_role:
            return header_role, f"header:{USER_APP_ROLE_HEADER}"
        cookie_role = request.cookies.get(USER_APP_ROLE_COOKIE, "").strip()
        if cookie_role:
            return cookie_role, f"cookie:{USER_APP_ROLE_COOKIE}"
    env_role = os.getenv(USER_APP_ENV_ROLE, "").strip()
    if env_role:
        return env_role, f"env:{USER_APP_ENV_ROLE}"
    return "user", "default:user_app"


def _session_id_from_request(request: Request | None) -> str:
    if request is None:
        return "local-user-app-session"
    header_session = request.headers.get(USER_APP_SESSION_HEADER, "").strip()
    if header_session:
        return header_session
    cookie_session = request.cookies.get(USER_APP_SESSION_COOKIE, "").strip()
    if cookie_session:
        return cookie_session
    return "local-user-app-session"


def _user_app_role(raw_role: str) -> tuple[RoleKey, bool]:
    normalized = raw_role.strip().lower().replace("-", "_")
    if normalized == "admin":
        return "practitioner", True
    if normalized in {"guest", "visitor", "anonymous"}:
        return "guest", False
    if normalized in {"practitioner", "master", "mingli_practitioner"}:
        return "practitioner", False
    return "user", False
