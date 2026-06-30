from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

from v40 import __version__
from v40.api.models import (
    CandidateWeightFromBatchRequest,
    EvaluationBatchFromRuntimeRequest,
    EvaluationRunFromRuntimeRequest,
    ExpressionFromRuntimeRequest,
    NativeBatchFromSeedsRequest,
    NativeBaziRuntimeRequest,
    PractitionerCalibrationRequest,
    ReleaseReadinessFromBatchesRequest,
    SyntheticCasesFromSeedsRequest,
    TrainingImpactFromEvaluationRequest,
    WeightActivationExecutionRequest,
    WeightActivationReviewRequest,
)
from v40.contracts.evaluation import EvaluationCaseSpec, ReleaseGateResult
from v40.contracts.manifest import contract_manifest
from v40.contracts.output import LLMExpressionResult
from v40.contracts.training import LabelSource, TrainingLabelEvent
from v40.engines import build_native_bazi_runtime
from v40.evaluation import (
    build_release_readiness_from_batches,
    build_shadow_compare_result,
    evaluate_cases_against_runtime,
    evaluate_native_seeds,
    evaluate_runtime_against_case,
)
from v40.migration import V30ExportEnvelope, build_runtime_from_v30_export
from v40.storage import V40PostgresRepository
from v40.storage.config import v40_repository_configured
from v40.synthetic import build_evaluation_cases_from_seeds
from v40.expression import (
    OllamaExpressionError,
    accept_expression_result,
    build_expression_telemetry,
    build_expression_task_from_runtime,
    list_ollama_models,
    render_local_expression_result,
    render_ollama_expression_result,
    resolve_ollama_expression_config,
)
from v40.training import (
    build_candidate_weight_version_from_batch,
    build_training_impact_from_evaluation,
    build_weight_activation_execution,
    build_weight_activation_review,
)


API_PREFIX = "/api/v40"


def create_app() -> FastAPI:
    app = FastAPI(title="Qiazhi V40", version=__version__)

    @app.get(f"{API_PREFIX}/health")
    def health() -> dict[str, object]:
        runtime_dir = os.getenv("V40_RUNTIME_DIR", str(Path(__file__).resolve().parents[2] / ".runtime"))
        return {
            "ok": True,
            "package": "v40",
            "version": __version__,
            "api_prefix": API_PREFIX,
            "admin_prefix": "/admin/v40",
            "ui_prefix": "/v40/ui",
            "runtime_dir": runtime_dir,
            "repository": os.getenv("V40_REPOSITORY", "postgres"),
            "database_boundary": "qiazhi_v40",
            "postgres_table_prefix": "v40_",
            "repository_configured": v40_repository_configured(),
            "redis_prefix": os.getenv("V40_REDIS_PREFIX", "v40"),
            "v30_runtime_import_allowed": False,
            "boundary": "v40_health_reports_independent_runtime_boundaries",
        }

    @app.get(f"{API_PREFIX}/contracts")
    def contracts() -> dict[str, object]:
        return contract_manifest()

    @app.post(f"{API_PREFIX}/runtime/native-bazi")
    def native_bazi_runtime(payload: NativeBaziRuntimeRequest) -> dict[str, object]:
        runtime = build_native_bazi_runtime(
            request_id=payload.request_id,
            reading_id=payload.reading_id,
            chart=payload.chart_facts,
            user_question=payload.user_question,
            topic=payload.topic,
            role_key=payload.role_key,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_runtime(runtime)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.native_bazi_runtime_response.v1",
            "runtime": runtime.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "native_bazi_runtime_uses_v40_engine_skeleton_without_v30_runtime",
        }

    @app.post(f"{API_PREFIX}/synthetic/cases/from-seeds")
    def synthetic_cases_from_seeds(payload: SyntheticCasesFromSeedsRequest) -> dict[str, object]:
        cases = build_evaluation_cases_from_seeds(payload.seeds)
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                for case in cases:
                    repository.save_evaluation_case(case)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.synthetic_cases_from_seeds_response.v1",
            "cases": [case.model_dump(mode="json") for case in cases],
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "synthetic_cases_are_evaluation_contracts_not_real_world_truth",
        }

    @app.post(f"{API_PREFIX}/evaluation/native-batch/from-seeds")
    def native_batch_from_seeds(payload: NativeBatchFromSeedsRequest) -> dict[str, object]:
        runtimes, cases, runs, summary = evaluate_native_seeds(
            batch_id=payload.batch_id,
            seeds=payload.seeds,
            candidate_version=payload.candidate_version,
            role_key=payload.role_key,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                for runtime in runtimes:
                    repository.save_runtime(runtime)
                for case in cases:
                    repository.save_evaluation_case(case)
                for run in runs:
                    repository.save_evaluation_run(run)
                    if run.release_gate:
                        repository.save_release_gate(run.release_gate)
                repository.save_evaluation_batch_summary(summary)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.native_batch_from_seeds_response.v1",
            "summary": summary.model_dump(mode="json"),
            "runs": [run.model_dump(mode="json") for run in runs],
            "runtime_refs": [runtime.reading_id for runtime in runtimes],
            "case_refs": [case.case_id for case in cases],
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "native_batch_from_seeds_evaluates_v40_native_runtime_without_v30_state",
        }

    @app.post(f"{API_PREFIX}/shadow-compare")
    def shadow_compare(payload: V30ExportEnvelope, persist: bool = False) -> dict[str, object]:
        runtime = build_runtime_from_v30_export(payload)
        compare = build_shadow_compare_result(
            compare_id=f"compare:{payload.export_id}",
            envelope=payload,
            runtime_result=runtime,
        )
        persisted = False
        if persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_runtime(runtime)
                repository.save_shadow_compare(compare)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.shadow_compare_response.v1",
            "runtime": runtime.model_dump(mode="json"),
            "compare": compare.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "shadow_compare_endpoint_imports_plain_json_without_touching_v30_runtime",
        }

    @app.get(f"{API_PREFIX}/shadow-compare/runs")
    def shadow_compare_runs(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            runs = repository.list_shadow_compare_runs(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.shadow_compare_runs_response.v1",
            "runs": runs,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "shadow_compare_history_reads_v40_repository_only",
        }

    @app.post(f"{API_PREFIX}/evaluation/cases")
    def save_evaluation_case(payload: EvaluationCaseSpec) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            repository.save_evaluation_case(payload)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.evaluation_case_save_response.v1",
            "saved": True,
            "case_id": payload.case_id,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "evaluation_case_saved_as_v40_measurement_contract_only",
        }

    @app.get(f"{API_PREFIX}/evaluation/cases")
    def list_evaluation_cases(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            cases = repository.list_evaluation_cases(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.evaluation_cases_response.v1",
            "cases": cases,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "evaluation_cases_read_v40_repository_only",
        }

    @app.post(f"{API_PREFIX}/evaluation/runs/from-runtime")
    def build_evaluation_run(payload: EvaluationRunFromRuntimeRequest) -> dict[str, object]:
        run = evaluate_runtime_against_case(
            run_id=payload.run_id,
            case_spec=payload.case_spec,
            runtime=payload.runtime,
            candidate_version=payload.candidate_version,
            build_release_gate=payload.build_release_gate,
            expression_telemetry=payload.expression_telemetry,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_evaluation_run(run)
                if run.release_gate:
                    repository.save_release_gate(run.release_gate)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.evaluation_run_from_runtime_response.v1",
            "run": run.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "evaluation_run_built_by_deterministic_metrics_without_llm_judge",
        }

    @app.get(f"{API_PREFIX}/evaluation/runs")
    def list_evaluation_runs(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            runs = repository.list_evaluation_runs(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.evaluation_runs_response.v1",
            "runs": runs,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "evaluation_runs_read_v40_repository_only",
        }

    @app.post(f"{API_PREFIX}/evaluation/batches/from-runtime")
    def build_evaluation_batch(payload: EvaluationBatchFromRuntimeRequest) -> dict[str, object]:
        runs, summary = evaluate_cases_against_runtime(
            batch_id=payload.batch_id,
            cases=payload.cases,
            runtime=payload.runtime,
            candidate_version=payload.candidate_version,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                for run in runs:
                    repository.save_evaluation_run(run)
                    if run.release_gate:
                        repository.save_release_gate(run.release_gate)
                repository.save_evaluation_batch_summary(summary)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.evaluation_batch_from_runtime_response.v1",
            "summary": summary.model_dump(mode="json"),
            "runs": [run.model_dump(mode="json") for run in runs],
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "evaluation_batch_built_by_deterministic_metrics_without_llm_judge",
        }

    @app.get(f"{API_PREFIX}/evaluation/batches")
    def list_evaluation_batches(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            batches = repository.list_evaluation_batches(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.evaluation_batches_response.v1",
            "batches": batches,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "evaluation_batches_read_v40_repository_only",
        }

    @app.post(f"{API_PREFIX}/training/labels")
    def save_training_label(payload: TrainingLabelEvent) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            repository.save_training_label_event(payload)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.training_label_save_response.v1",
            "saved": True,
            "event_id": payload.event_id,
            "local_only": payload.local_only,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "training_label_saved_as_feedback_signal_without_weight_write",
        }

    @app.post(f"{API_PREFIX}/calibration/practitioner-selection")
    def save_practitioner_calibration(payload: PractitionerCalibrationRequest) -> dict[str, object]:
        event = TrainingLabelEvent(
            event_id=payload.event_id,
            reading_id=payload.reading_id,
            source=LabelSource.PRACTITIONER_SELECTION,
            target_type=payload.target_type,
            target_ids=payload.target_ids,
            label=payload.label,
            strength=payload.strength,
            confidence=payload.confidence,
            reason=payload.reason,
            evidence_refs=payload.evidence_refs,
            created_by_role=payload.created_by_role,
            local_only=True,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_training_label_event(event)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.practitioner_calibration_response.v1",
            "event": event.model_dump(mode="json"),
            "persisted": persisted,
            "applies_to_current_reading": True,
            "writes_v40_weight": False,
            "writes_v30_state": False,
            "boundary": "practitioner_calibration_records_training_label_without_direct_weight_write",
        }

    @app.post(f"{API_PREFIX}/expression/from-runtime")
    def expression_from_runtime(payload: ExpressionFromRuntimeRequest) -> dict[str, object]:
        task = build_expression_task_from_runtime(
            task_id=payload.task_id,
            runtime=payload.runtime,
            role_key=payload.role_key,
            topic=payload.topic,
        )
        if payload.execution_mode == "provider_text":
            result = LLMExpressionResult(
                result_id=payload.result_id,
                task_id=task.task_id,
                reading_id=payload.runtime.reading_id,
                text=payload.provider_text,
                raw_thinking=payload.raw_thinking,
                provider=payload.provider,
                model=payload.model,
            )
        elif payload.execution_mode == "ollama":
            try:
                result = render_ollama_expression_result(
                    result_id=payload.result_id,
                    task=task,
                    runtime=payload.runtime,
                )
            except OllamaExpressionError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
        else:
            result = render_local_expression_result(
                result_id=payload.result_id,
                task=task,
                runtime=payload.runtime,
                provider=payload.provider,
                model=payload.model,
            )
        acceptance = accept_expression_result(
            result_id=payload.acceptance_id,
            task=task,
            result=result,
            runtime=payload.runtime,
        )
        telemetry = build_expression_telemetry(
            telemetry_id=f"telemetry:{payload.result_id}",
            task=task,
            result=result,
            acceptance=acceptance,
            execution_mode=payload.execution_mode,
        )
        return {
            "version": "v40.expression_from_runtime_response.v1",
            "task": task.model_dump(mode="json"),
            "result": result.model_dump(mode="json"),
            "acceptance": acceptance.model_dump(mode="json"),
            "telemetry": telemetry.model_dump(mode="json"),
            "accepted": acceptance.status.value == "accepted",
            "execution_mode": payload.execution_mode,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "expression_from_runtime_allows_llm_language_but_not_verdict_authority",
        }

    @app.get(f"{API_PREFIX}/expression/provider/ollama")
    def ollama_expression_provider_status() -> dict[str, object]:
        config = resolve_ollama_expression_config()
        return {
            "version": "v40.ollama_expression_provider_status.v1",
            "provider": config.provider,
            "base_url": config.base_url,
            "model": config.model,
            "timeout_seconds": config.timeout_seconds,
            "effective_thinking_timeout_seconds": config.effective_thinking_timeout_seconds,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "effective_thinking_max_tokens": config.effective_thinking_max_tokens,
            "enabled": config.enabled,
            "execute": config.execute,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "ollama_expression_provider_status_exposes_v40_llm_config_without_secrets",
        }

    @app.get(f"{API_PREFIX}/expression/provider/ollama/models")
    def ollama_expression_provider_models() -> dict[str, object]:
        try:
            return list_ollama_models()
        except OllamaExpressionError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get(f"{API_PREFIX}/training/labels")
    def list_training_labels(
        limit: int = Query(default=20, ge=1, le=100),
        reading_id: str = "",
    ) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            events = repository.list_training_label_events(limit=limit, reading_id=reading_id)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.training_labels_response.v1",
            "events": events,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "training_labels_read_v40_feedback_events_only",
        }

    @app.post(f"{API_PREFIX}/training/impact-from-evaluation")
    def build_training_impact(payload: TrainingImpactFromEvaluationRequest) -> dict[str, object]:
        diff = build_training_impact_from_evaluation(
            evaluation_run=payload.evaluation_run,
            training_run_id=payload.training_run_id,
            base_version=payload.base_version,
            candidate_version=payload.candidate_version,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_training_impact_diff(diff)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.training_impact_from_evaluation_response.v1",
            "impact": diff.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "training_impact_diff_generated_without_applying_production_weight",
        }

    @app.get(f"{API_PREFIX}/training/impact-diffs")
    def list_training_impacts(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            impacts = repository.list_training_impact_diffs(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.training_impact_diffs_response.v1",
            "impacts": impacts,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "training_impact_diffs_read_v40_repository_only",
        }

    @app.post(f"{API_PREFIX}/weights/candidates/from-batch")
    def build_candidate_weight(payload: CandidateWeightFromBatchRequest) -> dict[str, object]:
        try:
            weight_version = build_candidate_weight_version_from_batch(
                summary=payload.batch_summary,
                weight_version_id=payload.weight_version_id,
                source_training_run_id=payload.source_training_run_id,
                release_gate_id=payload.release_gate_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_global_weight_version(weight_version)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.candidate_weight_from_batch_response.v1",
            "weight_version": weight_version.model_dump(mode="json"),
            "persisted": persisted,
            "active": False,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "candidate_weight_version_registered_without_activation",
        }

    @app.get(f"{API_PREFIX}/weights/candidates")
    def list_candidate_weights(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            weights = repository.list_global_weight_versions(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.candidate_weights_response.v1",
            "weights": weights,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "candidate_weights_read_v40_repository_without_activation",
        }

    @app.post(f"{API_PREFIX}/release-readiness/from-batches")
    def build_release_readiness(payload: ReleaseReadinessFromBatchesRequest) -> dict[str, object]:
        summary = build_release_readiness_from_batches(
            readiness_id=payload.readiness_id,
            candidate_version=payload.candidate_version,
            batches=payload.batches,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_release_readiness(summary)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.release_readiness_from_batches_response.v1",
            "summary": summary.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "release_readiness_aggregated_without_activation",
        }

    @app.get(f"{API_PREFIX}/release-readiness")
    def list_release_readiness(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            readiness = repository.list_release_readiness(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.release_readiness_response.v1",
            "readiness": readiness,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "release_readiness_read_v40_repository_without_activation",
        }

    @app.post(f"{API_PREFIX}/weights/activation-reviews")
    def build_activation_review(payload: WeightActivationReviewRequest) -> dict[str, object]:
        review = build_weight_activation_review(
            review_id=payload.review_id,
            weight_version=payload.weight_version,
            release_readiness=payload.release_readiness,
            reviewed_by_role=payload.reviewed_by_role,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_weight_activation_review(review)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.weight_activation_review_response.v1",
            "review": review.model_dump(mode="json"),
            "persisted": persisted,
            "activation_applied": False,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "activation_review_recorded_without_applying_weight",
        }

    @app.get(f"{API_PREFIX}/weights/activation-reviews")
    def list_activation_reviews(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            reviews = repository.list_weight_activation_reviews(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.weight_activation_reviews_response.v1",
            "reviews": reviews,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "activation_reviews_read_v40_repository_without_activation",
        }

    @app.post(f"{API_PREFIX}/weights/activate")
    def activate_weight(payload: WeightActivationExecutionRequest) -> dict[str, object]:
        if payload.confirm_phrase != "ACTIVATE_V40_WEIGHT":
            raise HTTPException(status_code=422, detail="Activation requires explicit confirmation phrase")
        try:
            execution = build_weight_activation_execution(
                execution_id=payload.execution_id,
                review=payload.review,
                weight_version=payload.weight_version,
                rollback_version_id=payload.rollback_version_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        try:
            repository = V40PostgresRepository.from_env()
            applied = repository.activate_global_weight_version(execution)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.weight_activation_execution_response.v1",
            "execution": applied.model_dump(mode="json"),
            "activation_applied": True,
            "writes_v30_state": False,
            "writes_v40_weight": True,
            "boundary": "activation_execution_updates_v40_weight_only_with_explicit_confirmation",
        }

    @app.get(f"{API_PREFIX}/weights/activation-executions")
    def list_activation_executions(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            executions = repository.list_weight_activation_executions(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.weight_activation_executions_response.v1",
            "executions": executions,
            "writes_v30_state": False,
            "boundary": "activation_executions_read_v40_repository_only",
        }

    @app.post(f"{API_PREFIX}/release-gates")
    def save_release_gate(payload: ReleaseGateResult) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            repository.save_release_gate(payload)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.release_gate_save_response.v1",
            "saved": True,
            "gate_id": payload.gate_id,
            "recommendation": payload.recommendation.value,
            "production_write_allowed": False,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "release_gate_record_saved_without_applying_production_weight",
        }

    @app.get(f"{API_PREFIX}/release-gates")
    def list_release_gates(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            gates = repository.list_release_gates(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.release_gates_response.v1",
            "gates": gates,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "release_gates_read_v40_repository_only",
        }

    @app.get(f"{API_PREFIX}/lab/summary")
    def lab_summary() -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            summary = repository.lab_summary()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.lab_summary_response.v1",
            "summary": summary,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "lab_summary_reads_v40_control_plane_state_only",
        }

    return app


app = create_app()
