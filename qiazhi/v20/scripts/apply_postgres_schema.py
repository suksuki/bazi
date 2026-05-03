#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.scripts.contract import run_and_print  # noqa: E402
from v20.storage.postgres_schema import migration_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run or apply V20 Postgres schema contract.")
    parser.add_argument(
        "--env-file",
        default="v20/.runtime/local/service.env",
        help="Load V20 env before applying. Existing real shell values win; placeholder templates are replaced.",
    )
    parser.add_argument("--apply", action="store_true", help="Actually execute schema SQL. Default is dry-run.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        _load_env_file(Path(args.env_file))
        return _apply_schema(apply=args.apply)

    return run_and_print(
        _run,
        command="apply_postgres_schema.py",
        args=args,
        runtime_mutation=args.apply,
    )


def _apply_schema(*, apply: bool) -> dict[str, object]:
    manifest = migration_manifest()
    migrations = [row for row in manifest.get("migrations", ()) if isinstance(row, dict)]
    statements = [
        str(statement)
        for migration in migrations
        for statement in migration.get("sql", ())
        if str(statement).strip()
    ]
    url = os.getenv("V20_DATABASE_URL", "")
    payload: dict[str, object] = {
        "version": "v20.postgres_schema_apply_cli.v1",
        "status": "dry_run",
        "apply": apply,
        "migration_count": len(migrations),
        "statement_count": len(statements),
        "database_url_present": bool(url),
        "runtime_mutation": apply,
        "guardrails": [
            "EXPLICIT_APPLY_REQUIRED",
            "BACKUP_REQUIRED_BEFORE_REMOTE_APPLY",
            "NO_SECRET_VALUES_RENDERED",
        ],
    }
    if not apply:
        return payload
    if not url:
        return payload | {"status": "blocked_missing_V20_DATABASE_URL"}
    try:
        import psycopg2
    except Exception as exc:
        return payload | {"status": "blocked_missing_psycopg2", "error": str(exc)}

    with psycopg2.connect(url) as conn:
        with conn.cursor() as cur:
            for statement in statements:
                cur.execute(statement)
        conn.commit()
    return payload | {"status": "applied", "applied_statement_count": len(statements)}


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
