#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning.training_iteration import (  # noqa: E402
    read_training_iteration_artifact,
    run_training_iteration,
)
from v20.scripts.contract import run_and_print


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V20 script-only training/validation iteration.")
    parser.add_argument("--status", action="store_true", help="Read the latest written local iteration artifact.")
    parser.add_argument("--write", action="store_true", help="Write local training artifacts and an iteration report.")
    parser.add_argument("--progress", action="store_true", help="Print progress lines to stderr while running.")
    parser.add_argument("--include-rule-batch", action="store_true", help="Include the heavier rule/portrait/question batch phase.")
    parser.add_argument("--include-replay-eval", action="store_true", help="Include the heavier rule replay evaluation phase.")
    parser.add_argument("--skip-rule-batch", action="store_true", help="Deprecated no-op; the rule batch is skipped unless --include-rule-batch is set.")
    parser.add_argument("--dynamic-limit", type=int, default=12, help="Limit dynamic decision cases for the daily iteration; use 0 for all cases.")
    parser.add_argument("--rule-iteration-limit", type=int, default=120, help="Limit rule iteration packets for the daily iteration; use 0 for all rules.")
    parser.add_argument("--corpus-preview", type=int, default=0, help="Optionally preview N full-corpus cases.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        progress = (
            lambda message: print(f"[v20-iteration] {message}", file=sys.stderr, flush=True)
        ) if args.progress else None
        if args.status:
            return read_training_iteration_artifact()
        return run_training_iteration(
            write=args.write,
            include_rule_batch=args.include_rule_batch and not args.skip_rule_batch,
            include_replay_eval=args.include_replay_eval,
            dynamic_case_limit=max(0, args.dynamic_limit),
            rule_iteration_limit=max(0, args.rule_iteration_limit),
            corpus_preview_limit=max(0, args.corpus_preview),
            progress=progress,
        )

    return run_and_print(
        _run,
        command="run_training_iteration.py",
        args=args,
        runtime_mutation=args.write,
    )


if __name__ == "__main__":
    raise SystemExit(main())
