#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_await_new_calibration_evidence_status


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 W-S1 await-new-calibration-evidence status.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--artifact-dir", default=".runtime/validation/await-evidence")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_await_new_calibration_evidence_status(
        sample_limit=args.sample_limit,
        artifact_dir=args.artifact_dir,
    )
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"{result['version']}: "
            f"{'passed' if decision['await_new_evidence_ready'] else 'blocked'} "
            f"({decision['passed_check_count']}/{decision['check_count']}) "
            f"{decision['decision_status']} "
            f"waiting={decision['waiting_for_new_calibration_evidence']} "
            f"next={result['next_mainline_selection']['next_task']}"
        )
    return 0 if decision["await_new_evidence_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
