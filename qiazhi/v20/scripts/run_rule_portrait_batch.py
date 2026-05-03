#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.validation.rule_portrait_batch import (  # noqa: E402
    read_rule_portrait_batch_artifact,
    run_rule_portrait_batch,
    write_rule_portrait_batch_artifact,
)
from v20.scripts.contract import run_and_print


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V20 rule/portrait/question batch generation and validation.")
    parser.add_argument("--status", action="store_true", help="Read the latest written local batch artifact.")
    parser.add_argument("--write", action="store_true", help="Write the batch report into the local runtime dir.")
    parser.add_argument("--progress", action="store_true", help="Print progress lines to stderr while running.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        progress = (lambda message: print(f"[v20-batch] {message}", file=sys.stderr, flush=True)) if args.progress else None
        if args.status:
            return read_rule_portrait_batch_artifact()
        if args.write:
            return write_rule_portrait_batch_artifact(progress=progress)
        return run_rule_portrait_batch(progress=progress)

    return run_and_print(
        _run,
        command="run_rule_portrait_batch.py",
        args=args,
        runtime_mutation=args.write,
    )


if __name__ == "__main__":
    raise SystemExit(main())
