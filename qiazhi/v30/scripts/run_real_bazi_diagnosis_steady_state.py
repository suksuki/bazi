from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_real_bazi_diagnosis_steady_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RBD S1.13 steady-state closeout.")
    parser.add_argument("--real-case-limit", type=int, default=8)
    parser.add_argument("--sample-518k-limit", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_real_bazi_diagnosis_steady_state(
        real_case_limit=args.real_case_limit,
        sample_518k_limit=args.sample_518k_limit,
    )
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            "v30.real_bazi_diagnosis_steady_state.v1: "
            f"{'passed' if decision['rbd_steady_state_ready'] else 'failed'} "
            f"({decision['passed_closeout_check_count']}/{decision['closeout_check_count']}) "
            f"{decision['decision_status']}"
        )
        print(
            f"- signals={decision['training_signal_count']} "
            f"queue_items={decision['queued_item_count']} "
            f"next={result['next_mainline_selection']['task_id']}"
        )
    return 0 if decision["rbd_steady_state_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
