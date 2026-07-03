from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation.evaluation_training_spine import run_evaluation_training_spine


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 Evaluation & Training Spine quality gate.")
    parser.add_argument("--phase1-only", action="store_true", help="Skip Phase 2 ziwei/reality-probe cases.")
    parser.add_argument("--json", action="store_true", help="Print full JSON result.")
    args = parser.parse_args()

    result = run_evaluation_training_spine(include_phase2=not args.phase1_only)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        decision = result["decision"]
        print(
            f"{result['version']}: {result['status']} "
            f"({decision['passed_case_count']}/{decision['case_count']} cases) "
            f"score={decision['average_overall_score']} "
            f"overclaim={decision['overclaim_rate']}"
        )
        for case_id in decision.get("failed_case_ids", []):
            print(f"- failed: {case_id}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
