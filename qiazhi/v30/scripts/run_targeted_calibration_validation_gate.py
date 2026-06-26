from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.targeted_calibration_validation_gate import run_targeted_calibration_validation_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 targeted calibration validation gate.")
    parser.add_argument("--gate-id", default=None)
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    review = run_targeted_calibration_validation_gate(
        gate_id=args.gate_id,
        sample_limit=args.sample_limit,
    )
    if args.json:
        print(json.dumps(review, ensure_ascii=False, indent=2))
    else:
        decision = review["decision"]
        print(
            f"{review['version']}: {decision['decision_status']} "
            f"(synthetic={review['synthetic_all_summary']['passed_count']}/{review['synthetic_all_summary']['case_count']}, "
            f"518k={review['corpus_518k_sample_summary']['case_count']})"
        )
        for blocker in decision["blockers"]:
            print(f"- blocker: {blocker}")
        print(f"- next: {review['next_mainline_selection']['task_id']} {review['next_mainline_selection']['title']}")
        print(f"- boundary: {review['boundary']}")
    return 0 if review["decision"]["validation_gate_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
