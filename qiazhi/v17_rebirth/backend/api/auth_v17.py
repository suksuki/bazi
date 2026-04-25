from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, HTTPException, Request

from v17_rebirth.backend.infrastructure.auth_db import auth_storage
from v17_rebirth.backend.services.auth_service import (
    build_user_payload,
    get_request_user,
    require_authenticated_request,
    require_manager_request,
)

router = APIRouter(tags=["v17-auth"])


def _client_meta(request: Request) -> Dict[str, str]:
    forwarded = str(request.headers.get("x-forwarded-for") or "").strip()
    if forwarded:
        ip_address = forwarded.split(",", 1)[0].strip()
    else:
        client = request.client
        ip_address = str(getattr(client, "host", "") or "").strip()
    return {
        "ip_address": ip_address,
        "user_agent": str(request.headers.get("user-agent") or "").strip(),
    }


def _profile_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": int(row.get("id") or 0),
        "profile_name": str(row.get("profile_name") or "").strip(),
        "birth_time_iso": str(row.get("birth_time_iso") or "").strip(),
        "gender": str(row.get("gender") or "").strip(),
        "calendar_type": str(row.get("calendar_type") or "").strip(),
        "lunar_is_leap_month": bool(row.get("lunar_is_leap_month")),
        "city_name": str(row.get("city_name") or "").strip(),
        "city_code": str(row.get("city_code") or "").strip(),
        "city_group": str(row.get("city_group") or "").strip(),
        "city_longitude": row.get("city_longitude"),
        "created_at": str(row.get("created_at") or "").strip(),
        "updated_at": str(row.get("updated_at") or "").strip(),
        "last_used_at": str(row.get("last_used_at") or "").strip(),
    }


def _feedback_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": int(row.get("id") or 0),
        "user_id": int(row.get("user_id") or 0),
        "reviewer_role": str(row.get("reviewer_role") or "user").strip(),
        "reviewer_weight": float(row.get("reviewer_weight") or 1.0),
        "reviewer_username": str(row.get("reviewer_username") or "").strip(),
        "reviewer_display_name": str(row.get("reviewer_display_name") or "").strip(),
        "session_id": str(row.get("session_id") or "").strip(),
        "evidence_id": str(row.get("evidence_id") or "").strip(),
        "claim_id": str(row.get("claim_id") or "").strip(),
        "plugin_id": str(row.get("plugin_id") or "").strip(),
        "evidence_type": str(row.get("evidence_type") or "").strip(),
        "target_god": str(row.get("target_god") or "").strip(),
        "status": str(row.get("status") or "").strip(),
        "reason": str(row.get("reason") or "").strip(),
        "confidence": float(row.get("confidence") or 0.0),
        "source_title": str(row.get("source_title") or "").strip(),
        "source_summary": str(row.get("source_summary") or "").strip(),
        "chart_fingerprint": str(row.get("chart_fingerprint") or "").strip(),
        "payload": row.get("payload") if isinstance(row.get("payload"), dict) else {},
        "created_at": str(row.get("created_at") or "").strip(),
        "updated_at": str(row.get("updated_at") or "").strip(),
    }


@router.post("/v17/auth/register")
@router.post("/api/v17/auth/register")
async def register_auth_user(request: Request, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    username = str(payload.get("username") or "").strip()
    password = str(payload.get("password") or "")
    display_name = str(payload.get("display_name") or username).strip()
    email = str(payload.get("email") or "").strip()

    try:
        user = auth_storage.create_user(
            username=username,
            password=password,
            display_name=display_name,
            email=email or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    meta = _client_meta(request)
    session = auth_storage.create_session(
        user_id=int(user.get("id") or 0),
        ip_address=meta["ip_address"],
        user_agent=meta["user_agent"],
    )
    return {
        "ok": True,
        "user": build_user_payload(user),
        "session_token": session["session_token"],
        "session_expires_at": session["expires_at"],
        "bootstrap_admin": bool(user.get("bootstrap_admin")),
    }


@router.post("/v17/auth/login")
@router.post("/api/v17/auth/login")
async def login_auth_user(request: Request, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    identifier = str(payload.get("identifier") or payload.get("username") or "").strip()
    password = str(payload.get("password") or "")
    user = auth_storage.authenticate(identifier, password)
    if not user:
        raise HTTPException(status_code=401, detail="账号或密码错误。")
    meta = _client_meta(request)
    session = auth_storage.create_session(
        user_id=int(user.get("id") or 0),
        ip_address=meta["ip_address"],
        user_agent=meta["user_agent"],
    )
    return {
        "ok": True,
        "user": build_user_payload(user),
        "session_token": session["session_token"],
        "session_expires_at": session["expires_at"],
    }


@router.get("/v17/auth/me")
@router.get("/api/v17/auth/me")
async def current_auth_user(request: Request) -> Dict[str, Any]:
    user = require_authenticated_request(request)
    return {"ok": True, "user": user}


@router.post("/v17/auth/logout")
@router.post("/api/v17/auth/logout")
async def logout_auth_user(request: Request) -> Dict[str, Any]:
    raw = str(request.cookies.get("v17_session") or "").strip()
    if raw:
        auth_storage.revoke_session(raw)
    return {"ok": True}


@router.get("/v17/auth/users")
@router.get("/api/v17/auth/users")
async def list_auth_users(request: Request) -> Dict[str, Any]:
    require_manager_request(request)
    rows = [build_user_payload(row) for row in auth_storage.list_users()]
    return {"ok": True, "users": rows}


@router.get("/v17/auth/profiles")
@router.get("/api/v17/auth/profiles")
async def list_bazi_profiles(request: Request) -> Dict[str, Any]:
    user = require_authenticated_request(request)
    rows = [_profile_payload(row) for row in auth_storage.list_profiles(int(user["id"]))]
    return {"ok": True, "profiles": rows}


@router.get("/v17/auth/practitioner-feedback")
@router.get("/api/v17/auth/practitioner-feedback")
async def list_practitioner_feedback(request: Request) -> Dict[str, Any]:
    user = require_authenticated_request(request)
    query = request.query_params
    try:
        limit = int(query.get("limit") or 80)
    except Exception:
        limit = 80
    rows = auth_storage.list_practitioner_feedback(
        user_id=int(user["id"]),
        reviewer_role=str(user.get("role") or "user"),
        session_id=str(query.get("session_id") or "").strip(),
        evidence_id=str(query.get("evidence_id") or "").strip(),
        plugin_id=str(query.get("plugin_id") or "").strip(),
        scope=str(query.get("scope") or "own").strip(),
        limit=limit,
    )
    return {
        "ok": True,
        "feedback": [_feedback_payload(row) for row in rows],
        "viewer_role": str(user.get("role") or "user"),
    }


@router.post("/v17/auth/practitioner-feedback")
@router.post("/api/v17/auth/practitioner-feedback")
async def create_practitioner_feedback(request: Request, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    user = require_authenticated_request(request)
    try:
        row = auth_storage.create_practitioner_feedback(
            user_id=int(user["id"]),
            reviewer_role=str(user.get("role") or "user"),
            session_id=str(payload.get("session_id") or "").strip(),
            evidence_id=str(payload.get("evidence_id") or "").strip(),
            claim_id=str(payload.get("claim_id") or "").strip(),
            plugin_id=str(payload.get("plugin_id") or "").strip(),
            evidence_type=str(payload.get("evidence_type") or "").strip(),
            target_god=str(payload.get("target_god") or "").strip(),
            status=str(payload.get("status") or "").strip(),
            reason=str(payload.get("reason") or "").strip(),
            confidence=float(payload.get("confidence") or 0.0),
            source_title=str(payload.get("source_title") or "").strip(),
            source_summary=str(payload.get("source_summary") or "").strip(),
            chart_fingerprint=str(payload.get("chart_fingerprint") or "").strip(),
            payload=payload.get("payload") if isinstance(payload.get("payload"), dict) else {},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "feedback": _feedback_payload(row),
        "trust_tier": "practitioner" if str(user.get("role") or "") in {"manager", "admin"} else "user",
    }


@router.post("/v17/auth/profiles")
@router.post("/api/v17/auth/profiles")
async def create_bazi_profile(request: Request, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    user = require_authenticated_request(request)
    try:
        row = auth_storage.create_profile(
            user_id=int(user["id"]),
            profile_name=str(payload.get("profile_name") or "").strip(),
            birth_time_iso=str(payload.get("birth_time_iso") or "").strip(),
            gender=str(payload.get("gender") or "").strip(),
            calendar_type=str(payload.get("calendar_type") or "").strip(),
            lunar_is_leap_month=bool(payload.get("lunar_is_leap_month")),
            city_name=str(payload.get("city_name") or "").strip(),
            city_code=str(payload.get("city_code") or "").strip(),
            city_group=str(payload.get("city_group") or "").strip(),
            city_longitude=payload.get("city_longitude"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "profile": _profile_payload(row)}


@router.post("/v17/auth/profiles/{profile_id}")
@router.post("/api/v17/auth/profiles/{profile_id}")
async def update_bazi_profile(
    profile_id: int,
    request: Request,
    payload: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    user = require_authenticated_request(request)
    try:
        row = auth_storage.update_profile(
            profile_id,
            user_id=int(user["id"]),
            profile_name=str(payload.get("profile_name") or "").strip(),
            birth_time_iso=str(payload.get("birth_time_iso") or "").strip(),
            gender=str(payload.get("gender") or "").strip(),
            calendar_type=str(payload.get("calendar_type") or "").strip(),
            lunar_is_leap_month=bool(payload.get("lunar_is_leap_month")),
            city_name=str(payload.get("city_name") or "").strip(),
            city_code=str(payload.get("city_code") or "").strip(),
            city_group=str(payload.get("city_group") or "").strip(),
            city_longitude=payload.get("city_longitude"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "profile": _profile_payload(row)}


@router.post("/v17/auth/profiles/{profile_id}/delete")
@router.post("/api/v17/auth/profiles/{profile_id}/delete")
async def delete_bazi_profile(profile_id: int, request: Request) -> Dict[str, Any]:
    user = require_authenticated_request(request)
    try:
        auth_storage.delete_profile(profile_id, user_id=int(user["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "deleted_profile_id": int(profile_id)}


@router.post("/v17/auth/profiles/{profile_id}/touch")
@router.post("/api/v17/auth/profiles/{profile_id}/touch")
async def touch_bazi_profile(profile_id: int, request: Request) -> Dict[str, Any]:
    user = require_authenticated_request(request)
    try:
        row = auth_storage.touch_profile(profile_id, user_id=int(user["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "profile": _profile_payload(row)}


@router.post("/v17/auth/users/{user_id}/role")
@router.post("/api/v17/auth/users/{user_id}/role")
async def update_auth_user_role(
    user_id: int,
    request: Request,
    payload: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    actor = require_manager_request(request)
    role = str(payload.get("role") or "").strip().lower()
    try:
        updated = auth_storage.update_user_role(user_id, role, actor_role=str(actor.get("role") or "manager"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "updated_user": build_user_payload(updated),
        "operator": {
            "id": actor["id"],
            "username": actor["username"],
        },
    }
