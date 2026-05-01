#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.corpus.artifacts import DEFAULT_ARTIFACT_RUN_ID, corpus_artifact_paths  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Import V20 flat corpus labels into Postgres.")
    parser.add_argument("--run-id", default=DEFAULT_ARTIFACT_RUN_ID)
    parser.add_argument("--apply", action="store_true", help="Actually write Postgres. Default is dry-run only.")
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()

    paths = corpus_artifact_paths(args.run_id)
    url = os.getenv("V20_DATABASE_URL", "")
    payload = {
        "version": "v20.corpus_postgres_import_cli.v1",
        "run_id": args.run_id,
        "source": str(paths.flat_labels_path),
        "target_table": "v20_corpus_snapshots",
        "apply": args.apply,
        "database_url_present": bool(url),
        "runtime_mutation": bool(args.apply),
        "guardrails": [
            "EXPLICIT_APPLY_REQUIRED",
            "BACKUP_REQUIRED_BEFORE_REMOTE_IMPORT",
            "NO_SECRET_VALUES_RENDERED",
        ],
    }
    if not args.apply:
        payload["status"] = "dry_run"
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if not url:
        payload["status"] = "blocked_missing_V20_DATABASE_URL"
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    if not paths.flat_labels_path.exists():
        payload["status"] = "blocked_missing_flat_labels"
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    try:
        import psycopg2
        from psycopg2.extras import execute_values
    except Exception as exc:
        payload["status"] = "blocked_missing_psycopg2"
        payload["error"] = str(exc)
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    inserted = 0
    with psycopg2.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS v20_corpus_snapshots (
                  snapshot_id text PRIMARY KEY,
                  input_hash text NOT NULL,
                  compiler_version text NOT NULL,
                  created_at timestamptz NOT NULL DEFAULT now(),
                  updated_at timestamptz NOT NULL DEFAULT now(),
                  payload jsonb NOT NULL
                )
                """
            )
            batch = []
            for line in paths.flat_labels_path.open(encoding="utf-8"):
                row = json.loads(line)
                batch.append(
                    (
                        row["case_id"],
                        row["input_hash"],
                        "v20.corpus_label_snapshot.v1",
                        json.dumps(row, ensure_ascii=False, sort_keys=True),
                    )
                )
                if len(batch) >= args.batch_size:
                    inserted += _insert_batch(cur, execute_values, batch)
                    batch.clear()
            if batch:
                inserted += _insert_batch(cur, execute_values, batch)
        conn.commit()
    payload["status"] = "imported"
    payload["inserted_or_updated"] = inserted
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _insert_batch(cur, execute_values, batch) -> int:
    execute_values(
        cur,
        """
        INSERT INTO v20_corpus_snapshots (snapshot_id, input_hash, compiler_version, payload)
        VALUES %s
        ON CONFLICT (snapshot_id) DO UPDATE SET
          input_hash = EXCLUDED.input_hash,
          compiler_version = EXCLUDED.compiler_version,
          payload = EXCLUDED.payload,
          updated_at = now()
        """,
        batch,
    )
    return len(batch)


if __name__ == "__main__":
    raise SystemExit(main())
