#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.corpus.artifacts import corpus_artifact_paths, resolve_corpus_artifact_run_id  # noqa: E402
from v20.scripts.contract import run_and_print


def main() -> int:
    parser = argparse.ArgumentParser(description="Import V20 flat corpus labels into Postgres.")
    parser.add_argument("--run-id", default="", help="Defaults to the latest full precompute artifact run.")
    parser.add_argument(
        "--env-file",
        default="v20/.runtime/local/service.env",
        help="Load V20 local env before importing. Existing real shell values win; placeholder templates are replaced.",
    )
    parser.add_argument("--apply", action="store_true", help="Actually write Postgres. Default is dry-run only.")
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--progress", action="store_true", help="Print a progress bar to stderr while importing.")
    args = parser.parse_args()

    run_id = resolve_corpus_artifact_run_id(args.run_id)
    def _run() -> dict[str, object]:
        _load_env_file(Path(args.env_file))
        return _import_once(args.apply, args.batch_size, args.progress, run_id)

    return run_and_print(
        _run,
        command="import_corpus_postgres.py",
        args=args,
        runtime_mutation=args.apply,
    )


def _import_once(apply: bool, batch_size: int, progress: bool, run_id: str) -> dict[str, object]:
    paths = corpus_artifact_paths(run_id)
    url = os.getenv("V20_DATABASE_URL", "")
    payload: dict[str, object] = {
        "version": "v20.corpus_postgres_import_cli.v1",
        "run_id": run_id,
        "source": str(paths.flat_labels_path),
        "target_table": "v20_corpus_snapshots",
        "apply": apply,
        "database_url_present": bool(url),
        "runtime_mutation": bool(apply),
        "guardrails": [
            "EXPLICIT_APPLY_REQUIRED",
            "BACKUP_REQUIRED_BEFORE_REMOTE_IMPORT",
            "NO_SECRET_VALUES_RENDERED",
        ],
    }
    if not apply:
        payload["status"] = "dry_run"
        return payload
    if not url:
        payload["status"] = "blocked_missing_V20_DATABASE_URL"
        return payload
    if not paths.flat_labels_path.exists():
        payload["status"] = "blocked_missing_flat_labels"
        return payload

    try:
        import psycopg2
        from psycopg2.extras import execute_values
    except Exception as exc:
        return payload | {"status": "blocked_missing_psycopg2", "error": str(exc)}

    inserted = 0
    total = _count_lines(paths.flat_labels_path) if progress else 0
    started = time.monotonic()
    if progress:
        _emit_progress(inserted, total, started, "starting")
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
                if len(batch) >= max(1, batch_size):
                    inserted += _insert_batch(cur, execute_values, batch)
                    if progress:
                        _emit_progress(inserted, total, started, "importing")
                    batch.clear()
            if batch:
                inserted += _insert_batch(cur, execute_values, batch)
                if progress:
                    _emit_progress(inserted, total, started, "importing")
            _create_indexes(cur)
            if progress:
                _emit_progress(inserted, total, started, "indexing")
        conn.commit()
    if progress:
        _emit_progress(inserted, total, started, "completed")
    payload["status"] = "imported"
    payload["inserted_or_updated"] = inserted
    return payload


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


def _create_indexes(cur) -> None:
    for statement in (
        "CREATE INDEX IF NOT EXISTS idx_v20_corpus_snapshots_input_hash ON v20_corpus_snapshots(input_hash)",
        "CREATE INDEX IF NOT EXISTS idx_v20_corpus_payload_day_master ON v20_corpus_snapshots ((payload->>'day_master'))",
        "CREATE INDEX IF NOT EXISTS idx_v20_corpus_payload_day_master_element ON v20_corpus_snapshots ((payload->>'day_master_element'))",
        "CREATE INDEX IF NOT EXISTS idx_v20_corpus_payload_day_master_capacity ON v20_corpus_snapshots ((payload->>'day_master_capacity'))",
        "CREATE INDEX IF NOT EXISTS idx_v20_corpus_payload_cluster_key ON v20_corpus_snapshots ((payload->>'cluster_key'))",
        "CREATE INDEX IF NOT EXISTS idx_v20_corpus_payload_wealth ON v20_corpus_snapshots (((payload->>'wealth_feature_present')::boolean))",
        "CREATE INDEX IF NOT EXISTS idx_v20_corpus_payload_wealth_level ON v20_corpus_snapshots ((payload->>'wealth_material_level'))",
        "CREATE INDEX IF NOT EXISTS idx_v20_corpus_payload_mainline_domains ON v20_corpus_snapshots USING gin ((payload->'mainline_domains'))",
        "CREATE INDEX IF NOT EXISTS idx_v20_corpus_payload_gin ON v20_corpus_snapshots USING gin (payload)",
    ):
        cur.execute(statement)


def _count_lines(path: Path) -> int:
    with path.open(encoding="utf-8") as source:
        return sum(1 for line in source if line.strip())


def _emit_progress(done: int, total: int, started: float, status: str) -> None:
    ratio = min(1.0, done / total) if total else 0.0
    width = 24
    filled = max(0, min(width, round(width * ratio)))
    bar = "#" * filled + "-" * (width - filled)
    elapsed = max(0.001, time.monotonic() - started)
    rate = done / elapsed if done else 0.0
    remaining = max(0, total - done)
    eta = remaining / rate if rate > 0 else None
    eta_text = "unknown" if eta is None else f"{eta:.1f}s"
    print(
        f"[v20-postgres-import] [{bar}] {ratio * 100:6.2f}% "
        f"rows={done}/{total or '?'} status={status} rate={rate:.1f}/s eta={eta_text}",
        file=sys.stderr,
        flush=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
