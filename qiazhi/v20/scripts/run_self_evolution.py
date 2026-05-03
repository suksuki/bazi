#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning.self_evolution import (  # noqa: E402
    read_self_evolution_artifact,
    run_self_evolution_cycle,
)
from v20.scripts.contract import run_and_print


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V20 backend self-evolution manifest cycle.")
    parser.add_argument("--status", action="store_true", help="Read the latest written local evolution artifact.")
    parser.add_argument("--write", action="store_true", help="Write a local evolution manifest artifact.")
    parser.add_argument("--progress", action="store_true", help="Print progress lines to stderr while running.")
    parser.add_argument("--skip-rule-batch", action="store_true", help="Skip the rule/portrait/question batch phase.")
    parser.add_argument("--corpus-preview", type=int, default=0, help="Optionally preview N full-corpus cases.")
    args = parser.parse_args()

    progress = (
        lambda message: print(f"[v20-self-evolution] {message}", file=sys.stderr, flush=True)
    ) if args.progress else None
    def _run() -> dict[str, object]:
        progress = (
            lambda message: print(f"[v20-self-evolution] {message}", file=sys.stderr, flush=True)
        ) if args.progress else None
        if args.status:
            return read_self_evolution_artifact()
        return run_self_evolution_cycle(
            write=args.write,
            include_rule_batch=not args.skip_rule_batch,
            corpus_preview_limit=max(0, args.corpus_preview),
            progress=progress,
        )

    return run_and_print(
        _run,
        command="run_self_evolution.py",
        args=args,
        runtime_mutation=args.write,
    )


if __name__ == "__main__":
    raise SystemExit(main())
