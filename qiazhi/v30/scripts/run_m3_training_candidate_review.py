from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_m3_training_candidate_review


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 M3-G3 training candidate review.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--artifact-dir", default=".runtime/validation/m3")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_m3_training_candidate_review(
        sample_limit=args.sample_limit,
        artifact_dir=args.artifact_dir,
    )
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"{result['version']}: "
            f"{'passed' if decision['ready_for_training_review'] else 'blocked'} "
            f"({decision['passed_checks']}/{decision['total_checks']}) "
            f"{decision['decision_status']} "
            f"candidates={decision['candidate_count']}"
        )
    return 0 if decision["ready_for_training_review"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
