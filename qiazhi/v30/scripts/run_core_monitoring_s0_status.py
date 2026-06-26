#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.core_monitoring_s0_status import run_core_monitoring_s0_status


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V30 S0 core monitoring steady-state status.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_core_monitoring_s0_status(sample_limit=args.sample_limit)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        next_task = result["next_mainline_selection"]
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"- status_checks: {decision['passed_status_check_count']}/{decision['status_check_count']}")
        print(f"- waiting_for_new_evidence: {decision['waiting_for_new_evidence']}")
        print(f"- new_core_monitoring_task_allowed_by_default: {decision['new_core_monitoring_task_allowed_by_default']}")
        print(f"- future_monitoring_ready: {decision['future_monitoring_ready']}")
        print(f"- pointer_promotion_allowed: {decision['policy_pointer_promotion_allowed']}")
        print(f"- next: {next_task['task_id']} {next_task['title']}")
        print(f"- boundary: {result['boundary']}")
    return 0 if result["decision"]["s0_status_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
