from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from abu_v60.db import engine
from abu_v60.identity.contracts import LoginRequest, SessionView
from abu_v60.identity.service import IdentityService, InvalidCredentialsError
from abu_v60.settings import settings

router = APIRouter(prefix="/api/v60/auth", tags=["identity"])
service = IdentityService(engine)
COOKIE_NAME = "abu_v60_session"


def require_session(abu_v60_session: str | None = Cookie(default=None)) -> SessionView:
    if not abu_v60_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication_required"
        )
    try:
        return service.session_for_token(abu_v60_session)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


SessionDependency = Annotated[SessionView, Depends(require_session)]


@router.post("/login", response_model=SessionView)
def login(payload: LoginRequest, response: Response) -> SessionView:
    try:
        token, session = service.login(email=str(payload.email), password=payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        secure=settings.environment not in {"local", "test"},
        max_age=7 * 24 * 60 * 60,
        path="/",
    )
    return session


@router.get("/me", response_model=SessionView)
def me(session: SessionDependency) -> SessionView:
    return session


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    abu_v60_session: str | None = Cookie(default=None),
) -> None:
    if abu_v60_session:
        service.logout(abu_v60_session)
    response.delete_cookie(COOKIE_NAME, path="/")
