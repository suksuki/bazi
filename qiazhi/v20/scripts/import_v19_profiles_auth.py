#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.access.auth import import_v19_auth_sessions, v19_auth_migration_preview  # noqa: E402
from v20.profiles.migration import import_v19_profiles_to_postgres, v19_profile_migration_preview  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Import V19 profiles and auth sessions into V20.")
    parser.add_argument("--apply", action="store_true", help="Actually write V20 auth store and Postgres profile table.")
    parser.add_argument("--profiles-only", action="store_true")
    parser.add_argument("--auth-only", action="store_true")
    parser.add_argument("--owner-id", default="admin", help="Target owner_id for imported V19 profiles.")
    parser.add_argument("--admin-password-env", default="V20_IMPORT_ADMIN_PASSWORD")
    args = parser.parse_args()

    include_profiles = not args.auth_only
    include_auth = not args.profiles_only
    payload = {
        "version": "v20.v19_profiles_auth_import_cli.v1",
        "apply": args.apply,
        "runtime_mutation": bool(args.apply),
        "profiles": None,
        "auth": None,
        "guardrails": [
            "EXPLICIT_APPLY_REQUIRED",
            "NO_PASSWORD_VALUES_RENDERED",
            "NO_SESSION_TOKENS_RENDERED",
            "V19_SOURCE_IS_READ_ONLY",
        ],
    }
    if include_profiles:
        payload["profiles_preview"] = v19_profile_migration_preview()
        payload["profiles"] = import_v19_profiles_to_postgres(apply=args.apply, owner_id=args.owner_id)
    if include_auth:
        payload["auth_preview"] = v19_auth_migration_preview()
        import os

        payload["auth"] = import_v19_auth_sessions(
            apply=args.apply,
            admin_password=os.getenv(args.admin_password_env, ""),
        )
    payload["status"] = _status(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["status"] in {"dry_run", "imported"} else 2


def _status(payload: dict[str, object]) -> str:
    results = [payload.get("profiles"), payload.get("auth")]
    statuses = [row.get("status") for row in results if isinstance(row, dict)]
    if not statuses:
        return "empty"
    if all(status == "dry_run" for status in statuses):
        return "dry_run"
    if all(status in {"imported", "dry_run"} for status in statuses):
        return "imported"
    return "blocked"


if __name__ == "__main__":
    raise SystemExit(main())
