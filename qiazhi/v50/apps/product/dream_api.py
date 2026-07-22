from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from experience.dream import DREAM_PILOT_CONSENT_VERSION, visit_view
from product.agent_case_store import AgentCaseStore
from product.dream_feature import DreamFeaturePolicy
from product.dream_service import DreamBridgeError, DreamJourneyService
from product.dream_store_contracts import DreamStore
from product.product_store import ProductStore


DREAM_API_PREFIX = "/api/v50/dream"


class DreamVisitRequest(BaseModel):
    home_case_id: str = Field(default="", max_length=180)


class DreamTreeSelectionRequest(BaseModel):
    scene_ref: str = Field(min_length=16, max_length=180)


class DreamConsentRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=180)
    accepted: Literal[True]
    consent_version: Literal[DREAM_PILOT_CONSENT_VERSION] = DREAM_PILOT_CONSENT_VERSION


class DreamConsentWithdrawalRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=180)
    confirmed: Literal[True]


def create_dream_router(
    *,
    product_store: ProductStore,
    session_cookie: str,
    case_store: AgentCaseStore,
    dream_store: DreamStore,
    feature_policy: DreamFeaturePolicy,
) -> APIRouter:
    router = APIRouter(prefix=DREAM_API_PREFIX, tags=["abu-dream-bridge"])
    service = DreamJourneyService(
        case_store=case_store,
        dream_store=dream_store,
        feature_policy=feature_policy,
    )

    def user_id(request: Request) -> str:
        token = request.cookies.get(session_cookie, "")
        account = product_store.account_for_token(token) if token else None
        if not account:
            raise HTTPException(status_code=401, detail="authentication_required")
        return str(account["user_id"])

    @router.get("/status")
    def feature_status(
        request: Request,
        case_id: str = Query(default="", max_length=180),
    ) -> dict[str, object]:
        return service.feature_status(
            user_id=user_id(request),
            case_id=case_id,
        ).model_dump(mode="json")

    @router.get("/consent")
    def consent_status(
        request: Request,
        case_id: str = Query(min_length=1, max_length=180),
    ) -> dict[str, object]:
        try:
            status = service.consent_status(user_id=user_id(request), case_id=case_id)
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return status.model_dump(mode="json")

    @router.post("/consent")
    def grant_consent(
        payload: DreamConsentRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            status = service.grant_consent(
                user_id=user_id(request),
                case_id=payload.case_id,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return status.model_dump(mode="json")

    @router.post("/consent/withdraw")
    def withdraw_consent(
        payload: DreamConsentWithdrawalRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            status = service.withdraw_consent(
                user_id=user_id(request),
                case_id=payload.case_id,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return status.model_dump(mode="json")

    @router.post("/visits")
    def create_visit(payload: DreamVisitRequest, request: Request) -> dict[str, object]:
        try:
            visit = service.create_or_resume_visit(
                user_id=user_id(request),
                home_case_id=payload.home_case_id,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return visit_view(visit).model_dump(mode="json")

    @router.get("/visits/{visit_id}")
    def read_visit(visit_id: str, request: Request) -> dict[str, object]:
        try:
            visit = service.get_visit(user_id=user_id(request), visit_id=visit_id)
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return visit_view(visit).model_dump(mode="json")

    @router.post("/visits/{visit_id}/enter")
    def enter_visit(visit_id: str, request: Request) -> dict[str, object]:
        try:
            visit = service.enter(user_id=user_id(request), visit_id=visit_id)
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return visit_view(visit).model_dump(mode="json")

    @router.get("/visits/{visit_id}/encounter")
    def encounter(visit_id: str, request: Request) -> dict[str, object]:
        try:
            projection = service.encounter(user_id=user_id(request), visit_id=visit_id)
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return projection.model_dump(mode="json")

    @router.post("/visits/{visit_id}/select-tree")
    def select_tree(
        visit_id: str,
        payload: DreamTreeSelectionRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            visit = service.select_tree(
                user_id=user_id(request),
                visit_id=visit_id,
                public_scene_ref=payload.scene_ref,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return visit_view(visit).model_dump(mode="json")

    @router.get("/visits/{visit_id}/trees/{scene_ref}")
    def tree_projection(
        visit_id: str,
        scene_ref: str,
        request: Request,
    ) -> dict[str, object]:
        try:
            projection = service.tree_projection(
                user_id=user_id(request),
                visit_id=visit_id,
                public_scene_ref=scene_ref,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return projection.model_dump(mode="json")

    @router.get("/visits/{visit_id}/trees/{scene_ref}/mirror")
    def mirror_projection(
        visit_id: str,
        scene_ref: str,
        request: Request,
    ) -> dict[str, object]:
        try:
            projection = service.mirror_projection(
                user_id=user_id(request),
                visit_id=visit_id,
                public_scene_ref=scene_ref,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return projection.model_dump(mode="json")

    @router.post("/visits/{visit_id}/mirror/open")
    def open_mirror(visit_id: str, request: Request) -> dict[str, object]:
        try:
            visit = service.open_mirror(user_id=user_id(request), visit_id=visit_id)
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return visit_view(visit).model_dump(mode="json")

    @router.post("/visits/{visit_id}/mirror/close")
    def close_mirror(visit_id: str, request: Request) -> dict[str, object]:
        try:
            visit = service.close_mirror(user_id=user_id(request), visit_id=visit_id)
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return visit_view(visit).model_dump(mode="json")

    @router.get("/visits/{visit_id}/trees/{scene_ref}/mirror/context")
    def mirror_context(
        visit_id: str,
        scene_ref: str,
        request: Request,
        stage: str = Query(default="natal", max_length=40),
        selected: str = Query(default="", max_length=240),
        layer: str = Query(default="overview", max_length=80),
    ) -> dict[str, object]:
        try:
            return service.mirror_context(
                user_id=user_id(request),
                visit_id=visit_id,
                public_scene_ref=scene_ref,
                stage=stage,
                selected_object_ref=selected,
                visible_layer=layer,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc

    return router


def _http_error(error: DreamBridgeError) -> HTTPException:
    detail = str(error)
    if detail == "dream_feature_disabled":
        return HTTPException(status_code=404, detail=detail)
    if detail == "dream_visit_not_found":
        return HTTPException(status_code=404, detail=detail)
    if detail in {
        "DREAM_ENCOUNTER_UNAVAILABLE",
        "dream_scene_authorization_unavailable",
        "dream_scene_source_version_changed",
        "dream_pilot_composition_invalid",
        "dream_human_consent_identity_conflict",
    }:
        return HTTPException(status_code=409, detail=detail)
    if detail in {
        "dream_human_case_not_owned",
        "dream_human_scene_not_formally_available",
    }:
        return HTTPException(status_code=422, detail=detail)
    if detail in {
        "dream_visit_version_conflict",
        "dream_tree_selection_locked",
        "dream_tree_selection_not_allowed",
        "dream_scene_not_selected",
        "dream_scene_not_in_encounter",
        "dream_encounter_not_ready",
        "dream_visit_completed",
        "dream_mirror_not_open",
        "dream_mirror_open_not_allowed",
        "dream_mirror_close_not_allowed",
    }:
        return HTTPException(status_code=409, detail=detail)
    return HTTPException(status_code=422, detail=detail)


__all__ = ["DREAM_API_PREFIX", "create_dream_router"]
