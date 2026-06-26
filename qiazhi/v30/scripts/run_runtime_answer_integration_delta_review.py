from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.runtime_answer_integration_delta_review import run_runtime_answer_integration_delta_review


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 CORE-EVIDENCE-5 runtime answer integration delta review.")
    parser.add_argument("--reading-id", default="core-evidence-5-runtime-answer-integration")
    parser.add_argument("--json", action="store_true", help="Print full JSON artifact.")
    args = parser.parse_args()

    result = run_runtime_answer_integration_delta_review(reading_id=args.reading_id)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    decision = result["decision"]
    print(f"{result['version']}: {decision['decision_status']}")
    print(f"runtime_answer_integration_ready={decision['runtime_answer_integration_ready']}")
    print(f"passed={decision['passed_check_count']}/{decision['check_count']}")
    if decision["failed_check_ids"]:
        print("failed=" + ", ".join(decision["failed_check_ids"]))
    if decision["blockers"]:
        print("blockers=" + ", ".join(decision["blockers"]))
    next_task = result["next_mainline_selection"]
    print(f"next={next_task['task_id']} {next_task['title']}")
    return 0 if decision["runtime_answer_integration_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
