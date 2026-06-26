#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.external_release_dry_run import run_external_release_dry_run


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V30 R13 external-release dry run review.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument(
        "--full-pytest-decision",
        choices=("defer", "record_passed", "record_failed"),
        default="defer",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_external_release_dry_run(
        sample_limit=args.sample_limit,
        full_pytest_decision=args.full_pytest_decision,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        next_task = result["next_mainline_selection"]
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"- external_release_ready: {decision['external_release_ready']}")
        print(f"- full_pytest_deferred: {decision['full_pytest_deferred']}")
        print(f"- pointer_promotion_allowed: {decision['policy_pointer_promotion_allowed']}")
        print(f"- next: {next_task['task_id']} {next_task['title']}")
        print(f"- boundary: {result['boundary']}")
    return 0 if result["decision"]["dry_run_review_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
