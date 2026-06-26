from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_main_module_completion_review


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 main module completion review.")
    parser.add_argument("--reading-id", default="mcr1-main-module-completion-review")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_main_module_completion_review(reading_id=args.reading_id)
    decision = result["decision"]
    next_task = result["next_mainline_selection"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            "v30.main_module_completion_review.v1: "
            f"{'passed' if decision['main_module_completion_review_ready'] else 'failed'} "
            f"({decision['passed_count']}/{decision['check_count']}) "
            f"{decision['decision_status']}"
        )
        print(f"next={next_task['task_id']} {next_task['title']}")
    return 0 if decision["main_module_completion_review_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
