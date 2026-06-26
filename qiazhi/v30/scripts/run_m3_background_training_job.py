from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


M3_BACKGROUND_STEP_TIMEOUTS = {
    "m3_snapshot": 180,
    "m3_synthetic": 300,
    "training_pipeline": 900,
    "518k_sample": 900,
    "518k_shard": 1200,
    "518k_readiness_matrix": 1200,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_job(path: Path, job: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")


def _run_command(args: list[str], *, timeout_sec: int) -> dict[str, object]:
    try:
        completed = subprocess.run(
            args,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"Command '{' '.join(args)}' timed out after {timeout_sec} seconds") from exc
    result = {
        "step": "",
        "command": " ".join(args),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip()[-1200:],
        "stderr": completed.stderr.strip()[-1200:],
        "timeout_sec": timeout_sec,
    }
    if completed.returncode != 0:
        raise RuntimeError(
            f"{result['command']} failed with code {completed.returncode}: "
            f"{(completed.stderr or completed.stdout).strip()[-500:]}"
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V30 M3 training/validation background job.")
    parser.add_argument("--job-file", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--persist-m3-to-db", action="store_true")
    parser.add_argument("--include-shard", action="store_true")
    parser.add_argument("--shard-id", type=int, default=7)
    parser.add_argument("--shard-limit", type=int, default=16)
    parser.add_argument("--include-readiness-matrix", action="store_true")
    args = parser.parse_args()

    job_path = Path(args.job_file)
    steps: list[tuple[str, list[str], int]] = []
    m3_snapshot = ["python3", "scripts/run_m3_core_spine_snapshot.py", "--sample-limit", str(args.sample_limit)]
    if not args.persist_m3_to_db:
        m3_snapshot.append("--no-db")
    steps.extend(
        [
            ("m3_snapshot", m3_snapshot, M3_BACKGROUND_STEP_TIMEOUTS["m3_snapshot"]),
            (
                "m3_synthetic",
                ["python3", "scripts/run_synthetic_validation.py", "--tier", "m3_core_spine"],
                M3_BACKGROUND_STEP_TIMEOUTS["m3_synthetic"],
            ),
            (
                "training_pipeline",
                ["python3", "scripts/run_synthetic_validation.py", "--tier", "training_pipeline"],
                M3_BACKGROUND_STEP_TIMEOUTS["training_pipeline"],
            ),
            (
                "518k_sample",
                ["python3", "scripts/run_518k_validation.py", "--mode", "sample", "--limit", str(args.sample_limit)],
                M3_BACKGROUND_STEP_TIMEOUTS["518k_sample"],
            ),
        ]
    )
    if args.include_shard:
        steps.append(
            (
                "518k_shard",
                [
                    "python3",
                    "scripts/run_518k_validation.py",
                    "--mode",
                    "shard",
                    "--shard-id",
                    str(args.shard_id),
                    "--limit",
                    str(args.shard_limit),
                ],
                M3_BACKGROUND_STEP_TIMEOUTS["518k_shard"],
            )
        )
    if args.include_readiness_matrix:
        steps.append(
            (
                "518k_readiness_matrix",
                [
                    "python3",
                    "scripts/run_518k_readiness_matrix.py",
                    "--sample-limit",
                    str(args.sample_limit),
                    "--shard-id",
                    str(args.shard_id),
                    "--shard-limit",
                    str(args.shard_limit),
                ],
                M3_BACKGROUND_STEP_TIMEOUTS["518k_readiness_matrix"],
            )
        )

    existing: dict[str, object] = {}
    if job_path.exists():
        try:
            loaded = json.loads(job_path.read_text(encoding="utf-8"))
            existing = loaded if isinstance(loaded, dict) else {}
        except (OSError, json.JSONDecodeError):
            existing = {}
    existing_config = existing.get("config", {}) if isinstance(existing.get("config"), dict) else {}
    persist_requested = bool(existing_config.get("persist_m3_to_db") or args.persist_m3_to_db)
    job = {
        "version": "v30.admin.m3_background_training_job.v1",
        "job_id": args.job_id,
        "status": "running",
        "created_at": str(existing.get("created_at") or ""),
        "started_at": _utc_now(),
        "finished_at": "",
        "current_step": "running",
        "completed_steps": 0,
        "total_steps": len(steps),
        "progress_percent": 1,
        "steps": [step[0] for step in steps],
        "results": [],
        "worker_pid": existing.get("worker_pid"),
        "log_path": existing.get("log_path"),
        "config": {
            "sample_limit": args.sample_limit,
            "persist_m3_to_db": persist_requested,
            "persist_m3_to_db_executed": args.persist_m3_to_db,
            "include_shard": args.include_shard,
            "shard_id": args.shard_id,
            "shard_limit": args.shard_limit,
            "include_readiness_matrix": args.include_readiness_matrix,
            "full_518k": "not_supported_by_background_default",
            "step_timeouts_sec": {
                step_name: timeout_sec
                for step_name, _command, timeout_sec in steps
            },
        },
        "boundary": "runs_m3_training_validation_and_518k_sample_without_pointer_promotion_or_chart_fact_mutation",
    }
    _write_job(job_path, job)

    for index, (step_name, command, timeout_sec) in enumerate(steps):
        job["current_step"] = step_name
        job["step_started_at"] = _utc_now()
        job["progress_percent"] = max(3, int((index / len(steps)) * 100))
        _write_job(job_path, job)
        try:
            result = _run_command(command, timeout_sec=timeout_sec)
            result["step"] = step_name
        except TimeoutError as exc:
            if step_name != "m3_snapshot" or "--no-db" in command:
                job["status"] = "failed"
                job["error"] = str(exc)
                job["failed_step"] = step_name
                job["finished_at"] = _utc_now()
                _write_job(job_path, job)
                return 1
            fallback = [*command, "--no-db"]
            try:
                result = _run_command(fallback, timeout_sec=M3_BACKGROUND_STEP_TIMEOUTS["m3_snapshot"])
                result["step"] = step_name
                result["recovered_from_timeout"] = True
                result["recovery_reason"] = "db_persistence_timeout_no_db_artifact_fallback"
                result["primary_error"] = str(exc)
            except Exception as fallback_exc:
                job["status"] = "failed"
                job["error"] = str(fallback_exc)
                job["failed_step"] = step_name
                job["finished_at"] = _utc_now()
                _write_job(job_path, job)
                return 1
        except Exception as exc:
            job["status"] = "failed"
            job["error"] = str(exc)
            job["failed_step"] = step_name
            job["finished_at"] = _utc_now()
            _write_job(job_path, job)
            return 1
        results = list(job.get("results") or [])
        results.append(result)
        job["results"] = results
        job["completed_steps"] = index + 1
        job["progress_percent"] = int(((index + 1) / len(steps)) * 100)
        _write_job(job_path, job)

    job["status"] = "completed"
    job["current_step"] = "completed"
    job["finished_at"] = _utc_now()
    job["progress_percent"] = 100
    _write_job(job_path, job)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
