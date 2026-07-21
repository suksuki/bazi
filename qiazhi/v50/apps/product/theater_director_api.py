from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Request

from experience.runtime import TheaterRuntimeError
from product.theater_api_context import TheaterRouteContext
from product.theater_api_contracts import DirectorActionRequest


def register_director_routes(router: APIRouter, context: TheaterRouteContext) -> None:
    runtime = context.runtime

    @router.post("/sessions/{session_id}/director/advance")
    def director_advance(session_id: str, payload: DirectorActionRequest, request: Request) -> dict[str, object]:
        context.require_admin(request)
        try:
            session = runtime.advance(session_id=session_id, event=payload.event)
        except TheaterRuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "advanced", "session": session.model_dump(mode="json")}

    @router.post("/sessions/{session_id}/director/rejoin")
    def director_rejoin(session_id: str, request: Request) -> dict[str, object]:
        context.require_admin(request)
        try:
            session = runtime.rejoin(session_id=session_id)
        except TheaterRuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "rejoined", "session": session.model_dump(mode="json")}

    @router.post("/sessions/{session_id}/director/reveal")
    def director_reveal(session_id: str, request: Request) -> dict[str, object]:
        context.require_admin(request)
        try:
            event = runtime.reveal_group_trace(session_id=session_id)
        except TheaterRuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "revealed", "event": event.model_dump(mode="json")}

    @router.post("/sessions/{session_id}/director/{action}")
    def director_pause_resume(session_id: str, action: Literal["pause", "resume"], request: Request) -> dict[str, object]:
        context.require_admin(request)
        session = runtime.set_paused(session_id=session_id, paused=action == "pause")
        return {"status": action, "session": session.model_dump(mode="json")}
