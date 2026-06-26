from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_core_calibration_steady_state_queue


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CORE-CAL-S0 core calibration steady-state queue.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--artifact-dir", default=".runtime/validation/core-calibration-s0")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_core_calibration_steady_state_queue(
        sample_limit=args.sample_limit,
        artifact_dir=args.artifact_dir,
    )
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"{result['version']}: "
            f"{'passed' if decision['core_calibration_steady_state_queue_ready'] else 'blocked'} "
            f"({decision['passed_check_count']}/{decision['check_count']}) "
            f"{decision['decision_status']}"
        )
        print(
            f"- waiting={decision['waiting_for_new_calibration_evidence']} "
            f"candidates={decision['focused_fix_candidate_count']} "
            f"full_pytest={decision['full_pytest_required']} "
            f"auto_apply={decision['auto_apply_training_allowed']}"
        )
        print(f"- next={result['next_mainline_selection']['task_id']}")
    return 0 if decision["core_calibration_steady_state_queue_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
