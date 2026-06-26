#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning_orchestrator.nightly_executor import (  # noqa: E402
    read_nightly_executor_status,
    run_nightly_executor_skeleton,
)
from v20.scripts.contract import run_and_print  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V20 nightly learning executor skeleton.")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--status-every", type=int, default=2)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        if args.status:
            return read_nightly_executor_status(args.run_id)
        progress = (
            lambda message: print(f"[v20-nightly-executor] {message}", file=sys.stderr, flush=True)
        ) if args.progress else None
        return run_nightly_executor_skeleton(
            run_id=args.run_id,
            start=max(0, args.start),
            limit=max(1, args.limit),
            status_every=max(1, args.status_every),
            resume=not args.no_resume,
            progress=progress,
        )

    return run_and_print(
        _run,
        command="run_nightly_learning_executor.py",
        args=args,
        runtime_mutation=not args.status,
    )


if __name__ == "__main__":
    raise SystemExit(main())
