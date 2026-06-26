from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.training_system_closeout import run_training_system_closeout


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 BT4 training system closeout gate.")
    parser.add_argument("--training-run-id", default="bt4-closeout")
    parser.add_argument("--json", action="store_true", help="Print full JSON result.")
    args = parser.parse_args()

    result = run_training_system_closeout(training_run_id=args.training_run_id)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        checks = result["closeout_checks"]
        passed = sum(1 for row in checks if row["passed"])
        print(
            f"{result['version']}: "
            f"{'passed' if decision['training_system_closeout_ready'] else 'failed'} "
            f"({passed}/{len(checks)}) "
            f"{decision['decision_status']}"
        )
        for row in checks:
            if not row["passed"]:
                print(f"- {row['check_id']}: {row['expected']}")
    return 0 if result["decision"]["training_system_closeout_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
