from __future__ import annotations

from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import JSONResponse, StreamingResponse

from v17_rebirth.backend.api import stream_v17
from v17_rebirth.backend.services.auth_service import require_authenticated_request

router = APIRouter(dependencies=[Depends(require_authenticated_request)])


@router.get("/v17/stream", response_model=None)
@router.get("/api/v17/stream", response_model=None)
async def stream_v17_get(
    will_proxy: str = Query(default="stable", pattern="^(stable|aggressive|neutral)$"),
    birth_time: Optional[str] = Query(default=None),
    gender: Optional[str] = Query(default="male", pattern="^(male|female)$"),
    flow_year: Optional[int] = Query(default=None, ge=1800, le=2200),
    v17_origin: Optional[str] = Query(default=None),
    ui_lang: Optional[str] = Query(default="zh", pattern="^(zh|en|ko)$"),
) -> Union[StreamingResponse, JSONResponse]:
    return await stream_v17.stream_v17(
        will_proxy=will_proxy,
        birth_time=birth_time,
        gender=gender,
        flow_year=flow_year,
        v17_origin=v17_origin,
        ui_lang=ui_lang,
    )


@router.post("/v17/stream", response_model=None)
@router.post("/api/v17/stream", response_model=None)
async def stream_v17_post(
    payload: Dict[str, Any],
    will_proxy: str = Query(default="stable", pattern="^(stable|aggressive|neutral)$"),
    birth_time: Optional[str] = Query(default=None),
    gender: Optional[str] = Query(default="male", pattern="^(male|female)$"),
    flow_year: Optional[int] = Query(default=None, ge=1800, le=2200),
    ui_lang: Optional[str] = Query(default="zh", pattern="^(zh|en|ko)$"),
) -> Union[StreamingResponse, JSONResponse]:
    return await stream_v17.stream_v17_post(
        payload=payload,
        will_proxy=will_proxy,
        birth_time=birth_time,
        gender=gender,
        flow_year=flow_year,
        ui_lang=ui_lang,
    )


@router.post("/v17/action")
@router.post("/api/v17/action")
async def v17_action(
    payload: Dict[str, Any],
    v17_origin: Optional[str] = Header(default=None, alias="v17_origin"),
) -> JSONResponse:
    return await stream_v17.v17_action(payload=payload, v17_origin=v17_origin)


@router.post("/v17/freeze-report")
@router.post("/api/v17/freeze-report")
async def freeze_report(
    payload: Dict[str, Any],
    v17_origin_header: Optional[str] = Header(default=None, alias="v17_origin"),
) -> JSONResponse:
    return await stream_v17.freeze_report(payload=payload, v17_origin_header=v17_origin_header)
