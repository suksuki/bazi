from __future__ import annotations

import asyncio
import secrets
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request, WebSocket, WebSocketDisconnect

from experience.runtime import TheaterRuntimeError
from product.theater_api_context import TheaterRouteContext, public_run, token_hash
from product.theater_api_contracts import (
    ParticipantActionRequest,
    PrivateCompleteRequest,
    SessionCreateRequest,
    SessionJoinRequest,
)


def register_session_routes(router: APIRouter, context: TheaterRouteContext) -> None:
    runtime = context.runtime
    store = context.theater_store

    @router.get("/topics")
    def list_topics() -> dict[str, object]:
        return {"status": "ready", "topics": runtime.list_topics()}

    @router.post("/sessions")
    def create_session(payload: SessionCreateRequest, request: Request) -> dict[str, object]:
        account = context.account_for_request(request)
        if payload.mode == "live" and (not account or str(account.get("account_role")) != "admin"):
            raise HTTPException(status_code=403, detail="live_session_requires_admin")
        try:
            session = runtime.create_session(
                topic_id=payload.topic_id,
                topic_version=payload.topic_version,
                mode=payload.mode,
            )
        except TheaterRuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "session_ready", "session": session.model_dump(mode="json")}

    @router.post("/sessions/{session_id}/join")
    def join_session(session_id: str, payload: SessionJoinRequest, request: Request) -> dict[str, object]:
        account = context.account_for_request(request)
        participant_id = str(account["user_id"]) if account else f"guest-{uuid4().hex[:20]}"
        access_token = secrets.token_urlsafe(32)
        session = store.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="theater_session_not_found")
        try:
            envelope = context.envelope_port.issue_envelope(
                participant_id=participant_id,
                topic_id=session.topic_id,
                topic_version=session.topic_version,
                disclosure_level=payload.disclosure_level,
                case_id=payload.case_id,
                permitted_capabilities=runtime.required_capabilities(
                    topic_id=session.topic_id,
                    topic_version=session.topic_version,
                ),
            )
            run = runtime.join(
                session_id=session_id,
                envelope=envelope,
                access_token_hash=token_hash(access_token),
            )
        except (TheaterRuntimeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {
            "status": "joined",
            "participant_run": public_run(run),
            "access_token": access_token,
            "envelope_mode": envelope.mode,
            "snapshot": runtime.snapshot(session_id=session_id, participant_run_id=run.participant_run_id),
        }

    @router.get("/sessions/{session_id}")
    def session_snapshot(
        session_id: str,
        request: Request,
        participant_run_id: str | None = None,
        access_token: str = "",
        after: int = Query(default=0, ge=0),
    ) -> dict[str, object]:
        account = context.account_for_request(request)
        if participant_run_id:
            context.authorize_run(participant_run_id=participant_run_id, access_token=access_token, account=account)
        try:
            return runtime.snapshot(
                session_id=session_id,
                participant_run_id=participant_run_id,
                after_sequence=after,
            )
        except TheaterRuntimeError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/sessions/{session_id}/participant/complete")
    def complete_private(session_id: str, payload: PrivateCompleteRequest, request: Request) -> dict[str, object]:
        context.authorize_run(
            participant_run_id=payload.participant_run_id,
            access_token=payload.access_token,
            account=context.account_for_request(request),
        )
        try:
            run = runtime.complete_private(
                session_id=session_id,
                participant_run_id=payload.participant_run_id,
                response=payload.response,
            )
        except TheaterRuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "private_scene_completed", "participant_run": public_run(run)}

    @router.post("/sessions/{session_id}/participant/advance")
    def participant_advance(session_id: str, payload: ParticipantActionRequest, request: Request) -> dict[str, object]:
        context.authorize_run(
            participant_run_id=payload.participant_run_id,
            access_token=payload.access_token,
            account=context.account_for_request(request),
        )
        session = store.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="theater_session_not_found")
        if session.mode not in {"solo", "time_shift"}:
            raise HTTPException(status_code=403, detail="shared_live_clock_owned_by_director")
        try:
            session = runtime.advance(session_id=session_id, event=payload.event)
        except TheaterRuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "advanced", "session": session.model_dump(mode="json")}

    @router.get("/sessions/{session_id}/replay")
    def replay_session(
        session_id: str,
        request: Request,
        participant_run_id: str | None = None,
        access_token: str = "",
    ) -> dict[str, object]:
        if participant_run_id:
            context.authorize_run(
                participant_run_id=participant_run_id,
                access_token=access_token,
                account=context.account_for_request(request),
            )
        return runtime.replay(session_id=session_id, participant_run_id=participant_run_id)

    @router.websocket("/sessions/{session_id}/stream")
    async def stream_session(
        websocket: WebSocket,
        session_id: str,
        participant_run_id: str | None = None,
        access_token: str = "",
        after: int = 0,
    ) -> None:
        if participant_run_id:
            try:
                context.authorize_run(
                    participant_run_id=participant_run_id,
                    access_token=access_token,
                    account=context.account_for_websocket(websocket),
                )
            except HTTPException:
                await websocket.close(code=4403)
                return
        await websocket.accept()
        cursor = max(0, after)
        idle_ticks = 0
        try:
            initial = runtime.snapshot(
                session_id=session_id,
                participant_run_id=participant_run_id,
                after_sequence=cursor,
            )
            await websocket.send_json(initial)
            cursor = int(initial["session"]["sequence"])
            while True:
                await asyncio.sleep(0.55)
                snapshot = runtime.snapshot(
                    session_id=session_id,
                    participant_run_id=participant_run_id,
                    after_sequence=cursor,
                )
                if snapshot["events"]:
                    await websocket.send_json(snapshot)
                    cursor = int(snapshot["session"]["sequence"])
                    idle_ticks = 0
                else:
                    idle_ticks += 1
                    if idle_ticks >= 4:
                        snapshot["heartbeat"] = True
                        await websocket.send_json(snapshot)
                        idle_ticks = 0
        except WebSocketDisconnect:
            return
        except TheaterRuntimeError:
            await websocket.close(code=4404)
