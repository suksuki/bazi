from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_real_bazi_distribution_replay


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RBD real-case and 518K sample distribution replay.")
    parser.add_argument("--real-case-limit", type=int, default=8)
    parser.add_argument("--sample-518k-limit", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_real_bazi_distribution_replay(
        real_case_limit=args.real_case_limit,
        sample_518k_limit=args.sample_518k_limit,
    )
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            "v30.real_bazi_distribution_replay.v1: "
            f"{'passed' if decision['distribution_replay_ready'] else 'failed'} "
            f"({decision['passed_check_count']}/{decision['check_count']}) "
            f"{decision['decision_status']}"
        )
        print(
            f"- real_case={result['real_case_summary']['ready_case_count']}/"
            f"{result['real_case_summary']['replay_case_count']} "
            f"sample_518k={result['sample_518k_summary']['ready_case_count']}/"
            f"{result['sample_518k_summary']['replay_case_count']}"
        )
    return 0 if decision["distribution_replay_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
