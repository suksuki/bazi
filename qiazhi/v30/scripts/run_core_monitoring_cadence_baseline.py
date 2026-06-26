#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.core_monitoring_cadence_baseline import run_core_monitoring_cadence_baseline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V30 P7 core monitoring cadence baseline.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_core_monitoring_cadence_baseline(sample_limit=args.sample_limit)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        cadence = result["cadence_rules"]
        next_task = result["next_mainline_selection"]
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"- default_cadence: {cadence['default_cadence']}")
        print(f"- current_cycle_closed: {decision['current_cycle_closed']}")
        print(f"- future_monitoring_ready: {decision['future_monitoring_ready']}")
        print(f"- default_heavy_validation_allowed: {decision['default_heavy_validation_allowed']}")
        print(f"- pointer_promotion_allowed: {decision['policy_pointer_promotion_allowed']}")
        print(f"- next: {next_task['task_id']} {next_task['title']}")
        print(f"- boundary: {result['boundary']}")
    return 0 if result["decision"]["cadence_baseline_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
