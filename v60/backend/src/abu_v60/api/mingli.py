from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from abu_v60.api.identity import SessionDependency
from abu_v60.db import engine
from abu_v60.mingli import MingliOwnerCaseService, OwnerCaseError, OwnerCaseInput
from abu_v60.mingli.service import CaseNotFoundError, MingliCaseService

router = APIRouter(prefix="/api/v60/cases", tags=["mingli"])
service = MingliCaseService(engine)
owner_cases = MingliOwnerCaseService(engine)


@router.get("")
def list_cases(session: SessionDependency) -> list[dict[str, Any]]:
    return service.list_cases(account_ref=session.account.account_ref)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_case(
    payload: OwnerCaseInput,
    session: SessionDependency,
) -> dict[str, object]:
    try:
        return owner_cases.create(
            account_ref=session.account.account_ref,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post("/{case_ref}/activate")
def activate_case(
    case_ref: str,
    session: SessionDependency,
) -> dict[str, object]:
    try:
        return owner_cases.activate(
            account_ref=session.account.account_ref,
            case_ref=case_ref,
        )
    except OwnerCaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/{case_ref}/workspace")
def case_workspace(
    case_ref: str,
    session: SessionDependency,
) -> dict[str, Any]:
    try:
        return service.workspace(account_ref=session.account.account_ref, case_ref=case_ref)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
