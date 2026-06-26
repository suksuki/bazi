#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.core_monitoring_loop import run_core_monitoring_loop


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V30 P0 core monitoring loop review.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_core_monitoring_loop(sample_limit=args.sample_limit)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        next_task = result["next_mainline_selection"]
        monitoring = result["monitoring_baseline_summary"]
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"- monitoring_checks: {monitoring['check_count']}/{monitoring['required_check_count']}")
        print(f"- regression_detected: {decision['regression_detected']}")
        print(f"- core_module_reopen_recommended: {decision['core_module_reopen_recommended']}")
        print(f"- pointer_promotion_allowed: {decision['policy_pointer_promotion_allowed']}")
        print(f"- next: {next_task['task_id']} {next_task['title']}")
        print(f"- boundary: {result['boundary']}")
    return 0 if result["decision"]["monitoring_loop_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
