from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from product.theater_api_context import TheaterRouteContext
from product.theater_api_contracts import PerformancePrepareRequest
from product.theater_performance import TheaterPerformanceError


def register_performance_routes(router: APIRouter, context: TheaterRouteContext) -> None:
    store = context.theater_store
    service = context.performance_service

    @router.post("/sessions/{session_id}/cues/{cue_instance_id}/performance")
    def prepare_performance(
        session_id: str,
        cue_instance_id: str,
        payload: PerformancePrepareRequest,
        request: Request,
    ) -> dict[str, object]:
        context.authorize_run(
            participant_run_id=payload.participant_run_id,
            access_token=payload.access_token,
            account=context.account_for_request(request),
        )
        run = store.get_participant(payload.participant_run_id)
        cue = store.get_cue(cue_instance_id)
        if not run or run.session_id != session_id:
            raise HTTPException(status_code=404, detail="participant_run_not_found")
        if not cue or cue.cue_instance_id not in {
            item.cue_instance_id for item in store.list_cues(session_id)
        }:
            raise HTTPException(status_code=404, detail="performance_cue_not_found")
        if cue.visibility == "participant_private" and cue.participant_run_id != run.participant_run_id:
            raise HTTPException(status_code=403, detail="private_performance_access_denied")
        envelope = store.get_envelope(cue.envelope_id) if cue.envelope_id else None
        try:
            package = service.prepare(cue=cue, envelope=envelope)
        except TheaterPerformanceError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {
            "status": "performance_ready",
            "package": package.model_dump(mode="json"),
            "tts_regenerated": False,
            "llm_used": False,
            "reasoner_used": False,
        }

    @router.get("/sessions/{session_id}/performance/{package_id}/audio")
    def performance_audio(
        session_id: str,
        package_id: str,
        request: Request,
        participant_run_id: str,
        access_token: str,
    ) -> FileResponse:
        context.authorize_run(
            participant_run_id=participant_run_id,
            access_token=access_token,
            account=context.account_for_request(request),
        )
        run = store.get_participant(participant_run_id)
        package = service.repository.get(package_id)
        if not run or run.session_id != session_id or not package:
            raise HTTPException(status_code=404, detail="performance_package_not_found")
        if package.visibility == "participant_private" and package.participant_run_id != participant_run_id:
            raise HTTPException(status_code=403, detail="private_performance_access_denied")
        audio_path = service.repository.audio_path(package_id)
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="frozen_performance_audio_missing")
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            filename=f"{package_id}.wav",
            content_disposition_type="inline",
        )
