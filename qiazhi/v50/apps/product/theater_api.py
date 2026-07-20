from __future__ import annotations

import asyncio
import hashlib
import secrets
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from product.agent_case_store import AgentCaseStore
from product.product_store import ProductStore
from product.theater_envelope import ProductExperienceEnvelopePort
from product.theater_experiment import MingliExperimentUnavailable, ProductMingliExperimentPort
from product.theater_performance import TheaterPerformanceError, TheaterPerformanceService
from experience.compiler import compile_topic, load_topic_package
from experience.runtime import TheaterRuntime, TheaterRuntimeError
from experience.store import TheaterStore


THEATER_API_PREFIX = "/api/v50/theater"
TOPIC_DIR = Path(__file__).resolve().parents[2] / "packages" / "experience" / "topics"


class SessionCreateRequest(BaseModel):
    topic_id: str = "topic-00-seen-and-continuing"
    topic_version: str = "1.0.0"
    mode: Literal["live", "time_shift", "solo"] = "solo"


class SessionJoinRequest(BaseModel):
    case_id: str | None = None
    disclosure_level: Literal["observer", "chart_facts", "approved_insights"] = "approved_insights"


class PrivateCompleteRequest(BaseModel):
    participant_run_id: str
    access_token: str = Field(min_length=16, max_length=200)
    response: str = Field(default="", max_length=800)


class ParticipantActionRequest(BaseModel):
    participant_run_id: str
    access_token: str = Field(min_length=16, max_length=200)
    event: str = Field(default="next", min_length=1, max_length=80)


class PerformancePrepareRequest(BaseModel):
    participant_run_id: str
    access_token: str = Field(min_length=16, max_length=200)


class ExperimentNodeRequest(BaseModel):
    participant_run_id: str
    access_token: str = Field(min_length=16, max_length=200)
    node_id: str = Field(min_length=1, max_length=260)


class ExperimentActionRequest(BaseModel):
    participant_run_id: str
    access_token: str = Field(min_length=16, max_length=200)


class ExperimentSaveRequest(ExperimentActionRequest):
    observation: str = Field(default="", max_length=1200)
    open_question: str = Field(default="", max_length=1200)


class DirectorActionRequest(BaseModel):
    event: str = Field(default="next", min_length=1, max_length=80)


def build_theater_runtime(*, store: TheaterStore) -> TheaterRuntime:
    topics = [
        compile_topic(load_topic_package(TOPIC_DIR / "topic00_living_theater.json")),
        compile_topic(load_topic_package(TOPIC_DIR / "topic00_performance_proof01.json")),
        compile_topic(load_topic_package(TOPIC_DIR / "topic01_contract_fixture.json")),
        compile_topic(load_topic_package(TOPIC_DIR / "topic01_irreplaceable_node.json")),
    ]
    return TheaterRuntime(store=store, topics=topics)


def create_theater_router(
    *,
    product_store: ProductStore,
    session_cookie: str,
    case_store: AgentCaseStore,
    theater_store: TheaterStore,
    runtime: TheaterRuntime | None = None,
    performance_service: TheaterPerformanceService | None = None,
) -> APIRouter:
    router = APIRouter(prefix=THEATER_API_PREFIX, tags=["abu-living-theater"])
    runtime = runtime or build_theater_runtime(store=theater_store)
    performance_service = performance_service or TheaterPerformanceService.from_environment()
    envelope_port = ProductExperienceEnvelopePort(case_store=case_store)
    experiment_port = ProductMingliExperimentPort(
        case_store=case_store,
        theater_store=theater_store,
        runtime=runtime,
    )

    def account_for_request(request: Request):
        token = request.cookies.get(session_cookie, "")
        return product_store.account_for_token(token) if token else None

    def account_for_websocket(websocket: WebSocket):
        token = websocket.cookies.get(session_cookie, "")
        return product_store.account_for_token(token) if token else None

    def require_admin(request: Request):
        account = account_for_request(request)
        if not account or str(account.get("account_role") or "") != "admin":
            raise HTTPException(status_code=403, detail="theater_director_requires_admin")
        return account

    def authorize_run(*, participant_run_id: str, access_token: str, account) -> None:
        run = theater_store.get_participant(participant_run_id)
        if not run:
            raise HTTPException(status_code=404, detail="participant_run_not_found")
        account_matches = bool(account and str(account.get("user_id")) == run.participant_ref)
        token_matches = bool(
            access_token
            and run.access_token_hash
            and secrets.compare_digest(run.access_token_hash, _token_hash(access_token))
        )
        if not account_matches and not token_matches:
            raise HTTPException(status_code=403, detail="participant_access_denied")

    @router.get("/topics")
    def list_topics() -> dict[str, object]:
        return {"status": "ready", "topics": runtime.list_topics()}

    @router.post("/sessions")
    def create_session(payload: SessionCreateRequest, request: Request) -> dict[str, object]:
        account = account_for_request(request)
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
        account = account_for_request(request)
        participant_id = str(account["user_id"]) if account else f"guest-{uuid4().hex[:20]}"
        access_token = secrets.token_urlsafe(32)
        session = theater_store.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="theater_session_not_found")
        try:
            envelope = envelope_port.issue_envelope(
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
                access_token_hash=_token_hash(access_token),
            )
        except (TheaterRuntimeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {
            "status": "joined",
            "participant_run": _public_run(run),
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
        account = account_for_request(request)
        if participant_run_id:
            authorize_run(participant_run_id=participant_run_id, access_token=access_token, account=account)
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
        authorize_run(
            participant_run_id=payload.participant_run_id,
            access_token=payload.access_token,
            account=account_for_request(request),
        )
        try:
            run = runtime.complete_private(
                session_id=session_id,
                participant_run_id=payload.participant_run_id,
                response=payload.response,
            )
        except TheaterRuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "private_scene_completed", "participant_run": _public_run(run)}

    @router.post("/sessions/{session_id}/participant/advance")
    def participant_advance(session_id: str, payload: ParticipantActionRequest, request: Request) -> dict[str, object]:
        authorize_run(
            participant_run_id=payload.participant_run_id,
            access_token=payload.access_token,
            account=account_for_request(request),
        )
        session = theater_store.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="theater_session_not_found")
        if session.mode not in {"solo", "time_shift"}:
            raise HTTPException(status_code=403, detail="shared_live_clock_owned_by_director")
        try:
            session = runtime.advance(session_id=session_id, event=payload.event)
        except TheaterRuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "advanced", "session": session.model_dump(mode="json")}

    @router.get("/sessions/{session_id}/participant/experiment")
    def load_experiment(
        session_id: str,
        request: Request,
        participant_run_id: str,
        access_token: str,
    ) -> dict[str, object]:
        authorize_run(
            participant_run_id=participant_run_id,
            access_token=access_token,
            account=account_for_request(request),
        )
        try:
            return experiment_port.load(
                session_id=session_id,
                participant_run_id=participant_run_id,
            )
        except MingliExperimentUnavailable as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/sessions/{session_id}/participant/experiment/predict")
    def predict_experiment_node(
        session_id: str,
        payload: ExperimentNodeRequest,
        request: Request,
    ) -> dict[str, object]:
        authorize_run(
            participant_run_id=payload.participant_run_id,
            access_token=payload.access_token,
            account=account_for_request(request),
        )
        try:
            return experiment_port.predict(
                session_id=session_id,
                participant_run_id=payload.participant_run_id,
                node_id=payload.node_id,
            )
        except (MingliExperimentUnavailable, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/sessions/{session_id}/participant/experiment/ablate")
    def ablate_experiment_node(
        session_id: str,
        payload: ExperimentNodeRequest,
        request: Request,
    ) -> dict[str, object]:
        authorize_run(
            participant_run_id=payload.participant_run_id,
            access_token=payload.access_token,
            account=account_for_request(request),
        )
        try:
            return experiment_port.ablate(
                session_id=session_id,
                participant_run_id=payload.participant_run_id,
                node_id=payload.node_id,
            )
        except (MingliExperimentUnavailable, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/sessions/{session_id}/participant/experiment/restore")
    def restore_experiment(
        session_id: str,
        payload: ExperimentActionRequest,
        request: Request,
    ) -> dict[str, object]:
        authorize_run(
            participant_run_id=payload.participant_run_id,
            access_token=payload.access_token,
            account=account_for_request(request),
        )
        try:
            return experiment_port.restore(
                session_id=session_id,
                participant_run_id=payload.participant_run_id,
            )
        except MingliExperimentUnavailable as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/sessions/{session_id}/participant/experiment/save")
    def save_experiment(
        session_id: str,
        payload: ExperimentSaveRequest,
        request: Request,
    ) -> dict[str, object]:
        authorize_run(
            participant_run_id=payload.participant_run_id,
            access_token=payload.access_token,
            account=account_for_request(request),
        )
        try:
            return experiment_port.save(
                session_id=session_id,
                participant_run_id=payload.participant_run_id,
                observation=payload.observation,
                open_question=payload.open_question,
            )
        except MingliExperimentUnavailable as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/sessions/{session_id}/director/advance")
    def director_advance(session_id: str, payload: DirectorActionRequest, request: Request) -> dict[str, object]:
        require_admin(request)
        try:
            session = runtime.advance(session_id=session_id, event=payload.event)
        except TheaterRuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "advanced", "session": session.model_dump(mode="json")}

    @router.post("/sessions/{session_id}/director/rejoin")
    def director_rejoin(session_id: str, request: Request) -> dict[str, object]:
        require_admin(request)
        try:
            session = runtime.rejoin(session_id=session_id)
        except TheaterRuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "rejoined", "session": session.model_dump(mode="json")}

    @router.post("/sessions/{session_id}/director/reveal")
    def director_reveal(session_id: str, request: Request) -> dict[str, object]:
        require_admin(request)
        try:
            event = runtime.reveal_group_trace(session_id=session_id)
        except TheaterRuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "revealed", "event": event.model_dump(mode="json")}

    @router.post("/sessions/{session_id}/director/{action}")
    def director_pause_resume(session_id: str, action: Literal["pause", "resume"], request: Request) -> dict[str, object]:
        require_admin(request)
        session = runtime.set_paused(session_id=session_id, paused=action == "pause")
        return {"status": action, "session": session.model_dump(mode="json")}

    @router.get("/sessions/{session_id}/replay")
    def replay_session(
        session_id: str,
        request: Request,
        participant_run_id: str | None = None,
        access_token: str = "",
    ) -> dict[str, object]:
        if participant_run_id:
            authorize_run(
                participant_run_id=participant_run_id,
                access_token=access_token,
                account=account_for_request(request),
            )
        return runtime.replay(session_id=session_id, participant_run_id=participant_run_id)

    @router.post("/sessions/{session_id}/cues/{cue_instance_id}/performance")
    def prepare_performance(
        session_id: str,
        cue_instance_id: str,
        payload: PerformancePrepareRequest,
        request: Request,
    ) -> dict[str, object]:
        authorize_run(
            participant_run_id=payload.participant_run_id,
            access_token=payload.access_token,
            account=account_for_request(request),
        )
        run = theater_store.get_participant(payload.participant_run_id)
        cue = theater_store.get_cue(cue_instance_id)
        if not run or run.session_id != session_id:
            raise HTTPException(status_code=404, detail="participant_run_not_found")
        if not cue or cue.cue_instance_id not in {
            item.cue_instance_id for item in theater_store.list_cues(session_id)
        }:
            raise HTTPException(status_code=404, detail="performance_cue_not_found")
        if cue.visibility == "participant_private" and cue.participant_run_id != run.participant_run_id:
            raise HTTPException(status_code=403, detail="private_performance_access_denied")
        envelope = theater_store.get_envelope(cue.envelope_id) if cue.envelope_id else None
        try:
            package = performance_service.prepare(cue=cue, envelope=envelope)
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
        authorize_run(
            participant_run_id=participant_run_id,
            access_token=access_token,
            account=account_for_request(request),
        )
        run = theater_store.get_participant(participant_run_id)
        package = performance_service.repository.get(package_id)
        if not run or run.session_id != session_id or not package:
            raise HTTPException(status_code=404, detail="performance_package_not_found")
        if package.visibility == "participant_private" and package.participant_run_id != participant_run_id:
            raise HTTPException(status_code=403, detail="private_performance_access_denied")
        audio_path = performance_service.repository.audio_path(package_id)
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="frozen_performance_audio_missing")
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            filename=f"{package_id}.wav",
            content_disposition_type="inline",
        )

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
                authorize_run(
                    participant_run_id=participant_run_id,
                    access_token=access_token,
                    account=account_for_websocket(websocket),
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

    return router


def _token_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _public_run(run) -> dict[str, object]:
    payload = run.model_dump(mode="json")
    payload.pop("access_token_hash", None)
    return payload
