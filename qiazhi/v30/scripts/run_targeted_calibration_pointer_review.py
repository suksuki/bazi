from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.targeted_calibration_pointer_review import run_targeted_calibration_pointer_review


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 targeted calibration pointer review.")
    parser.add_argument("--review-id", default=None)
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    review = run_targeted_calibration_pointer_review(
        review_id=args.review_id,
        sample_limit=args.sample_limit,
    )
    if args.json:
        print(json.dumps(review, ensure_ascii=False, indent=2))
    else:
        decision = review["decision"]
        print(
            f"{review['version']}: {decision['decision_status']} "
            f"(diffs={review['pointer_diff_summary']['would_change_count']})"
        )
        for blocker in decision["blockers"]:
            print(f"- blocker: {blocker}")
        print(f"- next: {review['next_mainline_selection']['task_id']} {review['next_mainline_selection']['title']}")
        print(f"- boundary: {review['boundary']}")
    return 0 if review["decision"]["pointer_review_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
