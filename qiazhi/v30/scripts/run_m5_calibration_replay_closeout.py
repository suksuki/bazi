from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_m5_calibration_replay_closeout


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 M5 calibration replay closeout.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--artifact-dir", default=".runtime/validation/m5")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_m5_calibration_replay_closeout(
        sample_limit=args.sample_limit,
        artifact_dir=args.artifact_dir,
    )
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"{result['version']}: "
            f"{'passed' if decision['m5_calibration_replay_closed'] else 'blocked'} "
            f"({decision['passed_closeout_check_count']}/{decision['closeout_check_count']}) "
            f"{decision['decision_status']} "
            f"cases={decision['ranked_observation_count']} "
            f"complete={decision['complete_domain_observation_count']} "
            f"close_candidates={decision['close_candidate_count']} "
            f"next={result['next_mainline_selection']['next_task']}"
        )
    return 0 if decision["m5_calibration_replay_closed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
