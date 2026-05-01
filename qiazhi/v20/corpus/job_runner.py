from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v20.corpus.enumerator import FULL_CORPUS_CASE_COUNT, canonical_case_at
from v20.corpus.precompute_runner import precompute_case
from v20.storage.local_jsonl import local_jsonl_store_from_env


@dataclass(frozen=True)
class FullPrecomputeJobConfig:
    run_id: str
    start: int = 0
    limit: int = FULL_CORPUS_CASE_COUNT
    status_every: int = 500
    resume: bool = True

    @property
    def end(self) -> int:
        return min(FULL_CORPUS_CASE_COUNT, self.start + self.limit)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"end": self.end}


def default_full_precompute_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"v20_full_518k_{stamp}"


def full_precompute_root(runtime_dir: Path | None = None) -> Path:
    base = runtime_dir or local_jsonl_store_from_env().runtime_dir
    return base / "corpus" / "full_precompute"


def run_full_precompute_job(
    config: FullPrecomputeJobConfig,
    *,
    runtime_dir: Path | None = None,
) -> dict[str, object]:
    if config.start < 0 or config.start >= FULL_CORPUS_CASE_COUNT:
        raise ValueError(f"start out of range: {config.start}")
    if config.limit <= 0:
        raise ValueError("limit must be positive")
    if config.status_every <= 0:
        raise ValueError("status_every must be positive")

    root = full_precompute_root(runtime_dir)
    run_dir = root / config.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = run_dir / "snapshots.jsonl"
    error_path = run_dir / "errors.jsonl"
    progress_path = run_dir / "progress.json"
    latest_path = root / "latest_status.json"

    start_index = _resume_index(config, progress_path)
    started_at = datetime.now(timezone.utc).isoformat()
    started_monotonic = time.monotonic()
    processed = 0
    failed = 0
    status = _status_payload(
        config=config,
        run_dir=run_dir,
        next_index=start_index,
        processed=processed,
        failed=failed,
        started_at=started_at,
        elapsed_seconds=0.0,
        status="running",
    )
    _write_json(progress_path, status)
    _write_json(latest_path, status)

    with snapshot_path.open("a", encoding="utf-8") as snapshots, error_path.open("a", encoding="utf-8") as errors:
        for index in range(start_index, config.end):
            try:
                snapshot = precompute_case(canonical_case_at(index))
                snapshots.write(json.dumps(snapshot, ensure_ascii=False, sort_keys=True) + "\n")
                processed += 1
            except Exception as exc:  # pragma: no cover - defensive long-job resilience
                failed += 1
                error = {
                    "version": "v20.full_precompute_error.v1",
                    "run_id": config.run_id,
                    "index": index,
                    "error": str(exc),
                    "runtime_mutation": True,
                }
                errors.write(json.dumps(error, ensure_ascii=False, sort_keys=True) + "\n")
            if processed % config.status_every == 0 or index + 1 >= config.end:
                snapshots.flush()
                errors.flush()
                elapsed = time.monotonic() - started_monotonic
                status = _status_payload(
                    config=config,
                    run_dir=run_dir,
                    next_index=index + 1,
                    processed=processed,
                    failed=failed,
                    started_at=started_at,
                    elapsed_seconds=elapsed,
                    status="completed" if index + 1 >= config.end else "running",
                )
                _write_json(progress_path, status)
                _write_json(latest_path, status)
    return status


def read_full_precompute_status(
    run_id: str = "",
    *,
    runtime_dir: Path | None = None,
) -> dict[str, object]:
    root = full_precompute_root(runtime_dir)
    path = root / run_id / "progress.json" if run_id else root / "latest_status.json"
    if not path.exists():
        return {
            "version": "v20.full_precompute_job_status.v1",
            "status": "not_started",
            "runtime_mutation": False,
            "guardrails": ["STATUS_READ_ONLY", "NO_CORPUS_CONTENT_RENDERED"],
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["job_runtime_mutation"] = payload.get("runtime_mutation", False)
    payload["runtime_mutation"] = False
    payload["guardrails"] = list(payload.get("guardrails", ())) + [
        "STATUS_READ_ONLY",
        "NO_CORPUS_CONTENT_RENDERED",
    ]
    return payload


def _resume_index(config: FullPrecomputeJobConfig, progress_path: Path) -> int:
    if not config.resume or not progress_path.exists():
        return config.start
    try:
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        next_index = int(progress.get("next_index", config.start))
        return max(config.start, min(next_index, config.end))
    except Exception:
        return config.start


def _status_payload(
    *,
    config: FullPrecomputeJobConfig,
    run_dir: Path,
    next_index: int,
    processed: int,
    failed: int,
    started_at: str,
    elapsed_seconds: float,
    status: str,
) -> dict[str, object]:
    target_count = config.end - config.start
    total_completed = max(0, next_index - config.start)
    rate = processed / elapsed_seconds if elapsed_seconds > 0 else 0.0
    remaining = max(0, config.end - next_index)
    eta_seconds = remaining / rate if rate > 0 else None
    return {
        "version": "v20.full_precompute_job_status.v1",
        "run_id": config.run_id,
        "status": status,
        "config": config.to_dict(),
        "target_count": target_count,
        "next_index": next_index,
        "processed_this_session": processed,
        "completed_from_start": total_completed,
        "failed_this_session": failed,
        "progress_ratio": round(total_completed / target_count, 6) if target_count else 1.0,
        "cases_per_second": round(rate, 3),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "eta_seconds": round(eta_seconds, 3) if eta_seconds is not None else None,
        "started_at": started_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "snapshots_path": str(run_dir / "snapshots.jsonl"),
        "errors_path": str(run_dir / "errors.jsonl"),
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_CORPUS_PRECOMPUTE_JOB",
            "NO_POSTGRES_WRITE_BY_DEFAULT",
            "NO_DESTINY_TRUTH_LABEL",
            "NO_RULE_ACTIVATION",
        ],
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
