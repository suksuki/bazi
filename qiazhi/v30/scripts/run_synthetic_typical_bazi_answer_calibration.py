from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.synthetic_typical_bazi_answer_calibration import run_synthetic_typical_bazi_answer_calibration


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 CORE-CAL-S1 synthetic typical Bazi answer calibration.")
    parser.add_argument("--json", action="store_true", help="Print full JSON artifact.")
    args = parser.parse_args()

    result = run_synthetic_typical_bazi_answer_calibration()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    decision = result["decision"]
    print(f"{result['version']}: {decision['decision_status']}")
    print(
        f"passed={decision['passed_case_count']}/{decision['case_count']} "
        f"ready={decision['synthetic_typical_answer_calibration_ready']}"
    )
    if decision["failed_case_ids"]:
        print("failed_cases=" + ", ".join(decision["failed_case_ids"]))
    if decision["failed_check_ids"]:
        print("failed_checks=" + ", ".join(decision["failed_check_ids"]))
    next_task = result["next_mainline_selection"]
    print(f"next={next_task['task_id']} {next_task['title']}")
    return 0 if decision["synthetic_typical_answer_calibration_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
