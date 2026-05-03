from __future__ import annotations

import argparse
import hashlib
import json
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from v20.storage.local_jsonl import local_jsonl_store_from_env


CONTRACT_VERSION = "v20.script_contract.v1"


PASS_STATUSES = {
    "pass",
    "ready",
    "ready_for_dry_run",
    "ready_for_explicit_import",
    "ready_for_conversion",
    "ready_for_import",
    "ready_to_import",
    "ready_for_build",
    "ready_for_manual_sync",
    "written",
    "imported",
    "active_ready",
    "active",
    "dry_run",
    "ok",
    "empty",
    "not_built",
    "completed",
    "completed_without_mutation",
    "persisted",
    "exported",
    "needs_review",
    "needs_feature_support",
    "not_enough_data",
    "case_not_found",
}

FAIL_STATUSES = {
    "fail",
    "blocked",
    "error",
    "error_empty",
    "error_invalid",
    "needs_maintenance",
    "needs_work",
    "source_missing",
    "not_ready",
    "missing",
    "driver_missing",
    "connection_failed",
    "model_probe_failed",
    "blocked_missing_psycopg2",
    "blocked_missing_V20_DATABASE_URL",
    "blocked_postgres_error",
    "blocked_missing_flat_labels",
    "blocked_missing_pyarrow",
    "blocked_corrupt_dependency",
    "blocked_dependency_missing",
    "blocked_static_contract",
}


@dataclass(frozen=True)
class ContractResult:
    payload: dict[str, Any]
    exit_code: int


def build_payload(
    payload: dict[str, object],
    *,
    command: str,
    args: argparse.Namespace | None = None,
    runtime_mutation: bool | None = None,
    stage_trace: Iterable[str] | None = None,
    started_at: float | None = None,
) -> dict[str, object]:
    """Attach a shared contract envelope to any script output payload."""
    base = dict(payload)
    args_dict = _serialize_args(args)
    elapsed_ms = _elapsed_ms(started_at)

    status = str(base.get("status", "")).strip().lower()
    if not status:
        status = "pass" if base.get("ok", True) is True else "fail"
    base["status"] = _canonical_status(status)

    base.setdefault("version", "v20.script_payload.v1")
    base.setdefault("contract_version", CONTRACT_VERSION)
    base["runtime_mutation"] = _as_bool(runtime_mutation, base.get("runtime_mutation"))
    base["contract_command"] = f"v20/scripts/{command}"
    base["script_path"] = base.get("script_path") or f"v20/scripts/{command}"
    base["contract_run_at"] = datetime.now(timezone.utc).isoformat()
    base["contract_args"] = args_dict
    base["contract_args_hash"] = _stable_hash(args_dict)
    base["local_runtime_dir"] = str(local_jsonl_store_from_env().runtime_dir)
    base["contract_host_file"] = str(Path(__file__).resolve())
    base["elapsed_ms"] = elapsed_ms
    if stage_trace is not None:
        base["stage_trace"] = list(stage_trace)
    base.setdefault("guardrails", tuple())
    if not isinstance(base["guardrails"], list):
        base["guardrails"] = list(base["guardrails"])

    failures = base.setdefault("failures", [])
    if not isinstance(failures, list):
        base["failures"] = list(failures) if isinstance(failures, tuple) else [str(failures)] if failures else []
    quality_findings = base.setdefault("quality_findings", [])
    if not isinstance(quality_findings, list):
        base["quality_findings"] = (
            list(quality_findings)
            if isinstance(quality_findings, tuple)
            else [str(quality_findings)]
            if quality_findings
            else []
        )
    return base


def exit_code(payload: dict[str, object]) -> int:
    status = str(payload.get("status", "")).strip().lower()
    status = _canonical_status(status)
    if status in PASS_STATUSES:
        return 0
    if status in FAIL_STATUSES or status.startswith("blocked_"):
        return 1
    for nested_key in ("manifest_status", "package_status", "report_status", "pipeline_status"):
        nested = str(payload.get(nested_key, "")).strip().lower()
        if nested in {"blocked", "fail", "error"} or nested.startswith("blocked_"):
            return 1
    if payload.get("ok") is False:
        return 1
    # Unknown states are intentionally non-failing by default to avoid hard-coding future states.
    # If we need stricter behavior, scripts can set an explicit fail/pass status.
    return 0


def run_and_print(
    main_logic: Callable[[], dict[str, object]],
    *,
    command: str,
    args: argparse.Namespace | None = None,
    runtime_mutation: bool | None = None,
    stage_trace: Iterable[str] | None = None,
) -> int:
    started_at = time.monotonic()
    try:
        payload = main_logic()
    except Exception as exc:
        payload = {
            "version": "v20.script_payload.v1",
            "status": "error",
            "ok": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "runtime_mutation": bool(runtime_mutation),
        }
    payload = build_payload(
        payload,
        command=command,
        args=args,
        runtime_mutation=runtime_mutation,
        stage_trace=stage_trace,
        started_at=started_at,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code(payload)


def _canonical_status(value: str) -> str:
    return value.strip().lower()


def _as_bool(primary: bool | None, fallback: object) -> bool:
    if primary is not None:
        return bool(primary)
    if isinstance(fallback, bool):
        return fallback
    return False


def _stable_hash(payload: object) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=_json_default)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _serialize_args(args: argparse.Namespace | None) -> dict[str, object]:
    if args is None:
        return {}
    result: dict[str, object] = {}
    for key, value in sorted(vars(args).items()):
        result[key.replace("-", "_")] = _serialize_value(key, value)
    return result


def _serialize_value(name: str, value: object) -> object:
    if name.lower() in {"password", "admin_password", "token", "secret", "api_key"}:
        return "REDACTED"
    if isinstance(value, (tuple, list)):
        return [_serialize_value(name, row) for row in value]
    if isinstance(value, set):
        return sorted(str(item) for item in value)
    if isinstance(value, Path):
        return str(value)
    return value


def _elapsed_ms(started_at: float | None) -> int:
    if started_at is None:
        return 0
    return int(round((time.monotonic() - started_at) * 1000))


def _json_default(value: object) -> str:
    if isinstance(value, (set, tuple)):
        return json.dumps(sorted(value), ensure_ascii=False, sort_keys=True)
    if isinstance(value, Path):
        return str(value)
    return str(value)
