#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.mainline_selection import run_mainline_selection


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V30 M0 mainline selection review.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_mainline_selection(sample_limit=args.sample_limit)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        next_task = result["next_mainline_selection"]
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"- next: {next_task['task_id']} {next_task['title']}")
        print(f"- full_pytest_run_now: {decision['full_pytest_run_now']}")
        print(f"- pointer_promotion_allowed: {decision['policy_pointer_promotion_allowed']}")
        print(f"- boundary: {result['boundary']}")
    return 0 if result["decision"]["mainline_selection_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
