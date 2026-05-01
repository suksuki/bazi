#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.storage.postgres_ledger_import import ALLOWED_LEDGER_NAMES, build_ledger_postgres_import_plan  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run or apply local V20 feedback/calibration ledger import into Postgres."
    )
    parser.add_argument("--ledger", choices=ALLOWED_LEDGER_NAMES, default="practitioner_calibration_ledger")
    parser.add_argument("--apply", action="store_true", help="Actually write Postgres. Default is dry-run only.")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    payload = build_ledger_postgres_import_plan(
        ledger_name=args.ledger,
        apply=args.apply,
        batch_size=args.batch_size,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload.get("status") not in {"blocked_missing_V20_DATABASE_URL", "blocked_missing_psycopg2", "blocked_postgres_error"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
