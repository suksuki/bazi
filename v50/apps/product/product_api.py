from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from core.contracts import BirthInputCanonical
from core.life_domains import domain_manifest
from product.agent_case_store import AgentCaseStore
from product.product_profile_service import resolve_profile_birth, supersede_profile_life_cases
from product.product_store import ProductStore, ProductStoreError


PRODUCT_API_PREFIX = "/api/v50/product"
PRODUCT_SESSION_COOKIE = "deepbazi_v50_session"


class ProductRegisterRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=48)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    role: str = "member"


class ProductLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class ProductProfileRequest(BaseModel):
    birth_input: BirthInputCanonical


def create_product_router(*, store: ProductStore, case_store: AgentCaseStore) -> APIRouter:
    router = APIRouter()

    def authenticated_account(request: Request) -> dict[str, object]:
        token = request.cookies.get(PRODUCT_SESSION_COOKIE, "")
        account = store.account_for_token(token) if token else None
        if not account:
            raise HTTPException(status_code=401, detail="authentication_required")
        return account

    def set_session_cookie(response: Response, request: Request, token: str) -> None:
        response.set_cookie(
            PRODUCT_SESSION_COOKIE,
            token,
            max_age=60 * 60 * 24 * 30,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
            path="/",
        )

    @router.get(f"{PRODUCT_API_PREFIX}/manifest")
    def product_manifest() -> dict[str, object]:
        return {
            "version": "deepbazi.product_manifest.v1",
            "product": "Abu-led intelligent Mingli system",
            "domains": domain_manifest(),
            "cognitive_core": "llm_mingli_agent",
            "fact_systems": ["bazi", "ziwei"],
            "retired_chains": ["alpha_session_runtime", "deterministic_brain_reading", "template_product_projection"],
        }

    @router.post(f"{PRODUCT_API_PREFIX}/auth/register")
    def register(payload: ProductRegisterRequest, request: Request, response: Response) -> dict[str, object]:
        try:
            account = store.register_account(
                email=payload.email,
                password=payload.password,
                display_name=payload.display_name,
                role=payload.role,
            )
        except ProductStoreError as exc:
            status = 409 if str(exc) == "email_already_registered" else 422
            raise HTTPException(status_code=status, detail=str(exc)) from exc
        set_session_cookie(response, request, store.create_session(user_id=str(account["user_id"])))
        return {"status": "registered", "account": account, "persistent": store.persistent}

    @router.post(f"{PRODUCT_API_PREFIX}/auth/login")
    def login(payload: ProductLoginRequest, request: Request, response: Response) -> dict[str, object]:
        account = store.authenticate(email=payload.email, password=payload.password)
        if not account:
            raise HTTPException(status_code=401, detail="invalid_email_or_password")
        set_session_cookie(response, request, store.create_session(user_id=str(account["user_id"])))
        return {"status": "authenticated", "account": account, "persistent": store.persistent}

    @router.get(f"{PRODUCT_API_PREFIX}/auth/me")
    def current_account(request: Request) -> dict[str, object]:
        return {"status": "authenticated", "account": authenticated_account(request), "persistent": store.persistent}

    @router.post(f"{PRODUCT_API_PREFIX}/auth/logout")
    def logout(request: Request, response: Response) -> dict[str, object]:
        token = request.cookies.get(PRODUCT_SESSION_COOKIE, "")
        if token:
            store.revoke_session(token)
        response.delete_cookie(PRODUCT_SESSION_COOKIE, path="/")
        return {"status": "logged_out"}

    @router.get(f"{PRODUCT_API_PREFIX}/profiles")
    def list_profiles(request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        return {"status": "profile_archive_ready", "profiles": store.list_profiles(user_id=str(account["user_id"]))}

    @router.post(f"{PRODUCT_API_PREFIX}/profiles")
    def create_profile(payload: ProductProfileRequest, request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        profile = store.save_profile(
            user_id=str(account["user_id"]),
            birth_input=resolve_profile_birth(payload.birth_input),
        )
        return {"status": "profile_saved", "profile": profile}

    @router.get(f"{PRODUCT_API_PREFIX}/profiles/{{profile_id}}")
    def get_profile(profile_id: str, request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        profile = store.get_profile(user_id=str(account["user_id"]), profile_id=profile_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="profile_not_found")
        return {"status": "profile_ready", "profile": profile}

    @router.put(f"{PRODUCT_API_PREFIX}/profiles/{{profile_id}}")
    def update_profile(profile_id: str, payload: ProductProfileRequest, request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        user_id = str(account["user_id"])
        previous_profile = store.get_profile(user_id=user_id, profile_id=profile_id)
        try:
            profile = store.save_profile(
                user_id=user_id,
                birth_input=resolve_profile_birth(payload.birth_input),
                profile_id=profile_id,
            )
        except ProductStoreError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        invalidated_case_count = 0
        if previous_profile and previous_profile.get("profile_fingerprint") != profile.get("profile_fingerprint"):
            invalidated_case_count = supersede_profile_life_cases(
                case_store=case_store,
                user_id=user_id,
                profile_id=profile_id,
            )
        return {
            "status": "profile_updated",
            "profile": profile,
            "superseded_life_case_count": invalidated_case_count,
        }

    @router.delete(f"{PRODUCT_API_PREFIX}/profiles/{{profile_id}}")
    def delete_profile(profile_id: str, request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        if not store.delete_profile(user_id=str(account["user_id"]), profile_id=profile_id):
            raise HTTPException(status_code=404, detail="profile_not_found")
        return {"status": "profile_deleted", "profile_id": profile_id}

    return router
