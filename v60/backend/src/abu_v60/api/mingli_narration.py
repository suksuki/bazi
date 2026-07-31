from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status

from abu_v60.api.identity import SessionDependency
from abu_v60.db import engine
from abu_v60.media import TTSProviderError, TTSUnavailableError
from abu_v60.media.mingli_narration import (
    MingliNarrationConflictError,
    MingliNarrationError,
    MingliNarrationService,
)
from abu_v60.mingli.narration_contracts import MingliNarrationPrepareRequest

router = APIRouter(prefix="/api/v60/mingli/narrations", tags=["mingli-narration"])
service = MingliNarrationService(engine)


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
