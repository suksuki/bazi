from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.api.identity import SessionDependency
from abu_v60.db import engine
from abu_v60.media import TTSProviderError, TTSUnavailableError
from abu_v60.media.focused_speech import (
    FOCUSED_SPEECH_TIMELINE_HEADER,
    FocusedPassSpeechConflict,
    FocusedPassSpeechError,
    FocusedPassSpeechNotFound,
    FocusedPassSpeechService,
)
from abu_v60.media.mingli_narration import (
    MingliNarrationConflictError,
    MingliNarrationError,
    MingliNarrationService,
)
from abu_v60.mingli.narration_contracts import MingliNarrationPrepareRequest
from abu_v60.mingli.stage_contracts import MingliStageMode

router = APIRouter(prefix="/api/v60/mingli/narrations", tags=["mingli-narration"])
service = MingliNarrationService(engine)
focused_speech = FocusedPassSpeechService(engine)


class FocusedPassSpeechRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_version: Literal["v60.mingli-focused-speech-request.001"] = (
        "v60.mingli-focused-speech-request.001"
    )
    subject_id: str = Field(min_length=1, max_length=240)
    stage_mode: MingliStageMode = MingliStageMode.NATAL_4
    selected_year: int | None = Field(default=None, ge=1900, le=2200)
    expected_stage_projection_ref: str = Field(min_length=1)
    expected_stage_projection_hash: str = Field(min_length=64, max_length=64)
    record_ref: str = Field(min_length=1)
    expected_record_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def stage_coordinates_are_complete(self) -> FocusedPassSpeechRequest:
        if self.stage_mode == MingliStageMode.NATAL_DAYUN_YEAR_6:
            if self.selected_year is None:
                raise ValueError("mingli_focused_speech_six_year_required")
        elif self.selected_year is not None:
            raise ValueError("mingli_focused_speech_four_year_forbidden")
        return self


@router.post("/focused-pass")
def focused_pass_audio(
    payload: FocusedPassSpeechRequest,
    session: SessionDependency,
) -> Response:
    try:
        prepared = focused_speech.prepare(
            account_ref=session.account.account_ref,
            subject_id=payload.subject_id,
            stage_mode=payload.stage_mode,
            selected_year=payload.selected_year,
            expected_stage_projection_ref=payload.expected_stage_projection_ref,
            expected_stage_projection_hash=payload.expected_stage_projection_hash,
            record_ref=payload.record_ref,
            expected_record_hash=payload.expected_record_hash,
        )
    except FocusedPassSpeechNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FocusedPassSpeechConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except FocusedPassSpeechError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except TTSUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except TTSProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    return Response(
        content=prepared.audio.audio_bytes,
        media_type="audio/wav",
        headers={
            "Cache-Control": "private, no-store",
            "Content-Disposition": "inline",
            "Content-Length": str(len(prepared.audio.audio_bytes)),
            FOCUSED_SPEECH_TIMELINE_HEADER: prepared.timeline_header_value(),
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("")
def prepare_narration(
    payload: MingliNarrationPrepareRequest,
    response: Response,
    session: SessionDependency,
) -> dict[str, object]:
    try:
        stored = service.prepare(
            account_ref=session.account.account_ref,
            request=payload,
        )
    except MingliNarrationConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except MingliNarrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except TTSUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except TTSProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    response.headers["Cache-Control"] = "private, no-store"
    return {
        "asset": stored.asset.model_dump(mode="json"),
        "audio_url": f"/api/v60/mingli/narrations/{stored.asset.narration_ref}/audio",
    }


@router.api_route("/{narration_ref}/audio", methods=["GET", "HEAD"])
def narration_audio(
    narration_ref: str,
    request: Request,
    session: SessionDependency,
) -> Response:
    stored = service.owned_asset(
        account_ref=session.account.account_ref,
        narration_ref=narration_ref,
    )
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="mingli_narration_not_found",
        )
    audio_bytes = stored.audio_bytes
    total = len(audio_bytes)
    range_header = request.headers.get("range")
    start, end = 0, total - 1
    response_status = status.HTTP_200_OK
    if range_header is not None:
        try:
            start, end = _single_byte_range(range_header, total=total)
        except ValueError:
            return Response(
                status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                headers={
                    **_audio_headers(total=0),
                    "Content-Range": f"bytes */{total}",
                },
            )
        response_status = status.HTTP_206_PARTIAL_CONTENT
    payload = b"" if request.method == "HEAD" else audio_bytes[start : end + 1]
    headers = _audio_headers(total=end - start + 1)
    if response_status == status.HTTP_206_PARTIAL_CONTENT:
        headers["Content-Range"] = f"bytes {start}-{end}/{total}"
    return Response(
        content=payload,
        status_code=response_status,
        headers=headers,
        media_type="audio/wav",
    )


def _audio_headers(*, total: int) -> dict[str, str]:
    return {
        "Accept-Ranges": "bytes",
        "Cache-Control": "private, no-store",
        "Content-Disposition": "inline",
        "Content-Length": str(total),
        "X-Content-Type-Options": "nosniff",
    }


def _single_byte_range(value: str, *, total: int) -> tuple[int, int]:
    if not value.startswith("bytes=") or "," in value or total <= 0:
        raise ValueError("invalid_range")
    raw = value.removeprefix("bytes=").strip()
    left, separator, right = raw.partition("-")
    if not separator:
        raise ValueError("invalid_range")
    if not left:
        suffix = int(right)
        if suffix <= 0:
            raise ValueError("invalid_range")
        return max(0, total - suffix), total - 1
    start = int(left)
    end = int(right) if right else total - 1
    if start < 0 or start >= total or end < start:
        raise ValueError("invalid_range")
    return start, min(end, total - 1)
