from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from experience.compiler import compile_topic, load_topic_package
from experience.runtime import TheaterRuntime
from experience.store import TheaterStore
from product.agent_case_store import AgentCaseStore
from product.canonical_scene import CanonicalSceneOwner
from product.product_store import ProductStore
from product.theater_api_context import TheaterRouteContext
from product.theater_api_contracts import (
    DirectorActionRequest,
    ExperimentActionRequest,
    ExperimentNodeRequest,
    ExperimentSaveRequest,
    ParticipantActionRequest,
    PerformancePrepareRequest,
    PrivateCompleteRequest,
    SessionCreateRequest,
    SessionJoinRequest,
)
from product.theater_director_api import register_director_routes
from product.theater_envelope import ProductExperienceEnvelopePort
from product.theater_experiment import ProductMingliExperimentPort
from product.theater_experiment_api import register_experiment_routes
from product.theater_performance import TheaterPerformanceService
from product.theater_performance_api import register_performance_routes
from product.theater_session_api import register_session_routes


THEATER_API_PREFIX = "/api/v50/theater"
TOPIC_DIR = Path(__file__).resolve().parents[2] / "packages" / "experience" / "topics"


def build_theater_runtime(*, store: TheaterStore) -> TheaterRuntime:
    topics = [
        compile_topic(load_topic_package(TOPIC_DIR / "topic00_living_theater.json")),
        compile_topic(load_topic_package(TOPIC_DIR / "topic00_performance_proof01.json")),
        compile_topic(load_topic_package(TOPIC_DIR / "topic01_contract_fixture.json")),
        compile_topic(load_topic_package(TOPIC_DIR / "topic01_irreplaceable_node.json")),
    ]
    return TheaterRuntime(store=store, topics=topics)


def create_theater_router(
    *,
    product_store: ProductStore,
    session_cookie: str,
    case_store: AgentCaseStore,
    theater_store: TheaterStore,
    runtime: TheaterRuntime | None = None,
    performance_service: TheaterPerformanceService | None = None,
) -> APIRouter:
    router = APIRouter(prefix=THEATER_API_PREFIX, tags=["abu-living-theater"])
    resolved_runtime = runtime or build_theater_runtime(store=theater_store)
    scene_owner = CanonicalSceneOwner(case_store=case_store)
    context = TheaterRouteContext(
        product_store=product_store,
        session_cookie=session_cookie,
        theater_store=theater_store,
        runtime=resolved_runtime,
        envelope_port=ProductExperienceEnvelopePort(scene_owner=scene_owner),
        experiment_port=ProductMingliExperimentPort(
            case_store=case_store,
            scene_owner=scene_owner,
            theater_store=theater_store,
            runtime=resolved_runtime,
        ),
        performance_service=performance_service or TheaterPerformanceService.from_environment(),
    )
    register_session_routes(router, context)
    register_experiment_routes(router, context)
    register_director_routes(router, context)
    register_performance_routes(router, context)
    return router


__all__ = [
    "DirectorActionRequest",
    "ExperimentActionRequest",
    "ExperimentNodeRequest",
    "ExperimentSaveRequest",
    "ParticipantActionRequest",
    "PerformancePrepareRequest",
    "PrivateCompleteRequest",
    "SessionCreateRequest",
    "SessionJoinRequest",
    "build_theater_runtime",
    "create_theater_router",
]
