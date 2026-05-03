#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.corpus.artifacts import (  # noqa: E402
    build_corpus_artifacts,
    find_similar_cases,
    read_corpus_artifact_status,
    read_corpus_cluster_model,
    read_corpus_coverage_summary,
    read_corpus_training_artifacts,
)
from v20.scripts.contract import run_and_print


def main() -> int:
    parser = argparse.ArgumentParser(description="Build V20 corpus coverage, indexes, and training artifacts.")
    parser.add_argument("--run-id", default="", help="Defaults to the latest full precompute run when reading; required for building if you do not want the historical main id.")
    parser.add_argument("--progress", action="store_true", help="Print progress lines to stderr while building.")
    parser.add_argument("--no-sqlite", action="store_true", help="Skip the disposable local SQLite similarity cache.")
    parser.add_argument("--status", action="store_true", help="Read artifact build status.")
    parser.add_argument("--summary", action="store_true", help="Read coverage summary.")
    parser.add_argument("--clusters", action="store_true", help="Read the deterministic cluster model.")
    parser.add_argument("--training", action="store_true", help="Read portrait/rule training artifacts.")
    parser.add_argument("--similar-case-id", default="", help="Find structurally similar cases from Postgres, falling back to local SQLite cache.")
    parser.add_argument("--limit", type=int, default=8, help="Similarity result limit.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        if args.status:
            return read_corpus_artifact_status(args.run_id)
        if args.summary:
            return read_corpus_coverage_summary(args.run_id)
        if args.clusters:
            return read_corpus_cluster_model(args.run_id)
        if args.training:
            return read_corpus_training_artifacts(args.run_id)
        if args.similar_case_id:
            return find_similar_cases(args.similar_case_id, run_id=args.run_id, limit=args.limit)

        progress = (
            lambda message: print(f"[v20-corpus-artifacts] {message}", file=sys.stderr, flush=True)
        ) if args.progress else None
        return build_corpus_artifacts(
            args.run_id or "v20_full_518k_20260501_main",
            progress=progress,
            build_sqlite_cache=not args.no_sqlite,
        )

    return run_and_print(
        _run,
        command="build_corpus_artifacts.py",
        args=args,
        runtime_mutation=not args.status and not args.summary and not args.clusters and not args.training and not args.similar_case_id,
    )


if __name__ == "__main__":
    raise SystemExit(main())
