from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from experience.product_projection import NarrationManifestResponse, SpeechAssetResponse
from product.agent_case_store import AgentCaseStore
from product.canonical_scene import CanonicalSceneOwner, CanonicalSceneUnavailable
from product.abu_narration import AbuNarrationError, AbuNarrationService
from product.product_store import ProductStore
from product.theater_performance import TheaterPerformanceError


NARRATION_API_PREFIX = "/api/v50/narration"


def create_narration_router(
    *,
    product_store: ProductStore,
    session_cookie: str,
    case_store: AgentCaseStore,
    service: AbuNarrationService | None = None,
) -> APIRouter:
    router = APIRouter(prefix=NARRATION_API_PREFIX, tags=["abu-narrated-workspace"])
    service = service or AbuNarrationService.from_environment()
    scene_owner = CanonicalSceneOwner(case_store=case_store)

    def authenticated_account(request: Request) -> dict[str, object]:
        token = request.cookies.get(session_cookie, "")
        account = product_store.account_for_token(token) if token else None
        if not account:
            raise HTTPException(status_code=404, detail="mingli_case_not_found")
        return account

    def authorize_case(case_id: str, request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        account_id = str(account["user_id"])
        row = case_store.get(case_id=case_id, user_id=account_id)
        if row is None:
            raise HTTPException(status_code=404, detail="mingli_case_not_found")
        owner_id = str(row.get("user_id") or "")
        if owner_id and owner_id != account_id:
            raise HTTPException(status_code=404, detail="mingli_case_not_found")
        return account

    def manifest_for(case_id: str, request: Request):
        account = authenticated_account(request)
        try:
            projection = scene_owner.issue_projection(
                case_id=case_id,
                participant_id=str(account["user_id"]),
                account_role=str(account.get("account_role") or "member"),
                projection_kind="abu",
            )
            return service.compile_manifest(projection)
        except (CanonicalSceneUnavailable, AbuNarrationError) as exc:
            detail = str(exc)
            status = 404 if detail == "canonical_scene_case_not_found" else 409
            raise HTTPException(status_code=status, detail=detail) from exc

    @router.get("/cases/{case_id}/baseline", response_model=NarrationManifestResponse)
    def baseline_manifest(case_id: str, request: Request) -> dict[str, object]:
        manifest = manifest_for(case_id, request)
        return {
            "status": "narration_manifest_ready",
            "manifest": manifest.model_dump(mode="json"),
            "speech_assets": service.asset_statuses(manifest),
            "tts_called": False,
            "llm_used": False,
            "reasoner_used": False,
        }

    @router.post(
        "/cases/{case_id}/baseline/segments/{segment_id}",
        response_model=SpeechAssetResponse,
    )
    def prepare_segment(case_id: str, segment_id: str, request: Request) -> dict[str, object]:
        manifest = manifest_for(case_id, request)
        try:
            asset, cache_hit = service.prepare_segment(
                manifest=manifest,
                segment_id=segment_id,
            )
        except AbuNarrationError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except TheaterPerformanceError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {
            "status": "speech_asset_ready",
            "speech_asset": asset.model_dump(mode="json"),
            "cache_hit": cache_hit,
            "tts_called": not cache_hit,
            "llm_used": False,
            "reasoner_used": False,
        }

    @router.get("/cases/{case_id}/audio/{speech_asset_id}")
    def narration_audio(
        case_id: str,
        speech_asset_id: str,
        request: Request,
    ) -> FileResponse:
        authorize_case(case_id, request)
        try:
            asset = service.repository.get(speech_asset_id)
        except AbuNarrationError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if asset is None or asset.source.case_id != case_id:
            raise HTTPException(status_code=404, detail="speech_asset_not_found")
        path = service.repository.audio_path(speech_asset_id)
        return FileResponse(
            path,
            media_type="audio/wav",
            filename=f"{speech_asset_id}.wav",
            content_disposition_type="inline",
        )

    @router.get("/cases/{case_id}/audio/{speech_asset_id}/opus")
    def narration_audio_opus(
        case_id: str,
        speech_asset_id: str,
        request: Request,
    ) -> FileResponse:
        authorize_case(case_id, request)
        try:
            asset = service.repository.get(speech_asset_id)
        except AbuNarrationError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        variant = next(
            (item for item in (asset.media.playback_variants if asset else []) if item.format == "opus"),
            None,
        )
        if asset is None or asset.source.case_id != case_id or variant is None:
            raise HTTPException(status_code=404, detail="speech_asset_opus_not_found")
        return FileResponse(
            service.repository.variant_path(speech_asset_id, "opus"),
            media_type="audio/ogg; codecs=opus",
            filename=f"{speech_asset_id}.opus",
            content_disposition_type="inline",
        )

    return router
