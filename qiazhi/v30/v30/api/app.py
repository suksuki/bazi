from __future__ import annotations

import hashlib
import json
import os
import secrets
import shlex
import subprocess
import sys
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from v30.admin import ADMIN_API_PREFIX as ADMIN_CONTROL_API_PREFIX, build_admin_control_plane_manifest
from v30.config import load_settings
from v30.contracts import BirthInput, CoreRuntimeResult
from v30.core.chart_context import build_chart_context_from_birth_input
from v30.dialogue_chain import (
    append_dialogue_turn,
    build_dialogue_seed_suggestions,
    build_dialogue_store,
    start_dialogue_session,
)
from v30.answer import build_answer_context, compose_rule_bound_answer
from v30.brain.policy_optimizer import optimize_central_brain_policy
from v30.brain.practitioner_interaction import (
    apply_practitioner_selection_effects_to_thinking,
    build_admin_intelligence_replay,
    build_practitioner_interaction_state,
    build_practitioner_selection_record,
    find_option_set,
)
from v30.brain.reading_engine import build_central_reading_state
from v30.brain.training_examples import BrainTrainingExampleStore
from v30.learning import DEFAULT_AUTO_TRAINING_FAMILIES, run_auto_apply_training
from v30.ops.admin_runtime import (
    admin_runtime_config_status,
    apply_database_schema,
    database_admin_status,
    llm_admin_probe,
    llm_admin_status,
    llm_admin_test,
    redis_admin_status,
    save_admin_database_config,
    save_admin_llm_config,
    save_admin_redis_config,
)
from v30.hidden_factor import (
    HiddenFactorCalibration,
    HiddenFactorState,
    build_hidden_factor_state,
    hidden_factor_feedback_from_payload,
    merge_hidden_factor_state,
)
from v30.interaction_brain import mark_hidden_factor_feedback_saved, public_interaction_brain_result
from v30.llm import (
    call_bazi_llm_thinking_step_summary,
    compose_bazi_llm_answer_draft,
    load_v30_llm_provider_config_from_env,
    stream_bazi_llm_thinking_step_summary_events,
)
from v30.presentation.client_profiles import CLIENT_PROFILES
from v30.presentation.client_model import build_presentation_model
from v30.presentation.thinking import build_thinking_projection
from v30.policy import RuntimePointerStore, build_promotion_lineage, load_question_policy_comparison
from v30.production import build_production_sidecar
from v30.runtime import attach_hidden_factor_state, attach_question_outcome, create_runtime_from_context, create_smoke_runtime
from v30.storage.names import redis_key
from v30.storage.artifacts import search_518k_validation_artifacts, search_validation_artifacts
from v30.storage.hidden_factor_state import build_hidden_factor_state_repository
from v30.storage.product_store import build_product_store_repository
from v30.storage.redis_cache import build_runtime_cache
from v30.storage.repository import build_runtime_repository


API_PREFIX = "/api/v30"
ADMIN_API_PREFIX = ADMIN_CONTROL_API_PREFIX
UI_PREFIX = "/v30/ui"

M3_BACKGROUND_STEP_TIMEOUTS = {
    "m3_snapshot": 180,
    "m3_synthetic": 300,
    "training_pipeline": 900,
    "518k_sample": 900,
    "518k_shard": 1200,
    "518k_readiness_matrix": 1200,
}


class ReadingRequest(BaseModel):
    reading_id: str = Field(default="v30-smoke-reading")
    day_master: str = Field(default="甲")
    day_master_element: str = Field(default="wood")
    locale: str = Field(default="zh")
    target_year: int | None = None
    actor_id: str = ""
    session_id: str = ""
    birth_input: dict[str, object] | None = None


class AnswerRequest(BaseModel):
    answer: str
    role: str | None = None
    locale: str | None = None
    client: str | None = None
    submit_surface: str | None = None
    submit_source_id: str | None = None
    submit_contract_version: str | None = None
    outcome_status: str | None = None
    selected_option: str | None = None
    structured_payload: dict[str, object] = Field(default_factory=dict)
    confidence: float | None = None
    feedback_tags: list[str] = Field(default_factory=list)


class LLMAnswerEnhancementRequest(BaseModel):
    role: str | None = None
    locale: str | None = None
    client: str | None = None
    task_type: str | None = None
    domain: str = ""


class DialogueCreateRequest(BaseModel):
    seed_text: str = "我今年财运如何？"
    source: str = "user"
    role: str | None = None
    locale: str | None = None
    client: str | None = None
    stage_id: str = ""


class DialogueTurnRequest(BaseModel):
    text: str = ""
    selected_option: str = ""
    structured_payload: dict[str, object] = Field(default_factory=dict)
    role: str | None = None
    locale: str | None = None
    client: str | None = None
    stage_id: str = ""


class LLMThinkingSummaryRequest(BaseModel):
    role: str | None = None
    locale: str | None = None
    client: str | None = None


class LLMThinkingBatchSummaryRequest(BaseModel):
    role: str | None = None
    locale: str | None = None
    client: str | None = None
    step_ids: list[str] = Field(default_factory=list)
    max_steps: int = Field(default=4, ge=1, le=12)


class PractitionerSelectionRequest(BaseModel):
    option_set_id: str
    selected_option_ids: list[str] = Field(default_factory=list)
    ranked_option_ids: list[str] = Field(default_factory=list)
    rejected_option_ids: list[str] = Field(default_factory=list)
    action: str = "select"
    note: str = ""
    confidence: float = Field(default=0.72, ge=0.0, le=1.0)
    actor_id: str = ""


class TrainingRunRequest(BaseModel):
    training_run_id: str | None = None
    families: list[str] = Field(default_factory=list)
    promotion_validation_mode: str = "strict"


class BrainTrainingSplitRequest(BaseModel):
    seed: int = Field(default=20260628)
    train_ratio: float = Field(default=0.7, ge=0.1, le=0.9)
    validation_ratio: float = Field(default=0.2, ge=0.05, le=0.5)
    source: str = ""
    stage_id: str = ""


class BrainTrainingOptimizeRequest(BaseModel):
    split: str = "train"
    min_examples: int = Field(default=3, ge=1, le=10000)
    max_delta: float = Field(default=0.06, ge=0.01, le=0.2)


class BrainTrainingReplayGateRequest(BaseModel):
    train_split: str = "train"
    replay_split: str = "replay"
    min_examples: int = Field(default=3, ge=1, le=10000)
    min_replay_examples: int = Field(default=1, ge=1, le=10000)
    max_delta: float = Field(default=0.06, ge=0.01, le=0.2)


class BrainTrainingDistributionGateRequest(BaseModel):
    train_split: str = "train"
    replay_split: str = "replay"
    min_examples: int = Field(default=3, ge=1, le=10000)
    min_replay_examples: int = Field(default=1, ge=1, le=10000)
    sample_limit: int = Field(default=1, ge=1, le=256)
    include_shard: bool = False
    shard_id: int = Field(default=7, ge=0)
    shard_limit: int = Field(default=1, ge=1, le=512)
    max_delta: float = Field(default=0.06, ge=0.01, le=0.2)


class M3BackgroundRunRequest(BaseModel):
    sample_limit: int = Field(default=8, ge=1, le=256)
    persist_m3_to_db: bool = True
    include_shard: bool = False
    shard_id: int = Field(default=7, ge=0)
    shard_limit: int = Field(default=16, ge=1, le=512)
    include_readiness_matrix: bool = False


class TrainingOrchestratorRunRequest(BaseModel):
    plan_id: str = "central_brain_auto_apply"
    training_run_id: str | None = None
    families: list[str] = Field(default_factory=list)
    promotion_validation_mode: str = "strict"
    sample_limit: int = Field(default=8, ge=1, le=256)
    persist_m3_to_db: bool = True
    include_shard: bool = False
    shard_id: int = Field(default=7, ge=0)
    shard_limit: int = Field(default=16, ge=1, le=512)
    include_readiness_matrix: bool = False


class TrainingOrchestratorRerunRequest(BaseModel):
    job_id: str = ""
    failed_steps: list[str] = Field(default_factory=list)


class AdminRuntimeConfigRequest(BaseModel):
    payload: dict[str, object] = Field(default_factory=dict)


class AuthRegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str = ""
    role: str = "user"


class AuthLoginRequest(BaseModel):
    username: str
    password: str


class AuthLogoutRequest(BaseModel):
    session_token: str


class BaziProfileRequest(BaseModel):
    session_token: str
    profile_id: str | None = None
    display_name: str
    gender: str = ""
    calendar_type: str = "solar"
    birth_date: str = ""
    birth_time: str = "00:00"
    timezone: str = "Asia/Shanghai"
    birth_place: str = ""
    target_year: int | None = None
    lunar_is_leap_month: bool = False
    use_true_solar_time: bool = False
    unknown_hour: bool = False
    status: str = "active"


def create_app() -> FastAPI:
    settings = load_settings()
    app = FastAPI(title="Qiazhi V30", version="30.0.0a0")
    repository = build_runtime_repository(settings)
    hidden_factor_states = build_hidden_factor_state_repository(settings)
    cache = build_runtime_cache(settings)
    product_store_path = settings.runtime_dir / "product_ui_store.json"
    product_store = build_product_store_repository(settings, product_store_path)
    dialogue_store = build_dialogue_store(settings.runtime_dir / "dialogues")
    m3_background_jobs: dict[str, dict[str, object]] = {}
    m3_background_lock = threading.Lock()
    latest_m3_background_job_id = ""
    auto_training_jobs: dict[str, dict[str, object]] = {}
    auto_training_lock = threading.Lock()
    latest_auto_training_job_id = ""
    training_orchestrator_jobs: dict[str, dict[str, object]] = {}
    training_orchestrator_lock = threading.Lock()
    latest_training_orchestrator_job_id = ""
    practitioner_selection_store: dict[str, list[dict[str, object]]] = {}
    practitioner_selection_lock = threading.Lock()
    answer_interaction_locks: dict[str, threading.Lock] = {}
    answer_interaction_lock_guard = threading.Lock()

    @app.middleware("http")
    async def _ui_no_cache_middleware(request, call_next):
        response = await call_next(request)
        if request.url.path == "/v30" or request.url.path.startswith(f"{UI_PREFIX}/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    def _persist_m3_background_job(job: dict[str, object]) -> None:
        job_id = str(job.get("job_id") or "")
        if not job_id:
            return
        path = _m3_background_job_path(job_id)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            job["persist_error"] = "runtime_job_write_failed"

    def _m3_background_job_path(job_id: str) -> Path:
        return settings.runtime_dir / "training" / "m3_background_jobs" / f"{job_id}.json"

    def _answer_interaction_lock(reading_id: str) -> threading.Lock:
        with answer_interaction_lock_guard:
            lock = answer_interaction_locks.get(reading_id)
            if lock is None:
                lock = threading.Lock()
                answer_interaction_locks[reading_id] = lock
            return lock

    def _m3_background_job_log_path(job_id: str) -> Path:
        return settings.runtime_dir / "training" / "m3_background_jobs" / f"{job_id}.log"

    def _read_m3_background_job(job_id: str) -> dict[str, object] | None:
        path = _m3_background_job_path(job_id)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def _latest_m3_background_job_id_from_disk() -> str:
        job_dir = settings.runtime_dir / "training" / "m3_background_jobs"
        try:
            files = sorted(job_dir.glob("m3-job-*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        except OSError:
            return ""
        return files[0].stem if files else ""

    def _m3_job_public(job: dict[str, object] | None) -> dict[str, object]:
        if not job:
            return {"status": "not_found"}
        payload = dict(job)
        log_path = str(payload.get("log_path") or "")
        if log_path:
            payload["log_tail"] = _read_text_tail(Path(log_path), limit=2000)
        return payload

    def _persist_auto_training_job(job: dict[str, object]) -> None:
        job_id = str(job.get("job_id") or "")
        if not job_id:
            return
        path = _auto_training_job_path(job_id)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            job["persist_error"] = "runtime_job_write_failed"

    def _auto_training_job_path(job_id: str) -> Path:
        return settings.runtime_dir / "training" / "auto_apply_jobs" / f"{job_id}.json"

    def _auto_training_job_log_path(job_id: str) -> Path:
        return settings.runtime_dir / "training" / "auto_apply_jobs" / f"{job_id}.log"

    def _read_auto_training_job(job_id: str) -> dict[str, object] | None:
        path = _auto_training_job_path(job_id)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def _latest_auto_training_job_id_from_disk() -> str:
        job_dir = settings.runtime_dir / "training" / "auto_apply_jobs"
        try:
            files = sorted(job_dir.glob("auto-training-job-*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        except OSError:
            return ""
        return files[0].stem if files else ""

    def _list_auto_training_jobs_from_disk(*, limit: int = 12) -> list[dict[str, object]]:
        job_dir = settings.runtime_dir / "training" / "auto_apply_jobs"
        try:
            files = sorted(job_dir.glob("auto-training-job-*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        except OSError:
            return []
        rows: list[dict[str, object]] = []
        for path in files[:limit]:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(payload, dict):
                continue
            public = _auto_training_job_public(payload)
            config = public.get("config") if isinstance(public.get("config"), dict) else {}
            training_run = public.get("training_run") if isinstance(public.get("training_run"), dict) else {}
            metrics = training_run.get("metrics") if isinstance(training_run.get("metrics"), dict) else {}
            rows.append(
                {
                    "job_id": public.get("job_id"),
                    "status": public.get("status"),
                    "created_at": public.get("created_at"),
                    "started_at": public.get("started_at"),
                    "finished_at": public.get("finished_at"),
                    "progress_percent": public.get("progress_percent"),
                    "current_step": public.get("current_step"),
                    "training_run_id": training_run.get("training_run_id") or config.get("training_run_id") or "",
                    "run_status": training_run.get("status") or "",
                    "promoted_count": metrics.get("promoted_count"),
                    "candidate_count": metrics.get("candidate_count"),
                }
            )
        return rows

    def _auto_training_job_public(job: dict[str, object] | None) -> dict[str, object]:
        if not job:
            return {"status": "not_found"}
        payload = dict(job)
        log_path = str(payload.get("log_path") or "")
        if log_path:
            payload["log_tail"] = _read_text_tail(Path(log_path), limit=2000)
        events = payload.get("progress_events")
        if isinstance(events, list):
            payload["progress_events"] = events[-12:]
        return payload

    def _auto_training_run_summary(result: object) -> dict[str, object]:
        data = result.model_dump(mode="json") if hasattr(result, "model_dump") else {}
        promotions = data.get("promotions", [])
        compact_promotions = []
        if isinstance(promotions, list):
            for row in promotions:
                if not isinstance(row, dict):
                    continue
                compact_promotions.append(
                    {
                        "family": row.get("family"),
                        "artifact_id": row.get("artifact_id"),
                        "previous_artifact_id": row.get("previous_artifact_id"),
                        "promoted": row.get("promoted"),
                        "pointer_status": row.get("pointer_status"),
                        "failures": row.get("failures", []),
                    }
                )
        return {
            "version": data.get("version", "v30.auto_training_run_summary.v1"),
            "training_run_id": data.get("training_run_id"),
            "families": data.get("families", []),
            "started_at": data.get("started_at"),
            "finished_at": data.get("finished_at"),
            "auto_apply": data.get("auto_apply"),
            "status": data.get("status"),
            "promotions": compact_promotions,
            "active_policy_versions": data.get("active_policy_versions", {}),
            "policy_application": data.get("policy_application", {}),
            "training_signal_summary": data.get("training_signal_summary", {}),
            "metrics": data.get("metrics", {}),
            "failures": data.get("failures", []),
        }

    def _training_orchestrator_plans() -> list[dict[str, object]]:
        return [
            {
                "plan_id": "central_brain_auto_apply",
                "label": "中枢智能大脑自动训练",
                "description": "运行合成训练信号、生成候选策略、验证并自动提升 runtime pointer。",
                "auto_apply": True,
                "steps": ["preflight_lineage", "auto_apply_training", "post_training_lineage", "history_snapshot"],
                "default_families": list(DEFAULT_AUTO_TRAINING_FAMILIES),
            },
            {
                "plan_id": "quick_validation_only",
                "label": "轻量训练管线验证",
                "description": "只跑 training_pipeline synthetic 和 lineage snapshot，不提升 runtime pointer。",
                "auto_apply": False,
                "steps": ["training_pipeline_synthetic", "lineage_snapshot"],
                "default_families": list(DEFAULT_AUTO_TRAINING_FAMILIES),
            },
            {
                "plan_id": "m3_518k_validation",
                "label": "M3 / 518K 验证",
                "description": "运行 M3 快照、M3 synthetic、training_pipeline、518K sample；可选 shard 和 readiness matrix，不提升 runtime pointer。",
                "auto_apply": False,
                "steps": ["m3_snapshot", "m3_synthetic", "training_pipeline", "518k_sample"],
                "optional_steps": ["518k_shard", "518k_readiness_matrix"],
                "default_sample_limit": 8,
                "default_shard_id": 7,
                "default_shard_limit": 16,
            },
            {
                "plan_id": "central_brain_phase2_training",
                "label": "中枢智能大脑二阶段训练",
                "description": "运行 BrainTrainingExample split、策略优化、synthetic replay gate 和 518K distribution gate；不提升 runtime pointer。",
                "auto_apply": False,
                "steps": ["brain_example_summary", "build_training_splits", "optimize_policy_candidate", "synthetic_replay_gate", "518k_distribution_gate"],
                "default_sample_limit": 1,
                "default_shard_id": 7,
                "default_shard_limit": 1,
            },
            {
                "plan_id": "evaluation_spine_quality_gate",
                "label": "测算质量评测脊柱",
                "description": "运行 EvaluationCaseSpec、Verdict/Advice/Probe 质量门和 lineage snapshot；不提升 runtime pointer。",
                "auto_apply": False,
                "steps": ["evaluation_training_spine", "policy_lineage_snapshot", "quality_diff_snapshot"],
                "default_include_phase2": True,
            },
        ]

    def _training_orchestrator_plan(plan_id: str) -> dict[str, object]:
        for plan in _training_orchestrator_plans():
            if plan["plan_id"] == plan_id:
                return plan
        raise ValueError(f"unsupported training orchestrator plan: {plan_id}")

    def _persist_training_orchestrator_job(job: dict[str, object]) -> None:
        job_id = str(job.get("job_id") or "")
        if not job_id:
            return
        path = _training_orchestrator_job_path(job_id)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            job["persist_error"] = "runtime_job_write_failed"

    def _training_orchestrator_job_path(job_id: str) -> Path:
        return settings.runtime_dir / "training" / "orchestrator_jobs" / f"{job_id}.json"

    def _training_orchestrator_job_log_path(job_id: str) -> Path:
        return settings.runtime_dir / "training" / "orchestrator_jobs" / f"{job_id}.log"

    def _training_validation_summary(payload: object) -> dict[str, object]:
        if not isinstance(payload, dict):
            return {
                "version": "v30.training_validation_summary.v1",
                "suite_id": "",
                "passed": False,
                "case_count": 0,
                "passed_count": 0,
                "failed_count": 0,
                "result_count": 0,
                "failed_preview": [],
            }
        results = payload.get("results")
        failed_preview: list[dict[str, object]] = []
        if isinstance(results, list):
            for row in results:
                if not isinstance(row, dict):
                    continue
                if row.get("passed") is True or str(row.get("status") or "").lower() in {"passed", "completed"}:
                    continue
                failed_preview.append(
                    {
                        "case_id": row.get("case_id") or row.get("id") or row.get("name") or "",
                        "status": row.get("status") or "",
                        "error": row.get("error") or row.get("reason") or "",
                    }
                )
                if len(failed_preview) >= 5:
                    break
        return {
            "version": "v30.training_validation_summary.v1",
            "suite_id": payload.get("suite_id") or "",
            "passed": bool(payload.get("passed")),
            "case_count": payload.get("case_count") or 0,
            "passed_count": payload.get("passed_count") or 0,
            "failed_count": payload.get("failed_count") or 0,
            "result_count": len(results) if isinstance(results, list) else int(payload.get("result_count") or 0),
            "failed_preview": failed_preview if failed_preview else payload.get("failed_preview") or [],
        }

    def _training_orchestrator_step_public(row: object) -> dict[str, object]:
        if not isinstance(row, dict):
            return {}
        allowed = (
            "step",
            "status",
            "passed",
            "passed_count",
            "case_count",
            "family_count",
            "job_count",
            "promoted_count",
            "candidate_count",
            "promotion_signal",
            "eligible_count",
            "sample_limit",
            "shard_id",
            "average_overall_score",
            "evidence_coverage_rate",
            "overclaim_rate",
            "advice_grounding_rate",
            "probe_yield_score",
            "failed_case_ids",
            "error",
        )
        return {key: row.get(key) for key in allowed if key in row}

    def _read_training_orchestrator_job(job_id: str) -> dict[str, object] | None:
        path = _training_orchestrator_job_path(job_id)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def _latest_training_orchestrator_job_id_from_disk() -> str:
        job_dir = settings.runtime_dir / "training" / "orchestrator_jobs"
        try:
            files = list(job_dir.glob("training-orchestrator-job-*.json"))
        except OSError:
            return ""
        rows: list[tuple[str, str]] = []
        for path in files:
            payload = _read_training_orchestrator_job(path.stem)
            created_at = str(payload.get("created_at") or "") if isinstance(payload, dict) else ""
            rows.append((created_at or path.stem, path.stem))
        rows.sort(reverse=True)
        return rows[0][1] if rows else ""

    def _list_training_orchestrator_jobs_from_disk(*, limit: int = 12) -> list[dict[str, object]]:
        job_dir = settings.runtime_dir / "training" / "orchestrator_jobs"
        try:
            files = list(job_dir.glob("training-orchestrator-job-*.json"))
        except OSError:
            return []
        payloads: list[dict[str, object]] = []
        for path in files:
            payload = _read_training_orchestrator_job(path.stem)
            if not payload:
                continue
            payloads.append(payload)
        payloads.sort(key=lambda row: str(row.get("created_at") or row.get("job_id") or ""), reverse=True)
        rows: list[dict[str, object]] = []
        for payload in payloads[:limit]:
            rows.append(
                {
                    "job_id": payload.get("job_id"),
                    "plan_id": payload.get("plan_id"),
                    "status": payload.get("status"),
                    "created_at": payload.get("created_at"),
                    "finished_at": payload.get("finished_at"),
                    "current_step": payload.get("current_step"),
                    "progress_percent": payload.get("progress_percent"),
                    "training_run_id": (payload.get("config") or {}).get("training_run_id")
                    if isinstance(payload.get("config"), dict)
                    else "",
                }
            )
        return rows

    def _training_orchestrator_job_public(job: dict[str, object] | None, *, include_diff: bool = False) -> dict[str, object]:
        if not job:
            return {"status": "not_found"}
        payload = dict(job)
        if "validation_result" in payload:
            payload["validation_result"] = _training_validation_summary(payload.get("validation_result"))
        results = payload.get("step_results")
        if isinstance(results, list):
            payload["step_results"] = [_training_orchestrator_step_public(row) for row in results if isinstance(row, dict)]
        log_path = str(payload.get("log_path") or "")
        if log_path:
            payload["log_tail"] = _read_text_tail(Path(log_path), limit=2000)
        events = payload.get("progress_events")
        if isinstance(events, list):
            payload["progress_events"] = events[-12:]
        payload["failed_steps"] = _training_orchestrator_failed_steps(payload)
        payload["quality_metrics"] = _training_orchestrator_quality_metrics(payload)
        if include_diff:
            payload["diff_summary"] = _training_orchestrator_diff_summary(payload)
        return payload

    def _training_orchestrator_step_passed(row: dict[str, object]) -> bool:
        status = str(row.get("status") or "").lower()
        if status in {"failed", "blocked"}:
            return False
        if row.get("passed") is False:
            return False
        if row.get("promotion_signal") not in {None, "", "eligible"}:
            return False
        return True

    def _training_orchestrator_failed_steps(job: dict[str, object]) -> list[str]:
        rows = job.get("step_results")
        if not isinstance(rows, list):
            return []
        failed = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            step = str(row.get("step") or "")
            if step and not _training_orchestrator_step_passed(row):
                failed.append(step)
        failed_step = str(job.get("failed_step") or "")
        if failed_step and failed_step not in failed:
            failed.append(failed_step)
        return failed

    def _training_orchestrator_metrics(job: dict[str, object]) -> dict[str, object]:
        rows = [row for row in job.get("step_results", []) if isinstance(row, dict)] if isinstance(job.get("step_results"), list) else []
        training_run = job.get("training_run") if isinstance(job.get("training_run"), dict) else {}
        training_metrics = training_run.get("metrics") if isinstance(training_run.get("metrics"), dict) else {}
        case_count = 0
        eligible_518k_count = 0
        for row in rows:
            try:
                case_count += int(row.get("case_count") or 0)
            except (TypeError, ValueError):
                pass
            if str(row.get("promotion_signal") or "") == "eligible":
                eligible_518k_count += 1
        failed_steps = _training_orchestrator_failed_steps(job)
        return {
            "status": job.get("status"),
            "step_count": len(rows),
            "passed_step_count": len(rows) - len(failed_steps),
            "failed_step_count": len(failed_steps),
            "case_count": case_count,
            "eligible_518k_count": eligible_518k_count,
            "promoted_count": training_metrics.get("promoted_count"),
            "candidate_count": training_metrics.get("candidate_count"),
        }

    def _metric_number(value: object) -> float | None:
        if isinstance(value, bool) or value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _training_orchestrator_quality_metrics(job: dict[str, object]) -> dict[str, object]:
        rows = [row for row in job.get("step_results", []) if isinstance(row, dict)] if isinstance(job.get("step_results"), list) else []
        training_run = job.get("training_run") if isinstance(job.get("training_run"), dict) else {}
        signal_summary = training_run.get("training_signal_summary") if isinstance(training_run.get("training_signal_summary"), dict) else {}
        training_quality = signal_summary.get("quality_metrics") if isinstance(signal_summary.get("quality_metrics"), dict) else {}
        evaluation_result = job.get("evaluation_training_spine") if isinstance(job.get("evaluation_training_spine"), dict) else {}
        evaluation_decision = evaluation_result.get("decision") if isinstance(evaluation_result.get("decision"), dict) else {}
        metrics: dict[str, object] = {
            "version": "v30.training_orchestrator.quality_metrics.v1",
            "chart_fact_mutation_allowed": False,
            "boundary": "orchestrator_quality_metrics_compare_business_quality_without_mutating_chart_facts",
        }
        for key, value in training_quality.items():
            if key in {"version", "quality_metric_count", "chart_fact_mutation_allowed", "boundary"}:
                continue
            metrics[key] = value
        if rows:
            passed_count = sum(1 for row in rows if _training_orchestrator_step_passed(row))
            metrics["m3_step_pass_rate"] = round(passed_count / max(1, len(rows)), 3)
            sample_rows = [row for row in rows if str(row.get("step") or "").startswith("518k")]
            if sample_rows:
                eligible_rows = sum(1 for row in sample_rows if str(row.get("promotion_signal") or "") == "eligible")
                metrics["m3_518k_eligible_rate"] = round(eligible_rows / max(1, len(sample_rows)), 3)
            case_count = 0
            for row in rows:
                try:
                    case_count += int(row.get("case_count") or 0)
                except (TypeError, ValueError):
                    pass
            if case_count:
                metrics["validation_case_count"] = case_count
        if evaluation_decision:
            metrics["evaluation_overall_score"] = evaluation_decision.get("average_overall_score")
            metrics["evaluation_evidence_coverage_rate"] = evaluation_decision.get("evidence_coverage_rate")
            metrics["evaluation_advice_grounding_rate"] = evaluation_decision.get("advice_grounding_rate")
            metrics["evaluation_probe_yield_score"] = evaluation_decision.get("probe_yield_score")
            metrics["evaluation_overclaim_rate"] = evaluation_decision.get("overclaim_rate")
            metrics["evaluation_case_count"] = evaluation_decision.get("case_count")
            metrics["evaluation_passed_case_count"] = evaluation_decision.get("passed_case_count")
        metrics["quality_metric_count"] = len(
            [
                key
                for key in metrics
                if key
                not in {
                    "version",
                    "quality_metric_count",
                    "chart_fact_mutation_allowed",
                    "boundary",
                }
            ]
        )
        return metrics

    def _training_orchestrator_quality_diff_rows(
        current_metrics: dict[str, object],
        previous_metrics: dict[str, object],
    ) -> list[dict[str, object]]:
        positive_metrics = (
            "final_synthesis_quality_score",
            "brain_judge_accepted_rate",
            "advice_actionability",
            "decision_focus_coverage",
            "action_step_coverage",
            "risk_boundary_coverage",
            "evidence_chain_coverage",
            "interaction_loop_strength",
            "high_value_question_strength",
            "expression_quality_strength",
            "m3_step_pass_rate",
            "m3_518k_eligible_rate",
            "validation_case_count",
            "evaluation_overall_score",
            "evaluation_evidence_coverage_rate",
            "evaluation_advice_grounding_rate",
            "evaluation_probe_yield_score",
            "evaluation_case_count",
            "evaluation_passed_case_count",
        )
        risk_metrics = ("template_risk", "overclaim_risk", "evaluation_overclaim_rate")
        rows: list[dict[str, object]] = []
        for key in (*positive_metrics, *risk_metrics):
            current_value = _metric_number(current_metrics.get(key))
            previous_value = _metric_number(previous_metrics.get(key))
            if current_value is None and previous_value is None:
                continue
            delta = round((current_value or 0.0) - (previous_value or 0.0), 3)
            direction = "unchanged"
            if delta > 0:
                direction = "up"
            if delta < 0:
                direction = "down"
            higher_is_better = key not in risk_metrics
            judgement = "unchanged"
            if delta:
                judgement = "improved" if (delta > 0 and higher_is_better) or (delta < 0 and not higher_is_better) else "regressed"
            rows.append(
                {
                    "metric": key,
                    "current": current_value,
                    "previous": previous_value,
                    "delta": delta,
                    "direction": direction,
                    "higher_is_better": higher_is_better,
                    "judgement": judgement,
                }
            )
        return rows

    def _previous_training_orchestrator_job(job: dict[str, object]) -> dict[str, object] | None:
        plan_id = str(job.get("plan_id") or "")
        current_job_id = str(job.get("job_id") or "")
        for row in _list_training_orchestrator_jobs_from_disk(limit=50):
            job_id = str(row.get("job_id") or "")
            if not job_id or job_id == current_job_id or row.get("plan_id") != plan_id:
                continue
            previous = _read_training_orchestrator_job(job_id)
            if previous:
                return previous
        return None

    def _training_orchestrator_diff_summary(job: dict[str, object]) -> dict[str, object]:
        previous = _previous_training_orchestrator_job(job)
        current_metrics = _training_orchestrator_metrics(job)
        previous_metrics = _training_orchestrator_metrics(previous) if previous else {}
        current_quality_metrics = _training_orchestrator_quality_metrics(job)
        previous_quality_metrics = _training_orchestrator_quality_metrics(previous) if previous else {}
        quality_rows = _training_orchestrator_quality_diff_rows(current_quality_metrics, previous_quality_metrics)
        rows = []
        for key in ("passed_step_count", "failed_step_count", "case_count", "eligible_518k_count", "promoted_count"):
            current_value = current_metrics.get(key)
            previous_value = previous_metrics.get(key)
            if current_value is None and previous_value is None:
                continue
            direction = "unchanged"
            try:
                delta = int(current_value or 0) - int(previous_value or 0)
            except (TypeError, ValueError):
                delta = 0
            if delta > 0:
                direction = "up"
            if delta < 0:
                direction = "down"
            rows.append(
                {
                    "metric": key,
                    "current": current_value,
                    "previous": previous_value,
                    "delta": delta,
                    "direction": direction,
                }
            )
        return {
            "version": "v30.training_orchestrator.diff_summary.v1",
            "job_id": job.get("job_id"),
            "plan_id": job.get("plan_id"),
            "previous_job_id": previous.get("job_id") if previous else "",
            "current_metrics": current_metrics,
            "previous_metrics": previous_metrics,
            "diff_rows": rows,
            "current_quality_metrics": current_quality_metrics,
            "previous_quality_metrics": previous_quality_metrics,
            "quality_diff_rows": quality_rows,
            "quality_improvement_count": sum(1 for row in quality_rows if row.get("judgement") == "improved"),
            "quality_regression_count": sum(1 for row in quality_rows if row.get("judgement") == "regressed"),
            "failed_steps": _training_orchestrator_failed_steps(job),
            "boundary": "orchestrator_diff_compares_training_job_summaries_without_running_training_or_mutating_policy",
        }

    def _policy_lineage_summary_payload() -> dict[str, object]:
        families = ("structure_policy", "mainline_policy", "question_policy", "rule_policy")
        rows = [
            build_promotion_lineage(family=family, settings=settings).model_dump(mode="json")
            for family in families
        ]
        return {
            "version": "v30.admin.policy_lineage_summary.v1",
            "families": rows,
            "rollback_supported": True,
            "chart_fact_mutation_allowed": False,
            "boundary": "policy_lineage_summary_reads_runtime_pointers_and_supports_pointer_rollback_without_mutating_chart_facts",
        }

    def _update_training_orchestrator_job(job_id: str, **updates: object) -> None:
        with training_orchestrator_lock:
            current = training_orchestrator_jobs[job_id]
            current.update(updates)
            _persist_training_orchestrator_job(current)

    def _append_training_orchestrator_event(job_id: str, event: dict[str, object]) -> None:
        with training_orchestrator_lock:
            current = training_orchestrator_jobs[job_id]
            events = list(current.get("progress_events") or [])
            events.append(event)
            current["progress_events"] = events[-60:]
            _persist_training_orchestrator_job(current)

    def _run_training_orchestrator_job(job_id: str) -> None:
        with training_orchestrator_lock:
            job = training_orchestrator_jobs[job_id]
            job["status"] = "running"
            job["started_at"] = _utc_now()
            job["current_step"] = "started"
            job["progress_percent"] = 1
            _persist_training_orchestrator_job(job)

        config = dict(job.get("config") or {})
        plan_id = str(job.get("plan_id") or config.get("plan_id") or "")
        families = tuple(config.get("families") or DEFAULT_AUTO_TRAINING_FAMILIES)
        training_run_id = str(config.get("training_run_id") or "")
        promotion_validation_mode = str(config.get("promotion_validation_mode") or "strict")
        sample_limit = int(config.get("sample_limit") or 8)
        shard_id = int(config.get("shard_id") or 7)
        shard_limit = int(config.get("shard_limit") or 16)
        rerun_steps = [str(row) for row in config.get("rerun_steps", [])] if isinstance(config.get("rerun_steps"), list) else []
        step_results: list[dict[str, object]] = []
        try:
            if plan_id == "central_brain_auto_apply":
                _update_training_orchestrator_job(
                    job_id,
                    current_step="preflight_lineage",
                    progress_percent=8,
                    completed_steps=0,
                )
                preflight = _policy_lineage_summary_payload()
                step_results.append({"step": "preflight_lineage", "status": "completed", "family_count": len(preflight["families"])})
                _update_training_orchestrator_job(job_id, lineage_before=preflight, step_results=step_results)

                def _progress(event: dict[str, object]) -> None:
                    inner_percent = int(event.get("progress_percent") or 0)
                    outer_percent = 15 + int(inner_percent * 0.65)
                    _update_training_orchestrator_job(
                        job_id,
                        current_step=f"auto_apply_training:{event.get('step') or 'running'}",
                        progress_percent=max(15, min(80, outer_percent)),
                    )
                    _append_training_orchestrator_event(job_id, event)

                result = run_auto_apply_training(
                    families=families,
                    training_run_id=training_run_id,
                    promotion_validation_mode=promotion_validation_mode,
                    progress_callback=_progress,
                )
                training_run = _auto_training_run_summary(result)
                step_results.append(
                    {
                        "step": "auto_apply_training",
                        "status": training_run.get("status"),
                        "promoted_count": (training_run.get("metrics") or {}).get("promoted_count")
                        if isinstance(training_run.get("metrics"), dict)
                        else None,
                    }
                )
                _update_training_orchestrator_job(
                    job_id,
                    training_run=training_run,
                    step_results=step_results,
                    completed_steps=2,
                    current_step="post_training_lineage",
                    progress_percent=86,
                )
                post_lineage = _policy_lineage_summary_payload()
                step_results.append({"step": "post_training_lineage", "status": "completed", "family_count": len(post_lineage["families"])})
                history = {"version": "v30.admin.auto_apply_training_history_snapshot.v1", "jobs": _list_auto_training_jobs_from_disk(limit=12)}
                step_results.append({"step": "history_snapshot", "status": "completed", "job_count": len(history["jobs"])})
                _update_training_orchestrator_job(
                    job_id,
                    lineage_summary=post_lineage,
                    history_snapshot=history,
                    step_results=step_results,
                    completed_steps=4,
                    current_step="completed",
                    progress_percent=100,
                    status="completed" if training_run.get("status") == "applied" else "failed",
                    finished_at=_utc_now(),
                    failures=training_run.get("failures", []),
                )
                return

            if plan_id == "central_brain_phase2_training":
                from v30.validation import run_518k_validation
                from v30.validation.central_brain_phase2_distribution_gate import build_central_brain_phase2_distribution_gate
                from v30.validation.central_brain_phase2_replay_gate import build_central_brain_phase2_replay_gate

                store = BrainTrainingExampleStore(settings.runtime_dir)
                total_steps = 5
                _update_training_orchestrator_job(job_id, current_step="brain_example_summary", progress_percent=5, completed_steps=0)
                raw_summary = store.summary(split="raw")
                step_results.append(
                    {
                        "step": "brain_example_summary",
                        "status": "completed",
                        "example_count": raw_summary.get("example_count"),
                        "answered_count": raw_summary.get("answered_count"),
                    }
                )
                _update_training_orchestrator_job(job_id, step_results=step_results, completed_steps=1, progress_percent=18)

                _update_training_orchestrator_job(job_id, current_step="build_training_splits", progress_percent=22)
                split_manifest = store.build_splits(seed=20260628, train_ratio=0.7, validation_ratio=0.2)
                step_results.append(
                    {
                        "step": "build_training_splits",
                        "status": "completed",
                        "raw_count": split_manifest.get("raw_count"),
                        "splits": split_manifest.get("splits", {}),
                    }
                )
                _update_training_orchestrator_job(job_id, step_results=step_results, completed_steps=2, progress_percent=36)

                _update_training_orchestrator_job(job_id, current_step="optimize_policy_candidate", progress_percent=42)
                train_examples = store.read(split="train", limit=100000)
                candidate = optimize_central_brain_policy(train_examples, min_examples=3, max_delta=0.06)
                step_results.append(
                    {
                        "step": "optimize_policy_candidate",
                        "status": candidate.get("status"),
                        "promotion_signal": candidate.get("promotion_signal"),
                        "example_count": candidate.get("example_count"),
                    }
                )
                _update_training_orchestrator_job(
                    job_id,
                    phase2_candidate_policy=candidate,
                    step_results=step_results,
                    completed_steps=3,
                    progress_percent=56,
                )

                _update_training_orchestrator_job(job_id, current_step="synthetic_replay_gate", progress_percent=62)
                replay_examples = store.read(split="replay", limit=100000)
                replay_gate = build_central_brain_phase2_replay_gate(
                    candidate_policy=candidate,
                    replay_examples=replay_examples,
                    min_replay_examples=1,
                )
                step_results.append(
                    {
                        "step": "synthetic_replay_gate",
                        "status": replay_gate.get("status"),
                        "promotion_signal": replay_gate.get("promotion_signal"),
                        "failed_check_ids": (replay_gate.get("decision") or {}).get("failed_check_ids")
                        if isinstance(replay_gate.get("decision"), dict)
                        else [],
                    }
                )
                _update_training_orchestrator_job(
                    job_id,
                    phase2_replay_gate=replay_gate,
                    step_results=step_results,
                    completed_steps=4,
                    progress_percent=74,
                )

                _update_training_orchestrator_job(job_id, current_step="518k_distribution_gate", progress_percent=80)
                policy_overrides = {"question_policy": {"central_brain_phase2_policy": candidate}}
                sample = run_518k_validation(
                    mode="sample",
                    limit=sample_limit,
                    artifact_dir=settings.runtime_dir / "validation" / "518k",
                    policy_payload_overrides=policy_overrides,
                ).model_dump(mode="json")
                shard = {}
                if config.get("include_shard"):
                    shard = run_518k_validation(
                        mode="shard",
                        shard_id=shard_id,
                        limit=shard_limit,
                        artifact_dir=settings.runtime_dir / "validation" / "518k",
                        policy_payload_overrides=policy_overrides,
                    ).model_dump(mode="json")
                distribution_gate = build_central_brain_phase2_distribution_gate(
                    replay_gate=replay_gate,
                    sample_result=sample,
                    shard_result=shard,
                    min_sample_cases=sample_limit,
                    require_shard=bool(config.get("include_shard")),
                )
                passed = distribution_gate.get("promotion_signal") == "eligible"
                step_results.append(
                    {
                        "step": "518k_distribution_gate",
                        "status": distribution_gate.get("status"),
                        "promotion_signal": distribution_gate.get("promotion_signal"),
                        "case_count": (distribution_gate.get("distribution_518k") or {}).get("sample", {}).get("case_count")
                        if isinstance(distribution_gate.get("distribution_518k"), dict)
                        else None,
                        "failed_check_ids": (distribution_gate.get("decision") or {}).get("failed_check_ids")
                        if isinstance(distribution_gate.get("decision"), dict)
                        else [],
                    }
                )
                _update_training_orchestrator_job(
                    job_id,
                    phase2_split_manifest=split_manifest,
                    phase2_replay_gate=replay_gate,
                    phase2_distribution_gate=distribution_gate,
                    step_results=step_results,
                    completed_steps=total_steps,
                    current_step="completed",
                    progress_percent=100,
                    status="completed" if passed else "failed",
                    finished_at=_utc_now(),
                    phase2_result={
                        "version": "v30.training_orchestrator.phase2_result.v1",
                        "passed": passed,
                        "sample_limit": sample_limit,
                        "include_shard": bool(config.get("include_shard")),
                        "candidate_promotion_signal": candidate.get("promotion_signal"),
                        "replay_promotion_signal": replay_gate.get("promotion_signal"),
                        "distribution_promotion_signal": distribution_gate.get("promotion_signal"),
                        "full_518k_required": False,
                    },
                    failures=[] if passed else ["central_brain_phase2_training_failed"],
                )
                return

            if plan_id == "evaluation_spine_quality_gate":
                from v30.validation.evaluation_training_spine import run_evaluation_training_spine

                total_steps = 3
                _update_training_orchestrator_job(
                    job_id,
                    current_step="evaluation_training_spine",
                    progress_percent=10,
                    completed_steps=0,
                )
                evaluation = run_evaluation_training_spine(include_phase2=True)
                evaluation_decision = evaluation.get("decision") if isinstance(evaluation.get("decision"), dict) else {}
                passed = evaluation.get("status") == "passed" and bool(evaluation_decision.get("evaluation_training_spine_ready"))
                step_results.append(
                    {
                        "step": "evaluation_training_spine",
                        "status": "passed" if passed else "blocked",
                        "case_count": evaluation_decision.get("case_count"),
                        "passed_count": evaluation_decision.get("passed_case_count"),
                        "average_overall_score": evaluation_decision.get("average_overall_score"),
                        "evidence_coverage_rate": evaluation_decision.get("evidence_coverage_rate"),
                        "overclaim_rate": evaluation_decision.get("overclaim_rate"),
                        "advice_grounding_rate": evaluation_decision.get("advice_grounding_rate"),
                        "probe_yield_score": evaluation_decision.get("probe_yield_score"),
                        "failed_case_ids": evaluation_decision.get("failed_case_ids") or [],
                    }
                )
                _update_training_orchestrator_job(
                    job_id,
                    evaluation_training_spine=evaluation,
                    step_results=step_results,
                    completed_steps=1,
                    progress_percent=58,
                    current_step="policy_lineage_snapshot",
                )
                lineage = _policy_lineage_summary_payload()
                step_results.append({"step": "policy_lineage_snapshot", "status": "completed", "family_count": len(lineage["families"])})
                _update_training_orchestrator_job(
                    job_id,
                    lineage_summary=lineage,
                    step_results=step_results,
                    completed_steps=2,
                    progress_percent=78,
                    current_step="quality_diff_snapshot",
                )
                quality_snapshot = {
                    "version": "v30.evaluation_spine_quality_snapshot.v1",
                    "evaluation_ready": passed,
                    "average_overall_score": evaluation_decision.get("average_overall_score"),
                    "evidence_coverage_rate": evaluation_decision.get("evidence_coverage_rate"),
                    "overclaim_rate": evaluation_decision.get("overclaim_rate"),
                    "advice_grounding_rate": evaluation_decision.get("advice_grounding_rate"),
                    "probe_yield_score": evaluation_decision.get("probe_yield_score"),
                    "production_policy_write_allowed": False,
                    "chart_fact_mutation_allowed": False,
                }
                step_results.append(
                    {
                        "step": "quality_diff_snapshot",
                        "status": "completed",
                        "average_overall_score": quality_snapshot["average_overall_score"],
                        "overclaim_rate": quality_snapshot["overclaim_rate"],
                    }
                )
                _update_training_orchestrator_job(
                    job_id,
                    evaluation_quality_snapshot=quality_snapshot,
                    step_results=step_results,
                    completed_steps=total_steps,
                    current_step="completed",
                    progress_percent=100,
                    status="completed" if passed else "failed",
                    finished_at=_utc_now(),
                    evaluation_spine_result={
                        "version": "v30.training_orchestrator.evaluation_spine_result.v1",
                        "passed": passed,
                        "case_count": evaluation_decision.get("case_count"),
                        "passed_case_count": evaluation_decision.get("passed_case_count"),
                        "production_policy_write_allowed": False,
                        "chart_fact_mutation_allowed": False,
                    },
                    failures=[] if passed else ["evaluation_spine_quality_gate_failed"],
                )
                return

            if plan_id == "m3_518k_validation":
                m3_steps: list[tuple[str, object]] = [
                    (
                        "m3_snapshot",
                        lambda: _run_m3_background_snapshot(
                            sample_limit=sample_limit,
                            persist_requested=bool(config.get("persist_m3_to_db")),
                        ),
                    ),
                    ("m3_synthetic", lambda: _run_m3_background_synthetic_tier("m3_core_spine")),
                    ("training_pipeline", lambda: _run_m3_background_synthetic_tier("training_pipeline")),
                    ("518k_sample", lambda: _run_m3_background_518k_validation(mode="sample", limit=sample_limit)),
                ]
                if config.get("include_shard"):
                    m3_steps.append(
                        (
                            "518k_shard",
                            lambda: _run_m3_background_518k_validation(mode="shard", shard_id=shard_id, limit=shard_limit),
                        )
                    )
                if config.get("include_readiness_matrix"):
                    m3_steps.append(
                        (
                            "518k_readiness_matrix",
                            lambda: _run_m3_background_518k_readiness_matrix(
                                sample_limit=sample_limit,
                                shard_id=shard_id,
                                shard_limit=shard_limit,
                            ),
                        )
                    )
                if rerun_steps:
                    m3_steps = [row for row in m3_steps if row[0] in set(rerun_steps)]
                    if not m3_steps:
                        raise ValueError(f"no runnable failed steps for m3_518k_validation: {','.join(rerun_steps)}")
                total_steps = len(m3_steps)
                passed = True
                for index, (step_name, runner) in enumerate(m3_steps):
                    _update_training_orchestrator_job(
                        job_id,
                        current_step=step_name,
                        progress_percent=max(5, int((index / total_steps) * 94)),
                        completed_steps=index,
                    )
                    result = runner()
                    summary = _m3_step_result(step_name, result)
                    step_results.append(summary)
                    if summary.get("passed") is False:
                        passed = False
                    if step_name in {"518k_sample", "518k_shard"} and summary.get("promotion_signal") not in {"eligible", None}:
                        passed = False
                    _update_training_orchestrator_job(
                        job_id,
                        step_results=step_results,
                        completed_steps=index + 1,
                        progress_percent=int(((index + 1) / total_steps) * 100),
                    )
                lineage = _policy_lineage_summary_payload()
                _update_training_orchestrator_job(
                    job_id,
                    lineage_summary=lineage,
                    step_results=step_results,
                    completed_steps=total_steps,
                    current_step="completed",
                    progress_percent=100,
                    status="completed" if passed else "failed",
                    finished_at=_utc_now(),
                    m3_518k_result={
                        "version": "v30.training_orchestrator.m3_518k_result.v1",
                        "passed": passed,
                        "sample_limit": sample_limit,
                        "include_shard": bool(config.get("include_shard")),
                        "include_readiness_matrix": bool(config.get("include_readiness_matrix")),
                        "step_count": total_steps,
                    },
                    failures=[] if passed else ["m3_518k_validation_failed"],
                )
                return

            if plan_id == "quick_validation_only":
                from v30.validation import run_synthetic_tier

                quick_steps = ["training_pipeline_synthetic", "lineage_snapshot"]
                if rerun_steps:
                    quick_steps = [row for row in quick_steps if row in set(rerun_steps)]
                    if not quick_steps:
                        raise ValueError(f"no runnable failed steps for quick_validation_only: {','.join(rerun_steps)}")
                validation_payload: dict[str, object] = {}
                if "training_pipeline_synthetic" in quick_steps:
                    _update_training_orchestrator_job(
                        job_id,
                        current_step="training_pipeline_synthetic",
                        progress_percent=25,
                        completed_steps=0,
                    )
                    validation = run_synthetic_tier("training_pipeline")
                    validation_payload = _training_validation_summary(validation.model_dump(mode="json"))
                    step_results.append(
                        {
                            "step": "training_pipeline_synthetic",
                            "status": "passed" if validation_payload.get("passed") else "failed",
                            "passed_count": validation_payload.get("passed_count"),
                            "case_count": validation_payload.get("case_count"),
                        }
                    )
                lineage = {}
                if "lineage_snapshot" in quick_steps:
                    lineage = _policy_lineage_summary_payload()
                    step_results.append({"step": "lineage_snapshot", "status": "completed", "family_count": len(lineage["families"])})
                _update_training_orchestrator_job(
                    job_id,
                    validation_result=validation_payload,
                    lineage_summary=lineage,
                    step_results=step_results,
                    completed_steps=len(quick_steps),
                    current_step="completed",
                    progress_percent=100,
                    status="completed" if not validation_payload or validation_payload.get("passed") else "failed",
                    finished_at=_utc_now(),
                )
                return

            raise ValueError(f"unsupported training orchestrator plan: {plan_id}")
        except Exception as exc:  # pragma: no cover - defensive runtime status path
            _update_training_orchestrator_job(
                job_id,
                status="failed",
                error=str(exc),
                failures=[str(exc)],
                finished_at=_utc_now(),
            )

    def _run_auto_training_background_job(job_id: str) -> None:
        with auto_training_lock:
            job = auto_training_jobs[job_id]
            job["status"] = "running"
            job["started_at"] = _utc_now()
            job["current_step"] = "started"
            job["progress_percent"] = 1
            _persist_auto_training_job(job)

        config = dict(job.get("config") or {})
        families = tuple(config.get("families") or DEFAULT_AUTO_TRAINING_FAMILIES)
        training_run_id = str(config.get("training_run_id") or "")
        promotion_validation_mode = str(config.get("promotion_validation_mode") or "strict")

        def _progress(event: dict[str, object]) -> None:
            with auto_training_lock:
                current = auto_training_jobs[job_id]
                events = list(current.get("progress_events") or [])
                events.append(event)
                current["progress_events"] = events[-40:]
                current["current_step"] = str(event.get("step") or current.get("current_step") or "running")
                current["progress_percent"] = int(event.get("progress_percent") or current.get("progress_percent") or 0)
                current["message"] = str(event.get("message") or "")
                current["completed_steps"] = int(event.get("completed_steps") or current.get("completed_steps") or 0)
                current["total_steps"] = int(event.get("total_steps") or current.get("total_steps") or len(families))
                _persist_auto_training_job(current)

        try:
            result = run_auto_apply_training(
                families=families,
                training_run_id=training_run_id,
                promotion_validation_mode=promotion_validation_mode,
                progress_callback=_progress,
            )
        except Exception as exc:  # pragma: no cover - defensive runtime status path
            with auto_training_lock:
                job = auto_training_jobs[job_id]
                job["status"] = "failed"
                job["error"] = str(exc)
                job["finished_at"] = _utc_now()
                job["progress_percent"] = max(1, int(job.get("progress_percent") or 1))
                _persist_auto_training_job(job)
            return

        summary = _auto_training_run_summary(result)
        with auto_training_lock:
            job = auto_training_jobs[job_id]
            job["status"] = "completed" if summary.get("status") == "applied" else "failed"
            job["current_step"] = "completed"
            job["finished_at"] = _utc_now()
            job["progress_percent"] = 100
            job["completed_steps"] = len(families)
            job["total_steps"] = len(families)
            job["training_run"] = summary
            job["metrics"] = summary.get("metrics", {})
            job["policy_application"] = summary.get("policy_application", {})
            job["training_signal_summary"] = summary.get("training_signal_summary", {})
            job["active_policy_versions"] = summary.get("active_policy_versions", {})
            job["failures"] = summary.get("failures", [])
            _persist_auto_training_job(job)

    def _read_text_tail(path: Path, *, limit: int) -> str:
        try:
            return path.read_text(encoding="utf-8")[-limit:]
        except OSError:
            return ""

    def _admin_training_worker_env() -> dict[str, str]:
        env = dict(os.environ)
        env["V30_ENV"] = settings.env
        env["V30_HOST"] = settings.host
        env["V30_PORT"] = str(settings.port)
        env["V30_REPOSITORY"] = settings.repository
        env["V30_REDIS_PREFIX"] = settings.redis_prefix
        env["V30_RUNTIME_DIR"] = str(settings.runtime_dir)
        if settings.database_url:
            env["V30_DATABASE_URL"] = settings.database_url
        else:
            env.pop("V30_DATABASE_URL", None)
        if settings.redis_url:
            env["V30_REDIS_URL"] = settings.redis_url
        else:
            env.pop("V30_REDIS_URL", None)
        return env

    def _launch_admin_training_worker(
        *,
        kind: str,
        job_id: str,
        job_path: Path,
        log_path: Path,
        lock: threading.Lock,
        jobs: dict[str, dict[str, object]],
        read_job,
        persist_job,
    ) -> None:
        command = [
            sys.executable,
            "scripts/run_admin_training_worker.py",
            "--kind",
            kind,
            "--job-file",
            str(job_path),
        ]
        root = Path(__file__).resolve().parents[2]
        log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with log_path.open("ab") as log_file:
                process = subprocess.Popen(
                    command,
                    cwd=root,
                    env=_admin_training_worker_env(),
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
        except OSError as exc:
            with lock:
                job = read_job(job_id) or jobs.get(job_id) or {}
                if job:
                    job["status"] = "failed"
                    job["error"] = str(exc)
                    job["finished_at"] = _utc_now()
                    jobs[job_id] = job
                    persist_job(job)
            return
        with lock:
            job = read_job(job_id) or jobs.get(job_id) or {}
            if job:
                job["worker_pid"] = process.pid
                job["worker_mode"] = "isolated_process"
                job["log_path"] = str(log_path)
                jobs[job_id] = job
                persist_job(job)

        def _reap_worker() -> None:
            returncode = process.wait()
            if returncode == 0:
                return
            with lock:
                current = read_job(job_id) or jobs.get(job_id) or {}
                if current and current.get("status") not in {"completed", "failed"}:
                    current["status"] = "failed"
                    current["error"] = f"isolated training worker exited with code {returncode}"
                    current["finished_at"] = _utc_now()
                    jobs[job_id] = current
                    persist_job(current)

        threading.Thread(target=_reap_worker, daemon=True).start()

    def _cache_get_reading_payload(reading_id: str) -> dict[str, object] | None:
        if cache is None:
            return None
        try:
            return cache.get_reading_payload(reading_id)
        except Exception:
            return None

    def _cache_get_trace_payload(trace_id: str) -> dict[str, object] | None:
        if cache is None:
            return None
        try:
            return cache.get_trace_payload(trace_id)
        except Exception:
            return None

    def _cache_store_runtime(runtime: CoreRuntimeResult) -> None:
        if cache is None:
            return
        try:
            cache.set_reading(runtime)
            cache.set_trace(runtime)
        except Exception:
            return

    def _load_runtime_for_reading(reading_id: str) -> CoreRuntimeResult:
        payload = _cache_get_reading_payload(reading_id)
        payload = payload or repository.get_runtime_payload(reading_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="reading not found")
        runtime = CoreRuntimeResult.model_validate(payload)
        return _runtime_with_hidden_factor_state(runtime, hidden_factor_states)

    def _lightweight_await_new_evidence_status() -> dict[str, object]:
        source_ids = [
            "real_case_calibration",
            "business_acceptance",
            "518k_distribution",
            "training_signal_distribution",
            "llm_expression_acceptance",
            "question_chain_acceptance",
        ]
        return {
            "version": "v30.await_new_calibration_evidence_status.v1",
            "status": "completed",
            "decision": {
                "decision_status": "await_new_calibration_evidence_ready",
                "await_new_evidence_ready": True,
                "waiting_for_new_calibration_evidence": True,
                "focused_fix_candidate_count": 0,
                "focused_module_fix_required": False,
                "core_module_reopen_by_default": False,
                "full_pytest_required": False,
                "synthetic_all_required": False,
                "full_518k_required": False,
                "live_llm_required": False,
                "policy_pointer_promotion_allowed": False,
                "pointer_write_performed": False,
                "chart_fact_mutation_allowed": False,
            },
            "wait_policy": {
                "accepted_evidence_sources": source_ids,
                "new_evidence_entrypoint": "E-S1 Evidence-Driven Calibration Queue",
                "core_module_reopen_by_default": False,
                "chart_fact_mutation_allowed": False,
                "policy_pointer_promotion_allowed": False,
            },
            "runtime_mode": "lightweight_admin_projection",
            "boundary": "lightweight_await_status_projects_current_wait_state_without_running_heavy_sample_gates",
        }

    def _lightweight_synthetic_archetype_closeout_status() -> dict[str, object]:
        return {
            "version": "v30.synthetic_archetype_calibration_closeout.v1",
            "status": "completed",
            "decision": {
                "decision_status": "syn_cal4_synthetic_archetype_calibration_closed",
                "synthetic_archetype_calibration_closed": True,
                "closeout_check_count": 6,
                "passed_closeout_check_count": 6,
                "training_signal_count": 4,
                "queued_item_count": 0,
                "external_release_allowed": False,
                "chart_fact_mutation_allowed": False,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "full_pytest_required": False,
                "synthetic_all_required": False,
                "full_518k_required": False,
                "live_llm_required": False,
            },
            "routine_cadence": {
                "routine_targeted_commands": [
                    "python3 scripts/run_synthetic_validation.py --tier synthetic_archetype_rule_claim",
                    "python3 scripts/run_synthetic_archetype_training_signal_review.py",
                    "python3 scripts/run_synthetic_archetype_calibration_closeout.py",
                ],
            },
            "runtime_mode": "lightweight_admin_projection",
            "boundary": "lightweight_syn_cal4_status_projects_closed_state_without_running_training_replay",
        }

    def _save_hidden_factor_feedback_payload(
        *,
        runtime: CoreRuntimeResult,
        payload: dict[str, object],
    ) -> dict[str, object] | None:
        if not payload:
            return None
        calibration_payload = runtime.question_plan.policy_effect.get("hidden_factor_calibration", {})
        feedback = hidden_factor_feedback_from_payload(
            reading_id=runtime.reading_id,
            context_id=runtime.chart_context.context_id,
            payload=payload,
        )
        incoming = build_hidden_factor_state(
            reading_id=runtime.reading_id,
            context_id=runtime.chart_context.context_id,
            calibration=HiddenFactorCalibration.model_validate(calibration_payload),
            feedback=[feedback],
        )
        existing_payload = hidden_factor_states.get_state_payload(incoming.state_id)
        existing = HiddenFactorState.model_validate(existing_payload) if existing_payload else None
        state = merge_hidden_factor_state(existing, incoming)
        hidden_factor_states.save_state(state)
        return state.model_dump(mode="json")

    def _process_alive(pid: object) -> bool:
        try:
            value = int(pid)
        except (TypeError, ValueError):
            return False
        if value <= 0:
            return False
        try:
            os.kill(value, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def _parse_datetime(value: str) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _maybe_mark_m3_job_stale(job: dict[str, object]) -> dict[str, object]:
        if job.get("status") != "running":
            return job
        if job.get("worker_mode") in {"external_tmux", "service_thread", "thread_supervised_process"}:
            return job
        worker_pid = job.get("worker_pid")
        if worker_pid and _process_alive(worker_pid):
            return job
        if worker_pid:
            job["status"] = "stale"
            job["error"] = "background worker process is no longer running"
        else:
            started = _parse_datetime(str(job.get("step_started_at") or job.get("started_at") or ""))
            if started is None or (datetime.now(timezone.utc) - started).total_seconds() < 60:
                return job
            job["status"] = "stale"
            job["error"] = "background worker pid was not recorded and job stopped updating"
        job["finished_at"] = _utc_now()
        job["stale_recovery"] = "start a new M3 background task; previous partial results remain in this job file"
        _persist_m3_background_job(job)
        return job

    def _run_m3_background_process(
        *,
        job_id: str,
        command: list[str],
        log_path: Path,
    ) -> None:
        process: subprocess.Popen[bytes] | None = None
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            env = dict(os.environ)
            env["V30_REPOSITORY"] = "local_json"
            env.pop("V30_DATABASE_URL", None)
            env["V30_ADMIN_CONFIG_PATH"] = str(settings.runtime_dir / "training" / "m3_background_no_db_admin_config.json")
            with log_path.open("ab") as log_file:
                process = subprocess.Popen(
                    command,
                    cwd=Path(__file__).resolve().parents[2],
                    env=env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                with m3_background_lock:
                    job = _read_m3_background_job(job_id) or m3_background_jobs.get(job_id) or {}
                    if job:
                        job["worker_pid"] = process.pid
                        job["worker_mode"] = "thread_supervised_process"
                        m3_background_jobs[job_id] = job
                        _persist_m3_background_job(job)
                returncode = process.wait()
        except OSError as exc:
            with m3_background_lock:
                job = _read_m3_background_job(job_id) or m3_background_jobs.get(job_id) or {}
                if job:
                    job["status"] = "failed"
                    job["error"] = str(exc)
                    job["finished_at"] = _utc_now()
                    m3_background_jobs[job_id] = job
                    _persist_m3_background_job(job)
            return

        with m3_background_lock:
            job = _read_m3_background_job(job_id) or m3_background_jobs.get(job_id) or {}
            if not job:
                return
            if returncode != 0 and job.get("status") not in {"completed", "failed"}:
                job["status"] = "failed"
                job["error"] = f"background worker exited with code {returncode}"
                job["finished_at"] = _utc_now()
                m3_background_jobs[job_id] = job
                _persist_m3_background_job(job)
            elif job.get("status") == "running":
                job["status"] = "stale"
                job["error"] = "background worker exited before writing a final status"
                job["finished_at"] = _utc_now()
                job["stale_recovery"] = "inspect log_tail and restart the M3 background task"
                m3_background_jobs[job_id] = job
                _persist_m3_background_job(job)

    def _m3_step_result(name: str, payload: object) -> dict[str, object]:
        if isinstance(payload, dict) and "stdout" in payload:
            stdout = str(payload.get("stdout") or "").strip()
            return {
                "step": name,
                "command": payload.get("command"),
                "returncode": payload.get("returncode"),
                "stdout": stdout[-1200:],
                "stderr": str(payload.get("stderr") or "").strip()[-1200:],
                "timeout_sec": payload.get("timeout_sec"),
                "recovered_from_timeout": payload.get("recovered_from_timeout", False),
                "recovery_reason": payload.get("recovery_reason", ""),
                "primary_error": payload.get("primary_error", ""),
            }
        if name == "m3_snapshot" and isinstance(payload, dict):
            inventory = payload.get("inventory", {})
            db_write = payload.get("db_write", {})
            synthetic = payload.get("synthetic_validation", {})
            return {
                "step": name,
                "snapshot_id": payload.get("snapshot_id"),
                "artifact_uri": payload.get("artifact_uri"),
                "krp_unit_count": inventory.get("krp_unit_count") if isinstance(inventory, dict) else None,
                "rule_spec_count": inventory.get("rule_spec_count") if isinstance(inventory, dict) else None,
                "portrait_asset_count": inventory.get("portrait_asset_count") if isinstance(inventory, dict) else None,
                "synthetic": {
                    "passed": synthetic.get("passed") if isinstance(synthetic, dict) else None,
                    "passed_count": synthetic.get("passed_count") if isinstance(synthetic, dict) else None,
                    "case_count": synthetic.get("case_count") if isinstance(synthetic, dict) else None,
                },
                "db_write": db_write if isinstance(db_write, dict) else {},
                "recovered_from_timeout": payload.get("recovered_from_timeout", False),
                "recovery_reason": payload.get("recovery_reason", ""),
                "primary_error": payload.get("primary_error", ""),
            }
        if name in {"m3_synthetic", "training_pipeline"} and hasattr(payload, "model_dump"):
            data = payload.model_dump(mode="json")
            return {
                "step": name,
                "suite_id": data.get("suite_id"),
                "passed": data.get("passed"),
                "passed_count": data.get("passed_count"),
                "case_count": data.get("case_count"),
            }
        if name in {"518k_sample", "518k_shard"} and hasattr(payload, "model_dump"):
            data = payload.model_dump(mode="json")
            return {
                "step": name,
                "run_id": data.get("run_id"),
                "mode": data.get("mode"),
                "promotion_signal": data.get("promotion_signal"),
                "case_count": data.get("case_count"),
                "shard_ids": data.get("shard_ids"),
                "artifact_uri": data.get("artifact_uri"),
                "index_uri": data.get("index_uri"),
                "artifact_record_id": data.get("artifact_record_id"),
                "artifact_search_backend": data.get("artifact_search_backend"),
            }
        if name == "518k_readiness_matrix" and isinstance(payload, dict):
            checks = payload.get("checks", [])
            return {
                "step": name,
                "version": payload.get("version"),
                "passed": payload.get("passed"),
                "check_count": len(checks) if isinstance(checks, list) else None,
            }
        return {"step": name, "summary": str(payload)[:500]}

    def _run_m3_background_command(args: list[str], *, timeout_sec: int) -> dict[str, object]:
        env = dict(os.environ)
        env["V30_REPOSITORY"] = "local_json"
        env.pop("V30_DATABASE_URL", None)
        env["V30_ADMIN_CONFIG_PATH"] = str(settings.runtime_dir / "training" / "m3_background_no_db_admin_config.json")
        try:
            completed = subprocess.run(
                args,
                cwd=Path(__file__).resolve().parents[2],
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"Command '{' '.join(args)}' timed out after {timeout_sec} seconds") from exc
        payload = {
            "command": " ".join(args),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timeout_sec": timeout_sec,
        }
        if completed.returncode != 0:
            raise RuntimeError(
                f"{payload['command']} failed with code {completed.returncode}: "
                f"{(completed.stderr or completed.stdout).strip()[-500:]}"
            )
        return payload

    def _run_m3_background_snapshot(
        *,
        sample_limit: int,
        persist_requested: bool,
    ) -> dict[str, object]:
        db_status = database_admin_status()
        counts = db_status.get("counts", {}) if isinstance(db_status, dict) else {}
        artifact_dir = settings.runtime_dir / "validation" / "m3"
        latest_artifact = ""
        try:
            artifacts = sorted(artifact_dir.glob("v30.m3.snapshot.*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
            latest_artifact = str(artifacts[0]) if artifacts else ""
        except OSError:
            latest_artifact = ""
        return {
            "version": "v30.m3_background_snapshot_summary.v1",
            "snapshot_id": f"v30.m3.background.snapshot.{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            "artifact_uri": latest_artifact,
            "inventory": {
                "krp_unit_count": int(counts.get("v30_m3_knowledge_units") or 0),
                "rule_spec_count": int(counts.get("v30_m3_rule_specs") or 0),
                "portrait_asset_count": int(counts.get("v30_m3_portrait_assets") or 0),
                "validation_snapshot_count": int(counts.get("v30_m3_validation_snapshots") or 0),
            },
            "synthetic_validation": {
                "passed": None,
                "passed_count": None,
                "case_count": None,
                "reason": "m3_synthetic_runs_as_next_background_step",
            },
            "db_write": {
                "requested": persist_requested,
                "backend": "postgres_status_observed",
                "searchable": bool(counts.get("v30_m3_knowledge_units")),
                "reason": "background_snapshot_step_observes_existing_postgres_m3_tables_without_blocking_upsert",
            },
            "db_status": db_status,
            "sample_limit": sample_limit,
            "boundary": "m3_background_snapshot_is_nonblocking_status_summary_not_policy_promotion",
        }

    @contextmanager
    def _m3_background_validation_env():
        keys = ("V30_ADMIN_CONFIG_PATH", "V30_REPOSITORY", "V30_DATABASE_URL")
        previous = {key: os.environ.get(key) for key in keys}
        os.environ["V30_ADMIN_CONFIG_PATH"] = str(settings.runtime_dir / "training" / "m3_background_no_db_admin_config.json")
        os.environ["V30_REPOSITORY"] = "local_json"
        os.environ.pop("V30_DATABASE_URL", None)
        try:
            yield
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def _run_m3_background_synthetic_tier(tier: str) -> object:
        with _m3_background_validation_env():
            from v30.validation import run_synthetic_tier

            return run_synthetic_tier(tier)

    def _run_m3_background_518k_validation(**kwargs: object) -> object:
        with _m3_background_validation_env():
            from v30.validation import run_518k_validation

            return run_518k_validation(**kwargs)

    def _run_m3_background_518k_readiness_matrix(**kwargs: object) -> object:
        with _m3_background_validation_env():
            from v30.validation import run_518k_readiness_matrix

            return run_518k_readiness_matrix(**kwargs)

    def _run_m3_background_job(job_id: str) -> None:
        with m3_background_lock:
            job = m3_background_jobs[job_id]
            job["status"] = "running"
            job["started_at"] = _utc_now()
            _persist_m3_background_job(job)
        config = dict(job.get("config") or {})
        sample_limit = str(int(config["sample_limit"]))
        shard_id = str(int(config["shard_id"]))
        shard_limit = str(int(config["shard_limit"]))
        sample_limit_int = int(sample_limit)
        shard_id_int = int(shard_id)
        shard_limit_int = int(shard_limit)
        steps: list[tuple[str, object]] = [
            (
                "m3_snapshot",
                lambda: _run_m3_background_snapshot(
                    sample_limit=sample_limit_int,
                    persist_requested=bool(config.get("persist_m3_to_db")),
                ),
            ),
            ("m3_synthetic", lambda: _run_m3_background_synthetic_tier("m3_core_spine")),
            ("training_pipeline", lambda: _run_m3_background_synthetic_tier("training_pipeline")),
            ("518k_sample", lambda: _run_m3_background_518k_validation(mode="sample", limit=sample_limit_int)),
        ]
        if config.get("include_shard"):
            steps.append(
                (
                    "518k_shard",
                    lambda: _run_m3_background_518k_validation(
                        mode="shard",
                        shard_id=shard_id_int,
                        limit=shard_limit_int,
                    ),
                )
            )
        if config.get("include_readiness_matrix"):
            steps.append(
                (
                    "518k_readiness_matrix",
                    lambda: _run_m3_background_518k_readiness_matrix(
                        sample_limit=sample_limit_int,
                        shard_id=shard_id_int,
                        shard_limit=shard_limit_int,
                    ),
                )
            )
        total_steps = len(steps)
        for index, (step_name, runner) in enumerate(steps):
            with m3_background_lock:
                job = m3_background_jobs[job_id]
                job["current_step"] = step_name
                job["step_started_at"] = _utc_now()
                job["progress_percent"] = max(3, int((index / total_steps) * 100))
                _persist_m3_background_job(job)
            try:
                result = runner()
                summary = _m3_step_result(step_name, result)
            except TimeoutError as exc:
                if step_name != "m3_snapshot":
                    with m3_background_lock:
                        job = m3_background_jobs[job_id]
                        job["status"] = "failed"
                        job["error"] = str(exc)
                        job["failed_step"] = step_name
                        job["finished_at"] = _utc_now()
                        _persist_m3_background_job(job)
                    return
                try:
                    from scripts.run_m3_core_spine_snapshot import run_m3_core_spine_snapshot

                    result = run_m3_core_spine_snapshot(
                        sample_limit=sample_limit_int,
                        write_db=False,
                        artifact_dir=".runtime/validation/m3",
                    )
                    if isinstance(result, dict):
                        result["recovered_from_timeout"] = True
                        result["recovery_reason"] = "db_persistence_timeout_no_db_artifact_fallback"
                        result["primary_error"] = str(exc)
                    summary = _m3_step_result(step_name, result)
                except Exception as fallback_exc:  # pragma: no cover - defensive runtime status path
                    with m3_background_lock:
                        job = m3_background_jobs[job_id]
                        job["status"] = "failed"
                        job["error"] = str(fallback_exc)
                        job["failed_step"] = step_name
                        job["finished_at"] = _utc_now()
                        _persist_m3_background_job(job)
                    return
            except Exception as exc:  # pragma: no cover - defensive runtime status path
                with m3_background_lock:
                    job = m3_background_jobs[job_id]
                    job["status"] = "failed"
                    job["error"] = str(exc)
                    job["failed_step"] = step_name
                    job["finished_at"] = _utc_now()
                    _persist_m3_background_job(job)
                return
            with m3_background_lock:
                job = m3_background_jobs[job_id]
                results = list(job.get("results") or [])
                results.append(summary)
                job["results"] = results
                job["completed_steps"] = index + 1
                job["progress_percent"] = int(((index + 1) / total_steps) * 100)
                _persist_m3_background_job(job)
        with m3_background_lock:
            job = m3_background_jobs[job_id]
            job["status"] = "completed"
            job["current_step"] = "completed"
            job["finished_at"] = _utc_now()
            job["progress_percent"] = 100
            _persist_m3_background_job(job)

    @app.get(f"{API_PREFIX}/health")
    def health() -> dict[str, object]:
        return {
            "ok": True,
            "package": "v30",
            "api_prefix": API_PREFIX,
            "admin_api_prefix": ADMIN_API_PREFIX,
            "ui_prefix": UI_PREFIX,
            "runtime_dir": str(settings.runtime_dir),
            "repository": settings.repository,
            "redis_cache": cache is not None,
            "redis_probe_key": redis_key(settings.env, "lock", "health"),
        }

    @app.get(f"{ADMIN_API_PREFIX}/control-plane/manifest")
    def get_admin_control_plane_manifest(role: str = "viewer") -> dict[str, object]:
        return build_admin_control_plane_manifest(role=role).model_dump(mode="json")

    @app.post(f"{API_PREFIX}/auth/register")
    def register_user(payload: AuthRegisterRequest) -> dict[str, object]:
        store = product_store.load()
        username = _normalize_username(payload.username)
        if username in store["users"]:
            raise HTTPException(status_code=409, detail="username already exists")
        if len(payload.password) < 6:
            raise HTTPException(status_code=400, detail="password must be at least 6 characters")
        role = payload.role if payload.role in {"user", "practitioner"} else "user"
        if payload.role == "admin" or username == "admin":
            raise HTTPException(status_code=403, detail="admin account cannot be registered")
        actor_id = f"actor-{secrets.token_hex(6)}"
        user = {
            "username": username,
            "actor_id": actor_id,
            "display_name": payload.display_name or username,
            "role": role,
            "capabilities": _product_role_capabilities(role),
            "password": _hash_password(payload.password),
            "created_at": _utc_now(),
        }
        token = secrets.token_urlsafe(24)
        session = _new_product_session(user, token=token)
        store["users"][username] = user
        store["sessions"][token] = session
        product_store.save(store)
        return {
            "version": "v30.product_auth_session.v1",
            "status": "registered",
            "session": session,
            "user": _public_product_user(user),
            "boundary": "product_auth_does_not_change_chart_facts_or_runtime_projection_contract",
        }

    @app.post(f"{API_PREFIX}/auth/login")
    def login_user(payload: AuthLoginRequest) -> dict[str, object]:
        store = product_store.load()
        username = _normalize_username(payload.username)
        user = store["users"].get(username)
        if not isinstance(user, dict) or not _verify_product_password(payload.password, user):
            raise HTTPException(status_code=401, detail="invalid username or password")
        token = secrets.token_urlsafe(24)
        session = _new_product_session(user, token=token)
        store["sessions"][token] = session
        product_store.save(store)
        return {
            "version": "v30.product_auth_session.v1",
            "status": "logged_in",
            "session": session,
            "user": _public_product_user(user),
            "boundary": "product_auth_uses_actor_session_hooks_without_mutating_bazi_facts",
        }

    @app.get(f"{API_PREFIX}/auth/session")
    def get_auth_session(session_token: str = "") -> dict[str, object]:
        store = product_store.load()
        session = _require_product_session(store, session_token)
        user = store["users"].get(str(session.get("username") or ""))
        if not isinstance(user, dict):
            raise HTTPException(status_code=401, detail="session user not found")
        return {
            "version": "v30.product_auth_session.v1",
            "status": "active",
            "session": session,
            "user": _public_product_user(user),
            "boundary": "session_projection_does_not_authorize_chart_fact_mutation",
        }

    @app.post(f"{API_PREFIX}/auth/logout")
    def logout_user(payload: AuthLogoutRequest) -> dict[str, object]:
        store = product_store.load()
        removed = store["sessions"].pop(payload.session_token, None) is not None
        product_store.save(store)
        return {
            "version": "v30.product_auth_logout.v1",
            "status": "logged_out" if removed else "session_not_found",
            "boundary": "logout_removes_product_session_only",
        }

    @app.get(f"{API_PREFIX}/profiles")
    def list_bazi_profiles(session_token: str = "") -> dict[str, object]:
        store = product_store.load()
        session = _require_product_session(store, session_token)
        actor_id = str(session.get("actor_id") or "")
        profiles = [
            row for row in store["profiles"].values()
            if isinstance(row, dict) and row.get("actor_id") == actor_id
        ]
        profiles.sort(key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)
        profile_items = []
        for row in profiles:
            item = dict(row)
            item["bazi_preview"] = _profile_bazi_preview(item)
            profile_items.append(item)
        return {
            "version": "v30.bazi_profile_list.v1",
            "count": len(profiles),
            "items": profile_items,
            "boundary": "bazi_profiles_store_birth_input_metadata_with_readonly_chart_preview",
        }

    @app.post(f"{API_PREFIX}/profiles")
    def save_bazi_profile(payload: BaziProfileRequest) -> dict[str, object]:
        store = product_store.load()
        session = _require_product_session(store, payload.session_token)
        profile_id = payload.profile_id or f"profile-{secrets.token_hex(6)}"
        existing = store["profiles"].get(profile_id)
        if isinstance(existing, dict) and existing.get("actor_id") != session.get("actor_id"):
            raise HTTPException(status_code=403, detail="profile owner mismatch")
        profile = _bazi_profile_payload(profile_id=profile_id, payload=payload, session=session, existing=existing)
        store["profiles"][profile_id] = profile
        product_store.save(store)
        return {
            "version": "v30.bazi_profile.v1",
            "status": "saved",
            "profile": profile,
            "boundary": "profile_save_does_not_compute_or_mutate_chart_facts",
        }

    @app.get(f"{API_PREFIX}/ui/capabilities")
    def get_ui_capabilities() -> dict[str, object]:
        public_clients = ["web", "mobile"]
        public_roles = [
            {
                "key": "guest",
                "label": "游客",
                "default_client": "mobile",
                "surface": "preview",
                "diagnostics_visible": False,
                "capabilities": [],
            },
            {
                "key": "user",
                "label": "普通用户",
                "default_client": "web",
                "surface": "customer_reading",
                "diagnostics_visible": False,
                "capabilities": _product_role_capabilities("user"),
            },
            {
                "key": "practitioner",
                "label": "命理师",
                "default_client": "web",
                "surface": "practitioner_review",
                "diagnostics_visible": True,
                "capabilities": _product_role_capabilities("practitioner"),
            },
        ]
        return {
            "version": "v30.ui_capabilities.v1",
            "default_role": "user",
            "default_locale": "zh",
            "default_client": "web",
            "locales": [
                {"key": "zh", "label": "中文"},
                {"key": "en", "label": "English"},
                {"key": "ko", "label": "한국어"},
            ],
            "clients": [
                {
                    "key": key,
                    "label": {"web": "Web", "mobile": "Mobile"}[key],
                    "density": CLIENT_PROFILES[key].density,
                    "max_questions": CLIENT_PROFILES[key].max_questions,
                    "actions": CLIENT_PROFILES[key].actions,
                }
                for key in public_clients
            ],
            "roles": public_roles,
            "supported_view_params": {
                "role": [str(row["key"]) for row in public_roles],
                "locale": ["zh", "en", "ko"],
                "client": public_clients,
            },
            "api_contract": {
                "version": "v30.ui_api_contract.v1",
                "register": f"POST {API_PREFIX}/auth/register",
                "login": f"POST {API_PREFIX}/auth/login",
                "session": f"GET {API_PREFIX}/auth/session",
                "profiles": f"GET/POST {API_PREFIX}/profiles",
                "create_reading": f"POST {API_PREFIX}/readings",
                "view_reading": f"GET {API_PREFIX}/readings/{{reading_id}}/view",
                "answer_question": f"POST {API_PREFIX}/readings/{{reading_id}}/questions/{{question_id}}/answer",
                "enhance_answer_with_llm": f"POST {API_PREFIX}/readings/{{reading_id}}/questions/{{question_id}}/answer/llm",
                "structured_answer_fields": [
                    "submit_surface",
                    "submit_source_id",
                    "submit_contract_version",
                    "selected_option",
                    "structured_payload",
                    "confidence",
                    "feedback_tags",
                ],
                "structured_answer_contract": "v30.answer_constraints.v1",
                "surface_submit_contract": "v30.surface_submit_contract.v1",
                "valid_submit_surfaces": ["calibration_surface", "legacy_answer_endpoint"],
                "conversation_submit_endpoint": f"POST {API_PREFIX}/readings/{{reading_id}}/dialogues/{{dialogue_id}}/turns",
                "interaction_brain_result_contract": "v30.unified_interaction_brain_result.v1",
                "invalid_input_action": "ask_user_to_reselect",
                "diagnostic_summary_contract": "v30.interaction_brain_diagnostics_summary.v1",
                "synthetic_tier": "interaction_brain_structured_constraints",
                "dedicated_interactions_endpoint": "deferred_until_answer_endpoint_stable",
                "llm_answer_enhancement_mode": "blocking_llm_expression_default_fast_mode_explicit_only",
                "stable_surface_keys": ["reading_surface", "questions", "answer_panel", "diagnostics"],
                "boundary": "ui_api_contract_freezes_projection_shape_not_bazi_facts",
            },
            "boundary": "ui_capabilities_describe_projection_not_bazi_facts",
        }

    @app.post(f"{API_PREFIX}/readings")
    def create_reading(payload: ReadingRequest) -> dict[str, object]:
        birth_input_payload = getattr(payload, "birth_input", None)
        target_year = getattr(payload, "target_year", None)
        if birth_input_payload is not None:
            birth_input = BirthInput.model_validate(birth_input_payload)
            build_result = build_chart_context_from_birth_input(
                reading_id=payload.reading_id,
                birth_input=birth_input,
                locale=payload.locale,
                created_at=_target_datetime(target_year),
            )
            if build_result.chart_context is None:
                return {
                    "reading_id": payload.reading_id,
                    "status": build_result.status,
                    "chart_build": build_result.four_pillar_result.model_dump(mode="json"),
                    "failures": build_result.failures,
                }
            runtime = create_runtime_from_context(build_result.chart_context, trace_suffix="birth-input")
            runtime = _runtime_with_actor_context(runtime, payload)
            repository.save_runtime(runtime)
            repository.save_trace(runtime)
            _cache_store_runtime(runtime)
            return {
                "reading_id": runtime.reading_id,
                "trace_id": runtime.trace_id,
                "status": build_result.status,
                "chart_build": build_result.four_pillar_result.model_dump(mode="json"),
            }
        runtime = create_smoke_runtime(
            reading_id=payload.reading_id,
            day_master=payload.day_master,
            day_master_element=payload.day_master_element,
            locale=payload.locale,
        )
        runtime = _runtime_with_actor_context(runtime, payload)
        repository.save_runtime(runtime)
        repository.save_trace(runtime)
        _cache_store_runtime(runtime)
        return {"reading_id": runtime.reading_id, "trace_id": runtime.trace_id}

    @app.get(f"{API_PREFIX}/readings/history")
    def get_reading_history(
        actor_id: str = "",
        session_id: str = "",
        role: str = "user",
        locale: str = "zh",
        client: str = "web",
        limit: int = 20,
    ) -> dict[str, object]:
        diagnostic = _history_diagnostic_role(role)
        if not actor_id and not session_id:
            raise HTTPException(status_code=400, detail="actor_id or session_id is required")
        if not diagnostic and (not actor_id or not session_id):
            raise HTTPException(status_code=400, detail="actor_id and session_id are required for customer history")
        payloads = repository.list_runtime_payloads(
            actor_id=actor_id,
            session_id=session_id,
            limit=limit,
        )
        return _reading_history_projection(
            payloads,
            actor_id=actor_id,
            session_id=session_id,
            role=role,
            locale=locale,
            client=client,
            limit=limit,
        )

    @app.get(f"{API_PREFIX}/readings/{{reading_id}}")
    def get_reading(reading_id: str) -> dict[str, object]:
        payload = _cache_get_reading_payload(reading_id)
        payload = payload or repository.get_runtime_payload(reading_id)
        if payload is None:
            runtime = create_smoke_runtime(reading_id=reading_id)
            repository.save_runtime(runtime)
            repository.save_trace(runtime)
            _cache_store_runtime(runtime)
            return runtime.model_dump(mode="json")
        return payload

    @app.get(f"{API_PREFIX}/readings/{{reading_id}}/view")
    def get_reading_view(
        reading_id: str,
        role: str = "user",
        locale: str = "zh",
        client: str = "web",
    ) -> dict[str, object]:
        payload = _cache_get_reading_payload(reading_id)
        payload = payload or repository.get_runtime_payload(reading_id)
        if payload is None:
            runtime = create_smoke_runtime(reading_id=reading_id, locale=locale)
            repository.save_runtime(runtime)
            repository.save_trace(runtime)
            _cache_store_runtime(runtime)
        else:
            runtime = CoreRuntimeResult.model_validate(payload)
        runtime = _runtime_with_hidden_factor_state(runtime, hidden_factor_states)
        view = build_presentation_model(runtime, role_key=role, locale=locale, client=client)
        return view.model_dump(mode="json")

    @app.get(f"{API_PREFIX}/readings/{{reading_id}}/dialogue-seeds")
    def get_dialogue_seeds(
        reading_id: str,
        role: str = "user",
        locale: str = "zh",
        client: str = "web",
    ) -> dict[str, object]:
        runtime = _load_runtime_for_reading(reading_id)
        seeds = build_dialogue_seed_suggestions(runtime)
        return {
            "version": "v30.dialogue_seed_api.v1",
            "reading_id": reading_id,
            "role": role,
            "locale": locale,
            "client": client,
            "items": seeds,
            "boundary": "dialogue_seed_api_starts_independent_dialogue_sessions_not_chart_facts",
        }

    @app.get(f"{API_PREFIX}/readings/{{reading_id}}/dialogues")
    def list_dialogues(reading_id: str, limit: int = 20) -> dict[str, object]:
        sessions = dialogue_store.list_sessions(reading_id, limit=limit)
        return {
            "version": "v30.dialogue_session_list_api.v1",
            "reading_id": reading_id,
            "count": len(sessions),
            "items": [session.model_dump(mode="json") for session in sessions],
            "boundary": "dialogue_session_list_reads_conversation_memory_not_chart_facts",
        }

    @app.post(f"{API_PREFIX}/readings/{{reading_id}}/dialogues")
    def create_dialogue(reading_id: str, payload: DialogueCreateRequest) -> dict[str, object]:
        with _answer_interaction_lock(reading_id):
            runtime = _load_runtime_for_reading(reading_id)
            session = start_dialogue_session(
                runtime,
                payload.seed_text,
                source=payload.source,
                role_key=payload.role or runtime.question_plan.role_key,
                locale=payload.locale or runtime.chart_context.locale,
                client=payload.client or "web",
                stage_id=payload.stage_id,
            )
            dialogue_store.save_session(session)
            return {
                "version": "v30.dialogue_session_create_api.v1",
                "reading_id": reading_id,
                "dialogue_id": session.dialogue_id,
                "session": session.model_dump(mode="json"),
                "answer_interaction_serialized": True,
                "boundary": "dialogue_create_starts_independent_session_without_mutating_runtime_chart_facts",
            }

    @app.get(f"{API_PREFIX}/readings/{{reading_id}}/dialogues/{{dialogue_id}}")
    def get_dialogue(reading_id: str, dialogue_id: str) -> dict[str, object]:
        session = dialogue_store.get_session(reading_id, dialogue_id)
        if session is None:
            raise HTTPException(status_code=404, detail="dialogue not found")
        return {
            "version": "v30.dialogue_session_get_api.v1",
            "reading_id": reading_id,
            "dialogue_id": dialogue_id,
            "session": session.model_dump(mode="json"),
            "boundary": "dialogue_get_reads_conversation_memory_not_chart_facts",
        }

    @app.post(f"{API_PREFIX}/readings/{{reading_id}}/dialogues/{{dialogue_id}}/turns")
    def create_dialogue_turn(
        reading_id: str,
        dialogue_id: str,
        payload: DialogueTurnRequest,
    ) -> dict[str, object]:
        with _answer_interaction_lock(reading_id):
            runtime = _load_runtime_for_reading(reading_id)
            session = dialogue_store.get_session(reading_id, dialogue_id)
            if session is None:
                raise HTTPException(status_code=404, detail="dialogue not found")
            session = append_dialogue_turn(
                runtime,
                session,
                text=payload.text,
                selected_option=payload.selected_option,
                structured_payload=payload.structured_payload,
                role_key=payload.role or runtime.question_plan.role_key,
                locale=payload.locale or runtime.chart_context.locale,
                client=payload.client or "web",
                source="user",
                stage_id=payload.stage_id,
            )
            dialogue_store.save_session(session)
            return {
                "version": "v30.dialogue_turn_create_api.v1",
                "reading_id": reading_id,
                "dialogue_id": dialogue_id,
                "session": session.model_dump(mode="json"),
                "answer_interaction_serialized": True,
                "boundary": "dialogue_turn_appends_conversation_memory_without_mutating_runtime_chart_facts",
            }

    @app.get(f"{API_PREFIX}/readings/{{reading_id}}/thinking")
    def get_reading_thinking(reading_id: str) -> dict[str, object]:
        payload = _cache_get_reading_payload(reading_id)
        payload = payload or repository.get_runtime_payload(reading_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="reading not found")
        runtime = CoreRuntimeResult.model_validate(payload)
        runtime = _runtime_with_hidden_factor_state(runtime, hidden_factor_states)
        with practitioner_selection_lock:
            selections = list(practitioner_selection_store.get(reading_id, []))
        return apply_practitioner_selection_effects_to_thinking(build_thinking_projection(runtime), selections)

    @app.get(f"{API_PREFIX}/readings/{{reading_id}}/production-audit")
    def get_reading_production_audit(
        reading_id: str,
        role: str = "admin",
        locale: str = "zh",
        client: str = "admin",
        include_thinking: bool = False,
    ) -> dict[str, object]:
        payload = _cache_get_reading_payload(reading_id)
        payload = payload or repository.get_runtime_payload(reading_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="reading not found")
        runtime = CoreRuntimeResult.model_validate(payload)
        runtime = _runtime_with_hidden_factor_state(runtime, hidden_factor_states)
        view = build_presentation_model(runtime, role_key=role, locale=locale, client=client).model_dump(mode="json")
        thinking = build_thinking_projection(runtime) if include_thinking else {}
        central = runtime.question_plan.policy_effect.get("central_reading_state", {})
        central = central if isinstance(central, dict) else {}
        sidecar = build_production_sidecar(
            reading_id=runtime.reading_id,
            feature_evidence=runtime.feature_evidence,
            macro_signals=_list(runtime.question_plan.policy_effect.get("macro_dimension_signals")),
            ranked_decisions=_dict(runtime.question_plan.policy_effect.get("ranked_decisions")),
            practical_context=_dict(runtime.question_plan.policy_effect.get("practical_reading_context")),
            diagnosis=_dict(runtime.question_plan.policy_effect.get("real_bazi_diagnosis")),
            central_state=central,
            decision_result=_dict(central.get("decision_result")),
            final_synthesis=_dict(central.get("final_synthesis")),
            reading_surface=_dict(view.get("reading_surface")),
            thinking_projection=thinking if isinstance(thinking, dict) else {},
        )
        runtime_sidecar = runtime.question_plan.policy_effect.get("production_sidecar", {})
        runtime_sidecar = runtime_sidecar if isinstance(runtime_sidecar, dict) else {}
        return {
            "version": "v30.production_audit_api.v1",
            "reading_id": reading_id,
            "role": role,
            "locale": locale,
            "client": client,
            "include_thinking": include_thinking,
            "runtime_sidecar_summary": runtime_sidecar.get("summary", {}),
            "sidecar": sidecar.model_dump(mode="json"),
            "boundary": "production_audit_endpoint_is_read_only_and_does_not_mutate_decision_or_chart_facts",
        }

    @app.get(f"{ADMIN_API_PREFIX}/readings/{{reading_id}}/production-audit")
    def get_admin_control_plane_production_audit(
        reading_id: str,
        role: str = "admin",
        locale: str = "zh",
        client: str = "admin",
        include_thinking: bool = False,
    ) -> dict[str, object]:
        return get_reading_production_audit(
            reading_id,
            role=role,
            locale=locale,
            client=client,
            include_thinking=include_thinking,
        )

    @app.get(f"{API_PREFIX}/readings/{{reading_id}}/practitioner/options")
    def get_practitioner_option_state(
        reading_id: str,
        role: str = "practitioner",
    ) -> dict[str, object]:
        payload = _cache_get_reading_payload(reading_id)
        payload = payload or repository.get_runtime_payload(reading_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="reading not found")
        runtime = CoreRuntimeResult.model_validate(payload)
        runtime = _runtime_with_hidden_factor_state(runtime, hidden_factor_states)
        with practitioner_selection_lock:
            selections = list(practitioner_selection_store.get(reading_id, []))
        thinking = apply_practitioner_selection_effects_to_thinking(build_thinking_projection(runtime), selections)
        return build_practitioner_interaction_state(reading_id, thinking, selections, role_key=role)

    @app.post(f"{API_PREFIX}/readings/{{reading_id}}/practitioner/selections")
    def create_practitioner_selection(
        reading_id: str,
        payload: PractitionerSelectionRequest,
    ) -> dict[str, object]:
        runtime_payload = _cache_get_reading_payload(reading_id)
        runtime_payload = runtime_payload or repository.get_runtime_payload(reading_id)
        if runtime_payload is None:
            raise HTTPException(status_code=404, detail="reading not found")
        runtime = CoreRuntimeResult.model_validate(runtime_payload)
        runtime = _runtime_with_hidden_factor_state(runtime, hidden_factor_states)
        thinking = build_thinking_projection(runtime)
        option_set = find_option_set(thinking, payload.option_set_id, role_key="practitioner")
        if option_set is None:
            raise HTTPException(status_code=404, detail="option set not found")
        selection = build_practitioner_selection_record(
            option_set,
            selected_option_ids=payload.selected_option_ids,
            ranked_option_ids=payload.ranked_option_ids,
            rejected_option_ids=payload.rejected_option_ids,
            action=payload.action,
            note=payload.note,
            confidence=payload.confidence,
            actor_id=payload.actor_id,
        )
        with practitioner_selection_lock:
            rows = practitioner_selection_store.setdefault(reading_id, [])
            rows.append(selection)
            selections = list(rows)
        enhanced_thinking = apply_practitioner_selection_effects_to_thinking(thinking, selections)
        state = build_practitioner_interaction_state(reading_id, enhanced_thinking, selections, role_key="practitioner")
        central_reading_state = _central_state_with_practitioner_selections(runtime, selections)
        return {
            "version": "v30.practitioner_selection_api_result.v1",
            "reading_id": reading_id,
            "accepted": True,
            "selection": selection,
            "interaction_state": state,
            "thinking": enhanced_thinking,
            "central_reading_state": central_reading_state,
            "central_feedback_overlay": central_reading_state.get("central_feedback_overlay", {}),
            "chart_fact_mutation_allowed": False,
            "boundary": "practitioner_selection_api_updates_interpretation_overlay_not_chart_facts",
        }

    @app.post(f"{API_PREFIX}/readings/{{reading_id}}/thinking/{{step_id}}/summary/llm")
    def enhance_thinking_step_summary(
        reading_id: str,
        step_id: str,
        payload: LLMThinkingSummaryRequest,
    ) -> dict[str, object]:
        runtime_payload = _cache_get_reading_payload(reading_id)
        runtime_payload = runtime_payload or repository.get_runtime_payload(reading_id)
        if runtime_payload is None:
            raise HTTPException(status_code=404, detail="reading not found")
        runtime = CoreRuntimeResult.model_validate(runtime_payload)
        runtime = _runtime_with_hidden_factor_state(runtime, hidden_factor_states)
        thinking = build_thinking_projection(runtime)
        steps = thinking.get("steps")
        if not isinstance(steps, list):
            raise HTTPException(status_code=409, detail="thinking projection is not ready")
        step = next((row for row in steps if isinstance(row, dict) and row.get("step_id") == step_id), None)
        if step is None:
            raise HTTPException(status_code=404, detail="thinking step not found")
        policy = step.get("summary_policy") if isinstance(step.get("summary_policy"), dict) else {}
        if policy.get("llm_enhancement") != "auto":
            call = _thinking_summary_policy_skipped_call(step, policy)
        else:
            call = call_bazi_llm_thinking_step_summary(
                runtime,
                step,
                role_key=payload.role or runtime.question_plan.role_key,
                locale=payload.locale or runtime.chart_context.locale,
                client=payload.client or "web",
                config=load_v30_llm_provider_config_from_env(),
            )
            call = _thinking_summary_required_unavailable_call(call, policy)
        summary_panel = dict(step.get("summary_panel") if isinstance(step.get("summary_panel"), dict) else {})
        if call.get("status") == "accepted":
            summary_panel.update(
                {
                    "body": str(call.get("text") or summary_panel.get("body") or ""),
                    "source": "central_brain_llm_expression",
                    "llm_metadata": call,
                }
            )
        else:
            summary_panel.update(
                {
                    "source": _thinking_summary_panel_source(summary_panel, call),
                    "llm_metadata": call,
                }
            )
        enhanced_step = _step_with_llm_final_decision(step, summary_panel, call)
        return {
            "reading_id": reading_id,
            "step_id": step_id,
            "accepted": call.get("status") == "accepted",
            "summary_panel": summary_panel,
            "step": enhanced_step,
            "llm_metadata": call,
            "boundary": "thinking_step_summary_llm_endpoint_expression_only_no_runtime_mutation",
        }

    @app.post(f"{API_PREFIX}/readings/{{reading_id}}/thinking/{{step_id}}/summary/llm/stream")
    def stream_thinking_step_summary(
        reading_id: str,
        step_id: str,
        payload: LLMThinkingSummaryRequest,
    ) -> StreamingResponse:
        runtime_payload = _cache_get_reading_payload(reading_id)
        runtime_payload = runtime_payload or repository.get_runtime_payload(reading_id)
        if runtime_payload is None:
            raise HTTPException(status_code=404, detail="reading not found")
        runtime = CoreRuntimeResult.model_validate(runtime_payload)
        runtime = _runtime_with_hidden_factor_state(runtime, hidden_factor_states)
        thinking = build_thinking_projection(runtime)
        steps = thinking.get("steps")
        if not isinstance(steps, list):
            raise HTTPException(status_code=409, detail="thinking projection is not ready")
        step = next((row for row in steps if isinstance(row, dict) and row.get("step_id") == step_id), None)
        if step is None:
            raise HTTPException(status_code=404, detail="thinking step not found")
        policy = step.get("summary_policy") if isinstance(step.get("summary_policy"), dict) else {}

        def event_rows():
            call: dict[str, object] | None = None
            if policy.get("llm_enhancement") != "auto":
                call = _thinking_summary_policy_skipped_call(step, policy)
                summary_panel = dict(step.get("summary_panel") if isinstance(step.get("summary_panel"), dict) else {})
                summary_panel.update(
                    {
                        "source": _thinking_summary_panel_source(summary_panel, call),
                        "llm_metadata": call,
                    }
                )
                enhanced_step = _step_with_llm_final_decision(step, summary_panel, call)
                yield json.dumps(
                    {
                        "event": "final_step",
                        "reading_id": reading_id,
                        "step_id": step_id,
                        "accepted": False,
                        "step": enhanced_step,
                        "summary_panel": summary_panel,
                        "llm_metadata": call,
                        "boundary": "thinking_step_summary_stream_policy_skipped_without_llm",
                    },
                    ensure_ascii=False,
                ) + "\n"
                return
            for event in stream_bazi_llm_thinking_step_summary_events(
                runtime,
                step,
                role_key=payload.role or runtime.question_plan.role_key,
                locale=payload.locale or runtime.chart_context.locale,
                client=payload.client or "web",
                config=load_v30_llm_provider_config_from_env(),
            ):
                if event.get("event") == "final_call":
                    call = event.get("call") if isinstance(event.get("call"), dict) else {}
                    call = _thinking_summary_required_unavailable_call(call, policy)
                    summary_panel = dict(step.get("summary_panel") if isinstance(step.get("summary_panel"), dict) else {})
                    if call.get("status") == "accepted":
                        summary_panel.update(
                            {
                                "body": str(call.get("text") or summary_panel.get("body") or ""),
                                "source": "central_brain_llm_expression",
                                "llm_metadata": call,
                            }
                        )
                    else:
                        summary_panel.update(
                            {
                                "source": _thinking_summary_panel_source(summary_panel, call),
                                "llm_metadata": call,
                            }
                        )
                    enhanced_step = _step_with_llm_final_decision(step, summary_panel, call)
                    yield json.dumps(
                        {
                            "event": "final_step",
                            "reading_id": reading_id,
                            "step_id": step_id,
                            "accepted": call.get("status") == "accepted",
                            "step": enhanced_step,
                            "summary_panel": summary_panel,
                            "llm_metadata": call,
                            "boundary": "thinking_step_summary_stream_final_after_ollama_thinking",
                        },
                        ensure_ascii=False,
                    ) + "\n"
                else:
                    yield json.dumps(event, ensure_ascii=False) + "\n"
            if call is None:
                yield json.dumps(
                    {
                        "event": "stream_error",
                        "step_id": step_id,
                        "error": "missing_final_call",
                        "boundary": "thinking_step_summary_stream_requires_final_call",
                    },
                    ensure_ascii=False,
                ) + "\n"

        return StreamingResponse(event_rows(), media_type="application/x-ndjson")

    @app.post(f"{API_PREFIX}/readings/{{reading_id}}/thinking/summary/llm")
    def enhance_thinking_summaries(
        reading_id: str,
        payload: LLMThinkingBatchSummaryRequest,
    ) -> dict[str, object]:
        runtime_payload = _cache_get_reading_payload(reading_id)
        runtime_payload = runtime_payload or repository.get_runtime_payload(reading_id)
        if runtime_payload is None:
            raise HTTPException(status_code=404, detail="reading not found")
        runtime = CoreRuntimeResult.model_validate(runtime_payload)
        runtime = _runtime_with_hidden_factor_state(runtime, hidden_factor_states)
        thinking = build_thinking_projection(runtime)
        steps = thinking.get("steps")
        if not isinstance(steps, list):
            raise HTTPException(status_code=409, detail="thinking projection is not ready")
        requested_ids = {str(row) for row in payload.step_ids if str(row)}
        selected_steps = [
            row for row in steps
            if isinstance(row, dict) and (not requested_ids or str(row.get("step_id") or "") in requested_ids)
        ][: payload.max_steps]
        config = load_v30_llm_provider_config_from_env()
        enhanced_by_id: dict[str, dict[str, object]] = {}
        calls: list[dict[str, object]] = []
        for step in selected_steps:
            step_id = str(step.get("step_id") or "")
            policy = step.get("summary_policy") if isinstance(step.get("summary_policy"), dict) else {}
            if policy.get("llm_enhancement") != "auto":
                call = _thinking_summary_policy_skipped_call(step, policy)
            else:
                call = call_bazi_llm_thinking_step_summary(
                    runtime,
                    step,
                    role_key=payload.role or runtime.question_plan.role_key,
                    locale=payload.locale or runtime.chart_context.locale,
                    client=payload.client or "web",
                    config=config,
                )
                call = _thinking_summary_required_unavailable_call(call, policy)
            summary_panel = dict(step.get("summary_panel") if isinstance(step.get("summary_panel"), dict) else {})
            if call.get("status") == "accepted":
                summary_panel.update(
                    {
                        "body": str(call.get("text") or summary_panel.get("body") or ""),
                        "source": "central_brain_llm_expression",
                        "llm_metadata": call,
                    }
                )
            else:
                summary_panel.update(
                    {
                        "source": _thinking_summary_panel_source(summary_panel, call),
                        "llm_metadata": call,
                    }
                )
            enhanced_by_id[step_id] = _step_with_llm_final_decision(step, summary_panel, call)
            calls.append(call)
        enhanced_steps = [
            enhanced_by_id.get(str(row.get("step_id") or ""), row) if isinstance(row, dict) else row
            for row in steps
        ]
        accepted_count = sum(1 for call in calls if call.get("status") == "accepted")
        thinking = {
            **thinking,
            "steps": enhanced_steps,
            "llm_summary_batch": {
                "version": "v30.thinking_summary_llm_batch.v1",
                "requested_step_count": len(selected_steps),
                "accepted_count": accepted_count,
                "fallback_count": len(calls) - accepted_count,
                "executed_count": sum(1 for call in calls if call.get("executed")),
                "model": config.model,
                "provider": config.provider,
                "boundary": "batch_summary_expression_only_no_runtime_or_chart_fact_mutation",
            },
        }
        return {
            "reading_id": reading_id,
            "accepted_count": accepted_count,
            "fallback_count": len(calls) - accepted_count,
            "thinking": thinking,
            "calls": calls,
            "boundary": "thinking_summary_llm_batch_endpoint_expression_only_no_runtime_mutation",
        }

    @app.post(f"{API_PREFIX}/readings/{{reading_id}}/questions/{{question_id}}/answer")
    def answer_question(reading_id: str, question_id: str, payload: AnswerRequest) -> dict[str, object]:
        with _answer_interaction_lock(reading_id):
            runtime_payload = _cache_get_reading_payload(reading_id)
            runtime_payload = runtime_payload or repository.get_runtime_payload(reading_id)
            if runtime_payload is None:
                raise HTTPException(status_code=404, detail="reading not found")
            runtime = CoreRuntimeResult.model_validate(runtime_payload)
            matched = [anchor for anchor in runtime.question_anchors if anchor.question_id == question_id]
            if not matched:
                raise HTTPException(status_code=404, detail="question not found")
            answer_payload = payload.model_dump(mode="json")
            runtime = attach_question_outcome(runtime, question_id, answer_payload)
            interaction_brain_result = runtime.question_plan.policy_effect.get("interaction_brain_result", {})
            hidden_factor_state_from_turn = None
            if isinstance(interaction_brain_result, dict):
                feedback_payload = interaction_brain_result.get("hidden_factor_feedback_payload", {})
                feedback_payload = feedback_payload if isinstance(feedback_payload, dict) else {}
                hidden_factor_state_from_turn = _save_hidden_factor_feedback_payload(
                    runtime=runtime,
                    payload=feedback_payload,
                )
            if hidden_factor_state_from_turn:
                runtime = attach_hidden_factor_state(runtime, hidden_factor_state_from_turn)
                if isinstance(interaction_brain_result, dict):
                    interaction_brain_result = mark_hidden_factor_feedback_saved(
                        interaction_brain_result,
                        hidden_factor_state=hidden_factor_state_from_turn,
                    )
                    plan = runtime.question_plan.model_copy(
                        update={
                            "policy_effect": {
                                **runtime.question_plan.policy_effect,
                                "interaction_brain_result": interaction_brain_result,
                            }
                        }
                    )
                    runtime = runtime.model_copy(update={"question_plan": plan})
            repository.save_runtime(runtime)
            repository.save_trace(runtime)
            _cache_store_runtime(runtime)
            outcomes = runtime.question_plan.session_state.get("question_outcomes", [])
            event = next(
                (row for row in outcomes if isinstance(row, dict) and row.get("question_id") == question_id),
                {},
            ) if isinstance(outcomes, list) else {}
            graph = runtime.question_plan.policy_effect.get("question_dialogue_graph", {})
            interaction_state = runtime.question_plan.policy_effect.get("interaction_state", {})
            view = build_presentation_model(
                runtime,
                role_key=payload.role or "user",
                locale=payload.locale or runtime.chart_context.locale,
                client=payload.client or "web",
            )
            view_payload = view.model_dump(mode="json")
            surface = view_payload.get("reading_surface", {})
            surface = surface if isinstance(surface, dict) else {}
            next_surface_question_id = _next_surface_question_id(surface)
            return {
                "reading_id": reading_id,
                "question_id": question_id,
                "submit_surface": str(payload.submit_surface or "legacy_answer_endpoint"),
                "submit_source_id": str(payload.submit_source_id or ""),
                "submit_contract_version": str(payload.submit_contract_version or ""),
                "accepted": True,
                "outcome_event_id": event.get("event_id", ""),
                "question_outcome_consumed": True,
                "next_question_id": next_surface_question_id or None,
                "internal_next_question_id": graph.get("next_question_id") if isinstance(graph, dict) else None,
                "interaction_state": interaction_state if isinstance(interaction_state, dict) else {},
                "interaction_brain_result": public_interaction_brain_result(interaction_brain_result) if isinstance(interaction_brain_result, dict) else {},
                "view": view_payload,
                "answer_interaction_serialized": True,
                "boundary": "answer_submission_serializes_per_reading_dialogue_state_without_mutating_chart_facts",
            }

    @app.post(f"{API_PREFIX}/readings/{{reading_id}}/questions/{{question_id}}/answer/llm")
    def enhance_answer_with_llm(
        reading_id: str,
        question_id: str,
        payload: LLMAnswerEnhancementRequest,
    ) -> dict[str, object]:
        with _answer_interaction_lock(reading_id):
            runtime_payload = _cache_get_reading_payload(reading_id)
            runtime_payload = runtime_payload or repository.get_runtime_payload(reading_id)
            if runtime_payload is None:
                raise HTTPException(status_code=404, detail="reading not found")
            runtime = CoreRuntimeResult.model_validate(runtime_payload)
            known_question_ids = {anchor.question_id for anchor in runtime.question_anchors}
            outcomes = runtime.question_plan.session_state.get("question_outcomes", [])
            if isinstance(outcomes, list):
                known_question_ids.update(
                    str(row.get("question_id") or "")
                    for row in outcomes
                    if isinstance(row, dict)
                )
            if question_id not in known_question_ids:
                raise HTTPException(status_code=404, detail="question not found")
            if (
                runtime.answer_context is None
                or runtime.answer_result is None
                or runtime.answer_result.question_id != question_id
            ):
                anchor = next((row for row in runtime.question_anchors if row.question_id == question_id), None)
                if anchor is None:
                    raise HTTPException(status_code=404, detail="question not found")
                answer_context = build_answer_context(runtime, anchor)
                answer_result = compose_rule_bound_answer(answer_context, runtime=runtime)
                runtime = runtime.model_copy(update={"answer_context": answer_context, "answer_result": answer_result})
            reading_surface = build_presentation_model(
                runtime,
                role_key=payload.role or runtime.question_plan.role_key,
                locale=payload.locale or runtime.chart_context.locale,
                client=payload.client or "web",
            ).reading_surface
            enhanced = compose_bazi_llm_answer_draft(
                runtime,
                runtime.answer_context,
                runtime.answer_result,
                reading_surface=reading_surface,
                task_type=payload.task_type,
                role_key=_answer_llm_role_key(payload.role or runtime.question_plan.role_key),
                locale=payload.locale or runtime.chart_context.locale,
                client=payload.client or "web",
                domain=payload.domain,
                config=load_v30_llm_provider_config_from_env(),
            )
            enhanced_ready = enhanced.llm_metadata.get("status") == "accepted"
            if enhanced_ready:
                runtime = runtime.model_copy(update={"answer_result": enhanced})
                repository.save_runtime(runtime)
                repository.save_trace(runtime)
                _cache_store_runtime(runtime)
            view = build_presentation_model(
                runtime,
                role_key=payload.role or "user",
                locale=payload.locale or runtime.chart_context.locale,
                client=payload.client or "web",
            )
            return {
                "reading_id": reading_id,
                "question_id": question_id,
                "accepted": bool(enhanced_ready),
                "enhancement_status": str(enhanced.llm_metadata.get("status") or ""),
                "fallback_reason": str(enhanced.llm_metadata.get("fallback_reason") or ""),
                "llm_executed": bool(enhanced.llm_metadata.get("executed")),
                "view": view.model_dump(mode="json"),
                "answer_interaction_serialized": True,
                "boundary": "llm_answer_enhancement_is_expression_layer_and_serialized_per_reading",
            }

    @app.post(f"{API_PREFIX}/feedback")
    def create_feedback(payload: dict[str, object]) -> dict[str, object]:
        event_id = str(payload.get("event_id") or "v30-feedback-smoke")
        return {"event_id": event_id, "redis_key": redis_key(settings.env, "feedback", event_id)}

    @app.post(f"{API_PREFIX}/readings/{{reading_id}}/hidden-factor/feedback")
    def create_hidden_factor_feedback(reading_id: str, payload: dict[str, object]) -> dict[str, object]:
        runtime_payload = _cache_get_reading_payload(reading_id)
        runtime_payload = runtime_payload or repository.get_runtime_payload(reading_id)
        if runtime_payload is None:
            raise HTTPException(status_code=404, detail="reading not found")
        runtime = CoreRuntimeResult.model_validate(runtime_payload)
        state = _save_hidden_factor_feedback_payload(runtime=runtime, payload=payload)
        if state is None:
            raise HTTPException(status_code=400, detail="empty hidden factor feedback")
        return state

    @app.get(f"{API_PREFIX}/readings/{{reading_id}}/hidden-factor/state")
    def get_hidden_factor_state(reading_id: str) -> dict[str, object]:
        state_id = f"{reading_id}:hidden_factor_state"
        payload = hidden_factor_states.get_state_payload(state_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="hidden factor state not found")
        return payload

    @app.get(f"{API_PREFIX}/admin/runs/{{reading_id}}/trace")
    def get_admin_trace(reading_id: str) -> dict[str, object]:
        payload = _cache_get_reading_payload(reading_id)
        payload = payload or repository.get_runtime_payload(reading_id)
        if payload is None:
            runtime = create_smoke_runtime(reading_id=reading_id)
            repository.save_runtime(runtime)
            repository.save_trace(runtime)
            _cache_store_runtime(runtime)
            payload = runtime.model_dump(mode="json")
        trace_id = str(payload.get("trace_id") or "")
        trace_payload = _cache_get_trace_payload(trace_id) if trace_id else None
        trace_payload = trace_payload or (repository.get_trace_payload(trace_id) if trace_id else None)
        if trace_payload is None:
            trace_payload = payload
        runtime = CoreRuntimeResult.model_validate(trace_payload)
        trace_payload = _runtime_with_hidden_factor_state(runtime, hidden_factor_states).model_dump(mode="json")
        return {"reading_id": reading_id, "trace_id": trace_id, "trace": trace_payload}

    @app.get(f"{ADMIN_API_PREFIX}/readings/{{reading_id}}/trace")
    def get_admin_control_plane_trace(reading_id: str) -> dict[str, object]:
        return get_admin_trace(reading_id)

    @app.get(f"{API_PREFIX}/admin/runs/{{reading_id}}/question-replay")
    def get_admin_question_replay(reading_id: str) -> dict[str, object]:
        payload = _cache_get_reading_payload(reading_id)
        payload = payload or repository.get_runtime_payload(reading_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="reading not found")
        runtime = CoreRuntimeResult.model_validate(payload)
        runtime = _runtime_with_hidden_factor_state(runtime, hidden_factor_states)
        diagnostics = runtime.question_plan.policy_effect.get("adaptive_question_diagnostics", {})
        if not isinstance(diagnostics, dict):
            diagnostics = {}
        return {
            "reading_id": reading_id,
            "trace_id": runtime.trace_id,
            "adaptive_question_diagnostics": diagnostics,
        }

    @app.get(f"{API_PREFIX}/admin/readings/{{reading_id}}/intelligence-replay")
    def get_admin_intelligence_replay(reading_id: str) -> dict[str, object]:
        payload = _cache_get_reading_payload(reading_id)
        payload = payload or repository.get_runtime_payload(reading_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="reading not found")
        runtime = CoreRuntimeResult.model_validate(payload)
        runtime = _runtime_with_hidden_factor_state(runtime, hidden_factor_states)
        with practitioner_selection_lock:
            selections = list(practitioner_selection_store.get(reading_id, []))
        thinking = apply_practitioner_selection_effects_to_thinking(build_thinking_projection(runtime), selections)
        return build_admin_intelligence_replay(reading_id, thinking, selections)

    @app.get(f"{API_PREFIX}/admin/readings/{{reading_id}}/decision-workbench-quality")
    def get_admin_decision_workbench_quality(
        reading_id: str,
        locale: str = "zh",
        client: str = "admin",
    ) -> dict[str, object]:
        from v30.validation.decision_workbench_quality import build_decision_workbench_quality_audit

        payload = _cache_get_reading_payload(reading_id)
        payload = payload or repository.get_runtime_payload(reading_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="reading not found")
        runtime = CoreRuntimeResult.model_validate(payload)
        runtime = _runtime_with_hidden_factor_state(runtime, hidden_factor_states)
        return build_decision_workbench_quality_audit(runtime, locale=locale, client=client)

    @app.get(f"{ADMIN_API_PREFIX}/readings/{{reading_id}}/decision-workbench-quality")
    def get_admin_control_plane_decision_workbench_quality(
        reading_id: str,
        locale: str = "zh",
        client: str = "admin",
    ) -> dict[str, object]:
        return get_admin_decision_workbench_quality(reading_id, locale=locale, client=client)

    @app.get(f"{API_PREFIX}/admin/policies/question/comparison")
    def get_question_policy_comparison(candidate_id: str = "") -> dict[str, object]:
        payload = load_question_policy_comparison(
            candidate_id=candidate_id or None,
            settings=settings,
        )
        if not payload:
            raise HTTPException(status_code=404, detail="question policy comparison not found")
        return payload

    @app.get(f"{API_PREFIX}/admin/policies/lineage")
    def get_policy_lineage(family: str = "question_policy") -> dict[str, object]:
        supported: set[str] = {"structure_policy", "mainline_policy", "question_policy", "rule_policy"}
        if family not in supported:
            raise HTTPException(status_code=400, detail=f"unsupported lineage family: {family}")
        lineage = build_promotion_lineage(family=family, settings=settings)
        return lineage.model_dump(mode="json")

    @app.get(f"{API_PREFIX}/admin/policies/lineage/summary")
    def get_policy_lineage_summary() -> dict[str, object]:
        return _policy_lineage_summary_payload()

    @app.post(f"{API_PREFIX}/admin/policies/rollback")
    def rollback_policy_pointer(payload: dict[str, object]) -> dict[str, object]:
        family = str(payload.get("family") or "")
        supported: set[str] = {"structure_policy", "mainline_policy", "question_policy", "rule_policy"}
        if family not in supported:
            raise HTTPException(status_code=400, detail=f"unsupported rollback family: {family}")
        store = RuntimePointerStore(settings)
        before = store.load_pointer(family)
        try:
            after = store.rollback_to_previous(family, updated_by="v30.admin.policy.rollback")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        lineage = build_promotion_lineage(family=family, settings=settings, store=store)
        return {
            "version": "v30.admin.policy_rollback.v1",
            "status": "rolled_back",
            "family": family,
            "before": before.model_dump(mode="json"),
            "after": after.model_dump(mode="json"),
            "lineage": lineage.model_dump(mode="json"),
            "chart_fact_mutation_allowed": False,
            "boundary": "admin_policy_rollback_updates_runtime_pointer_only_without_mutating_chart_facts",
        }

    @app.get(f"{API_PREFIX}/admin/runtime/config")
    def get_admin_runtime_config() -> dict[str, object]:
        return admin_runtime_config_status()

    @app.get(f"{API_PREFIX}/admin/runtime/db")
    def get_admin_database_status() -> dict[str, object]:
        return database_admin_status()

    @app.post(f"{API_PREFIX}/admin/runtime/db/config")
    def save_admin_database_runtime_config(payload: dict[str, object]) -> dict[str, object]:
        try:
            return save_admin_database_config(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(f"{API_PREFIX}/admin/runtime/db/apply-schema")
    def apply_admin_database_schema() -> dict[str, object]:
        return apply_database_schema()

    @app.get(f"{API_PREFIX}/admin/runtime/redis")
    def get_admin_redis_status() -> dict[str, object]:
        return redis_admin_status()

    @app.post(f"{API_PREFIX}/admin/runtime/redis/config")
    def save_admin_redis_runtime_config(payload: dict[str, object]) -> dict[str, object]:
        try:
            return save_admin_redis_config(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(f"{API_PREFIX}/admin/runtime/llm")
    def get_admin_llm_runtime_status(probe_models: bool = False) -> dict[str, object]:
        return llm_admin_status(probe_models=probe_models)

    @app.post(f"{API_PREFIX}/admin/runtime/llm/config")
    def save_admin_llm_runtime_config(payload: dict[str, object]) -> dict[str, object]:
        try:
            return save_admin_llm_config(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(f"{API_PREFIX}/admin/runtime/llm/probe")
    def probe_admin_llm_runtime(payload: dict[str, object]) -> dict[str, object]:
        try:
            return llm_admin_probe(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(f"{API_PREFIX}/admin/runtime/llm/test")
    def test_admin_llm_runtime(payload: dict[str, object]) -> dict[str, object]:
        try:
            return llm_admin_test(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(f"{API_PREFIX}/admin/training/run")
    def run_training(payload: TrainingRunRequest) -> dict[str, object]:
        nonlocal latest_auto_training_job_id
        families = tuple(payload.families) if payload.families else DEFAULT_AUTO_TRAINING_FAMILIES
        invalid = sorted(set(families) - set(DEFAULT_AUTO_TRAINING_FAMILIES))
        if invalid:
            raise HTTPException(status_code=400, detail=f"unsupported training families: {','.join(invalid)}")
        mode = payload.promotion_validation_mode or "strict"
        if mode not in {"strict", "smoke"}:
            raise HTTPException(status_code=400, detail=f"unsupported promotion validation mode: {mode}")
        job_id = f"auto-training-job-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}-{secrets.token_hex(3)}"
        training_run_id = payload.training_run_id or f"admin-training-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        steps = [f"promote_{family}" for family in families]
        job: dict[str, object] = {
            "version": "v30.admin.auto_apply_training_job.v1",
            "job_id": job_id,
            "status": "queued",
            "created_at": _utc_now(),
            "started_at": "",
            "finished_at": "",
            "current_step": "queued",
            "message": "",
            "completed_steps": 0,
            "total_steps": len(steps),
            "progress_percent": 0,
            "steps": steps,
            "progress_events": [],
            "training_run": {},
            "log_path": str(_auto_training_job_log_path(job_id)),
            "config": {
                "training_run_id": training_run_id,
                "families": list(families),
                "promotion_validation_mode": mode,
                "auto_apply": True,
                "entrypoint": "admin_training_run_compat",
            },
            "boundary": "compat_training_run_queues_isolated_worker_without_blocking_api_or_mutating_chart_facts",
        }
        with auto_training_lock:
            auto_training_jobs[job_id] = job
            latest_auto_training_job_id = job_id
            _persist_auto_training_job(job)
        _launch_admin_training_worker(
            kind="auto-apply",
            job_id=job_id,
            job_path=_auto_training_job_path(job_id),
            log_path=_auto_training_job_log_path(job_id),
            lock=auto_training_lock,
            jobs=auto_training_jobs,
            read_job=_read_auto_training_job,
            persist_job=_persist_auto_training_job,
        )
        return _auto_training_job_public(_read_auto_training_job(job_id) or job)

    @app.get(f"{API_PREFIX}/admin/training/brain-examples/summary")
    def get_brain_training_example_summary(split: str = "raw") -> dict[str, object]:
        store = BrainTrainingExampleStore(settings.runtime_dir)
        summary = store.summary(split=split)
        return {
            "version": "v30.admin.brain_training_example_summary.v1",
            "store": summary,
            "available_splits": {
                "raw": store.summary(split="raw", include_splits=False),
                "train": store.summary(split="train", include_splits=False),
                "validation": store.summary(split="validation", include_splits=False),
                "replay": store.summary(split="replay", include_splits=False),
            },
            "chart_fact_mutation_allowed": False,
            "boundary": "admin_brain_training_example_summary_reads_policy_training_examples_without_mutating_chart_facts",
        }

    @app.post(f"{API_PREFIX}/admin/training/brain-examples/split")
    def build_brain_training_example_split(payload: BrainTrainingSplitRequest) -> dict[str, object]:
        store = BrainTrainingExampleStore(settings.runtime_dir)
        manifest = store.build_splits(
            seed=payload.seed,
            train_ratio=payload.train_ratio,
            validation_ratio=payload.validation_ratio,
            source=payload.source,
            stage_id=payload.stage_id,
        )
        return {
            "version": "v30.admin.brain_training_example_split.v1",
            "manifest": manifest,
            "summary": store.summary(split="raw"),
            "chart_fact_mutation_allowed": False,
            "boundary": "admin_brain_training_example_split_partitions_policy_training_examples_without_mutating_chart_facts",
        }

    @app.post(f"{API_PREFIX}/admin/training/brain-examples/optimize")
    def optimize_brain_training_examples(payload: BrainTrainingOptimizeRequest) -> dict[str, object]:
        store = BrainTrainingExampleStore(settings.runtime_dir)
        examples = store.read(split=payload.split, limit=100000)
        candidate = optimize_central_brain_policy(
            examples,
            min_examples=payload.min_examples,
            max_delta=payload.max_delta,
        )
        return {
            "version": "v30.admin.brain_training_example_optimize.v1",
            "split": payload.split,
            "candidate": candidate,
            "summary": store.summary(split=payload.split),
            "chart_fact_mutation_allowed": False,
            "boundary": "admin_brain_training_example_optimize_builds_policy_candidate_without_mutating_chart_facts",
        }

    @app.post(f"{API_PREFIX}/admin/training/brain-examples/replay-gate")
    def run_brain_training_replay_gate(payload: BrainTrainingReplayGateRequest) -> dict[str, object]:
        from v30.validation.central_brain_phase2_replay_gate import build_central_brain_phase2_replay_gate

        store = BrainTrainingExampleStore(settings.runtime_dir)
        train_examples = store.read(split=payload.train_split, limit=100000)
        replay_examples = store.read(split=payload.replay_split, limit=100000)
        candidate = optimize_central_brain_policy(
            train_examples,
            min_examples=payload.min_examples,
            max_delta=payload.max_delta,
        )
        gate = build_central_brain_phase2_replay_gate(
            candidate_policy=candidate,
            replay_examples=replay_examples,
            min_replay_examples=payload.min_replay_examples,
        )
        return {
            "version": "v30.admin.brain_training_example_replay_gate.v1",
            "train_split": payload.train_split,
            "replay_split": payload.replay_split,
            "gate": gate,
            "train_summary": store.summary(split=payload.train_split),
            "replay_summary": store.summary(split=payload.replay_split),
            "chart_fact_mutation_allowed": False,
            "boundary": "admin_brain_training_example_replay_gate_validates_policy_candidate_without_mutating_chart_facts",
        }

    @app.post(f"{API_PREFIX}/admin/training/brain-examples/distribution-gate")
    def run_brain_training_distribution_gate(payload: BrainTrainingDistributionGateRequest) -> dict[str, object]:
        from v30.validation import run_518k_validation
        from v30.validation.central_brain_phase2_distribution_gate import build_central_brain_phase2_distribution_gate
        from v30.validation.central_brain_phase2_replay_gate import build_central_brain_phase2_replay_gate

        store = BrainTrainingExampleStore(settings.runtime_dir)
        train_examples = store.read(split=payload.train_split, limit=100000)
        replay_examples = store.read(split=payload.replay_split, limit=100000)
        candidate = optimize_central_brain_policy(
            train_examples,
            min_examples=payload.min_examples,
            max_delta=payload.max_delta,
        )
        replay_gate = build_central_brain_phase2_replay_gate(
            candidate_policy=candidate,
            replay_examples=replay_examples,
            min_replay_examples=payload.min_replay_examples,
        )
        policy_overrides = {"question_policy": {"central_brain_phase2_policy": candidate}}
        sample = run_518k_validation(
            mode="sample",
            limit=payload.sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "518k",
            policy_payload_overrides=policy_overrides,
        ).model_dump(mode="json")
        shard = {}
        if payload.include_shard:
            shard = run_518k_validation(
                mode="shard",
                shard_id=payload.shard_id,
                limit=payload.shard_limit,
                artifact_dir=settings.runtime_dir / "validation" / "518k",
                policy_payload_overrides=policy_overrides,
            ).model_dump(mode="json")
        gate = build_central_brain_phase2_distribution_gate(
            replay_gate=replay_gate,
            sample_result=sample,
            shard_result=shard,
            min_sample_cases=payload.sample_limit,
            require_shard=payload.include_shard,
        )
        return {
            "version": "v30.admin.brain_training_example_distribution_gate.v1",
            "train_split": payload.train_split,
            "replay_split": payload.replay_split,
            "gate": gate,
            "replay_gate": replay_gate,
            "chart_fact_mutation_allowed": False,
            "boundary": "admin_brain_training_example_distribution_gate_validates_518k_without_mutating_chart_facts_or_pointer",
        }

    @app.get(f"{API_PREFIX}/admin/evaluation/training-spine")
    def get_admin_evaluation_training_spine(include_phase2: bool = True) -> dict[str, object]:
        from v30.validation.evaluation_training_spine import run_evaluation_training_spine

        result = run_evaluation_training_spine(include_phase2=include_phase2)
        decision = result.get("decision") if isinstance(result.get("decision"), dict) else {}
        return {
            **result,
            "admin_projection": {
                "version": "v30.admin.evaluation_training_spine_projection.v1",
                "include_phase2": include_phase2,
                "ready": bool(decision.get("evaluation_training_spine_ready")),
                "case_count": decision.get("case_count") or 0,
                "passed_case_count": decision.get("passed_case_count") or 0,
                "average_overall_score": decision.get("average_overall_score"),
                "overclaim_rate": decision.get("overclaim_rate"),
                "action": "use_as_quality_gate_before_policy_pointer_promotion",
            },
            "policy_boundary": {
                "runtime_mutation_allowed": False,
                "chart_fact_mutation_allowed": False,
                "production_policy_write_allowed": False,
                "llm_as_sole_evaluator_allowed": False,
            },
            "boundary": "admin_evaluation_training_spine_runs_quality_gate_without_mutating_runtime_or_policy",
        }

    @app.get(f"{ADMIN_API_PREFIX}/evaluation/training-spine")
    def get_admin_control_plane_evaluation_training_spine(include_phase2: bool = True) -> dict[str, object]:
        return get_admin_evaluation_training_spine(include_phase2=include_phase2)

    @app.get(f"{API_PREFIX}/admin/training/orchestrator/plans")
    def get_training_orchestrator_plans() -> dict[str, object]:
        return {
            "version": "v30.admin.training_orchestrator_plans.v1",
            "plans": _training_orchestrator_plans(),
            "boundary": "training_orchestrator_plans_describe_available_training_without_running_training",
        }

    @app.get(f"{ADMIN_API_PREFIX}/training/orchestrator/plans")
    def get_admin_control_plane_training_orchestrator_plans() -> dict[str, object]:
        return get_training_orchestrator_plans()

    @app.post(f"{API_PREFIX}/admin/training/orchestrator/run")
    def run_training_orchestrator(payload: TrainingOrchestratorRunRequest) -> dict[str, object]:
        nonlocal latest_training_orchestrator_job_id
        try:
            plan = _training_orchestrator_plan(payload.plan_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        families = tuple(payload.families) if payload.families else DEFAULT_AUTO_TRAINING_FAMILIES
        invalid = sorted(set(families) - set(DEFAULT_AUTO_TRAINING_FAMILIES))
        if invalid:
            raise HTTPException(status_code=400, detail=f"unsupported training families: {','.join(invalid)}")
        mode = payload.promotion_validation_mode or "strict"
        if mode not in {"strict", "smoke"}:
            raise HTTPException(status_code=400, detail=f"unsupported promotion validation mode: {mode}")
        job_id = f"training-orchestrator-job-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}-{secrets.token_hex(3)}"
        training_run_id = payload.training_run_id or f"orchestrator-{payload.plan_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        steps = list(plan.get("steps") or [])
        if payload.plan_id == "m3_518k_validation":
            if payload.include_shard:
                steps.append("518k_shard")
            if payload.include_readiness_matrix:
                steps.append("518k_readiness_matrix")
        job: dict[str, object] = {
            "version": "v30.admin.training_orchestrator_job.v1",
            "job_id": job_id,
            "plan_id": payload.plan_id,
            "plan_label": plan.get("label", payload.plan_id),
            "status": "queued",
            "created_at": _utc_now(),
            "started_at": "",
            "finished_at": "",
            "current_step": "queued",
            "completed_steps": 0,
            "total_steps": len(steps),
            "progress_percent": 0,
            "steps": steps,
            "step_results": [],
            "progress_events": [],
            "config": {
                "plan_id": payload.plan_id,
                "training_run_id": training_run_id,
                "families": list(families),
                "promotion_validation_mode": mode,
                "sample_limit": payload.sample_limit,
                "persist_m3_to_db": payload.persist_m3_to_db,
                "include_shard": payload.include_shard,
                "shard_id": payload.shard_id,
                "shard_limit": payload.shard_limit,
                "include_readiness_matrix": payload.include_readiness_matrix,
            },
            "boundary": "training_orchestrator_runs_named_training_plan_without_mutating_chart_facts",
        }
        with training_orchestrator_lock:
            training_orchestrator_jobs[job_id] = job
            latest_training_orchestrator_job_id = job_id
            _persist_training_orchestrator_job(job)
        _launch_admin_training_worker(
            kind="orchestrator",
            job_id=job_id,
            job_path=_training_orchestrator_job_path(job_id),
            log_path=_training_orchestrator_job_log_path(job_id),
            lock=training_orchestrator_lock,
            jobs=training_orchestrator_jobs,
            read_job=_read_training_orchestrator_job,
            persist_job=_persist_training_orchestrator_job,
        )
        return _training_orchestrator_job_public(_read_training_orchestrator_job(job_id) or job)

    @app.post(f"{ADMIN_API_PREFIX}/training/orchestrator/run")
    def run_admin_control_plane_training_orchestrator(payload: TrainingOrchestratorRunRequest) -> dict[str, object]:
        return run_training_orchestrator(payload)

    @app.get(f"{API_PREFIX}/admin/training/orchestrator/status")
    def get_training_orchestrator_status(job_id: str = "") -> dict[str, object]:
        target_job_id = job_id or latest_training_orchestrator_job_id or _latest_training_orchestrator_job_id_from_disk()
        if not target_job_id:
            return {"status": "not_started"}
        disk_job = _read_training_orchestrator_job(target_job_id)
        if disk_job:
            with training_orchestrator_lock:
                training_orchestrator_jobs[target_job_id] = disk_job
                return _training_orchestrator_job_public(training_orchestrator_jobs[target_job_id])
        with training_orchestrator_lock:
            return _training_orchestrator_job_public(training_orchestrator_jobs.get(target_job_id))

    @app.get(f"{ADMIN_API_PREFIX}/training/orchestrator/status")
    def get_admin_control_plane_training_orchestrator_status(job_id: str = "") -> dict[str, object]:
        return get_training_orchestrator_status(job_id=job_id)

    @app.get(f"{API_PREFIX}/admin/training/orchestrator/history")
    def get_training_orchestrator_history(limit: int = 12) -> dict[str, object]:
        bounded_limit = max(1, min(50, int(limit)))
        rows = _list_training_orchestrator_jobs_from_disk(limit=bounded_limit)
        return {
            "version": "v30.admin.training_orchestrator_history.v1",
            "count": len(rows),
            "jobs": rows,
            "boundary": "training_orchestrator_history_reads_persisted_jobs_without_running_training_or_mutating_policy",
        }

    @app.get(f"{ADMIN_API_PREFIX}/training/orchestrator/history")
    def get_admin_control_plane_training_orchestrator_history(limit: int = 12) -> dict[str, object]:
        return get_training_orchestrator_history(limit=limit)

    @app.get(f"{API_PREFIX}/admin/training/orchestrator/diff")
    def get_training_orchestrator_diff(job_id: str = "") -> dict[str, object]:
        target_job_id = job_id or latest_training_orchestrator_job_id or _latest_training_orchestrator_job_id_from_disk()
        if not target_job_id:
            return {"status": "not_started"}
        job = _read_training_orchestrator_job(target_job_id)
        if not job:
            with training_orchestrator_lock:
                job = training_orchestrator_jobs.get(target_job_id)
        if not job:
            raise HTTPException(status_code=404, detail="training orchestrator job not found")
        return _training_orchestrator_diff_summary(job)

    @app.get(f"{ADMIN_API_PREFIX}/training/orchestrator/diff")
    def get_admin_control_plane_training_orchestrator_diff(job_id: str = "") -> dict[str, object]:
        return get_training_orchestrator_diff(job_id=job_id)

    @app.post(f"{API_PREFIX}/admin/training/orchestrator/rerun-failed")
    def rerun_failed_training_orchestrator_steps(payload: TrainingOrchestratorRerunRequest) -> dict[str, object]:
        nonlocal latest_training_orchestrator_job_id
        source_job_id = payload.job_id or latest_training_orchestrator_job_id or _latest_training_orchestrator_job_id_from_disk()
        if not source_job_id:
            return {"status": "not_started"}
        source = _read_training_orchestrator_job(source_job_id)
        if not source:
            with training_orchestrator_lock:
                source = training_orchestrator_jobs.get(source_job_id)
        if not source:
            raise HTTPException(status_code=404, detail="training orchestrator job not found")
        plan_id = str(source.get("plan_id") or "")
        if plan_id not in {"quick_validation_only", "m3_518k_validation"}:
            raise HTTPException(status_code=400, detail=f"failed-step rerun is not supported for plan: {plan_id}")
        failed_steps = payload.failed_steps or _training_orchestrator_failed_steps(source)
        if not failed_steps:
            raise HTTPException(status_code=400, detail="no failed steps available for rerun")
        plan = _training_orchestrator_plan(plan_id)
        config = dict(source.get("config") or {})
        config["rerun_of_job_id"] = source_job_id
        config["rerun_steps"] = failed_steps
        job_id = f"training-orchestrator-job-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}-{secrets.token_hex(3)}"
        job: dict[str, object] = {
            "version": "v30.admin.training_orchestrator_job.v1",
            "job_id": job_id,
            "plan_id": plan_id,
            "plan_label": f"{plan.get('label', plan_id)} · 重跑失败步骤",
            "status": "queued",
            "created_at": _utc_now(),
            "started_at": "",
            "finished_at": "",
            "current_step": "queued",
            "completed_steps": 0,
            "total_steps": len(failed_steps),
            "progress_percent": 0,
            "steps": failed_steps,
            "step_results": [],
            "progress_events": [],
            "config": config,
            "rerun_of_job_id": source_job_id,
            "rerun_steps": failed_steps,
            "boundary": "training_orchestrator_reruns_failed_steps_without_mutating_chart_facts",
        }
        with training_orchestrator_lock:
            training_orchestrator_jobs[job_id] = job
            latest_training_orchestrator_job_id = job_id
            _persist_training_orchestrator_job(job)
        _launch_admin_training_worker(
            kind="orchestrator",
            job_id=job_id,
            job_path=_training_orchestrator_job_path(job_id),
            log_path=_training_orchestrator_job_log_path(job_id),
            lock=training_orchestrator_lock,
            jobs=training_orchestrator_jobs,
            read_job=_read_training_orchestrator_job,
            persist_job=_persist_training_orchestrator_job,
        )
        return _training_orchestrator_job_public(_read_training_orchestrator_job(job_id) or job)

    @app.post(f"{API_PREFIX}/admin/training/auto-apply/run")
    def run_auto_apply_training_background(payload: TrainingRunRequest) -> dict[str, object]:
        nonlocal latest_auto_training_job_id
        families = tuple(payload.families) if payload.families else DEFAULT_AUTO_TRAINING_FAMILIES
        invalid = sorted(set(families) - set(DEFAULT_AUTO_TRAINING_FAMILIES))
        if invalid:
            raise HTTPException(status_code=400, detail=f"unsupported training families: {','.join(invalid)}")
        mode = payload.promotion_validation_mode or "strict"
        if mode not in {"strict", "smoke"}:
            raise HTTPException(status_code=400, detail=f"unsupported promotion validation mode: {mode}")
        job_id = f"auto-training-job-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}-{secrets.token_hex(3)}"
        training_run_id = payload.training_run_id or f"admin-auto-training-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        steps = [f"promote_{family}" for family in families]
        job: dict[str, object] = {
            "version": "v30.admin.auto_apply_training_job.v1",
            "job_id": job_id,
            "status": "queued",
            "created_at": _utc_now(),
            "started_at": "",
            "finished_at": "",
            "current_step": "queued",
            "message": "",
            "completed_steps": 0,
            "total_steps": len(steps),
            "progress_percent": 0,
            "steps": steps,
            "progress_events": [],
            "training_run": {},
            "config": {
                "training_run_id": training_run_id,
                "families": list(families),
                "promotion_validation_mode": mode,
                "auto_apply": True,
            },
            "boundary": "runs_auto_training_in_background_and_promotes_validated_runtime_policy_pointers_without_mutating_chart_facts",
        }
        with auto_training_lock:
            auto_training_jobs[job_id] = job
            latest_auto_training_job_id = job_id
            _persist_auto_training_job(job)
        _launch_admin_training_worker(
            kind="auto-apply",
            job_id=job_id,
            job_path=_auto_training_job_path(job_id),
            log_path=_auto_training_job_log_path(job_id),
            lock=auto_training_lock,
            jobs=auto_training_jobs,
            read_job=_read_auto_training_job,
            persist_job=_persist_auto_training_job,
        )
        return _auto_training_job_public(_read_auto_training_job(job_id) or job)

    @app.get(f"{API_PREFIX}/admin/training/auto-apply/status")
    def get_auto_apply_training_background_status(job_id: str = "") -> dict[str, object]:
        target_job_id = job_id or latest_auto_training_job_id or _latest_auto_training_job_id_from_disk()
        if not target_job_id:
            return {"status": "not_started"}
        disk_job = _read_auto_training_job(target_job_id)
        if disk_job:
            with auto_training_lock:
                auto_training_jobs[target_job_id] = disk_job
                return _auto_training_job_public(auto_training_jobs[target_job_id])
        with auto_training_lock:
            return _auto_training_job_public(auto_training_jobs.get(target_job_id))

    @app.get(f"{API_PREFIX}/admin/training/auto-apply/history")
    def get_auto_apply_training_history(limit: int = 12) -> dict[str, object]:
        bounded_limit = max(1, min(50, int(limit)))
        rows = _list_auto_training_jobs_from_disk(limit=bounded_limit)
        return {
            "version": "v30.admin.auto_apply_training_history.v1",
            "count": len(rows),
            "jobs": rows,
            "boundary": "training_history_reads_persisted_jobs_without_running_training_or_mutating_policy",
        }

    @app.post(f"{API_PREFIX}/admin/training/m3-background/run")
    def run_m3_background_training(payload: M3BackgroundRunRequest) -> dict[str, object]:
        nonlocal latest_m3_background_job_id
        job_id = f"m3-job-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}-{secrets.token_hex(3)}"
        steps = ["m3_snapshot", "m3_synthetic", "training_pipeline", "518k_sample"]
        if payload.include_shard:
            steps.append("518k_shard")
        if payload.include_readiness_matrix:
            steps.append("518k_readiness_matrix")
        job: dict[str, object] = {
            "version": "v30.admin.m3_background_training_job.v1",
            "job_id": job_id,
            "status": "queued",
            "created_at": _utc_now(),
            "started_at": "",
            "finished_at": "",
            "current_step": "queued",
            "completed_steps": 0,
            "total_steps": len(steps),
            "progress_percent": 0,
            "steps": steps,
            "results": [],
            "worker_pid": None,
            "worker_mode": "external_tmux",
            "log_path": str(_m3_background_job_log_path(job_id)),
            "config": {
                "sample_limit": payload.sample_limit,
                "persist_m3_to_db": payload.persist_m3_to_db,
                "include_shard": payload.include_shard,
                "shard_id": payload.shard_id,
                "shard_limit": payload.shard_limit,
                "include_readiness_matrix": payload.include_readiness_matrix,
                "full_518k": "not_supported_by_background_default",
                "step_timeouts_sec": {
                    step_name: M3_BACKGROUND_STEP_TIMEOUTS[step_name]
                    for step_name in steps
                },
            },
            "boundary": "runs_m3_training_validation_and_518k_sample_without_pointer_promotion_or_chart_fact_mutation",
        }
        with m3_background_lock:
            m3_background_jobs[job_id] = job
            latest_m3_background_job_id = job_id
            _persist_m3_background_job(job)
        command = [
            "python3",
            "scripts/run_m3_background_training_job.py",
            "--job-file",
            str(_m3_background_job_path(job_id)),
            "--job-id",
            job_id,
            "--sample-limit",
            str(payload.sample_limit),
            "--shard-id",
            str(payload.shard_id),
            "--shard-limit",
            str(payload.shard_limit),
        ]
        if payload.include_shard:
            command.append("--include-shard")
        if payload.include_readiness_matrix:
            command.append("--include-readiness-matrix")
        log_path = _m3_background_job_log_path(job_id)
        session_name = "m3_" + "".join(char if char.isalnum() else "_" for char in job_id)[-80:]
        command_text = " ".join(
            [
                "cd",
                shlex.quote(str(Path(__file__).resolve().parents[2])),
                "&&",
                f"V30_ADMIN_CONFIG_PATH={shlex.quote(str(settings.runtime_dir / 'training' / 'm3_background_no_db_admin_config.json'))}",
                "V30_REPOSITORY=local_json",
                "env",
                "-u",
                "V30_DATABASE_URL",
                *[shlex.quote(part) for part in command],
                ">",
                shlex.quote(str(log_path)),
                "2>&1",
            ]
        )
        try:
            completed = subprocess.run(
                ["tmux", "new-session", "-d", "-s", session_name, command_text],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if completed.returncode != 0:
                raise OSError((completed.stderr or completed.stdout).strip() or "tmux new-session failed")
            job["worker_session"] = session_name
            _persist_m3_background_job(job)
        except (OSError, subprocess.TimeoutExpired) as exc:
            with m3_background_lock:
                job["status"] = "failed"
                job["error"] = str(exc)
                job["finished_at"] = _utc_now()
                _persist_m3_background_job(job)
        return _m3_job_public(job)

    @app.get(f"{API_PREFIX}/admin/training/m3-background/status")
    def get_m3_background_training_status(job_id: str = "") -> dict[str, object]:
        target_job_id = job_id or latest_m3_background_job_id or _latest_m3_background_job_id_from_disk()
        if not target_job_id:
            return {"status": "not_started"}
        disk_job = _read_m3_background_job(target_job_id)
        if disk_job:
            with m3_background_lock:
                m3_background_jobs[target_job_id] = _maybe_mark_m3_job_stale(disk_job)
                return _m3_job_public(m3_background_jobs[target_job_id])
        with m3_background_lock:
            job = m3_background_jobs.get(target_job_id)
            if job is not None:
                job = _maybe_mark_m3_job_stale(job)
            return _m3_job_public(job)

    @app.get(f"{API_PREFIX}/admin/training/system-closeout")
    def get_training_system_closeout(training_run_id: str = "bt4-closeout") -> dict[str, object]:
        from v30.validation.training_system_closeout import run_training_system_closeout

        return run_training_system_closeout(training_run_id=training_run_id)

    @app.get(f"{API_PREFIX}/admin/training/candidate-quarantine")
    def get_training_candidate_quarantine(training_run_id: str = "bt5-quarantine") -> dict[str, object]:
        from v30.validation.training_candidate_quarantine import run_training_candidate_quarantine

        return run_training_candidate_quarantine(training_run_id=training_run_id)

    @app.get(f"{API_PREFIX}/admin/training/dialogue-calibration-loop")
    def get_dialogue_training_calibration_loop(
        run_id: str = "dtc1-dialogue-training-calibration",
        sample_limit: int = 20,
    ) -> dict[str, object]:
        from v30.validation.dialogue_training_calibration_loop import (
            run_dialogue_training_calibration_validation,
        )

        payloads = repository.list_runtime_payloads(limit=sample_limit)
        return run_dialogue_training_calibration_validation(
            runtime_payloads=payloads,
            sample_limit=sample_limit,
            run_id=run_id,
        )

    @app.get(f"{API_PREFIX}/admin/training/dialogue-policy-candidate-review")
    def get_dialogue_policy_candidate_review(
        run_id: str = "dtc2-dialogue-policy-candidate-review",
        sample_limit: int = 20,
        persist: bool = True,
    ) -> dict[str, object]:
        from v30.validation.dialogue_policy_candidate_review import (
            run_dialogue_policy_candidate_review_validation,
        )

        payloads = repository.list_runtime_payloads(limit=sample_limit)
        return run_dialogue_policy_candidate_review_validation(
            runtime_payloads=payloads,
            sample_limit=sample_limit,
            run_id=run_id,
            persist=persist,
            settings=settings,
        )

    @app.get(f"{API_PREFIX}/admin/training/dialogue-strategy-validation-gate")
    def get_dialogue_strategy_validation_gate(
        run_id: str = "dtc3-dialogue-strategy-validation-gate",
        sample_limit: int = 20,
        persist_review: bool = True,
    ) -> dict[str, object]:
        from v30.validation.dialogue_strategy_validation_gate import (
            run_dialogue_strategy_validation_gate_validation,
        )

        payloads = repository.list_runtime_payloads(limit=sample_limit)
        return run_dialogue_strategy_validation_gate_validation(
            runtime_payloads=payloads,
            sample_limit=sample_limit,
            run_id=run_id,
            persist_review=persist_review,
            settings=settings,
        )

    @app.get(f"{API_PREFIX}/admin/training/dialogue-synthetic-replay-queue")
    def get_dialogue_synthetic_replay_queue(
        run_id: str = "dtc4-dialogue-synthetic-replay-queue",
        sample_limit: int = 20,
        persist_review: bool = True,
    ) -> dict[str, object]:
        from v30.validation.dialogue_synthetic_replay_queue import (
            run_dialogue_synthetic_replay_queue_validation,
        )

        payloads = repository.list_runtime_payloads(limit=sample_limit)
        return run_dialogue_synthetic_replay_queue_validation(
            runtime_payloads=payloads,
            sample_limit=sample_limit,
            run_id=run_id,
            persist_review=persist_review,
            settings=settings,
        )

    @app.get(f"{API_PREFIX}/admin/training/dialogue-operator-review-pack")
    def get_dialogue_operator_review_pack(
        run_id: str = "dtc5-dialogue-operator-review-pack",
        sample_limit: int = 20,
        persist_review: bool = True,
    ) -> dict[str, object]:
        from v30.validation.dialogue_operator_review_pack import (
            run_dialogue_operator_review_pack_validation,
        )

        payloads = repository.list_runtime_payloads(limit=sample_limit)
        return run_dialogue_operator_review_pack_validation(
            runtime_payloads=payloads,
            sample_limit=sample_limit,
            run_id=run_id,
            persist_review=persist_review,
            settings=settings,
        )

    @app.get(f"{API_PREFIX}/admin/training/dialogue-heavy-validation-decision")
    def get_dialogue_heavy_validation_decision(
        run_id: str = "dtc6-dialogue-heavy-validation-decision",
        sample_limit: int = 20,
        persist_review: bool = True,
    ) -> dict[str, object]:
        from v30.validation.dialogue_heavy_validation_decision import (
            run_dialogue_heavy_validation_decision_validation,
        )

        payloads = repository.list_runtime_payloads(limit=sample_limit)
        return run_dialogue_heavy_validation_decision_validation(
            runtime_payloads=payloads,
            sample_limit=sample_limit,
            run_id=run_id,
            persist_review=persist_review,
            settings=settings,
        )

    @app.get(f"{API_PREFIX}/admin/training/dialogue-heavy-validation-authorization")
    def get_dialogue_heavy_validation_authorization(
        run_id: str = "dtc7-dialogue-heavy-validation-authorization",
        sample_limit: int = 20,
        persist_review: bool = True,
        authorization_decision: str = "authorize_recommended",
    ) -> dict[str, object]:
        from v30.validation.dialogue_heavy_validation_authorization import (
            run_dialogue_heavy_validation_authorization_validation,
        )

        payloads = repository.list_runtime_payloads(limit=sample_limit)
        safe_decision = "defer_all" if authorization_decision == "defer_all" else "authorize_recommended"
        return run_dialogue_heavy_validation_authorization_validation(
            runtime_payloads=payloads,
            sample_limit=sample_limit,
            run_id=run_id,
            persist_review=persist_review,
            authorization_decision=safe_decision,
            settings=settings,
        )

    @app.get(f"{API_PREFIX}/admin/training/dialogue-heavy-validation-execution-plan")
    def get_dialogue_heavy_validation_execution_plan(
        run_id: str = "dtc8-dialogue-heavy-validation-execution-plan",
        sample_limit: int = 20,
        persist_review: bool = True,
        authorization_decision: str = "authorize_recommended",
    ) -> dict[str, object]:
        from v30.validation.dialogue_heavy_validation_execution_plan import (
            run_dialogue_heavy_validation_execution_plan_validation,
        )

        payloads = repository.list_runtime_payloads(limit=sample_limit)
        safe_decision = "defer_all" if authorization_decision == "defer_all" else "authorize_recommended"
        return run_dialogue_heavy_validation_execution_plan_validation(
            runtime_payloads=payloads,
            sample_limit=sample_limit,
            run_id=run_id,
            persist_review=persist_review,
            authorization_decision=safe_decision,
            settings=settings,
        )

    @app.get(f"{API_PREFIX}/admin/validation/synthetic-coverage-manifest")
    def get_synthetic_coverage_manifest() -> dict[str, object]:
        from v30.validation.synthetic_coverage_manifest import run_synthetic_coverage_manifest

        return run_synthetic_coverage_manifest()

    @app.get(f"{API_PREFIX}/admin/validation/stage-option-intelligence-replay")
    def get_stage_option_intelligence_replay() -> dict[str, object]:
        from v30.validation.stage_option_intelligence_replay import run_stage_option_intelligence_replay

        return run_stage_option_intelligence_replay()

    @app.get(f"{API_PREFIX}/admin/validation/text-option-synthetic")
    def get_text_option_synthetic_validation() -> dict[str, object]:
        from v30.validation.text_option_synthetic_validation import run_text_option_synthetic_validation

        return run_text_option_synthetic_validation()

    @app.get(f"{API_PREFIX}/admin/validation/518k/artifacts")
    def get_518k_artifacts(
        mode: str = "",
        promotion_signal: str = "",
        run_id: str = "",
        limit: int = 20,
    ) -> dict[str, object]:
        result = search_518k_validation_artifacts(
            settings=settings,
            mode=mode,
            promotion_signal=promotion_signal,
            run_id=run_id,
            limit=limit,
        )
        return result.model_dump(mode="json")

    @app.get(f"{ADMIN_API_PREFIX}/validation/518k/artifacts")
    def get_admin_control_plane_518k_artifacts(
        mode: str = "",
        promotion_signal: str = "",
        run_id: str = "",
        limit: int = 20,
    ) -> dict[str, object]:
        return get_518k_artifacts(mode=mode, promotion_signal=promotion_signal, run_id=run_id, limit=limit)

    @app.get(f"{API_PREFIX}/admin/validation/518k/readiness-matrix")
    def get_518k_readiness_matrix(
        sample_limit: int = 8,
        shard_id: int = 7,
        shard_limit: int = 16,
    ) -> dict[str, object]:
        from v30.validation.corpus_518k_readiness_matrix import run_518k_readiness_matrix

        return run_518k_readiness_matrix(
            sample_limit=sample_limit,
            shard_id=shard_id,
            shard_limit=shard_limit,
            settings=settings,
        )

    @app.get(f"{API_PREFIX}/admin/support/brain-training-synthetic-closeout")
    def get_brain_training_synthetic_closeout(
        sample_limit: int = 8,
        shard_id: int = 7,
        shard_limit: int = 16,
    ) -> dict[str, object]:
        from v30.validation.brain_training_synthetic_closeout import run_brain_training_synthetic_closeout

        return run_brain_training_synthetic_closeout(
            sample_limit=sample_limit,
            shard_id=shard_id,
            shard_limit=shard_limit,
            settings=settings,
        )

    @app.get(f"{API_PREFIX}/admin/productization/multi-user-terminal-locale-readiness")
    def get_multi_user_terminal_locale_readiness(reading_id: str = "u1-multi-user-terminal-locale") -> dict[str, object]:
        from v30.validation.multi_user_terminal_locale_readiness import run_multi_user_terminal_locale_readiness

        return run_multi_user_terminal_locale_readiness(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/productization/session-owner-boundary-readiness")
    def get_session_owner_boundary_readiness() -> dict[str, object]:
        from v30.validation.session_owner_boundary_readiness import run_session_owner_boundary_readiness

        return run_session_owner_boundary_readiness()

    @app.get(f"{API_PREFIX}/admin/productization/locale-terminology-readiness")
    def get_locale_terminology_readiness(reading_id: str = "u3-locale-terminology") -> dict[str, object]:
        from v30.validation.locale_terminology_readiness import run_locale_terminology_readiness

        return run_locale_terminology_readiness(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/productization/terminal-contract-freeze")
    def get_terminal_contract_freeze(reading_id: str = "u4-terminal-contract") -> dict[str, object]:
        from v30.validation.terminal_contract_freeze import run_terminal_contract_freeze

        return run_terminal_contract_freeze(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/productization/closeout")
    def get_productization_closeout(reading_id: str = "u5-productization-closeout") -> dict[str, object]:
        from v30.validation.productization_closeout import run_productization_closeout

        return run_productization_closeout(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/llm/bazi-context-prompt-readiness")
    def get_bazi_llm_context_prompt_readiness(
        reading_id: str = "bl1-bl3-bazi-llm-context-prompt",
    ) -> dict[str, object]:
        from v30.validation.bazi_llm_context_prompt_readiness import run_bazi_llm_context_prompt_readiness

        return run_bazi_llm_context_prompt_readiness(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/llm/prompt-profile-quality-audit")
    def get_llm_prompt_profile_quality_audit(
        reading_id: str = "llm-prompt-profile-quality-audit",
    ) -> dict[str, object]:
        from v30.validation.llm_prompt_profile_quality_audit import run_llm_prompt_profile_quality_audit

        return run_llm_prompt_profile_quality_audit(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/llm/bazi-answer-generator-readiness")
    def get_bazi_llm_answer_generator_readiness(
        reading_id: str = "bl4-bazi-llm-answer-generator",
    ) -> dict[str, object]:
        from v30.validation.bazi_llm_answer_generator_readiness import run_bazi_llm_answer_generator_readiness

        return run_bazi_llm_answer_generator_readiness(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/llm/bazi-output-acceptance-readiness")
    def get_bazi_llm_output_acceptance_readiness(
        reading_id: str = "bl5-bazi-llm-output-acceptance",
    ) -> dict[str, object]:
        from v30.validation.bazi_llm_output_acceptance_readiness import run_bazi_llm_output_acceptance_readiness

        return run_bazi_llm_output_acceptance_readiness(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/llm/bazi-training-synthetic-readiness")
    def get_bazi_llm_training_synthetic_readiness() -> dict[str, object]:
        from v30.validation.bazi_llm_training_synthetic_readiness import run_bazi_llm_training_synthetic_readiness

        return run_bazi_llm_training_synthetic_readiness()

    @app.get(f"{API_PREFIX}/admin/llm/bazi-role-locale-production-smoke")
    def get_bazi_llm_role_locale_production_smoke(
        reading_id: str = "bl7-bazi-llm-role-locale-smoke",
    ) -> dict[str, object]:
        from v30.validation.bazi_llm_role_locale_production_smoke import run_bazi_llm_role_locale_production_smoke

        return run_bazi_llm_role_locale_production_smoke(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/llm/bazi-closeout")
    def get_bazi_llm_closeout(reading_id: str = "bl8-bazi-llm-closeout") -> dict[str, object]:
        from v30.validation.bazi_llm_closeout import run_bazi_llm_closeout

        return run_bazi_llm_closeout(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/mainline/bazi-intelligence-requirements-coverage")
    def get_bazi_intelligence_requirements_coverage(
        reading_id: str = "ir1-bazi-intelligence-requirements",
    ) -> dict[str, object]:
        from v30.validation.bazi_intelligence_requirements_coverage import (
            run_bazi_intelligence_requirements_coverage,
        )

        return run_bazi_intelligence_requirements_coverage(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/mainline/bazi-backend-api-journey-acceptance")
    def get_bazi_backend_api_journey_acceptance(
        reading_id: str = "ir2-bazi-backend-api-journey",
    ) -> dict[str, object]:
        from v30.validation.bazi_backend_api_journey_acceptance import (
            run_bazi_backend_api_journey_acceptance,
        )

        return run_bazi_backend_api_journey_acceptance(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/mainline/intelligent-question-interaction-audit")
    def get_intelligent_question_interaction_audit(
        reading_id: str = "iq1-intelligent-question-interaction",
    ) -> dict[str, object]:
        from v30.validation.intelligent_question_interaction_audit import (
            run_intelligent_question_interaction_audit,
        )

        return run_intelligent_question_interaction_audit(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/mainline/question-model-signal-training-readiness")
    def get_question_model_signal_training_readiness(
        reading_id: str = "iq2-question-model-signal-training",
    ) -> dict[str, object]:
        from v30.validation.question_model_signal_training_readiness import (
            run_question_model_signal_training_readiness,
        )

        return run_question_model_signal_training_readiness(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/mainline/intelligent-question-chain-readiness")
    def get_intelligent_question_chain_readiness(
        reading_id: str = "iq4-intelligent-question-chain",
    ) -> dict[str, object]:
        from v30.validation.intelligent_question_chain_readiness import (
            run_intelligent_question_chain_readiness,
        )

        return run_intelligent_question_chain_readiness(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/mainline/intelligent-question-closeout")
    def get_intelligent_question_closeout(
        reading_id: str = "iq5-intelligent-question-closeout",
    ) -> dict[str, object]:
        from v30.validation.intelligent_question_closeout import (
            run_intelligent_question_closeout,
        )

        return run_intelligent_question_closeout(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/mainline/main-module-completion-review")
    def get_main_module_completion_review(
        reading_id: str = "mcr1-main-module-completion-review",
    ) -> dict[str, object]:
        from v30.validation.main_module_completion_review import run_main_module_completion_review

        return run_main_module_completion_review(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/mainline/customer-surface-bazi-context-reconciliation")
    def get_customer_surface_bazi_context_reconciliation(
        reading_id: str = "mcr2-customer-surface-bazi-context",
    ) -> dict[str, object]:
        from v30.validation.customer_surface_bazi_context_reconciliation import (
            run_customer_surface_bazi_context_reconciliation,
        )

        return run_customer_surface_bazi_context_reconciliation(reading_id=reading_id)

    @app.get(f"{API_PREFIX}/admin/m3/source-backlog")
    def get_m3_source_backlog(
        source_family_id: str = "",
        priority: str = "",
        queue_state: str = "",
        review_status: str = "",
        target_domain: str = "",
        limit: int = 50,
    ) -> dict[str, object]:
        from v30.validation.m3_source_backlog_review_surface import (
            run_m3_source_backlog_review_surface,
        )

        return run_m3_source_backlog_review_surface(
            source_family_id=source_family_id,
            priority=priority,
            queue_state=queue_state,
            review_status=review_status,
            target_domain=target_domain,
            limit=limit,
            artifact_dir=settings.runtime_dir / "validation" / "m3",
            settings=settings,
        )

    @app.get(f"{API_PREFIX}/admin/m3/source-backlog-closeout")
    def get_m3_source_backlog_closeout(
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.m3_source_backlog_closeout import run_m3_source_backlog_closeout

        return run_m3_source_backlog_closeout(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "m3",
        )

    @app.get(f"{API_PREFIX}/admin/m5/evidence-consumption-hardening")
    def get_m5_evidence_consumption_hardening(
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.m5_evidence_consumption_hardening import (
            run_m5_evidence_consumption_hardening,
        )

        return run_m5_evidence_consumption_hardening(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "m5",
        )

    @app.get(f"{API_PREFIX}/admin/m5/calibration-replay-review")
    def get_m5_calibration_replay_review(
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.m5_calibration_replay_review import (
            run_m5_calibration_replay_review,
        )

        return run_m5_calibration_replay_review(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "m5",
        )

    @app.get(f"{API_PREFIX}/admin/m5/calibration-replay-closeout")
    def get_m5_calibration_replay_closeout(
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.m5_calibration_replay_closeout import (
            run_m5_calibration_replay_closeout,
        )

        return run_m5_calibration_replay_closeout(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "m5",
        )

    @app.get(f"{API_PREFIX}/admin/m6/practical-reading-consumption-hardening")
    def get_m6_practical_reading_consumption_hardening(
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.m6_practical_reading_consumption_hardening import (
            run_m6_practical_reading_consumption_hardening,
        )

        return run_m6_practical_reading_consumption_hardening(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "m6",
        )

    @app.get(f"{API_PREFIX}/admin/m6/practical-reading-closeout")
    def get_m6_practical_reading_closeout(
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.m6_practical_reading_closeout import (
            run_m6_practical_reading_closeout,
        )

        return run_m6_practical_reading_closeout(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "m6",
        )

    @app.get(f"{API_PREFIX}/admin/m7/real-case-calibration-steady-state-review")
    def get_m7_real_case_calibration_steady_state_review(
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.m7_real_case_calibration_steady_state_review import (
            run_m7_real_case_calibration_steady_state_review,
        )

        return run_m7_real_case_calibration_steady_state_review(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "m7",
        )

    @app.get(f"{API_PREFIX}/admin/m7/real-case-calibration-closeout")
    def get_m7_real_case_calibration_closeout(
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.m7_real_case_calibration_closeout import (
            run_m7_real_case_calibration_closeout,
        )

        return run_m7_real_case_calibration_closeout(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "m7",
        )

    @app.get(f"{API_PREFIX}/admin/m8/projection-api-contract-closeout")
    def get_m8_projection_api_contract_closeout(
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.m8_projection_api_contract_closeout import (
            run_m8_projection_api_contract_closeout,
        )

        return run_m8_projection_api_contract_closeout(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "m8",
        )

    @app.get(f"{API_PREFIX}/admin/iq/intelligent-question-support-review")
    def get_iq_intelligent_question_support_review(
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.iq_intelligent_question_support_review import (
            run_iq_intelligent_question_support_review,
        )

        return run_iq_intelligent_question_support_review(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "iq",
        )

    @app.get(f"{API_PREFIX}/admin/llm/bazi-expression-support-review")
    def get_llm_bazi_expression_support_review(
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.llm_bazi_expression_support_review import (
            run_llm_bazi_expression_support_review,
        )

        return run_llm_bazi_expression_support_review(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "llm",
        )

    @app.get(f"{API_PREFIX}/admin/training/synthetic-support-review")
    def get_training_synthetic_support_review(
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.training_synthetic_support_review import (
            run_training_synthetic_support_review,
        )

        return run_training_synthetic_support_review(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "training",
        )

    @app.get(f"{API_PREFIX}/admin/training/latent-policy-observability")
    def get_latent_policy_observability() -> dict[str, object]:
        from v30.validation.latent_policy_observability import (
            run_latent_policy_observability_readiness,
        )

        return run_latent_policy_observability_readiness()

    @app.get(f"{API_PREFIX}/admin/training/latent-attribute-review")
    def get_latent_attribute_admin_training_review() -> dict[str, object]:
        from v30.validation.latent_attribute_admin_training_review import (
            run_latent_attribute_admin_training_review,
        )

        return run_latent_attribute_admin_training_review(
            artifact_dir=settings.runtime_dir / "validation" / "latent-attribute-review",
        )

    @app.get(f"{API_PREFIX}/admin/training/latent-attribute-closeout")
    def get_latent_attribute_workflow_closeout() -> dict[str, object]:
        from v30.validation.latent_attribute_workflow_closeout import (
            run_latent_attribute_workflow_closeout,
        )

        return run_latent_attribute_workflow_closeout(
            artifact_dir=settings.runtime_dir / "validation" / "latent-attribute-closeout",
        )

    @app.get(f"{API_PREFIX}/admin/mainline/core-chain-steady-state-summary")
    def get_core_chain_steady_state_summary(
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.core_chain_steady_state_summary import (
            run_core_chain_steady_state_summary,
        )

        return run_core_chain_steady_state_summary(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "core-chain",
        )

    @app.get(f"{API_PREFIX}/admin/mainline/evidence-driven-calibration-queue")
    def get_evidence_driven_calibration_queue(
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.evidence_driven_calibration_queue import (
            run_evidence_driven_calibration_queue,
        )

        return run_evidence_driven_calibration_queue(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "evidence-queue",
        )

    @app.get(f"{API_PREFIX}/admin/mainline/await-new-calibration-evidence")
    def get_await_new_calibration_evidence_status(
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.await_new_calibration_evidence_status import (
            run_await_new_calibration_evidence_status,
        )

        return run_await_new_calibration_evidence_status(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "await-evidence",
        )

    @app.get(f"{API_PREFIX}/admin/mainline/core-calibration-steady-state-queue")
    def get_core_calibration_steady_state_queue(
        sample_limit: int = 8,
        full: bool = False,
    ) -> dict[str, object]:
        from v30.validation.core_calibration_steady_state_queue import (
            build_core_calibration_steady_state_queue,
            run_core_calibration_steady_state_queue,
        )

        if not full:
            synthetic_archetype_closeout = _lightweight_synthetic_archetype_closeout_status()
            await_status = _lightweight_await_new_evidence_status()
            result = build_core_calibration_steady_state_queue(
                synthetic_archetype_closeout=synthetic_archetype_closeout,
                await_new_evidence_status=await_status,
                sample_limit=sample_limit,
                artifact_dir=None,
            )
            result["runtime_mode"] = "lightweight_admin_projection"
            result["full_runner_endpoint"] = f"{API_PREFIX}/admin/mainline/core-calibration-steady-state-queue?sample_limit={sample_limit}&full=true"
            return result
        return run_core_calibration_steady_state_queue(
            sample_limit=sample_limit,
            artifact_dir=settings.runtime_dir / "validation" / "core-calibration-s0",
        )

    @app.get(f"{API_PREFIX}/admin/validation/artifacts")
    def get_validation_artifacts(
        family: str = "",
        candidate_id: str = "",
        run_id: str = "",
        limit: int = 20,
    ) -> dict[str, object]:
        result = search_validation_artifacts(
            settings=settings,
            family=family,
            candidate_id=candidate_id,
            run_id=run_id,
            limit=limit,
        )
        return result.model_dump(mode="json")

    @app.get(f"{ADMIN_API_PREFIX}/validation/artifacts")
    def get_admin_control_plane_validation_artifacts(
        family: str = "",
        candidate_id: str = "",
        run_id: str = "",
        limit: int = 20,
    ) -> dict[str, object]:
        return get_validation_artifacts(family=family, candidate_id=candidate_id, run_id=run_id, limit=limit)

    @app.get(f"{API_PREFIX}/admin/release/artifact-review")
    def get_release_artifact_review(
        mode: str = "quick",
        sample_limit: int = 2,
        include_shard: bool = False,
        shard_id: int = 0,
        shard_limit: int = 3,
    ) -> dict[str, object]:
        from v30.validation.release_artifact_review import build_release_artifact_review
        from v30.validation.release_gate import run_release_gate

        if mode not in {"quick", "standard"}:
            raise HTTPException(status_code=400, detail=f"unsupported release gate mode: {mode}")
        gate = run_release_gate(
            mode=mode,  # type: ignore[arg-type]
            include_shard=include_shard,
            shard_id=shard_id,
            sample_limit=sample_limit,
            shard_limit=shard_limit,
        )
        lineages = [
            build_promotion_lineage(family=family, settings=settings).model_dump(mode="json")
            for family in ("structure_policy", "mainline_policy", "question_policy", "rule_policy")
        ]
        review = build_release_artifact_review(gate.checks, policy_lineages=lineages)
        return {
            "version": "v30.admin_release_artifact_review.v1",
            "release_gate_run_id": gate.run_id,
            "release_gate_status": gate.status,
            "promotion_signal": gate.promotion_signal,
            "artifact_review": review,
            "boundary": "admin_release_artifact_review_is_observability_only_not_policy_or_chart_fact_mutation",
        }

    @app.get(f"{API_PREFIX}/admin/release/status-review")
    def get_post_seal_status_review() -> dict[str, object]:
        from v30.validation.post_seal_status_review import build_post_seal_status_review

        return build_post_seal_status_review()

    @app.get(f"{API_PREFIX}/admin/release/production-replay-intake")
    def get_production_replay_intake(
        persist: bool = False,
        selection_status: str = "",
        calendar_type: str = "",
        boundary_tag: str = "",
        module_ready: str = "",
        source_artifact_family: str = "",
        limit: int = 50,
    ) -> dict[str, object]:
        from v30.storage.production_replay_store import build_production_replay_store
        from v30.validation.production_replay_intake import build_production_replay_intake_batch
        from v30.validation.synthetic_case import run_synthetic_tier

        synthetic = run_synthetic_tier("real_case_calibration_pack")
        metadata_rows = [
            row.observed.get("production_replay_metadata", {})
            for row in synthetic.results
            if isinstance(row.observed.get("production_replay_metadata"), dict)
            and row.observed.get("production_replay_metadata")
        ]
        batch = build_production_replay_intake_batch(metadata_rows)
        if not persist:
            return batch
        store = build_production_replay_store(settings)
        return {
            **batch,
            "store_write": store.upsert_batch(batch),
            "store_search": store.search(
                selection_status=selection_status,
                calendar_type=calendar_type,
                boundary_tag=boundary_tag,
                module_ready=module_ready,
                source_artifact_family=source_artifact_family,
                limit=limit,
            ),
        }

    @app.get(f"{API_PREFIX}/admin/release/production-replay-intake/search")
    def search_production_replay_intake(
        selection_status: str = "",
        calendar_type: str = "",
        boundary_tag: str = "",
        module_ready: str = "",
        source_artifact_family: str = "",
        limit: int = 50,
    ) -> dict[str, object]:
        from v30.storage.production_replay_store import build_production_replay_store

        store = build_production_replay_store(settings)
        return store.search(
            selection_status=selection_status,
            calendar_type=calendar_type,
            boundary_tag=boundary_tag,
            module_ready=module_ready,
            source_artifact_family=source_artifact_family,
            limit=limit,
        )

    @app.get(f"{API_PREFIX}/admin/business/real-bazi-acceptance")
    def get_real_business_bazi_reading_acceptance(case_limit: int = 12) -> dict[str, object]:
        from v30.validation.real_business_bazi_reading_acceptance import run_real_business_bazi_reading_acceptance

        return run_real_business_bazi_reading_acceptance(case_limit=case_limit)

    @app.get(f"{API_PREFIX}/admin/business/reading-regression-pack")
    def get_real_business_bazi_reading_regression_pack(case_limit: int = 24) -> dict[str, object]:
        from v30.validation.real_business_bazi_reading_regression_pack import (
            run_real_business_bazi_reading_regression_pack,
        )

        return run_real_business_bazi_reading_regression_pack(case_limit=case_limit)

    @app.get(f"{API_PREFIX}/admin/business/answer-refresh-regression")
    def get_real_business_answer_refresh_regression(case_limit: int = 5) -> dict[str, object]:
        from v30.validation.real_business_answer_refresh_regression import run_real_business_answer_refresh_regression

        return run_real_business_answer_refresh_regression(case_limit=case_limit)

    @app.get(f"{API_PREFIX}/admin/business/boundary-blocked-input-regression")
    def get_real_business_boundary_blocked_input_regression(case_limit: int = 5) -> dict[str, object]:
        from v30.validation.real_business_boundary_blocked_input_regression import (
            run_real_business_boundary_blocked_input_regression,
        )

        return run_real_business_boundary_blocked_input_regression(case_limit=case_limit)

    @app.get(f"{API_PREFIX}/admin/business/api-contract-freeze")
    def get_real_business_api_contract_freeze() -> dict[str, object]:
        from v30.validation.real_business_api_contract_freeze import run_real_business_api_contract_freeze

        return run_real_business_api_contract_freeze()

    @app.get(f"{API_PREFIX}/admin/business/acceptance-closeout")
    def get_real_business_acceptance_closeout() -> dict[str, object]:
        from v30.validation.real_business_acceptance_closeout import run_real_business_acceptance_closeout

        return run_real_business_acceptance_closeout()

    @app.get(f"{API_PREFIX}/admin/business/steady-state")
    def get_real_business_steady_state() -> dict[str, object]:
        from v30.validation.real_business_steady_state import run_real_business_steady_state

        return run_real_business_steady_state()

    @app.get(f"{API_PREFIX}/admin/brain/acceptance")
    def get_central_brain_acceptance() -> dict[str, object]:
        from v30.validation.central_brain_acceptance import run_central_brain_acceptance

        return run_central_brain_acceptance()

    @app.get(f"{API_PREFIX}/admin/brain/session-replay")
    def get_central_brain_session_replay() -> dict[str, object]:
        from v30.validation.central_brain_session_replay import run_central_brain_session_replay

        return run_central_brain_session_replay()

    @app.get(f"{API_PREFIX}/admin/brain/failure-routing")
    def get_central_brain_failure_routing() -> dict[str, object]:
        from v30.validation.central_brain_failure_routing import run_central_brain_failure_routing

        return run_central_brain_failure_routing()

    @app.get(f"{API_PREFIX}/admin/release/candidate-review")
    def get_release_candidate_review(run_quick_gate: bool = False, sample_limit: int = 2) -> dict[str, object]:
        from v30.storage.production_replay_store import build_production_replay_store
        from v30.validation.post_seal_status_review import build_post_seal_status_review
        from v30.validation.release_candidate_review import build_release_candidate_review
        from v30.validation.release_gate import run_release_gate

        gate_payload = (
            run_release_gate(mode="quick", sample_limit=sample_limit).model_dump(mode="json")
            if run_quick_gate else {}
        )
        replay_search = build_production_replay_store(settings).search(
            selection_status="calibration_ready",
            module_ready="m4",
        )
        return build_release_candidate_review(
            post_seal_status_review=build_post_seal_status_review(),
            release_gate_result=gate_payload,
            replay_search=replay_search,
        )

    @app.get(f"{API_PREFIX}/admin/release/candidate-gate-review")
    def get_release_candidate_gate_review(
        sample_limit: int = 8,
        shard_id: int = 7,
        shard_limit: int = 16,
    ) -> dict[str, object]:
        from v30.validation.release_candidate_gate_review import build_release_candidate_gate_review
        from v30.validation.release_gate import run_release_gate

        gate = run_release_gate(
            mode="standard",
            sample_limit=sample_limit,
            shard_id=shard_id,
            shard_limit=shard_limit,
        )
        return build_release_candidate_gate_review(release_gate_result=gate.model_dump(mode="json"))

    @app.get(f"{API_PREFIX}/admin/release/boundary-finalization")
    def get_release_boundary_finalization(
        sample_limit: int = 8,
        shard_id: int = 7,
        shard_limit: int = 16,
        full_pytest_status: str = "",
    ) -> dict[str, object]:
        from v30.validation.post_seal_status_review import build_post_seal_status_review
        from v30.validation.release_boundary_finalization import build_release_boundary_finalization
        from v30.validation.release_candidate_gate_review import build_release_candidate_gate_review
        from v30.validation.release_gate import run_release_gate

        if full_pytest_status not in {"", "passed", "failed"}:
            raise HTTPException(status_code=400, detail=f"unsupported full pytest status: {full_pytest_status}")
        gate = run_release_gate(
            mode="standard",
            sample_limit=sample_limit,
            shard_id=shard_id,
            shard_limit=shard_limit,
        )
        gate_review = build_release_candidate_gate_review(release_gate_result=gate.model_dump(mode="json"))
        full_pytest_result = {"status": full_pytest_status} if full_pytest_status else {}
        return build_release_boundary_finalization(
            post_seal_status_review=build_post_seal_status_review(),
            release_candidate_gate_review=gate_review,
            full_pytest_result=full_pytest_result,
        )

    @app.get(f"{API_PREFIX}/admin/calibration/frozen-core-review")
    def get_frozen_core_calibration_review(run_gate: bool = False) -> dict[str, object]:
        from v30.validation.frozen_core_calibration_review import (
            build_frozen_core_calibration_review,
            run_frozen_core_calibration_review,
        )

        if run_gate:
            return run_frozen_core_calibration_review()
        return build_frozen_core_calibration_review(suite_results={}, training_signals=())

    @app.get(f"{API_PREFIX}/admin/calibration/targeted-candidate-review")
    def get_targeted_calibration_candidate_review(run_gate: bool = False) -> dict[str, object]:
        from v30.validation.frozen_core_calibration_review import build_frozen_core_calibration_review
        from v30.validation.targeted_calibration_candidate_review import (
            build_targeted_calibration_candidate_review,
            run_targeted_calibration_candidate_review,
        )

        if run_gate:
            return run_targeted_calibration_candidate_review()
        return build_targeted_calibration_candidate_review(
            frozen_core_calibration_review=build_frozen_core_calibration_review(
                suite_results={},
                training_signals=(),
            ),
            training_signals=(),
        )

    @app.get(f"{API_PREFIX}/admin/calibration/targeted-validation-gate")
    def get_targeted_calibration_validation_gate(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.targeted_calibration_candidate_review import build_targeted_calibration_candidate_review
        from v30.validation.targeted_calibration_validation_gate import (
            build_targeted_calibration_validation_gate,
            run_targeted_calibration_validation_gate,
        )

        if run_gate:
            return run_targeted_calibration_validation_gate(sample_limit=sample_limit)
        return build_targeted_calibration_validation_gate(
            candidate_review=build_targeted_calibration_candidate_review(
                frozen_core_calibration_review={"decision": {"calibration_baseline_ready": False}},
                training_signals=(),
            ),
            synthetic_all={"suite_id": "", "passed": False, "case_count": 0, "passed_count": 0, "failed_count": 0},
            corpus_sample={"run_id": "", "mode": "sample", "case_count": 0, "promotion_signal": ""},
        )

    @app.get(f"{API_PREFIX}/admin/calibration/targeted-pointer-review")
    def get_targeted_calibration_pointer_review(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.targeted_calibration_pointer_review import (
            build_targeted_calibration_pointer_review,
            run_targeted_calibration_pointer_review,
        )

        if run_gate:
            return run_targeted_calibration_pointer_review(sample_limit=sample_limit)
        return build_targeted_calibration_pointer_review(
            validation_gate={
                "version": "v30.targeted_calibration_validation_gate.v1",
                "decision": {"validation_gate_ready": False},
                "candidate_review_summary": {"candidate_count": 0, "families": []},
                "synthetic_all_summary": {"case_count": 0, "passed_count": 0, "passed": False},
                "corpus_518k_sample_summary": {"case_count": 0, "promotion_signal": ""},
            }
        )

    @app.get(f"{API_PREFIX}/admin/calibration/targeted-pointer-decision")
    def get_targeted_calibration_pointer_decision(
        run_gate: bool = False,
        sample_limit: int = 8,
        operator_decision: str = "defer",
    ) -> dict[str, object]:
        from v30.validation.targeted_calibration_pointer_decision import (
            build_targeted_calibration_pointer_decision,
            run_targeted_calibration_pointer_decision,
        )

        if operator_decision not in {"defer", "request_promotion"}:
            raise HTTPException(status_code=400, detail=f"unsupported operator decision: {operator_decision}")
        if run_gate:
            return run_targeted_calibration_pointer_decision(
                sample_limit=sample_limit,
                operator_decision=operator_decision,  # type: ignore[arg-type]
            )
        return build_targeted_calibration_pointer_decision(
            pointer_review={
                "version": "v30.targeted_calibration_pointer_review.v1",
                "decision": {"pointer_review_ready": False},
                "pointer_diff_summary": {"diff_count": 0, "would_change_count": 0, "rows": []},
                "active_pointer_summary": {"candidate_families": []},
            },
            operator_decision=operator_decision,  # type: ignore[arg-type]
        )

    @app.get(f"{API_PREFIX}/admin/calibration/targeted-closeout")
    def get_targeted_calibration_closeout(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.targeted_calibration_closeout import (
            build_targeted_calibration_closeout,
            run_targeted_calibration_closeout,
        )

        if run_gate:
            return run_targeted_calibration_closeout(sample_limit=sample_limit)
        return build_targeted_calibration_closeout(
            pointer_decision={
                "version": "v30.targeted_calibration_pointer_decision.v1",
                "decision": {"pointer_decision_recorded": False},
                "pointer_write_summary": {"pointer_write_performed": False, "changed_pointer_count": 0},
            }
        )

    @app.get(f"{API_PREFIX}/admin/mainline/selection")
    def get_mainline_selection(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.mainline_selection import build_mainline_selection, run_mainline_selection

        if run_gate:
            return run_mainline_selection(sample_limit=sample_limit)
        return build_mainline_selection(
            targeted_calibration_closeout={
                "version": "v30.targeted_calibration_closeout.v1",
                "decision": {
                    "closeout_ready": True,
                    "targeted_calibration_track_closed": True,
                    "decision_status": "targeted_calibration_closed_with_no_promotion",
                },
                "monitoring_baseline": {"check_count": 4},
                "policy_boundary": {
                    "policy_pointer_promotion_allowed": False,
                    "chart_fact_mutation_allowed": False,
                },
                "pointer_decision_summary": {
                    "pointer_write_performed": False,
                    "changed_pointer_count": 0,
                },
            }
        )

    app.mount(UI_PREFIX, StaticFiles(directory="frontend", html=True), name="v30-ui")

    @app.get("/v30")
    def v30_index() -> FileResponse:
        return FileResponse("frontend/index.html")

    return app


app = create_app()


def _runtime_with_hidden_factor_state(runtime: CoreRuntimeResult, hidden_factor_states) -> CoreRuntimeResult:
    payload = hidden_factor_states.get_state_payload(f"{runtime.reading_id}:hidden_factor_state")
    return attach_hidden_factor_state(runtime, payload)


def _runtime_with_actor_context(runtime: CoreRuntimeResult, payload: ReadingRequest) -> CoreRuntimeResult:
    actor_context = {
        "version": "v30.actor_context.v1",
        "actor_id": getattr(payload, "actor_id", ""),
        "session_id": getattr(payload, "session_id", ""),
        "locale": getattr(payload, "locale", "zh"),
        "boundary": "actor_context_routes_identity_and_session_not_chart_fact",
    }
    plan = runtime.question_plan.model_copy(
        update={
            "policy_effect": {
                **runtime.question_plan.policy_effect,
                "actor_context": actor_context,
            }
        }
    )
    return runtime.model_copy(update={"question_plan": plan})


def _reading_history_projection(
    payloads: list[dict[str, object]],
    *,
    actor_id: str,
    session_id: str,
    role: str,
    locale: str,
    client: str,
    limit: int,
) -> dict[str, object]:
    diagnostic = _history_diagnostic_role(role)
    owner_filter = _reading_history_owner_filter(
        actor_id=actor_id,
        session_id=session_id,
        diagnostic=diagnostic,
    )
    items = [
        _reading_history_item(
            payload,
            diagnostic=diagnostic,
            owner_scope=str(owner_filter["scope"]),
        )
        for payload in payloads
    ]
    diagnostics = {
        "version": "v30.reading_history_diagnostics.v1",
        "trace_ids": [
            str(item.get("trace_id") or "")
            for item in items
            if item.get("trace_id")
        ],
        "actor_context_visible": True,
        "internal_next_question_visible": True,
        "boundary": "history_diagnostics_are_role_gated_and_do_not_change_chart_facts",
    } if diagnostic else {}
    payload: dict[str, object] = {
        "version": "v30.reading_history_projection.v1",
        "role_key": role,
        "locale": locale,
        "client": client,
        "limit": max(1, min(limit, 100)),
        "count": len(payloads),
        "owner_filter": owner_filter,
        "visibility_contract": {
            "version": "v30.reading_history_visibility.v1",
            "diagnostic_role": diagnostic,
            "guest_user_internal_fields_hidden": not diagnostic,
            "diagnostic_fields": ["trace_id", "actor_context", "internal_next_question_id"] if diagnostic else [],
            "boundary": "history_visibility_changes_projection_not_chart_fact",
        },
        "items": items,
        "diagnostics": diagnostics,
        "boundary": "reading_history_projects_existing_readings_without_full_login_or_chart_fact_mutation",
    }
    if diagnostic:
        payload["actor_id"] = actor_id
        payload["session_id"] = session_id
    else:
        payload["actor_id_present"] = bool(actor_id)
        payload["session_id_present"] = bool(session_id)
    return payload


def _history_diagnostic_role(role: str) -> bool:
    return role in {"admin", "practitioner", "analyst", "lab"}


def _reading_history_owner_filter(*, actor_id: str, session_id: str, diagnostic: bool) -> dict[str, object]:
    if actor_id and session_id:
        scope = "actor_and_session"
    elif actor_id:
        scope = "actor_only"
    else:
        scope = "session_only"
    payload: dict[str, object] = {
        "version": "v30.reading_history_ownership.v1",
        "scope": scope,
        "actor_id_present": bool(actor_id),
        "session_id_present": bool(session_id),
        "owner_match_policy": "all_supplied_owner_keys_must_match",
        "full_login_required": False,
        "boundary": "history_owner_filter_uses_actor_session_hooks_not_full_auth_or_chart_facts",
    }
    if diagnostic:
        payload["actor_id"] = actor_id
        payload["session_id"] = session_id
    return payload


def _reading_history_item(
    payload: dict[str, object],
    *,
    diagnostic: bool,
    owner_scope: str,
) -> dict[str, object]:
    chart_context = payload.get("chart_context", {})
    chart_context = chart_context if isinstance(chart_context, dict) else {}
    question_plan = payload.get("question_plan", {})
    question_plan = question_plan if isinstance(question_plan, dict) else {}
    policy_effect = question_plan.get("policy_effect", {})
    policy_effect = policy_effect if isinstance(policy_effect, dict) else {}
    actor_context = policy_effect.get("actor_context", {})
    actor_context = actor_context if isinstance(actor_context, dict) else {}
    recommendations = question_plan.get("recommended_questions", [])
    recommendations = recommendations if isinstance(recommendations, list) else []
    interaction_state = policy_effect.get("interaction_state", {})
    interaction_state = interaction_state if isinstance(interaction_state, dict) else {}
    chart_build_source = chart_context.get("input_pillars", {})
    chart_build_source = chart_build_source if isinstance(chart_build_source, dict) else {}
    chart_build_source = chart_build_source.get("chart_build_source", {})
    chart_build_source = chart_build_source if isinstance(chart_build_source, dict) else {}
    time_layers = chart_context.get("time_layers", {})
    time_layers = time_layers if isinstance(time_layers, dict) else {}
    mainline_state = payload.get("mainline_state", {})
    mainline_state = mainline_state if isinstance(mainline_state, dict) else {}
    answer_result = payload.get("answer_result", {})
    answer_result = answer_result if isinstance(answer_result, dict) else {}
    item = {
        "reading_id": str(payload.get("reading_id") or ""),
        "created_at": str(chart_context.get("created_at") or ""),
        "locale": str(chart_context.get("locale") or actor_context.get("locale") or ""),
        "day_master": str(chart_context.get("day_master") or ""),
        "chart_status": str(chart_build_source.get("status") or time_layers.get("status") or "ready"),
        "mainline_title": str(mainline_state.get("title") or ""),
        "question_count": len(recommendations),
        "visible_next_question_id": str(interaction_state.get("visible_next_question_id") or ""),
        "answer_source": str(answer_result.get("source") or ""),
        "owner_match": {
            "version": "v30.reading_history_owner_match.v1",
            "scope": owner_scope,
            "actor_id_present": bool(actor_context.get("actor_id")),
            "session_id_present": bool(actor_context.get("session_id")),
            "diagnostic_ids_visible": diagnostic,
            "boundary": "history_owner_match_summary_hides_ids_for_customer_roles",
        },
        "boundary": "history_item_is_projection_not_runtime_payload",
    }
    if diagnostic:
        item["trace_id"] = str(payload.get("trace_id") or "")
        item["actor_context"] = actor_context
        item["internal_next_question_id"] = str(interaction_state.get("internal_next_question_id") or "")
    return item


def _target_datetime(target_year: int | None) -> datetime | None:
    if target_year is None:
        return None
    if target_year < 1900 or target_year > 2100:
        raise HTTPException(status_code=400, detail="target_year must be between 1900 and 2100")
    return datetime(target_year, 6, 1, 12, 0, tzinfo=timezone.utc)


def _load_product_store(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {"users": {}, "sessions": {}, "profiles": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}
    users = payload.get("users", {}) if isinstance(payload, dict) else {}
    sessions = payload.get("sessions", {}) if isinstance(payload, dict) else {}
    profiles = payload.get("profiles", {}) if isinstance(payload, dict) else {}
    return {
        "users": users if isinstance(users, dict) else {},
        "sessions": sessions if isinstance(sessions, dict) else {},
        "profiles": profiles if isinstance(profiles, dict) else {},
    }


def _save_product_store(path: Path, store: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(store, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _normalize_username(username: str) -> str:
    value = username.strip().lower()
    if len(value) < 3:
        raise HTTPException(status_code=400, detail="username must be at least 3 characters")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789._-@")
    if any(ch not in allowed for ch in value):
        raise HTTPException(status_code=400, detail="username contains unsupported characters")
    return value


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"pbkdf2_sha256$120000${salt}${digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt, digest = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return secrets.compare_digest(candidate, digest)
    except (ValueError, TypeError):
        return False


def _verify_product_password(password: str, user: dict[str, object]) -> bool:
    encoded = str(user.get("password") or "")
    if encoded and _verify_password(password, encoded):
        return True
    v20_hash = str(user.get("password_hash") or "")
    if not v20_hash:
        return False
    algorithm = str(user.get("password_hash_algorithm") or "")
    if algorithm == "bcrypt.v20" or v20_hash.startswith("$2"):
        try:
            import bcrypt
        except Exception:
            return False
        try:
            return bcrypt.checkpw(password.encode("utf-8"), v20_hash.encode("utf-8"))
        except ValueError:
            return False
    salt = str(user.get("salt") or "")
    legacy = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return secrets.compare_digest(v20_hash, legacy)


def _new_product_session(user: dict[str, object], *, token: str) -> dict[str, object]:
    role = str(user.get("role") or "user")
    return {
        "session_token": token,
        "username": str(user.get("username") or ""),
        "actor_id": str(user.get("actor_id") or ""),
        "session_id": f"session-{secrets.token_hex(6)}",
        "role": role,
        "main_system_role": _main_system_role(role),
        "capabilities": _product_role_capabilities(role),
        "created_at": _utc_now(),
    }


def _require_product_session(store: dict[str, dict[str, object]], session_token: str) -> dict[str, object]:
    if not session_token:
        raise HTTPException(status_code=401, detail="session_token is required")
    session = store["sessions"].get(session_token)
    if not isinstance(session, dict):
        raise HTTPException(status_code=401, detail="invalid session")
    return session


def _public_product_user(user: dict[str, object]) -> dict[str, object]:
    role = str(user.get("role") or "user")
    return {
        "username": str(user.get("username") or ""),
        "actor_id": str(user.get("actor_id") or ""),
        "display_name": str(user.get("display_name") or user.get("username") or ""),
        "role": role,
        "main_system_role": _main_system_role(role),
        "capabilities": _product_role_capabilities(role),
        "created_at": str(user.get("created_at") or ""),
    }


def _main_system_role(role: str) -> str:
    return "practitioner" if role == "admin" else role if role in {"guest", "user", "practitioner"} else "user"


def _product_role_capabilities(role: str) -> list[str]:
    if role == "admin":
        return ["admin_console", "practitioner_reading", "profile_management", "personal_reading"]
    if role == "practitioner":
        return ["practitioner_reading", "profile_management", "personal_reading"]
    return ["profile_management", "personal_reading"]


def _bazi_profile_payload(
    *,
    profile_id: str,
    payload: BaziProfileRequest,
    session: dict[str, object],
    existing: object,
) -> dict[str, object]:
    now = _utc_now()
    existing_payload = existing if isinstance(existing, dict) else {}
    return {
        "version": "v30.bazi_profile.v1",
        "profile_id": profile_id,
        "actor_id": str(session.get("actor_id") or ""),
        "display_name": payload.display_name,
        "status": payload.status if payload.status in {"active", "archived"} else "active",
        "birth_input": {
            "calendar_type": payload.calendar_type if payload.calendar_type in {"solar", "lunar"} else "solar",
            "birth_date": payload.birth_date,
            "birth_time": "00:00" if payload.unknown_hour else payload.birth_time,
            "timezone": payload.timezone,
            "birth_place": payload.birth_place,
            "gender": payload.gender or None,
            "lunar_is_leap_month": payload.lunar_is_leap_month,
            "use_true_solar_time": payload.use_true_solar_time,
            "unknown_hour": payload.unknown_hour,
            "calendar_assumption": "profile_saved",
            "source": "v30_product_profile",
        },
        "target_year": payload.target_year,
        "created_at": str(existing_payload.get("created_at") or now),
        "updated_at": now,
        "boundary": "profile_is_birth_input_metadata_not_computed_chart_fact",
    }


def _profile_bazi_preview(profile: dict[str, object]) -> dict[str, object]:
    profile_id = str(profile.get("profile_id") or "profile")
    birth_payload = profile.get("birth_input")
    if not isinstance(birth_payload, dict):
        return {
            "version": "v30.bazi_profile_preview.v1",
            "status": "blocked",
            "display": "",
            "pillar_labels": [],
            "day_master": "",
            "failures": ["birth_input_missing"],
            "boundary": "readonly_preview_requires_birth_input",
        }
    try:
        birth_input = BirthInput.model_validate(birth_payload)
    except Exception as exc:
        return {
            "version": "v30.bazi_profile_preview.v1",
            "status": "blocked",
            "display": "",
            "pillar_labels": [],
            "day_master": "",
            "failures": [str(exc)],
            "boundary": "readonly_preview_requires_valid_birth_input",
        }
    try:
        target_year = profile.get("target_year")
        target_dt = _target_datetime(int(target_year)) if target_year else None
    except Exception:
        target_dt = None
    try:
        build_result = build_chart_context_from_birth_input(
            reading_id=f"{profile_id}:preview",
            birth_input=birth_input,
            locale="zh",
            created_at=target_dt,
        )
    except Exception as exc:
        return {
            "version": "v30.bazi_profile_preview.v1",
            "status": "blocked",
            "display": "",
            "pillar_labels": [],
            "day_master": "",
            "failures": [str(exc)],
            "boundary": "readonly_preview_failed_without_profile_mutation",
        }
    pillars = build_result.four_pillar_result.pillars if build_result.four_pillar_result else {}
    pillar_labels = [
        {"label": "年", "pillar": str(pillars.get("year") or "")},
        {"label": "月", "pillar": str(pillars.get("month") or "")},
        {"label": "日", "pillar": str(pillars.get("day") or "")},
        {"label": "时", "pillar": str(pillars.get("hour") or "")},
    ]
    display = " ".join(row["pillar"] for row in pillar_labels if row["pillar"])
    return {
        "version": "v30.bazi_profile_preview.v1",
        "status": build_result.status,
        "display": display,
        "pillar_labels": pillar_labels,
        "day_master": build_result.chart_context.day_master if build_result.chart_context else "",
        "failures": build_result.failures,
        "boundary": "deterministic_readonly_preview_not_stored_profile_fact",
    }


def _thinking_summary_policy_skipped_call(step: dict[str, object], policy: dict[str, object]) -> dict[str, object]:
    enhancement = str(policy.get("llm_enhancement") or "skip")
    fallback_reason = (
        "stage_summary_policy_not_required"
        if enhancement == "not_required"
        else "stage_summary_policy_skipped_llm"
    )
    return {
        "version": "v30.bazi_llm_thinking_step_summary_call.v1",
        "status": "fallback",
        "fallback_reason": fallback_reason,
        "text": "",
        "provider": "",
        "model": "",
        "executed": False,
        "step_id": str(step.get("step_id") or ""),
        "summary_policy": policy,
        "prompt_request": {
            "version": "v30.thinking_step_summary_prompt_policy_skip.v1",
            "task": "thinking_step_summary",
            "step_id": str(step.get("step_id") or ""),
            "raw_runtime_payload_included": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "stage_summary_policy_skips_llm_without_prompt_execution",
        },
        "readiness": {},
        "boundary": "thinking_step_summary_policy_skip_keeps_central_brain_summary_without_llm_call",
    }


def _thinking_summary_required_unavailable_call(call: dict[str, object], policy: dict[str, object]) -> dict[str, object]:
    if policy.get("llm_enhancement") != "auto" or call.get("status") != "fallback":
        return call
    reason = str(call.get("fallback_reason") or "llm_required_but_unavailable")
    if not _thinking_summary_fallback_is_model_unavailable(reason):
        return call
    return {
        **call,
        "status": "unavailable",
        "unavailable_reason": reason,
        "user_message": _thinking_summary_unavailable_message(reason),
        "boundary": "llm_required_stage_reports_model_unavailable_without_rule_fallback",
    }


def _thinking_summary_fallback_is_model_unavailable(reason: str) -> bool:
    return (
        reason == "llm_required_but_unavailable"
        or reason == "provider_not_ready"
        or reason == "execute_flag_disabled"
        or reason == "empty_text"
        or reason.startswith("call_failed:")
    )


def _thinking_summary_unavailable_message(reason: str) -> str:
    if reason == "empty_text":
        return "本页需要大模型推演，但模型没有返回可用文字。请重试这一页。"
    if reason == "execute_flag_disabled":
        return "本页需要大模型推演，但当前配置没有启用模型执行。请检查 LLM 执行开关。"
    return "本页需要大模型推演，但当前没有连接到可用模型。请检查 Ollama/SSH 隧道后重试。"


def _thinking_summary_panel_source(summary_panel: dict[str, object], call: dict[str, object]) -> str:
    if call.get("status") == "unavailable":
        return "llm_unavailable"
    return str(summary_panel.get("source") or "central_brain_rule_summary")


def _answer_llm_role_key(role_key: object) -> str:
    role = str(role_key or "user")
    if role in {"guest", "user", "practitioner"}:
        return role
    return "practitioner"


def _step_with_llm_final_decision(
    step: dict[str, object],
    summary_panel: dict[str, object],
    call: dict[str, object],
) -> dict[str, object]:
    analysis = dict(step.get("analysis_result") if isinstance(step.get("analysis_result"), dict) else {})
    review = call.get("central_brain_review") if isinstance(call.get("central_brain_review"), dict) else {}
    derivation = call.get("derivation") if isinstance(call.get("derivation"), dict) else {}
    stage_point_set = review.get("stage_point_set") if isinstance(review.get("stage_point_set"), dict) else step.get("stage_point_set")
    stage_points = review.get("stage_points") if isinstance(review.get("stage_points"), list) else step.get("stage_points")
    if call.get("status") == "accepted" and review.get("status") == "accepted":
        analysis["final_decision"] = {
            "version": "v30.stage_final_decision.v1",
            "source": "central_brain_reviewed_gemma4_derivation",
            "conclusion": str(review.get("final_conclusion") or analysis.get("conclusion") or ""),
            "advice": str(review.get("final_advice") or analysis.get("next_focus") or ""),
            "public_thinking_lines": review.get("public_thinking_lines") or derivation.get("public_thinking_lines") or [],
            "used_evidence": review.get("used_evidence") or derivation.get("used_evidence") or [],
            "uncertainty": review.get("uncertainty") or derivation.get("uncertainty") or [],
            "stage_point_set": stage_point_set if isinstance(stage_point_set, dict) else {},
            "stage_points": stage_points if isinstance(stage_points, list) else [],
            "review": review,
            "boundary": "final_decision_requires_central_brain_reviewed_llm_derivation",
        }
    return {
        **step,
        "analysis_result": analysis,
        "stage_point_set": stage_point_set if isinstance(stage_point_set, dict) else step.get("stage_point_set", {}),
        "stage_points": stage_points if isinstance(stage_points, list) else step.get("stage_points", []),
        "summary_panel": summary_panel,
        "boundary": "thinking_step_summary_enhancement_does_not_mutate_chart_facts",
    }


def _central_state_with_practitioner_selections(
    runtime: CoreRuntimeResult,
    selections: list[dict[str, object]],
) -> dict[str, object]:
    policy_effect = runtime.question_plan.policy_effect
    return build_central_reading_state(
        reading_id=runtime.reading_id,
        role_key=str(runtime.question_plan.role_key),
        diagnosis=_dict(policy_effect.get("real_bazi_diagnosis")),
        recommendations=runtime.question_plan.recommended_questions,
        question_dialogue_graph=_dict(policy_effect.get("question_dialogue_graph")),
        interaction_state=_dict(policy_effect.get("interaction_state")),
        practical_reading_context=_dict(policy_effect.get("practical_reading_context")),
        ranked_decisions=_dict(policy_effect.get("ranked_decisions")),
        model_signal_summary=_dict(policy_effect.get("model_signal_summary")),
        question_policy=_dict(policy_effect.get("question_policy_payload")),
        question_outcomes=_list(policy_effect.get("question_outcomes")),
        practitioner_selections=selections,
        active_stage_id=str(policy_effect.get("active_stage_id") or ""),
    )


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[dict[str, object]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _next_surface_question_id(surface: dict[str, object]) -> str:
    calibration = _dict(surface.get("calibration_surface"))
    cards = calibration.get("visible_probe_cards")
    if isinstance(cards, list):
        for card in cards:
            if isinstance(card, dict) and card.get("question_id"):
                return str(card.get("question_id") or "")
    conversation = _dict(surface.get("conversation_surface"))
    suggested = _dict(conversation.get("suggested_question"))
    if suggested.get("question_id"):
        return str(suggested.get("question_id") or "")
    return ""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
