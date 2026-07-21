from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from product.theater_api_context import TheaterRouteContext
from product.theater_api_contracts import ExperimentActionRequest, ExperimentNodeRequest, ExperimentSaveRequest
from product.theater_experiment import MingliExperimentUnavailable


def register_experiment_routes(router: APIRouter, context: TheaterRouteContext) -> None:
    port = context.experiment_port

    @router.get("/sessions/{session_id}/participant/experiment")
    def load_experiment(
        session_id: str,
        request: Request,
        participant_run_id: str,
        access_token: str,
    ) -> dict[str, object]:
        context.authorize_run(
            participant_run_id=participant_run_id,
            access_token=access_token,
            account=context.account_for_request(request),
        )
        try:
            return port.load(session_id=session_id, participant_run_id=participant_run_id)
        except MingliExperimentUnavailable as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/sessions/{session_id}/participant/experiment/predict")
    def predict_experiment_node(session_id: str, payload: ExperimentNodeRequest, request: Request) -> dict[str, object]:
        context.authorize_run(
            participant_run_id=payload.participant_run_id,
            access_token=payload.access_token,
            account=context.account_for_request(request),
        )
        try:
            return port.predict(
                session_id=session_id,
                participant_run_id=payload.participant_run_id,
                node_id=payload.node_id,
            )
        except (MingliExperimentUnavailable, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/sessions/{session_id}/participant/experiment/ablate")
    def ablate_experiment_node(session_id: str, payload: ExperimentNodeRequest, request: Request) -> dict[str, object]:
        context.authorize_run(
            participant_run_id=payload.participant_run_id,
            access_token=payload.access_token,
            account=context.account_for_request(request),
        )
        try:
            return port.ablate(
                session_id=session_id,
                participant_run_id=payload.participant_run_id,
                node_id=payload.node_id,
            )
        except (MingliExperimentUnavailable, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/sessions/{session_id}/participant/experiment/restore")
    def restore_experiment(session_id: str, payload: ExperimentActionRequest, request: Request) -> dict[str, object]:
        context.authorize_run(
            participant_run_id=payload.participant_run_id,
            access_token=payload.access_token,
            account=context.account_for_request(request),
        )
        try:
            return port.restore(session_id=session_id, participant_run_id=payload.participant_run_id)
        except MingliExperimentUnavailable as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/sessions/{session_id}/participant/experiment/save")
    def save_experiment(session_id: str, payload: ExperimentSaveRequest, request: Request) -> dict[str, object]:
        context.authorize_run(
            participant_run_id=payload.participant_run_id,
            access_token=payload.access_token,
            account=context.account_for_request(request),
        )
        try:
            return port.save(
                session_id=session_id,
                participant_run_id=payload.participant_run_id,
                observation=payload.observation,
                open_question=payload.open_question,
            )
        except MingliExperimentUnavailable as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
