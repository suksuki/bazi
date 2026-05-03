#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning.rule_subcondition_split import (  # noqa: E402
    build_rule_subcondition_split_report,
    read_rule_subcondition_split_artifact,
    write_rule_subcondition_split_artifact,
)
from v20.scripts.contract import run_and_print


def main() -> int:
    parser = argparse.ArgumentParser(description="Build V20 active rule subcondition split proposals.")
    parser.add_argument("--domain", default="", help="Optional domain filter.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum knowledge rule definitions to inspect.")
    parser.add_argument("--per-rule", type=int, default=0, help="Maximum subconditions per rule (0=all).")
    parser.add_argument("--write", action="store_true", help="Write a local runtime artifact.")
    parser.add_argument("--status", action="store_true", help="Read latest written local artifact.")
    parser.add_argument("--progress", action="store_true", help="Print progress to stderr.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        progress = (lambda message: print(message, file=sys.stderr, flush=True)) if args.progress else None
        if args.status:
            return read_rule_subcondition_split_artifact()
        if args.write:
            return write_rule_subcondition_split_artifact(
                domain=args.domain,
                limit=args.limit,
                per_rule=args.per_rule,
                progress=progress,
            )
        return build_rule_subcondition_split_report(
            args.domain,
            limit=args.limit,
            per_rule=args.per_rule,
            progress=progress,
        )

    return run_and_print(
        _run,
        command="run_rule_subcondition_split.py",
        args=args,
        runtime_mutation=args.write,
    )


if __name__ == "__main__":
    raise SystemExit(main())
