#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.scripts.contract import run_and_print  # noqa: E402
from v20.validation.structure_dynamics_corpus_distribution import (  # noqa: E402
    build_structure_dynamics_corpus_distribution,
    read_latest_structure_dynamics_corpus_distribution,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V20 structure dynamics corpus path distribution replay.")
    parser.add_argument("--run-id", default="", help="Stable artifact run id.")
    parser.add_argument("--start", type=int, default=0, help="Start index in the 518K corpus.")
    parser.add_argument("--limit", type=int, default=64, help="Number of corpus cases to replay.")
    parser.add_argument("--write", action="store_true", help="Write versioned distribution artifact and latest pointer.")
    parser.add_argument("--status", action="store_true", help="Read latest distribution artifact instead of replaying.")
    parser.add_argument("--summary", action="store_true", help="Return summary without example cases.")
    parser.add_argument("--progress", action="store_true", help="Print progress lines to stderr while running.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        if args.status:
            payload = read_latest_structure_dynamics_corpus_distribution()
        else:
            payload = build_structure_dynamics_corpus_distribution(
                start=args.start,
                limit=args.limit,
                run_id=args.run_id,
                write=args.write,
                progress=(lambda message: print(f"[v20-sde-corpus] {message}", file=sys.stderr, flush=True)) if args.progress else None,
            )
        if args.summary:
            return {
                key: value
                for key, value in payload.items()
                if key not in {"example_cases_by_label"}
            }
        return payload

    return run_and_print(
        _run,
        command="run_structure_dynamics_corpus_distribution.py",
        args=args,
        runtime_mutation=args.write and not args.status,
    )


if __name__ == "__main__":
    raise SystemExit(main())
