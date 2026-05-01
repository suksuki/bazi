from __future__ import annotations

from fastapi import FastAPI, HTTPException

from v20 import V20_VERSION
from v20.api.schemas import MeasureRequest
from v20.api.runtime import run_runtime_from_pillars
from v20.corpus.coverage import build_corpus_coverage_plan
from v20.learning.evolution import build_evolution_dry_run_plan
from v20.ops.config import load_runtime_config_from_env
from v20.ops.profiles import validate_runtime_config
from v20.redis.contracts import redis_contract_manifest, validate_redis_contract
from v20.storage.postgres_schema import build_postgres_schema_contract, migration_manifest
from v20.testing.tiers import test_tier_manifest
from v20.validation.suite import run_synthetic_suite


def create_app() -> FastAPI:
    app = FastAPI(
        title="Qiazhi V20",
        version=V20_VERSION,
        description="Independent V20 Bazi measurement runtime.",
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

    @app.get("/api/v20/testing/tiers")
    def testing_tiers() -> dict[str, object]:
        manifest = test_tier_manifest()
        return {
            "version": "v20.testing_tiers_response.v1",
            "manifest": manifest,
            "runtime_mutation": False,
        }

    @app.get("/api/v20/storage/schema")
    def storage_schema() -> dict[str, object]:
        return {
            "version": "v20.storage_schema_response.v1",
            "schema": build_postgres_schema_contract().to_dict(),
            "migration_manifest": migration_manifest(),
            "runtime_mutation": False,
        }

    @app.get("/api/v20/redis/contract")
    def redis_contract() -> dict[str, object]:
        contract = redis_contract_manifest()
        return {
            "version": "v20.redis_contract_response.v1",
            "contract": contract.to_dict(),
            "validation": validate_redis_contract(contract),
            "runtime_mutation": False,
        }

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
                locale=payload.locale,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_MEASURE_INPUT_INVALID", "message": str(exc)},
            ) from exc

    return app


app = create_app()
