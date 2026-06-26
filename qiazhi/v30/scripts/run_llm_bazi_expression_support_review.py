from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_llm_bazi_expression_support_review


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 LLM Bazi expression support review.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--artifact-dir", default=".runtime/validation/llm")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_llm_bazi_expression_support_review(
        sample_limit=args.sample_limit,
        artifact_dir=args.artifact_dir,
    )
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"{result['version']}: "
            f"{'passed' if decision['llm_bazi_expression_support_ready'] else 'blocked'} "
            f"({decision['passed_closeout_check_count']}/{decision['closeout_check_count']}) "
            f"{decision['decision_status']} "
            f"acceptance={decision['bazi_llm_acceptance_case_count']} "
            f"next={result['next_mainline_selection']['next_task']}"
        )
    return 0 if decision["llm_bazi_expression_support_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
