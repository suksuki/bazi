from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Response, status

from abu_v60.api.identity import SessionDependency
from abu_v60.db import engine
from abu_v60.mingli.synthetic_experiment_service import (
    SyntheticExperimentError,
    SyntheticExperimentService,
)
from abu_v60.mingli.synthetic_suite_service import (
    SyntheticSuiteService,
    SyntheticSuiteServiceError,
)
from abu_v60.mingli.synthetic_training_contracts import SyntheticSuiteRunRequestInput
from abu_v60.mingli.synthetic_training_service import (
    SyntheticTrainingService,
    SyntheticTrainingServiceError,
)

router = APIRouter(prefix="/api/v60/mingli/lab", tags=["mingli-synthetic-lab"])
service = SyntheticExperimentService(engine)
suite_service = SyntheticSuiteService(engine)
training_service = SyntheticTrainingService(engine)
SYNTHETIC_LAB_REVIEWER_ROLES = frozenset({"admin", "local_qa_owner"})


def _require_synthetic_lab_reviewer(session: Any) -> None:
    if session.account.account_role not in SYNTHETIC_LAB_REVIEWER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="mingli_synthetic_lab_reviewer_required",
        )


@router.get("/synthetic-experiments")
def synthetic_experiment_catalog(
    response: Response,
    session: SessionDependency,
) -> dict[str, Any]:
    _require_synthetic_lab_reviewer(session)
    response.headers["Cache-Control"] = "private, no-store"
    return service.catalog()


@router.get("/synthetic-suite-runs")
def synthetic_suite_run_catalog(
    response: Response,
    session: SessionDependency,
) -> dict[str, Any]:
    _require_synthetic_lab_reviewer(session)
    try:
        catalog = suite_service.catalog()
    except SyntheticSuiteServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    response.headers["Cache-Control"] = "private, no-store"
    return catalog


@router.get("/synthetic-suite-runs/{suite_run_ref}")
def synthetic_suite_run_snapshot(
    suite_run_ref: str,
    response: Response,
    session: SessionDependency,
) -> dict[str, Any]:
    _require_synthetic_lab_reviewer(session)
    try:
        catalog = suite_service.catalog(suite_run_ref=suite_run_ref)
    except SyntheticSuiteServiceError as exc:
        reason = str(exc)
        code = (
            status.HTTP_404_NOT_FOUND
            if reason == "mingli_synthetic_suite_run_not_found"
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=code, detail=reason) from exc
    response.headers["Cache-Control"] = "private, no-store"
    return catalog


@router.get("/synthetic-training")
def synthetic_training_status(
    response: Response,
    session: SessionDependency,
) -> dict[str, Any]:
    _require_synthetic_lab_reviewer(session)
    try:
        projection = training_service.status(
            requester_account_ref=session.account.account_ref,
        )
    except SyntheticTrainingServiceError as exc:
        raise _training_http_error(exc) from exc
    response.headers["Cache-Control"] = "private, no-store"
    return projection


@router.post(
    "/synthetic-suite-run-requests",
    status_code=status.HTTP_202_ACCEPTED,
)
def create_synthetic_suite_run_request(
    payload: SyntheticSuiteRunRequestInput,
    background_tasks: BackgroundTasks,
    response: Response,
    session: SessionDependency,
) -> dict[str, Any]:
    _require_synthetic_lab_reviewer(session)
    try:
        projection = training_service.create_request(
            requester_account_ref=session.account.account_ref,
            payload=payload,
        )
    except SyntheticTrainingServiceError as exc:
        raise _training_http_error(exc) from exc
    if projection.status == "QUEUED":
        background_tasks.add_task(
            training_service.run_request,
            request_ref=projection.request_ref,
        )
    response.headers["Cache-Control"] = "private, no-store"
    return projection.model_dump(mode="json")


@router.get("/synthetic-suite-run-requests/{request_ref}")
def synthetic_suite_run_request(
    request_ref: str,
    response: Response,
    session: SessionDependency,
) -> dict[str, Any]:
    _require_synthetic_lab_reviewer(session)
    try:
        projection = training_service.get_request(
            requester_account_ref=session.account.account_ref,
            request_ref=request_ref,
        )
    except SyntheticTrainingServiceError as exc:
        raise _training_http_error(exc) from exc
    response.headers["Cache-Control"] = "private, no-store"
    return projection.model_dump(mode="json")


@router.get("/synthetic-experiments/{experiment_ref}/snapshot")
def synthetic_experiment_snapshot(
    experiment_ref: str,
    response: Response,
    session: SessionDependency,
    variant: Literal["A", "B"] = "A",
    run_ref: Annotated[str | None, Query(min_length=1)] = None,
) -> dict[str, Any]:
    _require_synthetic_lab_reviewer(session)
    try:
        snapshot = service.snapshot(
            experiment_ref=experiment_ref,
            variant=variant,
            run_ref=run_ref,
        )
    except SyntheticExperimentError as exc:
        reason = str(exc)
        code = (
            status.HTTP_404_NOT_FOUND
            if reason in {
                "mingli_synthetic_experiment_not_found",
                "mingli_synthetic_experiment_not_run",
            }
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=code, detail=reason) from exc
    response.headers["Cache-Control"] = "private, no-store"
    return snapshot


def _training_http_error(error: SyntheticTrainingServiceError) -> HTTPException:
    reason = str(error)
    if reason == "mingli_synthetic_training_request_not_found":
        code = status.HTTP_404_NOT_FOUND
    elif reason.startswith(("mingli_agent_runtime_", "mingli_agent_provider_")):
        code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        code = status.HTTP_409_CONFLICT
    return HTTPException(status_code=code, detail=reason)
