from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from v20.scripts.contract import exit_code as contract_exit_code
from v20.testing.schema import TestCommand, TestTier
from v20.testing.tiers import TEST_TIERS, get_tier, test_tier_manifest


def run_tier(
    name: str,
    extra_args: tuple[str, ...] = (),
    *,
    dry_run: bool = False,
    command_timeout_seconds: float | None = None,
    emit_command_output: bool = True,
) -> dict[str, object]:
    root = Path(__file__).resolve().parents[2]
    tier = get_tier(name)
    start = time.monotonic()
    rows: list[dict[str, object]] = []
    for command in tier.commands:
        if command.opt_in_env and os.getenv(command.opt_in_env) not in {"1", "true", "TRUE", "yes", "on"}:
            rows.append(_skipped(command))
            continue
        argv = _expand_argv(command.argv, root, extra_args)
        command_timeout = (
            command.command_timeout_seconds
            if command_timeout_seconds is None
            else (
                command.command_timeout_seconds
                if command.command_timeout_seconds is not None and command.command_timeout_seconds < command_timeout_seconds
                else command_timeout_seconds
            )
        )
        if dry_run:
            rows.append(
                {
                    "name": command.name,
                    "status": "dry_run",
                    "argv": argv,
                    "purpose": command.purpose,
                    "command_timeout_seconds": command.command_timeout_seconds,
                    "timeout_seconds": command.command_timeout_seconds if command_timeout_seconds is None else command_timeout,
                }
            )
            continue
        row = _run_command(
            command.name,
            argv,
            root,
            timeout_seconds=command_timeout,
            emit_command_output=emit_command_output,
        )
        row["command_timeout_seconds"] = command.command_timeout_seconds
        row["timeout_seconds"] = command_timeout
        row["argv"] = argv
        rows.append(row)
        if row["status"] != "pass" and row["status"] != "needs_review" and row["status"] != "not_built":
            return _result(tier, rows, time.monotonic() - start, ok=False)
    return _result(tier, rows, time.monotonic() - start, ok=True)


def main(argv: list[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    dry_run = _pop_flag(raw_args, "--dry-run")
    command_timeout = _pop_float_flag(raw_args, "--command-timeout")
    json_output = _pop_flag(raw_args, "--json")
    parser = argparse.ArgumentParser(description="Run V20 bounded test tiers.")
    parser.add_argument("tier", choices=[tier.name for tier in TEST_TIERS] + ["list"])
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(raw_args)
    if args.tier == "list":
        manifest = test_tier_manifest()
        if json_output:
            print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            _print_manifest(manifest)
        return 0
    result = run_tier(
        args.tier,
        tuple(args.pytest_args),
        dry_run=dry_run,
        command_timeout_seconds=command_timeout,
        emit_command_output=not json_output,
    )
    if json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_result(result)
    return 0 if result["ok"] else 1


def _expand_argv(argv: tuple[str, ...], root: Path, extra_args: tuple[str, ...]) -> list[str]:
    expanded: list[str] = []
    for item in argv:
        if item == "__V20_PY_FILES__":
            expanded.extend(_v20_py_files(root))
        elif item == "__PYTEST_ARGS__":
            expanded.extend(_normalize_pytest_args(extra_args))
        elif item == "__PYTHON_BIN__":
            expanded.append(_python_bin())
        else:
            expanded.append(item)
    return expanded


def _python_bin() -> str:
    if os.getenv("PYTHON_BIN"):
        return str(os.environ["PYTHON_BIN"])
    root = Path(__file__).resolve().parents[2]
    venv_python = root / ".venv312" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return shutil.which("python3.12") or sys.executable or "python3.12"


def _v20_py_files(root: Path) -> list[str]:
    return [
        str(path.relative_to(root))
        for path in sorted((root / "v20").rglob("*.py"))
        if "__pycache__" not in path.parts
    ]


def _normalize_pytest_args(extra_args: tuple[str, ...]) -> list[str]:
    if not extra_args:
        return []
    if len(extra_args) == 1 and extra_args[0].strip() and not extra_args[0].startswith("-"):
        return ["-k", extra_args[0]]
    return list(extra_args)


def _run_command(
    name: str,
    argv: list[str],
    root: Path,
    *,
    timeout_seconds: float | None,
    emit_command_output: bool,
) -> dict[str, object]:
    start = time.monotonic()
    try:
        completed = subprocess.run(
            argv,
            cwd=root,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:  # pragma: no cover - exercised via targeted unit test
        return {
            "name": name,
            "status": "timeout",
            "returncode": 1,
            "duration_seconds": round(time.monotonic() - start, 3),
            "stderr": f"command timed out after {float(exc.timeout or 0):.3f}s",
            "timeout_seconds": timeout_seconds,
            "contract_payload": None,
        }

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    if emit_command_output and stdout:
        print(stdout, end="", flush=True)
    if emit_command_output and stderr:
        print(stderr, end="", flush=True)

    status = "pass" if completed.returncode == 0 else "fail"
    contract_payload = _extract_contract_payload(stdout) or _extract_contract_payload(stderr)
    if contract_payload is not None:
        status = _normalize_status(_status_from_contract_payload(contract_payload), completed.returncode)
        if status == "unknown":
            status = "pass" if contract_exit_code(contract_payload) == 0 else "fail"

    return {
        "name": name,
        "status": status,
        "returncode": completed.returncode,
        "duration_seconds": round(time.monotonic() - start, 3),
        "stdout": _truncate_output(stdout),
        "stderr": _truncate_output(stderr),
        "contract_payload": contract_payload,
        "contract_status": str(contract_payload.get("status", "")) if isinstance(contract_payload, dict) else "",
    }


def _status_from_contract_payload(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    status = str(payload.get("status", "")).strip().lower()
    if status:
        return status
    if payload.get("ok") is False:
        return "fail"
    if payload.get("ok") is True:
        return "pass"
    return ""


def _extract_contract_payload(output: str) -> dict[str, Any] | None:
    return _extract_contract_payload_from_text(output)


def _extract_contract_payload_from_text(output: str) -> dict[str, Any] | None:
    if not output:
        return None

    lines = [line for line in output.splitlines() if line.strip()]
    if not lines:
        return None

    for start in range(len(lines) - 1, -1, -1):
        candidate = "\n".join(lines[start:]).strip()
        parsed = _decode_json_block(candidate)
        if parsed is not None:
            return parsed

    stripped = output.strip()
    for start in range(len(stripped) - 1, -1, -1):
        if stripped[start] != "{":
            continue
        parsed = _decode_json_block(stripped[start:])
        if parsed is not None:
            return parsed
    return None


def _decode_json_block(candidate: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return parsed
        return None
    except Exception:
        try:
            parsed, end = json.JSONDecoder().raw_decode(candidate)
        except Exception:
            return None
        if not isinstance(parsed, dict):
            return None
        if candidate[end:].strip():
            return None
        return parsed


def _truncate_output(value: str, max_chars: int = 4096) -> str:
    if len(value) <= max_chars:
        return value
    suffix = max(0, len(value) - max_chars + 24)
    return f"{value[: max_chars - 24]}...({suffix} chars truncated)"


def _normalize_status(status: str, return_code: int) -> str:
    status = status.strip().lower()
    if status in {
        "pass",
        "ready",
        "ready_for_dry_run",
        "ready_for_explicit_import",
        "ready_for_conversion",
        "ready_for_import",
        "ready_to_import",
        "ready_for_build",
        "ready_for_manual_sync",
        "ready_for_import",
        "active",
        "dry_run",
        "ok",
        "empty",
        "not_built",
        "written",
        "imported",
        "active_ready",
        "completed",
        "completed_without_mutation",
        "persisted",
        "exported",
        "needs_review",
        "needs_feature_support",
        "not_enough_data",
        "case_not_found",
    }:
        return "pass"
    if status in {
        "fail",
        "blocked",
        "error",
        "error_empty",
        "error_invalid",
        "needs_maintenance",
    } or status.startswith("blocked_"):
        return "fail"
    return "pass" if return_code == 0 else "fail"


def _pop_float_flag(argv: list[str], flag: str) -> float | None:
    value: float | None = None
    while flag in argv:
        index = argv.index(flag)
        if index + 1 >= len(argv):
            raise SystemExit(f"missing value for {flag}")
        try:
            value = float(argv.pop(index + 1))
        except ValueError as exc:
            raise SystemExit(f"invalid float for {flag}: {argv[index]}") from exc
        argv.pop(index)
    return value


def _skipped(command: TestCommand) -> dict[str, object]:
    return {
        "name": command.name,
        "status": "skipped",
        "reason": f"set {command.opt_in_env}=1 to run",
        "purpose": command.purpose,
    }


def _result(tier: TestTier, rows: list[dict[str, object]], duration: float, *, ok: bool) -> dict[str, object]:
    return {
        "version": "v20.test_run_result.v1",
        "tier": tier.name,
        "ok": ok,
        "duration_seconds": round(duration, 3),
        "budget_seconds": tier.budget_seconds,
        "budget_ok": duration <= tier.budget_seconds,
        "commands": rows,
        "guardrails": list(tier.guardrails),
    }


def _pop_flag(argv: list[str], flag: str) -> bool:
    found = False
    while flag in argv:
        argv.remove(flag)
        found = True
    return found


def _print_manifest(manifest: dict[str, object] | None = None) -> None:
    manifest = manifest or test_tier_manifest()
    print("V20 test tiers:")
    for tier in manifest["tiers"]:
        print(f"- {tier['name']}: budget={tier['budget_seconds']}s purpose={tier['purpose']}")


def _print_result(result: dict[str, object]) -> None:
    print(f"V20 test tier {result['tier']}: ok={result['ok']} duration={result['duration_seconds']}s budget={result['budget_seconds']}s")
    for row in result["commands"]:
        print(f"- {row['name']}: {row['status']}")


if __name__ == "__main__":
    sys.exit(main())
