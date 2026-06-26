from __future__ import annotations

import hashlib
import json
import os
import secrets
import shlex
import subprocess
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from v30.config import load_settings
from v30.contracts import BirthInput, CoreRuntimeResult
from v30.core.chart_context import build_chart_context_from_birth_input
from v30.learning import DEFAULT_AUTO_TRAINING_FAMILIES, run_auto_apply_training
from v30.ops.admin_runtime import (
    admin_runtime_config_status,
    apply_database_schema,
    database_admin_status,
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
from v30.llm import compose_bazi_llm_answer_draft, load_v30_llm_provider_config_from_env
from v30.presentation.client_profiles import CLIENT_PROFILES
from v30.presentation.client_model import build_presentation_model
from v30.policy import build_promotion_lineage, load_question_policy_comparison
from v30.runtime import attach_hidden_factor_state, attach_question_outcome, create_runtime_from_context, create_smoke_runtime
from v30.storage.names import redis_key
from v30.storage.artifacts import search_518k_validation_artifacts, search_validation_artifacts
from v30.storage.hidden_factor_state import build_hidden_factor_state_repository
from v30.storage.redis_cache import build_runtime_cache
from v30.storage.repository import build_runtime_repository


API_PREFIX = "/api/v30"
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


class TrainingRunRequest(BaseModel):
    training_run_id: str | None = None
    families: list[str] = Field(default_factory=list)


class M3BackgroundRunRequest(BaseModel):
    sample_limit: int = Field(default=8, ge=1, le=256)
    persist_m3_to_db: bool = True
    include_shard: bool = False
    shard_id: int = Field(default=7, ge=0)
    shard_limit: int = Field(default=16, ge=1, le=512)
    include_readiness_matrix: bool = False


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
    m3_background_jobs: dict[str, dict[str, object]] = {}
    m3_background_lock = threading.Lock()
    latest_m3_background_job_id = ""

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

    def _read_text_tail(path: Path, *, limit: int) -> str:
        try:
            return path.read_text(encoding="utf-8")[-limit:]
        except OSError:
            return ""

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
            "ui_prefix": UI_PREFIX,
            "runtime_dir": str(settings.runtime_dir),
            "repository": settings.repository,
            "redis_cache": cache is not None,
            "redis_probe_key": redis_key(settings.env, "lock", "health"),
        }

    @app.post(f"{API_PREFIX}/auth/register")
    def register_user(payload: AuthRegisterRequest) -> dict[str, object]:
        store = _load_product_store(product_store_path)
        username = _normalize_username(payload.username)
        if username in store["users"]:
            raise HTTPException(status_code=409, detail="username already exists")
        if len(payload.password) < 6:
            raise HTTPException(status_code=400, detail="password must be at least 6 characters")
        role = payload.role if payload.role in {"user", "practitioner", "admin"} else "user"
        if role == "admin" and any(
            isinstance(existing_user, dict) and existing_user.get("role") == "admin"
            for existing_user in store["users"].values()
        ):
            raise HTTPException(status_code=409, detail="admin already exists")
        actor_id = f"actor-{secrets.token_hex(6)}"
        user = {
            "username": username,
            "actor_id": actor_id,
            "display_name": payload.display_name or username,
            "role": role,
            "password": _hash_password(payload.password),
            "created_at": _utc_now(),
        }
        token = secrets.token_urlsafe(24)
        session = _new_product_session(user, token=token)
        store["users"][username] = user
        store["sessions"][token] = session
        _save_product_store(product_store_path, store)
        return {
            "version": "v30.product_auth_session.v1",
            "status": "registered",
            "session": session,
            "user": _public_product_user(user),
            "boundary": "product_auth_does_not_change_chart_facts_or_runtime_projection_contract",
        }

    @app.post(f"{API_PREFIX}/auth/login")
    def login_user(payload: AuthLoginRequest) -> dict[str, object]:
        store = _load_product_store(product_store_path)
        username = _normalize_username(payload.username)
        user = store["users"].get(username)
        if not isinstance(user, dict) or not _verify_product_password(payload.password, user):
            raise HTTPException(status_code=401, detail="invalid username or password")
        token = secrets.token_urlsafe(24)
        session = _new_product_session(user, token=token)
        store["sessions"][token] = session
        _save_product_store(product_store_path, store)
        return {
            "version": "v30.product_auth_session.v1",
            "status": "logged_in",
            "session": session,
            "user": _public_product_user(user),
            "boundary": "product_auth_uses_actor_session_hooks_without_mutating_bazi_facts",
        }

    @app.get(f"{API_PREFIX}/auth/session")
    def get_auth_session(session_token: str = "") -> dict[str, object]:
        store = _load_product_store(product_store_path)
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
        store = _load_product_store(product_store_path)
        removed = store["sessions"].pop(payload.session_token, None) is not None
        _save_product_store(product_store_path, store)
        return {
            "version": "v30.product_auth_logout.v1",
            "status": "logged_out" if removed else "session_not_found",
            "boundary": "logout_removes_product_session_only",
        }

    @app.get(f"{API_PREFIX}/profiles")
    def list_bazi_profiles(session_token: str = "") -> dict[str, object]:
        store = _load_product_store(product_store_path)
        session = _require_product_session(store, session_token)
        actor_id = str(session.get("actor_id") or "")
        profiles = [
            row for row in store["profiles"].values()
            if isinstance(row, dict) and row.get("actor_id") == actor_id
        ]
        profiles.sort(key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)
        return {
            "version": "v30.bazi_profile_list.v1",
            "count": len(profiles),
            "items": profiles,
            "boundary": "bazi_profiles_store_birth_input_metadata_not_chart_facts",
        }

    @app.post(f"{API_PREFIX}/profiles")
    def save_bazi_profile(payload: BaziProfileRequest) -> dict[str, object]:
        store = _load_product_store(product_store_path)
        session = _require_product_session(store, payload.session_token)
        profile_id = payload.profile_id or f"profile-{secrets.token_hex(6)}"
        existing = store["profiles"].get(profile_id)
        if isinstance(existing, dict) and existing.get("actor_id") != session.get("actor_id"):
            raise HTTPException(status_code=403, detail="profile owner mismatch")
        profile = _bazi_profile_payload(profile_id=profile_id, payload=payload, session=session, existing=existing)
        store["profiles"][profile_id] = profile
        _save_product_store(product_store_path, store)
        return {
            "version": "v30.bazi_profile.v1",
            "status": "saved",
            "profile": profile,
            "boundary": "profile_save_does_not_compute_or_mutate_chart_facts",
        }

    @app.get(f"{API_PREFIX}/ui/capabilities")
    def get_ui_capabilities() -> dict[str, object]:
        public_clients = ["web", "mobile", "admin"]
        public_roles = [
            {
                "key": "guest",
                "label": "游客",
                "default_client": "mobile",
                "surface": "preview",
                "diagnostics_visible": False,
            },
            {
                "key": "user",
                "label": "普通用户",
                "default_client": "web",
                "surface": "customer_reading",
                "diagnostics_visible": False,
            },
            {
                "key": "practitioner",
                "label": "命理师",
                "default_client": "web",
                "surface": "practitioner_review",
                "diagnostics_visible": True,
            },
            {
                "key": "admin",
                "label": "Admin",
                "default_client": "admin",
                "surface": "operations",
                "diagnostics_visible": True,
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
                    "label": {"web": "Web", "mobile": "Mobile", "admin": "Admin"}[key],
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
                "structured_answer_fields": ["selected_option", "structured_payload", "confidence", "feedback_tags"],
                "structured_answer_contract": "v30.answer_constraints.v1",
                "interaction_brain_result_contract": "v30.unified_interaction_brain_result.v1",
                "invalid_input_action": "ask_user_to_reselect",
                "diagnostic_summary_contract": "v30.interaction_brain_diagnostics_summary.v1",
                "synthetic_tier": "interaction_brain_structured_constraints",
                "dedicated_interactions_endpoint": "deferred_until_answer_endpoint_stable",
                "llm_answer_enhancement_mode": "fast_answer_then_optional_llm_enhancement",
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

    @app.post(f"{API_PREFIX}/readings/{{reading_id}}/questions/{{question_id}}/answer")
    def answer_question(reading_id: str, question_id: str, payload: AnswerRequest) -> dict[str, object]:
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
        visible_next = view_payload.get("reading_surface", {}).get("next_question", {})
        return {
            "reading_id": reading_id,
            "question_id": question_id,
            "accepted": True,
            "outcome_event_id": event.get("event_id", ""),
            "question_outcome_consumed": True,
            "next_question_id": visible_next.get("question_id") if isinstance(visible_next, dict) else None,
            "internal_next_question_id": graph.get("next_question_id") if isinstance(graph, dict) else None,
            "interaction_state": interaction_state if isinstance(interaction_state, dict) else {},
            "interaction_brain_result": public_interaction_brain_result(interaction_brain_result) if isinstance(interaction_brain_result, dict) else {},
            "view": view_payload,
        }

    @app.post(f"{API_PREFIX}/readings/{{reading_id}}/questions/{{question_id}}/answer/llm")
    def enhance_answer_with_llm(
        reading_id: str,
        question_id: str,
        payload: LLMAnswerEnhancementRequest,
    ) -> dict[str, object]:
        runtime_payload = _cache_get_reading_payload(reading_id)
        runtime_payload = runtime_payload or repository.get_runtime_payload(reading_id)
        if runtime_payload is None:
            raise HTTPException(status_code=404, detail="reading not found")
        runtime = CoreRuntimeResult.model_validate(runtime_payload)
        if runtime.answer_context is None or runtime.answer_result is None:
            raise HTTPException(status_code=409, detail="answer context is not ready")
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
            role_key=payload.role or runtime.question_plan.role_key,
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
            "boundary": "llm_answer_enhancement_is_optional_expression_layer_not_chart_fact_source",
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

    @app.post(f"{API_PREFIX}/admin/runtime/llm/test")
    def test_admin_llm_runtime(payload: dict[str, object]) -> dict[str, object]:
        return llm_admin_test(payload)

    @app.post(f"{API_PREFIX}/admin/training/run")
    def run_training(payload: TrainingRunRequest) -> dict[str, object]:
        families = tuple(payload.families) if payload.families else DEFAULT_AUTO_TRAINING_FAMILIES
        invalid = sorted(set(families) - set(DEFAULT_AUTO_TRAINING_FAMILIES))
        if invalid:
            raise HTTPException(status_code=400, detail=f"unsupported training families: {','.join(invalid)}")
        result = run_auto_apply_training(
            families=families,
            training_run_id=payload.training_run_id,
        )
        return result.model_dump(mode="json")

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

    @app.get(f"{API_PREFIX}/admin/validation/synthetic-coverage-manifest")
    def get_synthetic_coverage_manifest() -> dict[str, object]:
        from v30.validation.synthetic_coverage_manifest import run_synthetic_coverage_manifest

        return run_synthetic_coverage_manifest()

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

    @app.get(f"{API_PREFIX}/admin/release/external-dry-run")
    def get_external_release_dry_run(
        run_gate: bool = False,
        sample_limit: int = 8,
        full_pytest_decision: str = "defer",
    ) -> dict[str, object]:
        from v30.validation.external_release_dry_run import (
            build_external_release_dry_run,
            run_external_release_dry_run,
        )

        if full_pytest_decision not in {"defer", "record_passed", "record_failed"}:
            raise HTTPException(status_code=400, detail=f"unsupported full pytest decision: {full_pytest_decision}")
        if run_gate:
            return run_external_release_dry_run(
                sample_limit=sample_limit,
                full_pytest_decision=full_pytest_decision,  # type: ignore[arg-type]
            )
        return build_external_release_dry_run(
            mainline_selection={
                "version": "v30.mainline_selection.v1",
                "status": "ready_for_next_mainline",
                "decision": {
                    "selected_task_id": "R13",
                    "selected_track": "external_release_boundary",
                    "full_pytest_run_now": False,
                    "policy_pointer_promotion_allowed": False,
                    "chart_fact_mutation_allowed": False,
                },
            },
            full_pytest_decision=full_pytest_decision,  # type: ignore[arg-type]
        )

    @app.get(f"{API_PREFIX}/admin/release/full-pytest-decision")
    def get_external_release_full_pytest_decision(
        run_gate: bool = False,
        sample_limit: int = 8,
        full_pytest_decision: str = "defer",
    ) -> dict[str, object]:
        from v30.validation.external_release_full_pytest_decision import (
            build_external_release_full_pytest_decision,
            run_external_release_full_pytest_decision,
        )

        if full_pytest_decision not in {"defer", "record_passed", "record_failed"}:
            raise HTTPException(status_code=400, detail=f"unsupported full pytest decision: {full_pytest_decision}")
        if run_gate:
            return run_external_release_full_pytest_decision(
                sample_limit=sample_limit,
                full_pytest_decision=full_pytest_decision,  # type: ignore[arg-type]
            )
        return build_external_release_full_pytest_decision(
            external_release_dry_run={
                "version": "v30.external_release_dry_run.v1",
                "status": "completed",
                "decision": {
                    "decision_status": "external_release_dry_run_deferred_full_pytest",
                    "dry_run_review_completed": True,
                    "external_release_ready": False,
                    "full_pytest_deferred": True,
                },
                "policy_boundary": {
                    "policy_pointer_promotion_allowed": False,
                    "pointer_write_allowed": False,
                    "chart_fact_mutation_allowed": False,
                },
            },
            full_pytest_decision=full_pytest_decision,  # type: ignore[arg-type]
        )

    @app.get(f"{API_PREFIX}/admin/release/blocked-status")
    def get_external_release_blocked_status(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.external_release_blocked_status import (
            build_external_release_blocked_status,
            run_external_release_blocked_status,
        )

        if run_gate:
            return run_external_release_blocked_status(sample_limit=sample_limit)
        return build_external_release_blocked_status(
            external_release_full_pytest_decision={
                "version": "v30.external_release_full_pytest_decision.v1",
                "status": "completed",
                "decision": {
                    "decision_status": "external_release_full_pytest_deferred",
                    "external_release_ready": False,
                    "external_release_blocked": True,
                    "full_pytest_deferred": True,
                },
                "full_pytest_execution_summary": {"status": "deferred"},
                "policy_boundary": {
                    "policy_pointer_promotion_allowed": False,
                    "pointer_write_allowed": False,
                    "chart_fact_mutation_allowed": False,
                },
            }
        )

    @app.get(f"{API_PREFIX}/admin/release/post-boundary-authorization")
    def get_post_release_boundary_authorization(
        run_gate: bool = False,
        sample_limit: int = 8,
        authorization_decision: str = "pause",
    ) -> dict[str, object]:
        from v30.validation.post_release_boundary_authorization import (
            build_post_release_boundary_authorization,
            run_post_release_boundary_authorization,
        )

        if authorization_decision not in {"pause", "authorize_full_pytest"}:
            raise HTTPException(status_code=400, detail=f"unsupported authorization decision: {authorization_decision}")
        if run_gate:
            return run_post_release_boundary_authorization(
                sample_limit=sample_limit,
                authorization_decision=authorization_decision,  # type: ignore[arg-type]
            )
        return build_post_release_boundary_authorization(
            external_release_blocked_status={
                "version": "v30.external_release_blocked_status.v1",
                "status": "completed",
                "decision": {
                    "decision_status": "external_release_blocked_pending_full_pytest",
                    "external_release_ready": False,
                    "external_release_blocked": True,
                    "full_pytest_deferred": True,
                },
                "release_blockers": [{"blocker_id": "full_pytest_deferred"}],
                "policy_boundary": {
                    "policy_pointer_promotion_allowed": False,
                    "pointer_write_allowed": False,
                    "chart_fact_mutation_allowed": False,
                },
            },
            authorization_decision=authorization_decision,  # type: ignore[arg-type]
        )

    @app.get(f"{API_PREFIX}/admin/mainline/selection-after-release-pause")
    def get_mainline_selection_after_release_pause(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.mainline_selection_after_release_pause import (
            build_mainline_selection_after_release_pause,
            run_mainline_selection_after_release_pause,
        )

        if run_gate:
            return run_mainline_selection_after_release_pause(sample_limit=sample_limit)
        return build_mainline_selection_after_release_pause(
            post_release_boundary_authorization={
                "version": "v30.post_release_boundary_authorization.v1",
                "status": "completed",
                "decision": {
                    "decision_status": "release_boundary_paused_pending_full_pytest_authorization",
                    "release_boundary_paused": True,
                    "full_pytest_authorized": False,
                    "full_pytest_run_triggered": False,
                    "external_release_ready": False,
                },
                "release_boundary_state": {"external_release_allowed": False},
                "policy_boundary": {
                    "policy_pointer_promotion_allowed": False,
                    "pointer_write_allowed": False,
                    "chart_fact_mutation_allowed": False,
                },
            }
        )

    @app.get(f"{API_PREFIX}/admin/core/monitoring-loop")
    def get_core_monitoring_loop(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.core_monitoring_loop import build_core_monitoring_loop, run_core_monitoring_loop

        if run_gate:
            return run_core_monitoring_loop(sample_limit=sample_limit)
        return build_core_monitoring_loop(
            mainline_selection_after_release_pause={
                "version": "v30.mainline_selection_after_release_pause.v1",
                "status": "ready_for_next_mainline",
                "decision": {
                    "decision_status": "core_monitoring_and_calibration_loop_selected",
                    "selected_task_id": "P0",
                    "selected_track": "core_monitoring_and_calibration",
                    "external_release_ready": False,
                    "full_pytest_authorized": False,
                    "policy_pointer_promotion_allowed": False,
                    "chart_fact_mutation_allowed": False,
                },
            },
            targeted_calibration_closeout={
                "version": "v30.targeted_calibration_closeout.v1",
                "decision": {
                    "decision_status": "targeted_calibration_closed_with_no_promotion",
                    "closeout_ready": True,
                    "targeted_calibration_track_closed": True,
                },
                "pointer_decision_summary": {"pointer_write_performed": False},
                "policy_boundary": {
                    "policy_pointer_promotion_allowed": False,
                    "chart_fact_mutation_allowed": False,
                },
                "monitoring_baseline": {
                    "check_count": 4,
                    "full_pytest_required": False,
                    "full_518k_required": False,
                    "checks": [
                        {"check_id": "m1_m8_frozen_scope"},
                        {"check_id": "targeted_candidate_review"},
                        {"check_id": "targeted_validation_gate"},
                        {"check_id": "pointer_decision_no_write"},
                    ],
                },
            },
        )

    @app.get(f"{API_PREFIX}/admin/core/lightweight-monitoring-checks")
    def get_lightweight_core_monitoring_checks(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.lightweight_core_monitoring_checks import (
            build_lightweight_core_monitoring_checks,
            run_lightweight_core_monitoring_checks,
        )

        if run_gate:
            return run_lightweight_core_monitoring_checks(sample_limit=sample_limit)
        return build_lightweight_core_monitoring_checks(
            core_monitoring_loop={
                "version": "v30.core_monitoring_loop.v1",
                "status": "completed",
                "decision": {
                    "decision_status": "core_monitoring_loop_ready",
                    "monitoring_loop_ready": True,
                    "policy_pointer_promotion_allowed": False,
                    "chart_fact_mutation_allowed": False,
                },
                "monitoring_baseline_summary": {"check_count": 4, "required_check_count": 4},
            },
            check_results=[
                {
                    "check_id": "m1_m8_frozen_scope",
                    "decision_status": "ready_for_targeted_calibration_iteration",
                    "expected_status": "ready_for_targeted_calibration_iteration",
                },
                {
                    "check_id": "targeted_candidate_review",
                    "decision_status": "ready_for_validation_gate_review",
                    "expected_status": "ready_for_validation_gate_review",
                },
                {
                    "check_id": "targeted_validation_gate",
                    "decision_status": "ready_for_policy_pointer_review",
                    "expected_status": "ready_for_policy_pointer_review",
                },
                {
                    "check_id": "pointer_decision_no_write",
                    "decision_status": "pointer_promotion_deferred",
                    "expected_status": "pointer_promotion_deferred",
                },
            ],
        )

    @app.get(f"{API_PREFIX}/admin/core/calibration-observation-summary")
    def get_core_calibration_observation_summary(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.core_calibration_observation_summary import (
            build_core_calibration_observation_summary,
            run_core_calibration_observation_summary,
        )

        if run_gate:
            return run_core_calibration_observation_summary(sample_limit=sample_limit)
        return build_core_calibration_observation_summary(
            lightweight_monitoring_checks={
                "version": "v30.lightweight_core_monitoring_checks.v1",
                "status": "completed",
                "decision": {
                    "decision_status": "lightweight_core_monitoring_checks_passed",
                    "monitoring_checks_completed": True,
                    "regression_detected": False,
                    "failed_check_ids": [],
                    "full_pytest_required": False,
                    "full_518k_required": False,
                    "policy_pointer_promotion_allowed": False,
                    "pointer_write_performed": False,
                    "chart_fact_mutation_allowed": False,
                },
                "check_summary": {
                    "required_check_count": 4,
                    "executed_check_count": 4,
                    "passed_check_count": 4,
                    "failed_check_count": 0,
                    "missing_check_ids": [],
                },
                "checks": [
                    {
                        "check_id": "m1_m8_frozen_scope",
                        "decision_status": "ready_for_targeted_calibration_iteration",
                        "expected_status": "ready_for_targeted_calibration_iteration",
                        "passed": True,
                    },
                    {
                        "check_id": "targeted_candidate_review",
                        "decision_status": "ready_for_validation_gate_review",
                        "expected_status": "ready_for_validation_gate_review",
                        "passed": True,
                    },
                    {
                        "check_id": "targeted_validation_gate",
                        "decision_status": "ready_for_policy_pointer_review",
                        "expected_status": "ready_for_policy_pointer_review",
                        "passed": True,
                    },
                    {
                        "check_id": "pointer_decision_no_write",
                        "decision_status": "pointer_promotion_deferred",
                        "expected_status": "pointer_promotion_deferred",
                        "passed": True,
                    },
                ],
                "policy_boundary": {"pointer_write_allowed": False},
                "next_mainline_selection": {"task_id": "P2"},
            },
        )

    @app.get(f"{API_PREFIX}/admin/core/calibration-drift-watch")
    def get_core_calibration_drift_watch(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.core_calibration_drift_watch import (
            build_core_calibration_drift_watch,
            run_core_calibration_drift_watch,
        )

        if run_gate:
            return run_core_calibration_drift_watch(sample_limit=sample_limit)
        return build_core_calibration_drift_watch(
            core_calibration_observation_summary={
                "version": "v30.core_calibration_observation_summary.v1",
                "status": "completed",
                "decision": {
                    "decision_status": "core_calibration_observation_summary_ready",
                    "observation_summary_ready": True,
                    "stable_observation_count": 4,
                    "needs_review_observation_count": 0,
                    "needs_review_check_ids": [],
                    "regression_detected": False,
                    "focused_module_fix_required": False,
                    "full_pytest_required": False,
                    "full_518k_required": False,
                    "policy_pointer_promotion_allowed": False,
                    "pointer_write_performed": False,
                    "chart_fact_mutation_allowed": False,
                },
                "monitoring_evidence_summary": {
                    "passed_check_count": 4,
                    "required_check_count": 4,
                },
            },
            calibration_evidence=[],
        )

    @app.get(f"{API_PREFIX}/admin/core/focused-calibration-evidence-queue")
    def get_focused_core_calibration_evidence_queue(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.focused_core_calibration_evidence_queue import (
            build_focused_core_calibration_evidence_queue,
            run_focused_core_calibration_evidence_queue,
        )

        if run_gate:
            return run_focused_core_calibration_evidence_queue(sample_limit=sample_limit)
        return build_focused_core_calibration_evidence_queue(
            core_calibration_drift_watch={
                "version": "v30.core_calibration_drift_watch.v1",
                "status": "completed",
                "decision": {
                    "decision_status": "core_calibration_drift_watch_ready",
                    "drift_watch_ready": True,
                    "drift_detected": False,
                    "drift_route_count": 0,
                    "focused_module_fix_required": False,
                    "full_pytest_required": False,
                    "full_518k_required": False,
                    "policy_pointer_promotion_allowed": False,
                    "pointer_write_performed": False,
                    "chart_fact_mutation_allowed": False,
                },
            },
            calibration_evidence=[],
        )

    @app.get(f"{API_PREFIX}/admin/core/calibration-queue-review")
    def get_core_calibration_queue_review(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.core_calibration_queue_review import (
            build_core_calibration_queue_review,
            run_core_calibration_queue_review,
        )

        if run_gate:
            return run_core_calibration_queue_review(sample_limit=sample_limit)
        return build_core_calibration_queue_review(
            focused_core_calibration_evidence_queue={
                "version": "v30.focused_core_calibration_evidence_queue.v1",
                "status": "completed",
                "decision": {
                    "decision_status": "focused_core_calibration_evidence_queue_ready",
                    "evidence_queue_ready": True,
                    "queued_evidence_count": 0,
                    "queue_item_count": 0,
                    "module_queue_count": 0,
                    "focused_module_fix_required": False,
                    "full_pytest_required": False,
                    "full_518k_required": False,
                    "policy_pointer_promotion_allowed": False,
                    "pointer_write_performed": False,
                    "chart_fact_mutation_allowed": False,
                },
                "queue_items": [],
            },
        )

    @app.get(f"{API_PREFIX}/admin/core/calibration-watch-closeout")
    def get_core_calibration_watch_closeout(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.core_calibration_watch_closeout import (
            build_core_calibration_watch_closeout,
            run_core_calibration_watch_closeout,
        )

        if run_gate:
            return run_core_calibration_watch_closeout(sample_limit=sample_limit)
        return build_core_calibration_watch_closeout(
            core_calibration_queue_review={
                "version": "v30.core_calibration_queue_review.v1",
                "status": "completed",
                "decision": {
                    "decision_status": "core_calibration_queue_review_ready",
                    "queue_review_ready": True,
                    "reviewed_module_count": 0,
                    "focused_fix_candidate_count": 0,
                    "focused_module_fix_required": False,
                    "continue_lightweight_watch": True,
                    "full_pytest_required": False,
                    "full_518k_required": False,
                    "policy_pointer_promotion_allowed": False,
                    "pointer_write_performed": False,
                    "chart_fact_mutation_allowed": False,
                },
            },
        )

    @app.get(f"{API_PREFIX}/admin/core/monitoring-cadence-baseline")
    def get_core_monitoring_cadence_baseline(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.core_monitoring_cadence_baseline import (
            build_core_monitoring_cadence_baseline,
            run_core_monitoring_cadence_baseline,
        )

        if run_gate:
            return run_core_monitoring_cadence_baseline(sample_limit=sample_limit)
        return build_core_monitoring_cadence_baseline(
            core_calibration_watch_closeout={
                "version": "v30.core_calibration_watch_closeout.v1",
                "status": "completed",
                "decision": {
                    "decision_status": "core_calibration_watch_closeout_ready",
                    "watch_closeout_ready": True,
                    "closeout_check_count": 4,
                    "passed_closeout_check_count": 4,
                    "current_cycle_closed": True,
                    "future_monitoring_ready": True,
                    "focused_module_fix_required": False,
                    "full_pytest_required": False,
                    "full_518k_required": False,
                    "policy_pointer_promotion_allowed": False,
                    "pointer_write_performed": False,
                    "chart_fact_mutation_allowed": False,
                },
                "watch_cycle_summary": {
                    "future_evidence_entrypoint": "P4 Focused Core Calibration Evidence Queue",
                    "future_review_entrypoint": "P5 Core Calibration Queue Review",
                },
            },
        )

    @app.get(f"{API_PREFIX}/admin/core/monitoring-cadence-documentation-sync")
    def get_core_monitoring_cadence_documentation_sync(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.core_monitoring_cadence_documentation_sync import (
            REQUIRED_SYNC_DOCUMENTS,
            build_core_monitoring_cadence_documentation_sync,
            run_core_monitoring_cadence_documentation_sync,
        )

        if run_gate:
            return run_core_monitoring_cadence_documentation_sync(sample_limit=sample_limit)
        return build_core_monitoring_cadence_documentation_sync(
            core_monitoring_cadence_baseline={
                "version": "v30.core_monitoring_cadence_baseline.v1",
                "status": "completed",
                "decision": {
                    "decision_status": "core_monitoring_cadence_baseline_ready",
                    "cadence_baseline_ready": True,
                    "current_cycle_closed": True,
                    "future_monitoring_ready": True,
                    "default_heavy_validation_allowed": False,
                    "focused_module_fix_required": False,
                    "full_pytest_required": False,
                    "full_518k_required": False,
                    "policy_pointer_promotion_allowed": False,
                    "pointer_write_performed": False,
                    "chart_fact_mutation_allowed": False,
                },
                "cadence_rules": {
                    "default_cadence": "on_new_calibration_evidence_only",
                    "new_evidence_entrypoint": "P4 Focused Core Calibration Evidence Queue",
                    "queued_evidence_review": "P5 Core Calibration Queue Review",
                },
            },
            synced_documents=REQUIRED_SYNC_DOCUMENTS,
        )

    @app.get(f"{API_PREFIX}/admin/core/monitoring-steady-state")
    def get_core_monitoring_steady_state(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.core_monitoring_steady_state import (
            build_core_monitoring_steady_state,
            run_core_monitoring_steady_state,
        )

        if run_gate:
            return run_core_monitoring_steady_state(sample_limit=sample_limit)
        return build_core_monitoring_steady_state(
            core_monitoring_cadence_documentation_sync={
                "version": "v30.core_monitoring_cadence_documentation_sync.v1",
                "status": "completed",
                "decision": {
                    "decision_status": "core_monitoring_cadence_documentation_sync_ready",
                    "documentation_sync_ready": True,
                    "synced_document_count": 10,
                    "required_document_count": 10,
                    "current_cycle_closed": True,
                    "future_monitoring_ready": True,
                    "default_heavy_validation_allowed": False,
                    "full_pytest_required": False,
                    "full_518k_required": False,
                    "policy_pointer_promotion_allowed": False,
                    "pointer_write_performed": False,
                    "chart_fact_mutation_allowed": False,
                },
                "documentation_sync_summary": {"missing_documents": []},
                "documentation_policy": {
                    "default_cadence": "on_new_calibration_evidence_only",
                    "future_evidence_entrypoint": "P4 Focused Core Calibration Evidence Queue",
                    "future_review_entrypoint": "P5 Core Calibration Queue Review",
                },
            },
        )

    @app.get(f"{API_PREFIX}/admin/core/monitoring-s0-status")
    def get_core_monitoring_s0_status(
        run_gate: bool = False,
        sample_limit: int = 8,
    ) -> dict[str, object]:
        from v30.validation.core_monitoring_s0_status import (
            build_core_monitoring_s0_status,
            run_core_monitoring_s0_status,
        )

        if run_gate:
            return run_core_monitoring_s0_status(sample_limit=sample_limit)
        return build_core_monitoring_s0_status(
            core_monitoring_steady_state={
                "version": "v30.core_monitoring_steady_state.v1",
                "status": "completed",
                "decision": {
                    "decision_status": "core_monitoring_steady_state_ready",
                    "steady_state_ready": True,
                    "steady_state_check_count": 4,
                    "passed_steady_state_check_count": 4,
                    "waiting_for_new_evidence": True,
                    "future_monitoring_ready": True,
                    "focused_module_fix_required": False,
                    "full_pytest_required": False,
                    "full_518k_required": False,
                    "policy_pointer_promotion_allowed": False,
                    "pointer_write_performed": False,
                    "chart_fact_mutation_allowed": False,
                },
                "steady_state_policy": {
                    "new_evidence_entrypoint": "P4 Focused Core Calibration Evidence Queue",
                    "queued_evidence_review": "P5 Core Calibration Queue Review",
                },
            },
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
    return {
        "session_token": token,
        "username": str(user.get("username") or ""),
        "actor_id": str(user.get("actor_id") or ""),
        "session_id": f"session-{secrets.token_hex(6)}",
        "role": str(user.get("role") or "user"),
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
    return {
        "username": str(user.get("username") or ""),
        "actor_id": str(user.get("actor_id") or ""),
        "display_name": str(user.get("display_name") or user.get("username") or ""),
        "role": str(user.get("role") or "user"),
        "created_at": str(user.get("created_at") or ""),
    }


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


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
