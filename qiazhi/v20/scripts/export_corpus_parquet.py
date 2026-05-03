#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
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
    parser = argparse.ArgumentParser(description="Convert V20 flat corpus labels JSONL to Parquet.")
    parser.add_argument("--run-id", default="", help="Defaults to the latest full precompute artifact run.")
    parser.add_argument("--target", default="")
    parser.add_argument("--progress", action="store_true", help="Print coarse export phases to stderr.")
    args = parser.parse_args()

    run_id = resolve_corpus_artifact_run_id(args.run_id)
    paths = corpus_artifact_paths(run_id)
    target = Path(args.target) if args.target else paths.artifact_dir / "flat_labels.parquet"
    def _run() -> dict[str, object]:
        base_payload = {
            "version": "v20.corpus_parquet_export_cli.v1",
            "run_id": run_id,
            "source": str(paths.flat_labels_path),
            "target": str(target),
            "runtime_mutation": False,
            "guardrails": [
                "PARQUET_IS_DERIVED_ARTIFACT",
                "FLAT_JSONL_REMAINS_EXPORT_SOURCE",
                "RUNTIME_RULE_ACTIVATION_ALLOWED_WITH_TRACE",
            ],
        }
        return _export(paths, target, base_payload, progress=args.progress)

    return run_and_print(
        _run,
        command="export_corpus_parquet.py",
        args=argparse.Namespace(run_id=args.run_id, target=args.target, progress=args.progress),
        runtime_mutation=True,
    )


def _export(paths: Any, target: Path, payload: dict[str, object], *, progress: bool) -> dict[str, object]:
    try:
        import pyarrow as pa
        import pyarrow.json as paj
        import pyarrow.parquet as pq
    except Exception as exc:
        return payload | {
            "status": "blocked_missing_pyarrow",
            "error": str(exc),
        }

    if not paths.flat_labels_path.exists():
        return payload | {"status": "blocked_missing_flat_labels"}
    started = time.monotonic()
    if progress:
        _emit("read_json", started)
    table = paj.read_json(str(paths.flat_labels_path))
    target.parent.mkdir(parents=True, exist_ok=True)
    if progress:
        _emit(f"write_parquet rows={table.num_rows}", started)
    pq.write_table(table, target, compression="zstd")
    if progress:
        _emit("completed", started)
    return payload | {
        "status": "exported",
        "row_count": table.num_rows,
        "pyarrow_version": pa.__version__,
        "runtime_mutation": True,
    }


def _emit(message: str, started: float) -> None:
    print(f"[v20-parquet-export] {message} elapsed={time.monotonic() - started:.1f}s", file=sys.stderr, flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
