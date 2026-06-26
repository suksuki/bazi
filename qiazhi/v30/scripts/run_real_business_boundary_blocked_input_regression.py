from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.real_business_boundary_blocked_input_regression import (
    run_real_business_boundary_blocked_input_regression,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 business boundary/blocked input regression.")
    parser.add_argument("--case-limit", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="Print full JSON result.")
    args = parser.parse_args()

    result = run_real_business_boundary_blocked_input_regression(case_limit=args.case_limit)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        summary = result["boundary_summary"]
        print(
            f"{result['version']}: "
            f"{'passed' if decision['boundary_blocked_input_ready'] else 'failed'} "
            f"({summary['passed_boundary_case_count']}/{summary['boundary_case_count']}) "
            f"{decision['decision_status']}"
        )
        for row in result["boundary_rows"]:
            if not row["boundary_input_ready"]:
                print(f"- {row['case_id']}: {', '.join(row['failed_check_ids'])}")
    return 0 if result["decision"]["boundary_blocked_input_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
