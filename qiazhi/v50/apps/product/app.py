from __future__ import annotations

import mimetypes
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from product.agent_api import create_agent_router
from product.agent_case_store import AgentCaseStore, build_agent_case_store
from product.agent_job_store import AgentJobStore
from product.canonical_scene_api import create_canonical_scene_router
from product.experience_api import create_experience_router
from product.legacy_usage import LegacyUsageStore, build_legacy_usage_store, legacy_route_key
from product.narration_api import create_narration_router
from product.narrated_workspace import NarratedWorkspaceService
from product.product_store import ProductStore, ProductStoreError, build_product_store
from product.theater_api import create_theater_router
from product.theater_store import build_theater_store
from product.voice_validation_api import create_voice_validation_router
from product.voice_validation_store import VoiceValidationStore, build_voice_validation_store
from core.contracts import BirthInputCanonical
from core.engines import BirthCalendarResolutionError, resolve_birth_input_pillars
from core.life_domains import domain_manifest
from core.life_case import LifeCase, LifeCaseRevision


STATIC_DIR = Path(__file__).resolve().parent / "static" / "l5"
EXPERIENCE_STATIC_DIR = Path(__file__).resolve().parent / "static" / "experience"
PRODUCT_API_PREFIX = "/api/v50/product"
PRODUCT_SESSION_COOKIE = "deepbazi_v50_session"

# Ubuntu's system MIME database may not include WebP. StaticFiles delegates to
# mimetypes, so register it once for every Abu animation and future asset pack.
mimetypes.add_type("image/webp", ".webp")
LOGGER = logging.getLogger(__name__)


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


def create_product_app(
    *,
    product_store: ProductStore | None = None,
    mingli_agent=None,
    agent_case_store: AgentCaseStore | None = None,
    agent_job_store: AgentJobStore | None = None,
    theater_performance_service=None,
    narrated_workspace_service=None,
    voice_validation_store: VoiceValidationStore | None = None,
    legacy_usage_store: LegacyUsageStore | None = None,
) -> FastAPI:
    """Build the production Abu-led Mingli application.

    This surface intentionally excludes the retired Alpha session runtime,
    deterministic Brain reading chain, and template Product Mode APIs.
    """

    app = FastAPI(title="DeepBazi", version="v50.mingli-product.v1")
    store = product_store or build_product_store()
    resolved_case_store = agent_case_store or build_agent_case_store()
    theater_store = build_theater_store()
    resolved_narration_service = (
        narrated_workspace_service
        if narrated_workspace_service is not None
        else NarratedWorkspaceService.from_environment()
    )
    resolved_voice_validation_store = voice_validation_store or build_voice_validation_store()
    resolved_legacy_usage_store = legacy_usage_store or build_legacy_usage_store()
    app.include_router(
        create_agent_router(
            product_store=store,
            session_cookie=PRODUCT_SESSION_COOKIE,
            agent=mingli_agent,
            case_store=resolved_case_store,
            job_store=agent_job_store,
        )
    )
    app.include_router(
        create_theater_router(
            product_store=store,
            session_cookie=PRODUCT_SESSION_COOKIE,
            case_store=resolved_case_store,
            theater_store=theater_store,
            performance_service=theater_performance_service,
        )
    )
    app.include_router(
        create_narration_router(
            product_store=store,
            session_cookie=PRODUCT_SESSION_COOKIE,
            case_store=resolved_case_store,
            service=resolved_narration_service,
        )
    )
    app.include_router(
        create_voice_validation_router(
            product_store=store,
            session_cookie=PRODUCT_SESSION_COOKIE,
            case_store=resolved_case_store,
            narration_service=resolved_narration_service,
            validation_store=resolved_voice_validation_store,
        )
    )
    app.include_router(
        create_experience_router(
            product_store=store,
            session_cookie=PRODUCT_SESSION_COOKIE,
            case_store=resolved_case_store,
            legacy_usage_store=resolved_legacy_usage_store,
        )
    )
    app.include_router(
        create_canonical_scene_router(
            product_store=store,
            session_cookie=PRODUCT_SESSION_COOKIE,
            case_store=resolved_case_store,
        )
    )

    @app.get("/abu-theater", include_in_schema=False)
    def abu_theater_entry() -> RedirectResponse:
        return RedirectResponse(
            url="/experience-static/internal-tools/abu-says-mingli-s0-v12/index.html",
            status_code=307,
        )

    @app.get(
        "/experience-static/prototypes/abu-says-mingli-s0/index.html",
        include_in_schema=False,
    )
    @app.get(
        "/experience-static/prototypes/abu-says-mingli-s0-v11/index.html",
        include_in_schema=False,
    )
    @app.get(
        "/experience-static/prototypes/abu-says-mingli-s0-v12/index.html",
        include_in_schema=False,
    )
    def legacy_abu_theater_entry() -> RedirectResponse:
        return RedirectResponse(url="/abu-theater", status_code=308)

    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="product-assets")
    app.mount(
        "/experience-static",
        StaticFiles(directory=EXPERIENCE_STATIC_DIR),
        name="experience-static",
    )

    @app.middleware("http")
    async def trace_legacy_runtime_usage(request: Request, call_next):
        response = await call_next(request)
        route_key = legacy_route_key(request.url.path)
        if route_key:
            try:
                resolved_legacy_usage_store.record(route_key=route_key, method=request.method)
            except Exception:  # noqa: BLE001 - observability must never interrupt the product.
                LOGGER.exception("legacy_runtime_usage_record_failed")
        return response

    @app.get("/", include_in_schema=False)
    def product_entry() -> RedirectResponse:
        return RedirectResponse(url="/abu-theater", status_code=307)

    @app.get("/app", include_in_schema=False)
    def product_index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/experience", include_in_schema=False)
    @app.get("/experience/", include_in_schema=False)
    def experience_index() -> FileResponse:
        return FileResponse(EXPERIENCE_STATIC_DIR / "index.html")

    @app.get("/theater", include_in_schema=False)
    @app.get("/theater/studio", include_in_schema=False)
    def theater_index() -> FileResponse:
        return FileResponse(STATIC_DIR / "theater.html")

    @app.get("/visual-alpha", include_in_schema=False)
    def retired_visual_alpha_route() -> RedirectResponse:
        return RedirectResponse(url="/app", status_code=308)

    @app.get("/app.js", include_in_schema=False)
    def product_javascript() -> FileResponse:
        return FileResponse(STATIC_DIR / "app.js", media_type="application/javascript")

    @app.get("/styles.css", include_in_schema=False)
    def product_styles() -> FileResponse:
        return FileResponse(STATIC_DIR / "styles.css", media_type="text/css")

    @app.get("/theater.js", include_in_schema=False)
    def theater_javascript() -> FileResponse:
        return FileResponse(STATIC_DIR / "theater.js", media_type="application/javascript")

    @app.get("/theater.css", include_in_schema=False)
    def theater_styles() -> FileResponse:
        return FileResponse(STATIC_DIR / "theater.css", media_type="text/css")

    @app.get("/favicon.ico", include_in_schema=False)
    def product_favicon() -> FileResponse:
        return FileResponse(STATIC_DIR / "assets" / "deepbazi_symbol.png", media_type="image/png")

    @app.get("/health", include_in_schema=False)
    def product_health() -> dict[str, object]:
        return {
            "status": "ok",
            "product": "deepbazi_v50",
            "cognitive_core": "llm_mingli_agent",
            "storage": store.storage_name,
        }

    @app.get(f"{PRODUCT_API_PREFIX}/manifest")
    def product_manifest() -> dict[str, object]:
        return {
            "version": "deepbazi.product_manifest.v1",
            "product": "Abu-led intelligent Mingli system",
            "domains": domain_manifest(),
            "cognitive_core": "llm_mingli_agent",
            "fact_systems": ["bazi", "ziwei"],
            "retired_chains": ["alpha_session_runtime", "deterministic_brain_reading", "template_product_projection"],
        }

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

    @app.post(f"{PRODUCT_API_PREFIX}/auth/register")
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

    @app.post(f"{PRODUCT_API_PREFIX}/auth/login")
    def login(payload: ProductLoginRequest, request: Request, response: Response) -> dict[str, object]:
        account = store.authenticate(email=payload.email, password=payload.password)
        if not account:
            raise HTTPException(status_code=401, detail="invalid_email_or_password")
        set_session_cookie(response, request, store.create_session(user_id=str(account["user_id"])))
        return {"status": "authenticated", "account": account, "persistent": store.persistent}

    @app.get(f"{PRODUCT_API_PREFIX}/auth/me")
    def current_account(request: Request) -> dict[str, object]:
        return {"status": "authenticated", "account": authenticated_account(request), "persistent": store.persistent}

    @app.post(f"{PRODUCT_API_PREFIX}/auth/logout")
    def logout(request: Request, response: Response) -> dict[str, object]:
        token = request.cookies.get(PRODUCT_SESSION_COOKIE, "")
        if token:
            store.revoke_session(token)
        response.delete_cookie(PRODUCT_SESSION_COOKIE, path="/")
        return {"status": "logged_out"}

    @app.get(f"{PRODUCT_API_PREFIX}/profiles")
    def list_profiles(request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        return {"status": "profile_archive_ready", "profiles": store.list_profiles(user_id=str(account["user_id"]))}

    @app.post(f"{PRODUCT_API_PREFIX}/profiles")
    def create_profile(payload: ProductProfileRequest, request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        birth_input = _resolve_birth(payload.birth_input)
        profile = store.save_profile(user_id=str(account["user_id"]), birth_input=birth_input)
        return {"status": "profile_saved", "profile": profile}

    @app.get(f"{PRODUCT_API_PREFIX}/profiles/{{profile_id}}")
    def get_profile(profile_id: str, request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        profile = store.get_profile(user_id=str(account["user_id"]), profile_id=profile_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="profile_not_found")
        return {"status": "profile_ready", "profile": profile}

    @app.put(f"{PRODUCT_API_PREFIX}/profiles/{{profile_id}}")
    def update_profile(profile_id: str, payload: ProductProfileRequest, request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        previous_profile = store.get_profile(user_id=str(account["user_id"]), profile_id=profile_id)
        birth_input = _resolve_birth(payload.birth_input)
        try:
            profile = store.save_profile(
                user_id=str(account["user_id"]),
                birth_input=birth_input,
                profile_id=profile_id,
            )
        except ProductStoreError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        invalidated_case_count = 0
        if previous_profile and previous_profile.get("profile_fingerprint") != profile.get("profile_fingerprint"):
            invalidated_case_count = _supersede_profile_life_cases(
                case_store=resolved_case_store,
                user_id=str(account["user_id"]),
                profile_id=profile_id,
            )
        return {
            "status": "profile_updated",
            "profile": profile,
            "superseded_life_case_count": invalidated_case_count,
        }

    @app.delete(f"{PRODUCT_API_PREFIX}/profiles/{{profile_id}}")
    def delete_profile(profile_id: str, request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        if not store.delete_profile(user_id=str(account["user_id"]), profile_id=profile_id):
            raise HTTPException(status_code=404, detail="profile_not_found")
        return {"status": "profile_deleted", "profile_id": profile_id}

    return app


def _supersede_profile_life_cases(
    *,
    case_store: AgentCaseStore,
    user_id: str,
    profile_id: str,
) -> int:
    changed = 0
    for row in case_store.list_for_user(user_id=user_id):
        if str(row.get("profile_id") or "") != profile_id or not row.get("life_case"):
            continue
        life_case = LifeCase.model_validate(row["life_case"])
        if life_case.status != "active":
            continue
        now = datetime.now(timezone.utc).isoformat()
        life_case = life_case.model_copy(update={
            "status": "superseded",
            "chart_version": life_case.chart_version.model_copy(update={"active": False}),
            "revisions": [
                *life_case.revisions,
                LifeCaseRevision(
                    revision_id=f"life-revision-{uuid4().hex[:16]}",
                    kind="chart_version_changed",
                    created_at=now,
                    summary="出生资料已修改；旧命盘版本及其洞察保留审计，但不再作为当前认知。",
                ),
            ],
            "updated_at": now,
        })
        row["life_case"] = life_case.model_dump(mode="json")
        case_store.save(
            case_id=str(row["case_id"]),
            user_id=user_id,
            profile_id=profile_id,
            payload=row,
        )
        changed += 1
    return changed


def _resolve_birth(birth_input: BirthInputCanonical) -> BirthInputCanonical:
    try:
        resolved = resolve_birth_input_pillars(birth_input)
    except BirthCalendarResolutionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not all((resolved.year_pillar, resolved.month_pillar, resolved.day_pillar, resolved.hour_pillar)):
        raise HTTPException(status_code=422, detail="complete_pillars_required")
    return resolved


app = create_product_app()
