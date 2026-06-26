#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.lightweight_core_monitoring_checks import run_lightweight_core_monitoring_checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V30 P1 lightweight core monitoring checks.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_lightweight_core_monitoring_checks(sample_limit=args.sample_limit)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        summary = result["check_summary"]
        next_task = result["next_mainline_selection"]
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"- checks: {summary['passed_check_count']}/{summary['required_check_count']}")
        print(f"- regression_detected: {decision['regression_detected']}")
        print(f"- failed_check_ids: {decision['failed_check_ids']}")
        print(f"- pointer_promotion_allowed: {decision['policy_pointer_promotion_allowed']}")
        print(f"- next: {next_task['task_id']} {next_task['title']}")
        print(f"- boundary: {result['boundary']}")
    return 0 if result["decision"]["monitoring_checks_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
