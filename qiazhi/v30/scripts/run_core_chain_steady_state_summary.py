from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_core_chain_steady_state_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 core chain steady-state summary.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--artifact-dir", default=".runtime/validation/core-chain")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_core_chain_steady_state_summary(
        sample_limit=args.sample_limit,
        artifact_dir=args.artifact_dir,
    )
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"{result['version']}: "
            f"{'passed' if decision['core_chain_steady_state_ready'] else 'blocked'} "
            f"({decision['passed_check_count']}/{decision['check_count']}) "
            f"{decision['decision_status']} "
            f"modules={decision['module_count']} "
            f"next={result['next_mainline_selection']['next_task']}"
        )
    return 0 if decision["core_chain_steady_state_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
