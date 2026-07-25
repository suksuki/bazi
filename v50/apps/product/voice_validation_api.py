from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from experience.voice_validation import (
    VoiceComprehensionAnalystReview,
    VoiceComprehensionSubmission,
    VoiceValidationInteractionEvent,
    VoiceValidationSession,
)
from product.agent_case_store import AgentCaseStore
from product.canonical_scene import CanonicalSceneOwner, CanonicalSceneUnavailable
from product.abu_narration import AbuNarrationError, AbuNarrationService
from product.product_store import ProductStore
from product.voice_validation_store import VoiceValidationStore


VOICE_VALIDATION_PREFIX = "/api/v50/narration/validation"


class StartVoiceValidationRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=180)
    requested_arm: str = Field(default="", max_length=40)


class VoiceValidationEventRequest(BaseModel):
    event: VoiceValidationInteractionEvent


class VoiceComprehensionRequest(BaseModel):
    submission: VoiceComprehensionSubmission


class VoiceAnalystReviewRequest(BaseModel):
    review: VoiceComprehensionAnalystReview


def create_voice_validation_router(
    *,
    product_store: ProductStore,
    session_cookie: str,
    case_store: AgentCaseStore,
    narration_service: AbuNarrationService,
    validation_store: VoiceValidationStore,
) -> APIRouter:
    router = APIRouter(prefix=VOICE_VALIDATION_PREFIX, tags=["abu-voice-validation"])
    scene_owner = CanonicalSceneOwner(case_store=case_store)

    def narration_manifest(case_id: str, participant_ref: str):
        projection = scene_owner.issue_projection(
            case_id=case_id,
            participant_id=participant_ref,
            account_role="member",
            projection_kind="abu",
        )
        return narration_service.compile_manifest(projection)

    def account_for(request: Request) -> dict[str, object]:
        token = request.cookies.get(session_cookie, "")
        account = product_store.account_for_token(token) if token else None
        if not account:
            raise HTTPException(status_code=401, detail="authentication_required")
        return account

    def authorized_session(session_id: str, request: Request) -> VoiceValidationSession:
        account = account_for(request)
        session = validation_store.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="voice_validation_session_not_found")
        if session.participant_ref != str(account["user_id"]) and account.get("account_role") != "admin":
            raise HTTPException(status_code=404, detail="voice_validation_session_not_found")
        return session

    @router.post("/sessions")
    def start_session(payload: StartVoiceValidationRequest, request: Request) -> dict[str, object]:
        account = account_for(request)
        participant_ref = str(account["user_id"])
        try:
            manifest = narration_manifest(payload.case_id, participant_ref)
        except (CanonicalSceneUnavailable, AbuNarrationError) as exc:
            detail = str(exc)
            status = 404 if detail == "canonical_scene_case_not_found" else 409
            raise HTTPException(status_code=status, detail=detail) from exc
        assignment_hash = hashlib.sha256(
            f"abu-voice-comprehension.v1:{participant_ref}:{payload.case_id}".encode("utf-8")
        ).hexdigest()
        assigned_arm = (
            "text_and_abu_voice" if int(assignment_hash[:8], 16) % 2 else "text_only"
        )
        if payload.requested_arm:
            if account.get("account_role") != "admin":
                raise HTTPException(status_code=403, detail="admin_arm_override_required")
            if payload.requested_arm not in {"text_only", "text_and_abu_voice"}:
                raise HTTPException(status_code=422, detail="unsupported_voice_validation_arm")
            assigned_arm = payload.requested_arm
        session = VoiceValidationSession(
            session_id=f"voice-study-{uuid4().hex}",
            participant_ref=participant_ref,
            case_id=payload.case_id,
            manifest_id=manifest.manifest_id,
            manifest_hash=manifest.manifest_hash,
            arm=assigned_arm,
            assignment_hash=assignment_hash,
            started_at=datetime.now(timezone.utc),
        )
        validation_store.create(session)
        return {
            "status": "voice_validation_started",
            "session": session.model_dump(mode="json"),
            "storage": validation_store.storage_name,
        }

    @router.post("/sessions/{session_id}/events")
    def append_event(
        session_id: str,
        payload: VoiceValidationEventRequest,
        request: Request,
    ) -> dict[str, object]:
        authorized_session(session_id, request)
        try:
            session = validation_store.append_event(session_id, payload.event)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="voice_validation_session_not_found") from exc
        return {"status": "voice_validation_event_recorded", "event_count": len(session.interactions)}

    @router.post("/sessions/{session_id}/comprehension")
    def submit_comprehension(
        session_id: str,
        payload: VoiceComprehensionRequest,
        request: Request,
    ) -> dict[str, object]:
        authorized_session(session_id, request)
        try:
            session = validation_store.submit(session_id, payload.submission)
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {
            "status": "voice_comprehension_submitted",
            "session_id": session.session_id,
            "arm": session.arm,
        }

    @router.get("/sessions/{session_id}")
    def get_session(session_id: str, request: Request) -> dict[str, object]:
        session = authorized_session(session_id, request)
        return {"status": "voice_validation_session_ready", "session": session.model_dump(mode="json")}

    @router.post("/sessions/{session_id}/analyst-review")
    def save_analyst_review(
        session_id: str,
        payload: VoiceAnalystReviewRequest,
        request: Request,
    ) -> dict[str, object]:
        account = account_for(request)
        if account.get("account_role") != "admin":
            raise HTTPException(status_code=403, detail="admin_review_required")
        try:
            session = validation_store.save_review(session_id, payload.review)
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "voice_analyst_review_locked", "session": session.model_dump(mode="json")}

    @router.get("/summary")
    def validation_summary(request: Request) -> dict[str, object]:
        account = account_for(request)
        if account.get("account_role") != "admin":
            raise HTTPException(status_code=403, detail="admin_summary_required")
        sessions = validation_store.list_sessions()
        return {
            "status": "voice_validation_summary_ready",
            "summary": summarize_voice_validation(sessions),
        }

    @router.get("/review-packet")
    def blinded_review_packet(request: Request) -> dict[str, object]:
        account = account_for(request)
        if account.get("account_role") != "admin":
            raise HTTPException(status_code=403, detail="admin_review_required")
        cases: list[dict[str, object]] = []
        for session in validation_store.list_sessions():
            if not session.comprehension:
                continue
            try:
                manifest = narration_manifest(session.case_id, session.participant_ref)
            except (CanonicalSceneUnavailable, AbuNarrationError):
                continue
            cases.append(
                {
                    "blind_id": f"VC-{hashlib.sha256(session.session_id.encode('utf-8')).hexdigest()[:8].upper()}",
                    "review_target": session.session_id,
                    "source_segments": [
                        {
                            "kind": segment.kind,
                            "title": segment.title,
                            "text": segment.text,
                        }
                        for segment in manifest.segments
                    ],
                    "participant_response": session.comprehension.model_dump(mode="json"),
                    "analyst_review": (
                        session.analyst_review.model_dump(mode="json")
                        if session.analyst_review
                        else None
                    ),
                }
            )
        return {
            "status": "voice_validation_blinded_review_packet_ready",
            "machine_arm_hidden": True,
            "interaction_log_hidden": True,
            "raw_birth_data_included": False,
            "cases": cases,
        }

    return router


def summarize_voice_validation(sessions: list[VoiceValidationSession]) -> dict[str, object]:
    by_arm: dict[str, dict[str, object]] = {}
    for arm in ("text_only", "text_and_abu_voice"):
        rows = [item for item in sessions if item.arm == arm]
        submitted = [item for item in rows if item.comprehension]
        reviewed = [item for item in rows if item.analyst_review]
        accuracy = [
            sum(
                [
                    item.analyst_review.whole_chart_accuracy,
                    item.analyst_review.work_path_accuracy,
                    item.analyst_review.condition_accuracy,
                    item.analyst_review.uncertainty_accuracy,
                ]
            )
            / 8
            for item in reviewed
            if item.analyst_review
        ]
        by_arm[arm] = {
            "sessions": len(rows),
            "submitted": len(submitted),
            "analyst_reviewed": len(reviewed),
            "mean_comprehension_accuracy": (
                round(sum(accuracy) / len(accuracy), 4) if accuracy else None
            ),
            "mean_fatigue": _mean(
                [item.comprehension.fatigue_score for item in submitted if item.comprehension]
            ),
            "mean_trust_delta": _mean(
                [
                    item.comprehension.professional_trust_delta
                    for item in submitted
                    if item.comprehension
                ]
            ),
        }
    reviewed_count = sum(1 for item in sessions if item.analyst_review)
    minimum_per_arm_reached = all(
        int(by_arm[arm]["analyst_reviewed"]) >= 6
        for arm in ("text_only", "text_and_abu_voice")
    )
    return {
        "experiment_version": "abu-voice-comprehension.v1",
        "total_sessions": len(sessions),
        "submitted_sessions": sum(1 for item in sessions if item.comprehension),
        "analyst_reviewed_sessions": reviewed_count,
        "by_arm": by_arm,
        "ready_for_product_decision": reviewed_count >= 12 and minimum_per_arm_reached,
        "minimum_reviewed_per_arm": 6,
        "human_validation_performed": reviewed_count > 0,
    }


def _mean(values: list[int]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None
