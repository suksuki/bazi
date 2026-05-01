#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.corpus.artifacts import DEFAULT_ARTIFACT_RUN_ID, corpus_artifact_paths  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert V20 flat corpus labels JSONL to Parquet.")
    parser.add_argument("--run-id", default=DEFAULT_ARTIFACT_RUN_ID)
    parser.add_argument("--target", default="")
    args = parser.parse_args()

    paths = corpus_artifact_paths(args.run_id)
    target = Path(args.target) if args.target else paths.artifact_dir / "flat_labels.parquet"
    payload = {
        "version": "v20.corpus_parquet_export_cli.v1",
        "run_id": args.run_id,
        "source": str(paths.flat_labels_path),
        "target": str(target),
        "runtime_mutation": False,
        "guardrails": [
            "PARQUET_IS_DERIVED_ARTIFACT",
            "FLAT_JSONL_REMAINS_EXPORT_SOURCE",
            "NO_RUNTIME_RULE_ACTIVATION",
        ],
    }
    try:
        import pyarrow as pa
        import pyarrow.json as paj
        import pyarrow.parquet as pq
    except Exception as exc:
        payload["status"] = "blocked_missing_pyarrow"
        payload["error"] = str(exc)
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    if not paths.flat_labels_path.exists():
        payload["status"] = "blocked_missing_flat_labels"
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    table = paj.read_json(str(paths.flat_labels_path))
    target.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, target, compression="zstd")
    payload["status"] = "exported"
    payload["row_count"] = table.num_rows
    payload["pyarrow_version"] = pa.__version__
    payload["runtime_mutation"] = True
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
