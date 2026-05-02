#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Build V20 active rule subcondition split proposals.")
    parser.add_argument("--domain", default="", help="Optional domain filter.")
    parser.add_argument("--limit", type=int, default=64, help="Maximum knowledge rule definitions to inspect.")
    parser.add_argument("--per-rule", type=int, default=5, help="Maximum subconditions per rule.")
    parser.add_argument("--write", action="store_true", help="Write a local runtime artifact.")
    parser.add_argument("--status", action="store_true", help="Read latest written local artifact.")
    parser.add_argument("--progress", action="store_true", help="Print progress to stderr.")
    args = parser.parse_args()

    progress = (lambda message: print(message, file=sys.stderr, flush=True)) if args.progress else None
    if args.status:
        payload = read_rule_subcondition_split_artifact()
    elif args.write:
        payload = write_rule_subcondition_split_artifact(
            domain=args.domain,
            limit=max(1, args.limit),
            per_rule=max(1, args.per_rule),
            progress=progress,
        )
    else:
        payload = build_rule_subcondition_split_report(
            args.domain,
            limit=max(1, args.limit),
            per_rule=max(1, args.per_rule),
            progress=progress,
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload.get("status") not in {"fail", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
