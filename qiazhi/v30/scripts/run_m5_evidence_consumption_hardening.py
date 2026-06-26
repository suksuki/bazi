from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.validation import run_m5_evidence_consumption_hardening


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 M5 evidence consumption hardening.")
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--artifact-dir", default=".runtime/validation/m5")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_m5_evidence_consumption_hardening(
        sample_limit=args.sample_limit,
        artifact_dir=args.artifact_dir,
    )
    decision = result["decision"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"{result['version']}: "
            f"{'passed' if decision['m5_evidence_consumption_ready'] else 'blocked'} "
            f"({decision['passed_hardening_check_count']}/{decision['hardening_check_count']}) "
            f"{decision['decision_status']} "
            f"domains={decision['ranked_decision_domain_count']} "
            f"scores={decision['candidate_score_total']}"
        )
    return 0 if decision["m5_evidence_consumption_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
