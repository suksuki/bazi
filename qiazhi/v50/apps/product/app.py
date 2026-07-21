from __future__ import annotations

from fastapi import FastAPI

from product.abu_narration import AbuNarrationService
from product.agent_api import create_agent_router
from product.agent_case_store import AgentCaseStore, build_agent_case_store
from product.agent_job_store import AgentJobStore
from product.canonical_scene_api import create_canonical_scene_router
from product.experience_api import create_experience_router
from product.legacy_usage import LegacyUsageStore, build_legacy_usage_store
from product.narration_api import create_narration_router
from product.product_api import PRODUCT_API_PREFIX, PRODUCT_SESSION_COOKIE, create_product_router
from product.product_store import ProductStore, build_product_store
from product.product_surface import register_product_surface
from product.theater_api import create_theater_router
from product.theater_store import build_theater_store
from product.voice_validation_api import create_voice_validation_router
from product.voice_validation_store import VoiceValidationStore, build_voice_validation_store


def create_product_app(
    *,
    product_store: ProductStore | None = None,
    mingli_agent=None,
    agent_case_store: AgentCaseStore | None = None,
    agent_job_store: AgentJobStore | None = None,
    theater_performance_service=None,
    abu_narration_service=None,
    voice_validation_store: VoiceValidationStore | None = None,
    legacy_usage_store: LegacyUsageStore | None = None,
) -> FastAPI:
    """Compose the production Abu-led Mingli application."""

    app = FastAPI(title="DeepBazi", version="v50.mingli-product.v1")
    store = product_store or build_product_store()
    case_store = agent_case_store or build_agent_case_store()
    narration_service = abu_narration_service or AbuNarrationService.from_environment()
    resolved_legacy_usage_store = legacy_usage_store or build_legacy_usage_store()

    app.include_router(
        create_agent_router(
            product_store=store,
            session_cookie=PRODUCT_SESSION_COOKIE,
            agent=mingli_agent,
            case_store=case_store,
            job_store=agent_job_store,
        )
    )
    app.include_router(
        create_theater_router(
            product_store=store,
            session_cookie=PRODUCT_SESSION_COOKIE,
            case_store=case_store,
            theater_store=build_theater_store(),
            performance_service=theater_performance_service,
        )
    )
    app.include_router(
        create_narration_router(
            product_store=store,
            session_cookie=PRODUCT_SESSION_COOKIE,
            case_store=case_store,
            service=narration_service,
        )
    )
    app.include_router(
        create_voice_validation_router(
            product_store=store,
            session_cookie=PRODUCT_SESSION_COOKIE,
            case_store=case_store,
            narration_service=narration_service,
            validation_store=voice_validation_store or build_voice_validation_store(),
        )
    )
    app.include_router(
        create_experience_router(
            product_store=store,
            session_cookie=PRODUCT_SESSION_COOKIE,
            case_store=case_store,
            legacy_usage_store=resolved_legacy_usage_store,
        )
    )
    app.include_router(
        create_canonical_scene_router(
            product_store=store,
            session_cookie=PRODUCT_SESSION_COOKIE,
            case_store=case_store,
        )
    )
    app.include_router(create_product_router(store=store, case_store=case_store))
    register_product_surface(app, store=store, legacy_usage_store=resolved_legacy_usage_store)
    return app


app = create_product_app()


__all__ = ["PRODUCT_API_PREFIX", "PRODUCT_SESSION_COOKIE", "app", "create_product_app"]
