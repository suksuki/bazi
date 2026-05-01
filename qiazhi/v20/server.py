from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles

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
from v20.api.schemas import FeedbackRequest, MeasureRequest, PolicyReviewRequest, PortraitCalibrationRequest
from v20.api.runtime import run_runtime_from_pillars
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
from v20.interaction.feedback_analysis import analyze_feedback
from v20.interaction.feedback_record import record_feedback_analysis
from v20.interaction.portrait_calibration import analyze_portrait_calibration, record_portrait_calibration
from v20.interaction.portrait_ontology import portrait_ontology_manifest
from v20.interaction.question_ranker import question_ranking_manifest
from v20.knowledge.ranking import knowledge_retrieval_manifest
from v20.knowledge.approval import build_first_wave_approval_preflight, build_knowledge_approval_preflight
from v20.knowledge.catalog import build_knowledge_catalog
from v20.knowledge.coverage import build_knowledge_coverage_report
from v20.knowledge.draft_import import build_knowledge_draft_import_preview
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
from v20.knowledge.source_catalog import build_knowledge_source_catalog
from v20.learning.evolution import build_evolution_dry_run_plan
from v20.learning.run_plan import build_learning_run_plan
from v20.learning.policy_review import policy_review_manifest, review_policy_proposal
from v20.learning.registries import registry_manifest
from v20.ops.admin_status import database_admin_status, llm_admin_status
from v20.ops.config import load_runtime_config_from_env
from v20.ops.dependencies import dependency_readiness_report
from v20.ops.profiles import validate_runtime_config
from v20.ops.service_unit import service_unit_manifest
from v20.ops.status import system_status_report
from v20.ops.sync import sync_readiness_report
from v20.profiles.migration import import_v19_profiles_to_postgres, v19_profile_migration_preview
from v20.profiles.store import list_profiles_from_postgres, read_profile_from_postgres
from v20.redis.contracts import redis_contract_manifest, validate_redis_contract
from v20.storage.postgres_schema import build_postgres_schema_contract, migration_manifest
from v20.storage.local_jsonl import local_jsonl_store_from_env
from v20.testing.matrix import build_test_coverage_matrix
from v20.testing.tiers import test_tier_manifest
from v20.validation.intelligence_generation import validate_intelligence_generation
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
    def admin_database() -> dict[str, object]:
        return database_admin_status()

    @app.get("/api/v20/admin/llm")
    def admin_llm(probe_models: bool = False) -> dict[str, object]:
        return llm_admin_status(probe_models=probe_models)

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

    @app.get("/api/v20/profiles/v19-migration-preview")
    def profiles_v19_migration_preview() -> dict[str, object]:
        return v19_profile_migration_preview()

    @app.post("/api/v20/profiles/import-v19")
    def profiles_import_v19(apply: bool = False, owner_id: str = "admin") -> dict[str, object]:
        return import_v19_profiles_to_postgres(apply=apply, owner_id=owner_id)

    @app.get("/api/v20/profiles")
    def profiles_list(request: Request, owner_id: str = "", limit: int = 80) -> dict[str, object]:
        session = _require_profile_session(request)
        target_owner = _profile_owner_for_session(session, owner_id)
        return list_profiles_from_postgres(owner_id=target_owner, limit=limit)

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

    @app.get("/api/v20/questions/ranking-policy")
    def question_ranking_policy() -> dict[str, object]:
        return question_ranking_manifest()

    @app.get("/api/v20/knowledge/retrieval-policy")
    def knowledge_retrieval_policy() -> dict[str, object]:
        return knowledge_retrieval_manifest()

    @app.get("/api/v20/knowledge/catalog")
    def knowledge_catalog() -> dict[str, object]:
        return build_knowledge_catalog()

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

    @app.get("/api/v20/features/confidence-calibration")
    def feature_confidence_calibration() -> dict[str, object]:
        return confidence_calibration_manifest()

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
        return read_corpus_artifact_status(run_id or "v20_full_518k_20260501_main")

    @app.get("/api/v20/corpus/artifacts/coverage-summary")
    def corpus_artifact_coverage_summary(run_id: str = "") -> dict[str, object]:
        return read_corpus_coverage_summary(run_id or "v20_full_518k_20260501_main")

    @app.get("/api/v20/corpus/artifacts/cluster-model")
    def corpus_artifact_cluster_model(run_id: str = "") -> dict[str, object]:
        return read_corpus_cluster_model(run_id or "v20_full_518k_20260501_main")

    @app.get("/api/v20/corpus/artifacts/training")
    def corpus_artifact_training(run_id: str = "") -> dict[str, object]:
        return read_corpus_training_artifacts(run_id or "v20_full_518k_20260501_main")

    @app.get("/api/v20/corpus/similar")
    def corpus_similar(case_id: str, run_id: str = "", limit: int = 8) -> dict[str, object]:
        return find_similar_cases(case_id, run_id=run_id or "v20_full_518k_20260501_main", limit=limit)

    @app.get("/api/v20/validation/synthetic-suite")
    def synthetic_suite() -> dict[str, object]:
        return run_synthetic_suite()

    @app.get("/api/v20/learning/evolution-plan")
    def evolution_plan() -> dict[str, object]:
        return build_evolution_dry_run_plan()

    @app.get("/api/v20/learning/run-plan")
    def learning_run_plan() -> dict[str, object]:
        return build_learning_run_plan()

    @app.get("/api/v20/learning/registries")
    def learning_registries() -> dict[str, object]:
        return registry_manifest()

    @app.get("/api/v20/learning/policy-review")
    def learning_policy_review_manifest() -> dict[str, object]:
        return policy_review_manifest()

    @app.get("/api/v20/intelligence/generation-manifest")
    def intelligence_generation_manifest() -> dict[str, object]:
        return build_intelligence_generation_manifest()

    @app.get("/api/v20/validation/intelligence-generation")
    def intelligence_generation_validation() -> dict[str, object]:
        return validate_intelligence_generation()

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
                llm_mode=payload.llm_mode,
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
                llm_mode=payload.llm_mode,
            )
            return project_runtime_for_role(result, role_key)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={"error": "V20_ROLE_MEASURE_INPUT_INVALID", "message": str(exc)},
            ) from exc

    return app


app = create_app()


def _require_profile_session(request: Request) -> dict[str, object]:
    auth = auth_status(request)
    if not auth.get("authenticated"):
        raise HTTPException(status_code=401, detail={"error": "V20_AUTH_REQUIRED"})
    return dict(auth.get("session") or {})


def _profile_owner_for_session(session: dict[str, object], owner_id: str) -> str:
    role = str(session.get("role") or "user")
    user_id = str(session.get("user_id") or "")
    requested_owner = str(owner_id or "").strip()
    if role == "admin":
        return requested_owner or "admin"
    if requested_owner and requested_owner != user_id:
        raise HTTPException(status_code=403, detail={"error": "V20_PROFILE_OWNER_FORBIDDEN"})
    return user_id
