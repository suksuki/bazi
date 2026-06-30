from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from v40 import __version__
from v40.api.models import (
    CandidateWeightFromBatchRequest,
    ConversationTurnRequest,
    EvaluationBatchFromRuntimeRequest,
    EvaluationRunFromRuntimeRequest,
    ExpressionFromRuntimeRequest,
    NativeBatchFromSeedsRequest,
    NativeBaziRuntimeRequest,
    NativeReadingReportRequest,
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
from v40.conversation import build_conversation_seeds, build_conversation_turn
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


def _build_expression_bundle(
    *,
    task_id: str,
    result_id: str,
    acceptance_id: str,
    runtime,
    role_key,
    topic,
    execution_mode: str,
    provider_text: str = "",
    provider: str = "local_expression_adapter",
    model: str = "v40.expression.contract.v1",
    raw_thinking: str = "",
) -> tuple[object, LLMExpressionResult, object, object]:
    task = build_expression_task_from_runtime(
        task_id=task_id,
        runtime=runtime,
        role_key=role_key,
        topic=topic,
    )
    if execution_mode == "provider_text":
        result = LLMExpressionResult(
            result_id=result_id,
            task_id=task.task_id,
            reading_id=runtime.reading_id,
            text=provider_text,
            raw_thinking=raw_thinking,
            provider=provider,
            model=model,
        )
    elif execution_mode == "ollama":
        result = render_ollama_expression_result(
            result_id=result_id,
            task=task,
            runtime=runtime,
        )
    else:
        result = render_local_expression_result(
            result_id=result_id,
            task=task,
            runtime=runtime,
            provider=provider,
            model=model,
        )
    acceptance = accept_expression_result(
        result_id=acceptance_id,
        task=task,
        result=result,
        runtime=runtime,
    )
    telemetry = build_expression_telemetry(
        telemetry_id=f"telemetry:{result_id}",
        task=task,
        result=result,
        acceptance=acceptance,
        execution_mode=execution_mode,
    )
    return task, result, acceptance, telemetry


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

    @app.get("/v40/ui", response_class=HTMLResponse)
    def user_ui() -> HTMLResponse:
        return HTMLResponse(_user_ui_html())

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

    @app.post(f"{API_PREFIX}/readings/native-report")
    def native_reading_report(payload: NativeReadingReportRequest) -> dict[str, object]:
        runtime = build_native_bazi_runtime(
            request_id=payload.request_id,
            reading_id=payload.reading_id,
            chart=payload.chart_facts,
            user_question=payload.user_question,
            topic=payload.topic,
            role_key=payload.role_key,
        )
        try:
            task, result, acceptance, telemetry = _build_expression_bundle(
                task_id=f"task:{payload.reading_id}:report",
                result_id=f"result:{payload.reading_id}:report",
                acceptance_id=f"acceptance:{payload.reading_id}:report",
                runtime=runtime,
                role_key=payload.role_key,
                topic=payload.topic,
                execution_mode=payload.execution_mode,
                provider_text=payload.provider_text,
                provider=payload.provider,
                model=payload.model,
                raw_thinking=payload.raw_thinking,
            )
        except OllamaExpressionError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        conversation_seeds = build_conversation_seeds(
            runtime=runtime,
            accepted_text=acceptance.accepted_text,
            role_key=payload.role_key,
        )
        enriched_runtime = runtime.model_copy(
            update={
                "expression_task": task,
                "expression_result": result,
                "acceptance_result": acceptance,
                "expression_telemetry": telemetry,
                "conversation_seeds": conversation_seeds,
            }
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_runtime(enriched_runtime)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.native_reading_report_response.v1",
            "runtime": enriched_runtime.model_dump(mode="json"),
            "surface_bundle": enriched_runtime.surface_bundle.model_dump(mode="json") if enriched_runtime.surface_bundle else {},
            "accepted_text": acceptance.accepted_text,
            "accepted": acceptance.status.value == "accepted",
            "conversation_seeds": [seed.model_dump(mode="json") for seed in conversation_seeds],
            "expression": {
                "task": task.model_dump(mode="json"),
                "result": result.model_dump(mode="json"),
                "acceptance": acceptance.model_dump(mode="json"),
                "telemetry": telemetry.model_dump(mode="json"),
            },
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "native_reading_report_is_product_runtime_entry_without_llm_verdict_authority",
        }

    @app.post(f"{API_PREFIX}/conversation/turn")
    def conversation_turn(payload: ConversationTurnRequest) -> dict[str, object]:
        try:
            turn, task, result, acceptance, telemetry = build_conversation_turn(
                turn_id=payload.turn_id,
                runtime=payload.runtime,
                question=payload.question,
                seed_id=payload.seed_id,
                selected_option=payload.selected_option,
                role_key=payload.role_key,
                topic=payload.topic,
                execution_mode=payload.execution_mode,
                provider_text=payload.provider_text,
                provider=payload.provider,
                model=payload.model,
                raw_thinking=payload.raw_thinking,
            )
        except OllamaExpressionError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "version": "v40.conversation_turn_response.v1",
            "turn": turn.model_dump(mode="json"),
            "answer_text": turn.answer_text,
            "accepted": turn.accepted,
            "next_seeds": [seed.model_dump(mode="json") for seed in turn.next_seeds],
            "expression": {
                "task": task.model_dump(mode="json"),
                "result": result.model_dump(mode="json"),
                "acceptance": acceptance.model_dump(mode="json"),
                "telemetry": telemetry.model_dump(mode="json"),
            },
            "writes_v30_state": False,
            "writes_v40_production": False,
            "reruns_reading": False,
            "boundary": "conversation_turn_is_independent_dialogue_runtime_after_report",
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
        try:
            task, result, acceptance, telemetry = _build_expression_bundle(
                task_id=payload.task_id,
                result_id=payload.result_id,
                acceptance_id=payload.acceptance_id,
                runtime=payload.runtime,
                role_key=payload.role_key,
                topic=payload.topic,
                execution_mode=payload.execution_mode,
                provider_text=payload.provider_text,
                provider=payload.provider,
                model=payload.model,
                raw_thinking=payload.raw_thinking,
            )
        except OllamaExpressionError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
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


def _user_ui_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>掐指一算 V40</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #070b0b;
      --panel: rgba(20, 28, 27, 0.78);
      --panel-soft: rgba(255,255,255,0.055);
      --line: rgba(190, 210, 198, 0.12);
      --text: #eef5ef;
      --muted: #8d9d95;
      --accent: #66d9b9;
      --accent-strong: #c7f2df;
      --warn: #eccb83;
      --bad: #ff928b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background:
        linear-gradient(135deg, rgba(102, 217, 185, 0.12), transparent 34%),
        linear-gradient(180deg, #081010 0%, var(--bg) 68%);
      color: var(--text);
      font: 14px/1.58 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }
    main { max-width: 1180px; margin: 0 auto; padding: 26px 18px 42px; }
    header { display: flex; justify-content: space-between; gap: 16px; align-items: end; margin-bottom: 18px; }
    h1 { margin: 0; font-size: 24px; font-weight: 760; }
    .brand-mark { color: var(--accent); font-size: 13px; margin-bottom: 4px; }
    .layout { display: grid; grid-template-columns: 360px minmax(0, 1fr); gap: 18px; align-items: start; }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      box-shadow: 0 24px 60px rgba(0,0,0,0.24);
      overflow: hidden;
    }
    .panel-head { padding: 15px 16px 10px; border-bottom: 1px solid var(--line); }
    .panel-head h2 { margin: 0; font-size: 15px; font-weight: 720; }
    form { padding: 14px 16px 16px; display: grid; gap: 12px; }
    label { display: grid; gap: 6px; color: var(--muted); font-size: 12px; }
    input, select, textarea {
      width: 100%;
      border: 0;
      border-radius: 8px;
      background: var(--panel-soft);
      color: var(--text);
      padding: 10px 11px;
      outline: 1px solid transparent;
      font: inherit;
    }
    textarea { min-height: 76px; resize: vertical; }
    input:focus, select:focus, textarea:focus { outline-color: rgba(102,217,185,0.62); }
    .pillars { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
    .pillar { display: grid; gap: 6px; }
    .pillar strong { color: var(--accent-strong); font-size: 12px; font-weight: 680; }
    .pair { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    button {
      border: 0;
      border-radius: 8px;
      background: #1d735f;
      color: white;
      padding: 11px 14px;
      font-weight: 760;
      cursor: pointer;
    }
    button:disabled { opacity: .6; cursor: wait; }
    .result { min-height: 520px; }
    .result-body { padding: 18px; display: grid; gap: 14px; }
    .status {
      display: flex;
      gap: 8px;
      align-items: center;
      color: var(--muted);
      font-size: 12px;
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--accent);
      box-shadow: 0 0 18px rgba(102,217,185,.8);
    }
    .thinking .dot { animation: pulse 1s ease-in-out infinite alternate; }
    @keyframes pulse { from { transform: scale(.78); opacity:.55; } to { transform: scale(1.18); opacity:1; } }
    .report {
      font-size: 15px;
      line-height: 1.78;
      color: var(--text);
    }
    .report h3 { margin: 10px 0 8px; font-size: 14px; color: var(--accent-strong); }
    .report p { margin: 0 0 10px; }
    .report ul { margin: 0 0 16px; padding-left: 18px; }
    .report li { margin: 4px 0; }
    .meta { display: flex; flex-wrap: wrap; gap: 8px; }
    .seeds { display: flex; flex-wrap: wrap; gap: 8px; }
    .conversation { display: grid; gap: 10px; }
    .message {
      border-left: 2px solid rgba(102,217,185,.44);
      background: rgba(255,255,255,.045);
      border-radius: 8px;
      padding: 11px 12px;
    }
    .message .q { color: var(--accent-strong); font-size: 12px; margin-bottom: 6px; }
    .message .a { color: var(--text); }
    .followup { display: none; grid-template-columns: minmax(0, 1fr) auto; gap: 8px; }
    .followup.active { display: grid; }
    .tag {
      border-radius: 999px;
      background: rgba(255,255,255,.07);
      color: var(--muted);
      padding: 6px 9px;
      font-size: 12px;
    }
    .tag.ok { color: var(--accent-strong); background: rgba(102,217,185,.12); }
    .tag.bad { color: var(--bad); background: rgba(255,146,139,.12); }
    .seed-button {
      background: rgba(255,255,255,.065);
      color: var(--accent-strong);
      padding: 8px 10px;
      border-radius: 999px;
      font-size: 12px;
    }
    @media (max-width: 900px) {
      .layout { grid-template-columns: 1fr; }
      header { align-items: start; flex-direction: column; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <div class="brand-mark">V40</div>
        <h1>掐指一算</h1>
      </div>
      <div class="status" id="provider"><span class="dot"></span><span>Gemma4</span></div>
    </header>
    <div class="layout">
      <section class="panel">
        <div class="panel-head"><h2>命盘</h2></div>
        <form id="form">
          <div class="row">
            <label>性别<select id="gender"><option value="乾">乾</option><option value="坤">坤</option></select></label>
            <label>模式<select id="execution"><option value="ollama">Gemma4</option><option value="local">Local</option></select></label>
          </div>
          <div class="pillars">
            <div class="pillar"><strong>年</strong><div class="pair"><input id="yearStem" value="甲" maxlength="1" /><input id="yearBranch" value="子" maxlength="1" /></div></div>
            <div class="pillar"><strong>月</strong><div class="pair"><input id="monthStem" value="戊" maxlength="1" /><input id="monthBranch" value="辰" maxlength="1" /></div></div>
            <div class="pillar"><strong>日</strong><div class="pair"><input id="dayStem" value="丙" maxlength="1" /><input id="dayBranch" value="午" maxlength="1" /></div></div>
            <div class="pillar"><strong>时</strong><div class="pair"><input id="hourStem" value="辛" maxlength="1" /><input id="hourBranch" value="卯" maxlength="1" /></div></div>
          </div>
          <div class="row">
            <label>大运<input id="currentLuck" value="甲辰" /></label>
            <label>流年<input id="currentYear" value="丙午" /></label>
          </div>
          <label>问题<textarea id="question">这个八字今年事业适合稳定发展还是转型突破？</textarea></label>
          <button id="submit" type="submit">开始测算</button>
        </form>
      </section>
      <section class="panel result">
        <div class="panel-head"><h2>测算结果</h2></div>
        <div class="result-body">
          <div class="status" id="status"><span class="dot"></span><span>等待测算</span></div>
          <div class="meta" id="meta"></div>
          <div class="report" id="report">填写命盘后开始。</div>
          <div class="conversation" id="conversation"></div>
          <div class="seeds" id="seeds"></div>
          <div class="followup" id="followupBox">
            <input id="followupQuestion" placeholder="也可以直接追问，例如：今年财运如何？" />
            <button id="askFollowup" type="button">继续问</button>
          </div>
        </div>
      </section>
    </div>
  </main>
  <script>
    const $ = (id) => document.getElementById(id);
    let currentRuntime = null;
    let currentExecutionMode = "ollama";
    const value = (id) => $(id).value.trim();
    function setStatus(text, busy = false) {
      $("status").className = busy ? "status thinking" : "status";
      $("status").lastElementChild.textContent = text;
      $("submit").disabled = busy;
    }
    function tag(text, mode = "") {
      return `<span class="tag ${mode}">${text}</span>`;
    }
    function displayProvider(provider, model) {
      const raw = String(model || provider || "");
      if (raw.includes("gemma") || raw.includes("ollama")) return raw;
      if (raw.includes("conversation.contract") || raw.includes("expression.contract")) return "Local";
      return raw || "Local";
    }
    function escapeHtml(text) {
      return String(text || "").replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[ch]));
    }
    function renderReport(text) {
      const lines = String(text || "").split(/\\n+/).map((line) => line.trim()).filter(Boolean);
      const html = [];
      let listOpen = false;
      const closeList = () => { if (listOpen) { html.push("</ul>"); listOpen = false; } };
      for (const raw of lines) {
        const clean = raw.replace(/^\\*\\*(.+?)\\*\\*$/, "$1").replace(/^#+\\s*/, "");
        const bullet = clean.match(/^[*-]\\s*(.+)$/);
        if (["结论", "建议", "校准", "命理师校准"].includes(clean)) {
          closeList();
          html.push(`<h3>${escapeHtml(clean)}</h3>`);
        } else if (bullet) {
          if (!listOpen) { html.push("<ul>"); listOpen = true; }
          html.push(`<li>${escapeHtml(bullet[1])}</li>`);
        } else {
          closeList();
          html.push(`<p>${escapeHtml(clean)}</p>`);
        }
      }
      closeList();
      return html.join("");
    }
    function renderSeedButtons(seeds) {
      $("seeds").innerHTML = (seeds || []).map((seed) => (
        `<button class="seed-button" type="button" data-seed-id="${escapeHtml(seed.seed_id)}" data-question="${escapeHtml(seed.question)}">${escapeHtml(seed.question)}</button>`
      )).join("");
      $("followupBox").classList.toggle("active", Boolean(currentRuntime));
    }
    function appendConversation(question, answer, telemetry) {
      const meta = telemetry ? ` · ${escapeHtml(displayProvider(telemetry.provider, telemetry.model))}` : "";
      const node = document.createElement("div");
      node.className = "message";
      node.innerHTML = `<div class="q">${escapeHtml(question)}${meta}</div><div class="a report">${renderReport(answer)}</div>`;
      $("conversation").appendChild(node);
    }
    async function askConversation(question, seedId = "") {
      if (!currentRuntime || !question.trim()) return;
      const button = $("askFollowup");
      button.disabled = true;
      setStatus("对话中", true);
      try {
        const turnId = `turn-${Date.now()}`;
        const res = await fetch("/api/v40/conversation/turn", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            turn_id: turnId,
            runtime: currentRuntime,
            question,
            seed_id: seedId,
            execution_mode: currentExecutionMode
          })
        });
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail || "对话失败");
        const telemetry = body.expression.telemetry;
        if (!body.accepted) throw new Error("本轮对话未通过验收。");
        appendConversation(question, body.answer_text, telemetry);
        renderSeedButtons(body.next_seeds || []);
        $("followupQuestion").value = "";
        setStatus("对话已形成", false);
      } catch (error) {
        appendConversation(question, error.message, null);
        setStatus("模型不可用", false);
      } finally {
        button.disabled = false;
      }
    }
    async function loadProvider() {
      try {
        const res = await fetch("/api/v40/expression/provider/ollama");
        const body = await res.json();
        $("provider").lastElementChild.textContent = `${body.model} · ${body.base_url}`;
      } catch (_) {}
    }
    $("form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const readingId = `ui-${Date.now()}`;
      const payload = {
        request_id: `request-${readingId}`,
        reading_id: readingId,
        execution_mode: value("execution"),
        topic: "career",
        role_key: "user",
        user_question: value("question"),
        chart_facts: {
          chart_id: `chart-${readingId}`,
          gender: value("gender"),
          year_stem: value("yearStem"),
          year_branch: value("yearBranch"),
          month_stem: value("monthStem"),
          month_branch: value("monthBranch"),
          day_stem: value("dayStem"),
          day_branch: value("dayBranch"),
          hour_stem: value("hourStem"),
          hour_branch: value("hourBranch"),
          current_luck: value("currentLuck"),
          current_year: value("currentYear")
        },
        persist: false
      };
      currentRuntime = null;
      currentExecutionMode = payload.execution_mode;
      setStatus("推演中", true);
      $("report").textContent = "";
      $("meta").innerHTML = "";
      $("seeds").innerHTML = "";
      $("conversation").innerHTML = "";
      $("followupBox").classList.remove("active");
      try {
        const res = await fetch("/api/v40/readings/native-report", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload)
        });
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail || "请求失败");
        const telemetry = body.expression.telemetry;
        currentRuntime = body.runtime;
        setStatus(body.accepted ? "已形成" : "未采用", false);
        $("report").innerHTML = renderReport(body.accepted_text || "本次表达未通过验收。");
        $("meta").innerHTML = [
          tag(displayProvider(telemetry.provider, telemetry.model), body.accepted ? "ok" : "bad"),
          tag(`thinking ${telemetry.thinking_trace_chars || 0}`),
          tag(telemetry.acceptance_status, body.accepted ? "ok" : "bad")
        ].join("");
        renderSeedButtons(body.conversation_seeds || []);
      } catch (error) {
        setStatus("模型不可用", false);
        $("report").textContent = error.message;
        $("meta").innerHTML = tag("no fallback", "bad");
      }
    });
    $("seeds").addEventListener("click", (event) => {
      const button = event.target.closest("button[data-question]");
      if (!button) return;
      askConversation(button.dataset.question || "", button.dataset.seedId || "");
    });
    $("askFollowup").addEventListener("click", () => {
      askConversation(value("followupQuestion"), "");
    });
    loadProvider();
  </script>
</body>
</html>"""


app = create_app()
