from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from abu_v60.api.identity import SessionDependency
from abu_v60.db import engine
from abu_v60.dream import DreamGroveError
from abu_v60.dream.errors import DreamConflictError, DreamStateError
from abu_v60.dream.personal_journey import DreamPersonalJourneyService
from abu_v60.dream.personal_journey_contracts import (
    DreamPersonalCheckInRequest,
    DreamPersonalObservationRequest,
    DreamPrivateInquiryRequest,
)
from abu_v60.dream.service import DreamService
from abu_v60.game import DreamCommandEnvelope

router = APIRouter(prefix="/api/v60/dream", tags=["dream"])
service = DreamService(engine)
personal_journey = DreamPersonalJourneyService(engine)


def _translate_error(exc: ValueError) -> HTTPException:
    return HTTPException(
        status_code=409 if isinstance(exc, DreamConflictError) else 422,
        detail=str(exc),
    )


@router.post("/encounter")
def ensure_encounter(session: SessionDependency) -> dict[str, Any]:
    try:
        return service.ensure_encounter(account_ref=session.account.account_ref)
    except (DreamStateError, DreamConflictError) as exc:
        raise _translate_error(exc) from exc


@router.get("/entry")
def dream_entry(session: SessionDependency) -> dict[str, Any]:
    try:
        return service.entry(account_ref=session.account.account_ref)
    except (DreamGroveError, DreamStateError, DreamConflictError) as exc:
        raise _translate_error(exc) from exc


@router.post("/grove/{candidate_ref}")
def select_grove_tree(
    candidate_ref: str,
    session: SessionDependency,
) -> dict[str, Any]:
    try:
        return service.start_grove_encounter(
            account_ref=session.account.account_ref,
            candidate_ref=candidate_ref,
        )
    except (DreamGroveError, DreamStateError, DreamConflictError) as exc:
        raise _translate_error(exc) from exc


@router.post("/grove/{candidate_ref}/personal-inquiry")
def start_personal_grove_journey(
    candidate_ref: str,
    payload: DreamPrivateInquiryRequest,
    session: SessionDependency,
) -> dict[str, Any]:
    try:
        return service.start_personal_grove_encounter(
            account_ref=session.account.account_ref,
            candidate_ref=candidate_ref,
            request=payload,
        )
    except (DreamGroveError, DreamStateError, DreamConflictError) as exc:
        raise _translate_error(exc) from exc


@router.post("/personal-observation")
def select_personal_observation(
    payload: DreamPersonalObservationRequest,
    session: SessionDependency,
) -> dict[str, Any]:
    try:
        task = personal_journey.select_observation(
            account_ref=session.account.account_ref,
            request=payload,
        )
        with engine.connect() as connection:
            projection = personal_journey.project_encounter(
                connection,
                account_ref=session.account.account_ref,
                encounter_ref=task.encounter_ref,
            )
    except (DreamStateError, DreamConflictError) as exc:
        raise _translate_error(exc) from exc
    if projection is None:
        raise HTTPException(status_code=404, detail="dream_personal_journey_not_found")
    return projection.model_dump(mode="json")


@router.post("/personal-check-in")
def record_personal_checkin(
    payload: DreamPersonalCheckInRequest,
    session: SessionDependency,
) -> dict[str, Any]:
    try:
        personal_journey.record_checkin(
            account_ref=session.account.account_ref,
            request=payload,
        )
        with engine.connect() as connection:
            projection = personal_journey.project_grove(
                connection,
                account_ref=session.account.account_ref,
            )
    except (DreamStateError, DreamConflictError) as exc:
        raise _translate_error(exc) from exc
    if projection is None:
        raise HTTPException(status_code=404, detail="dream_personal_journey_not_found")
    return projection.model_dump(mode="json")


@router.get("/encounter")
def encounter(session: SessionDependency) -> dict[str, Any]:
    try:
        return service.snapshot(account_ref=session.account.account_ref)
    except DreamStateError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/command")
def execute_command(
    payload: DreamCommandEnvelope,
    session: SessionDependency,
) -> dict[str, Any]:
    try:
        return service.execute_command(
            account_ref=session.account.account_ref,
            envelope=payload,
        )
    except (DreamStateError, DreamConflictError) as exc:
        raise _translate_error(exc) from exc
