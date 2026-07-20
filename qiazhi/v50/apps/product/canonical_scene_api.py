from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from experience.canonical_scene import CanonicalProjectionKind
from product.agent_case_store import AgentCaseStore
from product.canonical_scene import CanonicalSceneOwner, CanonicalSceneUnavailable
from product.product_store import ProductStore


CANONICAL_SCENE_API_PREFIX = "/api/v50/scenes"


def create_canonical_scene_router(
    *,
    product_store: ProductStore,
    session_cookie: str,
    case_store: AgentCaseStore,
) -> APIRouter:
    router = APIRouter(prefix=CANONICAL_SCENE_API_PREFIX, tags=["canonical-mingli-scene"])
    owner = CanonicalSceneOwner(case_store=case_store)

    def authenticated_account(request: Request) -> dict[str, object]:
        token = request.cookies.get(session_cookie, "")
        account = product_store.account_for_token(token) if token else None
        if not account:
            raise HTTPException(status_code=401, detail="authentication_required")
        return account

    @router.get("/cases/{case_id}")
    def canonical_scene(case_id: str, request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        try:
            bundle = owner.issue(
                case_id=case_id,
                participant_id=str(account["user_id"]),
                account_role=str(account.get("account_role") or "member"),
            )
        except CanonicalSceneUnavailable as exc:
            detail = str(exc)
            status = 404 if detail == "canonical_scene_case_not_found" else 409
            raise HTTPException(status_code=status, detail=detail) from exc
        return bundle.model_dump(mode="json")

    @router.get("/cases/{case_id}/projections/{projection_kind}")
    def canonical_projection(
        case_id: str,
        projection_kind: CanonicalProjectionKind,
        request: Request,
    ) -> dict[str, object]:
        account = authenticated_account(request)
        try:
            envelope = owner.issue_projection(
                case_id=case_id,
                participant_id=str(account["user_id"]),
                account_role=str(account.get("account_role") or "member"),
                projection_kind=projection_kind,
            )
        except CanonicalSceneUnavailable as exc:
            detail = str(exc)
            status = 404 if detail == "canonical_scene_case_not_found" else 409
            raise HTTPException(status_code=status, detail=detail) from exc
        return envelope.model_dump(mode="json")

    return router
