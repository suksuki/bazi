#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.ops.main_chain import build_main_chain_review  # noqa: E402
from v20.scripts.contract import run_and_print  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Review the V20 Bazi intelligent main chain end to end.")
    parser.add_argument("--rule-limit", type=int, default=0, help="Limit knowledge-rule definitions; 0 means all.")
    parser.add_argument("--include-training", action="store_true", help="Also run the dry-run learning iteration.")
    parser.add_argument("--progress", action="store_true", help="Print progress lines while training is included.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        progress = (
            lambda message: print(f"[v20-main-chain] {message}", file=sys.stderr, flush=True)
        ) if args.progress else None
        return build_main_chain_review(
            rule_limit=max(0, args.rule_limit),
            include_training=args.include_training,
            progress=progress,
        )

    return run_and_print(
        _run,
        command="run_main_chain_review.py",
        args=args,
        runtime_mutation=False,
    )


if __name__ == "__main__":
    raise SystemExit(main())
