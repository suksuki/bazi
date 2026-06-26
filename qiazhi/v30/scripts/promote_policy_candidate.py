from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v30.policy import make_baseline_candidate, promote_candidate_if_valid


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote a V30 policy candidate through validation gates.")
    parser.add_argument("--family", choices=("structure_policy",), default="structure_policy")
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--json", action="store_true", help="Print full JSON result.")
    args = parser.parse_args()

    candidate = make_baseline_candidate(
        candidate_id=args.candidate_id,
        family=args.family,
        change_summary="manual promotion candidate",
    )
    result = promote_candidate_if_valid(candidate)
    if args.json:
        print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        status = "promoted" if result.promoted else "rejected"
        print(f"{args.family}:{args.candidate_id}: {status}")
        if result.failures:
            for failure in result.failures:
                print(f"- {failure}")
    return 0 if result.promoted else 1


if __name__ == "__main__":
    raise SystemExit(main())
