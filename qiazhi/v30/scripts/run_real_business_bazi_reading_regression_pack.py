from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.real_business_bazi_reading_regression_pack import run_real_business_bazi_reading_regression_pack


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 business Bazi reading regression pack.")
    parser.add_argument("--case-limit", type=int, default=24)
    parser.add_argument("--json", action="store_true", help="Print full JSON result.")
    args = parser.parse_args()

    result = run_real_business_bazi_reading_regression_pack(case_limit=args.case_limit)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        summary = result["regression_summary"]
        print(
            f"{result['version']}: "
            f"{'passed' if decision['business_reading_regression_ready'] else 'failed'} "
            f"({summary['passed_case_count']}/{summary['regression_case_count']}) "
            f"{decision['decision_status']}"
        )
        for row in result["regression_rows"]:
            if not row["regression_ready"]:
                print(f"- {row['case_id']}: {', '.join(row['failed_check_ids'])}")
    return 0 if result["decision"]["business_reading_regression_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
