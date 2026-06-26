from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_m3_source_backlog_closeout


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 M3-G6 source backlog closeout and seal review.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--artifact-dir", default=".runtime/validation/m3")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_m3_source_backlog_closeout(
        sample_limit=args.sample_limit,
        artifact_dir=args.artifact_dir,
    )
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"{result['version']}: "
            f"{'passed' if decision['m3_closeout_ready'] else 'blocked'} "
            f"({decision['passed_closeout_check_count']}/{decision['closeout_check_count']}) "
            f"{decision['decision_status']} "
            f"candidates={decision['training_candidate_count']} "
            f"backlog_rows={decision['source_backlog_row_count']}"
        )
    return 0 if decision["m3_closeout_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
