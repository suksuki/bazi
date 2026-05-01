#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.corpus.enumerator import FULL_CORPUS_CASE_COUNT
from v20.corpus.job_runner import (
    FullPrecomputeJobConfig,
    default_full_precompute_run_id,
    read_full_precompute_status,
    run_full_precompute_job,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V20 full 518K corpus precompute locally.")
    parser.add_argument("--run-id", default="", help="Stable run id. Defaults to a timestamped id.")
    parser.add_argument("--start", type=int, default=0, help="Start index in the 518K corpus.")
    parser.add_argument("--limit", type=int, default=FULL_CORPUS_CASE_COUNT, help="Number of cases to process.")
    parser.add_argument("--status-every", type=int, default=500, help="Write progress every N processed cases.")
    parser.add_argument("--no-resume", action="store_true", help="Ignore existing progress for the same run id.")
    parser.add_argument("--status", action="store_true", help="Print latest or run-specific status instead of running.")
    parser.add_argument("--progress", action="store_true", help="Print progress lines to stderr while running.")
    args = parser.parse_args()

    run_id = args.run_id or default_full_precompute_run_id()
    if args.status:
        print(json.dumps(read_full_precompute_status(args.run_id), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    config = FullPrecomputeJobConfig(
        run_id=run_id,
        start=args.start,
        limit=args.limit,
        status_every=args.status_every,
        resume=not args.no_resume,
    )
    progress = (
        lambda message: print(f"[v20-full-precompute] {message}", file=sys.stderr, flush=True)
    ) if args.progress else None
    result = run_full_precompute_job(config, progress=progress)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
