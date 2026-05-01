from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from v20.testing.schema import TestCommand, TestTier
from v20.testing.tiers import TEST_TIERS, get_tier, test_tier_manifest


def run_tier(name: str, extra_args: tuple[str, ...] = (), *, dry_run: bool = False) -> dict[str, object]:
    root = Path(__file__).resolve().parents[2]
    tier = get_tier(name)
    start = time.monotonic()
    rows: list[dict[str, object]] = []
    for command in tier.commands:
        if command.opt_in_env and os.getenv(command.opt_in_env) not in {"1", "true", "TRUE", "yes", "on"}:
            rows.append(_skipped(command))
            continue
        argv = _expand_argv(command.argv, root, extra_args)
        if dry_run:
            rows.append({"name": command.name, "status": "dry_run", "argv": argv, "purpose": command.purpose})
            continue
        cmd_start = time.monotonic()
        completed = subprocess.run(argv, cwd=root)
        rows.append(
            {
                "name": command.name,
                "status": "pass" if completed.returncode == 0 else "fail",
                "returncode": completed.returncode,
                "duration_seconds": round(time.monotonic() - cmd_start, 3),
                "argv": argv,
            }
        )
        if completed.returncode != 0:
            return _result(tier, rows, time.monotonic() - start, ok=False)
    return _result(tier, rows, time.monotonic() - start, ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run V20 bounded test tiers.")
    parser.add_argument("tier", choices=[tier.name for tier in TEST_TIERS] + ["list"])
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.tier == "list":
        _print_manifest()
        return 0
    result = run_tier(args.tier, tuple(args.pytest_args), dry_run=args.dry_run)
    _print_result(result)
    return 0 if result["ok"] else 1


def _expand_argv(argv: tuple[str, ...], root: Path, extra_args: tuple[str, ...]) -> list[str]:
    expanded: list[str] = []
    for item in argv:
        if item == "__V20_PY_FILES__":
            expanded.extend(_v20_py_files(root))
        elif item == "__PYTEST_ARGS__":
            expanded.extend(_normalize_pytest_args(extra_args))
        else:
            expanded.append(item)
    return expanded


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


def _print_manifest() -> None:
    manifest = test_tier_manifest()
    print("V20 test tiers:")
    for tier in manifest["tiers"]:
        print(f"- {tier['name']}: budget={tier['budget_seconds']}s purpose={tier['purpose']}")


def _print_result(result: dict[str, object]) -> None:
    print(f"V20 test tier {result['tier']}: ok={result['ok']} duration={result['duration_seconds']}s budget={result['budget_seconds']}s")
    for row in result["commands"]:
        print(f"- {row['name']}: {row['status']}")


if __name__ == "__main__":
    sys.exit(main())
