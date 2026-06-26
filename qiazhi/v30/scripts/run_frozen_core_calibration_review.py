from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.frozen_core_calibration_review import (
    DEFAULT_FROZEN_CORE_CALIBRATION_TIERS,
    run_frozen_core_calibration_review,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 frozen-core calibration review.")
    parser.add_argument(
        "--tier",
        action="append",
        choices=DEFAULT_FROZEN_CORE_CALIBRATION_TIERS,
        help="Synthetic tier to include. Can be repeated; defaults to the F1 tier set.",
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON result.")
    args = parser.parse_args()

    tiers = tuple(args.tier) if args.tier else DEFAULT_FROZEN_CORE_CALIBRATION_TIERS
    review = run_frozen_core_calibration_review(tiers=tiers)
    if args.json:
        print(json.dumps(review, ensure_ascii=False, indent=2))
    else:
        decision = review["decision"]
        print(
            f"{review['version']}: {decision['decision_status']} "
            f"(tiers={len(review['synthetic_tier_summary'])}, "
            f"signals={review['training_signal_summary']['signal_count']})"
        )
        if decision["blockers"]:
            print(f"- blockers: {', '.join(decision['blockers'])}")
        print(f"- next: {review['next_mainline_selection']['task_id']} {review['next_mainline_selection']['title']}")
        print(f"- boundary: {review['boundary']}")
    return 0 if review["decision"]["calibration_baseline_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
