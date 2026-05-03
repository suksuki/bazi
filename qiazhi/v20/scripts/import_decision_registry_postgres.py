#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.storage.postgres_decision_import import build_decision_registry_postgres_import_plan  # noqa: E402
from v20.scripts.contract import run_and_print


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run or apply V20 DecisionRegistry review records into Postgres."
    )
    parser.add_argument(
        "--env-file",
        default="v20/.runtime/local/service.env",
        help="Load V20 local env before importing. Existing real shell values win; placeholder templates are replaced.",
    )
    parser.add_argument("--apply", action="store_true", help="Actually write Postgres. Default is dry-run only.")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        _load_env_file(Path(args.env_file))
        return build_decision_registry_postgres_import_plan(apply=args.apply, batch_size=max(1, args.batch_size))

    return run_and_print(
        _run,
        command="import_decision_registry_postgres.py",
        args=args,
        runtime_mutation=args.apply,
    )


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    replace_placeholder = _is_placeholder(os.getenv("V20_DATABASE_URL", ""))
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if not key:
            continue
        if key == "V20_DATABASE_URL" and replace_placeholder:
            os.environ[key] = value
        else:
            os.environ.setdefault(key, value)


def _is_placeholder(value: str) -> bool:
    return any(token in value for token in ("USER", "PASSWORD", "HOST", "PORT", "DBNAME", "CHANGE_ME"))


if __name__ == "__main__":
    raise SystemExit(main())
