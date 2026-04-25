from __future__ import annotations

from typing import Any, Dict, List

from fastapi import HTTPException, Request

from v17_rebirth.backend.infrastructure.auth_db import auth_storage

ROLE_PRIORITY = {
    "user": 1,
    "manager": 2,
    "admin": 3,
}

ROLE_CAPABILITIES: Dict[str, List[str]] = {
    "user": [
        "auth.read",
        "oracle.access",
        "oracle.surface.core",
        "oracle.surface.auxiliary",
        "evidence.feedback.write",
    ],
    "manager": [
        "auth.read",
        "oracle.access",
        "oracle.surface.core",
        "oracle.surface.auxiliary",
        "oracle.surface.trace",
        "evidence.feedback.write",
        "evidence.feedback.practitioner",
        "evidence.feedback.read_all",
        "user.manage",
    ],
    "admin": [
        "auth.read",
        "oracle.access",
        "oracle.surface.core",
        "oracle.surface.auxiliary",
        "oracle.surface.trace",
        "evidence.feedback.write",
        "evidence.feedback.practitioner",
        "evidence.feedback.read_all",
        "admin.access",
        "admin.write",
        "user.manage",
    ],
}


def _ip_address(request: Request) -> str:
    forwarded = str(request.headers.get("x-forwarded-for") or "").strip()
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    client = request.client
    return str(getattr(client, "host", "") or "").strip()


def _session_token_from_request(request: Request) -> str:
    bearer = str(request.headers.get("authorization") or "").strip()
    if bearer.lower().startswith("bearer "):
        return bearer.split(" ", 1)[1].strip()
    return str(request.cookies.get("v17_session") or "").strip()


def build_user_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    role = str(row.get("role") or "user").strip().lower() or "user"
    capabilities = ROLE_CAPABILITIES.get(role, ROLE_CAPABILITIES["user"])
    oracle_surfaces = ["core", "auxiliary"]
    if role in {"manager", "admin"}:
        oracle_surfaces.append("trace")
    return {
        "id": int(row.get("id") or 0),
        "username": str(row.get("username") or "").strip(),
        "display_name": str(row.get("display_name") or "").strip() or str(row.get("username") or "").strip(),
        "email": str(row.get("email") or "").strip(),
        "role": role,
        "is_active": bool(row.get("is_active")),
        "created_at": str(row.get("created_at") or "").strip(),
        "updated_at": str(row.get("updated_at") or "").strip(),
        "last_login_at": str(row.get("last_login_at") or "").strip(),
        "latest_ip_address": str(row.get("latest_ip_address") or "").strip(),
        "latest_user_agent": str(row.get("latest_user_agent") or "").strip(),
        "latest_seen_at": str(row.get("latest_seen_at") or "").strip(),
        "capabilities": capabilities,
        "surface_access": {
            "oracle": oracle_surfaces,
            "admin": role == "admin",
            "user_management": role in {"admin", "manager"},
        },
    }


def get_request_user(request: Request) -> Dict[str, Any] | None:
    token = _session_token_from_request(request)
    if not token:
        return None
    row = auth_storage.get_user_by_session_token(token)
    if not row:
        return None
    payload = build_user_payload(row)
    payload["session_token_present"] = True
    payload["ip_address"] = _ip_address(request)
    return payload


def require_authenticated_request(request: Request) -> Dict[str, Any]:
    payload = get_request_user(request)
    if not payload:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录。")
    return payload


def require_role_request(request: Request, minimum_role: str) -> Dict[str, Any]:
    payload = require_authenticated_request(request)
    need = ROLE_PRIORITY.get(str(minimum_role or "user").strip().lower(), 1)
    actual = ROLE_PRIORITY.get(str(payload.get("role") or "user").strip().lower(), 1)
    if actual < need:
        raise HTTPException(status_code=403, detail="当前账号权限不足。")
    return payload


def require_admin_request(request: Request) -> Dict[str, Any]:
    return require_role_request(request, "admin")


def require_manager_request(request: Request) -> Dict[str, Any]:
    return require_role_request(request, "manager")
