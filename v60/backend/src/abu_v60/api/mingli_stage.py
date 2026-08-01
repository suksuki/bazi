from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, Response, status

from abu_v60.api.identity import SessionDependency
from abu_v60.db import engine
from abu_v60.mingli.reading_summary import (
    MingliReadingSummaryError,
    MingliReadingSummaryService,
)
from abu_v60.mingli.stage import MingliStageError, MingliStageService
from abu_v60.mingli.stage_contracts import MingliStageMode

router = APIRouter(prefix="/api/v60/mingli", tags=["mingli-stage"])
service = MingliStageService(engine)
reading_summaries = MingliReadingSummaryService(engine)


@router.get("/stage/subjects")
def stage_subjects(
    response: Response,
    session: SessionDependency,
) -> list[dict[str, object]]:
    try:
        subjects = service.subjects(account_ref=session.account.account_ref)
    except MingliStageError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    response.headers["Cache-Control"] = "private, no-store"
    return subjects


@router.get("/stage")
def stage_projection(
    response: Response,
    session: SessionDependency,
    subject_id: Annotated[str, Query(min_length=1)] = "current",
    mode: MingliStageMode = MingliStageMode.NATAL_4,
    year: Annotated[int | None, Query(ge=1900, le=2200)] = None,
) -> dict[str, Any]:
    try:
        projection = service.project(
            account_ref=session.account.account_ref,
            subject_id=subject_id,
            stage_mode=mode,
            selected_year=year,
        )
    except MingliStageError as exc:
        reason = str(exc)
        code = (
            status.HTTP_404_NOT_FOUND
            if reason in {
                "mingli_stage_subject_not_found",
                "mingli_stage_showcase_not_seeded",
            }
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code=code, detail=reason) from exc
    response.headers["Cache-Control"] = "private, no-store"
    return projection.model_dump(mode="json")


@router.get("/stage/reading-summary")
def stage_reading_summary(
    response: Response,
    session: SessionDependency,
    case_ref: Annotated[str, Query(min_length=1)],
) -> dict[str, Any]:
    try:
        projection = reading_summaries.project(
            account_ref=session.account.account_ref,
            case_ref=case_ref,
        )
    except MingliReadingSummaryError as exc:
        reason = str(exc)
        code = (
            status.HTTP_404_NOT_FOUND
            if reason == "mingli_reading_summary_case_not_found"
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=code, detail=reason) from exc
    response.headers["Cache-Control"] = "private, no-store"
    return projection.model_dump(mode="json")
