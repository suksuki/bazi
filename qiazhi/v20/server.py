from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from v20 import V20_VERSION
from v20.access.projection import project_runtime_for_role
from v20.access.roles import access_role_manifest
from v20.api.schemas import FeedbackRequest, MeasureRequest, PolicyReviewRequest
from v20.api.runtime import run_runtime_from_pillars
from v20.corpus.coverage import build_corpus_coverage_plan
from v20.features.calibration import confidence_calibration_manifest
from v20.interaction.feedback_analysis import analyze_feedback
from v20.interaction.feedback_record import record_feedback_analysis
from v20.interaction.question_ranker import question_ranking_manifest
from v20.knowledge.ranking import knowledge_retrieval_manifest
from v20.learning.evolution import build_evolution_dry_run_plan
from v20.learning.policy_review import policy_review_manifest, review_policy_proposal
from v20.learning.registries import registry_manifest
from v20.ops.config import load_runtime_config_from_env
from v20.ops.dependencies import dependency_readiness_report
from v20.ops.profiles import validate_runtime_config
from v20.ops.service_unit import service_unit_manifest
from v20.ops.status import system_status_report
from v20.ops.sync import sync_readiness_report
from v20.redis.contracts import redis_contract_manifest, validate_redis_contract
from v20.storage.postgres_schema import build_postgres_schema_contract, migration_manifest
from v20.storage.local_jsonl import local_jsonl_store_from_env
from v20.testing.matrix import build_test_coverage_matrix
from v20.testing.tiers import test_tier_manifest
from v20.validation.suite import run_synthetic_suite


def create_app() -> FastAPI:
    app = FastAPI(
        title="Qiazhi V20",
        version=V20_VERSION,
        description="Independent V20 Bazi measurement runtime.",
    )
    frontend_dir = Path(__file__).resolve().parent / "frontend"
    if frontend_dir.exists():
        app.mount("/v20/ui", StaticFiles(directory=frontend_dir, html=True), name="v20_ui")

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

    @app.get("/api/v20/system/status")
    def system_status() -> dict[str, object]:
        return system_status_report()

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

    @app.get("/api/v20/runtime/dependencies")
    def runtime_dependencies() -> dict[str, object]:
        return dependency_readiness_report()

    @app.get("/api/v20/access/roles")
    def access_roles() -> dict[str, object]:
        return access_role_manifest()

    @app.get("/api/v20/questions/ranking-policy")
    def question_ranking_policy() -> dict[str, object]:
        return question_ranking_manifest()

    @app.get("/api/v20/knowledge/retrieval-policy")
    def knowledge_retrieval_policy() -> dict[str, object]:
        return knowledge_retrieval_manifest()

    @app.get("/api/v20/features/confidence-calibration")
    def feature_confidence_calibration() -> dict[str, object]:
        return confidence_calibration_manifest()

    @app.get("/api/v20/corpus/coverage")
    def corpus_coverage() -> dict[str, object]:
        return {
            "version": "v20.corpus_coverage_response.v1",
            "plan": build_corpus_coverage_plan().to_dict(),
            "runtime_mutation": False,
        }

    @app.get("/api/v20/validation/synthetic-suite")
    def synthetic_suite() -> dict[str, object]:
        return run_synthetic_suite()

    @app.get("/api/v20/learning/evolution-plan")
    def evolution_plan() -> dict[str, object]:
        return build_evolution_dry_run_plan()

    @app.get("/api/v20/learning/registries")
    def learning_registries() -> dict[str, object]:
        return registry_manifest()

    @app.get("/api/v20/learning/policy-review")
    def learning_policy_review_manifest() -> dict[str, object]:
        return policy_review_manifest()

    @app.post("/api/v20/learning/policy-review")
    def learning_policy_review(payload: PolicyReviewRequest) -> dict[str, object]:
        try:
            return review_policy_proposal(
                policy_type=payload.policy_type,
                policy_payload=payload.policy_payload,
                source=payload.source,
                eval_report_id=payload.eval_report_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={"error": "V20_POLICY_REVIEW_INVALID", "message": str(exc)}) from exc

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

    @app.post("/api/v20/measure")
    @app.post("/api/v20/runtime/measure")
    def measure(payload: MeasureRequest) -> dict[str, object]:
        try:
            return run_runtime_from_pillars(
                payload.year,
                payload.month,
                payload.day,
                payload.hour,
                input_id=payload.input_id,
                question_key=payload.question_key,
                user_text=payload.user_text,
                flow_year_pillar=payload.flow_year_pillar,
                luck_pillar=payload.luck_pillar,
                flow_month_pillar=payload.flow_month_pillar,
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_MEASURE_INPUT_INVALID", "message": str(exc)},
            ) from exc

    @app.post("/api/v20/measure/view/{role_key}")
    def measure_view(role_key: str, payload: MeasureRequest) -> dict[str, object]:
        try:
            result = run_runtime_from_pillars(
                payload.year,
                payload.month,
                payload.day,
                payload.hour,
                input_id=payload.input_id,
                question_key=payload.question_key,
                user_text=payload.user_text,
                flow_year_pillar=payload.flow_year_pillar,
                luck_pillar=payload.luck_pillar,
                flow_month_pillar=payload.flow_month_pillar,
                locale=payload.locale,
            )
            return project_runtime_for_role(result, role_key)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_ROLE_MEASURE_INPUT_INVALID", "message": str(exc)},
            ) from exc

    return app


app = create_app()
