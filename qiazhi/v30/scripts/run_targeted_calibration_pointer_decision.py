from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.targeted_calibration_pointer_decision import run_targeted_calibration_pointer_decision


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 targeted calibration pointer decision.")
    parser.add_argument("--decision-id", default=None)
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--operator-decision", choices=("defer", "request_promotion"), default="defer")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_targeted_calibration_pointer_decision(
        decision_id=args.decision_id,
        sample_limit=args.sample_limit,
        operator_decision=args.operator_decision,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        print(
            f"{result['version']}: {decision['decision_status']} "
            f"(operator_decision={result['operator_decision']}, "
            f"pointer_write={result['pointer_write_summary']['pointer_write_performed']})"
        )
        for blocker in decision["blockers"]:
            print(f"- blocker: {blocker}")
        print(f"- next: {result['next_mainline_selection']['task_id']} {result['next_mainline_selection']['title']}")
        print(f"- boundary: {result['boundary']}")
    return 0 if result["decision"]["pointer_decision_recorded"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
