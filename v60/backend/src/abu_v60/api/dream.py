from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from abu_v60.api.identity import SessionDependency
from abu_v60.db import engine
from abu_v60.dream import DreamGroveError
from abu_v60.dream.errors import DreamConflictError, DreamStateError
from abu_v60.dream.service import DreamService
from abu_v60.game import DreamCommandEnvelope

router = APIRouter(prefix="/api/v60/dream", tags=["dream"])
service = DreamService(engine)


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
