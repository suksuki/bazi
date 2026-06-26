from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_synthetic_typical_answer_training_signal_review


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CORE-CAL-S2 typical Bazi answer training signal review.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_synthetic_typical_answer_training_signal_review()
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            "v30.synthetic_typical_answer_training_signal_review.v1: "
            f"{'passed' if decision['synthetic_typical_answer_training_signal_review_ready'] else 'failed'} "
            f"({decision['passed_check_count']}/{decision['check_count']}) "
            f"{decision['decision_status']}"
        )
        print(
            f"- signals={decision['training_signal_count']} "
            f"queue_items={decision['queued_item_count']} "
            f"auto_apply={decision['auto_apply_training_allowed']}"
        )
        print(f"- next={result['next_mainline_selection']['task_id']}")
    return 0 if decision["synthetic_typical_answer_training_signal_review_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
