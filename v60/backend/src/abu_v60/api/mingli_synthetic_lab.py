from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Query, Response, status

from abu_v60.api.identity import SessionDependency
from abu_v60.db import engine
from abu_v60.mingli.synthetic_experiment_service import (
    SyntheticExperimentError,
    SyntheticExperimentService,
)

router = APIRouter(prefix="/api/v60/mingli/lab", tags=["mingli-synthetic-lab"])
service = SyntheticExperimentService(engine)
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
        catalog = service.catalog()["experiments"][0]
        if experiment_ref != catalog["experiment_ref"]:
            raise SyntheticExperimentError("mingli_synthetic_experiment_not_found")
        snapshot = service.snapshot(variant=variant, run_ref=run_ref)
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
