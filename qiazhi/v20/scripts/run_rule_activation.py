#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v20.learning.rule_activation import (  # noqa: E402
    build_rule_activation_report,
    build_rule_activation_packet_summary,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build V20 rule activation gate packets from active rule validation.")
    parser.add_argument("--domain", default="", help="Optional domain filter.")
    parser.add_argument("--limit", type=int, default=64)
    parser.add_argument("--summary", action="store_true", help="Print compact packets for admin review.")
    args = parser.parse_args()

    payload = (
        build_rule_activation_packet_summary(args.domain, limit=args.limit)
        if args.summary
        else build_rule_activation_report(args.domain, limit=args.limit)
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
