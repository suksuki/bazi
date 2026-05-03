#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning.rule_activation import (  # noqa: E402
    build_rule_activation_report,
    build_rule_activation_packet_summary,
)
from v20.scripts.contract import run_and_print


def main() -> int:
    parser = argparse.ArgumentParser(description="Build V20 rule activation gate packets from active rule validation.")
    parser.add_argument("--domain", default="", help="Optional domain filter.")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--summary", action="store_true", help="Print compact packets for admin review.")
    args = parser.parse_args()

    def _run() -> dict[str, object]:
        return (
            build_rule_activation_packet_summary(args.domain, limit=args.limit)
            if args.summary
            else build_rule_activation_report(args.domain, limit=args.limit)
        )

    return run_and_print(
        _run,
        command="run_rule_activation.py",
        args=args,
        runtime_mutation=False,
    )


if __name__ == "__main__":
    raise SystemExit(main())
