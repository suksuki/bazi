from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.targeted_calibration_candidate_review import (
    DEFAULT_TARGETED_CALIBRATION_FAMILIES,
    run_targeted_calibration_candidate_review,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 targeted calibration candidate review.")
    parser.add_argument("--review-id", default=None)
    parser.add_argument("--family", action="append", choices=DEFAULT_TARGETED_CALIBRATION_FAMILIES)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    families = tuple(args.family) if args.family else DEFAULT_TARGETED_CALIBRATION_FAMILIES
    review = run_targeted_calibration_candidate_review(families=families, review_id=args.review_id)
    if args.json:
        print(json.dumps(review, ensure_ascii=False, indent=2))
    else:
        decision = review["decision"]
        print(
            f"{review['version']}: {decision['decision_status']} "
            f"(candidates={review['candidate_summary']['candidate_count']})"
        )
        for blocker in decision["blockers"]:
            print(f"- blocker: {blocker}")
        print(f"- next: {review['next_mainline_selection']['task_id']} {review['next_mainline_selection']['title']}")
        print(f"- boundary: {review['boundary']}")
    return 0 if review["decision"]["targeted_calibration_review_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
