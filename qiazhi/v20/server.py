from __future__ import annotations

import json
import logging
import os
import hashlib
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware

from v20 import V20_VERSION
from v20.access.auth import (
    auth_status,
    guest_login,
    import_v19_auth_sessions,
    logout,
    password_login,
    register_user,
    v19_auth_migration_preview,
)
from v20.access.projection import project_runtime_for_role
from v20.access.roles import access_role_manifest
from v20.role_view.projection import apply_role_answer_view
from v20.role_view.runtime_pointer import (
    build_role_view_runtime_pointer,
    write_role_view_runtime_pointer_activate_candidate,
    write_role_view_runtime_pointer_rollback,
)
from v20.role_view.completion import build_role_view_completion_report
from v20.api.schemas import (
    FeedbackRequest,
    LatentEventCalibrationRequest,
    MeasureRequest,
    OrchestratorMemoryRecordRequest,
    PortraitCalibrationRequest,
    PractitionerCalibrationRequest,
    ProfileMutationRequest,
    QuestionReviewRequest,
    RoleQuestionClickRequest,
    QuestionSourceRankingRecordRequest,
)
from v20.api.runtime import run_runtime_from_pillars
from v20.utils.calendar import resolve_pillars, resolve_luck_pillar, resolve_target_year
from v20.corpus.artifacts import (
    find_similar_cases,
    read_corpus_artifact_status,
    read_corpus_cluster_model,
    read_corpus_coverage_summary,
    read_corpus_training_artifacts,
)
from v20.corpus.coverage import build_corpus_coverage_plan
from v20.corpus.full_precompute import build_full_precompute_manifest, preview_full_precompute_batch
from v20.corpus.job_runner import read_full_precompute_status
from v20.features.calibration import confidence_calibration_manifest
from v20.intelligence.generation import build_intelligence_generation_manifest
from v20.intelligence.knowledge_semantic_model import (
    build_knowledge_semantic_model,
    validate_knowledge_semantic_model,
)
from v20.interaction.feedback_analysis import analyze_feedback
from v20.interaction.feedback_record import record_feedback_analysis
from v20.interaction.latent_event_calibration import (
    LatentCalibrationAnswer,
    analyze_latent_event_calibration,
    latent_event_calibration_manifest,
    record_latent_event_calibration,
)
from v20.interaction.orchestrator_memory_record import (
    analyze_orchestrator_memory_signal,
    record_orchestrator_memory_signal,
)
from v20.interaction.portrait_calibration import analyze_portrait_calibration, record_portrait_calibration
from v20.interaction.portrait_ontology import portrait_ontology_manifest
from v20.interaction.practitioner_calibration import (
    PractitionerControlSelection,
    analyze_practitioner_calibration,
    record_practitioner_calibration,
)
from v20.interaction.question_ranker import question_ranking_manifest
from v20.interaction.question_review import analyze_question_review, record_question_review
from v20.interaction.question_source_record import analyze_question_source_ranking_report, record_question_source_ranking_report
from v20.interaction.role_question_click import analyze_role_question_click, record_role_question_click
from v20.interaction.question_seed_registry import question_seed_registry_manifest
from v20.knowledge.ranking import knowledge_retrieval_manifest
from v20.knowledge.approval import build_first_wave_approval_preflight, build_knowledge_approval_preflight
from v20.knowledge.catalog import build_knowledge_catalog
from v20.knowledge.completeness_audit import build_knowledge_completeness_audit
from v20.knowledge.completion import build_knowledge_completion_report
from v20.knowledge.coverage import build_knowledge_coverage_report
from v20.knowledge.directory import build_knowledge_directory_manifest
from v20.knowledge.directory_seeds import build_full_directory_seed_library
from v20.knowledge.draft_import import build_knowledge_draft_import_preview
from v20.knowledge.feature_model import build_bazi_feature_graph_model_contract
from v20.knowledge.macro_dimensions import build_macro_dimension_catalog
from v20.knowledge.migration import build_v19_knowledge_migration_audit
from v20.knowledge.release import build_knowledge_release_manifest
from v20.knowledge.review_packet import build_first_wave_review_packets, build_knowledge_review_packet
from v20.knowledge.review_assist import build_first_wave_review_assist, build_knowledge_review_assist
from v20.knowledge.review_queue import build_knowledge_review_queue
from v20.knowledge.rule_proposal import (
    build_first_wave_rule_proposal_preflight,
    build_first_wave_rule_proposals,
    build_knowledge_rule_proposals,
    build_rule_proposal_preflight,
)
from v20.knowledge.rule_extraction import (
    build_llm_rule_extraction_report,
    build_rule_extraction_report,
    validate_llm_rule_extraction_report,
    validate_rule_extraction_report,
)
from v20.knowledge.rule_library import build_knowledge_rule_library, validate_knowledge_rule_library
from v20.decision.knowledge_bridge import build_knowledge_rule_review_overlay
from v20.knowledge.source_catalog import build_knowledge_source_catalog
from v20.learning.evolution import build_evolution_dry_run_plan
from v20.learning.decision_registry_iteration import (
    build_decision_registry_iteration_report,
    read_decision_registry_iteration_artifact,
)
from v20.learning.question_ranking_learning import read_question_ranking_learning_artifact
from v20.learning.question_ranking_learning import build_question_ranking_learning_report
from v20.learning.question_dag_training import build_question_dag_training_report
from v20.learning.question_dag_policy_replay import (
    build_question_dag_policy_replay_report,
    read_question_dag_policy_replay_artifact,
)
from v20.learning.question_dag_policy_promotion import build_question_dag_policy_promotion_gate
from v20.learning.question_review_training import (
    build_question_review_training_report,
    read_question_review_training_artifact,
)
from v20.learning.role_question_click_training import (
    build_role_question_click_training_report,
    read_role_question_click_training_artifact,
)
from v20.learning.role_view_policy_candidates import (
    build_role_view_policy_candidate_report,
    read_role_view_policy_candidate_artifact,
)
from v20.learning.role_view_policy_replay import (
    build_role_view_policy_replay_report,
    read_role_view_policy_replay_artifact,
)
from v20.learning.latent_factor_calibration import latent_factor_calibration_manifest
from v20.learning.run_plan import build_learning_run_plan
from v20.learning_orchestrator.run_plan import build_learning_orchestrator_run_plan
from v20.learning_orchestrator.knowledge_rule_orchestrator import build_knowledge_rule_orchestrator_plan
from v20.learning_orchestrator.nightly_executor import read_nightly_executor_status
from v20.learning.orchestrator_policy_observability_training import build_policy_observability_training_report
from v20.learning.orchestrator_policy_candidates import read_orchestrator_policy_candidate_artifact
from v20.graph.question_source_graph import arbitrate_question_source_paths
from v20.learning.registries import registry_manifest
from v20.learning.rule_activation import (
    build_rule_activation_report,
    build_rule_activation_packet_summary,
)
from v20.learning.rule_subcondition_split import (
    build_rule_subcondition_split_report,
    read_rule_subcondition_split_artifact,
)
from v20.learning.rule_replay_eval import (
    build_rule_replay_eval_report,
    read_rule_replay_eval_artifact,
)
from v20.measurement.domain_alignment import bazi_alignment_manifest
from v20.measurement.dimensions import bazi_dimension_manifest
from v20.ops.admin_config import admin_config_status, save_admin_database_config, save_admin_llm_config
from v20.ops.admin_status import database_admin_status, llm_admin_status, llm_admin_test as run_llm_admin_test
from v20.ops.central_brain_architecture import build_central_brain_architecture_status
from v20.ops.training_tasks import (
    list_training_activation_preflights,
    list_training_tasks,
    pause_training_task,
    prepare_training_task_activation,
    read_training_task,
    start_training_task,
    training_task_registry,
)
from v20.ops.config import load_runtime_config_from_env
from v20.ops.dependencies import dependency_readiness_report
from v20.ops.logging import get_logger, log_event
from v20.ops.mainline_status import build_mainline_status
from v20.ops.profiles import validate_runtime_config
from v20.ops.readiness import liveness_report, readiness_report
from v20.ops.runtime_consumption_audit import build_runtime_consumption_audit
from v20.ops.service_unit import service_unit_manifest
from v20.ops.status import system_status_report
from v20.ops.sync import sync_readiness_report
from v20.orchestrator.runtime_policy import (
    build_runtime_policy_pointer,
    write_runtime_policy_activate_latest_candidate,
    write_runtime_policy_rollback,
)
from v20.llm.practitioner import (
    stream_practitioner_answer_with_llm,
    unwrap_practitioner_text,
    validate_practitioner_answer_day_master,
)
from v20.profiles.store import (
    create_profile_in_postgres,
    delete_profile_from_postgres,
    list_profiles_from_postgres,
    read_profile_from_postgres,
    update_profile_in_postgres,
)
from v20.redis.contracts import redis_contract_manifest, validate_redis_contract
from v20.redis.runtime_cache import (
    attach_cache_miss_meta,
    cacheable_measure_payload,
    check_rate_limit,
    clear_runtime_request_cache,
    get_runtime_cache,
    runtime_cache_status,
    runtime_cache_key,
    set_runtime_cache,
    should_cache_measure,
)
from v20.rules.catalog import build_bazi_rule_catalog
from v20.storage.postgres_schema import build_postgres_schema_contract, migration_manifest
from v20.storage.local_jsonl import local_jsonl_store_from_env
from v20.testing.matrix import build_test_coverage_matrix
from v20.testing.tiers import test_tier_manifest
from v20.validation.answer_safety_evaluator import evaluate_answer_governance_quality
from v20.validation.intelligence_generation import validate_intelligence_generation
from v20.validation.knowledge_rule_library import build_knowledge_rule_validation_report
from v20.validation.rule_synthetic import (
    build_rule_synthetic_training_report,
    read_rule_synthetic_training_artifact,
    run_rule_synthetic_suite,
)
from v20.validation.rule_portrait_batch import (
    read_rule_portrait_batch_artifact,
    run_rule_portrait_batch,
)
from v20.validation.suite import run_synthetic_suite


LOGGER = get_logger("v20.server")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Qiazhi V20",
        version=V20_VERSION,
        description="Independent V20 Bazi measurement runtime.",
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    frontend_dir = Path(__file__).resolve().parent / "frontend"
    if frontend_dir.exists():
        app.mount("/v20/ui", StaticFiles(directory=frontend_dir, html=True), name="v20_ui")

    @app.middleware("http")
    async def structured_request_logging(request: Request, call_next):
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            log_event(
                LOGGER,
                logging.ERROR,
                "request_failed",
                event="request_failed",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                error_type=type(exc).__name__,
                duration_ms=round((time.perf_counter() - start) * 1000, 2),
            )
            raise
        finally:
            level = logging.WARNING if status_code >= 400 else logging.INFO
            log_event(
                LOGGER,
                level,
                "request_completed",
                event="request_completed",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=round((time.perf_counter() - start) * 1000, 2),
                client_host=_client_host(request),
            )

    @app.get("/health")
    def health() -> dict[str, object]:
        config = load_runtime_config_from_env()
        validation = validate_runtime_config(config)
        return {
            "version": "v20.service_health.v1",
            "package_version": V20_VERSION,
            "status": "ok" if validation["ok"] else "degraded",
            "active_profile": config.active_profile,
            "ops_validation": validation,
            "runtime_mutation": False,
            "connection_policy": "no_postgres_or_redis_connection_on_health_check",
            "guardrails": [
                "V20_SERVICE_ENTRY",
                "HEALTH_CHECK_IS_READ_ONLY",
                "NO_SECRET_VALUES_RENDERED",
            ],
        }

    @app.get("/health/live")
    def health_live() -> dict[str, object]:
        return liveness_report()

    @app.get("/health/ready")
    def health_ready() -> dict[str, object]:
        return readiness_report()

    @app.get("/api/v20/auth/me")
    def auth_me(request: Request) -> dict[str, object]:
        return auth_status(request)

    @app.post("/api/v20/auth/guest")
    def auth_guest(response: Response, payload: dict = None) -> dict[str, object]:
        return guest_login(response, locale=str((payload or {}).get("locale") or "zh"))

    @app.post("/api/v20/auth/login")
    def auth_login(payload: dict[str, object], response: Response) -> dict[str, object]:
        result = password_login(payload, response)
        if not result.get("ok"):
            raise HTTPException(status_code=401, detail=result)
        return result

    @app.post("/api/v20/auth/register")
    def auth_register(payload: dict[str, object], response: Response) -> dict[str, object]:
        result = register_user(payload, response)
        if not result.get("ok"):
            raise HTTPException(status_code=400, detail=result)
        return result

    @app.post("/api/v20/auth/logout")
    def auth_logout(response: Response, request: Request) -> dict[str, object]:
        return logout(response, request)

    @app.get("/api/v20/auth/v19-migration-preview")
    def auth_v19_migration_preview() -> dict[str, object]:
        return v19_auth_migration_preview()

    @app.post("/api/v20/auth/import-v19")
    def auth_import_v19(apply: bool = False, payload: dict = None) -> dict[str, object]:
        return import_v19_auth_sessions(apply=apply, admin_password=str((payload or {}).get("admin_password") or ""))

    @app.get("/api/v20/system/status")
    def system_status() -> dict[str, object]:
        return system_status_report()

    @app.get("/api/v20/admin/db")
    def admin_database(request: Request) -> dict[str, object]:
        _require_admin_session(request)
        return database_admin_status()

    @app.get("/api/v20/admin/llm")
    def admin_llm(request: Request, probe_models: bool = False) -> dict[str, object]:
        _require_admin_session(request)
        return llm_admin_status(probe_models=probe_models)

    @app.post("/api/v20/admin/llm/test")
    def admin_llm_test_endpoint(payload: dict[str, object], request: Request) -> dict[str, object]:
        _require_admin_session(request)
        return run_llm_admin_test(payload)

    @app.get("/api/v20/admin/config")
    def admin_config(request: Request) -> dict[str, object]:
        _require_admin_session(request)
        return admin_config_status()

    @app.get("/api/v20/admin/training/tasks")
    def admin_training_tasks(request: Request, limit: int = 20) -> dict[str, object]:
        _require_admin_session(request)
        return list_training_tasks(limit=limit)

    @app.get("/api/v20/admin/training/activations")
    def admin_training_activation_preflights(request: Request, limit: int = 20) -> dict[str, object]:
        _require_admin_session(request)
        return list_training_activation_preflights(limit=limit)

    @app.get("/api/v20/admin/training/tasks/registry")
    def admin_training_task_registry(request: Request) -> dict[str, object]:
        _require_admin_session(request)
        return training_task_registry()

    @app.get("/api/v20/admin/runtime-consumption-audit")
    def admin_runtime_consumption_audit(request: Request) -> dict[str, object]:
        _require_admin_session(request)
        return build_runtime_consumption_audit()

    @app.get("/api/v20/admin/knowledge-completeness-audit")
    def admin_knowledge_completeness_audit(request: Request) -> dict[str, object]:
        _require_admin_session(request)
        return build_knowledge_completeness_audit()

    @app.get("/api/v20/admin/mainline-status")
    def admin_mainline_status(request: Request) -> dict[str, object]:
        _require_admin_session(request)
        return build_mainline_status()

    @app.get("/api/v20/admin/central-brain-architecture")
    def admin_central_brain_architecture(request: Request) -> dict[str, object]:
        _require_admin_session(request)
        return build_central_brain_architecture_status()

    @app.get("/api/v20/admin/training/tasks/{task_id}")
    def admin_training_task_status(task_id: str, request: Request) -> dict[str, object]:
        _require_admin_session(request)
        return read_training_task(task_id)

    @app.post("/api/v20/admin/training/tasks/start")
    def admin_training_task_start(payload: dict[str, object], request: Request) -> dict[str, object]:
        _require_admin_session(request)
        try:
            extra = payload.get("extra_args", ())
            extra_args = tuple(str(row) for row in extra) if isinstance(extra, list) else ()
            return start_training_task(
                str(payload.get("task_key") or ""),
                source_role="admin",
                extra_args=extra_args,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={"error": "V20_ADMIN_TRAINING_TASK_INVALID", "message": str(exc)}) from exc

    @app.post("/api/v20/admin/training/tasks/{task_id}/pause")
    def admin_training_task_pause(task_id: str, request: Request) -> dict[str, object]:
        _require_admin_session(request)
        return pause_training_task(task_id, source_role="admin")

    @app.post("/api/v20/admin/training/tasks/{task_id}/activate")
    def admin_training_task_activation_preflight(task_id: str, payload: dict[str, object], request: Request) -> dict[str, object]:
        _require_admin_session(request)
        try:
            return prepare_training_task_activation(
                task_id,
                dry_run=bool(payload.get("dry_run", True)),
                confirm_token=str(payload.get("confirm_token") or ""),
                reason=str(payload.get("reason") or ""),
                source_role="admin",
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={"error": "V20_ADMIN_TRAINING_ACTIVATION_INVALID", "message": str(exc)}) from exc

    @app.get("/api/v20/admin/policy-observability")
    def admin_policy_observability(request: Request) -> dict[str, object]:
        _require_admin_session(request)
        pointer = build_runtime_policy_pointer(brain_memory_signal={})
        report = build_policy_observability_training_report()
        question_source_graph = _question_source_graph_observability()
        return {
            "version": "v20.admin_policy_observability.v1",
            "status": "ready",
            "active_policy_version": pointer.get("active_policy_version", ""),
            "candidate_policy_version": pointer.get("candidate_policy_version", ""),
            "rollback_policy_version": pointer.get("rollback_policy_version", ""),
            "runtime_applied": pointer.get("runtime_applied", False),
            "fallback_active": not bool(pointer.get("runtime_applied", False)),
            "version_comparison": _policy_version_comparison(pointer, report),
            "pointer": pointer,
            "training_report": report,
            "question_source_graph": question_source_graph,
            "runtime_mutation": False,
            "guardrails": [
                "ADMIN_POLICY_OBSERVABILITY_READ_ONLY",
                "NO_POLICY_WRITE_FROM_ADMIN_PAGE",
                "NO_USER_TEXT_RENDERED",
                "ROLLBACK_POINTER_VISIBLE_TO_OPERATOR",
                "QUESTION_SOURCE_GRAPH_READ_ONLY",
            ],
        }

    @app.get("/api/v20/policy-observability")
    def policy_observability_readonly(request: Request) -> dict[str, object]:
        session = _require_policy_observer_session(request)
        pointer = build_runtime_policy_pointer(brain_memory_signal={})
        report = build_policy_observability_training_report()
        question_source_graph = _question_source_graph_observability()
        return {
            "version": "v20.policy_observability_readonly.v1",
            "status": "ready",
            "source_role": session.get("role", ""),
            "active_policy_version": pointer.get("active_policy_version", ""),
            "candidate_policy_version": pointer.get("candidate_policy_version", ""),
            "rollback_policy_version": pointer.get("rollback_policy_version", ""),
            "training_report": {
                "version": report.get("version", ""),
                "status": report.get("status", ""),
                "observation_count": report.get("observation_count", 0),
                "candidate_consumed_ratio": report.get("candidate_consumed_ratio", 0),
                "fallback_ratio": report.get("fallback_ratio", 0),
                "trend_summary": report.get("trend_summary", {}),
                "strategy_recommendations": report.get("strategy_recommendations", ()),
                "version_switch_timeline": report.get("version_switch_timeline", ()),
            },
            "question_source_graph": question_source_graph,
            "runtime_mutation": False,
            "guardrails": [
                "POLICY_OBSERVABILITY_READ_ONLY",
                "NO_ROLLBACK_OR_ACTIVATE_FROM_READONLY_ENDPOINT",
                "NO_USER_TEXT_RENDERED",
                "QUESTION_SOURCE_GRAPH_READ_ONLY",
            ],
        }

    @app.get("/api/v20/role-view/runtime-pointer")
    def role_view_runtime_pointer_readonly(request: Request) -> dict[str, object]:
        session = _require_policy_observer_session(request)
        pointer = build_role_view_runtime_pointer()
        return pointer | {
            "source_role": session.get("role", ""),
            "guardrails": [
                *tuple(pointer.get("guardrails", ())),
                "ROLE_VIEW_POINTER_READONLY_ENDPOINT",
                "NO_ACTIVATE_OR_ROLLBACK_FOR_ROLE_VIEW_POINTER",
            ],
        }

    @app.post("/api/v20/admin/role-view/runtime-pointer/activate-candidate")
    def admin_role_view_runtime_pointer_activate_candidate(payload: dict[str, object], request: Request) -> dict[str, object]:
        _require_admin_session(request)
        return write_role_view_runtime_pointer_activate_candidate(
            source_role="admin",
            reason=str((payload or {}).get("reason", "")),
        )

    @app.post("/api/v20/admin/role-view/runtime-pointer/rollback")
    def admin_role_view_runtime_pointer_rollback(payload: dict[str, object], request: Request) -> dict[str, object]:
        _require_admin_session(request)
        return write_role_view_runtime_pointer_rollback(
            source_role="admin",
            reason=str((payload or {}).get("reason", "")),
        )

    @app.post("/api/v20/admin/policy-observability/rollback")
    def admin_policy_observability_rollback(payload: dict[str, object], request: Request) -> dict[str, object]:
        _require_admin_session(request)
        return write_runtime_policy_rollback(
            source_role="admin",
            reason=str((payload or {}).get("reason", "")),
        )

    @app.post("/api/v20/admin/policy-observability/activate-latest")
    def admin_policy_observability_activate_latest(payload: dict[str, object], request: Request) -> dict[str, object]:
        _require_admin_session(request)
        return write_runtime_policy_activate_latest_candidate(
            source_role="admin",
            reason=str((payload or {}).get("reason", "")),
        )

    @app.post("/api/v20/admin/db/config")
    def admin_database_config(payload: dict[str, object], request: Request) -> dict[str, object]:
        _require_admin_session(request)
        try:
            return save_admin_database_config(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={"error": str(exc)}) from exc

    @app.post("/api/v20/admin/llm/config")
    def admin_llm_config(payload: dict[str, object], request: Request) -> dict[str, object]:
        _require_admin_session(request)
        try:
            return save_admin_llm_config(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={"error": str(exc)}) from exc

    @app.get("/api/v20/ops/config")
    def ops_config() -> dict[str, object]:
        config = load_runtime_config_from_env()
        return {
            "version": "v20.ops_config_response.v1",
            "config": config.to_dict(),
            "validation": validate_runtime_config(config),
            "runtime_mutation": False,
        }

    @app.get("/api/v20/ops/profile/{profile_name}")
    def ops_profile(profile_name: str) -> dict[str, object]:
        config = load_runtime_config_from_env()
        try:
            profile = config.profile(profile_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail={"error": "V20_PROFILE_NOT_FOUND", "profile": profile_name}) from exc
        return {
            "version": "v20.ops_profile_response.v1",
            "profile": profile.to_dict(),
            "runtime_mutation": False,
            "guardrails": ["NO_SECRET_VALUES_RENDERED", "PROFILE_RESPONSE_IS_CONFIG_ONLY"],
        }

    @app.get("/api/v20/ops/service-unit/{profile_name}")
    def ops_service_unit(profile_name: str) -> dict[str, object]:
        try:
            return service_unit_manifest(profile_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail={"error": "V20_PROFILE_NOT_FOUND", "profile": profile_name}) from exc

    @app.get("/api/v20/ops/sync-readiness")
    def ops_sync_readiness() -> dict[str, object]:
        return sync_readiness_report(load_runtime_config_from_env())

    @app.get("/api/v20/testing/tiers")
    def testing_tiers() -> dict[str, object]:
        manifest = test_tier_manifest()
        return {
            "version": "v20.testing_tiers_response.v1",
            "manifest": manifest,
            "runtime_mutation": False,
        }

    @app.get("/api/v20/testing/matrix")
    def testing_matrix() -> dict[str, object]:
        return build_test_coverage_matrix()

    @app.get("/api/v20/storage/schema")
    def storage_schema() -> dict[str, object]:
        return {
            "version": "v20.storage_schema_response.v1",
            "schema": build_postgres_schema_contract().to_dict(),
            "migration_manifest": migration_manifest(),
            "runtime_mutation": False,
        }

    @app.get("/api/v20/storage/local-jsonl")
    def storage_local_jsonl() -> dict[str, object]:
        return local_jsonl_store_from_env().status()

    @app.get("/api/v20/redis/contract")
    def redis_contract() -> dict[str, object]:
        contract = redis_contract_manifest()
        return {
            "version": "v20.redis_contract_response.v1",
            "contract": contract.to_dict(),
            "validation": validate_redis_contract(contract),
            "runtime_mutation": False,
        }

    @app.get("/api/v20/redis/cache-status")
    def redis_cache_status() -> dict[str, object]:
        return runtime_cache_status()

    @app.post("/api/v20/redis/cache-clear")
    def redis_cache_clear(request: Request) -> dict[str, object]:
        _require_admin_session(request)
        return clear_runtime_request_cache()

    @app.get("/api/v20/runtime/dependencies")
    def runtime_dependencies() -> dict[str, object]:
        return dependency_readiness_report()

    @app.get("/api/v20/access/roles")
    def access_roles() -> dict[str, object]:
        return access_role_manifest()

    @app.get("/api/v20/profiles")
    def profiles_list(request: Request, owner_id: str = "", limit: int = 80) -> dict[str, object]:
        session = _require_profile_session(request)
        target_owner = _profile_owner_for_session(session, owner_id)
        return list_profiles_from_postgres(owner_id=target_owner, limit=limit)

    @app.post("/api/v20/profiles")
    def profiles_create(payload: ProfileMutationRequest, request: Request) -> dict[str, object]:
        session = _require_profile_session(request)
        owner_id = _profile_owner_for_session(session, payload.owner_id)
        return create_profile_in_postgres(owner_id=owner_id, payload=payload.model_dump())

    @app.get("/api/v20/profiles/{profile_id}")
    def profiles_detail(profile_id: str, request: Request) -> dict[str, object]:
        session = _require_profile_session(request)
        result = read_profile_from_postgres(profile_id)
        if result.get("status") == "not_found":
            raise HTTPException(status_code=404, detail=result)
        profile = result.get("profile") if isinstance(result.get("profile"), dict) else {}
        if session.get("role") != "admin" and profile.get("owner_id") != session.get("user_id"):
            raise HTTPException(status_code=403, detail={"error": "V20_PROFILE_FORBIDDEN"})
        return result

    @app.patch("/api/v20/profiles/{profile_id}")
    def profiles_update(profile_id: str, payload: ProfileMutationRequest, request: Request) -> dict[str, object]:
        session = _require_profile_session(request)
        result = read_profile_from_postgres(profile_id)
        if result.get("status") == "not_found":
            raise HTTPException(status_code=404, detail=result)
        profile = result.get("profile") if isinstance(result.get("profile"), dict) else {}
        if session.get("role") != "admin" and profile.get("owner_id") != session.get("user_id"):
            raise HTTPException(status_code=403, detail={"error": "V20_PROFILE_FORBIDDEN"})
        owner_id = str(profile.get("owner_id") or _profile_owner_for_session(session, payload.owner_id))
        return update_profile_in_postgres(profile_id=profile_id, owner_id=owner_id, payload=payload.model_dump())

    @app.delete("/api/v20/profiles/{profile_id}")
    def profiles_delete(profile_id: str, request: Request) -> dict[str, object]:
        session = _require_profile_session(request)
        result = read_profile_from_postgres(profile_id)
        if result.get("status") == "not_found":
            raise HTTPException(status_code=404, detail=result)
        profile = result.get("profile") if isinstance(result.get("profile"), dict) else {}
        if session.get("role") != "admin" and profile.get("owner_id") != session.get("user_id"):
            raise HTTPException(status_code=403, detail={"error": "V20_PROFILE_FORBIDDEN"})
        return delete_profile_from_postgres(profile_id)

    @app.get("/api/v20/questions/ranking-policy")
    def question_ranking_policy() -> dict[str, object]:
        return question_ranking_manifest()

    @app.get("/api/v20/questions/seed-registry")
    def question_seed_registry() -> dict[str, object]:
        return question_seed_registry_manifest()

    @app.get("/api/v20/role-view/completion")
    def role_view_completion() -> dict[str, object]:
        return build_role_view_completion_report()

    @app.get("/api/v20/measurement/bazi-domain-alignment")
    def measurement_bazi_domain_alignment() -> dict[str, object]:
        return bazi_alignment_manifest()

    @app.get("/api/v20/measurement/dimensions")
    def measurement_dimensions() -> dict[str, object]:
        return bazi_dimension_manifest()

    @app.get("/api/v20/knowledge/retrieval-policy")
    def knowledge_retrieval_policy() -> dict[str, object]:
        return knowledge_retrieval_manifest()

    @app.get("/api/v20/knowledge/catalog")
    def knowledge_catalog() -> dict[str, object]:
        return build_knowledge_catalog()

    @app.get("/api/v20/knowledge/directory")
    def knowledge_directory() -> dict[str, object]:
        return build_knowledge_directory_manifest()

    @app.get("/api/v20/knowledge/directory-seeds")
    def knowledge_directory_seeds() -> dict[str, object]:
        return build_full_directory_seed_library()

    @app.get("/api/v20/knowledge/completion")
    def knowledge_completion() -> dict[str, object]:
        return build_knowledge_completion_report()

    @app.get("/api/v20/knowledge/completeness-audit")
    def knowledge_completeness_audit() -> dict[str, object]:
        return build_knowledge_completeness_audit()

    @app.get("/api/v20/knowledge/macro-dimensions")
    def knowledge_macro_dimensions() -> dict[str, object]:
        return build_macro_dimension_catalog()

    @app.get("/api/v20/knowledge/feature-graph-model")
    def knowledge_feature_graph_model() -> dict[str, object]:
        return build_bazi_feature_graph_model_contract()

    @app.get("/api/v20/knowledge/source-catalog")
    def knowledge_source_catalog() -> dict[str, object]:
        return build_knowledge_source_catalog()

    @app.get("/api/v20/knowledge/coverage-report")
    def knowledge_coverage_report() -> dict[str, object]:
        return build_knowledge_coverage_report()

    @app.get("/api/v20/knowledge/release-manifest")
    def knowledge_release_manifest() -> dict[str, object]:
        return build_knowledge_release_manifest()

    @app.get("/api/v20/knowledge/v19-migration-audit")
    def knowledge_v19_migration_audit() -> dict[str, object]:
        return build_v19_knowledge_migration_audit()

    @app.get("/api/v20/knowledge/draft-import-preview")
    def knowledge_draft_import_preview() -> dict[str, object]:
        return build_knowledge_draft_import_preview()

    @app.get("/api/v20/knowledge/review-queue")
    def knowledge_review_queue() -> dict[str, object]:
        return build_knowledge_review_queue()

    @app.get("/api/v20/knowledge/review-packet/{domain}")
    def knowledge_review_packet(domain: str) -> dict[str, object]:
        return build_knowledge_review_packet(domain)

    @app.get("/api/v20/knowledge/first-wave-review-packets")
    def knowledge_first_wave_review_packets() -> dict[str, object]:
        return build_first_wave_review_packets()

    @app.get("/api/v20/knowledge/approval-preflight/{domain}")
    def knowledge_approval_preflight(domain: str) -> dict[str, object]:
        return build_knowledge_approval_preflight(domain)

    @app.get("/api/v20/knowledge/first-wave-approval-preflight")
    def knowledge_first_wave_approval_preflight() -> dict[str, object]:
        return build_first_wave_approval_preflight()

    @app.get("/api/v20/knowledge/review-assist/{domain}")
    def knowledge_review_assist(domain: str) -> dict[str, object]:
        return build_knowledge_review_assist(domain)

    @app.get("/api/v20/knowledge/first-wave-review-assist")
    def knowledge_first_wave_review_assist() -> dict[str, object]:
        return build_first_wave_review_assist()

    @app.get("/api/v20/knowledge/rule-proposals/{domain}")
    def knowledge_rule_proposals(domain: str) -> dict[str, object]:
        return build_knowledge_rule_proposals(domain)

    @app.get("/api/v20/knowledge/first-wave-rule-proposals")
    def knowledge_first_wave_rule_proposals() -> dict[str, object]:
        return build_first_wave_rule_proposals()

    @app.get("/api/v20/knowledge/rule-proposal-preflight/{domain}")
    def knowledge_rule_proposal_preflight(domain: str) -> dict[str, object]:
        return build_rule_proposal_preflight(domain)

    @app.get("/api/v20/knowledge/first-wave-rule-proposal-preflight")
    def knowledge_first_wave_rule_proposal_preflight() -> dict[str, object]:
        return build_first_wave_rule_proposal_preflight()

    @app.get("/api/v20/knowledge/rule-extraction")
    def knowledge_rule_extraction() -> dict[str, object]:
        return build_rule_extraction_report()

    @app.get("/api/v20/knowledge/rule-extraction/{domain}")
    def knowledge_rule_extraction_domain(domain: str) -> dict[str, object]:
        return build_rule_extraction_report(domain)

    @app.get("/api/v20/knowledge/rule-extraction-validation")
    def knowledge_rule_extraction_validation() -> dict[str, object]:
        return validate_rule_extraction_report()

    @app.get("/api/v20/knowledge/rule-extraction-validation/{domain}")
    def knowledge_rule_extraction_validation_domain(domain: str) -> dict[str, object]:
        return validate_rule_extraction_report(domain)

    @app.get("/api/v20/knowledge/llm-rule-extraction")
    def knowledge_llm_rule_extraction() -> dict[str, object]:
        return build_llm_rule_extraction_report()

    @app.get("/api/v20/knowledge/llm-rule-extraction/{domain}")
    def knowledge_llm_rule_extraction_domain(domain: str) -> dict[str, object]:
        return build_llm_rule_extraction_report(domain)

    @app.get("/api/v20/knowledge/llm-rule-extraction-validation")
    def knowledge_llm_rule_extraction_validation() -> dict[str, object]:
        return validate_llm_rule_extraction_report()

    @app.get("/api/v20/knowledge/llm-rule-extraction-validation/{domain}")
    def knowledge_llm_rule_extraction_validation_domain(domain: str) -> dict[str, object]:
        return validate_llm_rule_extraction_report(domain)

    @app.get("/api/v20/knowledge/rule-library")
    def knowledge_rule_library(limit: int = 0) -> dict[str, object]:
        return build_knowledge_rule_library(limit=limit)

    @app.get("/api/v20/knowledge/rule-library/{domain}")
    def knowledge_rule_library_domain(domain: str, limit: int = 0) -> dict[str, object]:
        return build_knowledge_rule_library(domain, limit=limit)

    @app.get("/api/v20/knowledge/rule-library-validation")
    def knowledge_rule_library_validation(limit: int = 0) -> dict[str, object]:
        return validate_knowledge_rule_library(limit=limit)

    @app.get("/api/v20/knowledge/rule-library-validation/{domain}")
    def knowledge_rule_library_validation_domain(domain: str, limit: int = 0) -> dict[str, object]:
        return validate_knowledge_rule_library(domain, limit=limit)

    @app.get("/api/v20/knowledge/rule-review-overlay")
    def knowledge_rule_review_overlay() -> dict[str, object]:
        return build_knowledge_rule_review_overlay()

    @app.get("/api/v20/rules/catalog")
    def rules_catalog() -> dict[str, object]:
        return build_bazi_rule_catalog()

    @app.get("/api/v20/features/confidence-calibration")
    def feature_confidence_calibration() -> dict[str, object]:
        return confidence_calibration_manifest()

    @app.get("/api/v20/learning/latent-factor-calibration")
    def learning_latent_factor_calibration() -> dict[str, object]:
        return latent_factor_calibration_manifest()

    @app.get("/api/v20/learning/latent-event-calibration")
    def learning_latent_event_calibration() -> dict[str, object]:
        return latent_event_calibration_manifest()

    @app.get("/api/v20/portrait/ontology")
    def portrait_ontology() -> dict[str, object]:
        return portrait_ontology_manifest()

    @app.get("/api/v20/corpus/coverage")
    def corpus_coverage() -> dict[str, object]:
        return {
            "version": "v20.corpus_coverage_response.v1",
            "plan": build_corpus_coverage_plan().to_dict(),
            "runtime_mutation": False,
        }

    @app.get("/api/v20/corpus/full-precompute/manifest")
    def corpus_full_precompute_manifest() -> dict[str, object]:
        return build_full_precompute_manifest()

    @app.get("/api/v20/corpus/full-precompute/preview")
    def corpus_full_precompute_preview(start: int = 0, limit: int = 4) -> dict[str, object]:
        try:
            return preview_full_precompute_batch(start=start, limit=limit)
        except (IndexError, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_CORPUS_PRECOMPUTE_INPUT_INVALID", "message": str(exc)},
            ) from exc

    @app.get("/api/v20/corpus/full-precompute/status")
    def corpus_full_precompute_status(run_id: str = "") -> dict[str, object]:
        return read_full_precompute_status(run_id)

    @app.get("/api/v20/corpus/artifacts/status")
    def corpus_artifact_status(run_id: str = "") -> dict[str, object]:
        return read_corpus_artifact_status(run_id)

    @app.get("/api/v20/corpus/artifacts/coverage-summary")
    def corpus_artifact_coverage_summary(run_id: str = "") -> dict[str, object]:
        return read_corpus_coverage_summary(run_id)

    @app.get("/api/v20/corpus/artifacts/cluster-model")
    def corpus_artifact_cluster_model(run_id: str = "") -> dict[str, object]:
        return read_corpus_cluster_model(run_id)

    @app.get("/api/v20/corpus/artifacts/training")
    def corpus_artifact_training(run_id: str = "") -> dict[str, object]:
        return read_corpus_training_artifacts(run_id)

    @app.get("/api/v20/corpus/similar")
    def corpus_similar(case_id: str, run_id: str = "", limit: int = 8) -> dict[str, object]:
        return find_similar_cases(case_id, run_id=run_id, limit=limit)

    @app.get("/api/v20/validation/synthetic-suite")
    def synthetic_suite() -> dict[str, object]:
        return run_synthetic_suite()

    @app.get("/api/v20/validation/rule-synthetic-suite")
    def rule_synthetic_suite() -> dict[str, object]:
        return run_rule_synthetic_suite()

    @app.get("/api/v20/validation/rule-portrait-batch")
    def rule_portrait_batch() -> dict[str, object]:
        return run_rule_portrait_batch()

    @app.get("/api/v20/validation/knowledge-rule-library")
    def knowledge_rule_library_validation_report(limit: int = 0) -> dict[str, object]:
        return build_knowledge_rule_validation_report(limit=limit)

    @app.get("/api/v20/validation/knowledge-rule-library/{domain}")
    def knowledge_rule_library_validation_report_domain(domain: str, limit: int = 0) -> dict[str, object]:
        return build_knowledge_rule_validation_report(domain, limit=limit)

    @app.get("/api/v20/learning/evolution-plan")
    def evolution_plan() -> dict[str, object]:
        return build_evolution_dry_run_plan()

    @app.get("/api/v20/learning/run-plan")
    def learning_run_plan() -> dict[str, object]:
        return build_learning_run_plan()

    @app.get("/api/v20/learning/orchestrator/run-plan")
    def learning_orchestrator_run_plan(job: str = "nightly") -> dict[str, object]:
        return build_learning_orchestrator_run_plan(job)

    @app.get("/api/v20/learning/orchestrator/knowledge-rule-plan")
    def learning_orchestrator_knowledge_rule_plan(
        limit_per_domain: int = 2,
        synthetic_case_limit: int = 4,
        overlay_limit: int = 12,
    ) -> dict[str, object]:
        return build_knowledge_rule_orchestrator_plan(
            limit_per_domain=max(1, limit_per_domain),
            synthetic_case_limit=max(0, synthetic_case_limit),
            overlay_limit=max(0, overlay_limit),
        )

    @app.get("/api/v20/learning/orchestrator/nightly-executor/status")
    def learning_orchestrator_nightly_executor_status(run_id: str = "") -> dict[str, object]:
        return read_nightly_executor_status(run_id)

    @app.get("/api/v20/learning/rule-synthetic-training")
    def learning_rule_synthetic_training(status: bool = False) -> dict[str, object]:
        if status:
            return read_rule_synthetic_training_artifact()
        return build_rule_synthetic_training_report()

    @app.get("/api/v20/learning/rule-portrait-batch")
    def learning_rule_portrait_batch(status: bool = False) -> dict[str, object]:
        if status:
            return read_rule_portrait_batch_artifact()
        return run_rule_portrait_batch()

    @app.get("/api/v20/learning/registries")
    def learning_registries() -> dict[str, object]:
        return registry_manifest()

    @app.get("/api/v20/learning/rule-activation")
    def learning_rule_activation(limit: int = 0) -> dict[str, object]:
        return build_rule_activation_report(limit=limit)

    @app.get("/api/v20/learning/rule-activation/{domain}")
    def learning_rule_activation_domain(domain: str, limit: int = 0) -> dict[str, object]:
        return build_rule_activation_report(domain, limit=limit)

    @app.get("/api/v20/learning/rule-activation-packets")
    def learning_rule_activation_packets(limit: int = 0) -> dict[str, object]:
        return build_rule_activation_packet_summary(limit=limit)

    @app.get("/api/v20/learning/rule-activation-packets/{domain}")
    def learning_rule_activation_packets_domain(domain: str, limit: int = 0) -> dict[str, object]:
        return build_rule_activation_packet_summary(domain, limit=limit)

    @app.get("/api/v20/learning/rule-subcondition-split")
    def learning_rule_subcondition_split(limit: int = 0, per_rule: int = 0, status: bool = False) -> dict[str, object]:
        if status:
            return read_rule_subcondition_split_artifact()
        return build_rule_subcondition_split_report(limit=limit, per_rule=per_rule)

    @app.get("/api/v20/learning/rule-subcondition-split/{domain}")
    def learning_rule_subcondition_split_domain(domain: str, limit: int = 0, per_rule: int = 0) -> dict[str, object]:
        return build_rule_subcondition_split_report(domain, limit=limit, per_rule=per_rule)

    @app.get("/api/v20/learning/rule-replay-eval")
    def learning_rule_replay_eval(limit: int = 0, per_rule: int = 0, status: bool = False) -> dict[str, object]:
        if status:
            return read_rule_replay_eval_artifact()
        return build_rule_replay_eval_report(limit=limit, per_rule=per_rule)

    @app.get("/api/v20/learning/rule-replay-eval/{domain}")
    def learning_rule_replay_eval_domain(domain: str, limit: int = 0, per_rule: int = 0) -> dict[str, object]:
        return build_rule_replay_eval_report(domain, limit=limit, per_rule=per_rule)

    @app.get("/api/v20/learning/question-ranking")
    def learning_question_ranking(status: bool = False) -> dict[str, object]:
        if status:
            return read_question_ranking_learning_artifact()
        return build_question_ranking_learning_report()

    @app.get("/api/v20/learning/question-dag")
    def learning_question_dag() -> dict[str, object]:
        review_report = build_question_review_training_report()
        return build_question_dag_training_report(question_review_training_report=review_report)

    @app.get("/api/v20/learning/question-dag-replay")
    def learning_question_dag_replay(status: bool = False) -> dict[str, object]:
        if status:
            return read_question_dag_policy_replay_artifact()
        review_report = build_question_review_training_report()
        dag_report = build_question_dag_training_report(question_review_training_report=review_report)
        return build_question_dag_policy_replay_report(question_dag_training_report=dag_report)

    @app.get("/api/v20/learning/question-dag-promotion")
    def learning_question_dag_promotion() -> dict[str, object]:
        review_report = build_question_review_training_report()
        dag_report = build_question_dag_training_report(question_review_training_report=review_report)
        replay_report = build_question_dag_policy_replay_report(question_dag_training_report=dag_report)
        return build_question_dag_policy_promotion_gate(replay_report=replay_report)

    @app.get("/api/v20/learning/question-review")
    def learning_question_review(status: bool = False) -> dict[str, object]:
        if status:
            return read_question_review_training_artifact()
        return build_question_review_training_report()

    @app.get("/api/v20/learning/role-question-click")
    def learning_role_question_click(status: bool = False) -> dict[str, object]:
        if status:
            return read_role_question_click_training_artifact()
        return build_role_question_click_training_report()

    @app.get("/api/v20/learning/role-view-policy-candidates")
    def learning_role_view_policy_candidates(status: bool = False) -> dict[str, object]:
        if status:
            return read_role_view_policy_candidate_artifact()
        return build_role_view_policy_candidate_report()

    @app.get("/api/v20/learning/role-view-policy-replay")
    def learning_role_view_policy_replay(status: bool = False) -> dict[str, object]:
        if status:
            return read_role_view_policy_replay_artifact()
        return build_role_view_policy_replay_report()

    @app.get("/api/v20/learning/decision-registry-iteration")
    def learning_decision_registry_iteration(limit: int = 0, per_rule: int = 0, status: bool = False) -> dict[str, object]:
        if status:
            return read_decision_registry_iteration_artifact()
        return build_decision_registry_iteration_report(limit=limit, per_rule=per_rule)

    @app.get("/api/v20/learning/decision-registry-iteration/{domain}")
    def learning_decision_registry_iteration_domain(domain: str, limit: int = 0, per_rule: int = 0) -> dict[str, object]:
        return build_decision_registry_iteration_report(domain, limit=limit, per_rule=per_rule)

    @app.get("/api/v20/intelligence/generation-manifest")
    def intelligence_generation_manifest() -> dict[str, object]:
        return build_intelligence_generation_manifest()

    @app.get("/api/v20/intelligence/knowledge-semantic-model")
    def intelligence_knowledge_semantic_model() -> dict[str, object]:
        return build_knowledge_semantic_model()

    @app.get("/api/v20/validation/intelligence-generation")
    def intelligence_generation_validation() -> dict[str, object]:
        return validate_intelligence_generation()

    @app.get("/api/v20/validation/knowledge-semantic-model")
    def intelligence_knowledge_semantic_model_validation() -> dict[str, object]:
        return validate_knowledge_semantic_model(build_knowledge_semantic_model())

    @app.post("/api/v20/feedback/analyze")
    def feedback_analyze(payload: FeedbackRequest) -> dict[str, object]:
        return analyze_feedback(
            input_id=payload.input_id,
            source_role=payload.source_role,
            feedback_text=payload.feedback_text,
            feature_ids=tuple(payload.feature_ids),
            locale=payload.locale,
        )

    @app.post("/api/v20/feedback/record")
    def feedback_record(payload: FeedbackRequest) -> dict[str, object]:
        return record_feedback_analysis(
            input_id=payload.input_id,
            source_role=payload.source_role,
            feedback_text=payload.feedback_text,
            feature_ids=tuple(payload.feature_ids),
            locale=payload.locale,
        )

    @app.post("/api/v20/role-view/question-click/analyze")
    def role_question_click_analyze(payload: RoleQuestionClickRequest) -> dict[str, object]:
        try:
            return analyze_role_question_click(
                input_id=payload.input_id,
                source_role=payload.source_role,
                question=payload.question,
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={"error": "V20_ROLE_QUESTION_CLICK_INVALID", "message": str(exc)}) from exc

    @app.post("/api/v20/role-view/question-click/record")
    def role_question_click_record(payload: RoleQuestionClickRequest) -> dict[str, object]:
        try:
            return record_role_question_click(
                input_id=payload.input_id,
                source_role=payload.source_role,
                question=payload.question,
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={"error": "V20_ROLE_QUESTION_CLICK_INVALID", "message": str(exc)}) from exc

    @app.post("/api/v20/question-review/analyze")
    def question_review_analyze(payload: QuestionReviewRequest) -> dict[str, object]:
        try:
            return analyze_question_review(
                input_id=payload.input_id,
                source_role=payload.source_role,
                question=payload.question,
                action=payload.action,
                reason=payload.reason,
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={"error": "V20_QUESTION_REVIEW_INVALID", "message": str(exc)}) from exc

    @app.post("/api/v20/question-review/record")
    def question_review_record(payload: QuestionReviewRequest) -> dict[str, object]:
        try:
            return record_question_review(
                input_id=payload.input_id,
                source_role=payload.source_role,
                question=payload.question,
                action=payload.action,
                reason=payload.reason,
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={"error": "V20_QUESTION_REVIEW_INVALID", "message": str(exc)}) from exc

    @app.post("/api/v20/question-source-ranking/analyze")
    def question_source_ranking_analyze(payload: QuestionSourceRankingRecordRequest) -> dict[str, object]:
        try:
            return analyze_question_source_ranking_report(
                input_id=payload.input_id,
                source_role=payload.source_role,
                question_source_ranking_report=payload.question_source_ranking_report,
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_QUESTION_SOURCE_RANKING_ANALYZE_INVALID", "message": str(exc)},
            ) from exc

    @app.post("/api/v20/question-source-ranking/record")
    def question_source_ranking_record(payload: QuestionSourceRankingRecordRequest) -> dict[str, object]:
        try:
            return record_question_source_ranking_report(
                input_id=payload.input_id,
                source_role=payload.source_role,
                question_source_ranking_report=payload.question_source_ranking_report,
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_QUESTION_SOURCE_RANKING_RECORD_INVALID", "message": str(exc)},
            ) from exc

    @app.post("/api/v20/portrait/calibration/analyze")
    def portrait_calibration_analyze(payload: PortraitCalibrationRequest) -> dict[str, object]:
        try:
            return analyze_portrait_calibration(
                input_id=payload.input_id,
                feature_id=payload.feature_id,
                source_role=payload.source_role,
                signal=payload.signal,
                note=payload.note,
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={"error": "V20_PORTRAIT_CALIBRATION_INVALID", "message": str(exc)}) from exc

    @app.post("/api/v20/portrait/calibration/record")
    def portrait_calibration_record(payload: PortraitCalibrationRequest) -> dict[str, object]:
        try:
            return record_portrait_calibration(
                input_id=payload.input_id,
                feature_id=payload.feature_id,
                source_role=payload.source_role,
                signal=payload.signal,
                note=payload.note,
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={"error": "V20_PORTRAIT_CALIBRATION_INVALID", "message": str(exc)}) from exc

    @app.post("/api/v20/practitioner/calibration/analyze")
    def practitioner_calibration_analyze(payload: PractitionerCalibrationRequest) -> dict[str, object]:
        try:
            return analyze_practitioner_calibration(
                input_id=payload.input_id,
                source_role=payload.source_role,
                selections=_practitioner_selections_from_payload(payload),
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_PRACTITIONER_CALIBRATION_INVALID", "message": str(exc)},
            ) from exc

    @app.post("/api/v20/practitioner/calibration/record")
    def practitioner_calibration_record(payload: PractitionerCalibrationRequest) -> dict[str, object]:
        try:
            return record_practitioner_calibration(
                input_id=payload.input_id,
                source_role=payload.source_role,
                selections=_practitioner_selections_from_payload(payload),
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_PRACTITIONER_CALIBRATION_INVALID", "message": str(exc)},
            ) from exc

    @app.post("/api/v20/latent-event/calibration/analyze")
    def latent_event_calibration_analyze(payload: LatentEventCalibrationRequest) -> dict[str, object]:
        try:
            return analyze_latent_event_calibration(
                input_id=payload.input_id,
                source_role=payload.source_role,
                answers=_latent_event_answers_from_payload(payload),
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_LATENT_EVENT_CALIBRATION_INVALID", "message": str(exc)},
            ) from exc

    @app.post("/api/v20/latent-event/calibration/record")
    def latent_event_calibration_record(payload: LatentEventCalibrationRequest) -> dict[str, object]:
        try:
            return record_latent_event_calibration(
                input_id=payload.input_id,
                source_role=payload.source_role,
                answers=_latent_event_answers_from_payload(payload),
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_LATENT_EVENT_CALIBRATION_INVALID", "message": str(exc)},
            ) from exc

    @app.post("/api/v20/orchestrator/memory/analyze")
    def orchestrator_memory_analyze(payload: OrchestratorMemoryRecordRequest) -> dict[str, object]:
        try:
            return analyze_orchestrator_memory_signal(
                input_id=payload.input_id,
                source_role=payload.source_role,
                brain_memory_signal=payload.brain_memory_signal,
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_ORCHESTRATOR_MEMORY_INVALID", "message": str(exc)},
            ) from exc

    @app.post("/api/v20/orchestrator/memory/record")
    def orchestrator_memory_record(payload: OrchestratorMemoryRecordRequest) -> dict[str, object]:
        try:
            return record_orchestrator_memory_signal(
                input_id=payload.input_id,
                source_role=payload.source_role,
                brain_memory_signal=payload.brain_memory_signal,
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_ORCHESTRATOR_MEMORY_INVALID", "message": str(exc)},
            ) from exc

    def _resolved_measure_inputs(payload: MeasureRequest) -> tuple[dict[str, str], str]:
        pillars = resolve_pillars(
            payload.year,
            payload.month,
            payload.day,
            payload.hour,
            calendar=payload.calendar,
            gender=payload.gender,
            lunar_is_leap=payload.lunar_is_leap,
        )
        luck_pillar = payload.luck_pillar
        if not luck_pillar and payload.flow_year_pillar:
            luck_pillar = resolve_luck_pillar(
                payload.year,
                payload.month,
                payload.day,
                payload.hour,
                calendar=payload.calendar,
                gender=payload.gender,
                lunar_is_leap=payload.lunar_is_leap,
                target_year=resolve_target_year(payload.flow_year_pillar),
            )
        return pillars, luck_pillar

    @app.post("/api/v20/measure/preview")
    def measure_preview(payload: MeasureRequest, request: Request) -> dict[str, object]:
        _enforce_rate_limit("measure.preview", request)
        try:
            pillars, luck_pillar = _resolved_measure_inputs(payload)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_MEASURE_PREVIEW_INPUT_INVALID", "message": str(exc)},
            ) from exc
        time_layers = []
        if luck_pillar:
            time_layers.append({"layer_key": "luck", "pillar": _pillar_preview(luck_pillar)})
        if payload.flow_year_pillar:
            time_layers.append({"layer_key": "flow_year", "pillar": _pillar_preview(payload.flow_year_pillar)})
        if payload.flow_month_pillar:
            time_layers.append({"layer_key": "flow_month", "pillar": _pillar_preview(payload.flow_month_pillar)})
        return {
            "version": "v20.measure_preview.v1",
            "chart_facts": {
                "pillars": {key: _pillar_preview(value) for key, value in pillars.items()},
                "day_master": str(pillars.get("day", ""))[:1],
            },
            "time_context": {"layers": time_layers},
            "runtime_mutation": False,
            "guardrails": [
                "PREVIEW_ONLY_NO_RULE_DECISION",
                "NO_LLM_CALL",
                "NO_STORAGE_MUTATION",
            ],
        }

    @app.post("/api/v20/measure")
    @app.post("/api/v20/runtime/measure")
    def measure(payload: MeasureRequest, request: Request) -> dict[str, object]:
        _enforce_rate_limit("runtime.measure", request)
        source_role = _measure_source_role(payload, request)
        try:
            pillars, luck_pillar = _resolved_measure_inputs(payload)
            if should_cache_measure(payload):
                cache_key = runtime_cache_key(cacheable_measure_payload(payload, pillars=pillars, luck_pillar=luck_pillar), role_key="raw")
                cached = get_runtime_cache(cache_key)
                if cached is not None:
                    return cached
            else:
                cache_key = ""

            result = run_runtime_from_pillars(
                pillars["year"], pillars["month"], pillars["day"], pillars["hour"],
                input_id=payload.input_id,
                question_key=payload.question_key,
                question_id=payload.question_id,
                user_text=payload.user_text,
                flow_year_pillar=payload.flow_year_pillar,
                luck_pillar=luck_pillar,
                flow_month_pillar=payload.flow_month_pillar,
                locale=payload.locale,
                llm_mode=payload.llm_mode,
                source_role=source_role,
                record_question_source_report=True,
                practitioner_selections=tuple(selection.model_dump() for selection in payload.practitioner_selections),
                latent_event_answers=tuple(answer.model_dump() for answer in payload.latent_event_answers),
                answered_question_ids=tuple(payload.answered_question_ids),
                answered_question_keys=tuple(payload.answered_question_keys),
            )
            if should_cache_measure(payload):
                attach_cache_miss_meta(result, cache_key, stored=set_runtime_cache(cache_key, result))
            return result
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_MEASURE_INPUT_INVALID", "message": str(exc)},
            ) from exc

    @app.post("/api/v20/measure/view/{role_key}")
    def measure_view(role_key: str, payload: MeasureRequest, request: Request) -> dict[str, object]:
        if role_key == "admin":
            _require_admin_session(request)
        _enforce_rate_limit(f"measure.view.{role_key}", request)
        source_role = _measure_source_role(payload, request, role_key=role_key)
        try:
            pillars, luck_pillar = _resolved_measure_inputs(payload)
            if should_cache_measure(payload):
                cache_key = runtime_cache_key(cacheable_measure_payload(payload, pillars=pillars, luck_pillar=luck_pillar), role_key=role_key)
                cached = get_runtime_cache(cache_key)
                if cached is not None:
                    if cached.get("version") == "v20.role_runtime_view.v1":
                        return cached
                    return project_runtime_for_role(cached, role_key)
            else:
                cache_key = ""

            result = run_runtime_from_pillars(
                pillars["year"], pillars["month"], pillars["day"], pillars["hour"],
                input_id=payload.input_id,
                question_key=payload.question_key,
                question_id=payload.question_id,
                user_text=payload.user_text,
                flow_year_pillar=payload.flow_year_pillar,
                luck_pillar=luck_pillar,
                flow_month_pillar=payload.flow_month_pillar,
                locale=payload.locale,
                llm_mode=payload.llm_mode,
                source_role=source_role,
                record_question_source_report=True,
                practitioner_selections=tuple(selection.model_dump() for selection in payload.practitioner_selections),
                latent_event_answers=tuple(answer.model_dump() for answer in payload.latent_event_answers),
                answered_question_ids=tuple(payload.answered_question_ids),
                answered_question_keys=tuple(payload.answered_question_keys),
            )
            projected = project_runtime_for_role(result, role_key)
            if should_cache_measure(payload):
                attach_cache_miss_meta(projected, cache_key, stored=set_runtime_cache(cache_key, projected))
            return projected
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_ROLE_MEASURE_INPUT_INVALID", "message": str(exc)},
            ) from exc

    @app.post("/api/v20/measure/view/{role_key}/stream")
    def measure_view_stream(role_key: str, payload: MeasureRequest, request: Request) -> StreamingResponse:
        if role_key == "admin":
            _require_admin_session(request)
        _enforce_rate_limit(f"measure.stream.{role_key}", request)
        source_role = _measure_source_role(payload, request, role_key=role_key)

        def event_stream():
            try:
                pillars, luck_pillar = _resolved_measure_inputs(payload)
                runtime_cache_payload = cacheable_measure_payload(payload, pillars=pillars, luck_pillar=luck_pillar)
                runtime_cache_key_raw = runtime_cache_key(runtime_cache_payload, role_key="raw")
                cached_runtime = get_runtime_cache(runtime_cache_key_raw)

                if cached_runtime is not None:
                    result = cached_runtime
                else:
                    result = run_runtime_from_pillars(
                        pillars["year"], pillars["month"], pillars["day"], pillars["hour"],
                        input_id=payload.input_id,
                        question_key=payload.question_key,
                        question_id=payload.question_id,
                        user_text=payload.user_text,
                        flow_year_pillar=payload.flow_year_pillar,
                        luck_pillar=luck_pillar,
                        flow_month_pillar=payload.flow_month_pillar,
                        locale=payload.locale,
                        llm_mode="deterministic",
                        source_role=source_role,
                        record_question_source_report=True,
                        practitioner_selections=tuple(selection.model_dump() for selection in payload.practitioner_selections),
                        latent_event_answers=tuple(answer.model_dump() for answer in payload.latent_event_answers),
                        answered_question_ids=tuple(payload.answered_question_ids),
                        answered_question_keys=tuple(payload.answered_question_keys),
                    )
                    attach_cache_miss_meta(
                        result,
                        runtime_cache_key_raw,
                        stored=set_runtime_cache(runtime_cache_key_raw, result),
                    )
                projected = project_runtime_for_role(result, role_key)
                yield _sse("runtime", {"result": projected})

                chunks: list[str] = []
                decision_report = result.get("decision_report", {})
                if not isinstance(decision_report, dict):
                    decision_report = {}
                for chunk in stream_practitioner_answer_with_llm(
                    chart_facts=_dict_value(result, "chart_facts"),
                    time_context=_dict_value(result, "time_context"),
                    selected_question=_dict_value(result, "selected_question"),
                    decision_report=decision_report,
                    knowledge_semantic_model=_dict_value(result, "knowledge_semantic_model"),
                    portrait_projection=_dict_value(decision_report, "portrait_projection"),
                    feature_state_model=_dict_value(result, "feature_state_model"),
                    question_intent_model=_dict_value(result, "question_intent_model"),
                    interaction_session=_dict_value(result, "interaction_session"),
                    mainline_arbitration=_dict_value(result, "mainline_arbitration"),
                    answer_plan=result.get("answer_plan", {}),
                    deterministic_answer_text=str(result.get("answer_text") or ""),
                    locale=payload.locale,
                ):
                    text = str(chunk)
                    chunks.append(text)
                answer_text = unwrap_practitioner_text("".join(chunks)) or str(result.get("answer_text") or "")
                chart_facts = _dict_value(result, "chart_facts")
                day_master_validation = validate_practitioner_answer_day_master(
                    answer_text,
                    str(chart_facts.get("day_master", "")),
                )
                if not day_master_validation.get("ok"):
                    answer_text = str(result.get("answer_text") or "")
                if answer_text:
                    yield _sse("delta", {"text": answer_text})
                role_answer = _stream_role_answer_payload(answer_text, role_key, projected)
                yield _sse("done", role_answer | {"status": "ok", "day_master_validation": day_master_validation})
            except Exception as exc:
                yield _sse("error", {"message": str(exc), "status": "error"})

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    return app


app = create_app()


def _sse(event: str, payload: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _stream_role_answer_payload(answer_text: str, role_key: str, projected_runtime: dict[str, object]) -> dict[str, object]:
    role_projected = apply_role_answer_view(
        {"answer_text": answer_text},
        role_key,
        _dict_value(projected_runtime, "role_view_model"),
        source_answer="stream_practitioner_answer_text",
    )
    final_text = str(role_projected.get("answer_text", answer_text))
    quality = evaluate_answer_governance_quality(final_text)
    _record_stream_answer_quality(
        role_key=role_key,
        projected_runtime=projected_runtime,
        quality=quality,
    )
    return {
        "answer_text": final_text,
        "role_answer_profile": _dict_value(role_projected, "role_answer_profile"),
        "answer_governance_quality": quality,
    }


def _record_stream_answer_quality(
    *,
    role_key: str,
    projected_runtime: dict[str, object],
    quality: dict[str, object],
) -> dict[str, object]:
    try:
        return local_jsonl_store_from_env().append_record(
            "llm_stream_answer_quality",
            {
                "version": "v20.llm_stream_answer_quality_signal.v1",
                "role_key": str(role_key or ""),
                "input_id_hash": _short_hash(str(projected_runtime.get("input_id", ""))),
                "selected_question_key": str(_dict_value(projected_runtime, "selected_question").get("question_key", "")),
                "quality_score": float(quality.get("quality_score", 0.0) or 0.0),
                "quality_band": str(quality.get("quality_band", "")),
                "dimensions": quality.get("dimensions", {}) if isinstance(quality.get("dimensions", {}), dict) else {},
                "findings": tuple(str(item) for item in quality.get("findings", ()) if str(item)),
                "context_budget": _dict_value(projected_runtime, "llm_context_budget"),
                "runtime_mutation": False,
                "guardrails": [
                    "STREAM_QUALITY_SIGNAL_ONLY",
                    "NO_RAW_ANSWER_TEXT_STORED",
                    "TRAINING_CAN_CONSUME_WITHOUT_HUMAN_REVIEW",
                ],
            },
        )
    except Exception:
        return {
            "version": "v20.llm_stream_answer_quality_signal_write.v1",
            "status": "skipped",
            "runtime_mutation": False,
        }


def _dict_value(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key, {})
    return value if isinstance(value, dict) else {}


def _short_hash(value: str) -> str:
    if not value:
        return ""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _client_host(request: Request) -> str:
    if request.client is None:
        return ""
    return str(request.client.host or "")


def _require_profile_session(request: Request) -> dict[str, object]:
    auth = auth_status(request)
    if not auth.get("authenticated"):
        raise HTTPException(status_code=401, detail={"error": "V20_AUTH_REQUIRED"})
    return dict(auth.get("session") or {})


def _require_admin_session(request: Request) -> dict[str, object]:
    session = _require_profile_session(request)
    if session.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"error": "V20_ADMIN_REQUIRED"})
    return session


def _require_policy_observer_session(request: Request) -> dict[str, object]:
    session = _require_profile_session(request)
    if session.get("role") not in {"admin", "analyst"}:
        raise HTTPException(status_code=403, detail={"error": "V20_POLICY_OBSERVER_REQUIRED"})
    return session


def _measure_source_role(
    payload: MeasureRequest,
    request: Request,
    *,
    role_key: str | None = None,
) -> str:
    valid_roles = ("guest", "user", "analyst", "admin", "lab", "practitioner")
    if role_key in valid_roles:
        # 明确按页面角色视图归一化来源角色，不让前端字段随意越权
        return role_key

    auth = auth_status(request)
    if auth.get("authenticated"):
        session = auth.get("session") or {}
        role = str(session.get("role", "user"))
        if role in valid_roles:
            return role

    source_role = str(payload.source_role)
    return source_role if source_role in valid_roles else "user"


def _policy_version_comparison(pointer: dict[str, object], report: dict[str, object]) -> dict[str, object]:
    active = str(pointer.get("active_policy_version", ""))
    candidate = str(pointer.get("candidate_policy_version", ""))
    rollback = str(pointer.get("rollback_policy_version", ""))
    version_counts = report.get("active_policy_version_counts", {}) if isinstance(report, dict) else {}
    return {
        "version": "v20.admin_policy_version_comparison.v1",
        "active_policy_version": active,
        "candidate_policy_version": candidate,
        "rollback_policy_version": rollback,
        "active_equals_candidate": bool(candidate and active == candidate),
        "active_equals_rollback": bool(rollback and active == rollback),
        "active_observation_count": int(version_counts.get(active, 0) or 0) if isinstance(version_counts, dict) else 0,
        "candidate_observation_count": int(version_counts.get(candidate, 0) or 0) if isinstance(version_counts, dict) and candidate else 0,
        "rollback_observation_count": int(version_counts.get(rollback, 0) or 0) if isinstance(version_counts, dict) and rollback else 0,
        "runtime_mutation": False,
        "guardrails": [
            "VERSION_COMPARISON_READ_ONLY",
            "NO_POLICY_WRITE_FROM_COMPARISON",
            "ROLLBACK_TARGET_VISIBLE",
        ],
    }


def _question_source_graph_observability() -> dict[str, object]:
    quality_artifact = read_orchestrator_policy_candidate_artifact()
    quality_signal = quality_artifact if quality_artifact.get("status") not in {"", "not_built"} else {}
    graph = arbitrate_question_source_paths(quality_signal=quality_signal)
    guardrails = tuple(graph.get("guardrails", ()))
    return graph | {
        "source_quality_artifact_status": quality_artifact.get("status", "not_built"),
        "runtime_mutation": False,
        "guardrails": guardrails + (
            "QUESTION_SOURCE_GRAPH_OBSERVABILITY_READ_ONLY",
            "NO_ADMIN_WRITE_FROM_SOURCE_GRAPH",
        ),
    }


def _enforce_rate_limit(route_key: str, request: Request | None) -> None:
    identity = "anonymous"
    if request is not None:
        auth = auth_status(request)
        session = auth.get("session", {}) if auth.get("authenticated") else {}
        if isinstance(session, dict):
            identity = str(session.get("user_id") or session.get("username") or "anonymous")
        if identity == "anonymous" and request.client is not None:
            identity = str(request.client.host or "anonymous")
    result = check_rate_limit(identity, route_key=route_key, limit=_rate_limit_for_route(route_key))
    if not result.get("allowed", True):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "V20_RATE_LIMITED",
                "route_key": route_key,
                "retry_after_seconds": result.get("retry_after_seconds", 60),
                "guardrails": result.get("guardrails", []),
            },
        )


def _rate_limit_for_route(route_key: str) -> int:
    if ".stream." in route_key:
        return _int_env("V20_STREAM_RATE_LIMIT_PER_MINUTE", 12)
    return _int_env("V20_RATE_LIMIT_PER_MINUTE", 60)


def _int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return max(1, value)


def _pillar_preview(value: str) -> dict[str, str]:
    text = str(value or "").strip()
    if len(text) < 2:
        return {"stem": "", "branch": "", "label": text}
    return {"stem": text[:1], "branch": text[1:2], "label": text[:2]}


def _profile_owner_for_session(session: dict[str, object], owner_id: str) -> str:
    role = str(session.get("role") or "user")
    user_id = str(session.get("user_id") or "")
    requested_owner = str(owner_id or "").strip()
    if role == "admin":
        return requested_owner or "admin"
    if requested_owner and requested_owner != user_id:
        raise HTTPException(status_code=403, detail={"error": "V20_PROFILE_OWNER_FORBIDDEN"})
    return user_id


def _practitioner_selections_from_payload(
    payload: PractitionerCalibrationRequest,
) -> tuple[PractitionerControlSelection, ...]:
    return tuple(
        PractitionerControlSelection(
            control_key=selection.control_key,
            option=selection.option,
            source_decision_keys=tuple(selection.source_decision_keys),
        )
        for selection in payload.selections
    )


def _latent_event_answers_from_payload(
    payload: LatentEventCalibrationRequest,
) -> tuple[LatentCalibrationAnswer, ...]:
    return tuple(
        LatentCalibrationAnswer(
            scenario_id=answer.scenario_id,
            year_option=answer.year_option,
            result_option=answer.result_option,
            intensity=answer.intensity,
            confidence=answer.confidence,
        )
        for answer in payload.answers
    )
