from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_synthetic_archetype_calibration_closeout


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SYN-CAL4 synthetic archetype calibration closeout.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_synthetic_archetype_calibration_closeout()
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"{result['version']}: "
            f"{'passed' if decision['synthetic_archetype_calibration_closed'] else 'blocked'} "
            f"({decision['passed_closeout_check_count']}/{decision['closeout_check_count']}) "
            f"{decision['decision_status']}"
        )
        print(
            f"- signals={decision['training_signal_count']} "
            f"queue_items={decision['queued_item_count']} "
            f"auto_apply={decision['auto_apply_training_allowed']} "
            f"full_pytest={decision['full_pytest_required']}"
        )
        print(f"- next={result['next_mainline_selection']['task_id']}")
    return 0 if decision["synthetic_archetype_calibration_closed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
