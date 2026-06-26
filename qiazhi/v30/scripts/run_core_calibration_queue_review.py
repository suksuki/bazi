#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.core_calibration_queue_review import run_core_calibration_queue_review


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V30 P5 core calibration queue review.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_core_calibration_queue_review(sample_limit=args.sample_limit)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        next_task = result["next_mainline_selection"]
        print(f"{result['version']}: {decision['decision_status']}")
        print(f"- reviewed_modules: {decision['reviewed_module_count']}")
        print(f"- focused_fix_candidates: {decision['focused_fix_candidate_count']}")
        print(f"- focused_module_fix_required: {decision['focused_module_fix_required']}")
        print(f"- full_pytest_required: {decision['full_pytest_required']}")
        print(f"- pointer_promotion_allowed: {decision['policy_pointer_promotion_allowed']}")
        print(f"- next: {next_task['task_id']} {next_task['title']}")
        print(f"- boundary: {result['boundary']}")
    return 0 if result["decision"]["queue_review_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
