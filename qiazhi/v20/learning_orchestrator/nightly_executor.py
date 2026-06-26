from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from v20.corpus.job_runner import FullPrecomputeJobConfig, read_full_precompute_status, run_full_precompute_job
from v20.learning_orchestrator.run_plan import build_learning_orchestrator_run_plan
from v20.storage.local_jsonl import local_jsonl_store_from_env


def default_nightly_executor_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"v20_nightly_learning_{stamp}"


def run_nightly_executor_skeleton(
    *,
    run_id: str = "",
    start: int = 0,
    limit: int = 8,
    status_every: int = 2,
    resume: bool = True,
    progress=None,
    runtime_dir: Path | None = None,
) -> dict[str, object]:
    safe_run_id = run_id or default_nightly_executor_run_id()
    run_plan = build_learning_orchestrator_run_plan("nightly")
    config = FullPrecomputeJobConfig(
        run_id=safe_run_id,
        start=max(0, start),
        limit=max(1, limit),
        status_every=max(1, status_every),
        resume=resume,
    )
    precompute = run_full_precompute_job(config, runtime_dir=runtime_dir, progress=progress)
    status = _executor_status_payload(safe_run_id, run_plan, precompute, runtime_dir=runtime_dir)
    _write_executor_status(status, runtime_dir=runtime_dir)
    return status


def read_nightly_executor_status(run_id: str = "", *, runtime_dir: Path | None = None) -> dict[str, object]:
    root = _executor_root(runtime_dir)
    path = root / run_id / "status.json" if run_id else root / "latest_status.json"
    if path.exists():
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["runtime_mutation"] = False
        payload["guardrails"] = list(payload.get("guardrails", ())) + ["STATUS_READ_ONLY"]
        return payload
    return {
        "version": "v20.nightly_learning_executor_status.v1",
        "status": "not_started",
        "runtime_mutation": False,
        "guardrails": ["STATUS_READ_ONLY", "NO_FULL_518K_STARTED_BY_STATUS"],
    }


def _executor_status_payload(
    run_id: str,
    run_plan: dict[str, object],
    precompute: dict[str, object],
    *,
    runtime_dir: Path | None,
) -> dict[str, object]:
    target_count = int(precompute.get("target_count", 0) or 0)
    completed = int(precompute.get("completed_from_start", 0) or 0)
    return {
        "version": "v20.nightly_learning_executor_status.v1",
        "status": "completed" if precompute.get("status") == "completed" else str(precompute.get("status", "running")),
        "run_id": run_id,
        "job_key": "nightly",
        "executor_mode": "skeleton_limited_shard",
        "target_case_count": int(run_plan.get("job", {}).get("target_case_count", 518_400)) if isinstance(run_plan.get("job"), dict) else 518_400,
        "executed_case_count": target_count,
        "completed_case_count": completed,
        "progress_percent": round((completed / target_count) * 100, 3) if target_count else 0,
        "precompute_status": precompute,
        "candidate_policy_targets": run_plan.get("candidate_policy_targets", ()),
        "next_executor_step": "expand_shard_limit_then_add_evaluator_merge",
        "runtime_mutation": True,
        "guardrails": [
            "NIGHTLY_EXECUTOR_SKELETON_ONLY",
            "LIMITED_SHARD_RUN_NOT_FULL_518K",
            "NO_LLM_CALL",
            "NO_RUNTIME_POINTER_MUTATION",
            "CHECKPOINT_STATUS_WRITTEN",
        ],
    }


def _write_executor_status(status: dict[str, object], *, runtime_dir: Path | None) -> None:
    import json

    root = _executor_root(runtime_dir)
    run_dir = root / str(status.get("run_id", "nightly"))
    run_dir.mkdir(parents=True, exist_ok=True)
    text = json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True)
    (run_dir / "status.json").write_text(text, encoding="utf-8")
    (root / "latest_status.json").write_text(text, encoding="utf-8")


def _executor_root(runtime_dir: Path | None) -> Path:
    base = runtime_dir or local_jsonl_store_from_env().runtime_dir
    return base / "training" / "nightly_executor"
