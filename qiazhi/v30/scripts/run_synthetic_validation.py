from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import SYNTHETIC_SUITES, run_synthetic_tier


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 synthetic validation suites.")
    parser.add_argument("--tier", choices=tuple(sorted(SYNTHETIC_SUITES)), default="smoke")
    parser.add_argument("--json", action="store_true", help="Print full JSON result.")
    args = parser.parse_args()

    result = run_synthetic_tier(args.tier)
    if args.json:
        print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        print(
            f"{result.suite_id}: "
            f"{'passed' if result.passed else 'failed'} "
            f"({result.passed_count}/{result.case_count})"
        )
        for case in result.results:
            if not case.passed:
                print(f"- {case.case_id}: {', '.join(case.failures)}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
