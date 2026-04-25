from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, HTTPException, Request

from v17_rebirth.backend.infrastructure.auth_db import auth_storage
from v17_rebirth.backend.services.learning_experiment_queue import build_practitioner_experiment_queue
from v17_rebirth.backend.services.llm_collaboration import (
    build_evidence_review_contract,
    build_evidence_review_draft,
    build_evidence_review_prompt_text,
)
from v17_rebirth.backend.services.practitioner_learning import build_practitioner_learning_candidates
from v17_rebirth.backend.services.auth_service import (
    build_user_payload,
    get_request_user,
    require_admin_request,
    require_authenticated_request,
    require_manager_request,
)

router = APIRouter(tags=["v17-auth"])


def _is_practitioner_trust_role(role: Any) -> bool:
    return str(role or "").strip().lower() in {"practitioner", "manager", "admin"}


def _require_practitioner_trust(user: Dict[str, Any]) -> None:
    if not _is_practitioner_trust_role(user.get("role")):
        raise HTTPException(status_code=403, detail="当前账号不是命理师账号，无法提交专业反馈或案例。")


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


def _role_request_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": int(row.get("id") or 0),
        "user_id": int(row.get("user_id") or 0),
        "username": str(row.get("username") or "").strip(),
        "display_name": str(row.get("display_name") or "").strip(),
        "email": str(row.get("email") or "").strip(),
        "current_role": str(row.get("current_role") or "").strip(),
        "requested_role": str(row.get("requested_role") or "").strip(),
        "status": str(row.get("status") or "").strip(),
        "reason": str(row.get("reason") or "").strip(),
        "reviewer_user_id": int(row.get("reviewer_user_id") or 0),
        "reviewer_role": str(row.get("reviewer_role") or "").strip(),
        "reviewer_username": str(row.get("reviewer_username") or "").strip(),
        "reviewer_display_name": str(row.get("reviewer_display_name") or "").strip(),
        "reviewer_note": str(row.get("reviewer_note") or "").strip(),
        "created_at": str(row.get("created_at") or "").strip(),
        "updated_at": str(row.get("updated_at") or "").strip(),
        "decided_at": str(row.get("decided_at") or "").strip(),
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


def _case_benchmark_seed(row: Dict[str, Any]) -> Dict[str, Any]:
    audit_focus = []
    for key in ("tags", "boundary_flags", "failure_modes"):
        for item in row.get(key) or []:
            text = str(item or "").strip()
            if text and text not in audit_focus:
                audit_focus.append(text)
    return {
        "case_id": str(row.get("case_key") or "").strip(),
        "description": str(row.get("description") or row.get("case_title") or "").strip(),
        "four_pillars": row.get("four_pillars") if isinstance(row.get("four_pillars"), dict) else {},
        "luck_pillar": str(row.get("luck_pillar") or "").strip() or "—",
        "flow_pillar": str(row.get("flow_pillar") or "").strip() or "—",
        "gender": str(row.get("gender") or "male").strip() or "male",
        "audit_focus": audit_focus,
        "expected_top_contains": [str(item) for item in (row.get("expected_use_gods") or [])],
        "reviewer_note": str(row.get("expected_notes") or "").strip(),
        "source": "practitioner_case_library",
    }


def _case_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "id": int(row.get("id") or 0),
        "user_id": int(row.get("user_id") or 0),
        "owner_role": str(row.get("owner_role") or "user").strip(),
        "owner_weight": float(row.get("owner_weight") or 1.0),
        "owner_username": str(row.get("owner_username") or "").strip(),
        "owner_display_name": str(row.get("owner_display_name") or "").strip(),
        "case_key": str(row.get("case_key") or "").strip(),
        "case_title": str(row.get("case_title") or "").strip(),
        "description": str(row.get("description") or "").strip(),
        "birth_time_iso": str(row.get("birth_time_iso") or "").strip(),
        "gender": str(row.get("gender") or "").strip(),
        "calendar_type": str(row.get("calendar_type") or "").strip(),
        "lunar_is_leap_month": bool(row.get("lunar_is_leap_month")),
        "city_name": str(row.get("city_name") or "").strip(),
        "city_code": str(row.get("city_code") or "").strip(),
        "city_group": str(row.get("city_group") or "").strip(),
        "city_longitude": row.get("city_longitude"),
        "four_pillars": row.get("four_pillars") if isinstance(row.get("four_pillars"), dict) else {},
        "luck_pillar": str(row.get("luck_pillar") or "").strip(),
        "flow_pillar": str(row.get("flow_pillar") or "").strip(),
        "flow_year": row.get("flow_year"),
        "tags": row.get("tags") if isinstance(row.get("tags"), list) else [],
        "expected_patterns": row.get("expected_patterns") if isinstance(row.get("expected_patterns"), list) else [],
        "expected_use_gods": row.get("expected_use_gods") if isinstance(row.get("expected_use_gods"), list) else [],
        "expected_risks": row.get("expected_risks") if isinstance(row.get("expected_risks"), list) else [],
        "boundary_flags": row.get("boundary_flags") if isinstance(row.get("boundary_flags"), list) else [],
        "failure_modes": row.get("failure_modes") if isinstance(row.get("failure_modes"), list) else [],
        "expected_notes": str(row.get("expected_notes") or "").strip(),
        "source_feedback_ids": row.get("source_feedback_ids") if isinstance(row.get("source_feedback_ids"), list) else [],
        "chart_fingerprint": str(row.get("chart_fingerprint") or "").strip(),
        "status": str(row.get("status") or "").strip(),
        "payload": row.get("payload") if isinstance(row.get("payload"), dict) else {},
        "created_at": str(row.get("created_at") or "").strip(),
        "updated_at": str(row.get("updated_at") or "").strip(),
    }
    payload["benchmark_seed"] = _case_benchmark_seed(payload)
    return payload


def _contribution_map_from_users() -> Dict[int, Dict[str, Any]]:
    out: Dict[int, Dict[str, Any]] = {}
    for row in auth_storage.list_users():
        user = build_user_payload(row)
        user_id = int(user.get("id") or 0)
        contribution = user.get("practitioner_contribution")
        if user_id and isinstance(contribution, dict):
            out[user_id] = contribution
    return out


def _learning_review_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": int(row.get("id") or 0),
        "candidate_id": str(row.get("candidate_id") or "").strip(),
        "parameter_family": str(row.get("parameter_family") or "").strip(),
        "reviewer_user_id": int(row.get("reviewer_user_id") or 0),
        "reviewer_role": str(row.get("reviewer_role") or "").strip(),
        "reviewer_username": str(row.get("reviewer_username") or "").strip(),
        "reviewer_display_name": str(row.get("reviewer_display_name") or "").strip(),
        "status": str(row.get("status") or "").strip(),
        "reviewer_note": str(row.get("reviewer_note") or "").strip(),
        "safety_gate": str(row.get("safety_gate") or "").strip(),
        "candidate_snapshot": row.get("candidate_snapshot") if isinstance(row.get("candidate_snapshot"), dict) else {},
        "created_at": str(row.get("created_at") or "").strip(),
        "updated_at": str(row.get("updated_at") or "").strip(),
    }


def _learning_release_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": int(row.get("id") or 0),
        "experiment_id": str(row.get("experiment_id") or "").strip(),
        "candidate_id": str(row.get("candidate_id") or "").strip(),
        "parameter_family": str(row.get("parameter_family") or "").strip(),
        "reviewer_user_id": int(row.get("reviewer_user_id") or 0),
        "reviewer_role": str(row.get("reviewer_role") or "").strip(),
        "reviewer_username": str(row.get("reviewer_username") or "").strip(),
        "reviewer_display_name": str(row.get("reviewer_display_name") or "").strip(),
        "status": str(row.get("status") or "").strip(),
        "release_summary": str(row.get("release_summary") or "").strip(),
        "test_report": str(row.get("test_report") or "").strip(),
        "rollback_plan": str(row.get("rollback_plan") or "").strip(),
        "experiment_snapshot": row.get("experiment_snapshot") if isinstance(row.get("experiment_snapshot"), dict) else {},
        "applied": bool(row.get("applied")),
        "created_at": str(row.get("created_at") or "").strip(),
        "updated_at": str(row.get("updated_at") or "").strip(),
    }


def _learning_scorecard_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": int(row.get("id") or 0),
        "experiment_id": str(row.get("experiment_id") or "").strip(),
        "candidate_id": str(row.get("candidate_id") or "").strip(),
        "parameter_family": str(row.get("parameter_family") or "").strip(),
        "reviewer_user_id": int(row.get("reviewer_user_id") or 0),
        "reviewer_role": str(row.get("reviewer_role") or "").strip(),
        "reviewer_username": str(row.get("reviewer_username") or "").strip(),
        "reviewer_display_name": str(row.get("reviewer_display_name") or "").strip(),
        "synthetic_passed": bool(row.get("synthetic_passed")),
        "practitioner_passed": bool(row.get("practitioner_passed")),
        "improvement_count": int(row.get("improvement_count") or 0),
        "regression_count": int(row.get("regression_count") or 0),
        "verdict": str(row.get("verdict") or "").strip(),
        "summary": str(row.get("summary") or "").strip(),
        "payload": row.get("payload") if isinstance(row.get("payload"), dict) else {},
        "created_at": str(row.get("created_at") or "").strip(),
        "updated_at": str(row.get("updated_at") or "").strip(),
    }


def _attach_latest_learning_reviews(report: Dict[str, Any]) -> Dict[str, Any]:
    reviews = auth_storage.list_practitioner_learning_reviews(limit=240)
    latest_by_candidate: Dict[str, Dict[str, Any]] = {}
    counts_by_candidate: Dict[str, int] = {}
    for row in reviews:
        candidate_id = str(row.get("candidate_id") or "").strip()
        if not candidate_id:
            continue
        counts_by_candidate[candidate_id] = counts_by_candidate.get(candidate_id, 0) + 1
        latest_by_candidate.setdefault(candidate_id, _learning_review_payload(row))
    candidates = report.get("candidates")
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            candidate_id = str(candidate.get("candidate_id") or "").strip()
            latest = latest_by_candidate.get(candidate_id)
            candidate["review_count"] = counts_by_candidate.get(candidate_id, 0)
            candidate["latest_review"] = latest
            candidate["review_status"] = str((latest or {}).get("status") or "unreviewed")
    return report


def _build_learning_governance_export() -> Dict[str, Any]:
    feedback_rows = auth_storage.list_practitioner_feedback(
        user_id=0,
        reviewer_role="admin",
        scope="all",
        limit=180,
    )
    case_rows = auth_storage.list_practitioner_cases(
        user_id=0,
        owner_role="admin",
        scope="all",
        limit=180,
    )
    candidate_report = build_practitioner_learning_candidates(
        feedback_rows=feedback_rows,
        case_rows=case_rows,
        contribution_by_user_id=_contribution_map_from_users(),
        scope="all",
    )
    candidate_report = _attach_latest_learning_reviews(candidate_report)
    reviews = auth_storage.list_practitioner_learning_reviews(limit=240)
    experiment_report = build_practitioner_experiment_queue(
        auth_storage.list_practitioner_learning_reviews(status="approved_for_experiment", limit=120)
    )
    scorecards = auth_storage.list_practitioner_learning_scorecards(limit=240)
    releases = auth_storage.list_practitioner_learning_releases(limit=240)
    return {
        "ok": True,
        "protocol": "v17.practitioner.learning_governance_export.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "candidate_count": int((candidate_report.get("summary") or {}).get("candidate_count") or 0),
            "review_count": len(reviews),
            "experiment_count": int(experiment_report.get("experiment_count") or 0),
            "scorecard_count": len(scorecards),
            "release_count": len(releases),
        },
        "candidate_report": candidate_report,
        "reviews": [_learning_review_payload(row) for row in reviews],
        "experiment_report": experiment_report,
        "scorecards": [_learning_scorecard_payload(row) for row in scorecards],
        "releases": [_learning_release_payload(row) for row in releases],
        "guardrails": [
            "export is audit-only",
            "release records do not apply runtime parameter changes",
            "approved releases require promote scorecard and rollback plan",
        ],
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
            role="practitioner",
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
        "role_request": None,
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


@router.post("/v17/auth/role-requests")
@router.post("/api/v17/auth/role-requests")
async def create_auth_role_request(request: Request, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    user = require_authenticated_request(request)
    requested_role = str(payload.get("requested_role") or "practitioner").strip().lower()
    reason = str(payload.get("reason") or payload.get("practitioner_request_note") or "").strip()
    try:
        row = auth_storage.create_role_request(
            user_id=int(user.get("id") or 0),
            requested_role=requested_role,
            reason=reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "role_request": _role_request_payload(row)}


@router.get("/v17/auth/role-requests")
@router.get("/api/v17/auth/role-requests")
async def list_auth_role_requests(request: Request) -> Dict[str, Any]:
    require_manager_request(request)
    query = request.query_params
    try:
        limit = int(query.get("limit") or 80)
    except Exception:
        limit = 80
    try:
        rows = auth_storage.list_role_requests(
            status=str(query.get("status") or "pending").strip(),
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "role_requests": [_role_request_payload(row) for row in rows]}


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
    _require_practitioner_trust(user)
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
        "trust_tier": "practitioner" if _is_practitioner_trust_role(user.get("role")) else "user",
    }


@router.post("/v17/auth/practitioner-evidence-review")
@router.post("/api/v17/auth/practitioner-evidence-review")
async def create_practitioner_evidence_review(request: Request, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    user = require_authenticated_request(request)
    _require_practitioner_trust(user)
    raw_items = payload.get("items")
    items = raw_items if isinstance(raw_items, list) else []
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    contract = build_evidence_review_contract(
        items=[item for item in items if isinstance(item, dict)],
        summary=summary,
        session_id=str(payload.get("session_id") or "").strip(),
        chart_fingerprint=str(payload.get("chart_fingerprint") or "").strip(),
        verdict_text=str(payload.get("verdict_text") or "").strip(),
        reviewer_role=str(user.get("role") or "user"),
        output_language=str(payload.get("ui_lang") or payload.get("language") or "zh").strip(),
    )
    return {
        "ok": True,
        "mode": "draft",
        "review": build_evidence_review_draft(contract),
        "prompt_contract": contract,
        "prompt_text": build_evidence_review_prompt_text(contract),
        "viewer_role": str(user.get("role") or "user"),
        "safety_gate": "review_only",
    }


@router.get("/v17/auth/practitioner-cases")
@router.get("/api/v17/auth/practitioner-cases")
async def list_practitioner_cases(request: Request) -> Dict[str, Any]:
    user = require_authenticated_request(request)
    query = request.query_params
    try:
        limit = int(query.get("limit") or 80)
    except Exception:
        limit = 80
    rows = auth_storage.list_practitioner_cases(
        user_id=int(user["id"]),
        owner_role=str(user.get("role") or "user"),
        scope=str(query.get("scope") or "own").strip(),
        case_key=str(query.get("case_key") or "").strip(),
        status=str(query.get("status") or "").strip(),
        chart_fingerprint=str(query.get("chart_fingerprint") or "").strip(),
        limit=limit,
    )
    return {
        "ok": True,
        "cases": [_case_payload(row) for row in rows],
        "viewer_role": str(user.get("role") or "user"),
    }


@router.post("/v17/auth/practitioner-cases/{case_id}/status")
@router.post("/api/v17/auth/practitioner-cases/{case_id}/status")
async def update_practitioner_case_status(case_id: int, request: Request, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    user = require_manager_request(request)
    try:
        row = auth_storage.update_practitioner_case_status(
            case_id=case_id,
            status=str(payload.get("status") or "").strip(),
            reviewer_note=str(payload.get("reviewer_note") or "").strip(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "case": _case_payload(row),
        "viewer_role": str(user.get("role") or "user"),
        "applied_to_static_benchmark": False,
        "guardrail": "case_status_only_no_test_file_change",
    }


@router.get("/v17/auth/practitioner-learning-candidates")
@router.get("/api/v17/auth/practitioner-learning-candidates")
async def list_practitioner_learning_candidates(request: Request) -> Dict[str, Any]:
    user = require_authenticated_request(request)
    _require_practitioner_trust(user)
    query = request.query_params
    try:
        limit = max(20, min(180, int(query.get("limit") or 120)))
    except Exception:
        limit = 120
    requested_scope = str(query.get("scope") or "own").strip().lower()
    viewer_role = str(user.get("role") or "user").strip().lower()
    effective_scope = "all" if requested_scope == "all" and viewer_role in {"manager", "admin"} else "own"
    feedback_rows = auth_storage.list_practitioner_feedback(
        user_id=int(user["id"]),
        reviewer_role=viewer_role,
        scope=effective_scope,
        limit=limit,
    )
    case_rows = auth_storage.list_practitioner_cases(
        user_id=int(user["id"]),
        owner_role=viewer_role,
        scope=effective_scope,
        limit=limit,
    )
    report = build_practitioner_learning_candidates(
        feedback_rows=feedback_rows,
        case_rows=case_rows,
        contribution_by_user_id=_contribution_map_from_users(),
        scope=effective_scope,
    )
    report = _attach_latest_learning_reviews(report)
    report["viewer_role"] = viewer_role
    return report


@router.get("/v17/auth/practitioner-learning-reviews")
@router.get("/api/v17/auth/practitioner-learning-reviews")
async def list_practitioner_learning_reviews(request: Request) -> Dict[str, Any]:
    user = require_manager_request(request)
    query = request.query_params
    try:
        limit = int(query.get("limit") or 80)
    except Exception:
        limit = 80
    rows = auth_storage.list_practitioner_learning_reviews(
        candidate_id=str(query.get("candidate_id") or "").strip(),
        status=str(query.get("status") or "").strip(),
        limit=limit,
    )
    return {
        "ok": True,
        "reviews": [_learning_review_payload(row) for row in rows],
        "viewer_role": str(user.get("role") or "user"),
    }


@router.post("/v17/auth/practitioner-learning-reviews")
@router.post("/api/v17/auth/practitioner-learning-reviews")
async def create_practitioner_learning_review(request: Request, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    user = require_manager_request(request)
    snapshot = payload.get("candidate_snapshot") if isinstance(payload.get("candidate_snapshot"), dict) else {}
    try:
        row = auth_storage.create_practitioner_learning_review(
            reviewer_user_id=int(user.get("id") or 0),
            reviewer_role=str(user.get("role") or "user"),
            candidate_id=str(payload.get("candidate_id") or snapshot.get("candidate_id") or "").strip(),
            parameter_family=str(payload.get("parameter_family") or snapshot.get("parameter_family") or "").strip(),
            status=str(payload.get("status") or "").strip(),
            reviewer_note=str(payload.get("reviewer_note") or "").strip(),
            safety_gate=str(payload.get("safety_gate") or snapshot.get("safety_gate") or "manual_review_required").strip(),
            candidate_snapshot=snapshot,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "review": _learning_review_payload(row),
        "applied": False,
        "guardrail": "review_only_no_runtime_parameter_change",
    }


@router.get("/v17/auth/practitioner-learning-experiments")
@router.get("/api/v17/auth/practitioner-learning-experiments")
async def list_practitioner_learning_experiments(request: Request) -> Dict[str, Any]:
    user = require_manager_request(request)
    rows = auth_storage.list_practitioner_learning_reviews(
        status="approved_for_experiment",
        limit=120,
    )
    report = build_practitioner_experiment_queue(rows)
    report["viewer_role"] = str(user.get("role") or "user")
    return report


@router.get("/v17/auth/practitioner-learning-governance-export")
@router.get("/api/v17/auth/practitioner-learning-governance-export")
async def export_practitioner_learning_governance(request: Request) -> Dict[str, Any]:
    user = require_manager_request(request)
    payload = _build_learning_governance_export()
    payload["viewer_role"] = str(user.get("role") or "user")
    return payload


@router.get("/v17/auth/practitioner-learning-releases")
@router.get("/api/v17/auth/practitioner-learning-releases")
async def list_practitioner_learning_releases(request: Request) -> Dict[str, Any]:
    user = require_manager_request(request)
    query = request.query_params
    try:
        limit = int(query.get("limit") or 80)
    except Exception:
        limit = 80
    rows = auth_storage.list_practitioner_learning_releases(
        experiment_id=str(query.get("experiment_id") or "").strip(),
        status=str(query.get("status") or "").strip(),
        limit=limit,
    )
    return {
        "ok": True,
        "releases": [_learning_release_payload(row) for row in rows],
        "viewer_role": str(user.get("role") or "user"),
    }


@router.post("/v17/auth/practitioner-learning-releases")
@router.post("/api/v17/auth/practitioner-learning-releases")
async def create_practitioner_learning_release(request: Request, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    user = require_admin_request(request)
    snapshot = payload.get("experiment_snapshot") if isinstance(payload.get("experiment_snapshot"), dict) else {}
    experiment_id = str(payload.get("experiment_id") or snapshot.get("experiment_id") or "").strip()
    status = str(payload.get("status") or "").strip()
    if status == "approved" and not auth_storage.has_promote_learning_scorecard(experiment_id=experiment_id):
        raise HTTPException(status_code=400, detail="批准发布前必须存在通过 synthetic 与 practitioner benchmark 的 promote scorecard。")
    try:
        row = auth_storage.create_practitioner_learning_release(
            reviewer_user_id=int(user.get("id") or 0),
            reviewer_role=str(user.get("role") or "user"),
            experiment_id=experiment_id,
            candidate_id=str(payload.get("candidate_id") or snapshot.get("candidate_id") or "").strip(),
            parameter_family=str(payload.get("parameter_family") or snapshot.get("parameter_family") or "").strip(),
            status=status,
            release_summary=str(payload.get("release_summary") or "").strip(),
            test_report=str(payload.get("test_report") or "").strip(),
            rollback_plan=str(payload.get("rollback_plan") or "").strip(),
            experiment_snapshot=snapshot,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "release": _learning_release_payload(row),
        "applied": False,
        "guardrail": "release_record_only_no_config_change",
    }


@router.get("/v17/auth/practitioner-learning-scorecards")
@router.get("/api/v17/auth/practitioner-learning-scorecards")
async def list_practitioner_learning_scorecards(request: Request) -> Dict[str, Any]:
    user = require_manager_request(request)
    query = request.query_params
    try:
        limit = int(query.get("limit") or 80)
    except Exception:
        limit = 80
    rows = auth_storage.list_practitioner_learning_scorecards(
        experiment_id=str(query.get("experiment_id") or "").strip(),
        verdict=str(query.get("verdict") or "").strip(),
        limit=limit,
    )
    return {
        "ok": True,
        "scorecards": [_learning_scorecard_payload(row) for row in rows],
        "viewer_role": str(user.get("role") or "user"),
    }


@router.post("/v17/auth/practitioner-learning-scorecards")
@router.post("/api/v17/auth/practitioner-learning-scorecards")
async def create_practitioner_learning_scorecard(request: Request, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    user = require_manager_request(request)
    experiment = payload.get("experiment_snapshot") if isinstance(payload.get("experiment_snapshot"), dict) else {}
    try:
        row = auth_storage.create_practitioner_learning_scorecard(
            reviewer_user_id=int(user.get("id") or 0),
            reviewer_role=str(user.get("role") or "user"),
            experiment_id=str(payload.get("experiment_id") or experiment.get("experiment_id") or "").strip(),
            candidate_id=str(payload.get("candidate_id") or experiment.get("candidate_id") or "").strip(),
            parameter_family=str(payload.get("parameter_family") or experiment.get("parameter_family") or "").strip(),
            synthetic_passed=bool(payload.get("synthetic_passed")),
            practitioner_passed=bool(payload.get("practitioner_passed")),
            improvement_count=int(payload.get("improvement_count") or 0),
            regression_count=int(payload.get("regression_count") or 0),
            verdict=str(payload.get("verdict") or "").strip(),
            summary=str(payload.get("summary") or "").strip(),
            payload=payload.get("payload") if isinstance(payload.get("payload"), dict) else {},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "scorecard": _learning_scorecard_payload(row),
        "applied": False,
        "guardrail": "scorecard_record_only_no_config_change",
    }


@router.post("/v17/auth/practitioner-cases")
@router.post("/api/v17/auth/practitioner-cases")
async def create_practitioner_case(request: Request, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    user = require_authenticated_request(request)
    _require_practitioner_trust(user)
    try:
        row = auth_storage.create_practitioner_case(
            user_id=int(user["id"]),
            owner_role=str(user.get("role") or "user"),
            case_key=str(payload.get("case_key") or "").strip(),
            case_title=str(payload.get("case_title") or payload.get("title") or "").strip(),
            description=str(payload.get("description") or "").strip(),
            birth_time_iso=str(payload.get("birth_time_iso") or "").strip(),
            gender=str(payload.get("gender") or "").strip(),
            calendar_type=str(payload.get("calendar_type") or "solar").strip(),
            lunar_is_leap_month=bool(payload.get("lunar_is_leap_month")),
            city_name=str(payload.get("city_name") or "").strip(),
            city_code=str(payload.get("city_code") or "").strip(),
            city_group=str(payload.get("city_group") or "").strip(),
            city_longitude=payload.get("city_longitude"),
            four_pillars=payload.get("four_pillars") if isinstance(payload.get("four_pillars"), dict) else {},
            luck_pillar=str(payload.get("luck_pillar") or "").strip(),
            flow_pillar=str(payload.get("flow_pillar") or "").strip(),
            flow_year=payload.get("flow_year"),
            tags=payload.get("tags"),
            expected_patterns=payload.get("expected_patterns"),
            expected_use_gods=payload.get("expected_use_gods"),
            expected_risks=payload.get("expected_risks"),
            boundary_flags=payload.get("boundary_flags"),
            failure_modes=payload.get("failure_modes"),
            expected_notes=str(payload.get("expected_notes") or "").strip(),
            source_feedback_ids=payload.get("source_feedback_ids"),
            chart_fingerprint=str(payload.get("chart_fingerprint") or "").strip(),
            status=str(payload.get("status") or "submitted").strip(),
            payload=payload.get("payload") if isinstance(payload.get("payload"), dict) else {},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    case = _case_payload(row)
    return {
        "ok": True,
        "case": case,
        "trust_tier": "practitioner" if _is_practitioner_trust_role(user.get("role")) else "user",
        "benchmark_seed": case["benchmark_seed"],
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


@router.post("/v17/auth/role-requests/{request_id}/decision")
@router.post("/api/v17/auth/role-requests/{request_id}/decision")
async def decide_auth_role_request(
    request_id: int,
    request: Request,
    payload: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    actor = require_manager_request(request)
    decision = str(payload.get("status") or payload.get("decision") or "").strip().lower()
    reviewer_note = str(payload.get("reviewer_note") or payload.get("note") or "").strip()
    try:
        result = auth_storage.decide_role_request(
            request_id,
            status=decision,
            reviewer_user_id=int(actor.get("id") or 0),
            reviewer_role=str(actor.get("role") or "manager"),
            reviewer_note=reviewer_note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    updated_user = result.get("updated_user") if isinstance(result.get("updated_user"), dict) else {}
    return {
        "ok": True,
        "role_request": _role_request_payload(result["request"]),
        "updated_user": build_user_payload(updated_user) if updated_user else None,
        "operator": {
            "id": actor["id"],
            "username": actor["username"],
        },
    }
